#!/usr/bin/env python3
"""Deterministic v2.1-oa upgrade helpers and structural invariants."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any


V21_TOP_LEVEL = (
    "claim_sets",
    "active_claim_set_id",
    "analysis_snapshots",
    "active_snapshot_id",
    "issue_registry",
    "amendment_strategies",
    "primary_strategy_id",
    "recalculation_gate",
)

ELIGIBILITY = {"eligible", "conditional", "Q", "ineligible", "not_applicable"}
ASSESSMENT_MODES = {"full", "inherited", "no_separate_issue"}
CONCLUSION_STATUSES = {"confirmed", "conditional", "undetermined"}
ACTIVE_LIFECYCLE = "active"
INACTIVE_LIFECYCLE = {"superseded", "invalidated"}


def stable_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def active_claim_ids_v20(data: dict[str, Any]) -> list[str]:
    claims = data.get("claims", [])
    known = {item.get("id") for item in claims if item.get("id")}
    superseded = {item.get("supersedes") for item in claims if item.get("supersedes") in known}
    event_sources = {
        claim_id
        for event in data.get("claim_amendment_events", [])
        for claim_id in event.get("from_claim_ids", [])
        if event.get("to_claim_ids") or event.get("change_type") == "delete"
    }
    inactive_statuses = {"X", "deleted", "superseded", "merged", "invalidated", "withdrawn"}
    result = [
        str(item["id"])
        for item in claims
        if item.get("id") not in superseded
        and item.get("id") not in event_sources
        and item.get("status") not in inactive_statuses
    ]
    return sorted(dict.fromkeys(result))


def issue_fingerprint(issue: dict[str, Any]) -> dict[str, Any]:
    claim_ids = sorted(str(item) for item in issue.get("claim_ids", []))
    document_path = sorted(
        str(item)
        for item in issue.get("document_path", issue.get("document_ids", []))
    )
    return {
        "legal_basis": issue.get("legal_basis", issue.get("type", "other")),
        "claim_ids": claim_ids,
        "document_path": document_path,
        "assertion_type": issue.get("type", "other"),
    }


def path_rows(active_claim_ids: list[str], claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {item.get("id"): item for item in claims}
    rows: list[dict[str, Any]] = []
    for claim_id in active_claim_ids:
        claim = by_id.get(claim_id, {})
        raw_paths = claim.get("dependency_paths") or claim.get("claim_paths") or []
        if raw_paths:
            for index, raw in enumerate(raw_paths, start=1):
                if isinstance(raw, dict):
                    path_id = str(raw.get("id") or f"PATH-{claim_id}-{index:02d}")
                    ancestors = list(raw.get("ancestor_claim_ids", []))
                else:
                    path_id = str(raw)
                    ancestors = []
                rows.append({"id": path_id, "claim_id": claim_id, "ancestor_claim_ids": ancestors})
        else:
            rows.append({"id": f"PATH-{claim_id}-SELF", "claim_id": claim_id, "ancestor_claim_ids": []})
    return rows


def coverage_key(claim_id: str, path_id: str) -> str:
    return f"{claim_id}::{path_id}"


def document_eligibility_snapshot(documents: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("id")): {
            "novelty": item.get("eligibility", {}).get("novelty", "Q"),
            "inventive_step": item.get("eligibility", {}).get("inventive_step", "Q"),
        }
        for item in documents
        if item.get("id")
    }


def assessment_is_decisive_q(item: dict[str, Any]) -> bool:
    if any(row.get("status") == "Q" for row in item.get("feature_coverage", [])):
        return True
    if any(effect.get("status") == "Q" for effect in item.get("technical_effects", [])):
        return True
    decisive_fields = (
        "same_function_or_problem",
        "motivation",
        "interface_compatibility",
        "reasonable_expectation_of_success",
    )
    return any(
        candidate.get(field) == "Q"
        for candidate in item.get("combination_candidates", [])
        for field in decisive_fields
    )


def conclusion_status_for(
    item: dict[str, Any],
    documents: dict[str, dict[str, Any]],
    axis: str,
) -> str:
    doc_ids: list[str] = []
    if axis == "novelty":
        if item.get("document_id"):
            doc_ids.append(str(item["document_id"]))
    else:
        if item.get("closest_document_id"):
            doc_ids.append(str(item["closest_document_id"]))
        doc_ids.extend(
            str(candidate["document_id"])
            for candidate in item.get("combination_candidates", [])
            if candidate.get("document_id")
        )
    roles = [documents.get(doc_id, {}).get(axis, "Q") for doc_id in doc_ids]
    if assessment_is_decisive_q(item) or "Q" in roles:
        return "undetermined"
    if "conditional" in roles:
        return "conditional"
    return "confirmed"


def upgrade_to_v21(data: dict[str, Any]) -> dict[str, Any]:
    """Return a non-mutating v2.1-oa representation while preserving legacy IDs."""
    if data.get("schema_version") == "2.1-oa":
        return copy.deepcopy(data)
    upgraded = copy.deepcopy(data)
    active_claim_ids = active_claim_ids_v20(upgraded)
    claim_set_id = "CLMSET-ACTIVE-Q" if not active_claim_ids else "CLMSET-ACTIVE-01"
    upgraded["claim_sets"] = [
        {
            "id": claim_set_id,
            "claim_ids": active_claim_ids,
            "status": "active" if active_claim_ids else "candidate",
            "supersedes": None,
            "fact_status": "D" if active_claim_ids else "Q",
        }
    ]
    upgraded["active_claim_set_id"] = claim_set_id if active_claim_ids else None

    has_amendment = bool(upgraded.get("claim_amendment_events"))
    support_q = any(
        not event.get("support_refs") or event.get("recalculation_status") in {"Q", "pending"}
        for event in upgraded.get("claim_amendment_events", [])
    )
    strategy_id = "STR-01"
    strategy_status = "blocked" if has_amendment and support_q else "primary"
    upgraded["amendment_strategies"] = [
        {
            "id": strategy_id,
            "claim_set_id": claim_set_id,
            "status": strategy_status,
            "support_status": "Q" if support_q else "supported",
            "issue_ids": [item.get("id") for item in upgraded.get("office_action_issues", []) if item.get("id")],
        }
    ]
    upgraded["primary_strategy_id"] = strategy_id if strategy_status == "primary" else None

    paths = path_rows(active_claim_ids, upgraded.get("claims", []))
    snapshot_id = "SNAP-01"
    snapshot_status = "active" if active_claim_ids and upgraded["primary_strategy_id"] else "candidate"
    upgraded["analysis_snapshots"] = [
        {
            "id": snapshot_id,
            "claim_set_id": claim_set_id,
            "claim_paths": paths,
            "document_eligibility": document_eligibility_snapshot(upgraded.get("documents", [])),
            "primary_strategy_id": upgraded["primary_strategy_id"],
            "status": snapshot_status,
            "frozen_hash": stable_digest(
                {
                    "claim_ids": active_claim_ids,
                    "claim_paths": paths,
                    "document_eligibility": document_eligibility_snapshot(upgraded.get("documents", [])),
                    "primary_strategy_id": upgraded["primary_strategy_id"],
                }
            ),
        }
    ]
    upgraded["active_snapshot_id"] = snapshot_id if snapshot_status == "active" else None

    upgraded["issue_registry"] = []
    for index, issue in enumerate(upgraded.get("office_action_issues", []), start=1):
        registry_id = f"IR-{index:02d}"
        issue["registry_id"] = registry_id
        upgraded["issue_registry"].append(
            {
                "id": registry_id,
                "issue_id": issue.get("id"),
                "fingerprint": issue_fingerprint(issue),
                "status": "active",
            }
        )

    active_claim_set = set(active_claim_ids)
    document_roles = document_eligibility_snapshot(upgraded.get("documents", []))
    path_by_claim: dict[str, list[str]] = {}
    for row in paths:
        path_by_claim.setdefault(str(row["claim_id"]), []).append(str(row["id"]))
    for axis, key in (("novelty", "novelty_assessments"), ("inventive_step", "inventive_step_assessments")):
        for item in upgraded.get(key, []):
            claim_id = str(item.get("claim_id", ""))
            claim_paths = path_by_claim.get(claim_id, [])
            item.setdefault("path_id", claim_paths[0] if len(claim_paths) == 1 else None)
            item.setdefault("assessment_mode", "full")
            item["snapshot_id"] = snapshot_id
            item["lifecycle_status"] = ACTIVE_LIFECYCLE if claim_id in active_claim_set else "invalidated"
            item["conclusion_status"] = conclusion_status_for(item, document_roles, axis)
            if item["conclusion_status"] == "undetermined":
                item["risk"] = "undetermined"
                if axis == "inventive_step":
                    item["path_status"] = "open_Q"

    for trace in upgraded.get("response_trace", []):
        trace["snapshot_id"] = snapshot_id
        trace["lifecycle_status"] = (
            ACTIVE_LIFECYCLE if trace.get("claim_version_id") in active_claim_set else "invalidated"
        )

    expected = [coverage_key(row["claim_id"], row["id"]) for row in paths]
    completed_nb = sorted(
        coverage_key(item.get("claim_id"), item.get("path_id"))
        for item in upgraded.get("novelty_assessments", [])
        if item.get("lifecycle_status") == ACTIVE_LIFECYCLE and item.get("path_id")
    )
    completed_is = sorted(
        coverage_key(item.get("claim_id"), item.get("path_id"))
        for item in upgraded.get("inventive_step_assessments", [])
        if item.get("lifecycle_status") == ACTIVE_LIFECYCLE and item.get("path_id")
    )
    response_switched = bool(upgraded.get("response_trace")) and all(
        item.get("snapshot_id") == snapshot_id
        and item.get("lifecycle_status") == ACTIVE_LIFECYCLE
        and item.get("claim_version_id") in active_claim_set
        for item in upgraded.get("response_trace", [])
    )
    old_invalidated = all(
        item.get("lifecycle_status") != ACTIVE_LIFECYCLE
        for key in ("novelty_assessments", "inventive_step_assessments")
        for item in upgraded.get(key, [])
        if item.get("claim_id") not in active_claim_set
    ) and all(
        item.get("lifecycle_status") != ACTIVE_LIFECYCLE
        for item in upgraded.get("response_trace", [])
        if item.get("claim_version_id") not in active_claim_set
    )
    gate_passed = (
        bool(upgraded["active_snapshot_id"])
        and sorted(expected) == sorted(set(completed_nb))
        and sorted(expected) == sorted(set(completed_is))
        and response_switched
        and old_invalidated
    )
    upgraded["recalculation_gate"] = {
        "snapshot_id": snapshot_id,
        "impact_claim_ids": active_claim_ids,
        "impact_path_ids": [row["id"] for row in paths],
        "expected_nb_keys": expected,
        "expected_is_keys": expected,
        "completed_nb_keys": completed_nb,
        "completed_is_keys": completed_is,
        "response_trace_switched": response_switched,
        "old_analysis_invalidated": old_invalidated,
        "passed": gate_passed,
    }
    upgraded["schema_version"] = "2.1-oa"
    upgraded.setdefault("version_history", []).append(
        {
            "version": "2.1-oa",
            "change": "增加活动权利要求集合、分析快照、问题注册表、主策略和重算门；保留旧ID与事实语义。",
            "status": "draft" if not gate_passed else "reviewed",
        }
    )
    return upgraded

