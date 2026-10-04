from src.generation.schemas import Segment, Settings, Transcript, Word


def transcribe(path: str, settings: Settings) -> Transcript:
    from faster_whisper import WhisperModel

    model = WhisperModel(settings.whisper_model, device=settings.whisper_device,
                         compute_type=settings.whisper_compute_type)
    segments, info = model.transcribe(path, language=settings.language,
                                      word_timestamps=True, vad_filter=True)
    rows = [Segment(id=f"audio:{i}", start=s.start, end=s.end, text=s.text.strip(),
                    words=[Word(start=w.start, end=w.end, text=w.word) for w in (s.words or [])])
            for i, s in enumerate(segments) if s.text.strip()]
    if not rows:
        raise ValueError("No speech detected in the audio.")
    return Transcript(source_file=str(path), language=info.language, segments=rows)
