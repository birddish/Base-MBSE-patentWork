#!/usr/bin/env python3
"""Validate a v2.2-oa evidence pack and its standard OA delivery."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from oa_v22_contract import (
    ASSESSMENT_MODES, CONCLUSION_STATUSES, ELIGIBILITY, V22_TOP_LEVEL,
    assessment_doc_ids, assessment_is_decisive_q, claim_paths, coverage_key,
    claim_frozen_records, dependency_graph, descendants, issue_fingerprint, stable_digest,
)


REQUIRED_TOP_LEVEL = {
    "schema_version": str, "case": dict, "documents": list, "claims": list,
    "feature_groups": list, "evidence": list, "novelty_assessments": list,
    "inventive_step_assessments": list, "office_action_issues": list,
    "claim_amendment_events": list, "response_trace": list, "readiness": dict,
    "version_history": list,
}
STANDARD_DELIVERY_FILES = {
    "交付说明": "00-交付说明.md", "MBSE模型报告": "01-MBSE技术模型报告.md",
    "证据包": "02-patent_evidence_pack.json", "事实核实报告": "03-事实核实审计报告.md",
    "追溯链分析": "04-追溯链与技术启示分析.md", "修改策略": "05-权利要求修改策略.md",
    "修改后权利要求": "06-修改后权利要求书.md", "审查意见答复": "07-审查意见答复.md",
    "模型到答复追溯": "08-模型到答复追溯报告.md", "质量审计": "09-质量审计与提交状态.md",
    "运行元数据": "run-metadata.json",
}
INTERNAL_ID_PATTERNS = [
    re.compile(r"\b(?:OA|CLM|CF|REL|EV|NB|NBS|IS|ISS|RT|AMD|SNAP|CLMSET|STR|IR)-[A-Z0-9-]+\b"),
    re.compile(r"\bF-\d{2}\b"), re.compile(r"\bC-\d{2}(?:-[A-Z0-9]+)?\b"),
    re.compile(r"(?<![A-Za-z0-9])(?:R|F|S|B|E)\d+(?![A-Za-z0-9])"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--evidence-pack", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--skip-delivery-files", action="store_true")
    return parser.parse_args()


def by_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item["id"]): item for item in items if isinstance(item, dict) and item.get("id")}


def duplicate_ids(data: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for key in (*REQUIRED_TOP_LEVEL.keys(), *V22_TOP_LEVEL):
        value = data.get(key)
        if isinstance(value, list):
            ids.extend(str(item["id"]) for item in value if isinstance(item, dict) and item.get("id"))
    return sorted({item for item in ids if ids.count(item) > 1})


def handling_values(value: Any) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else [str(value)] if value is not None else []


def document_roles(data: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, dict[str, str]]:
    value = snapshot.get("document_eligibility")
    return value if isinstance(value, dict) else {}


def validate_dependencies(data: dict[str, Any], active_ids: set[str], snapshot: dict[str, Any], errors: list[str]) -> tuple[dict[str, list[str]], list[dict[str, Any]]]:
    parents, graph_errors = dependency_graph(data["claims"], sorted(active_ids))
    errors.extend(f"权利要求依赖图错误: {item}" for item in graph_errors)
    graph = data.get("claim_dependency_graph")
    if not isinstance(graph, dict):
        errors.append("缺少claim_dependency_graph对象")
        graph = {}
    expected_edges = {(parent, child) for child, values in parents.items() for parent in values}
    actual_edges = {(str(row.get("from")), str(row.get("to"))) for row in graph.get("edges", []) if isinstance(row, dict)}
    if set(graph.get("nodes", [])) != active_ids or actual_edges != expected_edges:
        errors.append("claim_dependency_graph与活动权利要求的显式引用关系不一致")
    if graph_errors and graph.get("status") != "blocked":
        errors.append("依赖关系错误存在时claim_dependency_graph必须blocked")
    if not graph_errors and graph.get("status") != "verified":
        errors.append("有效依赖图必须标为verified")
    expected_paths = claim_paths(parents, sorted(active_ids)) if not graph_errors else []
    actual_paths = snapshot.get("claim_paths", []) if isinstance(snapshot.get("claim_paths"), list) else []
    expected_map = {(row["claim_id"], tuple(row["ancestor_claim_ids"])) for row in expected_paths}
    actual_map = {(str(row.get("claim_id")), tuple(row.get("ancestor_claim_ids", []))) for row in actual_paths if isinstance(row, dict)}
    if actual_map != expected_map or len(actual_map) != len(actual_paths):
        errors.append("活动快照引用路径不是依赖图的全部且唯一完整路径")
    if snapshot.get("claim_dependency_graph") != graph:
        errors.append("活动快照未冻结当前claim_dependency_graph")
    return parents, actual_paths


def validate_assessments(data: dict[str, Any], snapshot_id: str, active_ids: set[str], paths: list[dict[str, Any]], doc_roles: dict[str, dict[str, str]], errors: list[str]) -> dict[str, set[str]]:
    path_claim = {str(row.get("id")): str(row.get("claim_id")) for row in paths}
    completed = {"novelty": set(), "inventive_step": set()}
    seen = {"novelty": set(), "inventive_step": set()}
    for axis, field in (("novelty", "novelty_assessments"), ("inventive_step", "inventive_step_assessments")):
        for item in data[field]:
            label = str(item.get("id", field)); claim_id = str(item.get("claim_id", "")); path_id = str(item.get("path_id", ""))
            current = item.get("snapshot_id") == snapshot_id and claim_id in active_ids
            if current and item.get("lifecycle_status") != "active":
                errors.append(f"{label}属于活动快照但未标为active")
            if not current and item.get("lifecycle_status") == "active":
                errors.append(f"旧{axis.upper()}记录{label}仍处于active")
            if current and path_claim.get(path_id) != claim_id:
                errors.append(f"{label}未绑定本权利要求的完整引用路径")
            if item.get("assessment_mode") not in ASSESSMENT_MODES:
                errors.append(f"{label} assessment_mode不合法")
            if item.get("conclusion_status") not in CONCLUSION_STATUSES:
                errors.append(f"{label} conclusion_status不合法")
            if axis == "novelty" and not item.get("feature_coverage"):
                errors.append(f"{label}缺少必要CF覆盖事实")
            if axis == "inventive_step" and not item.get("technical_effects"):
                errors.append(f"{label}缺少技术效果事实状态")
            for row_name in ("feature_coverage", "technical_effects"):
                for row_index, row in enumerate(item.get(row_name, [])):
                    if not isinstance(row, dict) or row.get("status") not in {"D", "I", "Q", "X"}:
                        errors.append(f"{label}.{row_name}[{row_index}]缺少合法事实状态D/I/Q/X")
            path_row = next((row for row in paths if row.get("id") == path_id), {})
            claim_map = by_id(data.get("claims", []))
            expanded_claim_ids = [*path_row.get("ancestor_claim_ids", []), claim_id]
            expected_cf = {str(cf_id) for current_claim in expanded_claim_ids
                           for cf_id in claim_map.get(str(current_claim), {}).get("feature_group_ids", [])}
            if axis == "novelty":
                actual_cf = {str(row.get("cf_id")) for row in item.get("feature_coverage", []) if isinstance(row, dict)}
                if actual_cf != expected_cf:
                    errors.append(f"{label}的CF覆盖与当前展开权利要求不一致")
            else:
                distinguishing = {str(cf_id) for cf_id in item.get("distinguishing_feature_group_ids", [])}
                if not distinguishing.issubset(expected_cf):
                    errors.append(f"{label}的区别CF不属于当前展开权利要求")
            doc_ids = assessment_doc_ids(item, axis)
            if axis == "novelty":
                if isinstance(item.get("document_id"), list) or len(doc_ids) != 1:
                    errors.append(f"{label}违反新颖性单文献规则")
                composite = (snapshot_id, claim_id, path_id, doc_ids[0] if doc_ids else "")
            else:
                composite = (snapshot_id, claim_id, path_id, str(item.get("closest_document_id", "")))
                for index, candidate in enumerate(item.get("combination_candidates", [])):
                    if not isinstance(candidate, dict):
                        errors.append(f"{label}组合候选{index}不是对象"); continue
                    for field_name in ("same_function_or_problem", "motivation", "interface_compatibility", "reasonable_expectation_of_success"):
                        if field_name not in candidate:
                            errors.append(f"{label}组合候选缺少{field_name}")
            if current:
                if composite in seen[axis]:
                    errors.append(f"{label}违反活动{axis.upper()}复合唯一键")
                seen[axis].add(composite)
                completed[axis].add(coverage_key(claim_id, path_id))
            roles = [doc_roles.get(doc_id, {}) for doc_id in doc_ids]
            axis_values = [record.get(axis, "Q") for record in roles]
            overall_values = [record.get("status", "Q") for record in roles]
            for doc_id, record in zip(doc_ids, roles):
                if record.get(axis, "Q") not in ELIGIBILITY or record.get("status", "Q") not in {"D", "I", "Q", "X"}:
                    errors.append(f"{doc_id}文献资格枚举不合法")
            decisive = assessment_is_decisive_q(item) or any(value == "Q" for value in [*axis_values, *overall_values])
            prohibited = any(value in {"ineligible", "not_applicable"} for value in axis_values)
            conditional = "conditional" in axis_values
            if decisive or prohibited:
                if item.get("conclusion_status") != "undetermined" or item.get("risk") != "undetermined":
                    errors.append(f"无资格、Q或决定性Q不得支撑{label}的确定结论")
                if axis == "inventive_step" and item.get("path_status") in {"closed", "complete", "obvious"}:
                    errors.append(f"{label}的创造性路径在资格/Q未清时不得闭合")
            elif conditional and item.get("conclusion_status") == "confirmed":
                errors.append(f"条件性文献不得支撑{label}的confirmed结论")
    return completed


def validate_summaries(data: dict[str, Any], snapshot_id: str, expected: set[str], errors: list[str]) -> dict[str, set[str]]:
    covered = {"novelty": set(), "inventive_step": set()}
    assessments = {"novelty": by_id(data["novelty_assessments"]), "inventive_step": by_id(data["inventive_step_assessments"])}
    for axis, field in (("novelty", "novelty_summaries"), ("inventive_step", "inventive_step_summaries")):
        seen: set[tuple[str, str, str]] = set()
        for item in data[field]:
            label = str(item.get("id", field)); key_tuple = (str(item.get("snapshot_id")), str(item.get("claim_id")), str(item.get("path_id")))
            active_cards = [card for card in assessments[axis].values() if card.get("snapshot_id") == item.get("snapshot_id")
                            and card.get("claim_id") == item.get("claim_id") and card.get("path_id") == item.get("path_id")
                            and card.get("lifecycle_status") == "active"]
            expected_card_ids = {str(card.get("id")) for card in active_cards}
            if set(str(value) for value in item.get("assessment_ids", [])) != expected_card_ids:
                errors.append(f"{label}未精确汇总同一路径的全部活动判断卡")
            statuses = {card.get("conclusion_status") for card in active_cards}
            derived = "undetermined" if "undetermined" in statuses else "conditional" if "conditional" in statuses else "confirmed" if statuses else None
            if item.get("conclusion_status") != derived:
                errors.append(f"{label}汇总结论未按undetermined>conditional>confirmed重新计算")
            if item.get("snapshot_id") == snapshot_id and item.get("lifecycle_status") == "active":
                if key_tuple in seen:
                    errors.append(f"{label}违反活动{axis.upper()}汇总结论唯一键")
                seen.add(key_tuple)
                covered[axis].add(coverage_key(key_tuple[1], key_tuple[2]))
            for assessment_id in item.get("assessment_ids", []):
                card = assessments[axis].get(str(assessment_id))
                if not card or card.get("snapshot_id") != item.get("snapshot_id") or card.get("claim_id") != item.get("claim_id") or card.get("path_id") != item.get("path_id"):
                    errors.append(f"{label}引用的判断卡不存在或不属于同一路径")
            if not item.get("assessment_ids"):
                errors.append(f"{label}没有底层判断卡")
            if item.get("conclusion_status") not in CONCLUSION_STATUSES:
                errors.append(f"{label} conclusion_status不合法")
        if covered[axis] != expected:
            errors.append(f"活动{axis.upper()}唯一汇总结论未完整覆盖全部权利要求路径")
    return covered


def validate_v22(data: dict[str, Any], errors: list[str], metrics: dict[str, Any]) -> None:
    for field in V22_TOP_LEVEL:
        if field not in data:
            errors.append(f"v2.2-oa缺少顶层字段: {field}")
    if any(field not in data for field in V22_TOP_LEVEL):
        return
    claims = by_id(data["claims"]); claim_sets = by_id(data["claim_sets"])
    active_sets = [item for item in data["claim_sets"] if item.get("status") == "active"]
    active_set = active_sets[0] if len(active_sets) == 1 else None
    if len(active_sets) != 1:
        errors.append(f"活动权利要求集合必须唯一，当前{len(active_sets)}个")
    active_set_id = data.get("active_claim_set_id")
    if not active_set or active_set_id not in claim_sets or active_set.get("id") != active_set_id:
        errors.append("active_claim_set_id未唯一指向活动集合")
    active_ids = set(active_set.get("claim_ids", [])) if active_set else set()
    if active_ids - set(claims):
        errors.append("活动集合引用不存在权利要求")
    if active_set and len(active_set.get("claim_ids", [])) != len(active_ids):
        errors.append("活动集合含重复权利要求")
    strategies = by_id(data["amendment_strategies"]); primary = [item for item in data["amendment_strategies"] if item.get("status") == "primary"]
    primary_id = data.get("primary_strategy_id")
    if len(primary) != 1 or primary_id not in strategies or primary[0].get("id") != primary_id:
        errors.append("主修改策略必须唯一且绑定primary_strategy_id")
    if primary and (primary[0].get("support_status") == "Q" or primary[0].get("claim_set_id") != active_set_id):
        errors.append("主修改策略支持或权利要求集合绑定无效")
    snapshots = by_id(data["analysis_snapshots"]); active_snapshots = [item for item in data["analysis_snapshots"] if item.get("status") == "active"]
    snapshot = active_snapshots[0] if len(active_snapshots) == 1 else None
    snapshot_id = data.get("active_snapshot_id")
    if len(active_snapshots) != 1 or snapshot_id not in snapshots or not snapshot or snapshot.get("id") != snapshot_id:
        errors.append("活动分析快照必须唯一且由active_snapshot_id指向")
        return
    if snapshot.get("claim_set_id") != active_set_id or snapshot.get("primary_strategy_id") != primary_id:
        errors.append("活动快照未冻结活动集合和主策略")
    parents, paths = validate_dependencies(data, active_ids, snapshot, errors)
    frozen_claims = claim_frozen_records(data.get("claims", []), sorted(active_ids), parents)
    eligibility_version = "ELIG-" + stable_digest(snapshot.get("document_eligibility", {}))[:16]
    payload = {"claim_ids": sorted(active_ids), "claim_records": frozen_claims, "claim_paths": paths,
               "claim_dependency_graph": data.get("claim_dependency_graph"),
               "document_eligibility": snapshot.get("document_eligibility", {}),
               "document_eligibility_version": eligibility_version, "primary_strategy_id": primary_id}
    if snapshot.get("claim_records") != frozen_claims:
        errors.append("活动快照未冻结当前权利要求正文、版本、特征组和父项")
    if snapshot.get("document_eligibility_version") != eligibility_version:
        errors.append("活动快照文献资格版本不一致")
    if snapshot.get("frozen_hash") != stable_digest(payload):
        errors.append("活动快照frozen_hash与冻结内容不一致")
    path_ids = [str(row.get("id")) for row in paths]
    if len(path_ids) != len(set(path_ids)):
        errors.append("活动路径ID为空或重复")
    expected = {coverage_key(str(row.get("claim_id")), str(row.get("id"))) for row in paths}
    roles = document_roles(data, snapshot)
    live_roles = {
        str(document.get("id")): {
            "novelty": document.get("eligibility", {}).get("novelty", "Q"),
            "inventive_step": document.get("eligibility", {}).get("inventive_step", "Q"),
            "status": document.get("eligibility", {}).get("status", "Q"),
        }
        for document in data["documents"] if document.get("id")
    }
    if roles != live_roles:
        errors.append("活动快照的文献资格与当前documents资格对象不一致")
    completed = validate_assessments(data, snapshot_id, active_ids, paths, roles, errors)
    summaries = validate_summaries(data, snapshot_id, expected, errors)
    if completed["novelty"] != expected or completed["inventive_step"] != expected:
        errors.append("全案NB/IS判断卡未覆盖全部活动引用路径")
    issues = by_id(data["office_action_issues"]); registry = data["issue_registry"]
    if not issues:
        errors.append("OA/复审案件必须至少登记一个有效审查问题")
    if not data["response_trace"]:
        errors.append("OA/复审案件必须至少存在一条活动答复追溯")
    registry_ids = [str(item.get("issue_id")) for item in registry]
    if set(registry_ids) != set(issues) or len(registry_ids) != len(set(registry_ids)):
        errors.append("问题注册表与OA问题未一一对应")
    registry_by_issue = {str(item.get("issue_id")): item for item in registry}
    for issue_id, issue in issues.items():
        row = registry_by_issue.get(issue_id)
        if row and (issue.get("registry_id") != row.get("id") or row.get("fingerprint") != issue_fingerprint(issue)):
            errors.append(f"{issue_id}的问题指纹或回指不一致")
    traced: set[str] = set()
    for trace in data["response_trace"]:
        current = trace.get("snapshot_id") == snapshot_id and trace.get("claim_version_id") in active_ids
        if current and trace.get("lifecycle_status") != "active":
            errors.append(f"{trace.get('id')}活动答复追溯未标active")
        if not current and trace.get("lifecycle_status") == "active":
            errors.append(f"旧答复追溯{trace.get('id')}仍活动")
        if current: traced.update(str(item) for item in trace.get("issue_ids", []))
    if traced != set(issues):
        errors.append("问题注册表、OA问题与活动答复追溯未100%对应")
    gate = data["recalculation_gate"]
    seeds = {str(claim_id) for event in data["claim_amendment_events"] for claim_id in event.get("to_claim_ids", []) if claim_id in active_ids}
    impacted = descendants(parents, seeds)
    impacted_paths = {str(row.get("id")) for row in paths if row.get("claim_id") in impacted}
    impacted_keys = {coverage_key(str(row.get("claim_id")), str(row.get("id"))) for row in paths if row.get("claim_id") in impacted}
    checks = {
        "impact_seed_claim_ids": seeds, "impact_claim_ids": impacted, "impact_path_ids": impacted_paths,
        "full_expected_nb_keys": expected, "full_expected_is_keys": expected,
        "full_completed_nb_keys": summaries["novelty"], "full_completed_is_keys": summaries["inventive_step"],
        "impact_expected_nb_keys": impacted_keys, "impact_expected_is_keys": impacted_keys,
        "impact_completed_nb_keys": summaries["novelty"].intersection(impacted_keys),
        "impact_completed_is_keys": summaries["inventive_step"].intersection(impacted_keys),
    }
    if gate.get("snapshot_id") != snapshot_id:
        errors.append("recalculation_gate未绑定活动快照")
    for field, expected_set in checks.items():
        if set(gate.get(field, [])) != expected_set:
            errors.append(f"recalculation_gate.{field}与真实全案覆盖或局部影响闭包不一致")
    if not gate.get("response_trace_switched") or not gate.get("old_analysis_invalidated") or not gate.get("dependency_graph_valid"):
        errors.append("重算门的追溯切换、旧分析失效或依赖图门未通过")
    if any(item.get("conclusion_status") == "undetermined" for field in ("novelty_assessments", "inventive_step_assessments") for item in data[field] if item.get("lifecycle_status") == "active"):
        if gate.get("document_qualification_clear") or gate.get("passed"):
            errors.append("存在无资格/Q判断时重算门不得通过")
    if not gate.get("passed"):
        errors.append("修改与NB/IS重算门未通过，不得形成正式OA交付")
    metrics.update({"active_claim_set_id": active_set_id, "active_snapshot_id": snapshot_id,
                    "expected_path_coverage": len(expected), "nb_path_coverage": len(summaries["novelty"]),
                    "is_path_coverage": len(summaries["inventive_step"]), "impact_claim_count": len(impacted),
                    "recalculation_gate_passed": bool(gate.get("passed"))})


def validate_context_manifest(data: dict[str, Any], run_dir: Path, errors: list[str]) -> None:
    path = run_dir / "oa_context_manifest.json"
    if not path.is_file():
        errors.append("缺少必需文件oa_context_manifest.json")
        return
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"oa_context_manifest.json无法读取: {exc}"); return
    if manifest.get("schema_version") != "oa-context-manifest/2.0":
        errors.append("oa_context_manifest必须为oa-context-manifest/2.0")
    if manifest.get("case_id") != data.get("case", {}).get("case_id"):
        errors.append("oa_context_manifest.case_id与证据包不一致")
    if manifest.get("evidence_pack_schema") != "v2.2-oa":
        errors.append("oa_context_manifest未声明v2.2-oa")
    if bool(manifest.get("recalculation_gate_passed")) != bool(data.get("recalculation_gate", {}).get("passed")):
        errors.append("oa_context_manifest重算门与证据包不一致")
    if manifest.get("legacy_snapshot_ids"):
        errors.append("oa_context_manifest仍保留旧活动快照")
    snapshot = next((item for item in data.get("analysis_snapshots", []) if item.get("id") == data.get("active_snapshot_id")), {})
    claim_set = next((item for item in data.get("claim_sets", []) if item.get("id") == data.get("active_claim_set_id")), {})
    normalized_hash = lambda value: "sha256:" + stable_digest(value).lower()
    expected = {
        "oa_active_snapshot_id": data.get("active_snapshot_id"),
        "oa_active_snapshot_hash": normalized_hash(snapshot),
        "active_claim_set_id": data.get("active_claim_set_id"),
        "active_claim_set_hash": normalized_hash(claim_set),
        "primary_strategy_id": data.get("primary_strategy_id"),
        "document_eligibility_version": snapshot.get("document_eligibility_version"),
    }
    for field, expected_value in expected.items():
        if manifest.get(field) != expected_value:
            errors.append(f"oa_context_manifest.{field}与证据包不一致")
    expected_issues = sorted(str(item.get("id")) for item in data.get("office_action_issues", []) if item.get("id"))
    if sorted(str(item) for item in manifest.get("issue_ids", [])) != expected_issues:
        errors.append("oa_context_manifest.issue_ids与证据包不一致")
    if not manifest.get("evidence_pack_path"):
        errors.append("oa_context_manifest缺少evidence_pack_path")


def validate(data: dict[str, Any], run_dir: Path, skip_files: bool = False) -> dict[str, Any]:
    errors: list[str] = []; warnings: list[str] = []; metrics: dict[str, Any] = {}
    for key, expected_type in REQUIRED_TOP_LEVEL.items():
        if key not in data: errors.append(f"缺少顶层字段: {key}")
        elif not isinstance(data[key], expected_type): errors.append(f"字段类型错误: {key}")
    if errors: return {"passed": False, "errors": errors, "warnings": warnings, "metrics": metrics}
    if data["schema_version"] in {"2.0-oa", "2.1-oa", "v2.1-oa"}:
        errors.append("旧OA 2.0/2.1包已拒绝；须从阶段零来源创建新的v2.2-oa包")
    elif data["schema_version"] != "v2.2-oa":
        errors.append("schema_version必须为v2.2-oa")
    case = data["case"]
    for field in ("case_id", "title", "jurisdiction", "primary_mode", "delivery_depth", "case_type"):
        if not case.get(field): errors.append(f"case缺少必需值: {field}")
    dupes = duplicate_ids(data)
    if dupes: errors.append(f"存在重复ID: {', '.join(dupes)}")
    document_ids = set(by_id(data["documents"])); claim_ids = set(by_id(data["claims"])); feature_ids = set(by_id(data["feature_groups"])); evidence_ids = set(by_id(data["evidence"]))
    for document in data["documents"]:
        eligibility = document.get("eligibility")
        if not isinstance(eligibility, dict) or any(field not in eligibility for field in ("novelty", "inventive_step", "status", "reason")):
            errors.append(f"{document.get('id')}缺少完整eligibility")
        elif not isinstance(eligibility.get("reason"), str) or not eligibility.get("reason", "").strip():
            errors.append(f"{document.get('id')} eligibility.reason必须为非空核验理由")
    for claim in data["claims"]:
        for field in ("id", "version", "text", "feature_group_ids", "status"):
            if field not in claim: errors.append(f"权利要求{claim.get('id')}缺少{field}")
        if claim.get("supersedes") and claim["supersedes"] not in claim_ids: errors.append(f"{claim.get('id')} supersedes不存在")
        for feature_id in claim.get("feature_group_ids", []):
            if feature_id not in feature_ids: errors.append(f"{claim.get('id')}引用不存在特征组{feature_id}")
    for evidence in data["evidence"]:
        if evidence.get("document_id") not in document_ids: errors.append(f"{evidence.get('id')}引用不存在文献")
    for item in data["novelty_assessments"]:
        if item.get("claim_id") not in claim_ids: errors.append(f"{item.get('id')}引用不存在权利要求")
        if isinstance(item.get("document_id"), list) or item.get("document_id") not in document_ids: errors.append(f"{item.get('id')}文献字段无效或违反单文献规则")
    for item in data["inventive_step_assessments"]:
        if item.get("claim_id") not in claim_ids or item.get("closest_document_id") not in document_ids: errors.append(f"{item.get('id')}权利要求或最接近现有技术无效")
    allowed = {"admit", "argue", "amend", "delete", "divide", "verify", "client_confirm"}
    for issue in data["office_action_issues"]:
        bad = set(handling_values(issue.get("handling"))) - allowed
        if bad: errors.append(f"{issue.get('id')}处理动作不合法")
        if set(issue.get("claim_ids", [])) - claim_ids: errors.append(f"{issue.get('id')}引用不存在权利要求")
        if set(issue.get("evidence_refs", [])) - evidence_ids: errors.append(f"{issue.get('id')}引用不存在证据")
    amendments_to = {claim_id for event in data["claim_amendment_events"] for claim_id in event.get("to_claim_ids", [])}
    modified = {claim["id"] for claim in data["claims"] if claim.get("supersedes")}
    if modified - amendments_to: errors.append("新版权利要求缺少修改事件")
    readiness = data["readiness"]
    if readiness.get("content_status") not in {"pass", "conditional", "fail"} or readiness.get("submission_status") not in {"ready", "blocked"}: errors.append("readiness状态不合法")
    if readiness.get("submission_status") == "ready" and (readiness.get("content_status") != "pass" or readiness.get("blockers") or readiness.get("client_confirmation_required")): errors.append("存在阻塞项时不得ready")
    if data["schema_version"] == "v2.2-oa": validate_v22(data, errors, metrics)
    validate_context_manifest(data, run_dir, errors)
    if not skip_files:
        for label, filename in STANDARD_DELIVERY_FILES.items():
            if not (run_dir / filename).is_file(): errors.append(f"缺少标准交付文件: {label} ({filename})")
        response = run_dir / STANDARD_DELIVERY_FILES["审查意见答复"]
        if response.is_file():
            text = response.read_text(encoding="utf-8")
            hits = [match.group(0) for pattern in INTERNAL_ID_PATTERNS for match in pattern.finditer(text)]
            if hits: errors.append(f"对外答复存在内部ID/节点符号: {', '.join(sorted(set(hits)))}")
    issues = set(by_id(data["office_action_issues"])); traced = {str(issue_id) for trace in data["response_trace"] for issue_id in trace.get("issue_ids", []) if issue_id in issues}
    metrics.update({"documents": len(data["documents"]), "claims": len(data["claims"]), "issues": len(issues),
                    "trace_rows": len(data["response_trace"]), "issue_trace_coverage": round(len(traced) / len(issues), 4) if issues else 0,
                    "content_status": readiness.get("content_status"), "submission_status": readiness.get("submission_status")})
    if not issues: warnings.append("未结构化识别office_action_issues；无法评价问题覆盖率。")
    return {"passed": not errors, "errors": errors, "warnings": warnings, "metrics": metrics}


def main() -> int:
    args = parse_args(); run_dir = args.run_dir.resolve(); pack_path = (args.evidence_pack or (run_dir / "02-patent_evidence_pack.json")).resolve()
    try: data = json.loads(pack_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc: report = {"passed": False, "errors": [f"证据包读取失败: {exc}"], "warnings": [], "metrics": {}}
    else: report = validate(data, run_dir, args.skip_delivery_files)
    report.update({"run_dir": str(run_dir), "evidence_pack": str(pack_path)})
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True); args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
