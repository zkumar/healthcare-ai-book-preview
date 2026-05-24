"""FHIR R4 Bundle Parser — illustrative implementation.

# For Google Colab compatibility:
# !pip install pandas

# In a production system, FHIR bundles would typically be retrieved from a
# FHIR server via a secure API, requiring authentication, pagination, and
# robust error handling. For this didactic example, we use a synthetic
# FHIR bundle directly embedded in the script to demonstrate the core
# parsing logic without external dependencies. The parsing functions
# are simplified to focus on key data extraction, with comments indicating
# where more comprehensive error handling and FHIR version-specific logic
# would be implemented.



Status: UNTESTED. This is the function sketch from Chapter 3.
Before this is referenced from chapter.md as a worked example it needs:
  - unit tests against a checked-in sample bundle fixture
  - a SMART-on-FHIR / OAuth 2.0 wrapper for live API use
  - FHIR pagination handling (Bundle.link[rel=next])
  - rate limiting and retry logic
  - regulatory audit logging (who pulled what, when, for which model)
  - profile validation (US Core, IPS, etc.) before downstream use
"""
from __future__ import annotations

import json
from typing import Optional

import pandas as pd

# --- Synthetic FHIR Bundle Data (for Colab and local execution) ---
SYNTHETIC_FHIR_BUNDLE = {
    "resourceType": "Bundle",
    "id": "bundle-example",
    "type": "searchset",
    "entry": [
        {
            "fullUrl": "http://example.com/fhir/Patient/example",
            "resource": {
                "resourceType": "Patient",
                "id": "example",
                "gender": "female",
                "birthDate": "1970-01-01",
                "address": [
                    {
                        "postalCode": "90210"
                    }
                ]
            }
        },
        {
            "fullUrl": "http://example.com/fhir/Observation/obs-bp",
            "resource": {
                "resourceType": "Observation",
                "id": "obs-bp",
                "status": "final",
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "85354-9",
                            "display": "Blood pressure panel with all components"
                        }
                    ]
                },
                "subject": {
                    "reference": "Patient/example"
                },
                "effectiveDateTime": "2023-01-15T10:30:00Z",
                "valueQuantity": {
                    "value": 120,
                    "unit": "mmHg",
                    "system": "http://unitsofmeasure.org",
                    "code": "mmHg"
                }
            }
        },
        {
            "fullUrl": "http://example.com/fhir/Observation/obs-temp",
            "resource": {
                "resourceType": "Observation",
                "id": "obs-temp",
                "status": "final",
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "8310-5",
                            "display": "Body temperature"
                        }
                    ]
                },
                "subject": {
                    "reference": "Patient/example"
                },
                "effectiveDateTime": "2023-01-15T10:30:00Z",
                "valueQuantity": {
                    "value": 37.5,
                    "unit": "Cel",
                    "system": "http://unitsofmeasure.org",
                    "code": "Cel"
                }
            }
        }
    ]
}

# --- End Synthetic FHIR Bundle Data ---


def parse_fhir_bundle(bundle_json: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Parse a FHIR R4 Bundle into Patient and Observation DataFrames.

    Illustrative only. Production deployments should layer authentication,
    pagination, rate limiting, and audit logging on top of this core.
    """
    patients: list[dict] = []
    observations: list[dict] = []

    for entry in bundle_json.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")

        if resource_type == "Patient":
            patients.append({
                "patient_id":  resource.get("id"),
                "gender":      resource.get("gender"),
                "birth_date":  resource.get("birthDate"),
                "postal_code": _get_postal_code(resource),
            })
        elif resource_type == "Observation":
            observations.append({
                "obs_id":      resource.get("id"),
                "patient_ref": _get_patient_ref(resource),
                "loinc_code":  _get_loinc_code(resource),
                "display":     _get_display(resource),
                "value":       _get_value(resource),
                "unit":        _get_unit(resource),
                "datetime":    resource.get("effectiveDateTime"),
            })

    return pd.DataFrame(patients), pd.DataFrame(observations)


def _get_postal_code(resource: dict) -> Optional[str]:
    addresses = resource.get("address", [])
    return addresses[0].get("postalCode") if addresses else None


def _get_patient_ref(resource: dict) -> Optional[str]:
    subject = resource.get("subject", {})
    ref = subject.get("reference", "")
    if not ref:
        return None
    return ref.split("/")[-1] if "/" in ref else ref


def _get_loinc_code(resource: dict) -> Optional[str]:
    for coding in resource.get("code", {}).get("coding", []):
        if "loinc.org" in coding.get("system", ""):
            return coding.get("code")
    return None


def _get_display(resource: dict) -> Optional[str]:
    codings = resource.get("code", {}).get("coding", [])
    return codings[0].get("display") if codings else None


def _get_value(resource: dict) -> Optional[float]:
    vq = resource.get("valueQuantity", {})
    return vq.get("value")


def _get_unit(resource: dict) -> Optional[str]:
    vq = resource.get("valueQuantity", {})
    return vq.get("unit")


# --- Unit Tests (for Colab and local execution) ---
def test_parse_fhir_bundle():
    patients_df, obs_df = parse_fhir_bundle(SYNTHETIC_FHIR_BUNDLE)

    assert not patients_df.empty
    assert len(patients_df) == 1
    assert patients_df.iloc[0]["patient_id"] == "example"
    assert patients_df.iloc[0]["gender"] == "female"
    assert patients_df.iloc[0]["postal_code"] == "90210"

    assert not obs_df.empty
    assert len(obs_df) == 2
    assert obs_df.iloc[0]["loinc_code"] == "85354-9"
    assert obs_df.iloc[0]["value"] == 120
    assert obs_df.iloc[0]["unit"] == "mmHg"
    assert obs_df.iloc[1]["loinc_code"] == "8310-5"
    assert obs_df.iloc[1]["value"] == 37.5
    assert obs_df.iloc[1]["unit"] == "Cel"

def test_get_postal_code():
    patient_resource = {"address": [{"postalCode": "12345"}]}
    assert _get_postal_code(patient_resource) == "12345"
    assert _get_postal_code({"address": []}) is None
    assert _get_postal_code({}) is None

def test_get_patient_ref():
    obs_resource = {"subject": {"reference": "Patient/pat123"}}
    assert _get_patient_ref(obs_resource) == "pat123"
    assert _get_patient_ref({"subject": {}}) is None
    assert _get_patient_ref({}) is None

def test_get_loinc_code():
    obs_resource = {"code": {"coding": [{"system": "http://loinc.org", "code": "1234-5"}]}}
    assert _get_loinc_code(obs_resource) == "1234-5"
    assert _get_loinc_code({"code": {"coding": []}}) is None
    assert _get_loinc_code({}) is None

def test_get_display():
    obs_resource = {"code": {"coding": [{"display": "Blood Pressure"}]}}
    assert _get_display(obs_resource) == "Blood Pressure"
    assert _get_display({"code": {"coding": []}}) is None
    assert _get_display({}) is None

def test_get_value():
    obs_resource = {"valueQuantity": {"value": 100.0}}
    assert _get_value(obs_resource) == 100.0
    assert _get_value({"valueQuantity": {}}) is None
    assert _get_value({}) is None

def test_get_unit():
    obs_resource = {"valueQuantity": {"unit": "kg"}}
    assert _get_unit(obs_resource) == "kg"
    assert _get_unit({"valueQuantity": {}}) is None
    assert _get_unit({}) is None

# --- End Unit Tests ---


if __name__ == "__main__":
    print("Running unit tests...")
    test_parse_fhir_bundle()
    test_get_postal_code()
    test_get_patient_ref()
    test_get_loinc_code()
    test_get_display()
    test_get_value()
    test_get_unit()
    print("Unit tests passed.\n")

    print("--- Example FHIR Bundle Parsing ---")
    patients_df, obs_df = parse_fhir_bundle(SYNTHETIC_FHIR_BUNDLE)
    print(f"Patients: {len(patients_df)} | Observations: {len(obs_df)}")
    print("\nPatients DataFrame:")
    print(patients_df.to_markdown(index=False))
    print("\nObservations DataFrame (first 5 rows):")
    print(obs_df[["loinc_code", "display", "value", "unit", "datetime"]].head().to_markdown(index=False))
    print("\nHuman-in-the-loop: Data Engineer validates FHIR bundle structure; Clinical Informaticist validates extracted data elements.")
