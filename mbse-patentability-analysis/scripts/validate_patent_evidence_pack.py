from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


FACT = {"D", "I", "Q", "X", "[D]", "[I]", "[Q]", "[X]"}
DRAFTING = {"[D]", "[N]", "[G]", "[Q]", "[X]"}
CLOSURE = {"closed", "open", "Q"}
SOURCE = {"mature", "partial", "Q"}
SEARCH = {"检索设计", "初筛线索", "全文定位", "比对完结", "Q"}
ADMISSION = {"admitted", "conditional", "paused", "excluded", "Q"}
COMBINATION = {"allowed", "conditional", "prohibited", "Q"}
CHAIN_ROLE = {"main_chain", "open_candidate", "strengthening_subchain"}
TEXT_LOCATION = {"线索", "说明书片段", "说明书全文", "权利要求全文", "附图定位", "Q"}
LEGAL_EVIDENCE = {"书目未核", "公开日未核", "基准日前资格已核", "单文献覆盖已核", "Q"}
CLAIM_CONSUMPTION = {"consumed_independent", "consumed_dependent", "reserved", "paused", "excluded", "Q"}
BRANCH_CONSUMPTION = {"consumed_dependent", "reserved", "paused", "excluded", "Q"}
STRATEGY_GATE = {"passed", "confirmed", "failed", "Q"}


def items(value: Any) -> list[dict[str, Any]]:
    return value if isinstance(value, list) else []


def ids(value: list[dict[str, Any]]) -> set[str]:
    return {str(x.get("id")) for x in value if x.get("id")}


def require_refs(errors: list[str], label: str, refs: Any, allowed: set[str]) -> None:
    if not isinstance(refs, list) or not refs:
        errors.append(f"{label} 缺少非空回指")
        return
    missing = [str(x) for x in refs if str(x) not in allowed]
    if missing:
        errors.append(f"{label} 存在断链ID：{', '.join(missing)}")


def validate_v1(data: dict[str, Any], errors: list[str]) -> None:
    for key in ("claims", "feature_groups", "documents", "evidence", "novelty_assessments", "inventive_step_assessments"):
        if key not in data or not isinstance(data[key], list):
            errors.append(f"1.0缺少数组字段：{key}")
    claim_ids, cf_ids = ids(items(data.get("claims"))), ids(items(data.get("feature_groups")))
    doc_ids, ev_ids = ids(items(data.get("documents"))), ids(items(data.get("evidence")))
    for claim in items(data.get("claims")):
        require_refs(errors, f"权利要求{claim.get('id')} feature_group_ids", claim.get("feature_group_ids"), cf_ids)
    for cf in items(data.get("feature_groups")):
        require_refs(errors, f"特征组{cf.get('id')} source_refs", cf.get("source_refs"), ev_ids)
    for ev in items(data.get("evidence")):
        if ev.get("document_id") not in doc_ids:
            errors.append(f"证据{ev.get('id')}的document_id断链")
        if ev.get("fact_status") not in FACT:
            errors.append(f"证据{ev.get('id')}使用非法fact_status")
    if len(claim_ids) != len(items(data.get("claims"))) or len(cf_ids) != len(items(data.get("feature_groups"))):
        errors.append("claims或feature_groups存在缺失/重复ID")


def validate_v11(data: dict[str, Any], errors: list[str], *, check_legacy_metrics: bool = True) -> None:
    validate_v1(data, errors)
    case = data.get("case", {})
    if case.get("draft_mode") not in {"prereview", "formal"}:
        errors.append("case.draft_mode非法")
    target = case.get("target_claim_count")
    if target is not None and (not isinstance(target, int) or target <= 0):
        errors.append("case.target_claim_count必须为正整数或null")

    model = data.get("model")
    workflow = data.get("workflow")
    if not isinstance(model, dict) or not isinstance(workflow, dict):
        errors.append("1.1缺少model或workflow对象")
        return
    kinds = ("R", "F", "S", "B", "E", "IF", "CV", "STATE")
    model_ids: dict[str, set[str]] = {}
    all_model_ids: set[str] = set()
    node_by_id: dict[str, dict[str, Any]] = {}
    for kind in kinds:
        nodes = items(model.get(kind))
        model_ids[kind] = ids(nodes)
        all_model_ids |= model_ids[kind]
        for node in nodes:
            nid = str(node.get("id", ""))
            if not nid:
                errors.append(f"model.{kind}存在无ID节点")
                continue
            node_by_id[nid] = node
    for kind in kinds:
        for node in items(model.get(kind)):
            nid = str(node.get("id", ""))
            if not nid:
                continue
            if node.get("fact_status") not in {"[D]", "[I]", "[Q]", "[X]"}:
                errors.append(f"节点{nid}使用非法fact_status")
            ds = node.get("drafting_status")
            if ds not in DRAFTING:
                errors.append(f"节点{nid}使用非法drafting_status")
            if ds == "[N]":
                c = node.get("technical_confirmation")
                if not isinstance(c, dict) or not all(c.get(x) for x in ("subject", "date", "content", "basis")) or not c.get("ctx_ids"):
                    errors.append(f"[N]节点{nid}缺少完整技术确认记录")
            if ds == "[G]":
                refs = node.get("generalizes_from_ids")
                if not isinstance(refs, list) or not refs:
                    errors.append(f"[G]节点{nid}缺少[D]/[N]概括来源")
                else:
                    for ref in refs:
                        source = node_by_id.get(str(ref))
                        if source is None or source.get("drafting_status") not in {"[D]", "[N]"}:
                            errors.append(f"[G]节点{nid}的概括来源{ref}无效")

    for node in items(model.get("F")):
        nid = str(node.get("id"))
        if not all(node.get(x) for x in ("system_boundary", "input", "transformation", "output", "trigger")):
            errors.append(f"F节点{nid}缺少边界、输入、变换、输出或触发字段")
    causal_ids = model_ids["S"] | model_ids["B"] | model_ids["IF"] | model_ids["CV"] | model_ids["STATE"]
    for node in items(model.get("E")):
        nid = str(node.get("id"))
        if not all(node.get(x) for x in ("affected_object", "affected_attribute", "result", "conditions")):
            errors.append(f"E节点{nid}缺少对象、属性、结果或条件字段")
        require_refs(errors, f"E节点{nid}.causal_source_ids", node.get("causal_source_ids"), causal_ids)

    chains = items(workflow.get("chains"))
    pus = items(workflow.get("protectable_units"))
    psts = items(workflow.get("protection_subjects"))
    ctxs = items(workflow.get("contexts"))
    ius = items(workflow.get("innovation_units"))
    combos = items(workflow.get("combination_support"))
    admissions = items(workflow.get("admission_records"))
    mappings = items(workflow.get("claim_mappings"))
    chain_ids, pu_ids, pst_ids, ctx_ids, iu_ids = map(ids, (chains, pus, psts, ctxs, ius))
    claim_ids = ids(items(data.get("claims")))
    cf_ids = ids(items(data.get("feature_groups")))
    ev_ids = ids(items(data.get("evidence")))
    relation_ids = {str(r) for cf in items(data.get("feature_groups")) for r in cf.get("relation_ids", [])}
    chain_by_id = {str(x.get("id")): x for x in chains}
    pu_by_id = {str(x.get("id")): x for x in pus}
    pst_by_id = {str(x.get("id")): x for x in psts}

    for ctx in ctxs:
        if ctx.get("status") not in {"[D]", "[I]", "[Q]", "[X]"}:
            errors.append(f"CTX {ctx.get('id')}状态非法")
    for chain in chains:
        cid = str(chain.get("id"))
        for field, kind in (("r_ids", "R"), ("f_ids", "F"), ("s_ids", "S"), ("b_ids", "B"), ("e_ids", "E")):
            require_refs(errors, f"{cid}.{field}", chain.get(field), model_ids[kind])
        require_refs(errors, f"{cid}.ctx_ids", chain.get("ctx_ids"), ctx_ids)
        require_refs(errors, f"{cid}.state_ids", chain.get("state_ids"), model_ids["STATE"])
        if chain.get("technical_closure") not in CLOSURE:
            errors.append(f"{cid}使用非法technical_closure")
        if chain.get("relationship_type") == "strengthened-by" and chain.get("strengthens_pu_id") not in pu_ids:
            errors.append(f"{cid}的strengthens_pu_id无效")
        f_nodes = [node_by_id.get(str(x), {}) for x in chain.get("f_ids", [])]
        e_nodes = [node_by_id.get(str(x), {}) for x in chain.get("e_ids", [])]
        normalize = lambda value: "".join(str(value).split()).lower()
        for f_node in f_nodes:
            for e_node in e_nodes:
                if normalize(f_node.get("text")) == normalize(e_node.get("text")) or normalize(f_node.get("output")) == normalize(e_node.get("result")):
                    errors.append(f"{cid}存在F/E或F.Output/E同义反复")

    for pu in pus:
        pid = str(pu.get("id"))
        require_refs(errors, f"{pid}.chain_ids", pu.get("chain_ids"), chain_ids)
        if pu.get("source_maturity") not in SOURCE or pu.get("search_maturity") not in SEARCH or pu.get("drafting_admission") not in ADMISSION:
            errors.append(f"{pid}使用非法成熟度或准入状态")
        source_chains = [chain_by_id.get(str(x), {}) for x in pu.get("chain_ids", [])]
        if any(x.get("relationship_type") == "strengthened-by" for x in source_chains):
            errors.append(f"{pid}错误地由strengthened-by子链形成")
        if any(x.get("technical_closure") == "open" for x in source_chains):
            if pu.get("drafting_admission") == "admitted":
                errors.append(f"open对象{pid}进入admitted")
            if pu.get("drafting_admission") == "conditional" and not pu.get("conditions"):
                errors.append(f"open对象{pid}的conditional缺少补正条件")

    for pst in psts:
        sid = str(pst.get("id"))
        if pst.get("pu_id") not in pu_ids:
            errors.append(f"{sid}的pu_id断链")
        if pst.get("object_integrity") not in {"passed", "failed", "Q"} or not pst.get("integrity_reason"):
            errors.append(f"{sid}缺少客体完整性结论或理由")

    for iu in ius:
        iid = str(iu.get("id"))
        if iu.get("pu_id") not in pu_ids or iu.get("pst_id") not in pst_ids:
            errors.append(f"{iid}缺少PU/PST回指")
            continue
        require_refs(errors, f"{iid}.chain_ids", iu.get("chain_ids"), chain_ids)
        pst = pst_by_id[str(iu.get("pst_id"))]
        if iu.get("valid") is True and iu.get("pst_boundary_signature") != pst.get("boundary_signature"):
            errors.append(f"{iid}沿用与当前PST不一致的旧边界")
        if iu.get("search_maturity") not in SEARCH:
            errors.append(f"{iid}使用非法search_maturity")

    forbidden_claims: set[str] = set()
    for combo in combos:
        conclusion = combo.get("conclusion")
        if conclusion not in COMBINATION:
            errors.append(f"组合{combo.get('id')}使用非法结论")
        linked = {str(x) for x in combo.get("claim_ids", [])}
        if conclusion in {"prohibited", "Q"} or (conclusion == "conditional" and not combo.get("satisfied")):
            forbidden_claims |= linked

    stage2_by_pair = {(str(x.get("pu_id")), str(x.get("pst_id"))): x for x in admissions}
    for ar in admissions:
        if ar.get("pu_id") not in pu_ids or ar.get("pst_id") not in pst_ids:
            errors.append(f"准入记录{ar.get('id')}的PU/PST断链")
        if ar.get("technical_closure") not in CLOSURE or ar.get("source_maturity") not in SOURCE or ar.get("search_maturity") not in SEARCH or ar.get("drafting_admission") not in ADMISSION:
            errors.append(f"准入记录{ar.get('id')}状态非法")

    for mapping in mappings:
        mid = str(mapping.get("claim_id"))
        if mid not in claim_ids:
            errors.append(f"映射{mid}的claim_id断链")
            continue
        require_refs(errors, f"映射{mid}.chain_ids", mapping.get("chain_ids"), chain_ids)
        if mapping.get("pu_id") not in pu_ids or mapping.get("pst_id") not in pst_ids:
            errors.append(f"映射{mid}缺少PU/PST回指")
        require_refs(errors, f"映射{mid}.ctx_ids", mapping.get("ctx_ids"), ctx_ids)
        require_refs(errors, f"映射{mid}.feature_group_ids", mapping.get("feature_group_ids"), cf_ids)
        require_refs(errors, f"映射{mid}.relation_ids", mapping.get("relation_ids"), relation_ids)
        require_refs(errors, f"映射{mid}.evidence_ids", mapping.get("evidence_ids"), ev_ids)
        if mapping.get("master_included") and mid in forbidden_claims:
            errors.append(f"prohibited/Q/未满足conditional组合进入权利要求{mid}")
        if mapping.get("claim_type") == "independent":
            if any(chain_by_id.get(str(x), {}).get("relationship_type") == "strengthened-by" for x in mapping.get("chain_ids", [])):
                errors.append(f"strengthened-by子链进入独权{mid}")
        if mapping.get("master_included"):
            pu = pu_by_id.get(str(mapping.get("pu_id")), {})
            ar = stage2_by_pair.get((str(mapping.get("pu_id")), str(mapping.get("pst_id"))), {})
            if case.get("draft_mode") == "formal":
                if pu.get("drafting_admission") not in {"admitted", "conditional"} or (pu.get("drafting_admission") == "conditional" and not ar.get("conditions_satisfied")):
                    errors.append(f"正式母版权利要求{mid}消费未准入PU")
                if not ar.get("stage2_complete"):
                    errors.append(f"正式母版权利要求{mid}阶段2未完成")

    graph = workflow.get("dependency_graph", {})
    graph_nodes = items(graph.get("nodes"))
    node_meta = {str(x.get("claim_id")): x for x in graph_nodes}
    for node in graph_nodes:
        claim_id = str(node.get("claim_id"))
        if claim_id not in claim_ids:
            errors.append(f"依赖图节点{claim_id}的claim_id断链")
        if node.get("claim_type") not in {"independent", "dependent"}:
            errors.append(f"依赖图节点{claim_id}的claim_type非法")
    for edge in items(graph.get("edges")):
        child, parent = str(edge.get("from_claim_id")), str(edge.get("to_claim_id"))
        if child not in node_meta or parent not in node_meta:
            errors.append(f"依赖边{child}->{parent}断链")
        elif node_meta.get(child, {}).get("multiple_dependent") and node_meta.get(parent, {}).get("multiple_dependent"):
            errors.append(f"多项从权{child}违法引用另一多项从权{parent}")

    compression = workflow.get("compression", {})
    if target is None and (compression.get("performed") is True or compression.get("before_count") != compression.get("after_count")):
        errors.append("未设置target_claim_count却发生数字压缩")

    if check_legacy_metrics:
        metrics = workflow.get("metrics", {})
        expected_metrics = {
            "v2_master_claim_count": len(items(data.get("claims"))),
            "v2_independent_claim_count": sum(1 for x in graph_nodes if x.get("claim_type") == "independent"),
            "closed_chain_count": sum(1 for x in chains if x.get("technical_closure") == "closed"),
            "open_chain_count": sum(1 for x in chains if x.get("technical_closure") == "open"),
            "pu_candidate_count": len(pus),
        }
        if not isinstance(metrics.get("v1_master_claim_count"), int) or metrics.get("v1_master_claim_count", -1) < 0:
            errors.append("workflow.metrics.v1_master_claim_count必须为非负整数")
        for key, expected in expected_metrics.items():
            if metrics.get(key) != expected:
                errors.append(f"workflow.metrics.{key}应为{expected}，实际为{metrics.get(key)}")

    independent_claims = {str(x.get("claim_id")) for x in graph_nodes if x.get("claim_type") == "independent"}
    mapped_independent = {str(x.get("claim_id")) for x in mappings if x.get("claim_type") == "independent" and x.get("master_included")}
    missing_independent = sorted(independent_claims - mapped_independent)
    if missing_independent:
        errors.append(f"独权缺少完整反向映射：{', '.join(missing_independent)}")


def validate_v12(data: dict[str, Any], errors: list[str]) -> None:
    validate_v11(data, errors, check_legacy_metrics=False)
    workflow = data.get("workflow")
    if not isinstance(workflow, dict):
        return

    chains = items(workflow.get("chains"))
    pus = items(workflow.get("protectable_units"))
    psts = items(workflow.get("protection_subjects"))
    ius = items(workflow.get("innovation_units"))
    exclusions = items(workflow.get("exclusion_records"))
    branches = items(workflow.get("claim_branch_inventory"))
    combos = items(workflow.get("combination_support"))
    admissions = items(workflow.get("admission_records"))
    mappings = items(workflow.get("claim_mappings"))
    graph_nodes = items(workflow.get("dependency_graph", {}).get("nodes"))
    claim_ids = ids(items(data.get("claims")))
    pu_ids, pst_ids = ids(pus), ids(psts)
    pu_by_id = {str(x.get("id")): x for x in pus}
    pst_by_id = {str(x.get("id")): x for x in psts}
    chain_by_id = {str(x.get("id")): x for x in chains}
    model_ids = {
        str(node.get("id"))
        for kind in ("R", "F", "S", "B", "E", "IF", "CV", "STATE")
        for node in items(data.get("model", {}).get(kind))
        if node.get("id")
    }
    ev_ids = ids(items(data.get("evidence")))
    cf_ids = ids(items(data.get("feature_groups")))
    relation_ids = {
        str(relation_id)
        for feature_group in items(data.get("feature_groups"))
        for relation_id in feature_group.get("relation_ids", [])
    }

    for chain in chains:
        cid = str(chain.get("id"))
        role = chain.get("chain_role")
        if role not in CHAIN_ROLE:
            errors.append(f"{cid}使用非法或缺失chain_role")
            continue
        if role == "main_chain" and chain.get("technical_closure") != "closed":
            errors.append(f"{cid}标为main_chain但未闭合")
        if role == "open_candidate" and chain.get("technical_closure") == "closed":
            errors.append(f"{cid}标为open_candidate却已闭合")
        if role == "strengthening_subchain" and chain.get("relationship_type") != "strengthened-by":
            errors.append(f"{cid}标为strengthening_subchain但关系不是strengthened-by")

    invalid_pu_ids: set[str] = set()
    for pu in pus:
        pid = str(pu.get("id"))
        if pu.get("text_location_maturity") not in TEXT_LOCATION:
            errors.append(f"{pid}使用非法或缺失text_location_maturity")
        if pu.get("legal_evidence_maturity") not in LEGAL_EVIDENCE:
            errors.append(f"{pid}使用非法或缺失legal_evidence_maturity")
        if pu.get("technicality") == "failed" or pu.get("drafting_admission") == "excluded":
            invalid_pu_ids.add(pid)
            errors.append(f"{pid}为排除或技术性失败对象，不得成为PU")
        for chain_id in pu.get("chain_ids", []):
            role = chain_by_id.get(str(chain_id), {}).get("chain_role")
            if role == "strengthening_subchain":
                errors.append(f"{pid}错误地由strengthening_subchain形成")
            if role == "open_candidate" and pu.get("drafting_admission") == "admitted":
                errors.append(f"{pid}由open_candidate越级进入admitted")

    exclusion_source_ids: set[str] = set()
    exclusion_object_ids: set[str] = set()
    exclusion_ids: set[str] = set()
    for exclusion in exclusions:
        xid = str(exclusion.get("id", ""))
        if not xid:
            errors.append("exclusion_records存在无ID记录")
            continue
        if xid in exclusion_ids:
            errors.append(f"排除记录{xid}重复")
        exclusion_ids.add(xid)
        if exclusion.get("fact_status") != "[X]" or exclusion.get("drafting_status") != "[X]":
            errors.append(f"排除记录{xid}的事实轴和撰写轴必须均为[X]")
        require_refs(errors, f"排除记录{xid}.source_node_ids", exclusion.get("source_node_ids"), model_ids)
        require_refs(errors, f"排除记录{xid}.evidence_ids", exclusion.get("evidence_ids"), ev_ids)
        if not str(exclusion.get("reason", "")).strip():
            errors.append(f"排除记录{xid}缺少排除理由")
        exclusion_source_ids |= {str(x) for x in exclusion.get("source_node_ids", [])}
        exclusion_object_ids |= {
            str(x)
            for field in ("object_ids", "related_object_ids", "excluded_object_ids")
            for x in exclusion.get(field, [])
        }
    direct_overlap = exclusion_ids & (pu_ids | pst_ids)
    referenced_overlap = exclusion_object_ids & (pu_ids | pst_ids)
    if direct_overlap or referenced_overlap:
        conflicts = sorted(direct_overlap | referenced_overlap)
        errors.append(f"排除台账与保护对象集合冲突：{', '.join(conflicts)}")
    for obj in pus + psts:
        if exclusion_source_ids & {str(x) for x in obj.get("source_node_ids", [])}:
            errors.append(f"排除内容同时进入保护对象{obj.get('id')}")

    iu_by_pst: dict[str, list[dict[str, Any]]] = {}
    for iu in ius:
        iid = str(iu.get("id"))
        if iu.get("text_location_maturity") not in TEXT_LOCATION:
            errors.append(f"{iid}使用非法或缺失text_location_maturity")
        if iu.get("legal_evidence_maturity") not in LEGAL_EVIDENCE:
            errors.append(f"{iid}使用非法或缺失legal_evidence_maturity")
        iu_by_pst.setdefault(str(iu.get("pst_id")), []).append(iu)

    mappings_by_pst: dict[str, list[dict[str, Any]]] = {}
    for mapping in mappings:
        mappings_by_pst.setdefault(str(mapping.get("pst_id")), []).append(mapping)

    strategy_fields = (
        "independent_value",
        "implementation_actor",
        "source_support",
        "search_boundary",
        "filing_layout",
    )
    pst_semantic_keys: set[tuple[str, str]] = set()
    for pst in psts:
        sid = str(pst.get("id"))
        if not str(pst.get("semantic_key", "")).strip():
            errors.append(f"{sid}缺少稳定semantic_key")
        pst_key = (str(pst.get("pu_id")), str(pst.get("semantic_key", "")).strip())
        if pst_key[1] and pst_key in pst_semantic_keys:
            errors.append(f"{sid}与同PU另一PST使用重复semantic_key")
        pst_semantic_keys.add(pst_key)
        if not str(pst.get("enumeration_basis", "")).strip():
            errors.append(f"{sid}缺少PST枚举来源")
        if not str(pst.get("boundary_difference", "")).strip():
            errors.append(f"{sid}缺少与其他PST的边界差异")
        if not isinstance(pst.get("textual_mirror"), bool):
            errors.append(f"{sid}缺少textual_mirror布尔结论")
        if pst.get("pu_id") in invalid_pu_ids:
            errors.append(f"{sid}回指排除或技术性失败PU")
        consumption = pst.get("claim_consumption_status")
        if consumption not in CLAIM_CONSUMPTION:
            errors.append(f"{sid}使用非法或缺失claim_consumption_status")
        if not str(pst.get("consumption_reason", "")).strip():
            errors.append(f"{sid}缺少consumption_reason")
        gate = pst.get("strategy_gate")
        if not isinstance(gate, dict):
            errors.append(f"{sid}缺少strategy_gate")
            gate = {}
        for field in strategy_fields:
            if gate.get(field) not in {"passed", "failed", "Q"}:
                errors.append(f"{sid}.strategy_gate.{field}非法或缺失")
        if gate.get("status") not in STRATEGY_GATE:
            errors.append(f"{sid}.strategy_gate.status非法或缺失")
        if gate.get("status") == "confirmed":
            confirmation = gate.get("confirmation")
            if not isinstance(confirmation, dict) or not confirmation.get("subject") or not confirmation.get("date"):
                errors.append(f"{sid}策略门confirmed但缺少确认主体或日期")
        if pst.get("object_integrity") == "failed":
            if any(iu.get("valid") is True for iu in iu_by_pst.get(sid, [])):
                errors.append(f"客体完整性失败PST {sid}不得关联有效IU")
            if any(m.get("master_included") for m in mappings_by_pst.get(sid, [])):
                errors.append(f"客体完整性失败PST {sid}不得进入权利要求")
        if consumption == "consumed_independent":
            if pst.get("object_integrity") != "passed":
                errors.append(f"{sid}客体完整性未通过却消费为独权")
            if gate.get("status") not in {"passed", "confirmed"}:
                errors.append(f"{sid}策略门未通过却消费为独权")
            if pst.get("type") == "方法":
                if pst.get("textual_mirror") is True:
                    errors.append(f"方法PST {sid}只是产品文字镜像却消费为独权")
                if not str(pst.get("implementation_actor", "")).strip():
                    errors.append(f"方法PST {sid}缺少明确实施主体")
                if not isinstance(pst.get("step_support_refs"), list) or not pst.get("step_support_refs"):
                    errors.append(f"方法PST {sid}缺少步骤支持")
                if gate.get("implementation_actor") != "passed" or gate.get("source_support") != "passed":
                    errors.append(f"方法PST {sid}的实施主体或步骤支持策略门未通过")

    for admission in admissions:
        aid = str(admission.get("id"))
        if admission.get("text_location_maturity") not in TEXT_LOCATION:
            errors.append(f"准入记录{aid}使用非法或缺失text_location_maturity")
        if admission.get("legal_evidence_maturity") not in LEGAL_EVIDENCE:
            errors.append(f"准入记录{aid}使用非法或缺失legal_evidence_maturity")

    included_claims = {
        str(mapping.get("claim_id"))
        for mapping in mappings
        if mapping.get("master_included")
    }
    for combo in combos:
        combo_id = str(combo.get("id"))
        consumption = combo.get("claim_consumption_status")
        if consumption not in CLAIM_CONSUMPTION:
            errors.append(f"组合{combo_id}使用非法或缺失claim_consumption_status")
        if not str(combo.get("consumption_reason", "")).strip():
            errors.append(f"组合{combo_id}缺少consumption_reason")
        for field in ("source_support_status", "boundary_compatibility", "unity_status"):
            if combo.get(field) not in {"passed", "failed", "Q"}:
                errors.append(f"组合{combo_id}.{field}非法或缺失")
        linked_included = {str(x) for x in combo.get("claim_ids", [])} & included_claims
        if linked_included and consumption not in {"consumed_independent", "consumed_dependent"}:
            errors.append(f"组合{combo_id}进入权利要求但没有已消费状态")
        if linked_included and not str(combo.get("consumption_reason", "")).strip():
            errors.append(f"组合{combo_id}进入权利要求但缺少消费理由")
        if consumption in {"consumed_independent", "consumed_dependent"} and not linked_included:
            errors.append(f"组合{combo_id}标为已消费但未关联进入母版的权利要求")
        if combo.get("conclusion") == "conditional" and consumption in {"consumed_independent", "consumed_dependent"}:
            confirmation = combo.get("condition_confirmation")
            if combo.get("satisfied") is not True or not isinstance(confirmation, dict) or not confirmation.get("subject") or not confirmation.get("date"):
                errors.append(f"条件组合{combo_id}未满足并确认却进入权利要求")

    for mapping in mappings:
        if mapping.get("claim_type") != "independent" or not mapping.get("master_included"):
            continue
        claim_id = str(mapping.get("claim_id"))
        pst = pst_by_id.get(str(mapping.get("pst_id")), {})
        if pst.get("object_integrity") != "passed":
            errors.append(f"独权{claim_id}对应PST客体完整性未通过")
        if pst.get("claim_consumption_status") != "consumed_independent":
            errors.append(f"独权{claim_id}对应PST未标记consumed_independent")
        if pst.get("strategy_gate", {}).get("status") not in {"passed", "confirmed"}:
            errors.append(f"独权{claim_id}对应PST策略门未通过")
        roles = {chain_by_id.get(str(x), {}).get("chain_role") for x in mapping.get("chain_ids", [])}
        if "open_candidate" in roles or "strengthening_subchain" in roles:
            errors.append(f"open或强化子链越级进入独权{claim_id}")

    mapping_by_claim = {
        str(mapping.get("claim_id")): mapping
        for mapping in mappings
        if mapping.get("master_included")
    }
    dependent_claim_ids = {
        claim_id
        for claim_id, mapping in mapping_by_claim.items()
        if mapping.get("claim_type") == "dependent"
    }
    consumed_branch_claim_ids: list[str] = []
    consumed_semantic_keys: set[tuple[str, str]] = set()
    branch_ids: set[str] = set()
    for branch in branches:
        branch_id = str(branch.get("id", ""))
        if not branch_id:
            errors.append("claim_branch_inventory存在无ID记录")
            continue
        if branch_id in branch_ids:
            errors.append(f"从属分支{branch_id}重复")
        branch_ids.add(branch_id)
        semantic = str(branch.get("semantic_key", "")).strip()
        if not semantic:
            errors.append(f"从属分支{branch_id}缺少semantic_key")
        pu_id = str(branch.get("pu_id"))
        pst_id = str(branch.get("pst_id"))
        if pu_id not in pu_ids or pst_id not in pst_ids:
            errors.append(f"从属分支{branch_id}的PU/PST断链")
        elif str(pst_by_id.get(pst_id, {}).get("pu_id")) != pu_id:
            errors.append(f"从属分支{branch_id}的PU与PST不匹配")
        require_refs(
            errors,
            f"从属分支{branch_id}.feature_group_ids",
            branch.get("feature_group_ids"),
            cf_ids,
        )
        require_refs(
            errors,
            f"从属分支{branch_id}.relation_ids",
            branch.get("relation_ids"),
            relation_ids,
        )
        require_refs(
            errors,
            f"从属分支{branch_id}.source_refs",
            branch.get("source_refs"),
            ev_ids,
        )
        for field in (
            "fallback_value",
            "non_redundancy",
            "source_support",
            "pst_compatibility",
        ):
            if branch.get(field) not in {"passed", "failed", "Q"}:
                errors.append(f"从属分支{branch_id}.{field}非法或缺失")
        consumption = branch.get("claim_consumption_status")
        if consumption not in BRANCH_CONSUMPTION:
            errors.append(f"从属分支{branch_id}消费状态非法或缺失")
        if not str(branch.get("consumption_reason", "")).strip():
            errors.append(f"从属分支{branch_id}缺少消费理由")
        claim_id = str(branch.get("claim_id") or "")
        if consumption == "consumed_dependent":
            if any(
                branch.get(field) != "passed"
                for field in (
                    "fallback_value",
                    "non_redundancy",
                    "source_support",
                    "pst_compatibility",
                )
            ):
                errors.append(f"从属分支{branch_id}硬门未全通过却被消费")
            mapping = mapping_by_claim.get(claim_id)
            if not claim_id or mapping is None or mapping.get("claim_type") != "dependent":
                errors.append(f"从属分支{branch_id}未回指唯一从权")
            else:
                if str(mapping.get("pu_id")) != pu_id or str(mapping.get("pst_id")) != pst_id:
                    errors.append(f"从属分支{branch_id}与从权PU/PST不一致")
                consumed_branch_claim_ids.append(claim_id)
            semantic_key = (pst_id, semantic)
            if semantic and semantic_key in consumed_semantic_keys:
                errors.append(f"同一PST下重复消费从属分支semantic_key={semantic}")
            consumed_semantic_keys.add(semantic_key)
        elif claim_id:
            errors.append(f"未消费从属分支{branch_id}不应关联claim_id")

    duplicate_branch_claims = {
        claim_id
        for claim_id in consumed_branch_claim_ids
        if consumed_branch_claim_ids.count(claim_id) > 1
    }
    if duplicate_branch_claims:
        errors.append(
            "一项从权被多条分支重复消费：" + ", ".join(sorted(duplicate_branch_claims))
        )
    missing_branch_claims = dependent_claim_ids - set(consumed_branch_claim_ids)
    if missing_branch_claims:
        errors.append(
            "从权缺少claim_branch_inventory消费记录："
            + ", ".join(sorted(missing_branch_claims))
        )
    orphan_branch_claims = set(consumed_branch_claim_ids) - dependent_claim_ids
    if orphan_branch_claims:
        errors.append(
            "已消费分支未对应进入母版的从权："
            + ", ".join(sorted(orphan_branch_claims))
        )

    claim_to_pst = {
        str(mapping.get("claim_id")): str(mapping.get("pst_id"))
        for mapping in mappings
        if mapping.get("master_included")
    }
    qualified_legal = {"基准日前资格已核", "单文献覆盖已核"}
    for assessment in items(data.get("novelty_assessments")) + items(data.get("inventive_step_assessments")):
        if assessment.get("status") not in {"reviewed", "agreed"} or assessment.get("risk") in {None, "undetermined"}:
            continue
        direct = assessment.get("legal_evidence_maturity")
        pst_id = claim_to_pst.get(str(assessment.get("claim_id")))
        maturities = {
            iu.get("legal_evidence_maturity")
            for iu in iu_by_pst.get(str(pst_id), [])
        }
        if direct in {"Q", "书目未核", "公开日未核"} or (direct is None and maturities and not (maturities & qualified_legal)):
            errors.append(f"判断卡{assessment.get('id')}在法律证据成熟度不足时建立已核验结论")

    assertions = workflow.get("delivery_assertions", {})
    if isinstance(assertions, dict):
        absent_ids = {str(x) for x in assertions.get("absent_protectable_object_ids", [])}
        conflict = absent_ids & (pu_ids | pst_ids)
        if conflict:
            errors.append(f"交付声明与证据包对象集合冲突：{', '.join(sorted(conflict))}")

    metrics = workflow.get("metrics", {})
    expected_metrics = {
        "v2_master_claim_count": len(items(data.get("claims"))),
        "v2_independent_claim_count": sum(1 for x in graph_nodes if x.get("claim_type") == "independent"),
        "closed_main_chain_count": sum(
            1 for x in chains
            if x.get("chain_role") == "main_chain" and x.get("technical_closure") == "closed"
        ),
        "open_candidate_count": sum(1 for x in chains if x.get("chain_role") == "open_candidate"),
        "strengthening_subchain_count": sum(1 for x in chains if x.get("chain_role") == "strengthening_subchain"),
        "excluded_record_count": len(exclusions),
        "pu_candidate_count": len(pus),
    }
    if not isinstance(metrics.get("v1_master_claim_count"), int) or metrics.get("v1_master_claim_count", -1) < 0:
        errors.append("workflow.metrics.v1_master_claim_count必须为非负整数")
    for key, expected in expected_metrics.items():
        if metrics.get(key) != expected:
            errors.append(f"workflow.metrics.{key}应为{expected}，实际为{metrics.get(key)}")


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"JSON无法读取：{exc}"]
    version = str(data.get("schema_version", ""))
    if version == "1.0":
        validate_v1(data, errors)
    elif version == "1.1":
        validate_v11(data, errors)
    elif version == "1.2":
        validate_v12(data, errors)
    else:
        errors.append(f"不支持schema_version={version}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="校验专利证据包1.0/1.1/1.2；不修改输入文件")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    failures = 0
    for path in args.paths:
        errors = validate(path)
        if errors:
            failures += 1
            print(f"FAIL {path}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {path}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
