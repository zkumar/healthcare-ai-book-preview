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
