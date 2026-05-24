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
