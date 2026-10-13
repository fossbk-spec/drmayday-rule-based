"""Read canonical synthetic records without leaking fixture metadata to classifiers."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.knowledge import sha256_file


METADATA_KEYS = {"id", "nhan", "mo_ta", "expected_engine", "workflow_gap", "du_lieu"}


@dataclass
class Record:
    record_id: str
    snapshot: Any
    ground_truth: Optional[str]
    metadata: Dict[str, Any]
    error: Optional[str] = None


def load_records(paths) -> List[Record]:
    records = []
    for source in paths:
        path = Path(source)
        digest = sha256_file(path)
        metadata_base = {"file": str(path), "sha256": digest}
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            records.append(Record(f"{path.name}:#0", None, None, dict(metadata_base), type(exc).__name__))
            continue
        if isinstance(document, dict) and "cases" in document:
            cases = document["cases"]
        elif isinstance(document, list):
            cases = document
        else:
            cases = [document]
        if not isinstance(cases, list):
            records.append(Record(f"{path.name}:#0", None, None, dict(metadata_base), "InvalidCases"))
            continue
        seen = {}
        used_ids = set()
        for index, case in enumerate(cases):
            name = str(case.get("id", f"#{index}")) if isinstance(case, dict) else f"#{index}"
            seen[name] = seen.get(name, 0) + 1
            suffix_number = seen[name]
            candidate = name if suffix_number == 1 else f"{name}#{suffix_number}"
            while candidate in used_ids:
                suffix_number += 1
                candidate = f"{name}#{suffix_number}"
            used_ids.add(candidate)
            record_id = f"{path.name}:{candidate}"
            metadata = dict(metadata_base)
            if isinstance(case, dict):
                metadata.update({key: case[key] for key in METADATA_KEYS - {"du_lieu", "nhan"} if key in case})
            if candidate != name:
                metadata["duplicate_id"] = name
                metadata["duplicate_index"] = suffix_number
            snapshot = case.get("du_lieu") if isinstance(case, dict) and "du_lieu" in case else (
                {key: value for key, value in case.items() if key not in METADATA_KEYS}
                if isinstance(case, dict) else case
            )
            if isinstance(snapshot, dict):
                snapshot = {key: value for key, value in snapshot.items() if key not in METADATA_KEYS}
            records.append(Record(record_id, snapshot,
                                  case.get("nhan") if isinstance(case, dict) else None,
                                  metadata, None if isinstance(snapshot, dict) else "InvalidSnapshot"))
    return records
