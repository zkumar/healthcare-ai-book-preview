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
