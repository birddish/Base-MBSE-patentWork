from __future__ import annotations

import json
import tempfile
from pathlib import Path

import validate_model_orchestration as validator


LANGUAGES = ["zh", "en", "ja", "ko", "fr", "de"]
JURISDICTIONS = ["CN", "US", "JP", "KR", "EP", "WO"]


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def context(profile: str, mode: str) -> dict:
    payload = ({"solution_or_claim_feature_set_id": "FS-1", "feature_set_version": "1", "baseline_date": "2025-01-01"}
               if mode == "novelty" else
               {"product_spec_id": "PS-1", "product_spec_version": "1", "rights_territories": ["CN"], "legal_status_checked_at": "2026-01-01T00:00:00Z"})
    return {"schema_version": "search-context/lightweight-1.0", "delivery_profile": profile,
            "case_id": "CASE-1", "mode": mode, "mode_payload": payload,
            "required_languages": LANGUAGES, "required_jurisdictions": JURISDICTIONS,
            "feature_set_id": "FS-1", "input_scope": "test", "source_files": []}


def handoff(profile: str, mode: str, documents: list[dict] | None = None) -> dict:
    return {"schema_version": "search-handoff/lightweight-1.0", "delivery_profile": profile,
            "case_id": "CASE-1", "mode": mode,
            "queries": [{"query_text": "test query", "database": "TEST", "executed_at": "2026-01-01T00:00:00Z"}],
            "raw_result_files": ["sources/results.json"],
            "jurisdiction_distribution": {key: 0 for key in JURISDICTIONS},
            "documents": documents or [], "evidence_links": [], "risk_register": []}


def errors_for(profile: str, mode: str, documents: list[dict] | None = None) -> list[str]:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        write_json(root / "search_context.json", context(profile, mode))
        write_json(root / "search_handoff.json", handoff(profile, mode, documents))
        errors: list[str] = []
        validator.validate_lightweight_runtime(root, errors)
        return errors


def main() -> int:
    assert not errors_for("quick", "novelty")
    assert not errors_for("standard", "fto", [{"risk_candidate": True, "legal_status": "active"}])
    assert any("X/Y/A" in error for error in errors_for("quick", "novelty", [{"classification": "X"}]))
    assert any("lacks legal_status" in error for error in errors_for("standard", "fto", [{"risk_candidate": True}]))
    print("Quick/standard delivery-profile tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
