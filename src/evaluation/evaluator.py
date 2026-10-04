import re

from src.generation.schemas import Note, VerifiedClaim


def normalize(text):
    return re.sub(r"\s+", " ", text).strip()


def verify_draft(section, draft, records, generator):
    accepted, rejected = [], []
    for index, claim in enumerate(draft.claims):
        reason = None
        for evidence in claim.evidence:
            record = records.get(evidence.source_id)
            quote = normalize(evidence.quote)
            if record is None or not quote or quote not in normalize(record["text"]):
                reason = "Unknown source or quote not found in source"
                break
        if claim.kind == "Lecturer's Explanation" and not any(
                records.get(e.source_id, {}).get("type") == "audio" for e in claim.evidence):
            reason = "Lecturer explanation requires audio evidence"
        method = "extractive"
        if reason is None and not any(normalize(claim.text) == normalize(e.quote) for e in claim.evidence):
            verdict = generator.verify(claim)
            method = "llm_supported"
            if not verdict.supported:
                reason = verdict.reason or "Unsupported by evidence"
        if reason:
            rejected.append(f"Claim {index + 1}: {reason}")
        else:
            accepted.append(VerifiedClaim(**claim.model_dump(), verification=method))
    # Never label an uncalibrated same-model verification result High.
    return Note(section_id=section.id, title=f"Section {section.id.split(':')[-1]}",
                claims=accepted, confidence="Medium" if accepted and not rejected else "Low",
                rejected=rejected)
