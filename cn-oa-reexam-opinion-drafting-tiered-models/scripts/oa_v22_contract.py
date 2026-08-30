#!/usr/bin/env python3
"""Deterministic v2.2-oa construction helpers and legal-data invariants."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any


V22_TOP_LEVEL = (
    "claim_sets", "active_claim_set_id", "claim_dependency_graph", "analysis_snapshots",
    "active_snapshot_id", "issue_registry", "amendment_strategies", "primary_strategy_id",
    "novelty_summaries", "inventive_step_summaries", "recalculation_gate",
)
ELIGIBILITY = {"eligible", "conditional", "Q", "ineligible", "not_applicable"}
ASSESSMENT_MODES = {"full", "inherited", "no_separate_issue"}
CONCLUSION_STATUSES = {"confirmed", "conditional", "undetermined"}
ACTIVE_LIFECYCLE = "active"


def stable_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def coverage_key(claim_id: str, path_id: str) -> str:
    return f"{claim_id}::{path_id}"


def active_claim_ids(data: dict[str, Any]) -> list[str]:
    claims = data.get("claims", [])
    known = {item.get("id") for item in claims if item.get("id")}
    superseded = {item.get("supersedes") for item in claims if item.get("supersedes") in known}
    event_sources = {
        claim_id for event in data.get("claim_amendment_events", [])
        for claim_id in event.get("from_claim_ids", [])
        if event.get("to_claim_ids") or event.get("change_type") == "delete"
    }
    inactive = {"X", "deleted", "superseded", "merged", "invalidated", "withdrawn"}
    return sorted(str(item["id"]) for item in claims if item.get("id") not in superseded
                  and item.get("id") not in event_sources and item.get("status") not in inactive)


def issue_fingerprint(issue: dict[str, Any]) -> dict[str, Any]:
    return {
        "legal_basis": issue.get("legal_basis", issue.get("type", "other")),
        "claim_ids": sorted(str(item) for item in issue.get("claim_ids", [])),
        "document_path": sorted(str(item) for item in issue.get("document_path", issue.get("document_ids", []))),
        "assertion_type": issue.get("type", "other"),
    }


def document_eligibility_snapshot(documents: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(item["id"]): {
            "novelty": item.get("eligibility", {}).get("novelty", "Q"),
            "inventive_step": item.get("eligibility", {}).get("inventive_step", "Q"),
            "status": item.get("eligibility", {}).get("status", "Q"),
        }
        for item in documents if item.get("id")
    }


def assessment_is_decisive_q(item: dict[str, Any]) -> bool:
    if any(row.get("status") not in {"D", "I", "X"} for row in item.get("feature_coverage", [])):
        return True
    if any(effect.get("status") not in {"D", "I", "X"} for effect in item.get("technical_effects", [])):
        return True
    fields = ("same_function_or_problem", "motivation", "interface_compatibility", "reasonable_expectation_of_success")
    return any(candidate.get(field) == "Q" for candidate in item.get("combination_candidates", []) for field in fields)


def assessment_doc_ids(item: dict[str, Any], axis: str) -> list[str]:
    if axis == "novelty":
        return [str(item["document_id"])] if item.get("document_id") else []
    result = [str(item["closest_document_id"])] if item.get("closest_document_id") else []
    result.extend(str(candidate["document_id"]) for candidate in item.get("combination_candidates", [])
                  if isinstance(candidate, dict) and candidate.get("document_id"))
    return result


def conclusion_status_for(item: dict[str, Any], documents: dict[str, dict[str, Any]], axis: str) -> str:
    roles: list[str] = []
    overall: list[str] = []
    for doc_id in assessment_doc_ids(item, axis):
        record = documents.get(doc_id, {})
        roles.append(str(record.get(axis, "Q")))
        overall.append(str(record.get("status", "Q")))
    if assessment_is_decisive_q(item) or any(value == "Q" for value in [*roles, *overall]):
        return "undetermined"
    if any(value in {"ineligible", "not_applicable"} for value in roles):
        return "undetermined"
    if "conditional" in roles:
        return "conditional"
    return "confirmed" if roles and all(value == "eligible" for value in roles) else "undetermined"


def _text_indicates_dependency(text: str) -> bool:
    return bool(re.search(r"根据权利要求|如权利要求|according\s+to\s+claim|claim\s+\d+\s+of", text, re.I))


def _claim_number(claim: dict[str, Any]) -> str | None:
    if claim.get("claim_number") is not None:
        return str(claim["claim_number"])
    match = re.search(r"(\d+)$", str(claim.get("id", "")))
    return str(int(match.group(1))) if match else None


def claim_frozen_records(claims: list[dict[str, Any]], active_ids: list[str],
                         parents: dict[str, list[str]]) -> list[dict[str, Any]]:
    by_id = {str(item.get("id")): item for item in claims if item.get("id")}
    rows: list[dict[str, Any]] = []
    for claim_id in sorted(active_ids):
        claim = by_id.get(claim_id, {})
        rows.append({"id": claim_id, "claim_number": _claim_number(claim), "version": claim.get("version"),
                     "text_hash": stable_digest(str(claim.get("text", ""))),
                     "feature_group_ids": sorted(str(item) for item in claim.get("feature_group_ids", [])),
                     "depends_on_claim_ids": sorted(str(item) for item in parents.get(claim_id, []))})
    return rows


def _text_dependency_numbers(text: str) -> set[str]:
    numbers: set[str] = set()
    groups = re.findall(r"(?:权利要求|claims?)\s*([0-9\s,，、;；和或至\-—–to]+)", text, re.I)
    for group in groups:
        for start, end in re.findall(r"(\d+)\s*(?:至|to|\-|—|–)\s*(\d+)", group, re.I):
            low, high = int(start), int(end)
            if low <= high and high - low <= 100:
                numbers.update(str(item) for item in range(low, high + 1))
        stripped = re.sub(r"(\d+)\s*(?:至|to|\-|—|–)\s*(\d+)", " ", group, flags=re.I)
        numbers.update(str(int(item)) for item in re.findall(r"\d+", stripped))
    return numbers


def dependency_graph(claims: list[dict[str, Any]], active_ids: list[str]) -> tuple[dict[str, list[str]], list[str]]:
    active = set(active_ids)
    by_id = {str(item.get("id")): item for item in claims if item.get("id")}
    number_rows = [(_claim_number(item), str(item.get("id"))) for item in claims if item.get("id") and _claim_number(item)]
    duplicate_numbers = sorted({number for number, _claim_id in number_rows if sum(1 for item, _ in number_rows if item == number) > 1})
    id_by_number = {number: claim_id for number, claim_id in number_rows}
    parents: dict[str, list[str]] = {}
    errors: list[str] = [f"claim_number重复: {number}" for number in duplicate_numbers]
    for claim_id in active_ids:
        claim = by_id.get(claim_id, {})
        raw = claim.get("depends_on_claim_ids")
        if raw is None:
            raw = []
            if claim.get("claim_type") == "dependent" or _text_indicates_dependency(str(claim.get("text", ""))):
                errors.append(f"{claim_id}: 从属关系未显式提供")
        if not isinstance(raw, list):
            errors.append(f"{claim_id}: depends_on_claim_ids必须为数组")
            raw = []
        normalized = [str(item) for item in raw]
        dependent_marker = claim.get("claim_type") == "dependent" or _text_indicates_dependency(str(claim.get("text", "")))
        if dependent_marker and not normalized:
            errors.append(f"{claim_id}: 从属权利要求必须显式提供至少一个父项")
        if len(normalized) != len(set(normalized)):
            errors.append(f"{claim_id}: 引用父项重复")
        for parent in normalized:
            if parent not in active:
                errors.append(f"{claim_id}: 引用不存在或非活动父项{parent}")
            if parent == claim_id:
                errors.append(f"{claim_id}: 不得自引用")
        if claim.get("claim_type") == "independent" and normalized:
            errors.append(f"{claim_id}: 独立权利要求不得声明父项")
        dependency_numbers = _text_dependency_numbers(str(claim.get("text", "")))
        unknown_numbers = dependency_numbers - set(id_by_number)
        text_refs = {id_by_number[number] for number in dependency_numbers if number in id_by_number}
        if dependent_marker and not dependency_numbers:
            errors.append(f"{claim_id}: 正文从属引用无法完整解析，关系状态必须阻断")
        if unknown_numbers:
            errors.append(f"{claim_id}: 正文引用未知权利要求{sorted(unknown_numbers)}")
        if text_refs != set(normalized):
            errors.append(f"{claim_id}: 正文引用与depends_on_claim_ids不一致")
        parents[claim_id] = normalized

    colors: dict[str, int] = {}

    def visit(node: str) -> None:
        colors[node] = 1
        for parent in parents.get(node, []):
            if parent not in parents:
                continue
            if colors.get(parent) == 1:
                errors.append(f"引用图存在环: {node}->{parent}")
            elif colors.get(parent, 0) == 0:
                visit(parent)
        colors[node] = 2

    for claim_id in active_ids:
        if colors.get(claim_id, 0) == 0:
            visit(claim_id)
    return parents, sorted(set(errors))


def claim_paths(parents: dict[str, list[str]], active_ids: list[str]) -> list[dict[str, Any]]:
    cache: dict[str, list[list[str]]] = {}

    def expand(claim_id: str, visiting: set[str]) -> list[list[str]]:
        if claim_id in cache:
            return cache[claim_id]
        if claim_id in visiting:
            return []
        if not parents.get(claim_id):
            cache[claim_id] = [[]]
            return cache[claim_id]
        result: list[list[str]] = []
        for parent in parents[claim_id]:
            for prefix in expand(parent, visiting | {claim_id}):
                result.append([*prefix, parent])
        cache[claim_id] = result
        return result

    rows: list[dict[str, Any]] = []
    for claim_id in active_ids:
        for index, ancestors in enumerate(expand(claim_id, set()), start=1):
            rows.append({"id": f"PATH-{claim_id}-{index:02d}", "claim_id": claim_id, "ancestor_claim_ids": ancestors})
    return rows


def descendants(parents: dict[str, list[str]], seeds: set[str]) -> set[str]:
    result = set(seeds)
    changed = True
    while changed:
        changed = False
        for claim_id, direct_parents in parents.items():
            if claim_id not in result and result.intersection(direct_parents):
                result.add(claim_id); changed = True
    return result


def _summary_rows(axis: str, assessments: list[dict[str, Any]], paths: list[dict[str, Any]], snapshot_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    prefix = "NBS" if axis == "novelty" else "ISS"
    for index, path in enumerate(paths, start=1):
        cards = [item for item in assessments if item.get("snapshot_id") == snapshot_id
                 and item.get("claim_id") == path["claim_id"] and item.get("path_id") == path["id"]
                 and item.get("lifecycle_status") == "active"]
        if not cards:
            continue
        statuses = {item.get("conclusion_status") for item in cards}
        conclusion = "undetermined" if "undetermined" in statuses else "conditional" if "conditional" in statuses else "confirmed"
        rows.append({"id": f"{prefix}-{index:02d}", "snapshot_id": snapshot_id, "claim_id": path["claim_id"],
                     "path_id": path["id"], "assessment_ids": [item.get("id") for item in cards],
                     "conclusion_status": conclusion, "lifecycle_status": "active"})
    return rows


def create_v22(data: dict[str, Any]) -> dict[str, Any]:
    """Create a new v2.2-oa object from a stage-zero pre-application representation."""
    if data.get("schema_version") == "v2.1-oa":
        raise ValueError("v2.1-oa is explicitly unsupported; create a fresh v2.2-oa case from stage-zero source materials")
    if data.get("schema_version") == "v2.2-oa":
        return copy.deepcopy(data)
    upgraded = copy.deepcopy(data)
    active_ids = active_claim_ids(upgraded)
    claim_set_id = "CLMSET-ACTIVE-01"
    parents, dependency_errors = dependency_graph(upgraded.get("claims", []), active_ids)
    paths = claim_paths(parents, active_ids) if not dependency_errors else []
    graph = {"nodes": active_ids, "edges": [{"from": parent, "to": child} for child in active_ids for parent in parents.get(child, [])],
             "status": "blocked" if dependency_errors else "verified", "errors": dependency_errors}
    upgraded["claim_dependency_graph"] = graph
    upgraded["claim_sets"] = [{"id": claim_set_id, "claim_ids": active_ids,
                                "status": "active" if active_ids else "candidate", "supersedes": None,
                                "fact_status": "D" if active_ids else "Q"}]
    upgraded["active_claim_set_id"] = claim_set_id if active_ids else None
    support_q = any(not event.get("support_refs") or event.get("recalculation_status") in {"Q", "pending"}
                    for event in upgraded.get("claim_amendment_events", []))
    strategy_id = "STR-01"
    upgraded["amendment_strategies"] = [{"id": strategy_id, "claim_set_id": claim_set_id,
                                           "status": "blocked" if support_q else "primary",
                                           "support_status": "Q" if support_q else "supported",
                                           "issue_ids": [item.get("id") for item in upgraded.get("office_action_issues", []) if item.get("id")]}]
    upgraded["primary_strategy_id"] = None if support_q else strategy_id
    snapshot_id = "OA-SNAP-01"
    doc_roles = document_eligibility_snapshot(upgraded.get("documents", []))
    snapshot_status = "active" if active_ids and not dependency_errors and not support_q else "candidate"
    frozen_claims = claim_frozen_records(upgraded.get("claims", []), active_ids, parents)
    eligibility_version = "ELIG-" + stable_digest(doc_roles)[:16]
    payload = {"claim_ids": active_ids, "claim_records": frozen_claims, "claim_paths": paths,
               "claim_dependency_graph": graph, "document_eligibility": doc_roles,
               "document_eligibility_version": eligibility_version,
               "primary_strategy_id": upgraded["primary_strategy_id"]}
    upgraded["analysis_snapshots"] = [{"id": snapshot_id, "claim_set_id": claim_set_id, "claim_paths": paths,
                                        "claim_records": frozen_claims, "claim_dependency_graph": graph,
                                        "document_eligibility": doc_roles, "document_eligibility_version": eligibility_version,
                                        "primary_strategy_id": upgraded["primary_strategy_id"], "status": snapshot_status,
                                        "frozen_hash": stable_digest(payload)}]
    upgraded["active_snapshot_id"] = snapshot_id if snapshot_status == "active" else None
    upgraded["issue_registry"] = []
    for index, issue in enumerate(upgraded.get("office_action_issues", []), start=1):
        registry_id = f"IR-{index:02d}"; issue["registry_id"] = registry_id
        upgraded["issue_registry"].append({"id": registry_id, "issue_id": issue.get("id"),
                                            "fingerprint": issue_fingerprint(issue), "status": "active"})
    path_by_claim: dict[str, list[str]] = {}
    for row in paths:
        path_by_claim.setdefault(row["claim_id"], []).append(row["id"])
    for axis, field in (("novelty", "novelty_assessments"), ("inventive_step", "inventive_step_assessments")):
        for item in upgraded.get(field, []):
            options = path_by_claim.get(str(item.get("claim_id")), [])
            item.setdefault("path_id", options[0] if len(options) == 1 else None)
            item.setdefault("assessment_mode", "full")
            item["snapshot_id"] = snapshot_id
            valid_path = item.get("path_id") in options
            item["lifecycle_status"] = "active" if snapshot_status == "active" and valid_path else "invalidated"
            item["conclusion_status"] = conclusion_status_for(item, doc_roles, axis)
            if item["conclusion_status"] != "confirmed":
                item["risk"] = "undetermined"
                if axis == "inventive_step": item["path_status"] = "open_Q"
    upgraded["novelty_summaries"] = _summary_rows("novelty", upgraded.get("novelty_assessments", []), paths, snapshot_id)
    upgraded["inventive_step_summaries"] = _summary_rows("inventive_step", upgraded.get("inventive_step_assessments", []), paths, snapshot_id)
    for trace in upgraded.get("response_trace", []):
        trace["snapshot_id"] = snapshot_id
        trace["lifecycle_status"] = "active" if snapshot_status == "active" and trace.get("claim_version_id") in set(active_ids) else "invalidated"
    seeds = {str(claim_id) for event in upgraded.get("claim_amendment_events", []) for claim_id in event.get("to_claim_ids", []) if claim_id in set(active_ids)}
    impacted = descendants(parents, seeds)
    impacted_paths = [row["id"] for row in paths if row["claim_id"] in impacted]
    full_expected = {coverage_key(row["claim_id"], row["id"]) for row in paths}
    completed_nb = {coverage_key(row["claim_id"], row["path_id"]) for row in upgraded["novelty_summaries"]}
    completed_is = {coverage_key(row["claim_id"], row["path_id"]) for row in upgraded["inventive_step_summaries"]}
    impacted_expected = {coverage_key(row["claim_id"], row["id"]) for row in paths if row["claim_id"] in impacted}
    issues_present = bool(upgraded.get("office_action_issues"))
    traces_present = bool(upgraded.get("response_trace"))
    response_switched = issues_present and traces_present and all(
        trace.get("snapshot_id") == snapshot_id and trace.get("lifecycle_status") == "active"
        for trace in upgraded.get("response_trace", [])
    )
    old_invalidated = all(item.get("lifecycle_status") != "active" for field in ("novelty_assessments", "inventive_step_assessments")
                          for item in upgraded.get(field, []) if item.get("snapshot_id") != snapshot_id)
    qualifications_clear = all(item.get("conclusion_status") != "undetermined" for field in ("novelty_assessments", "inventive_step_assessments")
                               for item in upgraded.get(field, []) if item.get("lifecycle_status") == "active")
    passed = bool(upgraded["active_snapshot_id"]) and full_expected == completed_nb == completed_is and impacted_expected.issubset(completed_nb) and impacted_expected.issubset(completed_is) and response_switched and old_invalidated and qualifications_clear
    upgraded["recalculation_gate"] = {
        "snapshot_id": upgraded["active_snapshot_id"], "impact_seed_claim_ids": sorted(seeds),
        "impact_claim_ids": sorted(impacted), "impact_path_ids": sorted(impacted_paths),
        "full_expected_nb_keys": sorted(full_expected), "full_expected_is_keys": sorted(full_expected),
        "full_completed_nb_keys": sorted(completed_nb), "full_completed_is_keys": sorted(completed_is),
        "impact_expected_nb_keys": sorted(impacted_expected), "impact_expected_is_keys": sorted(impacted_expected),
        "impact_completed_nb_keys": sorted(completed_nb.intersection(impacted_expected)),
        "impact_completed_is_keys": sorted(completed_is.intersection(impacted_expected)),
        "response_trace_switched": response_switched, "old_analysis_invalidated": old_invalidated,
        "dependency_graph_valid": not dependency_errors, "document_qualification_clear": qualifications_clear,
        "passed": passed,
    }
    upgraded["schema_version"] = "v2.2-oa"
    upgraded.setdefault("version_history", []).append({"version": "v2.2-oa", "change": "由阶段零来源创建新的OA证据包；加入显式依赖图、唯一汇总对象、资格门和局部影响闭包。", "status": "reviewed" if passed else "draft"})
    return upgraded
