from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Span(StrictModel):
    start: float = Field(ge=0)
    end: float = Field(ge=0)

    @model_validator(mode="after")
    def ordered(self):
        if self.end < self.start:
            raise ValueError("end must be >= start")
        return self


class Word(Span):
    text: str


class Segment(Span):
    id: str = Field(pattern=r"^audio:[0-9]+$")
    text: str = Field(min_length=1)
    words: list[Word] = Field(default_factory=list)


class Transcript(StrictModel):
    source_file: str
    language: str
    segments: list[Segment] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_segments(self):
        ids = [s.id for s in self.segments]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate segment IDs")
        if any(a.start > b.start for a, b in zip(self.segments, self.segments[1:])):
            raise ValueError("Segments must be chronological")
        return self


class Slide(StrictModel):
    id: str = Field(pattern=r"^slide:[0-9]+$")
    source_file: str
    page: int = Field(ge=1)
    text: str


class Section(Span):
    id: str
    segment_ids: list[str]
    text: str


class Match(StrictModel):
    slide_id: str
    score: float = Field(ge=-1, le=1)


class DocumentSection(StrictModel):
    id: str
    slide_ids: list[str]
    text: str


class Alignment(StrictModel):
    section_id: str
    matches: list[Match]


class Evidence(StrictModel):
    source_id: str
    quote: str = Field(min_length=1)


class Claim(StrictModel):
    kind: Literal["Core Idea", "Key Equation", "Lecturer's Explanation", "Example"]
    text: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)


class Draft(StrictModel):
    title: str = Field(min_length=1)
    claims: list[Claim]


class Verdict(StrictModel):
    supported: bool
    reason: str


class VerifiedClaim(Claim):
    verification: Literal["extractive", "llm_supported"]


class Note(StrictModel):
    section_id: str
    title: str
    claims: list[VerifiedClaim]
    confidence: Literal["Low", "Medium"]
    rejected: list[str]


class Settings(StrictModel):
    whisper_model: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    language: str | None = None
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:4b"
    chunk_seconds: float = Field(default=45, gt=0)
    section_max_seconds: float = Field(default=240, gt=0)
    topic_threshold: float = Field(default=0.55, ge=-1, le=1)
    alignment_threshold: float = Field(default=0.35, ge=-1, le=1)
    alignment_top_k: int = Field(default=3, ge=1)
    output_dir: str = "outputs/notes"
    processed_dir: str = "data/processed"
