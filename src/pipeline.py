import argparse
import json
from pathlib import Path
from uuid import uuid4

import yaml

from src.audio.transcriber import transcribe
from src.documents.pdf_parser import parse_pdf
from src.documents.ppt_parser import parse_pptx
from src.evaluation.evaluator import verify_draft
from src.evaluation.metrics import summarize
from src.generation.markdown import render
from src.generation.note_generator import OllamaGenerator
from src.generation.schemas import DocumentSection, Settings, Transcript
from src.processing.aligner import align
from src.processing.chunker import chunk_transcript
from src.processing.topic_segmenter import SentenceEncoder, segment_topics


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def load_settings(path=None):
    if path is None:
        return Settings()
    return Settings.model_validate(yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {})


def run(*, title="Lecture Notes", audio=None, slides_path=None, transcript_path=None,
        settings=None, demo=False):
    settings = settings or Settings()
    if demo:
        from src.demo import DemoEncoder, ExtractiveGenerator, fixture
        transcript, slides = fixture()
        encoder, generator = DemoEncoder(), ExtractiveGenerator()
    else:
        if audio and transcript_path:
            raise ValueError("录音和转写 JSON 请只提供一种。")
        if not (audio or transcript_path or slides_path):
            raise ValueError("请上传录音或 PDF/PPTX 课件；也可以勾选合成演示。")
        transcript = (Transcript.model_validate_json(Path(transcript_path).read_text(encoding="utf-8"))
                      if transcript_path else transcribe(str(audio), settings) if audio else None)
        slides = []
        if slides_path:
            suffix = Path(slides_path).suffix.lower()
            if suffix not in {".pdf", ".pptx"}:
                raise ValueError("Slides must be PDF or PPTX.")
            slides = (parse_pdf if suffix == ".pdf" else parse_pptx)(str(slides_path))
        if transcript is None and not any(s.text.strip() for s in slides):
            raise ValueError("课件中没有可提取的文字。图片或扫描课件需要先进行 OCR，或上传课堂录音。")
        encoder = SentenceEncoder(settings.embedding_model) if transcript else None
        generator = OllamaGenerator(settings)

    run_id = uuid4().hex
    processed = Path(settings.processed_dir) / run_id
    output = Path(settings.output_dir) / run_id
    records = {s.id: {"type": "audio", "text": s.text, "start": s.start, "end": s.end,
                      "source_file": transcript.source_file} for s in transcript.segments} if transcript else {}
    records.update({s.id: {"type": "slide", **s.model_dump(exclude={"id"})} for s in slides})
    if transcript:
        save(processed / "transcripts/transcript.json", transcript.model_dump())
    save(processed / "slides/slides.json", [s.model_dump() for s in slides])
    if transcript:
        sections = segment_topics(chunk_transcript(transcript, settings.chunk_seconds), encoder, settings)
        alignments = align(sections, slides, encoder, settings)
        source_groups = [s.segment_ids + [m.slide_id for m in a.matches]
                         for s, a in zip(sections, alignments)]
    else:
        # One physical page per section; no fabricated audio timeline or similarity scores.
        sections = [DocumentSection(id=f"section:{s.page}", slide_ids=[s.id], text=s.text)
                    for s in slides if s.text.strip()]
        alignments = []
        source_groups = [s.slide_ids for s in sections]
    save(processed / "sections.json", [s.model_dump() for s in sections])
    save(processed / "alignments/alignments.json", [a.model_dump() for a in alignments])
    notes = []
    for section, ids in zip(sections, source_groups):
        evidence = {sid: records[sid] for sid in ids}
        draft = generator.generate(section, evidence)
        save(processed / f"drafts/{section.id.replace(':', '-')}.json", draft.model_dump())
        note = verify_draft(section, draft, evidence, generator)
        if not transcript:
            note.title = f"Slide {records[ids[0]]['page']}"
        notes.append(note)
    markdown = render(title, notes, records)
    output.mkdir(parents=True, exist_ok=True)
    md_path = output / "notes.md"
    json_path = output / "notes.json"
    md_path.write_text(markdown, encoding="utf-8")
    save(json_path, {"title": title, "demo": demo,
                     "input_mode": "audio" if transcript else "slides_only", "settings": settings.model_dump(),
                     "notes": [n.model_dump() for n in notes], "sources": records})
    save(output / "report.json", summarize(notes, alignments))
    return markdown, str(md_path.resolve()), str(json_path.resolve())


def main():
    parser = argparse.ArgumentParser(description="Generate evidence-backed local lecture notes")
    parser.add_argument("--audio")
    parser.add_argument("--transcript", help="Previously exported timestamped transcript JSON")
    parser.add_argument("--slides")
    parser.add_argument("--title", default="Lecture Notes")
    parser.add_argument("--config")
    parser.add_argument("--demo", action="store_true", help="Synthetic extractive demo; no model downloads")
    args = parser.parse_args()
    try:
        _, md, structured = run(title=args.title, audio=args.audio, slides_path=args.slides,
                                transcript_path=args.transcript, demo=args.demo,
                                settings=load_settings(args.config))
    except Exception as exc:
        parser.exit(1, f"Pipeline failed: {exc}\n")
    print(f"Markdown: {md}\nJSON: {structured}")


if __name__ == "__main__":
    main()
