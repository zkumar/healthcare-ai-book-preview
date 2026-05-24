# Practitioner Depth — Chapter 2 — The Regulated Machine

*Technical grounding for the chapter's regulatory argument. This section teaches how intended use, harm, accountability, and evidence obligations change across healthcare AI contexts.*

## Data Snapshots

## Domain Data Snapshots — Chapter 2

### IEC 62304 Software Safety Classification

IEC 62304 classifies medical-device software into three safety classes based on the potential severity of harm from software failure. For AI-embedded systems, classification must account for both the direct output of the model and its downstream clinical use.

| Class | Failure Consequence | Examples | Required Process Rigor |
|---|---|---|---|
| **A** | No injury or damage to health possible | Administrative scheduling AI · patient-education chatbot · non-clinical documentation assistant | Basic software-development-process documentation |
| **B** | Non-serious injury possible | Medication-adherence reminder AI · wellness risk score · appointment no-show prediction | Software development plan, requirements, architecture, detailed design, unit/integration testing, maintenance plan |
| **C** | Death or serious injury possible | Sepsis prediction AI · surgical guidance system · diagnostic imaging AI · drug-dosing recommendation engine · autonomous prior-authorization decision system | All Class B requirements plus: rigorous requirements with traceability matrix · formal ISO 14971 risk analysis · comprehensive test coverage with documented rationale · change control on every model update · post-market surveillance and anomaly reporting |

> **Expert Note — AI-Specific Reclassification**
>
> If a Class A system's model output begins influencing clinical decisions — even informally — it must be reclassified. Most GenAI systems deployed in clinical workflows will be Class B or Class C. Every model retrain that changes clinical behavior is a change-control event, and the safety classification must be reviewed whenever the AI system's intended use changes.

---

### ISO 14971 Risk Register Structure

ISO 14971 requires a formal risk-management file for every medical device, including AI systems. The risk register is the core artifact. Each identified hazard requires probability, severity, detectability, and residual-risk assessment.

| Field | Description |
|---|---|
| Hazard ID | Unique identifier (e.g., `HAZ-001`) |
| Hazard Description | Root cause of potential harm |
| Hazardous Situation | Sequence of events leading to harm |
| Harm | Clinical consequence if hazard reaches patient |
| Severity (S) | 1–5 scale: 1 = Negligible, 5 = Death |
| Probability (P) | 1–5 scale: 1 = Incredible, 5 = Frequent |
| Risk Level (S × P) | Pre-mitigation risk score |
| Risk Control Measure | Engineering, labelling, or training control |
| Residual Severity | Post-mitigation severity |
| Residual Probability | Post-mitigation probability |
| Residual Risk | Acceptable / Unacceptable / ALARP |
| Verification Method | How control measure effectiveness is confirmed |

A reference Python implementation for the **medical-device risk-register example** lives in [`code/risk_register.py`](code/risk_register.py). The separate healthcare quality-measure example lives in [`code/hedis_bp_control.py`](code/hedis_bp_control.py).

---

### Cross-Sector Healthcare AI Compliance Prompts

The regulatory chapter uses MedTech standards to illustrate rigorous software governance, but practitioners should not infer that regulation begins and ends with medical devices. The same AI capability can trigger different obligations depending on whether it is deployed by a device manufacturer, pharmaceutical company, payer, or provider organization. Use the prompts below as a first-pass compliance discovery tool before selecting a technical architecture.

| Sector | Primary compliance question | Evidence the implementation should preserve | Human review point |
|---|---|---|---|
| **MedTech** | Does the AI output influence diagnosis, monitoring, therapy, device performance, or patient-safety risk? | Intended-use statement, software safety class, hazard analysis, validation protocol, change-control history, post-market monitoring record | Quality / regulatory review before release and after model updates |
| **Pharma** | Does the AI affect GxP records, clinical-trial operations, safety surveillance, regulatory submissions, medical information, or promotional content? | Source data lineage, prompt / output logs where appropriate, human review record, approved final content, audit trail, deviation handling | Medical, regulatory, safety, or promotional-review approval before regulated use |
| **Payer** | Does the AI affect coverage, utilization management, risk adjustment, quality measurement, care-management priority, member communication, or payment integrity? | Member-level rationale, policy mapping, bias and fairness checks, authorization / denial support, appeal packet traceability, CMS or state-program evidence where applicable | Clinical reviewer, compliance officer, or medical director approval before adverse or high-impact action |
| **Provider** | Does the AI affect clinical judgment, documentation, coding, billing, patient communication, care-team workflow, or standard-of-care expectations? | EHR integration design, clinician-facing explanation, data provenance, note attribution, billing-review evidence, safety escalation logs | Licensed clinician accountability at the point of care, with audit support for retrospective review |

> **Practitioner Principle — Intended Use Determines Governance**
>
> Do not classify an AI system only by model type. Classify it by the decision it influences, the user who relies on it, the population it affects, and the harm that could follow from a wrong or misleading output.

## Code

_Tested and Colab-compatible. Click **Open in Colab** to run any sample in your browser — no setup._

### `hedis_bp_control.py`

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zkumar/healthcare-ai-book-preview/blob/main/docs/02-the-regulated-machine/code/hedis_bp_control.ipynb)

[Download .py](code/hedis_bp_control.py) · [Download notebook](code/hedis_bp_control.ipynb)

```python
"""Healthcare quality-measure example for Chapter 2.

This script teaches how a simplified HEDIS-style blood-pressure-control rule can
be represented as denominator, exclusion, numerator, and evidence logic.

It is a healthcare quality-measure teaching example, not a medical-device risk
register. Official HEDIS specifications, payer contracts, accreditation rules,
value-set updates, enrollment windows, event timing, exclusions, supplemental
data rules, audit trails, and certification controls are intentionally out of
scope and may differ materially from this simplified implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BloodPressureReading:
    """A simplified blood-pressure observation used as measure evidence."""

    date: str
    systolic: int
    diastolic: int

    def is_controlled(self) -> bool:
        """Return True when the reading is below the teaching threshold."""
        return self.systolic < 140 and self.diastolic < 90


@dataclass(frozen=True)
class Member:
    """Simplified member record for a healthcare quality-measure example."""

    member_id: str
    age: int
    has_hypertension: bool
    hospice: bool
    blood_pressure_readings: list[BloodPressureReading]


def evaluate_simplified_bp_control(member: Member) -> dict[str, Any]:
    """Evaluate a simplified HEDIS-style blood-pressure-control rule.

    The teaching logic has four intentionally simple steps:

    1. Determine whether the member is excluded.
    2. Determine whether the member belongs in the denominator.
    3. Select the latest blood-pressure reading as evidence.
    4. Apply the simplified numerator threshold.
    """
    if member.hospice:
        return {
            "member_id": member.member_id,
            "eligible": False,
            "meets_rule": False,
            "reason": "Excluded: hospice flag present",
            "evidence": None,
        }

    if member.age < 18 or not member.has_hypertension:
        return {
            "member_id": member.member_id,
            "eligible": False,
            "meets_rule": False,
            "reason": "Not in denominator",
            "evidence": None,
        }

    readings = sorted(member.blood_pressure_readings, key=lambda reading: reading.date)
    if not readings:
        return {
            "member_id": member.member_id,
            "eligible": True,
            "meets_rule": False,
            "reason": "No blood-pressure evidence",
            "evidence": None,
        }

    latest = readings[-1]
    controlled = latest.is_controlled()
    return {
        "member_id": member.member_id,
        "eligible": True,
        "meets_rule": controlled,
        "reason": "Controlled" if controlled else "Most recent blood pressure is above threshold",
        "evidence": {
            "date": latest.date,
            "systolic": latest.systolic,
            "diastolic": latest.diastolic,
        },
    }


def build_example_member() -> Member:
    """Create a sample member for the teaching example."""
    return Member(
        member_id="M001",
        age=54,
        has_hypertension=True,
        hospice=False,
        blood_pressure_readings=[
            BloodPressureReading(date="2024-01-15", systolic=142, diastolic=91),
            BloodPressureReading(date="2024-06-10", systolic=128, diastolic=78),
        ],
    )


# --- Unit tests for local execution and Colab ---
def test_controlled_member() -> None:
    result = evaluate_simplified_bp_control(build_example_member())
    assert result["eligible"] is True
    assert result["meets_rule"] is True
    assert result["evidence"]["date"] == "2024-06-10"


def test_hospice_exclusion() -> None:
    member = build_example_member()
    excluded_member = Member(
        member_id=member.member_id,
        age=member.age,
        has_hypertension=member.has_hypertension,
        hospice=True,
        blood_pressure_readings=member.blood_pressure_readings,
    )
    result = evaluate_simplified_bp_control(excluded_member)
    assert result["eligible"] is False
    assert result["reason"] == "Excluded: hospice flag present"


def test_no_blood_pressure_evidence() -> None:
    member = Member(
        member_id="M002",
        age=61,
        has_hypertension=True,
        hospice=False,
        blood_pressure_readings=[],
    )
    result = evaluate_simplified_bp_control(member)
    assert result["eligible"] is True
    assert result["meets_rule"] is False
    assert result["reason"] == "No blood-pressure evidence"


if __name__ == "__main__":
    print("Running simplified healthcare quality-measure unit tests...")
    test_controlled_member()
    test_hospice_exclusion()
    test_no_blood_pressure_evidence()
    print("Unit tests passed.\n")

    example_member = build_example_member()
    result = evaluate_simplified_bp_control(example_member)
    print("--- Simplified HEDIS-Style Blood-Pressure-Control Example ---")
    print(result)
    print("\nEducational boundary: this is a simplified healthcare quality-measure example, not a medical-device risk register and not an official HEDIS implementation.")
```

### `risk_register.py`

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zkumar/healthcare-ai-book-preview/blob/main/docs/02-the-regulated-machine/code/risk_register.ipynb)

[Download .py](code/risk_register.py) · [Download notebook](code/risk_register.ipynb)

```python
"""Medical-device risk-register example for Chapter 2.

This script teaches how a regulated medical-device software team might represent
hazards, hazardous situations, harms, mitigations, residual risk, verification
evidence, and review status in a simple auditable structure.

It is a teaching implementation for medical-device governance. It is not a
substitute for an organization's formal quality management system, regulatory
strategy, clinical validation plan, or risk-management file.
"""
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional

import pandas as pd


class Severity(IntEnum):
    """Simplified severity scale for medical-device risk scoring."""

    NEGLIGIBLE = 1     # No injury
    MINOR = 2          # Temporary injury, no professional intervention
    SERIOUS = 3        # Injury requiring professional medical intervention
    CRITICAL = 4       # Permanent impairment or life-threatening harm
    CATASTROPHIC = 5   # Death


class Probability(IntEnum):
    """Simplified probability scale for medical-device risk scoring."""

    INCREDIBLE = 1     # Unimaginable that harm occurs
    REMOTE = 2         # Unlikely but possible
    OCCASIONAL = 3     # Likely to occur sometime
    PROBABLE = 4       # Will occur several times
    FREQUENT = 5       # Likely to occur repeatedly


@dataclass
class RiskEntry:
    """One row in a simplified medical-device risk register."""

    hazard_id: str
    hazard_description: str
    hazardous_situation: str
    harm: str
    severity: Severity
    probability: Probability
    risk_control: str
    residual_severity: Severity
    residual_probability: Probability
    verification_method: str
    review_owner: str
    review_status: str
    notes: Optional[str] = None

    @property
    def pre_risk_score(self) -> int:
        return self.severity * self.probability

    @property
    def residual_risk_score(self) -> int:
        return self.residual_severity * self.residual_probability

    @property
    def residual_risk_level(self) -> str:
        score = self.residual_risk_score
        if score <= 4:
            return "ACCEPTABLE"
        if score <= 9:
            return "ALARP"  # As Low As Reasonably Practicable
        return "UNACCEPTABLE"


class RiskRegister:
    """Simple container for medical-device software risk entries."""

    def __init__(self, device_name: str, software_class: str):
        self.device_name = device_name
        self.software_class = software_class
        self.entries: list[RiskEntry] = []

    def add(self, entry: RiskEntry) -> None:
        self.entries.append(entry)

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([
            {
                "Hazard ID": e.hazard_id,
                "Hazard": e.hazard_description,
                "Harm": e.harm,
                "Pre-Risk Score": e.pre_risk_score,
                "Risk Control": e.risk_control,
                "Residual Risk Score": e.residual_risk_score,
                "Residual Risk Level": e.residual_risk_level,
                "Verification": e.verification_method,
                "Review Owner": e.review_owner,
                "Review Status": e.review_status,
            }
            for e in self.entries
        ])

    def unacceptable_risks(self) -> list[RiskEntry]:
        return [entry for entry in self.entries if entry.residual_risk_level == "UNACCEPTABLE"]


def build_example_register() -> RiskRegister:
    """Build a worked example for AI-enabled medical-device software.

    The example uses sepsis early-warning software as a teaching case because it
    affects clinical monitoring and can create patient harm if it fails. Real
    medical-device risk files are broader, trace hazards to requirements and
    verification evidence, and are reviewed under formal quality procedures.
    """
    register = RiskRegister(
        device_name="AI-Enabled Sepsis Early-Warning Medical Device Software",
        software_class="IEC 62304 Class C teaching example",
    )
    register.add(RiskEntry(
        hazard_id="MD-HAZ-001",
        hazard_description="False-negative sepsis prediction",
        hazardous_situation="High-risk patient is not flagged and the clinician is not alerted",
        harm="Delayed sepsis treatment with potential life-threatening deterioration",
        severity=Severity.CATASTROPHIC,
        probability=Probability.REMOTE,
        risk_control=(
            "Sensitivity threshold review; mandatory clinician review for ICU patients; "
            "fallback to non-AI screening workflow if the model is unavailable"
        ),
        residual_severity=Severity.CATASTROPHIC,
        residual_probability=Probability.INCREDIBLE,
        verification_method="Clinical validation study and alarm-workflow simulation",
        review_owner="Medical-device risk manager",
        review_status="Pending formal benefit-risk review",
        notes="Residual risk requires documented acceptance under the quality system.",
    ))
    register.add(RiskEntry(
        hazard_id="MD-HAZ-002",
        hazard_description="False-positive sepsis prediction",
        hazardous_situation="Patient is incorrectly flagged as high risk and unnecessary escalation occurs",
        harm="Alarm fatigue, additional testing, and possible workflow burden",
        severity=Severity.SERIOUS,
        probability=Probability.OCCASIONAL,
        risk_control="Alert-threshold tuning, usability testing, and clinician acknowledgement workflow",
        residual_severity=Severity.MINOR,
        residual_probability=Probability.REMOTE,
        verification_method="Retrospective performance analysis and human-factors validation",
        review_owner="Clinical safety lead",
        review_status="Ready for review",
        notes="This row illustrates that not all hazards have the same severity profile.",
    ))
    return register


# --- Unit tests for local execution and Colab ---
def test_risk_scoring() -> None:
    entry = RiskEntry(
        hazard_id="TEST-001",
        hazard_description="Test hazard",
        hazardous_situation="Test hazardous situation",
        harm="Test harm",
        severity=Severity.SERIOUS,
        probability=Probability.OCCASIONAL,
        risk_control="Test control",
        residual_severity=Severity.MINOR,
        residual_probability=Probability.REMOTE,
        verification_method="Test verification",
        review_owner="Test reviewer",
        review_status="Draft",
    )
    assert entry.pre_risk_score == 9
    assert entry.residual_risk_score == 4
    assert entry.residual_risk_level == "ACCEPTABLE"

    unacceptable_entry = RiskEntry(
        hazard_id="TEST-002",
        hazard_description="Unacceptable test hazard",
        hazardous_situation="Unacceptable test situation",
        harm="Unacceptable test harm",
        severity=Severity.CATASTROPHIC,
        probability=Probability.FREQUENT,
        risk_control="Test control",
        residual_severity=Severity.CRITICAL,
        residual_probability=Probability.PROBABLE,
        verification_method="Test verification",
        review_owner="Test reviewer",
        review_status="Draft",
    )
    assert unacceptable_entry.residual_risk_score == 16
    assert unacceptable_entry.residual_risk_level == "UNACCEPTABLE"


def test_risk_register_methods() -> None:
    register = build_example_register()
    assert len(register.entries) == 2
    assert len(register.unacceptable_risks()) == 0
    df = register.to_dataframe()
    assert not df.empty
    assert "Hazard ID" in df.columns
    assert "Review Status" in df.columns


if __name__ == "__main__":
    print("Running medical-device risk-register unit tests...")
    test_risk_scoring()
    test_risk_register_methods()
    print("Unit tests passed.\n")

    example_register = build_example_register()
    print("--- Medical-Device Risk Register Example ---")
    print(f"Device: {example_register.device_name}")
    print(f"Software Class: {example_register.software_class}\n")
    print(example_register.to_dataframe().to_markdown(index=False))

    unacceptable = example_register.unacceptable_risks()
    print(f"\nTotal Unacceptable Risks: {len(unacceptable)}")
    if unacceptable:
        for risk in unacceptable:
            print(f"  - {risk.hazard_id}: {risk.hazard_description} (Score: {risk.residual_risk_score})")
    else:
        print("No unacceptable residual risks identified in this teaching example.")

    print("\nHuman-in-the-loop: a medical-device risk manager reviews and approves risk classifications, controls, and residual-risk acceptance.")
```
