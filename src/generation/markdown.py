def timestamp(seconds):
    value = int(seconds)
    hours, remainder = divmod(value, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}" if hours else f"{minutes:02}:{seconds:02}"


def render(title, notes, records):
    lines = [f"# {title}", "", "> Automatically checked against supplied evidence; review before use.", ""]
    if records and all(r["type"] == "slide" for r in records.values()):
        lines += ["> Slides-only notes: based on slide text; no audio or lecturer explanation supplied.", ""]
    for i, note in enumerate(notes, 1):
        lines += [f"## {i}. {note.title}", ""]
        used = {}
        for claim in note.claims:
            refs = []
            for evidence in claim.evidence:
                used[evidence.source_id] = records[evidence.source_id]
                refs.append(f"`{evidence.source_id}`")
            lines += [f"### {claim.kind}", "", claim.text, "", "Evidence: " + ", ".join(refs), ""]
        if not note.claims:
            lines += ["No sufficiently supported claims; manual review required.", ""]
        lines += ["### Sources", ""]
        for sid, record in used.items():
            if record["type"] == "audio":
                label = f"🎧 {timestamp(record['start'])}–{timestamp(record['end'])}"
            else:
                label = f"📄 Slide {record['page']}"
            lines += [f"- {label} — {record['source_file']} (`{sid}`)"]
        lines += ["", "### Confidence", "", note.confidence,
                  "", "Evidence support only; ASR and same-model review can be wrong.", ""]
        if note.rejected:
            lines += [f"Omitted {len(note.rejected)} unsupported claim(s); see JSON audit.", ""]
    return "\n".join(lines)
