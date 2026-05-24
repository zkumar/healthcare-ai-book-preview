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
