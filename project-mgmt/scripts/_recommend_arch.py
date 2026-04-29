#!/usr/bin/env python3
"""
确定性架构推荐 — 给 wizard 阶段 D 屏 3 用。

把"团队规模 × 项目并发"决策从 LLM 手里收回来,变成确定性脚本。
LLM 在 wizard 阶段 D 必须**调用本脚本**,不能凭感觉推荐。

实测发现 LLM 在面对同样输入(9 人 + 10+ 个项目)时给出不同推荐
(有时 B1 有时 B2),不符合 architecture-decision.md 矩阵。所以这一步
做成确定性脚本。

矩阵(同 architecture-decision.md):

  | 团队 \\ 项目 | 1-3 个 | 4-10 个 | 10+ 个 |
  |-------------|--------|---------|--------|
  | <5 人       | A     | B1      | B2     |
  | 5-15 人     | B1    | B1(主流)| B2     |
  | 15+ 人      | B1    | B2      | B2     |

用法:
  python3 _recommend_arch.py --team <size> --projects <count>

  team:    "<5" | "5-15" | "15+"
  projects: "1-3" | "4-10" | "10+"

输出 JSON 到 stdout:
  {
    "arch": "B1",
    "arch_name": "多任务表",
    "rationale": "...",
    "warnings": ["..."]
  }
"""

import argparse
import json
import sys

ARCH_NAMES = {
    "A": "轻量共享(1 个 Base · 1 张共享任务表)",
    "B1": "多任务表(1 个 Base · 每项目独立任务表 + dashboard)",
    "B2": "多空间分离(每项目独立 Base + Master Base 总览)",
}

# 矩阵 [team][projects] → arch
MATRIX = {
    "<5": {
        "1-3": "A",
        "4-10": "B1",
        "10+": "B2",
    },
    "5-15": {
        "1-3": "B1",
        "4-10": "B1",
        "10+": "B2",
    },
    "15+": {
        "1-3": "B1",
        "4-10": "B2",
        "10+": "B2",
    },
}

# 主流 / 强推荐组合(对应 architecture-decision.md 加粗格)
RECOMMENDED = {("<5", "1-3"), ("5-15", "4-10"), ("15+", "10+")}

WARNINGS = {
    ("<5", "10+"): "⚠️ 团队不到 5 人却要管 10+ 个项目,**B2 多空间会让你忙不过来**(每项目要切 Base)。请先确认这 10+ 是否分散在多业务方向 — 如果是,建议先建主方向那个空间(可能就 4-10 个项目,推 B1)。",
    ("15+", "1-3"): "⚠️ 15+ 人团队却只跑 1-3 个项目,B1 是给你的;但要确认成员是否真都在这 1-3 个项目上(更大概率有不同方向项目,建议各方向单独建空间)。",
}


def recommend(team: str, projects: str) -> dict:
    if team not in MATRIX:
        raise ValueError(f"team 必须是 <5 / 5-15 / 15+,不能是 '{team}'")
    if projects not in MATRIX[team]:
        raise ValueError(f"projects 必须是 1-3 / 4-10 / 10+,不能是 '{projects}'")

    arch = MATRIX[team][projects]
    is_main = (team, projects) in RECOMMENDED
    warning = WARNINGS.get((team, projects))

    rationale_lines = []
    rationale_lines.append(f"团队规模:{team} 人")
    rationale_lines.append(f"项目并发:{projects} 个")
    rationale_lines.append(f"矩阵交叉点 → 架构 {arch}")
    if is_main:
        rationale_lines.append(f"(这是 {team} 人团队 + {projects} 个项目的**主流推荐**)")
    rationale_lines.append("")
    rationale_lines.append(f"架构 {arch} = {ARCH_NAMES[arch]}")

    return {
        "arch": arch,
        "arch_name": ARCH_NAMES[arch],
        "rationale": "\n".join(rationale_lines),
        "warnings": [warning] if warning else [],
        "matrix_note": (
            "本结果由 _recommend_arch.py 按 architecture-decision.md 矩阵确定性推断,"
            "不是 LLM 凭感觉。LLM 必须直接展示本结果给用户,不能擅自更改架构推荐。"
        ),
    }


def main():
    ap = argparse.ArgumentParser(
        description="确定性架构推荐(基于 architecture-decision.md 矩阵)"
    )
    ap.add_argument("--team", required=True, choices=["<5", "5-15", "15+"],
                    help="团队规模档位")
    ap.add_argument("--projects", required=True, choices=["1-3", "4-10", "10+"],
                    help="本空间项目并发档位")
    args = ap.parse_args()

    try:
        result = recommend(args.team, args.projects)
    except ValueError as e:
        sys.stderr.write(f"❌ 参数错误: {e}\n")
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
