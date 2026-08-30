from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
NAME = ROOT.name
KIND = "search" if NAME.startswith("patent-search") else "oa" if NAME.startswith("cn-oa-reexam") else "drafting"
WORKFLOW = {"drafting": "cn-patent-drafting", "search": "patent-search", "oa": "cn-oa-reexam"}[KIND]
SKILL_WORKFLOWS = {"cn-patent-drafting-workflow-tiered-models": "cn-patent-drafting",
                   "patent-search-workflow-tiered-models": "patent-search",
                   "cn-oa-reexam-opinion-drafting-tiered-models": "cn-oa-reexam"}
PACKAGE_ORCHESTRATION_STATUS = "enabled"
TIER_OUTPUTS = {
    "Luna": {"extraction", "raw_hit"},
    "Terra": {"candidate", "review", "candidate_match"},
    "Sol": {"review", "approved_draft", "verified_finding"},
}
TIER_ROOTS = {"Luna": "staging/luna", "Terra": "staging/terra", "Sol": "reviewed/sol"}
TRUSTED_MODEL_IDS = {"Luna": ["gpt-5.6-luna"], "Terra": ["gpt-5.6-terra"], "Sol": ["gpt-5.6-sol"]}
TRUSTED_ISSUER = "codex-controller-v2"
TRUSTED_KEY_ID = "codex-controller-rsa-2026-01"
TRUSTED_RSA_EXPONENT = 65537
# Replaced during the release build with the fixed controller public modulus. The private key is never stored in a Skill.
TRUSTED_RSA_MODULUS = 17796352908666486129782375122690613600616706866544980558696902031605090024558621890644147886973080047559137830999319497913568262889883380950496378726359417213447664017579088753741880211696050044342387027794172907245208635426986649361940346866920863893493730958570133334663620021389056645507995825365945866614551539226795491162515082873477460514517073645642938317107682352391406132758746904211986773392609144468408387343860902004724378828998684767686596701715334797888004156471838111801430857358339825293131534041767815472237240411898215424165077320790443902024633041073032312200139110789645709564364102208190597591189
ATTORNEY_ISSUER = "codex-attorney-attestation-v2"
ATTORNEY_KEY_ID = "codex-attorney-rsa-2026-01"
ATTORNEY_RSA_MODULUS = 22053787741618299466120853526306604255476145451434408961997057169615729802109349299191617374486919761503018936529805789836228726533844046670503826846080663404078892285120724854565389526000329419802446291635836395608284892078497231738626305313507750730489375930782789849997655665638059196362594163068345476584356140191597745044298712820824551252389881412073583782854675629306164595841551240771453484211673673389666777012468243534650819572163340311457608363071916345366367966087246058649849821585889016701359095950866015064539313090519731653669380662190822978622348500608136062710037787966062513111358230429889534955899
RSA_SHA256_PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")
FORMAL_CLASSES = {"approved_draft", "verified_finding"}
FORMAL_OBJECT_TYPES = {"NB", "IS", "ACTIVE_CLAIM_SET", "CONFIRMED_CLAIM", "ATTORNEY_CONFIRMATION"}
BASE_FILES = [
    "SKILL.md", "references/model-routing-contract.md", "references/context-and-handoff-contract.md",
    "assets/orchestration/case-context-manifest.template.json", "assets/orchestration/task-context.template.json",
    "assets/orchestration/task-handoff.template.json", "assets/orchestration/routing-ledger.template.json",
    "assets/orchestration/invalidation-ledger.template.json", "assets/orchestration/model-registry.template.json",
    "assets/orchestration/execution-record.template.json", "assets/orchestration/attorney-confirmation.template.json",
    "assets/orchestration/controller-trust-store.template.json",
    "assets/orchestration/schemas/common-contracts.v2.schema.json",
    "assets/orchestration/schemas/cross-skill-contracts.v2.schema.json",
]
KIND_FILES = {
    "drafting": ["references/stage-model-io-contract.md", "references/cross-skill-adapters.md",
                  "assets/orchestration/search-context.template.json", "assets/orchestration/search-handoff.template.json",
                  "assets/orchestration/oa-context.template.json", "assets/orchestration/oa-handoff.template.json"],
    "search": ["references/search-context-contract.md", "references/query-contract.md",
                "references/search-invalidation-rules.md", "assets/orchestration/search-context.template.json",
                "assets/orchestration/search-handoff.template.json",
                "assets/orchestration/query-definition.template.json", "assets/orchestration/query-run.template.json"],
    "oa": ["references/oa-context-and-parallel-contract.md", "references/version-and-recalculation-gates.md",
            "assets/orchestration/oa-context-manifest.template.json", "assets/orchestration/oa-context.template.json",
            "assets/orchestration/oa-handoff.template.json"],
}


def load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path}: invalid JSON: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path}: top-level value must be an object")
        return {}
    return value


def canonical_bytes(value: Any, excluded: set[str] | None = None) -> bytes:
    excluded = excluded or set()

    def strip(item: Any) -> Any:
        if isinstance(item, dict):
            return {key: strip(item[key]) for key in sorted(item) if key not in excluded}
        if isinstance(item, list):
            return [strip(child) for child in item]
        return item

    return json.dumps(strip(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_sha256(value: Any, excluded: set[str] | None = None) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value, excluded)).hexdigest()


def raw_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def is_hash(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 71 or not value.startswith("sha256:"):
        return False
    try:
        int(value[7:], 16)
        return True
    except ValueError:
        return False


def safe_path(root: Path, relative: Any, label: str, errors: list[str]) -> Path | None:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        errors.append(f"{label}: path must be a non-empty relative path")
        return None
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        errors.append(f"{label}: path escapes run directory: {relative!r}")
        return None
    return candidate


def validate_schema(value: Any, schema: dict[str, Any], label: str, errors: list[str]) -> None:
    expected_type = schema.get("type")
    accepted = expected_type if isinstance(expected_type, list) else [expected_type]
    checks = {
        "object": lambda item: isinstance(item, dict), "array": lambda item: isinstance(item, list),
        "string": lambda item: isinstance(item, str), "boolean": lambda item: isinstance(item, bool),
        "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool), "null": lambda item: item is None,
    }
    if expected_type is not None and not any(checks.get(kind, lambda _item: False)(value) for kind in accepted):
        errors.append(f"{label}: expected type {expected_type!r}")
        return
    if "const" in schema and value != schema["const"]:
        errors.append(f"{label}: expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{label}: value {value!r} is outside {schema['enum']!r}")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{label}: missing required field {key!r}")
        for key, child in schema.get("properties", {}).items():
            if key in value:
                validate_schema(value[key], child, f"{label}.{key}", errors)
    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            validate_schema(item, schema["items"], f"{label}[{index}]", errors)


def catalog(filename: str, errors: list[str]) -> dict[str, Any]:
    value = load_json(ROOT / "assets/orchestration/schemas" / filename, errors)
    if not isinstance(value.get("schemas"), dict):
        errors.append(f"{filename}: missing schemas object")
        return {}
    return value["schemas"]


def require_version(value: dict[str, Any], expected: str, label: str, errors: list[str]) -> None:
    actual = value.get("schema_version")
    legacy = {
        "multi-model-orchestration/1.0", "multi-model-task/1.0", "multi-model-handoff/1.0",
        "multi-model-routing/1.0", "multi-model-invalidation/1.0", "multi-model-execution/1.0",
        "search-context/1.0", "search-handoff/1.0", "oa-context/1.0", "oa-handoff/1.0",
        "v2.1-oa", "oa-model-context/1.0",
    }
    if actual in legacy:
        errors.append(f"{label}: legacy schema {actual!r} is unsupported; create a new V2 run directory (no migration is provided)")
    elif actual != expected:
        errors.append(f"{label}: schema_version must be {expected!r}, got {actual!r}")


def validate_static(errors: list[str]) -> None:
    for relative in [*BASE_FILES, *KIND_FILES[KIND]]:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required file: {relative}")
    skill_path = ROOT / "SKILL.md"
    if skill_path.is_file():
        skill = skill_path.read_text(encoding="utf-8")
        for needle in ["execution_mode", "task_context.json", "task_handoff.json", "multi-model-orchestration/2.0"]:
            if needle not in skill:
                errors.append(f"SKILL.md missing V2 orchestration rule: {needle}")
    for path in (ROOT / "assets/orchestration").rglob("*.json"):
        load_json(path, errors)
    common = catalog("common-contracts.v2.schema.json", errors)
    cross = catalog("cross-skill-contracts.v2.schema.json", errors)
    for name, filename in {
        "case_context_manifest": "case-context-manifest.template.json", "task_context": "task-context.template.json",
        "task_handoff": "task-handoff.template.json", "routing_ledger": "routing-ledger.template.json",
        "invalidation_ledger": "invalidation-ledger.template.json", "model_registry": "model-registry.template.json",
        "execution_record": "execution-record.template.json", "attorney_confirmation": "attorney-confirmation.template.json",
        "controller_trust_store": "controller-trust-store.template.json",
    }.items():
        path = ROOT / "assets/orchestration" / filename
        if path.is_file() and name in common:
            validate_schema(load_json(path, errors), common[name], filename, errors)
    for name, filename in {"search_context": "search-context.template.json", "search_handoff": "search-handoff.template.json",
                           "oa_context": "oa-context.template.json", "oa_handoff": "oa-handoff.template.json"}.items():
        path = ROOT / "assets/orchestration" / filename
        if path.is_file() and name in cross:
            validate_schema(load_json(path, errors), cross[name], filename, errors)


def validate_file_records(run_dir: Path, records: Any, label: str, errors: list[str]) -> list[str]:
    output: list[str] = []
    if not isinstance(records, list):
        errors.append(f"{label}: expected an array")
        return output
    for index, record in enumerate(records):
        item_label = f"{label}[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{item_label}: expected object")
            continue
        if not isinstance(record.get("version"), str):
            errors.append(f"{item_label}: missing string version")
        if not is_hash(record.get("sha256")):
            errors.append(f"{item_label}: invalid sha256")
        path = safe_path(run_dir, record.get("path"), item_label, errors)
        if path is None:
            continue
        relative = str(record["path"]).replace("\\", "/")
        output.append(relative)
        if not path.is_file():
            errors.append(f"{item_label}: file does not exist: {relative}")
        elif is_hash(record.get("sha256")) and raw_sha256(path) != record["sha256"]:
            errors.append(f"{item_label}: raw file SHA-256 mismatch")
    return output


def file_record_keys(records: Any) -> set[tuple[str, str, str]]:
    if not isinstance(records, list):
        return set()
    return {
        (str(item.get("path", "")).replace("\\", "/"), str(item.get("version", "")), str(item.get("sha256", "")))
        for item in records if isinstance(item, dict)
    }


def validate_snapshot(run_dir: Path, manifest: dict[str, Any], errors: list[str]) -> None:
    snapshot = manifest.get("active_snapshot")
    if not isinstance(snapshot, dict):
        return
    validate_file_records(run_dir, snapshot.get("inputs"), "case.active_snapshot.inputs", errors)
    expected = canonical_sha256({"id": snapshot.get("id"), "inputs": snapshot.get("inputs")})
    if snapshot.get("hash") != expected:
        errors.append("case active_snapshot.hash does not match normalized inputs")


def open_invalidation(ledger: dict[str, Any], task_id: str, context: dict[str, Any], handoff: dict[str, Any]) -> str | None:
    task_ids = {task_id, *(handoff.get("depends_on") or [])}
    object_ids = set(context.get("input_object_ids") or [])
    snapshot_ids = {context.get("input_snapshot_id")}
    paths = {item.get("path") for item in handoff.get("generated_files") or [] if isinstance(item, dict)}
    for event in ledger.get("events") or []:
        if not isinstance(event, dict) or event.get("status") not in {"open", "active"}:
            continue
        if task_ids.intersection(event.get("affected_task_ids") or []) or object_ids.intersection(event.get("affected_object_ids") or []):
            return str(event.get("event_id") or "open-event")
        if snapshot_ids.intersection(event.get("affected_snapshot_ids") or []) or paths.intersection(event.get("affected_output_paths") or []):
            return str(event.get("event_id") or "open-event")
    return None


def invalidation_hash(ledger: dict[str, Any]) -> str:
    return canonical_sha256(ledger)


def validate_invalidation_ledger(ledger: dict[str, Any], case_id: Any, label: str, errors: list[str]) -> None:
    if ledger.get("case_id") != case_id or not isinstance(ledger.get("revision"), int) or ledger.get("revision") < 0:
        errors.append(f"{label}: invalid case_id/revision")
    allowed_status = {"open", "active", "applied", "resolved", "closed"}
    for index, event in enumerate(ledger.get("events") or []):
        if not isinstance(event, dict) or not event.get("event_id") or event.get("status") not in allowed_status:
            errors.append(f"{label}.events[{index}]: invalid event identity/status")


def release_state_hash(manifest: dict[str, Any], invalidation: dict[str, Any]) -> str:
    return canonical_sha256({
        "case_id": manifest.get("case_id"), "workflow": manifest.get("workflow"),
        "execution_mode": manifest.get("execution_mode"), "orchestration_status": manifest.get("orchestration_status"),
        "current_stage": manifest.get("current_stage"), "active_snapshot": manifest.get("active_snapshot"),
        "evidence_pack": manifest.get("evidence_pack"), "blocked_by": manifest.get("blocked_by"),
        "invalidation_ledger_hash": invalidation_hash(invalidation), "invalidation_revision": invalidation.get("revision"),
    })


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def verify_crypto(value: dict[str, Any], expected_issuer: str, expected_key_id: str, modulus: int,
                  id_field: str, label: str, errors: list[str]) -> bool:
    if value.get("issuer") != expected_issuer or value.get("key_id") != expected_key_id:
        errors.append(f"{label}: signed object has an untrusted issuer/key")
        return False
    identifier = value.get(id_field)
    if not isinstance(identifier, str) or not identifier:
        errors.append(f"{label}: signed object ID is missing")
        return False
    issued, expires = parse_time(value.get("issued_at")), parse_time(value.get("expires_at"))
    now = datetime.now(timezone.utc)
    if issued is None or expires is None or issued > now or expires <= now or issued >= expires or not value.get("nonce"):
        errors.append(f"{label}: signed object time window/nonce is invalid")
        return False
    try:
        signature = base64.b64decode(value.get("signature", ""), validate=True)
        size = (modulus.bit_length() + 7) // 8
        decoded = pow(int.from_bytes(signature, "big"), TRUSTED_RSA_EXPONENT, modulus).to_bytes(size, "big")
    except Exception:
        errors.append(f"{label}: malformed controller signature")
        return False
    digest = hashlib.sha256(canonical_bytes(value, {"signature"})).digest()
    padding_length = size - len(RSA_SHA256_PREFIX) - len(digest) - 3
    expected = b"\x00\x01" + b"\xff" * padding_length + b"\x00" + RSA_SHA256_PREFIX + digest
    if padding_length < 8 or decoded != expected:
        errors.append(f"{label}: controller signature verification failed")
        return False
    return True


def validate_trust_store(trust_store: dict[str, Any] | None, label: str, errors: list[str]) -> bool:
    if not trust_store:
        errors.append(f"{label}: a controller-signed external trust store is required")
        return False
    required_arrays = ["execution_receipts", "release_receipts", "authorization_receipts", "revoked_receipt_ids"]
    if (trust_store.get("schema_version") != "controller-trust/1.0"
            or trust_store.get("issuer") != TRUSTED_ISSUER or trust_store.get("key_id") != TRUSTED_KEY_ID
            or trust_store.get("model_registry") != TRUSTED_MODEL_IDS
            or not isinstance(trust_store.get("revision"), int)
            or any(not isinstance(trust_store.get(field), list) for field in required_arrays)):
        errors.append(f"{label}: controller trust store identity/schema/model registry is invalid")
        return False
    return verify_crypto(trust_store, TRUSTED_ISSUER, TRUSTED_KEY_ID, TRUSTED_RSA_MODULUS,
                         "store_id", f"{label}.trust_store", errors)


def verify_signature(value: dict[str, Any], trust_store: dict[str, Any] | None, label: str, errors: list[str],
                     id_field: str = "receipt_id") -> bool:
    if not validate_trust_store(trust_store, label, errors):
        return False
    identifier = value.get(id_field)
    if identifier in set(trust_store.get("revoked_receipt_ids") or []):
        errors.append(f"{label}: signed object ID is missing or revoked")
        return False
    expected_issuer = ATTORNEY_ISSUER if id_field == "confirmation_id" else TRUSTED_ISSUER
    expected_key_id = ATTORNEY_KEY_ID if id_field == "confirmation_id" else TRUSTED_KEY_ID
    modulus = ATTORNEY_RSA_MODULUS if id_field == "confirmation_id" else TRUSTED_RSA_MODULUS
    return verify_crypto(value, expected_issuer, expected_key_id, modulus, id_field, label, errors)


def trusted_receipt(record: dict[str, Any], trust_store: dict[str, Any] | None, label: str, errors: list[str]) -> None:
    if not validate_trust_store(trust_store, label, errors):
        return
    receipt = next((item for item in trust_store.get("execution_receipts", []) if isinstance(item, dict)
                    and item.get("execution_record_id") == record.get("execution_record_id")), None)
    fields = ["execution_record_id", "record_hash", "case_id", "task_id", "workflow", "stage", "source_skill",
              "actual_model_id", "actual_model_tier", "task_context_hash", "task_handoff_hash", "output_hash",
              "cross_handoff_hash", "invalidation_ledger_hash", "invalidation_revision"]
    if not receipt or any(receipt.get(field) != record.get(field) for field in fields):
        errors.append(f"{label}: no execution receipt binds the full controller record/input/output")
        return
    verify_signature(receipt, trust_store, label, errors)


def trusted_authorization(context: dict[str, Any], trust_store: dict[str, Any] | None, label: str,
                          errors: list[str]) -> None:
    if not validate_trust_store(trust_store, label, errors):
        return
    receipt_id = context.get("authorization_receipt_id")
    receipt = next((item for item in trust_store.get("authorization_receipts", []) if isinstance(item, dict)
                    and item.get("receipt_id") == receipt_id), None)
    fields = ["case_id", "source_task_id", "source_skill", "target_skill", "context_hash",
              "upstream_snapshot_id", "upstream_snapshot_hash", "target_active_snapshot_id",
              "target_active_snapshot_hash", "source_manifest_hash", "target_manifest_hash",
              "source_stage", "target_stage", "allowed_writeback"]
    if not receipt or any(receipt.get(field) != context.get(field) for field in fields):
        errors.append(f"{label}: no signed upstream authorization binds this context/writeback scope")
        return
    verify_signature(receipt, trust_store, label, errors)


def trusted_release(manifest: dict[str, Any], invalidation: dict[str, Any], trust_store: dict[str, Any] | None,
                    errors: list[str]) -> None:
    if manifest.get("orchestration_status") != "enabled":
        return
    if not validate_trust_store(trust_store, "Gate-2 release", errors):
        return
    receipt = next((item for item in trust_store.get("release_receipts", []) if isinstance(item, dict)
                    and item.get("case_id") == manifest.get("case_id") and item.get("workflow") == manifest.get("workflow")
                    and item.get("release_gate") == "gate-2" and item.get("audit_status") == "no-p0-p1"
                    and item.get("active_snapshot_hash") == (manifest.get("active_snapshot") or {}).get("hash")
                    and item.get("release_state_hash") == release_state_hash(manifest, invalidation)
                    and item.get("invalidation_ledger_hash") == invalidation_hash(invalidation)
                    and item.get("invalidation_revision") == invalidation.get("revision")), None)
    if not receipt:
        errors.append("enabled orchestration lacks a matching signed Gate-2 release receipt")
        return
    verify_signature(receipt, trust_store, "Gate-2 release", errors)


def validate_execution(run_dir: Path, context: dict[str, Any], handoff: dict[str, Any], registry: dict[str, Any],
                       routing: dict[str, Any], invalidation: dict[str, Any], trust_store: dict[str, Any] | None,
                       label: str, errors: list[str]) -> None:
    record_id = handoff.get("execution_record_id")
    if not isinstance(record_id, str) or not record_id:
        errors.append(f"{label}: orchestrated task missing execution_record_id")
        return
    path = run_dir / "execution_records" / f"{record_id}.json"
    if not path.is_file():
        errors.append(f"{label}: controller execution record is missing")
        return
    record = load_json(path, errors)
    require_version(record, "multi-model-execution/2.0", str(path), errors)
    schema = catalog("common-contracts.v2.schema.json", errors).get("execution_record")
    if schema:
        validate_schema(record, schema, str(path), errors)
    expected_hash = canonical_sha256(record, {"record_hash"})
    if record.get("record_hash") != expected_hash or handoff.get("execution_record_hash") != expected_hash:
        errors.append(f"{label}: execution record hash mismatch")
    expected_cross_hash = None
    for filename in ["search_handoff.json", "oa_handoff.json"]:
        candidate_path = run_dir / filename
        if candidate_path.is_file():
            candidate = load_json(candidate_path, errors)
            if candidate.get("review_task_id") == context.get("task_id") and candidate.get("execution_record_id") == record_id:
                expected_cross_hash = candidate.get("handoff_hash")
    expected = {
        "execution_record_id": record_id, "case_id": context.get("case_id"), "task_id": context.get("task_id"),
        "workflow": context.get("workflow"), "stage": context.get("stage"), "source_skill": ROOT.name,
        "assigned_tier": context.get("assigned_tier"), "actual_model_id": handoff.get("actual_model_id"),
        "actual_model_tier": handoff.get("actual_model_tier"), "input_snapshot_id": context.get("input_snapshot_id"),
        "input_snapshot_hash": context.get("input_snapshot_hash"),
        "task_context_hash": context.get("task_context_hash"), "task_handoff_hash": handoff.get("task_handoff_hash"),
        "output_hash": handoff.get("output_hash"), "cross_handoff_hash": expected_cross_hash,
        "invalidation_ledger_hash": invalidation_hash(invalidation), "invalidation_revision": invalidation.get("revision"),
    }
    for key, value in expected.items():
        if record.get(key) != value:
            errors.append(f"{label}: execution record {key} mismatch")
    if record.get("controller") != "orchestrator":
        errors.append(f"{label}: execution record is not controller-owned")
    tiers = registry.get("tiers") if isinstance(registry.get("tiers"), dict) else {}
    if record.get("actual_model_id") not in tiers.get(record.get("actual_model_tier"), []):
        errors.append(f"{label}: actual_model_id is not allowed by model registry")
    valid_route = any(isinstance(event, dict) and event.get("case_id") == context.get("case_id")
                      and event.get("task_id") == context.get("task_id") and event.get("assigned_tier") == context.get("assigned_tier")
                      and event.get("actual_model_id") == record.get("actual_model_id")
                      and event.get("actual_model_tier") == record.get("actual_model_tier")
                      and event.get("source_skill") == ROOT.name and event.get("controller") == "orchestrator"
                      and event.get("execution_record_id") == record_id and event.get("status") in {"approved", "executed", "active"}
                      for event in routing.get("events") or [])
    if not valid_route:
        errors.append(f"{label}: no valid controller routing event")
    trusted_receipt(record, trust_store, label, errors)


def validate_task(run_dir: Path, task_dir: Path, manifest: dict[str, Any], routing: dict[str, Any], invalidation: dict[str, Any],
                  registry: dict[str, Any], trust_store: dict[str, Any] | None, errors: list[str]) -> None:
    label = task_dir.name
    context_path, handoff_path = task_dir / "task_context.json", task_dir / "task_handoff.json"
    if not context_path.is_file() or not handoff_path.is_file():
        errors.append(f"{label}: context/handoff pair is incomplete")
        return
    context, handoff = load_json(context_path, errors), load_json(handoff_path, errors)
    require_version(context, "multi-model-task/2.0", str(context_path), errors)
    require_version(handoff, "multi-model-handoff/2.0", str(handoff_path), errors)
    common = catalog("common-contracts.v2.schema.json", errors)
    validate_schema(context, common.get("task_context", {}), str(context_path), errors)
    validate_schema(handoff, common.get("task_handoff", {}), str(handoff_path), errors)
    expected_context_hash = canonical_sha256(context, {"task_context_hash"})
    if context.get("task_context_hash") != expected_context_hash:
        errors.append(f"{label}: task_context_hash mismatch")
    expected_handoff_hash = canonical_sha256(handoff, {"task_handoff_hash", "execution_record_hash"})
    if handoff.get("task_handoff_hash") != expected_handoff_hash:
        errors.append(f"{label}: task_handoff_hash mismatch")
    shared = ["case_id", "task_id", "workflow", "stage", "execution_mode", "assigned_tier", "task_context_hash", "input_snapshot_id", "input_snapshot_hash"]
    for key in shared:
        if context.get(key) != handoff.get(key):
            errors.append(f"{label}: context/handoff {key} mismatch")
    if context.get("task_id") != label:
        errors.append(f"{label}: task_id must match task directory")
    for key in ["case_id", "workflow", "execution_mode"]:
        if context.get(key) != manifest.get(key):
            errors.append(f"{label}: task {key} does not match case manifest")
    if context.get("stage") != manifest.get("current_stage"):
        errors.append(f"{label}: task stage is not the case current_stage")
    snapshot = manifest.get("active_snapshot") or {}
    if context.get("input_snapshot_id") != snapshot.get("id") or context.get("input_snapshot_hash") != snapshot.get("hash"):
        errors.append(f"{label}: task does not use active case snapshot")
    validate_file_records(run_dir, context.get("source_inputs"), f"{label}.source_inputs", errors)
    if not file_record_keys(context.get("source_inputs")).issubset(file_record_keys(snapshot.get("inputs"))):
        errors.append(f"{label}: task source_inputs include files outside the active snapshot")
    generated = validate_file_records(run_dir, handoff.get("generated_files"), f"{label}.generated_files", errors)
    if handoff.get("output_hash") != canonical_sha256(handoff.get("generated_files") or []):
        errors.append(f"{label}: output_hash mismatch")
    if handoff.get("output_class") != context.get("expected_output_class") or handoff.get("result_class") != context.get("expected_result_class"):
        errors.append(f"{label}: output/result class does not match task context")
    tier = handoff.get("actual_model_tier") or context.get("assigned_tier")
    for value in [handoff.get("output_class"), handoff.get("result_class")]:
        if tier not in TIER_OUTPUTS or (value is not None and value not in TIER_OUTPUTS[tier]):
            errors.append(f"{label}: tier {tier!r} cannot emit {value!r}")
    merge_target = handoff.get("merge_target")
    merge_path = safe_path(run_dir, merge_target, f"{label}.merge_target", errors)
    target = str(merge_target).replace("\\", "/").rstrip("/") if isinstance(merge_target, str) else ""
    allowlist = [str(item).replace("\\", "/").rstrip("/") for item in context.get("merge_allowlist") or [] if isinstance(item, str)]
    if not any(target == item or target.startswith(item + "/") for item in allowlist):
        errors.append(f"{label}: merge_target outside allowlist")
    if merge_path:
        for relative in generated:
            try:
                (run_dir / relative).resolve().relative_to(merge_path)
            except ValueError:
                errors.append(f"{label}: generated file outside merge_target: {relative}")
    fixed_root = TIER_ROOTS.get(str(tier))
    if fixed_root:
        if not allowlist or any(item != fixed_root and not item.startswith(fixed_root + "/") for item in allowlist):
            errors.append(f"{label}: task merge allowlist exceeds fixed {tier} root {fixed_root}")
        if target != fixed_root and not target.startswith(fixed_root + "/"):
            errors.append(f"{label}: merge_target exceeds fixed {tier} root {fixed_root}")
        for relative in generated:
            if relative != fixed_root and not relative.startswith(fixed_root + "/"):
                errors.append(f"{label}: generated file exceeds fixed {tier} root: {relative}")
    expected_paths = {str(item).replace("\\", "/") for item in context.get("expected_outputs") or []}
    if expected_paths != set(generated):
        errors.append(f"{label}: generated files do not exactly match expected_outputs")
    lower_tier = tier in {"Luna", "Terra"}
    object_types = {item.get("object_type") for item in handoff.get("generated_files") or [] if isinstance(item, dict)}
    formal_path = any(path.startswith(("confirmed/", "approved/", "formal/", "active/")) or path == "patent_evidence_pack.json" for path in generated)
    if lower_tier and (object_types & FORMAL_OBJECT_TYPES or formal_path):
        errors.append(f"{label}: lower-tier formal write is forbidden")
    if KIND == "search" and lower_tier:
        for relative in generated:
            if Path(relative).suffix.lower() != ".json":
                errors.append(f"{label}: lower-tier search output must use the controlled JSON format")
            elif lower_tier_search_payload_has_formal_content(run_dir / relative):
                errors.append(f"{label}: lower-tier search output contains formal X/Y/A or NB/IS content")
    if lower_tier and handoff.get("proposed_status") in {"reviewed", "confirmed", "approved", "active"}:
        errors.append(f"{label}: lower-tier formal status is forbidden")
    mode = context.get("execution_mode")
    if mode == "advisory":
        for key in ["actual_model_id", "actual_model_tier", "execution_record_id", "execution_record_hash"]:
            if handoff.get(key) is not None:
                errors.append(f"{label}: advisory handoff must leave {key} null")
        if handoff.get("authority_class") != "unverified" or handoff.get("output_class") in FORMAL_CLASSES or handoff.get("result_class") in FORMAL_CLASSES:
            errors.append(f"{label}: advisory output cannot be verified/formal")
    elif mode == "orchestrated":
        if handoff.get("actual_model_tier") != context.get("assigned_tier"):
            errors.append(f"{label}: actual tier differs from controller assignment")
        validate_execution(run_dir, context, handoff, registry, routing, invalidation, trust_store, label, errors)
    formal = handoff.get("output_class") in FORMAL_CLASSES or handoff.get("result_class") in FORMAL_CLASSES
    if formal and (tier != "Sol" or handoff.get("authority_class") != "verified"):
        errors.append(f"{label}: formal output requires verified Sol")
    if formal and manifest.get("orchestration_status") != "enabled":
        errors.append(f"{label}: formal output blocked while orchestration is not enabled")
    legal_formal = (handoff.get("output_class") == "approved_draft" or handoff.get("result_class") == "approved_draft"
                    or bool(object_types & FORMAL_OBJECT_TYPES))
    if legal_formal:
        required_artifacts = [{"artifact_id": str(item.get("object_id") or item.get("path")),
                               "path": item.get("path"), "version": item.get("version"), "sha256": item.get("sha256")}
                              for item in handoff.get("generated_files") or [] if isinstance(item, dict)]
        snapshot = manifest.get("active_snapshot") or {}
        confirmation_stage = context.get("stage")
        required_scope = {"approved_draft"}
        if KIND == "oa":
            oa_path = run_dir / "oa_context_manifest.json"
            oa_manifest = load_json(oa_path, errors) if oa_path.is_file() else {}
            snapshot = {"id": oa_manifest.get("oa_active_snapshot_id"), "hash": oa_manifest.get("oa_active_snapshot_hash")}
            required_scope.add("oa_v2.2")
            required_artifacts.append({"artifact_id": str(oa_manifest.get("active_claim_set_id")), "path": "",
                                       "version": "active", "sha256": oa_manifest.get("active_claim_set_hash")})
            pack = manifest.get("evidence_pack") or {}
            required_artifacts.append({"artifact_id": str(pack.get("path")), "path": pack.get("path"),
                                       "version": pack.get("schema_version"), "sha256": pack.get("sha256")})
        validate_attorney_confirmation(run_dir, handoff.get("attorney_confirmation_id"), manifest.get("case_id"),
                                       snapshot.get("id"), snapshot.get("hash"), confirmation_stage,
                                       required_artifacts, required_scope, trust_store, label, errors)
    event = open_invalidation(invalidation, label, context, handoff)
    if event:
        errors.append(f"{label}: open invalidation event {event!r} affects task")
    if handoff.get("lifecycle_status") != "active" or handoff.get("blocked_for_merge"):
        errors.append(f"{label}: stale/invalidated/superseded or blocked handoff cannot merge")


def validate_cross_execution(run_dir: Path, manifest: dict[str, Any], task_id: Any, record_id: Any, record_hash: Any,
                             registry: dict[str, Any], routing: dict[str, Any], invalidation: dict[str, Any],
                             trust_store: dict[str, Any] | None, expected_workflow: str, label: str, errors: list[str]) -> dict[str, Any]:
    if not all(isinstance(item, str) and item for item in [task_id, record_id, record_hash]):
        errors.append(f"{label}: review task/execution record provenance is incomplete")
        return {}
    source_skill = "patent-search-workflow-tiered-models" if expected_workflow == "patent-search" else "cn-oa-reexam-opinion-drafting-tiered-models"
    source_invalidation = skill_invalidation(run_dir, invalidation, source_skill, manifest.get("case_id"), label, errors)
    path = (run_dir / "execution_records" / f"{record_id}.json") if WORKFLOW == expected_workflow else (
        run_dir / "external_execution_records" / source_skill / f"{record_id}.json"
    )
    if not path.is_file():
        errors.append(f"{label}: referenced controller execution record is missing")
        return {}
    record = load_json(path, errors)
    require_version(record, "multi-model-execution/2.0", str(path), errors)
    expected_hash = canonical_sha256(record, {"record_hash"})
    if record.get("record_hash") != expected_hash or record_hash != expected_hash:
        errors.append(f"{label}: referenced execution record hash mismatch")
    if record.get("case_id") != manifest.get("case_id") or record.get("task_id") != task_id or record.get("execution_record_id") != record_id:
        errors.append(f"{label}: referenced execution record identity mismatch")
    expected_source_skill = "patent-search-workflow-tiered-models" if expected_workflow == "patent-search" else "cn-oa-reexam-opinion-drafting-tiered-models"
    if record.get("workflow") != expected_workflow or record.get("source_skill") != expected_source_skill:
        errors.append(f"{label}: referenced execution record belongs to the wrong workflow/skill")
    if record.get("controller") != "orchestrator" or record.get("actual_model_tier") != "Sol":
        errors.append(f"{label}: verified/formal cross-skill result requires controller-owned Sol execution")
    tiers = registry.get("tiers") if isinstance(registry.get("tiers"), dict) else {}
    if record.get("actual_model_id") not in tiers.get("Sol", []):
        errors.append(f"{label}: Sol model id is not allowed by registry")
    task_dir = provenance_task_dir(run_dir, task_id, expected_workflow, source_skill)
    context_path, handoff_path = task_dir / "task_context.json", task_dir / "task_handoff.json"
    if not context_path.is_file() or not handoff_path.is_file():
        errors.append(f"{label}: referenced Sol review task context/handoff is missing")
    else:
        context, handoff = load_json(context_path, errors), load_json(handoff_path, errors)
        shared = ["case_id", "task_id", "workflow", "stage", "execution_mode", "assigned_tier", "task_context_hash", "input_snapshot_id", "input_snapshot_hash"]
        if any(context.get(field) != handoff.get(field) for field in shared):
            errors.append(f"{label}: referenced Sol review task context/handoff mismatch")
        if context.get("task_context_hash") != canonical_sha256(context, {"task_context_hash"}):
            errors.append(f"{label}: referenced Sol review task context hash mismatch")
        if handoff.get("task_handoff_hash") != canonical_sha256(handoff, {"task_handoff_hash", "execution_record_hash"}):
            errors.append(f"{label}: referenced Sol review task handoff hash mismatch")
        if handoff.get("output_hash") != canonical_sha256(handoff.get("generated_files") or []):
            errors.append(f"{label}: referenced Sol review output hash mismatch")
        source_manifest = skill_manifest(run_dir, manifest, source_skill, label, errors)
        snapshot = source_manifest.get("active_snapshot") or {}
        if context.get("case_id") != manifest.get("case_id") or context.get("workflow") != expected_workflow:
            errors.append(f"{label}: referenced Sol review task belongs to the wrong case/workflow")
        if context.get("input_snapshot_id") != snapshot.get("id") or context.get("input_snapshot_hash") != snapshot.get("hash"):
            errors.append(f"{label}: referenced Sol review task does not use the active snapshot")
        if record.get("input_snapshot_id") != context.get("input_snapshot_id") or record.get("input_snapshot_hash") != context.get("input_snapshot_hash"):
            errors.append(f"{label}: execution record snapshot differs from the referenced review task")
        for field, expected in [("task_context_hash", context.get("task_context_hash")),
                                ("task_handoff_hash", handoff.get("task_handoff_hash")),
                                ("output_hash", handoff.get("output_hash")),
                                ("invalidation_ledger_hash", invalidation_hash(source_invalidation)),
                                ("invalidation_revision", source_invalidation.get("revision"))]:
            if record.get(field) != expected:
                errors.append(f"{label}: execution record {field} differs from the referenced review task")
        if context.get("assigned_tier") != "Sol" or handoff.get("actual_model_tier") != "Sol" or handoff.get("authority_class") != "verified":
            errors.append(f"{label}: referenced review task is not an active verified Sol task")
        if handoff.get("execution_mode") != "orchestrated" or handoff.get("actual_model_id") != record.get("actual_model_id"):
            errors.append(f"{label}: referenced review task model/execution mode differs from controller record")
        if record.get("assigned_tier") != "Sol" or record.get("actual_model_tier") != "Sol":
            errors.append(f"{label}: controller record does not prove a Sol-assigned review")
        if handoff.get("execution_record_id") != record_id or handoff.get("execution_record_hash") != record_hash:
            errors.append(f"{label}: review task handoff does not bind the cited execution record")
        if handoff.get("lifecycle_status") != "active" or handoff.get("blocked_for_merge"):
            errors.append(f"{label}: referenced review task is stale/invalidated/blocked")
        event = open_invalidation(source_invalidation, str(task_id), context, handoff)
        if event:
            errors.append(f"{label}: referenced review task is affected by open invalidation event {event}")
    valid_route = any(isinstance(event, dict) and event.get("case_id") == manifest.get("case_id")
                      and event.get("task_id") == task_id and event.get("assigned_tier") == "Sol"
                      and event.get("actual_model_id") == record.get("actual_model_id") and event.get("actual_model_tier") == "Sol"
                      and event.get("source_skill") == source_skill and event.get("controller") == "orchestrator"
                      and event.get("execution_record_id") == record_id
                      and event.get("status") in {"approved", "executed", "active"} for event in routing.get("events") or [])
    if not valid_route:
        errors.append(f"{label}: referenced cross-skill review task has no controller route")
    trusted_receipt(record, trust_store, label, errors)
    return record


def provenance_task_dir(run_dir: Path, task_id: Any, expected_workflow: str, source_skill: str) -> Path:
    if WORKFLOW == expected_workflow:
        return run_dir / "tasks" / str(task_id)
    return run_dir / "external_tasks" / source_skill / str(task_id)


def skill_manifest(run_dir: Path, local_manifest: dict[str, Any], skill_name: str, label: str,
                   errors: list[str]) -> dict[str, Any]:
    if skill_name == ROOT.name:
        return local_manifest
    path = run_dir / "external_manifests" / skill_name / "case_context_manifest.json"
    if not path.is_file():
        errors.append(f"{label}: external active case manifest is missing for {skill_name}")
        return {}
    value = load_json(path, errors)
    require_version(value, "multi-model-orchestration/2.0", str(path), errors)
    schema = catalog("common-contracts.v2.schema.json", errors).get("case_context_manifest")
    if schema:
        validate_schema(value, schema, str(path), errors)
    if value.get("workflow") != SKILL_WORKFLOWS.get(skill_name) or value.get("case_id") != local_manifest.get("case_id"):
        errors.append(f"{label}: external case manifest workflow/case identity mismatch")
    if not value.get("current_stage"):
        errors.append(f"{label}: external case manifest current_stage is missing")
    validate_snapshot(run_dir, value, errors)
    return value


def manifest_hash(value: dict[str, Any]) -> str:
    return canonical_sha256(value)


def skill_invalidation(run_dir: Path, local_ledger: dict[str, Any], skill_name: str, case_id: Any,
                       label: str, errors: list[str]) -> dict[str, Any]:
    if skill_name == ROOT.name:
        return local_ledger
    path = run_dir / "external_manifests" / skill_name / "invalidation_ledger.json"
    if not path.is_file():
        errors.append(f"{label}: external invalidation ledger is missing for {skill_name}")
        return {}
    value = load_json(path, errors)
    require_version(value, "multi-model-invalidation/2.0", str(path), errors)
    validate_invalidation_ledger(value, case_id, str(path), errors)
    return value


def validate_cross_snapshots(run_dir: Path, value: dict[str, Any], source_skill: str, target_skill: str,
                             local_manifest: dict[str, Any], label: str,
                             errors: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    source_manifest = skill_manifest(run_dir, local_manifest, source_skill, label, errors)
    target_manifest = skill_manifest(run_dir, local_manifest, target_skill, label, errors)
    source_snapshot = source_manifest.get("active_snapshot") or {}
    target_snapshot = target_manifest.get("active_snapshot") or {}
    if (value.get("case_id") != source_manifest.get("case_id")
            or value.get("upstream_snapshot_id") != source_snapshot.get("id")
            or value.get("upstream_snapshot_hash") != source_snapshot.get("hash")):
        errors.append(f"{label}: upstream snapshot is not the source Skill active snapshot")
    if (value.get("case_id") != target_manifest.get("case_id")
            or value.get("target_active_snapshot_id") != target_snapshot.get("id")
            or value.get("target_active_snapshot_hash") != target_snapshot.get("hash")):
        errors.append(f"{label}: target active snapshot is not the target Skill active snapshot")
    if (value.get("source_manifest_hash") != manifest_hash(source_manifest)
            or value.get("source_stage") != source_manifest.get("current_stage")):
        errors.append(f"{label}: source Skill manifest hash/stage mismatch")
    if (value.get("target_manifest_hash") != manifest_hash(target_manifest)
            or value.get("target_stage") != target_manifest.get("current_stage")):
        errors.append(f"{label}: target Skill manifest hash/stage mismatch")
    return source_manifest, target_manifest


def validate_attorney_confirmation(run_dir: Path, confirmation_id: Any, case_id: Any, snapshot_id: Any,
                                   snapshot_hash: Any, expected_stage: Any, required_artifacts: list[dict[str, Any]],
                                   required_scope: set[str], trust_store: dict[str, Any] | None,
                                   label: str, errors: list[str]) -> None:
    if not isinstance(confirmation_id, str) or not confirmation_id:
        errors.append(f"{label}: attorney_confirmation_id is required")
        return
    path = run_dir / "attorney_confirmations" / f"{confirmation_id}.json"
    if not path.is_file():
        errors.append(f"{label}: attorney confirmation record is missing")
        return
    confirmation = load_json(path, errors)
    require_version(confirmation, "attorney-confirmation/1.0", str(path), errors)
    schema = catalog("common-contracts.v2.schema.json", errors).get("attorney_confirmation")
    if schema:
        validate_schema(confirmation, schema, str(path), errors)
    if confirmation.get("confirmation_id") != confirmation_id or confirmation.get("case_id") != case_id:
        errors.append(f"{label}: attorney confirmation identity mismatch")
    if confirmation.get("snapshot_id") != snapshot_id or confirmation.get("snapshot_hash") != snapshot_hash:
        errors.append(f"{label}: attorney confirmation snapshot mismatch")
    if confirmation.get("stage") != expected_stage:
        errors.append(f"{label}: attorney confirmation stage mismatch")
    if (confirmation.get("confirmed_by_role") != "patent_attorney" or confirmation.get("attorney_confirmed") is not True
            or not confirmation.get("confirmed_by") or not confirmation.get("confirmed_at")
            or not confirmation.get("confirmation_scope")):
        errors.append(f"{label}: confirmation was not made by a patent attorney")
    refs: set[tuple[str, str, str, str]] = set()
    for index, item in enumerate(confirmation.get("artifact_refs") or []):
        item_label = f"{label}.attorney_artifact_refs[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{item_label}: expected object")
            continue
        artifact_id, version, digest = item.get("artifact_id"), item.get("version"), item.get("sha256")
        relative = str(item.get("path") or "").replace("\\", "/")
        if not artifact_id or not version or not is_hash(digest):
            errors.append(f"{item_label}: artifact_id/version/sha256 are required")
        if relative:
            artifact_path = safe_path(run_dir, relative, item_label, errors)
            if artifact_path is None or not artifact_path.is_file() or (artifact_path.is_file() and raw_sha256(artifact_path) != digest):
                errors.append(f"{item_label}: confirmed artifact file/hash is invalid")
        refs.add((str(artifact_id), relative, str(version), str(digest)))
    required = {(str(item.get("artifact_id")), str(item.get("path") or "").replace("\\", "/"),
                 str(item.get("version")), str(item.get("sha256"))) for item in required_artifacts}
    if not required or not required.issubset(refs):
        errors.append(f"{label}: attorney confirmation does not cover every formal artifact")
    if not required_scope.issubset(set(confirmation.get("confirmation_scope") or [])):
        errors.append(f"{label}: attorney confirmation scope is insufficient")
    verify_signature(confirmation, trust_store, label, errors, id_field="confirmation_id")


def search_snapshot_hash(value: dict[str, Any]) -> str:
    findings = []
    for item in value.get("verified_findings") or []:
        if isinstance(item, dict):
            findings.append({key: child for key, child in item.items()
                             if key not in {"review_task_id", "execution_record_id", "execution_record_hash"}})
    payload = {
        "search_snapshot_id": value.get("search_snapshot_id"),
        "feature_set_hash": value.get("feature_set_hash"),
        "pst_boundary_signature": value.get("pst_boundary_signature"),
        "query_run_ids": value.get("query_run_ids") or [],
        "query_run_refs": value.get("query_run_refs") or [],
        "documents": value.get("documents") or [],
        "evidence_links": value.get("evidence_links") or [],
        "verified_findings": findings,
        "writeback_objects": value.get("writeback_objects") or [],
        "invalidated_object_ids": value.get("invalidated_object_ids") or [],
    }
    return canonical_sha256(payload)


def validate_search_mode_context(value: dict[str, Any], label: str, errors: list[str]) -> None:
    required = {
        "novelty": {"solution_or_claim_feature_set_id", "feature_set_version", "baseline_date"},
        "invalidity": {"target_patent", "active_claim_set_id", "active_claim_set_version", "baseline_date"},
        "fto": {"product_spec_id", "product_spec_version", "rights_territories", "legal_status_checked_at"},
        "landscape": {"collection_boundary", "time_window", "inclusion_rules", "exclusion_rules", "cleaning_version"},
    }
    mode = value.get("mode")
    payload = value.get("mode_payload")
    if mode not in required or not isinstance(payload, dict):
        errors.append(f"{label}: invalid search mode/mode_payload")
    else:
        missing = sorted(field for field in required[mode] if payload.get(field) in (None, "", []))
        if missing:
            errors.append(f"{label}: mode_payload missing {', '.join(missing)}")
        foreign = (set().union(*required.values()) - required[mode]).intersection(payload)
        if foreign:
            errors.append(f"{label}: mode_payload contains fields from another mode: {', '.join(sorted(foreign))}")
        if mode in {"novelty", "invalidity"}:
            try:
                datetime.fromisoformat(str(payload.get("baseline_date")))
            except ValueError:
                errors.append(f"{label}: baseline_date must be an ISO date")
        if mode == "fto":
            if not isinstance(payload.get("rights_territories"), list) or not all(isinstance(item, str) and item for item in payload.get("rights_territories", [])):
                errors.append(f"{label}: rights_territories must be a non-empty string array")
            if parse_time(payload.get("legal_status_checked_at")) is None:
                errors.append(f"{label}: legal_status_checked_at must be an ISO timestamp")
        if mode == "landscape":
            if not isinstance(payload.get("time_window"), dict) or not payload["time_window"].get("start") or not payload["time_window"].get("end"):
                errors.append(f"{label}: time_window must contain start/end")
            for field in ["inclusion_rules", "exclusion_rules"]:
                if not isinstance(payload.get(field), list):
                    errors.append(f"{label}: {field} must be an array")
    languages = set(value.get("required_languages") or [])
    jurisdictions = set(value.get("required_jurisdictions") or [])
    reduced = languages != {"zh", "en", "ja", "ko", "fr", "de"} or jurisdictions != {"CN", "US", "JP", "KR", "EP", "WO"}
    authorization = value.get("scope_reduction_authorization")
    if reduced and not (isinstance(authorization, dict) and authorization.get("authorized_by")
                        and authorization.get("authorized_at") and authorization.get("reason")):
        errors.append(f"{label}: six-language/six-jurisdiction reduction lacks structured authorization")
    approved = value.get("approved_query_ids") or []
    if len(approved) != len(set(approved)):
        errors.append(f"{label}: approved_query_ids contains duplicates")


def query_record_path(run_dir: Path, category: str, identifier: Any, label: str, errors: list[str]) -> Path | None:
    if not isinstance(identifier, str) or not identifier or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for character in identifier):
        errors.append(f"{label}: invalid query identifier")
        return None
    return safe_path(run_dir, f"queries/{category}/{identifier}.json", label, errors)


def validate_query_definitions(run_dir: Path, context: dict[str, Any], label: str,
                               errors: list[str]) -> dict[str, dict[str, Any]]:
    approved_ids = context.get("approved_query_ids") or []
    refs = context.get("approved_query_definitions") or []
    if not isinstance(refs, list):
        errors.append(f"{label}: approved_query_definitions must be an array")
        return {}
    ref_map = {item.get("query_id"): item.get("definition_hash") for item in refs if isinstance(item, dict)}
    if set(ref_map) != set(approved_ids) or len(ref_map) != len(refs):
        errors.append(f"{label}: approved query IDs and definition references differ")
    definitions: dict[str, dict[str, Any]] = {}
    for query_id in approved_ids:
        item_label = f"{label}.query[{query_id}]"
        path = query_record_path(run_dir, "definitions", query_id, item_label, errors)
        if path is None or not path.is_file():
            errors.append(f"{item_label}: immutable query definition is missing")
            continue
        value = load_json(path, errors)
        expected_hash = canonical_sha256(value, {"definition_hash"})
        if (value.get("schema_version") != "query-definition/1.0" or value.get("query_id") != query_id
                or value.get("case_id") != context.get("case_id") or value.get("mode") != context.get("mode")
                or value.get("feature_set_hash") != context.get("feature_set_hash")
                or value.get("definition_hash") != expected_hash or ref_map.get(query_id) != expected_hash):
            errors.append(f"{item_label}: definition identity/hash/context mismatch")
        if not value.get("query_text") or not value.get("approval_task_id") or not value.get("approved_by") or not value.get("approved_at"):
            errors.append(f"{item_label}: query text or approval record is incomplete")
        if set(value.get("languages") or []) != set(context.get("required_languages") or []) or set(value.get("jurisdictions") or []) != set(context.get("required_jurisdictions") or []):
            errors.append(f"{item_label}: language/jurisdiction scope differs from search context")
        definitions[str(query_id)] = value
    return definitions


def validate_query_runs(run_dir: Path, context: dict[str, Any], handoff: dict[str, Any],
                        registry: dict[str, Any], label: str, errors: list[str]) -> None:
    definitions = validate_query_definitions(run_dir, context, label, errors)
    tiers = registry.get("tiers") or {}
    refs = handoff.get("query_run_refs") or []
    ref_map = {item.get("run_id"): item.get("run_hash") for item in refs if isinstance(item, dict)}
    run_ids = handoff.get("query_run_ids") or []
    if set(ref_map) != set(run_ids) or len(ref_map) != len(refs):
        errors.append(f"{label}: query_run_ids and signed query_run_refs differ")
    expected_benchmarks = set(context.get("benchmark_document_ids") or [])
    for run_id in run_ids:
        item_label = f"{label}.run[{run_id}]"
        path = query_record_path(run_dir, "runs", run_id, item_label, errors)
        if path is None or not path.is_file():
            errors.append(f"{item_label}: immutable query run is missing")
            continue
        value = load_json(path, errors)
        definition = definitions.get(str(value.get("query_id")))
        if (value.get("schema_version") != "query-run/1.0" or value.get("run_id") != run_id
                or value.get("case_id") != context.get("case_id")
                or value.get("run_hash") != canonical_sha256(value, {"run_hash"})
                or ref_map.get(run_id) != value.get("run_hash")):
            errors.append(f"{item_label}: run identity/hash mismatch")
        if (not definition or value.get("query_definition_hash") != definition.get("definition_hash")
                or value.get("query_text") != definition.get("query_text")):
            errors.append(f"{item_label}: run does not reproduce its approved query definition")
        actual_tier = value.get("actual_model_tier")
        task_path = run_dir / "tasks" / str(value.get("source_task_id")) / "task_handoff.json"
        source_handoff = load_json(task_path, errors) if task_path.is_file() else {}
        if (actual_tier not in tiers or value.get("actual_model_id") not in tiers.get(actual_tier, [])
                or source_handoff.get("actual_model_id") != value.get("actual_model_id")
                or source_handoff.get("actual_model_tier") != actual_tier):
            errors.append(f"{item_label}: actual model is not bound to the source task")
        if not value.get("database") or not value.get("tool_version") or not isinstance(value.get("pagination"), dict) or parse_time(value.get("executed_at")) is None:
            errors.append(f"{item_label}: execution metadata is incomplete or invalid")
        result_files = value.get("result_files") or []
        if not result_files:
            errors.append(f"{item_label}: result_files is empty")
        validate_file_records(run_dir, result_files, f"{item_label}.result_files", errors)
        for field, expected_keys in [("language_distribution", {"zh", "en", "ja", "ko", "fr", "de"}),
                                     ("jurisdiction_distribution", {"CN", "US", "JP", "KR", "EP", "WO"})]:
            distribution = value.get(field)
            if not isinstance(distribution, dict) or set(distribution) != expected_keys or not all(isinstance(number, int) and number >= 0 for number in distribution.values()):
                errors.append(f"{item_label}: {field} lacks complete non-negative coverage counts")
        hits = {str(item.get("document_id")) if isinstance(item, dict) else str(item) for item in value.get("benchmark_hits") or []}
        if not expected_benchmarks.issubset(hits):
            errors.append(f"{item_label}: benchmark coverage is incomplete")


def lower_tier_search_payload_has_formal_content(path: Path) -> bool:
    if path.suffix.lower() != ".json" or not path.is_file():
        return False
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return True
    def walk(item: Any) -> bool:
        if isinstance(item, dict):
            for key, child in item.items():
                normalized = str(key).lower()
                if normalized in {"classification", "xya_class", "novelty_assessment", "inventive_step_assessment", "nb", "is"}:
                    return True
                if normalized == "object_type" and child in FORMAL_OBJECT_TYPES:
                    return True
                if walk(child):
                    return True
        elif isinstance(item, list):
            return any(walk(child) for child in item)
        return False
    return walk(value)


def validate_cross(run_dir: Path, value: dict[str, Any], kind: str, manifest: dict[str, Any],
                   registry: dict[str, Any], routing: dict[str, Any], invalidation: dict[str, Any],
                   trust_store: dict[str, Any] | None, label: str, errors: list[str]) -> None:
    schemas = catalog("cross-skill-contracts.v2.schema.json", errors)
    if kind not in schemas:
        errors.append(f"{label}: local cross-skill schema missing")
        return
    validate_schema(value, schemas[kind], label, errors)
    version = {"search_context": "search-context/2.0", "search_handoff": "search-handoff/2.0", "oa_context": "oa-context/2.0", "oa_handoff": "oa-handoff/2.0"}[kind]
    require_version(value, version, label, errors)
    snapshot = manifest.get("active_snapshot") or {}
    if value.get("case_id") != manifest.get("case_id"):
        errors.append(f"{label}: case_id does not match local case")
    if value.get("execution_mode") != manifest.get("execution_mode"):
        errors.append(f"{label}: execution_mode does not match case manifest")
    identities = {
        "search_context": ("cn-patent-drafting-workflow-tiered-models", "patent-search-workflow-tiered-models"),
        "search_handoff": ("patent-search-workflow-tiered-models", "cn-patent-drafting-workflow-tiered-models"),
        "oa_context": ("cn-patent-drafting-workflow-tiered-models", "cn-oa-reexam-opinion-drafting-tiered-models"),
        "oa_handoff": ("cn-oa-reexam-opinion-drafting-tiered-models", "cn-patent-drafting-workflow-tiered-models"),
    }
    source_skill, target_skill = identities[kind]
    if value.get("source_skill") != source_skill or value.get("target_skill") != target_skill:
        errors.append(f"{label}: source/target skill identity mismatch")
    if value.get("source_skill_version") != "2.0" or value.get("target_skill_version") != "2.0":
        errors.append(f"{label}: source/target skill version must be 2.0")
    source_manifest, target_manifest = validate_cross_snapshots(run_dir, value, source_skill, target_skill,
                                                                 manifest, label, errors)
    if not isinstance(value.get("source_task_id"), str) or not value.get("source_task_id"):
        errors.append(f"{label}: source_task_id is required")
    if not kind.endswith("handoff"):
        if kind == "search_context":
            validate_search_mode_context(value, label, errors)
            validate_query_definitions(run_dir, value, label, errors)
        if value.get("context_hash") != canonical_sha256(value, {"context_hash"}):
            errors.append(f"{label}: context_hash mismatch")
        validate_file_records(run_dir, value.get("source_files"), f"{label}.source_files", errors)
        source_snapshot = source_manifest.get("active_snapshot") or {}
        if not file_record_keys(value.get("source_files")).issubset(file_record_keys(source_snapshot.get("inputs"))):
            errors.append(f"{label}: source_files include files outside the source Skill active snapshot")
        for index, location in enumerate(value.get("source_evidence_locations") or []):
            item = f"{label}.source_evidence_locations[{index}]"
            if not isinstance(location, dict):
                errors.append(f"{item}: expected object")
                continue
            path = safe_path(run_dir, location.get("source_file_path"), item, errors)
            expected_hash = location.get("source_file_hash")
            if not is_hash(expected_hash) or path is None or not path.is_file() or (path.is_file() and raw_sha256(path) != expected_hash):
                errors.append(f"{item}: source evidence file/hash is invalid")
        if value.get("execution_mode") == "orchestrated":
            trusted_authorization(value, trust_store, label, errors)
        elif value.get("authorization_receipt_id") is not None:
            errors.append(f"{label}: advisory context must not claim a controller authorization receipt")
        return
    expected_handoff_hash = canonical_sha256(value, {"handoff_hash", "execution_record_hash"})
    if value.get("handoff_hash") != expected_handoff_hash:
        errors.append(f"{label}: handoff_hash mismatch")
    if value.get("execution_mode") == "advisory" and (value.get("authority_class") != "unverified" or value.get("output_class") in FORMAL_CLASSES or value.get("result_class") in FORMAL_CLASSES):
        errors.append(f"{label}: advisory cross-skill handoff cannot be verified/formal")
    handoff_workflow = "patent-search" if kind == "search_handoff" else "cn-oa-reexam"
    handoff_source_skill = "patent-search-workflow-tiered-models" if kind == "search_handoff" else "cn-oa-reexam-opinion-drafting-tiered-models"
    if not provenance_task_dir(run_dir, value.get("source_task_id"), handoff_workflow, handoff_source_skill).is_dir():
        errors.append(f"{label}: source_task_id does not identify an available source task")
    context_filename = "search_context.json" if kind == "search_handoff" else "oa_context.json"
    context_path = run_dir / context_filename
    request_context = load_json(context_path, errors) if context_path.is_file() else {}
    if not request_context:
        errors.append(f"{label}: corresponding {context_filename} is required")
    else:
        for field in ["case_id", "execution_mode"]:
            if value.get(field) != request_context.get(field):
                errors.append(f"{label}: handoff {field} differs from request context")
        # A response reverses the request direction: request target becomes
        # response source, while request source becomes response target.
        reverse_fields = {
            "upstream_snapshot_id": "target_active_snapshot_id",
            "upstream_snapshot_hash": "target_active_snapshot_hash",
            "target_active_snapshot_id": "upstream_snapshot_id",
            "target_active_snapshot_hash": "upstream_snapshot_hash",
            "source_manifest_hash": "target_manifest_hash",
            "target_manifest_hash": "source_manifest_hash",
            "source_stage": "target_stage",
            "target_stage": "source_stage",
        }
        for handoff_field, context_field in reverse_fields.items():
            if value.get(handoff_field) != request_context.get(context_field):
                errors.append(f"{label}: handoff {handoff_field} differs from reversed request context")
        requested = set(request_context.get("allowed_writeback") or [])
        granted = set(value.get("allowed_writeback") or [])
        fixed = {"DOC", "EV", "NB", "IS"} if kind == "search_handoff" else {"CLM", "CF", "EV", "NB", "IS", "OA_RESPONSE"}
        if not granted.issubset(requested) or not granted.issubset(fixed):
            errors.append(f"{label}: allowed_writeback exceeds request or fixed interface authority")
        if value.get("execution_mode") == "orchestrated":
            trusted_authorization(request_context, trust_store, label, errors)
        if kind == "search_handoff":
            for field in ["feature_set_hash", "pst_boundary_signature"]:
                if value.get(field) != request_context.get(field):
                    errors.append(f"{label}: {field} differs from the signed search request")
            validate_query_runs(run_dir, request_context, value, registry, label, errors)
    query_run_ids = set(value.get("query_run_ids") or [])
    evidence_by_id: dict[str, dict[str, Any]] = {}
    if kind == "search_handoff":
        if value.get("search_snapshot_hash") != search_snapshot_hash(value):
            errors.append(f"{label}: search_snapshot_hash does not match normalized search contents")
        document_ids: set[str] = set()
        for index, document in enumerate(value.get("documents") or []):
            item = f"{label}.documents[{index}]"
            if not isinstance(document, dict):
                errors.append(f"{item}: expected object")
                continue
            document_id = document.get("document_id")
            if not isinstance(document_id, str) or not document_id:
                errors.append(f"{item}: document_id is required")
            elif document_id in document_ids:
                errors.append(f"{item}: duplicate document_id")
            document_ids.add(str(document_id))
            for field in ["publication_number", "publication_date", "version", "source_task_id", "query_run_id"]:
                if not document.get(field):
                    errors.append(f"{item}: missing {field}")
            if document.get("query_run_id") not in query_run_ids:
                errors.append(f"{item}: query_run_id is not listed by the handoff")
            if not provenance_task_dir(run_dir, document.get("source_task_id"), handoff_workflow, handoff_source_skill).is_dir():
                errors.append(f"{item}: source_task_id does not exist")
        for index, evidence in enumerate(value.get("evidence_links") or []):
            item = f"{label}.evidence_links[{index}]"
            if not isinstance(evidence, dict):
                errors.append(f"{item}: expected object")
                continue
            for field in ["evidence_id", "document_id", "source_task_id", "query_run_id", "full_text_location", "source_file_path", "source_file_hash"]:
                if not evidence.get(field):
                    errors.append(f"{item}: missing {field}")
            if evidence.get("document_id") not in document_ids:
                errors.append(f"{item}: document_id does not reference handoff.documents")
            evidence_id = evidence.get("evidence_id")
            if evidence_id in evidence_by_id:
                errors.append(f"{item}: duplicate evidence_id")
            elif isinstance(evidence_id, str) and evidence_id:
                evidence_by_id[evidence_id] = evidence
            if evidence.get("query_run_id") not in query_run_ids:
                errors.append(f"{item}: query_run_id is not listed by the handoff")
            source_path = safe_path(run_dir, evidence.get("source_file_path"), item, errors)
            if not is_hash(evidence.get("source_file_hash")) or source_path is None or not source_path.is_file() or (source_path.is_file() and raw_sha256(source_path) != evidence.get("source_file_hash")):
                errors.append(f"{item}: source evidence file/hash is invalid")
            if not provenance_task_dir(run_dir, evidence.get("source_task_id"), handoff_workflow, handoff_source_skill).is_dir():
                errors.append(f"{item}: source_task_id does not exist")
    findings = value.get("verified_findings") or []
    if not isinstance(findings, list):
        errors.append(f"{label}: verified_findings must be an array")
        findings = []
    for index, finding in enumerate(findings):
        item = f"{label}.verified_findings[{index}]"
        if not isinstance(finding, dict):
            errors.append(f"{item}: expected object")
            continue
        for field in ["finding_id", "review_task_id", "execution_record_id", "execution_record_hash", "source_task_id", "evidence"]:
            if not finding.get(field):
                errors.append(f"{item}: missing {field}")
        evidence = finding.get("evidence")
        if kind == "search_handoff":
            classification = finding.get("classification")
            if classification not in {"X", "Y", "A"}:
                errors.append(f"{item}: classification must be X, Y, or A")
            if finding.get("novelty_observation") not in {"not_assessed", "single_document_risk", "insufficient_single_document_coverage"}:
                errors.append(f"{item}: invalid novelty_observation")
            if finding.get("inventive_step_observation") not in {"not_assessed", "combination_risk", "combination_insufficient", "pending"}:
                errors.append(f"{item}: invalid inventive_step_observation")
            if classification == "Y":
                path = finding.get("combination_path")
                required_path = ["motivation", "functional_consistency", "compatibility", "reasonable_success_expectation"]
                if not isinstance(path, dict) or any(path.get(field) in (None, "", []) for field in required_path):
                    errors.append(f"{item}: Y finding lacks a complete combination path")
        if isinstance(evidence, dict):
            for field in ["document_id", "full_text_location", "source_file_path", "source_file_hash"]:
                if not evidence.get(field):
                    errors.append(f"{item}.evidence: missing {field}")
            if kind == "search_handoff" and not evidence.get("evidence_id"):
                errors.append(f"{item}.evidence: missing evidence_id")
            if kind == "search_handoff" and not evidence.get("query_run_id"):
                errors.append(f"{item}.evidence: missing query_run_id")
            if kind == "search_handoff" and evidence.get("query_run_id") not in query_run_ids:
                errors.append(f"{item}.evidence: query_run_id is not listed by the handoff")
            source_path = safe_path(run_dir, evidence.get("source_file_path"), f"{item}.evidence", errors)
            if not is_hash(evidence.get("source_file_hash")) or source_path is None or not source_path.is_file() or (source_path.is_file() and raw_sha256(source_path) != evidence.get("source_file_hash")):
                errors.append(f"{item}.evidence: source evidence file/hash is invalid")
            if kind == "search_handoff":
                linked = evidence_by_id.get(str(evidence.get("evidence_id")))
                exact_fields = ["document_id", "query_run_id", "full_text_location", "source_file_path", "source_file_hash"]
                if not linked or any(evidence.get(field) != linked.get(field) for field in exact_fields):
                    errors.append(f"{item}.evidence: finding is not an exact link to a registered evidence record")
        if not provenance_task_dir(run_dir, finding.get("source_task_id"), handoff_workflow, handoff_source_skill).is_dir():
            errors.append(f"{item}: source_task_id does not exist")
        expected_workflow = "patent-search" if kind == "search_handoff" else "cn-oa-reexam"
        finding_record = validate_cross_execution(run_dir, manifest, finding.get("review_task_id"), finding.get("execution_record_id"),
                                                  finding.get("execution_record_hash"), registry, routing, invalidation,
                                                  trust_store, expected_workflow, item, errors)
        if finding_record and finding_record.get("cross_handoff_hash") != value.get("handoff_hash"):
            errors.append(f"{item}: signed Sol execution does not bind this cross-Skill handoff")
    allowed = set(value.get("allowed_writeback") or [])
    for index, obj in enumerate(value.get("writeback_objects") or []):
        item = f"{label}.writeback_objects[{index}]"
        if not isinstance(obj, dict):
            errors.append(f"{item}: expected object")
            continue
        if obj.get("object_type") not in allowed:
            errors.append(f"{item}: object_type is not allowed")
        for field in ["object_id", "object_type", "version", "sha256", "source_task_id"]:
            if not obj.get(field):
                errors.append(f"{item}: missing {field}")
        if not is_hash(obj.get("sha256")):
            errors.append(f"{item}: invalid object sha256")
        if not provenance_task_dir(run_dir, obj.get("source_task_id"), handoff_workflow, handoff_source_skill).is_dir():
            errors.append(f"{item}: source_task_id does not exist")
        if obj.get("path"):
            object_path = safe_path(run_dir, obj.get("path"), item, errors)
            if object_path is None or not object_path.is_file() or (object_path.is_file() and raw_sha256(object_path) != obj.get("sha256")):
                errors.append(f"{item}: writeback file/hash is invalid")
    formal = (bool(findings) or bool(value.get("writeback_objects")) or value.get("output_class") in FORMAL_CLASSES
              or value.get("result_class") in FORMAL_CLASSES or (kind == "oa_handoff" and bool(value.get("new_claim_set_id"))))
    if formal:
        for index, obj in enumerate(value.get("writeback_objects") or []):
            if isinstance(obj, dict) and not obj.get("path"):
                errors.append(f"{label}.writeback_objects[{index}]: formal writeback requires a hashed file path")
            if not isinstance(obj, dict):
                continue
            if obj.get("source_task_id") != value.get("review_task_id"):
                errors.append(f"{label}.writeback_objects[{index}]: formal writeback must originate from the cited Sol review task")
            source_dir = provenance_task_dir(run_dir, obj.get("source_task_id"), handoff_workflow, handoff_source_skill)
            source_handoff_path = source_dir / "task_handoff.json"
            source_handoff = load_json(source_handoff_path, errors) if source_handoff_path.is_file() else {}
            generated_keys = file_record_keys(source_handoff.get("generated_files"))
            object_key = (str(obj.get("path", "")).replace("\\", "/"), str(obj.get("version", "")), str(obj.get("sha256", "")))
            if (source_handoff.get("actual_model_tier") != "Sol" or source_handoff.get("authority_class") != "verified"
                    or object_key not in generated_keys or not object_key[0].startswith("reviewed/sol/")):
                errors.append(f"{label}.writeback_objects[{index}]: formal writeback is not a hashed reviewed/sol output of the cited task")
    invalidated_ids = set(value.get("invalidated_object_ids") or [])
    for object_id in invalidated_ids:
        matched = any(isinstance(event, dict) and object_id in set(event.get("affected_object_ids") or [])
                      and event.get("status") in {"applied", "resolved", "closed"}
                      for event in invalidation.get("events") or [])
        if not matched:
            errors.append(f"{label}: invalidated object {object_id!r} lacks a closed/applied invalidation event")
    if formal:
        expected_workflow = "patent-search" if kind == "search_handoff" else "cn-oa-reexam"
        record = validate_cross_execution(run_dir, manifest, value.get("review_task_id"), value.get("execution_record_id"),
                                          value.get("execution_record_hash"), registry, routing, invalidation,
                                          trust_store, expected_workflow, label, errors)
        if value.get("execution_mode") != "orchestrated" or value.get("actual_model_tier") != "Sol" or value.get("authority_class") != "verified":
            errors.append(f"{label}: verified/formal cross-skill result requires orchestrated verified Sol authority")
        if record and (value.get("actual_model_id") != record.get("actual_model_id") or value.get("actual_model_tier") != record.get("actual_model_tier")):
            errors.append(f"{label}: cross-skill actual model does not match controller record")
        if record and record.get("cross_handoff_hash") != value.get("handoff_hash"):
            errors.append(f"{label}: signed Sol execution does not bind this cross-Skill handoff")
        if manifest.get("orchestration_status") != "enabled":
            errors.append(f"{label}: verified/formal cross-skill result is blocked before enabled release")
    if kind == "search_handoff" and findings and value.get("result_class") != "verified_finding":
        errors.append(f"{label}: verified findings require result_class=verified_finding")
    legal_formal = (value.get("output_class") == "approved_draft" or value.get("result_class") == "approved_draft"
                    or any(isinstance(item, dict) and item.get("object_type") in FORMAL_OBJECT_TYPES
                           for item in value.get("writeback_objects") or []))
    if legal_formal and kind == "search_handoff":
        required_artifacts = [{"artifact_id": str(item.get("object_id")), "path": item.get("path"),
                               "version": item.get("version"), "sha256": item.get("sha256")}
                              for item in value.get("writeback_objects") or [] if isinstance(item, dict)]
        validate_attorney_confirmation(run_dir, value.get("attorney_confirmation_id"), value.get("case_id"),
                                       value.get("search_snapshot_id"), value.get("search_snapshot_hash"),
                                       value.get("source_stage"), required_artifacts, {"search_legal_writeback"},
                                       trust_store, label, errors)
    if kind == "oa_handoff":
        if formal and not value.get("recalculation_gate_passed"):
            errors.append(f"{label}: OA formal writeback requires recalculation gate")
        if formal and not (value.get("actual_model_tier") == "Sol" and value.get("review_task_id") and value.get("execution_record_id") and value.get("authority_class") == "verified" and value.get("attorney_confirmed") and value.get("attorney_confirmation_id")):
            errors.append(f"{label}: OA formal writeback lacks Sol review/attorney confirmation")
        if formal:
            required_artifacts = [{"artifact_id": str(item.get("object_id")), "path": item.get("path"),
                                   "version": item.get("version"), "sha256": item.get("sha256")}
                                  for item in value.get("writeback_objects") or [] if isinstance(item, dict)]
            required_artifacts.extend({"artifact_id": str(item.get("artifact_id") or item.get("document_id")),
                                       "path": item.get("path"), "version": item.get("version"),
                                       "sha256": item.get("sha256")} for item in value.get("response_documents") or []
                                      if isinstance(item, dict))
            required_artifacts.append({"artifact_id": "evidence-pack-after", "path": "", "version": "v2.2-oa",
                                       "sha256": value.get("evidence_pack_hash_after")})
            validate_attorney_confirmation(run_dir, value.get("attorney_confirmation_id"), value.get("case_id"),
                                           value.get("oa_active_snapshot_id") or value.get("target_active_snapshot_id"),
                                           value.get("oa_active_snapshot_hash") or value.get("target_active_snapshot_hash"),
                                           value.get("source_stage"), required_artifacts,
                                           {"oa_approved_draft", "oa_v2.2"}, trust_store, label, errors)
            new_id, new_hash = value.get("new_claim_set_id"), value.get("new_claim_set_hash")
            if not isinstance(new_id, str) or not new_id or not is_hash(new_hash):
                errors.append(f"{label}: OA formal writeback lacks a valid new claim-set ID/hash")
            if value.get("source_claim_set_id") not in set(value.get("supersedes") or []):
                errors.append(f"{label}: OA new claim set does not supersede the source claim set")
            claim_objects = [item for item in value.get("writeback_objects") or [] if isinstance(item, dict)
                             and item.get("object_id") == new_id and item.get("object_type") == "CLM"]
            if len(claim_objects) != 1 or claim_objects[0].get("sha256") != new_hash or not claim_objects[0].get("path"):
                errors.append(f"{label}: OA new claim set is not atomically represented by one hashed CLM writeback file")
            if not is_hash(value.get("evidence_pack_hash_after")):
                errors.append(f"{label}: OA formal writeback lacks a valid resulting evidence-pack hash")


def validate_oa_evidence_pack(run_dir: Path, manifest: dict[str, Any], oa_manifest: dict[str, Any], errors: list[str]) -> None:
    record = manifest.get("evidence_pack")
    if not isinstance(record, dict):
        errors.append("case manifest evidence_pack record is missing")
        return
    path = safe_path(run_dir, record.get("path"), "case.evidence_pack.path", errors)
    if record.get("schema_version") != "v2.2-oa" or path is None or not path.is_file():
        errors.append("formal OA output requires an existing v2.2-oa evidence pack")
        return
    actual_hash = raw_sha256(path)
    if record.get("sha256") != actual_hash or oa_manifest.get("evidence_pack_hash") != actual_hash:
        errors.append("OA evidence-pack hash differs from case/OA manifests")
    try:
        from validate_oa_delivery import validate as validate_delivery
        data = json.loads(path.read_text(encoding="utf-8"))
        report = validate_delivery(data, run_dir, skip_files=True)
    except Exception as exc:
        errors.append(f"OA evidence-pack substantive validation failed to run: {exc}")
        return
    if not report.get("passed"):
        errors.append("OA evidence-pack substantive v2.2 validation failed: " + "; ".join(report.get("errors", [])))
    snapshot = next((item for item in data.get("analysis_snapshots", []) if item.get("id") == data.get("active_snapshot_id")), {})
    claim_set = next((item for item in data.get("claim_sets", []) if item.get("id") == data.get("active_claim_set_id")), {})
    expected_issue_ids = sorted(str(item.get("id")) for item in data.get("office_action_issues", []) if item.get("id"))
    expected = {
        "active_claim_set_id": data.get("active_claim_set_id"),
        "active_claim_set_hash": canonical_sha256(claim_set),
        "oa_active_snapshot_id": data.get("active_snapshot_id"),
        "oa_active_snapshot_hash": canonical_sha256(snapshot),
        "primary_strategy_id": data.get("primary_strategy_id"),
        "document_eligibility_version": snapshot.get("document_eligibility_version"),
        "evidence_pack_path": record.get("path"), "evidence_pack_schema": "v2.2-oa",
        "evidence_pack_hash": actual_hash,
        "recalculation_gate_passed": bool((data.get("recalculation_gate") or {}).get("passed")),
    }
    for field, expected_value in expected.items():
        if oa_manifest.get(field) != expected_value:
            errors.append(f"OA context manifest {field} differs from the v2.2 evidence pack")
    if sorted(str(item) for item in oa_manifest.get("issue_ids", [])) != expected_issue_ids:
        errors.append("OA context manifest issue_ids differ from the v2.2 evidence pack")


def validate_runtime(run_dir: Path, errors: list[str], trust_store: dict[str, Any] | None = None) -> None:
    paths = {name: run_dir / name for name in ["case_context_manifest.json", "routing_ledger.json", "invalidation_ledger.json", "model_registry.json"]}
    for path in paths.values():
        if not path.is_file():
            errors.append(f"runtime missing {path.name}")
    if not paths["case_context_manifest.json"].is_file():
        return
    manifest = load_json(paths["case_context_manifest.json"], errors)
    require_version(manifest, "multi-model-orchestration/2.0", str(paths["case_context_manifest.json"]), errors)
    common = catalog("common-contracts.v2.schema.json", errors)
    validate_schema(manifest, common.get("case_context_manifest", {}), "case_context_manifest.json", errors)
    if manifest.get("workflow") != WORKFLOW:
        errors.append(f"case workflow must be {WORKFLOW!r}")
    if manifest.get("orchestration_status") == "enabled" and PACKAGE_ORCHESTRATION_STATUS != "enabled":
        errors.append("package-level release remains pilot; case manifest cannot enable formal orchestration")
    if manifest.get("execution_mode") == "orchestrated" and manifest.get("orchestration_status") == "advisory_only":
        errors.append("orchestrated execution is disabled while orchestration_status=advisory_only")
    validate_snapshot(run_dir, manifest, errors)
    routing = load_json(paths["routing_ledger.json"], errors) if paths["routing_ledger.json"].is_file() else {}
    invalidation = load_json(paths["invalidation_ledger.json"], errors) if paths["invalidation_ledger.json"].is_file() else {}
    registry = load_json(paths["model_registry.json"], errors) if paths["model_registry.json"].is_file() else {}
    for value, name, version in [(routing, "routing_ledger", "multi-model-routing/2.0"), (invalidation, "invalidation_ledger", "multi-model-invalidation/2.0"), (registry, "model_registry", "multi-model-registry/2.0")]:
        require_version(value, version, name, errors)
        validate_schema(value, common.get(name, {}), name, errors)
        if name != "model_registry" and value.get("case_id") != manifest.get("case_id"):
            errors.append(f"{name}: case_id mismatch")
    validate_invalidation_ledger(invalidation, manifest.get("case_id"), "invalidation_ledger", errors)
    if manifest.get("orchestration_status") == "enabled" and manifest.get("blocked_by"):
        errors.append("enabled orchestration requires blocked_by to be empty")
    trusted_release(manifest, invalidation, trust_store, errors)
    if registry.get("tiers") != TRUSTED_MODEL_IDS:
        errors.append("model_registry.json differs from the immutable V2 tier/model mapping")
    tasks_dir = run_dir / "tasks"
    if not tasks_dir.is_dir():
        errors.append("runtime missing tasks directory")
    else:
        for task_dir in sorted(path for path in tasks_dir.iterdir() if path.is_dir()):
            validate_task(run_dir, task_dir, manifest, routing, invalidation, registry, trust_store, errors)
    if KIND == "drafting":
        cross = [("search_context.json", "search_context"), ("search_handoff.json", "search_handoff"), ("oa_context.json", "oa_context"), ("oa_handoff.json", "oa_handoff")]
    elif KIND == "search":
        cross = [("search_context.json", "search_context"), ("search_handoff.json", "search_handoff")]
    else:
        oa_path = run_dir / "oa_context_manifest.json"
        oa = {}
        if not oa_path.is_file():
            errors.append("OA runtime missing required oa_context_manifest.json")
        else:
            oa = load_json(oa_path, errors)
            require_version(oa, "oa-context-manifest/2.0", str(oa_path), errors)
            snapshot = manifest.get("active_snapshot") or {}
            if oa.get("case_id") != manifest.get("case_id") or oa.get("upstream_snapshot_id") != snapshot.get("id") or oa.get("upstream_snapshot_hash") != snapshot.get("hash"):
                errors.append("oa_context_manifest does not match active case snapshot")
            if not oa.get("recalculation_gate_passed", False):
                for handoff_path in run_dir.glob("tasks/*/task_handoff.json"):
                    candidate = load_json(handoff_path, errors)
                    if candidate.get("output_class") in FORMAL_CLASSES or candidate.get("result_class") in FORMAL_CLASSES:
                        errors.append("OA approved_draft emitted while recalculation gate is false")
            if oa.get("legacy_snapshot_ids"):
                errors.append("OA context manifest keeps legacy snapshots active")
            formal_tasks = any((candidate := load_json(path, errors)).get("output_class") in FORMAL_CLASSES
                               or candidate.get("result_class") in FORMAL_CLASSES
                               for path in run_dir.glob("tasks/*/task_handoff.json"))
            oa_handoff_path = run_dir / "oa_handoff.json"
            formal_handoff = False
            if oa_handoff_path.is_file():
                candidate = load_json(oa_handoff_path, errors)
                formal_handoff = (candidate.get("output_class") in FORMAL_CLASSES or candidate.get("result_class") in FORMAL_CLASSES
                                  or bool(candidate.get("new_claim_set_id")) or bool(candidate.get("writeback_objects")))
            if formal_tasks or formal_handoff:
                validate_oa_evidence_pack(run_dir, manifest, oa, errors)
        cross = [("oa_context.json", "oa_context"), ("oa_handoff.json", "oa_handoff")]
    for filename, kind in cross:
        path = run_dir / filename
        if path.is_file():
            validate_cross(run_dir, load_json(path, errors), kind, manifest, registry, routing, invalidation,
                           trust_store, filename, errors)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate V2 tiered-model orchestration contracts")
    parser.add_argument("run_dir", nargs="?", type=Path)
    parser.add_argument("--trust-store", type=Path, help="controller-owned trust store located outside the case run directory")
    args = parser.parse_args()
    errors: list[str] = []
    validate_static(errors)
    if args.run_dir is not None:
        run_dir = args.run_dir.resolve()
        trust_store = None
        if args.trust_store is not None:
            trust_path = args.trust_store.resolve()
            try:
                trust_path.relative_to(run_dir)
            except ValueError:
                trust_store = load_json(trust_path, errors)
            else:
                errors.append("controller trust store must be outside the writable case run directory")
        validate_runtime(run_dir, errors, trust_store)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        print(f"{len(errors)} orchestration check(s) failed.")
        return 1
    print(f"V2 model orchestration checks passed for {KIND} workflow.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
