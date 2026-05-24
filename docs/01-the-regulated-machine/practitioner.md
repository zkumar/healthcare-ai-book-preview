# Practitioner Depth — Chapter 1 — The Regulated Machine

*Technical grounding that operationalizes the chapter's regulatory concepts. Written for software engineers, quality professionals, and clinical informaticists building regulated AI systems.*

## Data Snapshots

## Domain Data Snapshots — Chapter 1

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

A reference Python implementation lives in [`code/risk_register.py`](code/risk_register.py).

## Code

_Tested and Colab-compatible. Click **Open in Colab** to run any sample in your browser — no setup._

### `risk_register.py`

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zkumar/healthcare-ai-book-preview/blob/main/docs/01-the-regulated-machine/code/risk_register.ipynb)

[Download .py](code/risk_register.py) · [Download notebook](code/risk_register.ipynb)

```python
"""ISO 14971 Risk Register — illustrative implementation.

# For Google Colab compatibility:
# !pip install pandas

# In a production system, Excel export, risk heat-map visualization,
# and regulatory report generation would involve external libraries
# (e.g., openpyxl, matplotlib, custom PDF generators) or integrations
# with dedicated risk management software. For this didactic example,
# we focus on the core data model and logic, with DataFrame output
# as a flexible intermediate representation.



Status: TESTED and Colab-compatible. This practitioner code provides an illustrative implementation of an ISO 14971 Risk Register.

Key abstractions for a production system:
  - **Excel Export/Visualization:** In a real-world scenario, this would integrate with libraries like `openpyxl` for Excel output or `matplotlib`/`seaborn` for risk heat-map visualizations.
  - **Regulatory Report Generation:** Production systems would involve custom PDF generators or integration with specialized regulatory reporting tools.
  - **Full CMS HCC V28 Model Coefficients:** For comprehensive risk stratification, a production system would incorporate the full set of CMS HCC V28 model coefficients.
  - **HEDIS Care-Gap Rules:** Real-world care gap analysis would involve integrating with extensive HEDIS care-gap rulesets.
  - **FHIR Server Integration:** Robust FHIR bundle parsing would involve direct integration with FHIR servers for data retrieval and validation.
  - **UMLS Linker and Negspacy Implementation:** Advanced clinical NLP would leverage a fully configured UMLS linker and comprehensive negspacy rules for negation detection.
  - **OMOP Vocabulary Download:** Production systems would dynamically download and manage OMOP vocabularies for semantic traversal.
  - **LLM-based Semantic Scoring:** Requirements quality scoring would be enhanced with LLM-based semantic analysis.
  - **External Connectors:** Traceability matrix generation would connect to external requirements management and test management tools.
  - **Semantic Embedding Models:** Complaint clustering would utilize advanced semantic embedding models for more accurate grouping.
  - **GUDID Schema Syncing:** UDI validation would involve real-time syncing with GUDID schemas.
  - **PubMed API Integration:** CER literature screening would integrate with PubMed API for automated literature search.
  - **Vector Database and LLM Integration:** Quality Brain RAG would leverage vector databases and LLMs for contextual retrieval.
  - **NVD API Integration:** SBOM validation would integrate with NVD API for vulnerability data.
  - **LLM-based STRIDE Generation:** Threat modeling would use LLMs to generate STRIDE threats.
  - **LLM-based Natural Language Complaint Analysis:** MDR reportability would involve LLM-based analysis of complaints.
  - **LLM-backed Content Generation:** PSUR generation would use LLMs for content creation.
  - **LLM-based Clinical Context:** Care gap analysis would incorporate LLM-based clinical context.
  - **Clinical NLP Pipelines:** Coding suggestions would utilize advanced clinical NLP pipelines.
  - **Epic CDS Hooks Integration:** NEWS2 scoring would integrate with Epic CDS Hooks.
  - **Jurisdiction-specific Reporting Rules:** Pharmacovigilance would adhere to specific regulatory reporting rules.
  - **Specialized Statistical Software:** Trial design would use specialized statistical software.
  - **MLOps Platform Integration:** Model registry would integrate with MLOps platforms for deployment and monitoring.
"""
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional

import pandas as pd

# --- Unit Tests (for Colab and local execution) ---
def test_risk_scoring():
    entry = RiskEntry(
        hazard_id="TEST-001",
        hazard_description="Test Hazard",
        hazardous_situation="Test Situation",
        harm="Test Harm",
        severity=Severity.SERIOUS,
        probability=Probability.OCCASIONAL,
        risk_control="None",
        residual_severity=Severity.MINOR,
        residual_probability=Probability.REMOTE,
        verification_method="Test Method",
    )
    assert entry.pre_risk_score == 9  # 3 * 3
    assert entry.residual_risk_score == 4 # 2 * 2
    assert entry.residual_risk_level == "ACCEPTABLE"

    unacceptable_entry = RiskEntry(
        hazard_id="TEST-002",
        hazard_description="Unacceptable Hazard",
        hazardous_situation="Unacceptable Situation",
        harm="Unacceptable Harm",
        severity=Severity.CATASTROPHIC,
        probability=Probability.FREQUENT,
        risk_control="None",
        residual_severity=Severity.CRITICAL,
        residual_probability=Probability.PROBABLE,
        verification_method="Test Method",
    )
    assert unacceptable_entry.residual_risk_score == 16 # 4 * 4
    assert unacceptable_entry.residual_risk_level == "UNACCEPTABLE"

def test_risk_register_methods():
    register = RiskRegister("Test Device", "Test Class")
    entry1 = RiskEntry(
        hazard_id="TEST-001",
        hazard_description="Test Hazard 1",
        hazardous_situation="Test Situation 1",
        harm="Test Harm 1",
        severity=Severity.SERIOUS,
        probability=Probability.OCCASIONAL,
        risk_control="None",
        residual_severity=Severity.MINOR,
        residual_probability=Probability.REMOTE,
        verification_method="Test Method",
    )
    entry2 = RiskEntry(
        hazard_id="TEST-002",
        hazard_description="Test Hazard 2",
        hazardous_situation="Test Situation 2",
        harm="Test Harm 2",
        severity=Severity.CATASTROPHIC,
        probability=Probability.FREQUENT,
        risk_control="None",
        residual_severity=Severity.CRITICAL,
        residual_probability=Probability.PROBABLE,
        verification_method="Test Method",
    )
    register.add(entry1)
    register.add(entry2)

    assert len(register.entries) == 2
    assert len(register.unacceptable_risks()) == 1
    df = register.to_dataframe()
    assert not df.empty
    assert "Hazard ID" in df.columns


# --- End Unit Tests ---


class Severity(IntEnum):
    NEGLIGIBLE   = 1   # No injury
    MINOR        = 2   # Temporary injury, no professional intervention
    SERIOUS      = 3   # Injury requiring professional medical intervention
    CRITICAL     = 4   # Permanent impairment or life-threatening
    CATASTROPHIC = 5   # Death


class Probability(IntEnum):
    INCREDIBLE = 1   # Unimaginable that harm occurs
    REMOTE     = 2   # Unlikely but possible
    OCCASIONAL = 3   # Likely to occur sometime
    PROBABLE   = 4   # Will occur several times
    FREQUENT   = 5   # Likely to occur repeatedly


@dataclass
class RiskEntry:
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
        elif score <= 9:
            return "ALARP"   # As Low As Reasonably Practicable
        else:
            return "UNACCEPTABLE"


class RiskRegister:
    def __init__(self, device_name: str, software_class: str):
        self.device_name = device_name
        self.software_class = software_class
        self.entries: list[RiskEntry] = []

    def add(self, entry: RiskEntry) -> None:
        self.entries.append(entry)

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([{
            "Hazard ID":           e.hazard_id,
            "Harm":                e.harm,
            "Pre-Risk Score":      e.pre_risk_score,
            "Risk Control":        e.risk_control,
            "Residual Risk Score": e.residual_risk_score,
            "Residual Risk Level": e.residual_risk_level,
        } for e in self.entries])

    def unacceptable_risks(self) -> list[RiskEntry]:
        return [e for e in self.entries if e.residual_risk_level == "UNACCEPTABLE"]


def _example() -> RiskRegister:
    """Worked example: Sepsis Prediction AI — IEC 62304 Class C."""
    register = RiskRegister("Sepsis Early Warning AI", "IEC 62304 Class C")
    register.add(RiskEntry(
        hazard_id            = "HAZ-001",
        hazard_description   = "False-negative sepsis prediction",
        hazardous_situation  = "High-risk patient not flagged; clinician not alerted",
        harm                 = "Delayed sepsis treatment; potential death",
        severity             = Severity.CATASTROPHIC,
        probability          = Probability.REMOTE,
        risk_control         = ("Sensitivity threshold tuned to >90%; HITL mandatory review "
                                "for all ICU patients; fallback to SOFA score if model unavailable"),
        residual_severity    = Severity.CATASTROPHIC,
        residual_probability = Probability.INCREDIBLE,
        verification_method  = "Clinical validation study; sensitivity/specificity on holdout set",
        notes                = "Residual risk accepted per benefit-risk analysis REF-BR-001",
    ))
    return register


if __name__ == "__main__":
    print("Running unit tests...")
    test_risk_scoring()
    test_risk_register_methods()
    print("Unit tests passed.\n")
    register = _example()
    print("--- Example Risk Register ---")
    print(f"Device: {register.device_name} | Software Class: {register.software_class}\n")
    print(register.to_dataframe().to_markdown(index=False))
    print(f"\nTotal Unacceptable Risks: {len(register.unacceptable_risks())}")
    if register.unacceptable_risks():
        print("Details of Unacceptable Risks:")
        for r in register.unacceptable_risks():
            print(f"  - {r.hazard_id}: {r.hazard_description} (Score: {r.residual_risk_score})")
    else:
        print("No unacceptable risks identified.")
    print("\nHuman-in-the-loop: Risk Manager reviews and approves all risk classifications and controls.")
```
