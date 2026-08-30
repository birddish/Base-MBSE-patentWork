#!/usr/bin/env python3
"""Validate v2.0/v2.1 OA evidence packs and the standard OA delivery."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from oa_v21_contract import (
    ASSESSMENT_MODES,
    CONCLUSION_STATUSES,
    ELIGIBILITY,
    V21_TOP_LEVEL,
    assessment_is_decisive_q,
    coverage_key,
    issue_fingerprint,
    stable_digest,
)


REQUIRED_TOP_LEVEL = {
    "schema_version": str,
    "case": dict,
    "documents": list,
    "claims": list,
    "feature_groups": list,
    "evidence": list,
    "novelty_assessments": list,
    "inventive_step_assessments": list,
    "office_action_issues": list,
    "claim_amendment_events": list,
    "response_trace": list,
    "readiness": dict,
    "version_history": list,
}

STANDARD_DELIVERY_FILES = {
    "交付说明": "00-交付说明.md",
    "MBSE模型报告": "01-MBSE技术模型报告.md",
    "证据包": "02-patent_evidence_pack.json",
    "事实核实报告": "03-事实核实审计报告.md",
    "追溯链分析": "04-追溯链与技术启示分析.md",
    "修改策略": "05-权利要求修改策略.md",
    "修改后权利要求": "06-修改后权利要求书.md",
    "审查意见答复": "07-审查意见答复.md",
    "模型到答复追溯": "08-模型到答复追溯报告.md",
    "质量审计": "09-质量审计与提交状态.md",
    "运行元数据": "run-metadata.json",
}

INTERNAL_ID_PATTERNS = [
    re.compile(r"\b(?:OA|CLM|CF|REL|EV|NB|IS|RT|AMD|SNAP|CLMSET|STR|IR)-[A-Z0-9-]+\b"),
    re.compile(r"\bF-\d{2}\b"),
    re.compile(r"\bC-\d{2}(?:-[A-Z0-9]+)?\b"),
    re.compile(r"(?<![A-Za-z0-9])(?:R|F|S|B|E)\d+(?![A-Za-z0-9])"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--evidence-pack", type=Path)
    parser.add_argument("--report", type=Path, help="optional JSON report output")
    parser.add_argument("--skip-delivery-files", action="store_true")
    return parser.parse_args()


def duplicate_ids(data: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for key in (
        "documents",
        "claims",
        "feature_groups",
        "evidence",
        "novelty_assessments",
        "inventive_step_assessments",
        "office_action_issues",
        "claim_amendment_events",
        "response_trace",
        "claim_sets",
        "analysis_snapshots",
        "issue_registry",
        "amendment_strategies",
    ):
        ids.extend(str(item["id"]) for item in data.get(key, []) if isinstance(item, dict) and item.get("id"))
    return sorted({item_id for item_id in ids if ids.count(item_id) > 1})


def _items_by_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item["id"]): item for item in items if isinstance(item, dict) and item.get("id")}


def _handling_values(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)] if value is not None else []


def _document_roles(data: dict[str, Any], snapshot: dict[str, Any] | None = None) -> dict[str, dict[str, str]]:
    if snapshot and isinstance(snapshot.get("document_eligibility"), dict):
        return snapshot["document_eligibility"]
    return {
        str(doc.get("id")): {
            "novelty": str(doc.get("eligibility", {}).get("novelty", "Q")),
            "inventive_step": str(doc.get("eligibility", {}).get("inventive_step", "Q")),
        }
        for doc in data.get("documents", [])
        if doc.get("id")
    }


def _assessment_doc_ids(item: dict[str, Any], axis: str) -> list[str]:
    if axis == "novelty":
        return [str(item["document_id"])] if item.get("document_id") else []
    result = [str(item["closest_document_id"])] if item.get("closest_document_id") else []
    result.extend(
        str(candidate["document_id"])
        for candidate in item.get("combination_candidates", [])
        if isinstance(candidate, dict) and candidate.get("document_id")
    )
    return result


def _validate_v21(data: dict[str, Any], errors: list[str], metrics: dict[str, Any]) -> None:
    for field in V21_TOP_LEVEL:
        if field not in data:
            errors.append(f"v2.1-oa 缺少顶层字段: {field}")
    if any(field not in data for field in V21_TOP_LEVEL):
        return

    claims = _items_by_id(data["claims"])
    claim_sets = _items_by_id(data["claim_sets"])
    active_sets = [item for item in data["claim_sets"] if item.get("status") == "active"]
    if len(active_sets) != 1:
        errors.append(f"活动权利要求集合必须唯一，当前为 {len(active_sets)} 个")
        active_set = None
    else:
        active_set = active_sets[0]
    active_set_id = data.get("active_claim_set_id")
    if active_set_id not in claim_sets or not active_set or active_set.get("id") != active_set_id:
        errors.append("active_claim_set_id 未唯一指向活动权利要求集合")
    active_claim_ids = set(active_set.get("claim_ids", [])) if active_set else set()
    missing_active_claims = sorted(active_claim_ids - set(claims))
    if missing_active_claims:
        errors.append(f"活动集合引用不存在的权利要求: {', '.join(missing_active_claims)}")
    if active_set and len(active_set.get("claim_ids", [])) != len(active_claim_ids):
        errors.append("活动权利要求集合含重复权利要求")

    strategies = _items_by_id(data["amendment_strategies"])
    primary = [item for item in data["amendment_strategies"] if item.get("status") == "primary"]
    primary_id = data.get("primary_strategy_id")
    if len(primary) != 1:
        errors.append(f"主修改策略必须唯一，当前为 {len(primary)} 个")
    if primary_id not in strategies or len(primary) != 1 or primary[0].get("id") != primary_id:
        errors.append("primary_strategy_id 未唯一指向主修改策略")
    for strategy in data["amendment_strategies"]:
        if strategy.get("support_status") == "Q" and strategy.get("status") == "primary":
            errors.append(f"{strategy.get('id')} 的修改支持为 Q，不得作为主策略")
        if strategy.get("status") == "primary" and strategy.get("claim_set_id") != active_set_id:
            errors.append(f"{strategy.get('id')} 未绑定活动权利要求集合")

    snapshots = _items_by_id(data["analysis_snapshots"])
    active_snapshots = [item for item in data["analysis_snapshots"] if item.get("status") == "active"]
    if len(active_snapshots) != 1:
        errors.append(f"活动分析快照必须唯一，当前为 {len(active_snapshots)} 个")
        snapshot = None
    else:
        snapshot = active_snapshots[0]
    snapshot_id = data.get("active_snapshot_id")
    if snapshot_id not in snapshots or not snapshot or snapshot.get("id") != snapshot_id:
        errors.append("active_snapshot_id 未唯一指向活动分析快照")
    if snapshot:
        if snapshot.get("claim_set_id") != active_set_id:
            errors.append("活动快照未冻结活动权利要求集合")
        if snapshot.get("primary_strategy_id") != primary_id:
            errors.append("活动快照未冻结唯一主修改策略")
        frozen_payload = {
            "claim_ids": sorted(active_claim_ids),
            "claim_paths": snapshot.get("claim_paths", []),
            "document_eligibility": snapshot.get("document_eligibility", {}),
            "primary_strategy_id": primary_id,
        }
        if snapshot.get("frozen_hash") != stable_digest(frozen_payload):
            errors.append("活动快照 frozen_hash 与冻结内容不一致")

    path_rows = snapshot.get("claim_paths", []) if snapshot else []
    path_ids: set[str] = set()
    expected_keys: set[str] = set()
    for row in path_rows:
        path_id = str(row.get("id", ""))
        claim_id = str(row.get("claim_id", ""))
        if not path_id or path_id in path_ids:
            errors.append("活动快照存在空或重复引用路径ID")
        path_ids.add(path_id)
        if claim_id not in active_claim_ids:
            errors.append(f"引用路径 {path_id} 未绑定活动权利要求")
        expected_keys.add(coverage_key(claim_id, path_id))
    path_claims = {str(row.get("claim_id")) for row in path_rows}
    missing_paths = sorted(active_claim_ids - path_claims)
    if missing_paths:
        errors.append(f"活动权利要求缺少引用路径: {', '.join(missing_paths)}")

    doc_roles = _document_roles(data, snapshot)
    for doc_id, roles in doc_roles.items():
        for axis in ("novelty", "inventive_step"):
            if roles.get(axis) not in ELIGIBILITY:
                errors.append(f"{doc_id} 的 {axis} 资格枚举不合法: {roles.get(axis)}")

    completed: dict[str, set[str]] = {"novelty": set(), "inventive_step": set()}
    for axis, field in (("novelty", "novelty_assessments"), ("inventive_step", "inventive_step_assessments")):
        for item in data[field]:
            label = str(item.get("id", field))
            claim_id = str(item.get("claim_id", ""))
            path_id = str(item.get("path_id", ""))
            is_current = item.get("snapshot_id") == snapshot_id and claim_id in active_claim_ids
            if is_current:
                if item.get("lifecycle_status") != "active":
                    errors.append(f"{label} 属于活动快照但未标为 active")
                if path_id not in path_ids:
                    errors.append(f"{label} 引用不存在的活动路径 {path_id}")
                completed[axis].add(coverage_key(claim_id, path_id))
            elif item.get("lifecycle_status") == "active":
                errors.append(f"旧{axis.upper()}分析 {label} 仍处于活动状态")
            if item.get("assessment_mode") not in ASSESSMENT_MODES:
                errors.append(f"{label} assessment_mode 不合法")
            if item.get("conclusion_status") not in CONCLUSION_STATUSES:
                errors.append(f"{label} conclusion_status 不合法")
            roles = [doc_roles.get(doc_id, {}).get(axis, "Q") for doc_id in _assessment_doc_ids(item, axis)]
            decisive_q = assessment_is_decisive_q(item) or "Q" in roles
            if decisive_q:
                if item.get("conclusion_status") != "undetermined":
                    errors.append(f"决定性 Q 进入 {label} 的肯定或条件性结论")
                if item.get("risk") != "undetermined":
                    errors.append(f"决定性 Q 进入 {label} 的 high/low 等确定性风险")
                if axis == "inventive_step" and item.get("path_status") in {"closed", "complete", "obvious"}:
                    errors.append(f"决定性 Q 下 {label} 的创造性组合路径不得闭合")
            elif "conditional" in roles and item.get("conclusion_status") == "confirmed":
                errors.append(f"条件性文献资格进入 {label} 的 confirmed 结论")
            if axis == "inventive_step":
                bad_docs = [doc_id for doc_id in _assessment_doc_ids(item, axis) if doc_roles.get(doc_id, {}).get(axis) in {"ineligible", "not_applicable"}]
                if bad_docs and item.get("lifecycle_status") == "active":
                    errors.append(f"{label} 使用无创造性资格文献: {', '.join(bad_docs)}")

    if completed["novelty"] != expected_keys:
        errors.append("活动从属项/引用路径的 NB 覆盖不完整")
    if completed["inventive_step"] != expected_keys:
        errors.append("活动从属项/引用路径的 IS 覆盖不完整")

    issues = _items_by_id(data["office_action_issues"])
    registry = data["issue_registry"]
    registry_issue_ids = [str(item.get("issue_id")) for item in registry]
    if set(registry_issue_ids) != set(issues) or len(registry_issue_ids) != len(set(registry_issue_ids)):
        errors.append("问题注册表与 OA 问题未一一对应")
    registry_by_issue = {str(item.get("issue_id")): item for item in registry}
    for issue_id, issue in issues.items():
        row = registry_by_issue.get(issue_id)
        if not row:
            continue
        if issue.get("registry_id") != row.get("id"):
            errors.append(f"{issue_id} 未回指其问题注册表记录")
        if row.get("fingerprint") != issue_fingerprint(issue):
            errors.append(f"{issue_id} 的问题指纹与注册表不一致")

    traced: set[str] = set()
    for trace in data["response_trace"]:
        label = str(trace.get("id", "response_trace"))
        is_current = trace.get("snapshot_id") == snapshot_id and trace.get("claim_version_id") in active_claim_ids
        if is_current:
            if trace.get("lifecycle_status") != "active":
                errors.append(f"{label} 属于活动快照但未标为 active")
            traced.update(str(item) for item in trace.get("issue_ids", []))
        elif trace.get("lifecycle_status") == "active":
            errors.append(f"旧答复追溯 {label} 仍处于活动状态")
    if traced != set(issues):
        errors.append("问题注册表、OA问题与活动答复追溯未100%对应")

    gate = data["recalculation_gate"]
    expected_sorted = sorted(expected_keys)
    if gate.get("snapshot_id") != snapshot_id:
        errors.append("recalculation_gate 未绑定活动快照")
    if set(gate.get("impact_claim_ids", [])) != active_claim_ids:
        errors.append("修改影响闭包与活动权利要求集合不一致")
    if set(gate.get("impact_path_ids", [])) != path_ids:
        errors.append("修改影响闭包与活动引用路径不一致")
    if sorted(set(gate.get("expected_nb_keys", []))) != expected_sorted or sorted(set(gate.get("expected_is_keys", []))) != expected_sorted:
        errors.append("recalculation_gate 的预期NB/IS覆盖集合错误")
    if sorted(set(gate.get("completed_nb_keys", []))) != sorted(completed["novelty"]):
        errors.append("recalculation_gate 的已完成NB集合与实际记录不一致")
    if sorted(set(gate.get("completed_is_keys", []))) != sorted(completed["inventive_step"]):
        errors.append("recalculation_gate 的已完成IS集合与实际记录不一致")
    if not gate.get("response_trace_switched"):
        errors.append("新版本未切换答复追溯")
    if not gate.get("old_analysis_invalidated"):
        errors.append("旧NB/IS或旧答复追溯未失效")
    if not gate.get("passed"):
        errors.append("修改与NB/IS重算门未通过")

    metrics.update(
        {
            "active_claim_set_id": active_set_id,
            "active_snapshot_id": snapshot_id,
            "primary_strategy_id": primary_id,
            "expected_path_coverage": len(expected_keys),
            "nb_path_coverage": len(completed["novelty"]),
            "is_path_coverage": len(completed["inventive_step"]),
            "recalculation_gate_passed": bool(gate.get("passed")),
        }
    )


def find_response(run_dir: Path) -> Path | None:
    exact = run_dir / STANDARD_DELIVERY_FILES["审查意见答复"]
    return exact if exact.is_file() else None


def validate(data: dict[str, Any], run_dir: Path, skip_files: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    metrics: dict[str, Any] = {}

    for key, expected_type in REQUIRED_TOP_LEVEL.items():
        if key not in data:
            errors.append(f"缺少顶层字段: {key}")
        elif not isinstance(data[key], expected_type):
            errors.append(f"字段类型错误: {key} 应为 {expected_type.__name__}")
    if errors:
        return {"passed": False, "errors": errors, "warnings": warnings, "metrics": metrics}
    if data["schema_version"] not in {"2.0-oa", "2.1-oa"}:
        errors.append("schema_version 必须为 2.0-oa 或 2.1-oa")

    case = data["case"]
    for field in ("case_id", "title", "jurisdiction", "primary_mode", "delivery_depth", "case_type"):
        if not case.get(field):
            errors.append(f"case 缺少必需值: {field}")
    dupes = duplicate_ids(data)
    if dupes:
        errors.append(f"存在重复 ID: {', '.join(dupes)}")

    document_ids = {item.get("id") for item in data["documents"]}
    claim_ids = {item.get("id") for item in data["claims"]}
    feature_ids = {item.get("id") for item in data["feature_groups"]}
    evidence_ids = {item.get("id") for item in data["evidence"]}
    issue_ids = {item.get("id") for item in data["office_action_issues"]}

    for document in data["documents"]:
        eligibility = document.get("eligibility")
        if not isinstance(eligibility, dict):
            errors.append(f"{document.get('id')} 缺少 eligibility")
            continue
        for field in ("novelty", "inventive_step", "status", "reason"):
            if field not in eligibility:
                errors.append(f"{document.get('id')} eligibility 缺少 {field}")
    for claim in data["claims"]:
        for field in ("id", "version", "text", "feature_group_ids", "status"):
            if field not in claim:
                errors.append(f"权利要求 {claim.get('id')} 缺少 {field}")
        if claim.get("supersedes") and claim["supersedes"] not in claim_ids:
            errors.append(f"{claim.get('id')} 的 supersedes 指向不存在的权利要求")
        for feature_id in claim.get("feature_group_ids", []):
            if feature_id not in feature_ids:
                errors.append(f"{claim.get('id')} 引用不存在的特征组 {feature_id}")
    for ev in data["evidence"]:
        if ev.get("document_id") not in document_ids:
            errors.append(f"{ev.get('id')} 引用不存在的文献 {ev.get('document_id')}")
    for nb in data["novelty_assessments"]:
        if nb.get("claim_id") not in claim_ids:
            errors.append(f"{nb.get('id')} 引用不存在的权利要求")
        if isinstance(nb.get("document_id"), list):
            errors.append(f"{nb.get('id')} 违反新颖性单文献规则")
        elif nb.get("document_id") not in document_ids:
            errors.append(f"{nb.get('id')} 引用不存在的文献")
    for item in data["inventive_step_assessments"]:
        if item.get("claim_id") not in claim_ids:
            errors.append(f"{item.get('id')} 引用不存在的权利要求")
        if item.get("closest_document_id") not in document_ids:
            errors.append(f"{item.get('id')} 引用不存在的最接近现有技术")

    allowed_handling = {"admit", "argue", "amend", "delete", "divide", "verify", "client_confirm"}
    for issue in data["office_action_issues"]:
        for field in ("id", "type", "claim_ids", "assertion", "fact_audit_status", "handling", "response_location", "status"):
            if field not in issue:
                errors.append(f"问题 {issue.get('id')} 缺少 {field}")
        bad_actions = sorted(set(_handling_values(issue.get("handling"))) - allowed_handling)
        if bad_actions:
            errors.append(f"{issue.get('id')} 的处理动作不合法: {', '.join(bad_actions)}")
        for claim_id in issue.get("claim_ids", []):
            if claim_id not in claim_ids:
                errors.append(f"{issue.get('id')} 引用不存在的权利要求 {claim_id}")
        for evidence_id in issue.get("evidence_refs", []):
            if evidence_id not in evidence_ids:
                errors.append(f"{issue.get('id')} 引用不存在的证据 {evidence_id}")

    amendments_to = {claim_id for event in data["claim_amendment_events"] for claim_id in event.get("to_claim_ids", [])}
    modified_claims = {claim["id"] for claim in data["claims"] if claim.get("supersedes")}
    missing_events = sorted(modified_claims - amendments_to)
    if missing_events:
        errors.append(f"新版权利要求缺少修改事件: {', '.join(missing_events)}")

    readiness = data["readiness"]
    if readiness.get("content_status") not in {"pass", "conditional", "fail"}:
        errors.append("readiness.content_status 不合法")
    if readiness.get("submission_status") not in {"ready", "blocked"}:
        errors.append("readiness.submission_status 不合法")
    for field in ("blockers", "client_confirmation_required"):
        if not isinstance(readiness.get(field), list):
            errors.append(f"readiness.{field} 必须为数组")
    has_blockers = bool(readiness.get("blockers") or readiness.get("client_confirmation_required"))
    if readiness.get("submission_status") == "ready" and (has_blockers or readiness.get("content_status") != "pass"):
        errors.append("存在阻塞项或内容未通过，submission_status 不得为 ready")

    if data["schema_version"] == "2.1-oa":
        _validate_v21(data, errors, metrics)
    else:
        warnings.append("v2.0-oa 仅执行兼容性基础校验；须规范化到 v2.1-oa 才能通过活动集合与重算硬门。")

    if not skip_files:
        for label, filename in STANDARD_DELIVERY_FILES.items():
            if not (run_dir / filename).is_file():
                errors.append(f"缺少标准交付文件: {label} ({filename})")
        response = find_response(run_dir)
        if response:
            text = response.read_text(encoding="utf-8")
            hits = [match.group(0) for pattern in INTERNAL_ID_PATTERNS for match in pattern.finditer(text)]
            if hits:
                errors.append(f"对外答复存在内部 ID/节点符号: {', '.join(sorted(set(hits)))}")
        else:
            errors.append("未找到标准文件 07-审查意见答复.md")

    traced_issues = {
        str(issue_id)
        for trace in data["response_trace"]
        for issue_id in trace.get("issue_ids", [])
        if issue_id in issue_ids
    }
    total_issues = len(data["office_action_issues"])
    metrics.update(
        {
            "documents": len(data["documents"]),
            "claims": len(data["claims"]),
            "issues": total_issues,
            "trace_rows": len(data["response_trace"]),
            "issue_trace_coverage": round(len(traced_issues) / total_issues, 4) if total_issues else 0,
            "content_status": readiness.get("content_status"),
            "submission_status": readiness.get("submission_status"),
        }
    )
    if total_issues == 0:
        warnings.append("未结构化识别 office_action_issues；无法评价问题覆盖率。")
    return {"passed": not errors, "errors": errors, "warnings": warnings, "metrics": metrics}


def main() -> int:
    args = parse_args()
    run_dir = args.run_dir.resolve()
    pack_path = (args.evidence_pack or (run_dir / "02-patent_evidence_pack.json")).resolve()
    try:
        data = json.loads(pack_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report = {"passed": False, "errors": [f"证据包读取失败: {exc}"], "warnings": [], "metrics": {}}
    else:
        report = validate(data, run_dir, args.skip_delivery_files)
    report.update({"run_dir": str(run_dir), "evidence_pack": str(pack_path)})
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
