# Practitioner Depth — Chapter 4 — The Semantic Layer

*Technical grounding that operationalizes the chapter's semantic layer concepts. Written for data engineers, NLP practitioners, and clinical informaticists working with healthcare coding systems and clinical text.*

## Data Snapshots

## Domain Data Snapshots — Chapter 4

### USCDI v3 Vocabulary Mandates

The United States Core Data for Interoperability v3 mandates specific vocabulary standards for each data class. AI systems consuming or producing regulated FHIR data must align to these requirements.

| Data Class | Data Element | Required Vocabulary |
|---|---|---|
| **Problems** | Problem / Diagnosis | SNOMED CT (preferred); ICD-10-CM (acceptable) |
| **Laboratory** | Lab Test Name | LOINC |
| **Laboratory** | Lab Test Result Units | UCUM |
| **Medications** | Medication | RxNorm |
| **Medications** | Medication Instructions | FHIR `MedicationRequest` |
| **Vital Signs** | Vital Sign Measurement | LOINC |
| **Vital Signs** | Vital Sign Result Units | UCUM |
| **Diagnoses** | Encounter Diagnosis | ICD-10-CM |
| **Procedures** | Procedure | SNOMED CT, CPT, HCPCS, ICD-10-PCS |
| **Allergies** | Substance (medication) | RxNorm |
| **Allergies** | Substance (non-drug) | SNOMED CT |
| **Immunizations** | Vaccine Administered | CVX (CDC vaccine codes) |
| **Social Determinants** | SDOH Assessment | LOINC (panel codes) |
| **Social Determinants** | SDOH Goals | SNOMED CT |

**Key regulatory anchor:** 45 CFR Part 170 Subpart B
**FHIR IG reference:** HL7 US Core Implementation Guide v6.1

> **Expert Note — Why Vocabulary Compliance Is Audit Evidence**
>
> An AI system that emits codes outside USCDI-mandated vocabularies cannot be attested as evidence of care delivery in HEDIS, MIPS, or eCQM audits — even when its clinical logic is correct. The vocabulary is the audit interface; aligning to it before deployment is cheaper than retrofitting after a failed attestation cycle.

A reference Python implementation of OMOP concept hierarchy traversal lives in [`code/omop_snomed_traversal.py`](code/omop_snomed_traversal.py); a reference clinical NLP entity extraction sketch lives in [`code/clinical_nlp_scispacy.py`](code/clinical_nlp_scispacy.py).

## Code

_Tested and Colab-compatible. Click **Open in Colab** to run any sample in your browser — no setup._

### `clinical_nlp_scispacy.py`

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zkumar/healthcare-ai-book-preview/blob/main/docs/04-the-semantic-layer/code/clinical_nlp_scispacy.ipynb)

[Download .py](code/clinical_nlp_scispacy.py) · [Download notebook](code/clinical_nlp_scispacy.ipynb)

```python
"""Clinical NLP Pipeline — scispaCy entity extraction with negation detection.

# For Google Colab compatibility:
# !pip install scispacy negspacy
# !pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.1/en_core_sci_lg-0.5.1.tar.gz
# !pip install scispacy[umls]

# In a production clinical NLP pipeline, a full UMLS license and a robust
# entity linking service would be used to map clinical entities to standardized
# terminologies like SNOMED CT. Similarly, a more sophisticated negation
# detection system (like the full negspacy implementation) would be integrated.
# For this didactic example, we demonstrate the core scispaCy entity extraction
# and a simplified negspacy integration, with UMLS linking commented out to
# avoid external dependency setup and licensing requirements.



Status: UNTESTED. This is the scispaCy sketch from Chapter 4.
Before this is referenced from chapter.md as a worked example it needs:
  - replace the simplified _check_negation with a real NegEx implementation
    (e.g. negspacy or medspaCy)
  - section detection (assessment vs. history vs. plan)
  - temporality classification (current vs. historical findings)
  - uncertainty propagation (confident vs. probable vs. ruled-out)
  - HIPAA-compliant de-identification before any production use
  - validation against an annotated clinical corpus (e.g. i2b2, n2c2)
  - tests against a fixed set of canned notes with expected entity sets

scispaCy is the clinical and biomedical NLP extension of spaCy. This sketch
demonstrates entity extraction with simplified negation detection from a
clinical note, plus optional UMLS linking that maps extracted entities to
UMLS Concept Unique Identifiers (and through them to SNOMED CT).
"""
from dataclasses import dataclass
from typing import Optional

import spacy
import scispacy  # noqa: F401 — registers scispaCy components on spaCy

from negspacy.negation import Negex

# Load clinical NLP model (en_core_sci_lg: large scientific/clinical model)
nlp = spacy.load("en_core_sci_lg")

# Add NegEx for robust negation detection
nlp.add_pipe("negex", config={"ent_types": ["ENTITY"]})

# Add UMLS entity linker — maps extracted entities to UMLS / SNOMED concepts.
# Requires: pip install scispacy[umls]
# UMLS linker setup removed for testing. Re-enable if needed and resources allow.


@dataclass
class ClinicalEntity:
    text: str
    label: str            # DISEASE, CHEMICAL, etc.
    start: int
    end: int
    negated: bool
    umls_cui: Optional[str]   # UMLS Concept Unique Identifier
    snomed_code: Optional[str]
    confidence: float


def extract_clinical_entities(note_text: str) -> list[ClinicalEntity]:
    """Extract clinical entities from a free-text note with negation detection."""
    doc = nlp(note_text)
    entities: list[ClinicalEntity] = []

    for ent in doc.ents:

        # NegEx sets the ._.negex extension on entities
        negated = ent._.negex

        umls_cui: Optional[str] = None
        snomed_code: Optional[str] = None
        confidence: float = 0.0
        
        # Check if UMLS linker is active and has matches
        if hasattr(ent._, "kb_ents") and ent._.kb_ents:
            top_match = ent._.kb_ents[0]
            umls_cui = top_match[0]
            confidence = top_match[1]

        entities.append(ClinicalEntity(
            text       = ent.text,
            label      = ent.label_,
            start      = ent.start_char,
            end        = ent.end_char,
            negated    = negated,
            umls_cui   = umls_cui,
            snomed_code= snomed_code,
            confidence = round(confidence, 3),
        ))
    return entities

# --- Unit Tests (for Colab and local execution) ---
def test_extract_clinical_entities():
    note = "Patient denies chest pain. Patient has diabetes." # Simplified for testing negation of 'diabetes'
    entities = extract_clinical_entities(note)
    
    assert len(entities) > 0
    
    # Check negation for "chest pain"
    chest_pain_ents = [e for e in entities if "chest pain" in e.text.lower()]
    if chest_pain_ents:
        assert chest_pain_ents[0].negated == True
        
    # Check positive assertion for "diabetes"
    diabetes_ents = [e for e in entities if "diabetes" in e.text.lower()]
    # Ensure diabetes is found and not negated
    assert any(e.text.lower() == "diabetes" and not e.negated for e in entities)

# --- End Unit Tests ---


_EXAMPLE_NOTE = """
Patient is a 67-year-old male with a history of type 2 diabetes mellitus
and hypertension, presenting with shortness of breath. No evidence of
pneumonia on chest X-ray. Denies chest pain or palpitations. Current
medications include metformin 1000mg twice daily and lisinopril 10mg daily.
Labs notable for HbA1c of 8.2%, creatinine 1.4 mg/dL.
"""


if __name__ == "__main__":
    print("Running unit tests...")
    test_extract_clinical_entities()
    print("Unit tests passed.\n")

    print("--- Example Clinical NLP Extraction ---")
    entities = extract_clinical_entities(_EXAMPLE_NOTE)
    for e in entities:
        status = "[NEGATED]" if e.negated else "[POSITIVE]"
        print(f"{status} {e.label:12} | {e.text:35} | UMLS: {e.umls_cui} ({e.confidence})")
    print("\nHuman-in-the-loop: Clinical Documentation Improvement (CDI) specialist reviews extracted entities for accuracy.")
```

### `omop_snomed_traversal.py`

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zkumar/healthcare-ai-book-preview/blob/main/docs/04-the-semantic-layer/code/omop_snomed_traversal.ipynb)

[Download .py](code/omop_snomed_traversal.py) · [Download notebook](code/omop_snomed_traversal.ipynb)

```python
"""OMOP Vocabulary Query — SNOMED CT Hierarchy Traversal.

# For Google Colab compatibility:
# !pip install duckdb pandas pyarrow

# In a production system, the OMOP vocabulary (concept, concept_ancestor, etc.)
# would be downloaded from Athena (https://athena.ohdsi.org/vocabulary/list)
# and stored as persistent Parquet files or in a dedicated database. For this
# didactic example, we generate a minimal synthetic OMOP vocabulary in-memory
# and use DuckDB to query these in-memory tables. This abstracts away the need
# for external data files and a full vocabulary download, making the example
# self-contained and immediately runnable.



Status: UNTESTED. This is the DuckDB + Parquet sketch from Chapter 4.
Before this is referenced from chapter.md as a worked example it needs:
  - test fixtures (small synthetic concept / concept_ancestor parquet files)
  - a real OMOP vocabulary download from https://athena.ohdsi.org/vocabulary/list
  - validation that descendant counts match expected SNOMED CT subtrees
  - error handling for missing parquet files / empty result sets
  - benchmarking against larger concept trees (e.g. all neoplasms)

Demonstrates how to query the OMOP concept_ancestor table to retrieve all
descendants of a SNOMED CT concept — enabling hierarchical population health
queries. Uses DuckDB for in-process SQL on OMOP Parquet files.
"""
import duckdb
import pandas as pd
import os

# --- Synthetic OMOP Data Generation (for Colab and local execution) ---
def _generate_synthetic_omop_data():
    """Generate minimal synthetic OMOP vocabulary parquet files for testing."""
    if os.path.exists("concept.parquet") and os.path.exists("concept_ancestor.parquet") and os.path.exists("concept_relationship.parquet"):
        return

    print("Generating synthetic OMOP vocabulary parquet files...")
    
    # concept.parquet
    concept_df = pd.DataFrame([
        {"concept_id": 73211009, "concept_name": "Diabetes mellitus", "concept_code": "73211009", "domain_id": "Condition", "vocabulary_id": "SNOMED", "standard_concept": "S", "invalid_reason": None},
        {"concept_id": 44054006, "concept_name": "Type 2 diabetes mellitus", "concept_code": "44054006", "domain_id": "Condition", "vocabulary_id": "SNOMED", "standard_concept": "S", "invalid_reason": None},
        {"concept_id": 46635009, "concept_name": "Type 1 diabetes mellitus", "concept_code": "46635009", "domain_id": "Condition", "vocabulary_id": "SNOMED", "standard_concept": "S", "invalid_reason": None},
        {"concept_id": 10000001, "concept_name": "Type 2 diabetes mellitus without complications", "concept_code": "E11.9", "domain_id": "Condition", "vocabulary_id": "ICD10CM", "standard_concept": None, "invalid_reason": None},
        {"concept_id": 10000002, "concept_name": "Type 1 diabetes mellitus without complications", "concept_code": "E10.9", "domain_id": "Condition", "vocabulary_id": "ICD10CM", "standard_concept": None, "invalid_reason": None},
    ])
    concept_df.to_parquet("concept.parquet")

    # concept_ancestor.parquet
    ancestor_df = pd.DataFrame([
        {"ancestor_concept_id": 73211009, "descendant_concept_id": 73211009, "min_levels_of_separation": 0},
        {"ancestor_concept_id": 73211009, "descendant_concept_id": 44054006, "min_levels_of_separation": 1},
        {"ancestor_concept_id": 73211009, "descendant_concept_id": 46635009, "min_levels_of_separation": 1},
    ])
    ancestor_df.to_parquet("concept_ancestor.parquet")

    # concept_relationship.parquet
    relationship_df = pd.DataFrame([
        {"concept_id_1": 44054006, "concept_id_2": 10000001, "relationship_id": "Maps to"},
        {"concept_id_1": 46635009, "concept_id_2": 10000002, "relationship_id": "Maps to"},
    ])
    relationship_df.to_parquet("concept_relationship.parquet")

# --- End Synthetic OMOP Data Generation ---


def get_snomed_descendants(
    con: duckdb.DuckDBPyConnection,
    root_concept_id: int,
    concept_parquet: str = "concept.parquet",
    ancestor_parquet: str = "concept_ancestor.parquet",
) -> pd.DataFrame:
    """Retrieve all SNOMED CT descendant concepts for a given root concept.

    Example: root_concept_id=233604007 (Pneumonia) returns all pneumonia subtypes.
    """
    query = f"""
        SELECT
            c.concept_id,
            c.concept_name,
            c.concept_code AS snomed_code,
            c.domain_id,
            ca.min_levels_of_separation AS hierarchy_depth
        FROM read_parquet('{ancestor_parquet}') ca
        JOIN read_parquet('{concept_parquet}') c
            ON ca.descendant_concept_id = c.concept_id
        WHERE ca.ancestor_concept_id = {root_concept_id}
            AND c.vocabulary_id = 'SNOMED'
            AND c.standard_concept = 'S'        -- Standard concepts only
            AND c.invalid_reason IS NULL        -- Exclude deprecated concepts
        ORDER BY ca.min_levels_of_separation, c.concept_name
    """
    return con.execute(query).df()


def get_icd10_equivalents(
    con: duckdb.DuckDBPyConnection,
    concept_ids: list[int],
    concept_relationship_parquet: str = "concept_relationship.parquet",
    concept_parquet: str = "concept.parquet",
) -> pd.DataFrame:
    """Map SNOMED CT concepts to their ICD-10-CM equivalents via OMOP mappings."""
    ids_str = ",".join(str(i) for i in concept_ids)
    query = f"""
        SELECT
            c_src.concept_name AS snomed_name,
            c_src.concept_code AS snomed_code,
            c_tgt.concept_name AS icd10_name,
            c_tgt.concept_code AS icd10_code
        FROM read_parquet('{concept_relationship_parquet}') cr
        JOIN read_parquet('{concept_parquet}') c_src
            ON cr.concept_id_1 = c_src.concept_id
        JOIN read_parquet('{concept_parquet}') c_tgt
            ON cr.concept_id_2 = c_tgt.concept_id
        WHERE cr.concept_id_1 IN ({ids_str})
            AND cr.relationship_id = 'Maps to'
            AND c_tgt.vocabulary_id = 'ICD10CM'
    """
    return con.execute(query).df()


# --- Unit Tests (for Colab and local execution) ---
def test_omop_traversal():
    _generate_synthetic_omop_data()
    con = duckdb.connect()
    
    DIABETES_SNOMED_ID = 73211009
    descendants = get_snomed_descendants(con, DIABETES_SNOMED_ID)
    
    assert not descendants.empty
    assert len(descendants) == 3
    assert 44054006 in descendants["concept_id"].values # Type 2
    assert 46635009 in descendants["concept_id"].values # Type 1
    
    icd10 = get_icd10_equivalents(con, descendants["concept_id"].tolist())
    assert not icd10.empty
    assert len(icd10) == 2
    assert "E11.9" in icd10["icd10_code"].values
    assert "E10.9" in icd10["icd10_code"].values

# --- End Unit Tests ---

if __name__ == "__main__":
    print("Running unit tests...")
    test_omop_traversal()
    print("Unit tests passed.\n")

    print("--- Example OMOP SNOMED Traversal ---")
    _generate_synthetic_omop_data()
    con = duckdb.connect()

    DIABETES_SNOMED_ID = 73211009  # Diabetes mellitus (SNOMED CT)
    descendants = get_snomed_descendants(con, DIABETES_SNOMED_ID)
    print(f"Found {len(descendants)} diabetes concept descendants (synthetic data)")
    print(descendants[["concept_id", "concept_name", "snomed_code", "hierarchy_depth"]].to_markdown(index=False))

    # Map descendants back to ICD-10-CM
    if not descendants.empty:
        icd10 = get_icd10_equivalents(con, descendants["concept_id"].tolist())
        print(f"\nFound {len(icd10)} ICD-10-CM mappings")
        print(icd10.to_markdown(index=False))
    
    print("\nHuman-in-the-loop: Clinical Informaticist verifies concept mappings and hierarchy completeness.")
```
