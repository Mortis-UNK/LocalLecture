import json

import httpx

from src.generation.prompts import GENERATE, VERIFY
from src.generation.schemas import Draft, Verdict


class OllamaGenerator:
    def __init__(self, settings):
        self.url = settings.ollama_url.rstrip("/") + "/api/chat"
        self.model = settings.ollama_model

    def structured(self, instruction, payload, schema):
        with httpx.Client(timeout=300) as client:
            response = client.post(self.url, json={
                "model": self.model, "stream": False, "think": False,
                "format": schema.model_json_schema(), "options": {"temperature": 0, "num_ctx": 16384},
                "messages": [{"role": "system", "content": instruction},
                             {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]})
            response.raise_for_status()
        return schema.model_validate_json(response.json()["message"]["content"])

    def generate(self, section, records):
        # Fail visibly instead of silently truncating evidence and losing provenance.
        if sum(len(s["text"]) for s in records.values()) > 18000:
            raise ValueError("Section evidence exceeds context budget; reduce chunk/section duration or alignment_top_k.")
        return self.structured(GENERATE, {"section": section.id, "records": records}, Draft)

    def verify(self, claim):
        return self.structured(VERIFY, claim.model_dump(), Verdict)
