import re

import numpy as np

from src.generation.schemas import Claim, Draft, Evidence, Segment, Slide, Transcript, Verdict


class DemoEncoder:
    """Small deterministic vocabulary for synthetic fixtures only, not real alignment."""
    vocabulary = ["gradient", "descent", "loss", "learning", "rate", "overfitting", "dropout", "training"]

    def encode(self, texts):
        values = np.array([[re.findall(r"\w+", text.lower()).count(word) for word in self.vocabulary]
                           for text in texts], dtype=float)
        return values / np.maximum(np.linalg.norm(values, axis=1, keepdims=True), 1e-12)


class ExtractiveGenerator:
    def generate(self, section, records):
        return Draft(title="Synthetic demonstration", claims=[
            Claim(kind="Core Idea", text=r["text"], evidence=[Evidence(source_id=sid, quote=r["text"])])
            for sid, r in records.items() if r["text"].strip()])

    def verify(self, claim):
        return Verdict(supported=False, reason="Demo only supports exact extraction")


def fixture():
    return Transcript(source_file="synthetic-lecture.wav", language="en", segments=[
        Segment(id="audio:0", start=872, end=915, text="Gradient descent updates parameters to reduce the loss."),
        Segment(id="audio:1", start=916, end=957, text="The learning rate affects gradient descent stability."),
        Segment(id="audio:2", start=1200, end=1235, text="Dropout can reduce overfitting during training.")]), [
            Slide(id="slide:12", source_file="synthetic-slides.pdf", page=12,
                  text="Gradient descent updates parameters to reduce the loss."),
            Slide(id="slide:15", source_file="synthetic-slides.pdf", page=15,
                  text="Dropout can reduce overfitting during training.")]
