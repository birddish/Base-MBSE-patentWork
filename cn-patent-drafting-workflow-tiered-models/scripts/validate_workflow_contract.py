from __future__ import annotations

import re
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "references"


REQUIRED_TEXT = {
    "SKILL.md": [
        "references/protectable-unit-contract.md",
        "references/workflow-regression-cases.md",
        "references/model-routing-contract.md",
        "references/context-and-handoff-contract.md",
        "references/stage-model-io-contract.md",
        "references/cross-skill-adapters.md",
    ],
    "references/model-routing-contract.md": [
        "Luna：确定性执行层",
        "Terra：受证据约束的候选层",
        "Sol：实质判断与整合层",
        "assigned_model",
        "NB/IS",
        "代理师阶段确认",
    ],
    "references/context-and-handoff-contract.md": [
        "execution_mode=advisory",
        "task_context.json",
        "task_handoff.json",
        "input_snapshot_hash",
        "proposed_status=Q",
    ],
    "references/cross-skill-adapters.md": [
        "search_context.json",
        "search_handoff.json",
        "oa_context.json",
        "oa_handoff.json",
        "task_context.json",
        "task_handoff.json",
    ],
    "references/protectable-unit-contract.md": [
        "CHAIN =",
        "PU    =",
        "PST   =",
        "CTX   =",
        "STATE =",
        "fact_status",
        "drafting_status",
        "drafting_admission",
        "IU(PU,PST) = SearchProjection(PU | PST_boundary)",
        "F与E边界合同",
        "F.Output",
        "technical_closure=closed",
        "allowed/conditional/prohibited/Q",
        "prereview/formal",
    ],
    "references/stage-1-mbse-modeling.md": [
        "R_problem",
        "R_context",
        "PU候选表",
        "PST初步枚举表",
        "输出状态写入STATE",
        "功能闭合",
        "效果闭合",
        "strengthened-by",
    ],
    "references/stage-2-search-and-comparison.md": [
        "客户既有申请核查",
        "单一性风险",
        "PU准入矩阵",
        "不得直接把“区别特征”升级为独权必要技术特征",
        "旧IU失效",
        "search_context.json",
        "search_handoff.json",
    ],
    "references/stage-3-claim-drafting.md": [
        "PST客体完整性硬门",
        "CTX组合支持硬门",
        "权利要求依赖图硬门",
        "target_claim_count",
        "多项从权引用另一多项从权",
        "F.Output/STATE.OutputState",
        "预审草案",
        "R/F/S/B/E → CHAIN → PU → PST → IU及阶段2反馈",
    ],
    "references/stage-8-existing-application-audit.md": [
        "全部M/E/C领域",
        "暂停或排除PU是否误入申请文件",
        "全部提交候选权利要求",
    ],
    "references/stage-9-prosecution-handoff.md": [
        "prosecution_handoff.md",
        "oa_context.json",
        "oa_handoff.json",
        "recalculation_gate",
    ],
    "references/workflow-regression-cases.md": [
        "瓶盖",
        "食品料理机",
        "垃圾箱",
        "快拆卡箍",
        "多项从属权利要求引用另一项多项从属权利要求",
        "未设置`target_claim_count`",
        "F/E同义反复或因果缺失",
        "V1旧版母版权项总数",
        "F-4 跨CTX拼接",
        "F-5 旧IU沿用",
        "F-6 open越级准入",
    ],
}


BANNED_PATTERNS = {
    r"10项版|十项版|权利要求1至10": "存在固定项数遗留",
    r"一条独立闭合链\s*[→=-]+\s*一项独立权利要求": "仍把CHAIN直接等同独权",
    r"B\s*和\s*E\s*(?:常)?为同一": "仍把机械B与E视为同一对象",
    r"E通常进入说明书效果论证，仅在表现为必要、可支持的技术输出状态时转为限定": "仍把E与输出状态混同",
    r"所有技术内容必须标记以下五种状态之一": "仍混用事实来源与撰写采用状态",
    r"IU\s*=\s*SearchProjection\(PU\)(?!\s*\|)": "仍使用未绑定PST边界的旧IU定义",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")


def main() -> int:
    failures = 0
    for relative, needles in REQUIRED_TEXT.items():
        path = ROOT / relative
        if not path.is_file():
            fail(f"缺少文件 {relative}")
            failures += 1
            continue
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                fail(f"{relative} 缺少约束：{needle}")
                failures += 1

    corpus = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [ROOT / "SKILL.md", *sorted(REF.glob("*.md"))]
    )
    for pattern, message in BANNED_PATTERNS.items():
        if re.search(pattern, corpus):
            fail(message)
            failures += 1

    for prefix in ["search", "oa"]:
        context = json.loads((ROOT / f"assets/orchestration/{prefix}-context.template.json").read_text(encoding="utf-8"))
        handoff = json.loads((ROOT / f"assets/orchestration/{prefix}-handoff.template.json").read_text(encoding="utf-8"))
        reverse_pairs = {
            "upstream_snapshot_id": "target_active_snapshot_id",
            "target_active_snapshot_id": "upstream_snapshot_id",
            "source_stage": "target_stage",
            "target_stage": "source_stage",
        }
        if handoff.get("source_skill") != context.get("target_skill") or handoff.get("target_skill") != context.get("source_skill"):
            fail(f"{prefix} 回传模板的Skill方向未反转")
            failures += 1
        for handoff_field, context_field in reverse_pairs.items():
            if handoff.get(handoff_field) != context.get(context_field):
                fail(f"{prefix} 回传模板的 {handoff_field} 未按请求方向反转")
                failures += 1

    if failures:
        print(f"{failures} workflow contract check(s) failed.")
        return 1
    print("Workflow contract and regression-oracle checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
