"""Minimal healthcare AI risk-register example for Chapter 2.

The script teaches how hazards, harms, mitigations, residual risk, verification
evidence, and review status can be represented in an auditable structure. It is
a teaching implementation, not a substitute for an organization's formal quality
management or compliance system.
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


def test_evaluate_simplified_bp_control():
    member = {
        "member_id": "M001",
        "age": 54,
        "has_hypertension": True,
        "hospice": False,
        "blood_pressure_readings": [
            {"date": "2024-01-15", "systolic": 142, "diastolic": 91},
            {"date": "2024-06-10", "systolic": 128, "diastolic": 78},
        ],
    }
    result = evaluate_simplified_bp_control(member)
    assert result["eligible"] is True
    assert result["meets_rule"] is True
    assert result["evidence"]["date"] == "2024-06-10"

    hospice_member = dict(member, hospice=True)
    excluded = evaluate_simplified_bp_control(hospice_member)
    assert excluded["eligible"] is False
    assert excluded["reason"] == "Excluded: hospice flag present"


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


def evaluate_simplified_bp_control(member: dict) -> dict:
    """Evaluate a simplified HEDIS-style blood-pressure-control rule.

    This function is for education only. Official HEDIS specifications and
    industrial quality engines include detailed value sets, enrollment windows,
    encounter logic, exclusions, supplemental data rules, audit controls, and
    certification requirements that are intentionally out of scope here.
    """
    if member.get("hospice"):
        return {
            "member_id": member.get("member_id"),
            "eligible": False,
            "meets_rule": False,
            "reason": "Excluded: hospice flag present",
            "evidence": None,
        }

    if member.get("age", 0) < 18 or not member.get("has_hypertension"):
        return {
            "member_id": member.get("member_id"),
            "eligible": False,
            "meets_rule": False,
            "reason": "Not in denominator",
            "evidence": None,
        }

    readings = sorted(member.get("blood_pressure_readings", []), key=lambda r: r["date"])
    if not readings:
        return {
            "member_id": member.get("member_id"),
            "eligible": True,
            "meets_rule": False,
            "reason": "No blood-pressure evidence",
            "evidence": None,
        }

    latest = readings[-1]
    controlled = latest["systolic"] < 140 and latest["diastolic"] < 90
    return {
        "member_id": member.get("member_id"),
        "eligible": True,
        "meets_rule": controlled,
        "reason": "Controlled" if controlled else "Most recent blood pressure is above threshold",
        "evidence": latest,
    }


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
    test_evaluate_simplified_bp_control()
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
    print("\n--- Simplified HEDIS-Style Rule Example ---")
    hedis_member = {
        "member_id": "M001",
        "age": 54,
        "has_hypertension": True,
        "hospice": False,
        "blood_pressure_readings": [
            {"date": "2024-01-15", "systolic": 142, "diastolic": 91},
            {"date": "2024-06-10", "systolic": 128, "diastolic": 78},
        ],
    }
    print(evaluate_simplified_bp_control(hedis_member))
    print("\nHuman-in-the-loop: Risk Manager reviews and approves all risk classifications and controls.")
