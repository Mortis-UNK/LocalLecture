from src.generation.schemas import Section, Transcript


def chunk_transcript(transcript: Transcript, seconds: float) -> list[Section]:
    if seconds <= 0:
        raise ValueError("Chunk duration must be positive")
    chunks, group = [], []

    def flush():
        chunks.append(Section(id=f"chunk:{len(chunks)}", start=group[0].start,
                              end=max(s.end for s in group),
                              segment_ids=[s.id for s in group],
                              text=" ".join(s.text for s in group)))

    for segment in transcript.segments:
        if group and segment.end - group[0].start > seconds:
            flush()
            group = []
        group.append(segment)
    if group:
        flush()
    return chunks
