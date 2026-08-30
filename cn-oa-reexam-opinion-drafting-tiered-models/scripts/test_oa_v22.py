from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from oa_v22_contract import create_v22, stable_digest
from validate_oa_delivery import validate


def base_source() -> dict:
    return {
        "schema_version": "internal-stage-zero",
        "case": {"case_id": "CASE-1", "title": "测试案件", "jurisdiction": "CN", "reference_date": "2025-01-01",
                 "application_date": "2025-01-01", "primary_mode": "mechanical", "delivery_depth": "standard",
                 "case_type": "office_action", "status": "draft"},
        "documents": [{"id": "DOC-D1", "role": "prior_art", "publication_number": "CN1", "publication_date": "2020-01-01",
                       "eligibility": {"novelty": "eligible", "inventive_step": "eligible", "status": "D", "reason": "官方书目信息已核验"}, "status": "D"}],
        "claims": [
            {"id": "CLM-OLD", "version": "v0", "text": "旧权利要求", "feature_group_ids": ["CF-1"], "status": "X", "claim_type": "independent", "depends_on_claim_ids": []},
            {"id": "CLM-1", "version": "v1", "supersedes": "CLM-OLD", "text": "一种装置，包括特征A。", "feature_group_ids": ["CF-1"], "status": "D", "claim_type": "independent", "depends_on_claim_ids": []},
            {"id": "CLM-2", "version": "v1", "text": "根据权利要求1所述的装置，还包括特征B。", "feature_group_ids": ["CF-1", "CF-2"], "status": "D", "claim_type": "dependent", "depends_on_claim_ids": ["CLM-1"]},
        ],
        "feature_groups": [{"id": "CF-1", "text": "特征A", "status": "D"}, {"id": "CF-2", "text": "特征B", "status": "D"}],
        "evidence": [{"id": "EV-1", "document_id": "DOC-D1", "location": "权利要求1", "fact_status": "D"}],
        "novelty_assessments": [
            {"id": "NB-1", "claim_id": "CLM-1", "document_id": "DOC-D1", "feature_coverage": [{"cf_id": "CF-1", "status": "D"}], "single_document_rule": True, "risk": "low", "status": "reviewed"},
            {"id": "NB-2", "claim_id": "CLM-2", "document_id": "DOC-D1", "feature_coverage": [{"cf_id": "CF-1", "status": "D"}, {"cf_id": "CF-2", "status": "D"}], "single_document_rule": True, "risk": "low", "status": "reviewed"},
        ],
        "inventive_step_assessments": [
            {"id": "IS-1", "claim_id": "CLM-1", "closest_document_id": "DOC-D1", "distinguishing_feature_group_ids": ["CF-1"], "technical_effects": [{"status": "D"}], "objective_technical_problem": "如何改善性能", "combination_candidates": [], "risk": "low", "path_status": "complete", "status": "reviewed"},
            {"id": "IS-2", "claim_id": "CLM-2", "closest_document_id": "DOC-D1", "distinguishing_feature_group_ids": ["CF-2"], "technical_effects": [{"status": "D"}], "objective_technical_problem": "如何改善可靠性", "combination_candidates": [], "risk": "low", "path_status": "complete", "status": "reviewed"},
        ],
        "office_action_issues": [{"id": "OA-1", "type": "inventive_step", "claim_ids": ["CLM-1", "CLM-2"], "assertion": "缺乏创造性", "fact_audit_status": "supported", "handling": "argue", "evidence_refs": ["EV-1"], "response_location": "答复第一部分", "status": "open"}],
        "claim_amendment_events": [{"id": "AMD-1", "from_claim_ids": ["CLM-OLD"], "to_claim_ids": ["CLM-1"], "change_type": "add_limit", "support_refs": ["EV-1"], "scope_effect": "narrower", "target_issue_ids": ["OA-1"], "client_confirmation_required": False, "recalculation_status": "complete"}],
        "response_trace": [{"id": "RT-1", "response_section": "答复第一部分", "claim_version_id": "CLM-1", "issue_ids": ["OA-1"], "fact_refs": ["EV-1"], "path_refs": ["IS-1"], "conclusion": "当前组合不足以证明显而易见", "status": "reviewed"}],
        "readiness": {"content_status": "pass", "submission_status": "ready", "blockers": [], "client_confirmation_required": []},
        "version_history": [],
    }


def write_manifest(root: Path, pack: dict) -> None:
    snapshot = next(item for item in pack["analysis_snapshots"] if item["id"] == pack.get("active_snapshot_id"))
    claim_set = next(item for item in pack["claim_sets"] if item["id"] == pack.get("active_claim_set_id"))
    digest = lambda value: "sha256:" + stable_digest(value).lower()
    manifest = {"schema_version": "oa-context-manifest/2.0", "case_id": pack["case"]["case_id"], "execution_mode": "advisory",
                "upstream_snapshot_id": "SNAP-1", "upstream_snapshot_hash": "sha256:" + "0" * 64,
                "oa_active_snapshot_id": pack.get("active_snapshot_id"), "oa_active_snapshot_hash": digest(snapshot),
                "active_claim_set_id": pack.get("active_claim_set_id"), "active_claim_set_hash": digest(claim_set),
                "primary_strategy_id": pack.get("primary_strategy_id"),
                "issue_ids": [item["id"] for item in pack.get("office_action_issues", [])],
                "document_eligibility_version": snapshot.get("document_eligibility_version"),
                "evidence_pack_path": "patent_evidence_pack.json", "evidence_pack_schema": "v2.2-oa",
                "evidence_pack_hash": "sha256:" + "3" * 64,
                "recalculation_gate_passed": bool(pack.get("recalculation_gate", {}).get("passed")),
                "legacy_snapshot_ids": [], "blocked_by": []}
    (root / "oa_context_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def report(pack: dict) -> dict:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp); write_manifest(root, pack)
        return validate(pack, root, skip_files=True)


def assert_error(pack: dict, needle: str) -> None:
    result = report(pack)
    assert not result["passed"] and any(needle in item for item in result["errors"]), (needle, result)


def report_with_manifest_changes(pack: dict, changes: dict) -> dict:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp); write_manifest(root, pack)
        path = root / "oa_context_manifest.json"; manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest.update(changes); path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return validate(pack, root, skip_files=True)


def main() -> int:
    pack = create_v22(base_source())
    positive = report(pack)
    assert positive["passed"], positive

    old = copy.deepcopy(pack); old["schema_version"] = "v2.1-oa"
    assert_error(old, "旧OA")

    ineligible = copy.deepcopy(pack)
    ineligible["documents"][0]["eligibility"]["novelty"] = "ineligible"
    ineligible["analysis_snapshots"][0]["document_eligibility"]["DOC-D1"]["novelty"] = "ineligible"
    assert_error(ineligible, "无资格、Q或决定性Q")

    overall_q = copy.deepcopy(pack)
    overall_q["documents"][0]["eligibility"]["status"] = "Q"
    overall_q["analysis_snapshots"][0]["document_eligibility"]["DOC-D1"]["status"] = "Q"
    assert_error(overall_q, "无资格、Q或决定性Q")

    missing_nb_status = copy.deepcopy(pack); missing_nb_status["novelty_assessments"][0]["feature_coverage"][0].pop("status")
    assert_error(missing_nb_status, "缺少合法事实状态")
    missing_effect_status = copy.deepcopy(pack); missing_effect_status["inventive_step_assessments"][0]["technical_effects"][0].pop("status")
    assert_error(missing_effect_status, "缺少合法事实状态")
    empty_reason = copy.deepcopy(pack); empty_reason["documents"][0]["eligibility"]["reason"] = ""
    assert_error(empty_reason, "reason必须为非空")

    changed_claim = copy.deepcopy(pack); changed_claim["claims"][1]["text"] = "完全不同的权利要求正文"; changed_claim["claims"][1]["feature_group_ids"] = ["CF-2"]
    assert_error(changed_claim, "未冻结当前权利要求正文")

    live_drift = copy.deepcopy(pack)
    live_drift["documents"][0]["eligibility"].update(novelty="ineligible", status="Q")
    assert_error(live_drift, "当前documents资格对象不一致")

    missing_dependency_source = base_source(); missing_dependency_source["claims"][2].pop("depends_on_claim_ids")
    blocked = create_v22(missing_dependency_source)
    assert blocked["active_snapshot_id"] is None
    assert blocked["claim_dependency_graph"]["status"] == "blocked"
    assert all("SELF" not in str(row.get("id")) for row in blocked["analysis_snapshots"][0]["claim_paths"])

    empty_dependency_source = base_source(); empty_dependency_source["claims"][2]["depends_on_claim_ids"] = []
    empty_dependency = create_v22(empty_dependency_source)
    assert empty_dependency["active_snapshot_id"] is None
    assert any("至少一个父项" in item for item in empty_dependency["claim_dependency_graph"]["errors"])

    extra_parent_source = base_source()
    extra_parent_source["claims"].append({"id": "CLM-3", "version": "v1", "text": "一种另一装置，包括特征A。",
                                           "feature_group_ids": ["CF-1"], "status": "D", "claim_type": "independent",
                                           "depends_on_claim_ids": []})
    extra_parent_source["claims"][2]["depends_on_claim_ids"] = ["CLM-1", "CLM-3"]
    extra_parent = create_v22(extra_parent_source)
    assert extra_parent["active_snapshot_id"] is None
    assert any("正文引用与depends_on_claim_ids不一致" in item for item in extra_parent["claim_dependency_graph"]["errors"])

    duplicate_number_source = base_source(); duplicate_number_source["claims"][1]["claim_number"] = 1
    duplicate_number_source["claims"].append({"id": "CLM-3", "claim_number": 1, "version": "v1", "text": "另一独立权利要求",
                                               "feature_group_ids": ["CF-1"], "status": "D", "claim_type": "independent",
                                               "depends_on_claim_ids": []})
    duplicate_number = create_v22(duplicate_number_source)
    assert duplicate_number["active_snapshot_id"] is None
    assert any("claim_number重复" in item for item in duplicate_number["claim_dependency_graph"]["errors"])

    cyclic_source = base_source(); cyclic_source["claims"][1]["depends_on_claim_ids"] = ["CLM-2"]; cyclic_source["claims"][1]["claim_type"] = "dependent"
    cyclic = create_v22(cyclic_source)
    assert cyclic["active_snapshot_id"] is None and any("环" in item for item in cyclic["claim_dependency_graph"]["errors"])

    duplicate_nb = copy.deepcopy(pack); row = copy.deepcopy(duplicate_nb["novelty_assessments"][0]); row["id"] = "NB-DUP"; duplicate_nb["novelty_assessments"].append(row)
    assert_error(duplicate_nb, "复合唯一键")

    duplicate_summary = copy.deepcopy(pack); row = copy.deepcopy(duplicate_summary["novelty_summaries"][0]); row["id"] = "NBS-DUP"; duplicate_summary["novelty_summaries"].append(row)
    assert_error(duplicate_summary, "汇总结论唯一键")

    omitted_card = copy.deepcopy(pack); row = copy.deepcopy(omitted_card["novelty_assessments"][0]); row["id"] = "NB-EXTRA"; row["conclusion_status"] = "conditional"; row["risk"] = "undetermined"; omitted_card["novelty_assessments"].append(row)
    assert_error(omitted_card, "全部活动判断卡")

    wrong_closure = copy.deepcopy(pack); wrong_closure["recalculation_gate"]["impact_claim_ids"] = ["CLM-1"]
    assert_error(wrong_closure, "真实全案覆盖或局部影响闭包")

    old_active = copy.deepcopy(pack); row = copy.deepcopy(old_active["inventive_step_assessments"][0]); row["id"] = "IS-OLD"; row["snapshot_id"] = "OA-SNAP-OLD"; row["lifecycle_status"] = "active"; old_active["inventive_step_assessments"].append(row)
    assert_error(old_active, "仍处于active")

    missing_path = copy.deepcopy(pack); missing_path["inventive_step_assessments"][0].pop("path_id")
    assert_error(missing_path, "完整引用路径")

    bad_manifest = report_with_manifest_changes(pack, {"oa_active_snapshot_hash": "sha256:" + "9" * 64,
                                                        "active_claim_set_hash": "sha256:" + "8" * 64,
                                                        "primary_strategy_id": "STR-WRONG", "issue_ids": [],
                                                        "document_eligibility_version": "ELIG-WRONG"})
    assert not bad_manifest["passed"] and any("oa_context_manifest" in item for item in bad_manifest["errors"]), bad_manifest

    incomplete_combo = copy.deepcopy(pack); incomplete_combo["inventive_step_assessments"][0]["combination_candidates"] = [{"document_id": "DOC-D1", "motivation": "D"}]
    assert_error(incomplete_combo, "组合候选缺少")

    gate_false = copy.deepcopy(pack); gate_false["recalculation_gate"]["passed"] = False
    assert_error(gate_false, "不得形成正式OA交付")

    no_issue_source = base_source(); no_issue_source["office_action_issues"] = []; no_issue_source["response_trace"] = []
    no_issue = create_v22(no_issue_source)
    assert_error(no_issue, "至少登记一个有效审查问题")

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp); old_path = root / "old.json"; output_path = root / "new.json"
        old_path.write_text(json.dumps({"schema_version": "v2.1-oa"}), encoding="utf-8")
        command = [sys.executable, str(Path(__file__).with_name("normalize_oa_evidence_pack.py")), str(old_path), str(output_path)]
        rejected = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        assert rejected.returncode != 0 and "拒绝旧OA证据包" in (rejected.stdout + rejected.stderr)

        source = base_source(); source["schema_version"] = "1.1"; source_path = root / "source-1.1.json"
        source_path.write_text(json.dumps(source, ensure_ascii=False), encoding="utf-8")
        accepted = subprocess.run([sys.executable, str(Path(__file__).with_name("normalize_oa_evidence_pack.py")), str(source_path), str(output_path)], capture_output=True, text=True, encoding="utf-8")
        assert accepted.returncode == 0, accepted.stdout + accepted.stderr
        assert json.loads(output_path.read_text(encoding="utf-8"))["schema_version"] == "v2.2-oa"

    print("v2.2-oa positive and negative substantive validation tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
