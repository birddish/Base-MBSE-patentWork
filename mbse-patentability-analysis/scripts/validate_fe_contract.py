from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_TEXT = {
    "SKILL.md": [
        "F.Output",
        "STATE.OutputState",
        "不增加独立O层",
        "受影响对象",
    ],
    "references/mbse-framework.md": [
        "F = <SystemBoundary, Input, Transformation, Output, PreconditionOrTrigger>",
        "AffectedObject",
        "EffectType",
        "OutputState",
    ],
    "references/sysml-lite-mapping.md": [
        "F.Output",
        "受影响属性",
        "同义改写",
    ],
    "references/failure-patterns.md": [
        "同义反复闭环",
        "比较型E",
    ],
    "references/modes/mode-disclosure.md": [
        "F功能合同表",
        "E效果合同表",
        "OutputState",
    ],
    "assets/templates/disclosure-output-template.md": [
        "F功能合同表",
        "E效果合同表",
        "affected_attribute",
    ],
}

BANNED_PATTERNS = {
    r"效果：权限实时评估": "旧示例仍把功能输出当作E",
    r"效果：主动防御": "旧示例仍用能力名称替代E",
    r"效果：精准脱敏": "旧示例仍用功能名称替代E",
    r"按温度状态调节散热功率": "旧温控E示例仍重复功能输出",
    r"状态转换的结果（即技术效果）": "仍把OutputState直接等同于E",
    r"B\s*和\s*E\s*(?:通常|常)?为同一": "仍把B与E视为同一对象",
}


def main() -> int:
    failures: list[str] = []
    for relative, needles in REQUIRED_TEXT.items():
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"缺少文件：{relative}")
            continue
        content = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in content:
                failures.append(f"{relative} 缺少：{needle}")

    corpus = "\n".join(
        path.read_text(encoding="utf-8")
        for path in ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".mmd"}
    )
    for pattern, message in BANNED_PATTERNS.items():
        if re.search(pattern, corpus):
            failures.append(message)

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        print(f"{len(failures)} F/E contract check(s) failed.")
        return 1

    print("F/E object-contract and regression checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
