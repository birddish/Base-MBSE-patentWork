#!/usr/bin/env python3
"""Create a fresh, non-overwriting v2.2-oa pack from a stage-zero 1.1 source pack."""

from __future__ import annotations

import argparse
import copy
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from oa_v22_contract import V22_TOP_LEVEL, create_v22


REQUIRED_TOP_LEVEL = (
    "schema_version",
    "case",
    "documents",
    "claims",
    "feature_groups",
    "evidence",
    "novelty_assessments",
    "inventive_step_assessments",
    "office_action_issues",
    "claim_amendment_events",
    "response_trace",
    "readiness",
    "version_history",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="stage-zero pre-application 1.1 patent_evidence_pack.json")
    parser.add_argument("output", type=Path, help="new v2.2-oa JSON path; must differ from input")
    parser.add_argument("--run-dir", type=Path, help="delivery directory used to recover OA issues and response trace")
    return parser.parse_args()


def safe_date(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return None


def doc_id(value: str) -> str:
    return value if value.startswith("DOC-") else f"DOC-{value}"


def normalize_status(value: Any) -> str:
    return value if value in {"D", "I", "Q", "X"} else "Q"


def infer_issue_type(assertion: str) -> str:
    if "新颖" in assertion or "全部技术特征" in assertion:
        return "novelty"
    if "创造" in assertion or "容易联想" in assertion or "简单变换" in assertion:
        return "inventive_step"
    if "清楚" in assertion or "引用关系" in assertion:
        return "clarity"
    if "支持" in assertion:
        return "support"
    if "单一" in assertion:
        return "unity"
    if "治疗" in assertion or "疾病" in assertion:
        return "subject_matter"
    return "other"


def infer_handling(issue_type: str, fact_status: str) -> str:
    if fact_status in {"unsupported", "partly_supported", "not_found"}:
        return "argue"
    return {
        "novelty": "amend",
        "inventive_step": "argue",
        "clarity": "amend",
        "support": "amend",
        "unity": "divide",
        "subject_matter": "delete",
    }.get(issue_type, "verify")


def fact_status(text: str) -> str:
    if "部分支持" in text:
        return "partly_supported"
    if "不支持" in text:
        return "unsupported"
    if "无记录" in text or "无记载" in text:
        return "not_found"
    if "支持" in text:
        return "supported"
    return "Q"


def parse_issue_rows(run_dir: Path | None) -> list[dict[str, Any]]:
    if not run_dir:
        return []
    reports = list(run_dir.glob("*事实核实审计报告.md"))
    if not reports:
        return []
    lines = reports[0].read_text(encoding="utf-8").splitlines()
    issues: list[dict[str, Any]] = []
    for line in lines:
        if not re.match(r"^\|\s*F-\d+\s*\|", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        legacy_id = cells[0]
        assertion = cells[1]
        conclusion = next((cell for cell in reversed(cells) if any(k in cell for k in ("支持", "无记", "待核"))), "")
        status = fact_status(conclusion)
        issue_type = infer_issue_type(assertion)
        issues.append(
            {
                "id": f"OA-{int(legacy_id.split('-')[1]):02d}",
                "legacy_fact_audit_id": legacy_id,
                "type": issue_type,
                "claim_ids": [],
                "assertion": assertion,
                "fact_audit_status": status,
                "handling": infer_handling(issue_type, status),
                "evidence_refs": [],
                "response_location": "审查意见答复（按问题类型对应段落）",
                "status": "closed" if list(run_dir.glob("*审查意见答复.md")) else "open",
            }
        )
    return issues


def normalize_documents(data: dict[str, Any], reference_date: str | None) -> tuple[list[dict[str, Any]], dict[str, str]]:
    normalized: list[dict[str, Any]] = []
    id_map: dict[str, str] = {}
    for raw in data.get("documents", []):
        old_id = str(raw.get("id", f"LEGACY-{len(normalized)+1}"))
        new_id = doc_id(old_id)
        id_map[old_id] = new_id
        role = str(raw.get("role", "other"))
        publication_date = safe_date(raw.get("publication_date"))
        status = normalize_status(raw.get("status", raw.get("date_status")))
        novelty = inventive = "not_applicable"
        reason = "申请文件或程序文件，不作现有技术资格判断。"
        if "conflicting_application" in role:
            novelty, inventive = "Q", "ineligible"
            reason = "旧包标记为抵触申请候选；新颖性资格待核验，不得用于创造性。"
        elif "prior_art" in role:
            if publication_date and reference_date:
                novelty = inventive = "eligible" if publication_date < reference_date else "ineligible"
                reason = "依旧包记录的公开日与案件基准日比较；正式稿仍应核对官方书目信息。"
            else:
                novelty = inventive = "Q"
                reason = "公开日或案件基准日不足，文献资格待核验。"
        normalized.append(
            {
                "id": new_id,
                "role": role,
                "publication_number": raw.get("publication_number"),
                "publication_date": publication_date,
                "bibliographic_source": raw.get("bibliographic_source", raw.get("note", "")),
                "eligibility": {
                    "novelty": novelty,
                    "inventive_step": inventive,
                    "status": "Q" if "Q" in {novelty, inventive} else status,
                    "reason": reason,
                },
                "status": status,
                "legacy_role": role,
            }
        )
    return normalized, id_map


def current_claim_ids(claims: list[dict[str, Any]]) -> list[str]:
    superseded = {claim.get("supersedes") for claim in claims if claim.get("supersedes")}
    return [str(claim["id"]) for claim in claims if claim.get("id") not in superseded and claim.get("status") != "X"]


def ensure_claim_version_chain(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = copy.deepcopy(claims)
    existing = {claim.get("id") for claim in result}
    placeholders: list[dict[str, Any]] = []
    for index, claim in enumerate(result, start=1):
        version = str(claim.get("version", ""))
        if version and version not in {"original", "v0", "v0.1"} and not claim.get("supersedes"):
            placeholder_id = f"CLM-LEGACY-SOURCE-Q-{index:02d}"
            while placeholder_id in existing:
                placeholder_id += "X"
            placeholders.append(
                {
                    "id": placeholder_id,
                    "version": "legacy-source-unstructured",
                    "text": "旧证据包未结构化记录该新权利要求的直接前驱文本。",
                    "feature_group_ids": [],
                    "status": "Q",
                }
            )
            claim["supersedes"] = placeholder_id
            existing.add(placeholder_id)
    return placeholders + result


def normalize_v1(data: dict[str, Any], run_dir: Path | None) -> dict[str, Any]:
    raw_case = data.get("case", {})
    reference_date = safe_date(raw_case.get("reference_date") or raw_case.get("application_date"))
    documents, id_map = normalize_documents(data, reference_date)
    claims = ensure_claim_version_chain(data.get("claims", []))
    evidence = copy.deepcopy(data.get("evidence", []))
    for item in evidence:
        item["document_id"] = id_map.get(str(item.get("document_id")), doc_id(str(item.get("document_id"))))
    novelty = copy.deepcopy(data.get("novelty_assessments", []))
    for item in novelty:
        item["document_id"] = id_map.get(str(item.get("document_id")), doc_id(str(item.get("document_id"))))
    inventive = copy.deepcopy(data.get("inventive_step_assessments", []))
    for item in inventive:
        if item.get("closest_document_id"):
            item["closest_document_id"] = id_map.get(str(item["closest_document_id"]), doc_id(str(item["closest_document_id"])))
    issues = parse_issue_rows(run_dir)
    latest_claims = current_claim_ids(claims)
    for issue in issues:
        issue["claim_ids"] = latest_claims
        issue["evidence_refs"] = [item["id"] for item in evidence if item.get("document_id") == "DOC-OA"][:1]
    assessment_ids = [item.get("id") for item in novelty + inventive if item.get("id")]
    traces = [
        {
            "id": f"RT-{index:02d}",
            "response_section": issue["response_location"],
            "claim_version_id": latest_claims[0] if latest_claims else None,
            "issue_ids": [issue["id"]],
            "fact_refs": issue["evidence_refs"],
            "path_refs": assessment_ids,
            "conclusion": f"旧交付已以{issue['handling']}作为主处理动作；本行为回归结构化映射。",
            "status": "draft",
        }
        for index, issue in enumerate(issues, start=1)
    ]
    amendment_events: list[dict[str, Any]] = []
    claim_index = {claim["id"]: claim for claim in claims if claim.get("id")}
    for index, claim in enumerate(claims, start=1):
        if not claim.get("supersedes"):
            continue
        support_refs: list[str] = []
        for cf in data.get("feature_groups", []):
            if cf.get("id") in claim.get("feature_group_ids", []):
                support_refs.extend(cf.get("source_refs", []))
        recalculated = any(item.get("claim_id") == claim.get("id") for item in novelty + inventive)
        amendment_events.append(
            {
                "id": f"AMD-{index:02d}",
                "from_claim_ids": [claim["supersedes"]],
                "to_claim_ids": [claim["id"]],
                "change_type": "divide" if "DIV" in claim["id"] else "add_limit",
                "support_refs": sorted(set(support_refs)),
                "scope_effect": "divided" if "DIV" in claim["id"] else "narrower",
                "target_issue_ids": [issue["id"] for issue in issues],
                "client_confirmation_required": "DIV" in claim["id"],
                "recalculation_status": "complete" if recalculated else "Q",
            }
        )
    blockers = ["本包为旧交付的回归结构化副本，未核验官方提交期限和形式信息。"]
    if any(doc["status"] == "Q" or doc["eligibility"]["status"] == "Q" for doc in documents):
        blockers.append("至少一篇文献的书目/时间资格或完整性待核验。")
    return {
        "schema_version": "stage-zero-normalized",
        "case": {
            "case_id": raw_case.get("case_id", "LEGACY-CASE-Q"),
            "title": raw_case.get("title", "旧包未记录标题"),
            "jurisdiction": raw_case.get("jurisdiction", "CN"),
            "reference_date": reference_date,
            "application_date": safe_date(raw_case.get("application_date")),
            "primary_mode": raw_case.get("oa_mode", "mechanical"),
            "auxiliary_views": [],
            "delivery_depth": "standard",
            "case_type": "office_action",
            "status": raw_case.get("status", "draft"),
        },
        "documents": documents,
        "claims": claims,
        "feature_groups": copy.deepcopy(data.get("feature_groups", [])),
        "evidence": evidence,
        "novelty_assessments": novelty,
        "inventive_step_assessments": inventive,
        "office_action_issues": issues,
        "claim_amendment_events": amendment_events,
        "response_trace": traces,
        "readiness": {
            "content_status": "conditional" if blockers else "pass",
            "submission_status": "blocked",
            "blockers": blockers,
            "client_confirmation_required": ["核实最终权利要求范围取舍和正式提交信息。"],
        },
        "version_history": copy.deepcopy(data.get("version_history", []))
        + [{"version": "stage-zero-normalized", "change": "从申请前1.1来源建立阶段零内部表示。", "status": "draft"}],
        "legacy_prosecution_events": copy.deepcopy(data.get("prosecution_events", [])),
    }


def normalize_case3(data: dict[str, Any], run_dir: Path | None) -> dict[str, Any]:
    application = data.get("application", {})
    reference_date = safe_date(application.get("application_date"))
    documents, id_map = normalize_documents(data, reference_date)
    legacy_claims = data.get("claim_objects", [])
    evidence = [
        {
            "id": "EV-LEGACY-Q-01",
            "document_id": id_map.get("AP", "DOC-AP"),
            "location": "旧证据包的 claim_objects.features；详细支持位置见原交付报告",
            "excerpt_or_summary": "旧包未在 JSON 中按特征结构化记录原文位置。",
            "fact_status": "Q",
        }
    ]
    feature_groups: list[dict[str, Any]] = []
    claims: list[dict[str, Any]] = [
        {
            "id": "CLM-ORIGINAL-Q",
            "version": "legacy-source-unstructured",
            "text": "旧证据包未结构化记录原权利要求全文。",
            "feature_group_ids": [],
            "status": "Q",
        }
    ]
    for claim_index, raw_claim in enumerate(legacy_claims, start=1):
        cf_ids: list[str] = []
        for feature_index, feature in enumerate(raw_claim.get("features", []), start=1):
            cf_id = f"CF-{claim_index:02d}-{feature_index:02d}"
            cf_ids.append(cf_id)
            feature_groups.append(
                {
                    "id": cf_id,
                    "text": feature,
                    "node_ids": [],
                    "relation_ids": [],
                    "source_refs": ["EV-LEGACY-Q-01"],
                    "description_support_refs": [],
                    "status": "Q",
                }
            )
        claims.append(
            {
                "id": "CLM-NEW-01" if claim_index == 1 else f"CLM-NEW-{claim_index:02d}",
                "legacy_id": raw_claim.get("id"),
                "version": "proposed-v1",
                "supersedes": "CLM-ORIGINAL-Q",
                "text": "；".join(raw_claim.get("features", [])),
                "feature_group_ids": cf_ids,
                "status": "Q",
            }
        )
    novelty: list[dict[str, Any]] = []
    for index, block in enumerate(data.get("novelty_blocks", []), start=1):
        novelty.append(
            {
                "id": f"NB-{index:02d}",
                "claim_id": "CLM-NEW-01",
                "document_id": id_map.get(str(block.get("document")), doc_id(str(block.get("document")))),
                "date_status": "Q",
                "feature_coverage": [],
                "single_document_rule": True,
                "risk": "undetermined",
                "reason": "; ".join(block.get("missing_or_not_integrally_disclosed", [])),
                "status": "draft",
                "legacy_result": block.get("result"),
            }
        )
    legacy_is = data.get("inventive_step", {})
    inventive = [
        {
            "id": "IS-01",
            "claim_id": "CLM-NEW-01",
            "closest_document_id": id_map.get(str(legacy_is.get("closest_prior_art")), doc_id(str(legacy_is.get("closest_prior_art")))),
            "distinguishing_feature_group_ids": [],
            "technical_effects": [],
            "objective_technical_problem": "申请前1.1来源未按OA结构记录，见原追溯链报告。",
            "combination_candidates": [],
            "engineering_analysis_refs": legacy_is.get("fusion_failures", []),
            "risk": "undetermined",
            "status": "draft",
            "legacy_core_gap": legacy_is.get("core_gap"),
        }
    ]
    issues = parse_issue_rows(run_dir)
    for issue in issues:
        issue["claim_ids"] = ["CLM-NEW-01"]
    traces = [
        {
            "id": f"RT-{index:02d}",
            "response_section": issue["response_location"],
            "claim_version_id": "CLM-NEW-01",
            "issue_ids": [issue["id"]],
            "fact_refs": [],
            "path_refs": ["IS-01"],
            "conclusion": f"旧交付已以{issue['handling']}作为主处理动作；本行为回归结构化映射。",
            "status": "draft",
        }
        for index, issue in enumerate(issues, start=1)
    ]
    return {
        "schema_version": "stage-zero-normalized",
        "case": {
            "case_id": data.get("case_id", "LEGACY-CASE-Q"),
            "title": application.get("title", "旧包未记录标题"),
            "jurisdiction": "CN",
            "reference_date": reference_date,
            "application_date": reference_date,
            "primary_mode": data.get("field_mode", "mechanical"),
            "auxiliary_views": [],
            "delivery_depth": "standard",
            "case_type": "office_action",
            "status": "draft",
        },
        "documents": documents,
        "claims": claims,
        "feature_groups": feature_groups,
        "evidence": evidence,
        "novelty_assessments": novelty,
        "inventive_step_assessments": inventive,
        "office_action_issues": issues,
        "claim_amendment_events": [
            {
                "id": "AMD-01",
                "from_claim_ids": ["CLM-ORIGINAL-Q"],
                "to_claim_ids": ["CLM-NEW-01"],
                "change_type": "add_limit",
                "support_refs": ["EV-LEGACY-Q-01"],
                "scope_effect": "narrower",
                "target_issue_ids": [issue["id"] for issue in issues],
                "client_confirmation_required": True,
                "recalculation_status": "Q",
            }
        ],
        "response_trace": traces,
        "readiness": {
            "content_status": "conditional",
            "submission_status": "blocked",
            "blockers": [
                "D1 公开日存在两种记载，抵触申请条件待官方核验。",
                "旧证据包未结构化记录原权利要求和全部支持位置。",
                "未核验官方提交期限与形式信息。",
            ],
            "client_confirmation_required": ["确认修改后权利要求的保护范围取舍。"],
        },
        "version_history": [
            {"version": "stage-zero-normalized", "change": "从申请前1.1来源建立阶段零内部表示。", "status": "draft"}
        ],
        "legacy_payload": copy.deepcopy(data),
    }


def main() -> int:
    args = parse_args()
    input_path = args.input.resolve()
    output_path = args.output.resolve()
    if input_path == output_path:
        raise SystemExit("拒绝覆盖原证据包；请指定新输出路径。")
    data = json.loads(input_path.read_text(encoding="utf-8"))
    run_dir = args.run_dir.resolve() if args.run_dir else input_path.parent
    source_schema = data.get("schema_version")
    if source_schema in {"2.0-oa", "2.1-oa", "v2.1-oa"}:
        raise SystemExit("拒绝旧OA证据包：2.0/2.1均不支持迁移；请从申请前1.1材料新建V2.2案件。")
    if source_schema not in {"1.1", "patent-evidence-pack/1.1"}:
        raise SystemExit(f"仅接受申请前1.1证据包作为阶段零来源，当前schema={source_schema!r}。")
    if isinstance(data.get("case"), dict):
        base = normalize_v1(data, run_dir)
    else:
        base = normalize_case3(data, run_dir)
    normalized = create_v22(base)
    missing = [key for key in (*REQUIRED_TOP_LEVEL, *V22_TOP_LEVEL) if key not in normalized]
    if missing:
        raise SystemExit(f"内部错误：标准化结果缺少 {missing}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"normalized: {input_path}")
    print(f"output: {output_path}")
    print(f"schema: {normalized['schema_version']}; gate: {normalized['recalculation_gate']['passed']}")
    print(f"issues: {len(normalized['office_action_issues'])}; traces: {len(normalized['response_trace'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
