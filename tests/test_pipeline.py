import json
from pathlib import Path
import tempfile
import unittest

from pydantic import ValidationError

from src.demo import DemoEncoder, ExtractiveGenerator, fixture
from src.evaluation.evaluator import verify_draft
from src.generation.schemas import Claim, Draft, Evidence, Section, Segment, Settings, Slide
from src.pipeline import run
from src.processing.aligner import align
from src.processing.chunker import chunk_transcript
from src.processing.topic_segmenter import segment_topics


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.section = Section(id="section:0", start=0, end=10, segment_ids=["audio:0"], text="Loss decreases.")
        self.records = {"audio:0": {"type": "audio", "text": "Loss decreases."}}

    def verify(self, text, source="audio:0", quote="Loss decreases.", kind="Core Idea"):
        draft = Draft(title="Unverified title", claims=[Claim(kind=kind, text=text,
                      evidence=[Evidence(source_id=source, quote=quote)])])
        return verify_draft(self.section, draft, self.records, ExtractiveGenerator())

    def test_rejects_fabricated_source(self):
        self.assertFalse(self.verify("Loss decreases.", source="slide:999").claims)

    def test_rejects_fabricated_quote(self):
        self.assertFalse(self.verify("Loss increases.", quote="Loss increases.").claims)

    def test_rejects_unsupported_claim_with_real_quote(self):
        self.assertFalse(self.verify("Loss decreases by 90%.").claims)

    def test_rejects_whitespace_quote(self):
        self.assertFalse(self.verify("Anything", quote="  ").claims)

    def test_exact_extraction(self):
        note = self.verify("Loss decreases.")
        self.assertEqual(note.claims[0].verification, "extractive")
        self.assertNotEqual(note.confidence, "High")

    def test_slide_cannot_impersonate_lecturer(self):
        self.records["slide:1"] = {"type": "slide", "text": "Loss decreases."}
        self.assertFalse(self.verify("Loss decreases.", source="slide:1", kind="Lecturer's Explanation").claims)

    def test_invalid_time(self):
        with self.assertRaises(ValidationError):
            Segment(id="a", start=4, end=3, text="bad")

    def test_preserves_every_segment(self):
        transcript, _ = fixture()
        chunks = chunk_transcript(transcript, 45)
        sections = segment_topics(chunks, DemoEncoder(), Settings())
        self.assertEqual([sid for s in sections for sid in s.segment_ids], [s.id for s in transcript.segments])
        self.assertEqual(sections[0].start, 872)

    def test_alignment_abstains_on_empty_and_unrelated_slides(self):
        slides = [Slide(id="slide:1", source_file="s.pdf", page=1, text=""),
                  Slide(id="slide:2", source_file="s.pdf", page=2, text="unrelated")]
        self.assertEqual(align([self.section], slides, DemoEncoder(), Settings())[0].matches, [])

    def test_demo_end_to_end(self):
        with tempfile.TemporaryDirectory() as temp:
            settings = Settings(output_dir=f"{temp}/notes", processed_dir=f"{temp}/processed")
            markdown, md_path, json_path = run(demo=True, settings=settings)
            data = json.loads(Path(json_path).read_text(encoding="utf-8"))
            self.assertTrue(data["demo"])
            self.assertIn("14:32", markdown)
            self.assertIn("Slide 12", markdown)
            self.assertTrue(Path(md_path).exists())
            self.assertTrue(all(n["claims"] for n in data["notes"]))
            for note in data["notes"]:
                for claim in note["claims"]:
                    for evidence in claim["evidence"]:
                        self.assertIn(evidence["quote"], data["sources"][evidence["source_id"]]["text"])


if __name__ == "__main__":
    unittest.main()
