import numpy as np

from src.generation.schemas import Alignment, Match, Settings


def align(sections, slides, encoder, settings: Settings):
    usable = [s for s in slides if s.text.strip()]
    if not usable:
        return [Alignment(section_id=s.id, matches=[]) for s in sections]
    section_vectors = encoder.encode([s.text for s in sections])
    slide_vectors = encoder.encode([s.text for s in usable])
    scores = np.clip(section_vectors @ slide_vectors.T, -1, 1)
    return [Alignment(section_id=section.id, matches=[
        Match(slide_id=usable[j].id, score=float(row[j]))
        for j in np.argsort(-row, kind="stable")[:settings.alignment_top_k]
        if row[j] >= settings.alignment_threshold])
        for section, row in zip(sections, scores)]
