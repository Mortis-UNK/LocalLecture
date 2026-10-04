# LocalLecture

[English](README.md) | [简体中文](README.zh-CN.md)

**Evidence-grounded lecture note generation from audio and slide materials.**

LocalLecture is an independent Python project that generates structured lecture notes from recordings and PDF/PPTX materials using locally hosted models. Each accepted claim includes a source quotation and a reference to transcript timestamps or slide pages.

The prototype combines timestamped transcription, semantic topic segmentation, slide retrieval, structured generation, and evidence validation. It supports audio-only, slides-only, and combined inputs through a command-line pipeline and a local Gradio interface.

## Features

- **Timestamped transcription:** faster-whisper produces segment and word timestamps; chunking preserves the original transcript segments.
- **Semantic segmentation and retrieval:** Sentence Transformers embeddings group adjacent chunks and retrieve relevant slide text using cosine similarity and a thresholded top-k search.
- **Claim-level evidence:** Pydantic schemas require source IDs and quotations; validation checks source availability, quotation matching, and semantic support for paraphrased claims.
- **Traceable outputs:** Markdown citations use timestamps and page numbers from source records. JSON retains accepted claims, rejection reasons, settings, and source text.
- **Modular processing:** intermediate transcripts, parsed slides, sections, retrieval results, and drafts are saved for inspection.

Slide matching currently uses text similarity. It does not implement temporal synchronization between the recording and slide presentation, or visual understanding of slide images.

## Quick start: synthetic demo

Use Python 3.11 or 3.12. From the project root, run the following in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m src.pipeline --demo --title "Neural Networks (Synthetic Demo)"
```

This demo requires no recording, Ollama, or model downloads. It uses synthetic transcripts and slides, word-frequency vectors, and extractive generation to demonstrate pipeline behavior and source traceability. It does not evaluate real ASR, embedding retrieval, or LLM performance.

## Run with local models

Install the full dependencies and prepare Ollama:

```powershell
python -m pip install -r requirements.txt
ollama pull qwen3:4b
```

If Ollama is not already running, start `ollama serve` in another terminal. Run the combined pipeline:

```powershell
python -m src.pipeline --audio data/raw/audio/lecture.mp3 --slides data/raw/slides/lecture.pdf --title "Lecture Notes" --config config/config.yaml
```

For audio-only processing, omit `--slides`. For slides-only processing:

```powershell
python -m src.pipeline --slides data/raw/slides/lecture.pptx --title "Slide Notes" --config config/config.yaml
```

Launch the local interface:

```powershell
python -m app.gradio_app
```

Whisper and Sentence Transformers download models on first use. Once those models are cached and Ollama is ready, inference runs locally. The Gradio interface listens on the local machine without creating a public sharing link.

The default ASR configuration uses CPU/int8. GPU execution requires the appropriate faster-whisper runtime. To experiment with Qwen3 8B, download `qwen3:8b` and change `ollama_model` in the configuration. The CLI reads YAML through `--config`; the interface uses `Settings` defaults.

### Slides-only behavior

This mode requires Ollama but does not load Whisper or the embedding model. Notes are generated and validated for each page containing extractable text. Citations contain slide pages only; claims categorized as lecturer explanations require audio evidence and are rejected in this mode.

Blank pages retain their original page numbers but are skipped during generation. Documents with no extractable text produce an error requesting OCR or a recording. The exported JSON records `input_mode: slides_only`.

### Reuse an exported transcript

```powershell
python -m src.pipeline --transcript data/processed/<run-id>/transcripts/transcript.json --slides data/raw/slides/lecture.pptx
```

Replace `<run-id>` with a previous run ID.

## Evidence validation

1. Audio records use IDs such as `audio:N` and retain segment start/end times. Slide records use `slide:N` and one-based physical page numbers, independent of numbers printed on the slides.
2. Each generated claim must include a source ID and a quotation. References are restricted to the current section's audio records and retrieved slide candidates.
3. The validator checks that each source exists and that its quotation occurs in the source text after whitespace normalization.
4. Exact quoted claims pass deterministic checks; paraphrased claims are additionally checked for semantic support by Ollama.
5. Rejected claims are excluded from Markdown. Rejection reasons remain in JSON, and original drafts are saved separately.

Citations are rendered from source records rather than model-generated timestamps or page numbers. Retrieval similarity alone does not establish evidential support.

Confidence labels are uncalibrated: the maximum is `Medium`, and sections with rejections or no accepted claims receive `Low`. These labels are not probabilities of correctness. Generation and semantic verification use the same model and can share errors. Section titles use deterministic numbering; the lecture title is supplied by the user.

## Project structure and outputs

Each run receives a unique ID to avoid overwriting earlier results.

```text
config/config.yaml             Pipeline settings
src/audio/                     Timestamped transcription
src/documents/                 PDF/PPTX text extraction
src/processing/                Chunking, segmentation, slide retrieval
src/generation/                Schemas, Ollama generation, Markdown
src/evaluation/                Evidence validation and run metrics
src/pipeline.py                CLI and pipeline orchestration
app/gradio_app.py              Local upload/download interface
tests/                         Automated tests
experiments/                   Evaluation plans
data/raw/                      Local recordings and slide files
data/processed/<run-id>/
  transcripts/transcript.json  Transcript and timestamps
  slides/slides.json           Extracted page text
  sections.json                Sections
  alignments/alignments.json   Retrieved slide candidates
  drafts/                     Unverified generated drafts
outputs/notes/<run-id>/
  notes.md                    Notes with source references
  notes.json                  Claims, evidence, settings, rejections
  report.json                 Claim acceptance and alignment coverage
```

Raw materials, processed data, and generated outputs are excluded from Git by the existing `.gitignore`.

## Testing and current validation status

With the full dependencies installed, run:

```powershell
python -m unittest discover -s tests -v
```

The tests cover synthetic end-to-end processing, fabricated sources and quotations, unsupported claims, timestamp validation, segment preservation, abstention on unrelated slides, and slides-only processing. Document tests use generated PDF/PPTX fixtures and a substitute generator.

A saved slides-only run on real lecture materials is available locally. Real audio transcription and the combined audio/slide/Ollama pipeline still require end-to-end validation. Existing run metrics describe claim acceptance and retrieval coverage; they do not measure factual accuracy.

## Limitations and planned evaluation

- PPTX parsing extracts text, tables, and grouped shapes; the system does not interpret images, charts, or handwritten equations. PDF extraction uses per-page Markdown without a vision model. Image-only materials require suitable OCR preprocessing.
- The prototype does not perform speaker diarization, timestamp-linked audio playback, or merging of multiple slide decks.
- Segmentation and retrieval thresholds are initial experimental settings. Unmatched sections retain audio evidence without forcing a slide match.
- Chunking preserves complete ASR segments, so an unusually long segment can exceed the target duration. Oversized generation contexts raise an error rather than silently dropping evidence.
- Model and parsing failures are surfaced explicitly. Intermediate transcripts are saved before note generation.

Planned evaluation will use manually annotated lecture samples to compare audio-only and combined inputs, assess slide matching and source support, and investigate information coverage. Model comparisons and claims of improved reliability remain future work.

## Upstream references

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper): transcription, timestamps, and voice activity detection.
- [PyMuPDF4LLM API](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/api.html): per-page Markdown extraction.
- [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs): JSON Schema-constrained generation.
