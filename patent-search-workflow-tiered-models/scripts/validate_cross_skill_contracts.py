from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import validate_model_orchestration as orchestration


SKILLS_ROOT = Path(__file__).resolve().parents[2]
DRAFTING = SKILLS_ROOT / "cn-patent-drafting-workflow-tiered-models"
SEARCH = SKILLS_ROOT / "patent-search-workflow-tiered-models"
OA = SKILLS_ROOT / "cn-oa-reexam-opinion-drafting-tiered-models"
PAIRS = [
    ("search_context", DRAFTING / "assets/orchestration/search-context.template.json", SEARCH / "assets/orchestration/search-context.template.json", "search-context/2.0"),
    ("search_handoff", DRAFTING / "assets/orchestration/search-handoff.template.json", SEARCH / "assets/orchestration/search-handoff.template.json", "search-handoff/2.0"),
    ("oa_context", DRAFTING / "assets/orchestration/oa-context.template.json", OA / "assets/orchestration/oa-context.template.json", "oa-context/2.0"),
    ("oa_handoff", DRAFTING / "assets/orchestration/oa-handoff.template.json", OA / "assets/orchestration/oa-handoff.template.json", "oa-handoff/2.0"),
]
SCHEMA_PATH = "assets/orchestration/schemas/cross-skill-contracts.v2.schema.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare_pair(name: str, producer: dict[str, Any], consumer: dict[str, Any], schema: str, definition: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    normalized_producer = copy.deepcopy(producer); normalized_producer.pop("delivery_profile", None)
    normalized_consumer = copy.deepcopy(consumer); normalized_consumer.pop("delivery_profile", None)
    if normalized_producer != normalized_consumer:
        errors.append(f"{name}: producer and consumer templates are not byte-semantically identical")
    for side, value in [("producer", producer), ("consumer", consumer)]:
        orchestration.require_version(value, schema, f"{name}.{side}", errors)
        orchestration.validate_schema(value, definition, f"{name}.{side}", errors)
    if name.endswith("handoff"):
        if producer.get("output_class") != "candidate" or producer.get("authority_class") != "unverified":
            errors.append(f"{name}: unsafe handoff defaults")
        if name == "oa_handoff" and producer.get("recalculation_gate_passed") is not False:
            errors.append("oa_handoff: recalculation gate must default to false")
        if producer.get("writeback_objects") != []:
            errors.append(f"{name}: formal writeback objects must default to empty")
    return errors


def validate() -> list[str]:
    errors: list[str] = []
    schema_files = [DRAFTING / SCHEMA_PATH, SEARCH / SCHEMA_PATH, OA / SCHEMA_PATH]
    if len({digest(path) for path in schema_files if path.is_file()}) != 1 or not all(path.is_file() for path in schema_files):
        errors.append("cross-skill schema catalogs are missing or have drifted")
        return errors
    schemas = load(schema_files[0]).get("schemas", {})
    for name, producer_path, consumer_path, version in PAIRS:
        try:
            producer, consumer = load(producer_path), load(consumer_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{name}: cannot load contract: {exc}")
            continue
        if name not in schemas:
            errors.append(f"{name}: missing local schema")
            continue
        errors.extend(compare_pair(name, producer, consumer, version, schemas[name]))
    return errors


def run_negative_self_tests() -> list[str]:
    failures: list[str] = []
    schemas = load(DRAFTING / SCHEMA_PATH)["schemas"]
    for name, producer_path, _consumer_path, version in PAIRS:
        producer = load(producer_path)
        consumer = copy.deepcopy(producer)
        required = schemas[name].get("required", [])
        if required:
            consumer.pop(required[-1], None)
        if not compare_pair(name, producer, consumer, version, schemas[name]):
            failures.append(f"{name}: missing nested/required field was not detected")
        wrong = copy.deepcopy(producer)
        wrong["schema_version"] = "legacy/1.0"
        if not compare_pair(name, producer, wrong, version, schemas[name]):
            failures.append(f"{name}: legacy version was not detected")
        if name.endswith("handoff"):
            unsafe = copy.deepcopy(producer)
            unsafe["authority_class"] = "verified"
            unsafe["output_class"] = "approved_draft"
            if not compare_pair(name, unsafe, unsafe, version, schemas[name]):
                failures.append(f"{name}: unsafe defaults were not detected")
    return failures


def main() -> int:
    errors = validate() + run_negative_self_tests()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("V2 cross-skill schemas, templates, nested semantics, and negative tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
