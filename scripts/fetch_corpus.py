#!/usr/bin/env python3
"""把开源历年真题 Markdown 语料按需抓取到考生私有目录。

设计约束：
- 只写 --data-dir 指定目录（默认仓库根 .study），绝不触碰受 Git 跟踪的文件；
- 外部语料为混合许可（第三方真题/教材内容不可再分发），因此只做"运行时引用"，
  不并入本仓库、不随仓库分发；
- 需要 GitHub 网络访问；失败时给出可人工执行的替代命令。

用法：
    python3 scripts/fetch_corpus.py --data-dir .study            # 首次抓取
    python3 scripts/fetch_corpus.py --data-dir .study --update   # 更新已有副本
    python3 scripts/fetch_corpus.py --data-dir .study --status   # 只查状态
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_URL = "https://github.com/hongge-ai/ruankao-senior-architecture-designer.git"
CORPUS_DIRNAME = "corpus"

# 抓取后向考生展示的语料地图（相对 corpus/ 的路径 -> 说明）
CORPUS_MAP = [
    ("content/INDEX.md", "语料总索引（先读这个）"),
    ("content/00-系统架构设计师考试大纲-清洗版/INDEX.md", "考试大纲"),
    ("content/01-系统架构设计师教材-清洗版/INDEX.md", "教材 20 章（按章 INDEX 按需加载）"),
    ("content/02-历年真题-清洗版/INDEX.md", "历年真题 36 份（综合/案例/论文）"),
    ("content/02-历年真题总索引.md", "历年真题总索引（选定首选文件再读）"),
    ("content/03-核心考点精要/INDEX.md", "核心考点精要"),
]


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None,
                          capture_output=True, text=True, timeout=600)


def git_available() -> bool:
    return shutil.which("git") is not None


def fetch(data_dir: Path, update: bool) -> int:
    corpus_dir = data_dir / CORPUS_DIRNAME

    if corpus_dir.exists() and not update:
        print(f"[SKIP] 语料已存在：{corpus_dir}")
        print("       更新请加 --update；查看内容请加 --status")
        return 0

    if not git_available():
        print("[FAIL] 未找到 git。请先安装 git，或手动执行：")
        print(f"       git clone --depth 1 {REPO_URL} \"{corpus_dir}\"")
        return 1

    data_dir.mkdir(parents=True, exist_ok=True)

    if update and corpus_dir.exists():
        print(f"[..] 更新语料：{corpus_dir}")
        result = run(["git", "pull", "--ff-only"], cwd=corpus_dir)
    else:
        if corpus_dir.exists():
            print(f"[..] 目录已存在但非完整克隆，重新抓取：{corpus_dir}")
            shutil.rmtree(corpus_dir, ignore_errors=True)
        print(f"[..] 浅克隆语料到：{corpus_dir}")
        result = run(["git", "clone", "--depth", "1", REPO_URL, str(corpus_dir)])

    if result.returncode != 0:
        print("[FAIL] 抓取失败（可能是网络无法访问 github.com）。")
        print("       可稍后重试，或手动执行：")
        print(f"       git clone --depth 1 {REPO_URL} \"{corpus_dir}\"")
        if result.stderr.strip():
            print("       错误摘要：" + result.stderr.strip().splitlines()[-1])
        return 1

    print("[OK] 语料就绪。之后可以直接问 agent：")
    print("     「这个考点哪年考过」「2016 年案例分析考了什么」")
    print()
    print("语料地图（先读 INDEX，再按需打开单份试卷，不要一次性全载入）：")
    for rel, desc in CORPUS_MAP:
        marker = "✓" if (corpus_dir / rel).exists() else "·"
        print(f"  {marker} {rel}  — {desc}")
    print()
    print("注意：该语料为混合许可，第三方真题与教材内容仅限个人学习，请勿再分发。")
    return 0


def status(data_dir: Path) -> int:
    corpus_dir = data_dir / CORPUS_DIRNAME
    if not corpus_dir.exists():
        print(f"[--] 尚未抓取语料。运行：python3 scripts/fetch_corpus.py --data-dir {data_dir}")
        return 0
    result = run(["git", "log", "-1", "--format=%h %cd %s", "--date=short"], cwd=corpus_dir)
    stamp = result.stdout.strip() if result.returncode == 0 else "（非 git 目录）"
    print(f"[OK] 语料位置：{corpus_dir}")
    print(f"     版本：{stamp}")
    missing = [rel for rel, _ in CORPUS_MAP if not (corpus_dir / rel).exists()]
    if missing:
        print("     缺失入口：" + ", ".join(missing))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="按需抓取开源历年真题语料到私人目录")
    parser.add_argument("--data-dir", default=".study",
                        help="私人状态目录（默认：仓库根 .study）")
    parser.add_argument("--update", action="store_true", help="更新已有语料副本")
    parser.add_argument("--status", action="store_true", help="只查看语料状态")
    args = parser.parse_args()

    data_dir = Path(args.data_dir).expanduser().resolve()
    if args.status:
        return status(data_dir)
    return fetch(data_dir, update=args.update)


if __name__ == "__main__":
    sys.exit(main())
