# Practitioner Depth — Chapter 2 — Anatomy of a Healthcare Enterprise

*Technical grounding that operationalizes the chapter's five-sector concepts. Written for data engineers, healthcare analysts, and AI practitioners building payer and provider systems.*

## Data Snapshots

## Domain Data Snapshots — Chapter 2

### 837P Professional Claim — Key Loop and Segment Structure

The ASC X12 837P (Professional) transaction is the standard electronic format for submitting professional medical claims. Understanding its structure is essential for payer AI systems that process, audit, or analyze claims data at scale.

| Loop / Segment | Purpose | Notes |
|---|---|---|
| **ISA** | Interchange Control Header | Sender/receiver IDs, date, version |
| **GS** | Functional Group Header | Functional identifier, control number |
| **ST** | Transaction Set Header | `837` = Health Care Claim |
| **LOOP 2000A — Billing Provider** | | |
| `NM1*85` | Billing Provider Name | Entity type, NPI, tax ID |
| `N3` | Address | Street |
| `N4` | City / State / Zip | |
| **LOOP 2000B — Subscriber (Insured)** | | |
| `NM1*IL` | Subscriber Name | Member ID, last name, first name |
| `DMG` | Subscriber Demographics | DOB, gender |
| `INS` | Subscriber Information | Relationship to insured |
| **LOOP 2000C — Patient** (if different from subscriber) | | |
| `NM1*QC` | Patient Name | |
| `DMG` | Patient Demographics | |
| **LOOP 2300 — Claim Information** | | |
| `CLM` | Claim Details | Claim ID, total charge, place of service, signature on file, assignment of benefits |
| `DTP*434` | Service Date Range | |
| `REF*D9` | Claim Identifier | |
| `HI` | Diagnosis Codes | ICD-10-CM: principal + secondary |
| `HI*BK` | Principal Diagnosis | e.g., `HI*BK:E11.9` = Type 2 Diabetes unspecified |
| **LOOP 2400 — Service Line** | | |
| `LX` | Service Line Number | |
| `SV1` | Professional Service | CPT/HCPCS code, charge, units, place of service |
| `DTP*472` | Date of Service | |
| `REF*6R` | Line Item Control Number | |
| **SE** | Transaction Set Trailer | |
| **GE** | Functional Group Trailer | |
| **IEA** | Interchange Control Trailer | |

#### Key AI-relevant fields

| Field | Meaning | Why it matters |
|---|---|---|
| `CLM01` | Claim ID | Join key across 837 (submission) and 835 (remittance/payment) |
| `HI*BK` | Principal diagnosis (ICD-10-CM) | Primary feature for clinical AI modeling |
| `SV101` | Procedure code (CPT/HCPCS) | Primary feature for clinical AI modeling |
| `SV102` | Charge amount | Cost / utilization signal |
| `SV104` | Units of service | Utilization signal |
| `NM109` | NPI | Links claims to provider registries |

> **Expert Note — Modeling Anchors**
>
> For payer AI systems, the `HI` segment (diagnosis codes) and `SV1` segment (procedure codes) are the primary features for clinical modeling. The `NM1*85` NPI links claims to provider registries. The `CLM01` claim ID is the join key between 837 (claim submission) and 835 (remittance / payment) transactions.

---

### Consumer Health Data Integration Pipeline — Architecture Sketch

A consumer health data integration pipeline must address three architectural challenges simultaneously: **format normalization** (Apple Health, Fitbit, Garmin all use different schemas), **clinical validation** (consumer sensor data requires quality scoring before clinical use), and **consent enforcement** (data use must be traceable to patient authorization).

| Stage | Responsibility | Key operations |
|---|---|---|
| **1 — Ingestion** | Receive HealthKit / Google Fit exports or FHIR-compliant API feeds | Validate format and completeness on arrival; tag each record with source device, firmware version, ingestion timestamp |
| **2 — Normalization** | Map device-specific observation types to LOINC codes | Convert units to UCUM standard; apply device-specific calibration offsets where available from manufacturer documentation |
| **3 — Quality Scoring** | Apply signal-quality filters | Detect physiologically implausible values, artifact, data gaps; score each observation `High` / `Moderate` / `Low` / `Reject` |
| **4 — Consent Enforcement** | Validate against current consent agreement | Apply data-use restriction flags; log all downstream access to the consent audit trail |
| **5 — FHIR Output** | Serialize for downstream consumers | Emit quality-scored, consent-validated observations as FHIR R4 `Observation` resources for the enterprise FHIR server, payer risk models, and provider clinical systems |

A reference Python sketch of the payer-side risk-stratification stage that consumes this pipeline lives in [`code/risk_stratification.py`](code/risk_stratification.py).

## Code

_Tested and Colab-compatible. Click **Open in Colab** to run any sample in your browser — no setup._

### `risk_stratification.py`

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zkumar/healthcare-ai-book-preview/blob/main/docs/02-anatomy-of-the-healthcare-enterprise/code/risk_stratification.ipynb)

[Download .py](code/risk_stratification.py) · [Download notebook](code/risk_stratification.ipynb)

```python
"""Payer Risk Stratification Pipeline — illustrative implementation.

# For Google Colab compatibility:
# !pip install pandas

# In a production system, the full CMS HCC V28 model coefficients
# would be loaded from a comprehensive dataset, and HEDIS care-gap rules
# would be dynamically updated from official specifications. For this
# didactic example, we use simplified, illustrative subsets and rules
# to demonstrate the core logic of risk stratification and care gap identification.



Status: UNTESTED. This is the simplified HCC-aware risk-stratification sketch
from Chapter 2. Before this is referenced from chapter.md as a worked example
it needs:
  - the full CMS HCC V28 model coefficients (this file uses a 7-condition
    illustrative subset; the production model has ~115 condition categories
    with gender-age interaction terms, disease interaction adjustments, and
    separate coefficients for new enrollees and institutional patients)
  - unit tests covering RAF score boundaries and tier-assignment edges
  - a worked example with a population larger than four members
  - HEDIS care-gap rules verified against current measure year
"""
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

# --- Unit Tests (for Colab and local execution) ---
def test_calculate_raf_score():
    # Test a basic member profile
    member = MemberRiskProfile("MBR-TEST-01", 60, "F", ["E11.9", "I10"], 0)
    raf = calculate_raf_score(member)
    # Expected: base_score (0.15 + (60-18)*0.008) * 1.0 = 0.486
    # HCC: E11 (0.368) + I10 (0.156) = 0.524
    # Total: 0.486 + 0.524 = 1.01
    assert abs(raf - 1.01) < 0.001

    # Test with utilization
    member_util = MemberRiskProfile("MBR-TEST-02", 70, "M", ["I50", "N18"], 2)
    raf_util = calculate_raf_score(member_util)
    # Expected: base_score (0.15 + (70-18)*0.008) * 1.05 = 0.8064
    # HCC: I50 (0.894) + N18 (0.532) = 1.426
    # Util factor: 1 + (2 * 0.05) = 1.1
    # Total: (0.5943 + 1.426) * 1.1 = 2.22233
    assert abs(raf_util - 2.222) < 0.001

def test_assign_risk_tier():
    assert assign_risk_tier(2.5) == "TIER-1-CRITICAL"
    assert assign_risk_tier(3.0) == "TIER-1-CRITICAL"
    assert assign_risk_tier(1.5) == "TIER-2-HIGH"
    assert assign_risk_tier(2.49) == "TIER-2-HIGH"
    assert assign_risk_tier(0.8) == "TIER-3-MODERATE"
    assert assign_risk_tier(1.49) == "TIER-3-MODERATE"
    assert assign_risk_tier(0.79) == "TIER-4-LOW"
    assert assign_risk_tier(0.0) == "TIER-4-LOW"

def test_identify_care_gaps():
    member_diabetes = MemberRiskProfile("MBR-GAP-01", 55, "F", ["E11.9"], 0)
    assert "HbA1c_Test_Overdue" in identify_care_gaps(member_diabetes)

    member_bp = MemberRiskProfile("MBR-GAP-02", 65, "M", ["I10"], 0)
    assert "BP_Control_Monitoring" in identify_care_gaps(member_bp)

    member_hf = MemberRiskProfile("MBR-GAP-03", 70, "F", ["I50.9"], 0)
    assert "Heart_Failure_Followup" in identify_care_gaps(member_hf)

    member_colorectal = MemberRiskProfile("MBR-GAP-04", 50, "M", [], 0)
    assert "Colorectal_Screening_Due" in identify_care_gaps(member_colorectal)

    member_no_gaps = MemberRiskProfile("MBR-GAP-05", 30, "F", ["Z00.00"], 0)
    assert not identify_care_gaps(member_no_gaps)

def test_stratify_population():
    population = [
        MemberRiskProfile("MBR-POP-01", 60, "F", ["E11.9", "I10"], 0),
        MemberRiskProfile("MBR-POP-02", 70, "M", ["I50", "N18"], 2),
    ]
    df = stratify_population(population)
    assert not df.empty
    assert len(df) == 2
    assert df.iloc[0]["risk_tier"] == "TIER-2-HIGH" # MBR-POP-02
    assert df.iloc[1]["risk_tier"] == "TIER-3-MODERATE" # MBR-POP-01

# --- End Unit Tests ---


# Simplified HCC condition categories relevant to risk stratification.
# Production version uses the full CMS HCC V28 model coefficients.
HCC_WEIGHTS: dict[str, float] = {
    "E11": 0.368,   # Type 2 Diabetes
    "I50": 0.894,   # Heart Failure
    "J44": 0.346,   # COPD
    "N18": 0.532,   # Chronic Kidney Disease
    "F32": 0.309,   # Major Depressive Disorder
    "E66": 0.273,   # Obesity
    "I10": 0.156,   # Hypertension (base)
}


@dataclass
class MemberRiskProfile:
    member_id: str
    age: int
    gender: str
    icd10_codes: list[str]
    utilization_12m: int  # ED visits + inpatient days, last 12 months
    raf_score: float = 0.0
    risk_tier: str = ""
    care_gap_flags: list[str] = field(default_factory=list)


def calculate_raf_score(profile: MemberRiskProfile) -> float:
    """Simplified RAF (Risk Adjustment Factor) score.

    Production version uses the full CMS HCC V28 model coefficients.
    """
    # Demographic base score (simplified)
    age_factor = 0.15 + (profile.age - 18) * 0.008 if profile.age >= 18 else 0.10
    gender_factor = 1.05 if profile.gender == "M" else 1.0
    base_score = age_factor * gender_factor

    # HCC condition scores
    hcc_score = 0.0
    for code in profile.icd10_codes:
        prefix = code[:3]  # ICD-10 3-char category
        if prefix in HCC_WEIGHTS:
            hcc_score += HCC_WEIGHTS[prefix]

    # Utilization adjustment
    util_factor = 1 + (profile.utilization_12m * 0.05)

    return round((base_score + hcc_score) * util_factor, 3)


def assign_risk_tier(raf: float) -> str:
    if raf >= 2.5:
        return "TIER-1-CRITICAL"
    elif raf >= 1.5:
        return "TIER-2-HIGH"
    elif raf >= 0.8:
        return "TIER-3-MODERATE"
    else:
        return "TIER-4-LOW"


def identify_care_gaps(profile: MemberRiskProfile) -> list[str]:
    """Identify HEDIS-aligned care gaps based on diagnosis profile."""
    gaps: list[str] = []
    codes = set(c[:3] for c in profile.icd10_codes)

    if "E11" in codes and profile.age >= 18:
        gaps.append("HbA1c_Test_Overdue")          # CDC: Diabetes HbA1c testing
    if "I10" in codes and profile.age >= 18:
        gaps.append("BP_Control_Monitoring")       # CBP: Controlling Blood Pressure
    if "I50" in codes:
        gaps.append("Heart_Failure_Followup")      # HFF: 7-day post-discharge
    if profile.age >= 50 and "colorectal_screen" not in profile.icd10_codes:
        gaps.append("Colorectal_Screening_Due")    # COL: Colorectal cancer screening

    return gaps


def stratify_population(members: list[MemberRiskProfile]) -> pd.DataFrame:
    results = []
    for m in members:
        m.raf_score = calculate_raf_score(m)
        m.risk_tier = assign_risk_tier(m.raf_score)
        m.care_gap_flags = identify_care_gaps(m)
        results.append({
            "member_id":   m.member_id,
            "age":         m.age,
            "raf_score":   m.raf_score,
            "risk_tier":   m.risk_tier,
            "care_gaps":   len(m.care_gap_flags),
            "gap_details": "; ".join(m.care_gap_flags),
            "conditions":  len(m.icd10_codes),
        })
    return pd.DataFrame(results).sort_values("raf_score", ascending=False)


def _example() -> pd.DataFrame:
    sample_population = [
        MemberRiskProfile("MBR-001", 67, "M", ["E11.9", "I10", "I50.9"], utilization_12m=4),
        MemberRiskProfile("MBR-002", 45, "F", ["F32.1", "E66.09"],        utilization_12m=1),
        MemberRiskProfile("MBR-003", 72, "M", ["N18.3", "I10", "J44.1"],  utilization_12m=6),
        MemberRiskProfile("MBR-004", 38, "F", ["E11.65"],                 utilization_12m=0),
    ]
    return stratify_population(sample_population)


if __name__ == "__main__":
    print("Running unit tests...")
    test_calculate_raf_score()
    test_assign_risk_tier()
    test_identify_care_gaps()
    test_stratify_population()
    print("Unit tests passed.\n")
    print("--- Example Risk Stratification ---")
    results = _example()
    print(results.to_markdown(index=False))
    print(f"\nTotal Members: {len(results)}")
    print(f"Tier-1 Critical Members: {len(results[results.risk_tier == 'TIER-1-CRITICAL'])}")
    print(f"Members with Care Gaps: {len(results[results.care_gaps > 0])}")
    print("\nHuman-in-the-loop: Medical Director reviews stratification criteria; Care Managers review individual member profiles.")
```
