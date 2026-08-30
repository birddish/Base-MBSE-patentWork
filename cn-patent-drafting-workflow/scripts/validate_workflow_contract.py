from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "references"


REQUIRED_TEXT = {
    "SKILL.md": [
        "references/protectable-unit-contract.md",
        "references/workflow-regression-cases.md",
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
        "workflow.exclusion_records",
        "chain_role",
        "text_location_maturity",
        "legal_evidence_maturity",
        "claim_consumption_status",
        "PST权项消费策略门",
        "PST枚举完备性与去重",
        "claim_branch_inventory",
        "从属权项分支消费门",
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
        "main_chain",
        "open_candidate",
        "strengthening_subchain",
        "exclusion_records",
        "作用拓扑同一性",
        "PST枚举不得把每个PU自动乘以产品、方法和装置",
    ],
    "references/stage-2-search-and-comparison.md": [
        "客户既有申请核查",
        "单一性风险",
        "PU准入矩阵",
        "不得直接把“区别特征”升级为独权必要技术特征",
        "旧IU失效",
        "text_location_maturity",
        "legal_evidence_maturity",
        "exclusion_records",
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
        "权项消费策略门",
        "claim_consumption_status=consumed_independent",
        "workflow.claim_branch_inventory",
        "每个已消费分支恰好形成一项从权",
    ],
    "references/stage-8-existing-application-audit.md": [
        "全部M/E/C领域",
        "暂停或排除PU是否误入申请文件",
        "全部提交候选权利要求",
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
        "F-7至F-15",
        "PU-X/PST-X",
        "reserved/strategy_review_required",
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

    if failures:
        print(f"{failures} workflow contract check(s) failed.")
        return 1
    print("Workflow contract and regression-oracle checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
