def summarize(notes, alignments):
    accepted = sum(len(n.claims) for n in notes)
    rejected = sum(len(n.rejected) for n in notes)
    return {
        "sections": len(notes), "accepted_claims": accepted, "rejected_claims": rejected,
        "claim_acceptance_rate": accepted / (accepted + rejected) if accepted + rejected else None,
        "aligned_section_rate": sum(bool(a.matches) for a in alignments) / len(alignments) if alignments else None,
        "warning": "These are pipeline diagnostics, not factual accuracy or calibrated confidence.",
    }
