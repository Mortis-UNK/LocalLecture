import numpy as np

from src.generation.schemas import Section, Settings


class SentenceEncoder:
    def __init__(self, model: str):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model)

    def encode(self, texts):
        return self.model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)


def segment_topics(chunks: list[Section], encoder, settings: Settings) -> list[Section]:
    if not chunks:
        return []
    vectors = encoder.encode([c.text for c in chunks])
    groups = [[chunks[0]]]
    for i, chunk in enumerate(chunks[1:], start=1):
        similarity = float(np.dot(vectors[i - 1], vectors[i]))
        if (similarity < settings.topic_threshold or
                chunk.end - groups[-1][0].start > settings.section_max_seconds):
            groups.append([])
        groups[-1].append(chunk)
    return [Section(id=f"section:{i}", start=g[0].start, end=max(c.end for c in g),
                    segment_ids=[sid for c in g for sid in c.segment_ids],
                    text=" ".join(c.text for c in g)) for i, g in enumerate(groups)]
