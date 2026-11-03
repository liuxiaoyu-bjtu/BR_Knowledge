"""仅提交本次测试工具及导航增量；共享文件保留其他修改与暂存。"""
from pathlib import Path
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
OUT = ROOT / "04-shared/sdk-tests/足球坐标只读测试"
TITLE = "足球坐标只读测试（2026-11-03）"
SHARED = ["AGENTS.md", "INDEX.md", "CHANGELOG.md", "01-booster-kb/07-tech-platform/_index.md"]


def git(*args, data=None, env=None):
    result = subprocess.run(["git", *args], cwd=ROOT, input=data, capture_output=True, env=env)
    if result.returncode:
        raise RuntimeError((result.stdout + result.stderr).decode("utf-8", "replace"))
    return result.stdout


def update(name, raw):
    newline = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8").replace("\r\n", "\n")
    if TITLE in text:
        return raw
    link = "04-shared/sdk-tests/足球坐标只读测试/README.md"
    if name.endswith("/_index.md"):
        link = "../../" + link
    if name == "CHANGELOG.md":
        added = ("## 2026-11-03｜" + TITLE + "\n\n"
                 "按用户要求新增[静态坐标测试工具](" + link + ")：独立py、9格/4代码Notebook和ZIP。"
                 "检测框经深度与内参求候选球心，再用公开get_transform转换到trunk，保存原图、原深度、矩阵、时间差及卷尺偏差。"
                 "默认0.001、同像素配准和光轴Z按假设记录；没有将trunk直接等同踢球控制原点。"
                 "16项离线检查通过，未运行机器人或修改课程附件/登记确认。\n\n")
    else:
        added = ("> **" + TITLE + "**：[只读测试程序、Notebook与工具包](" + link + ")用于核对"
                 "Ball框→深度球心→TF→trunk候选坐标，自动保存原始数据和卷尺偏差。"
                 "无需教师JSON，无运动/踢球调用；0.001深度比例、配准及控制原点待核实。"
                 "16项离线检查通过，未运行机器人或新增课程确认。\n\n")
    if name.endswith("/_index.md"):
        anchor = "# 技术平台\n\n"
        if text.count(anchor) != 1:
            raise RuntimeError("导航标题不唯一")
        text = text.replace(anchor, anchor + added, 1)
    else:
        position = text.index("\n\n") + 2
        text = text[:position] + added + text[position:]
    return text.replace("\n", newline).encode("utf-8")


def stage(env, name, raw):
    blob = git("hash-object", "-w", "--path", name, "--stdin", data=raw).decode().strip()
    git("update-index", "--add", "--cacheinfo", "100644", blob, name, env=env)


if "--commit" not in sys.argv:
    for name in SHARED:
        path = ROOT / name
        backup = TASK / "before" / name
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            backup.write_bytes(path.read_bytes())
        path.write_bytes(update(name, path.read_bytes()))
    print("Updated four navigation documents.")
else:
    head = git("rev-parse", "HEAD").decode().strip()
    index_before = git("ls-files", "--stage", "-z")
    original = {name: git("show", ":" + name) for name in SHARED}
    env = dict(os.environ, GIT_INDEX_FILE=str(TASK / "task.index"))
    git("read-tree", head, env=env)
    for name in SHARED:
        stage(env, name, update(name, git("show", head + ":" + name)))
    own = []
    for base in [OUT, TASK]:
        for path in base.rglob("*"):
            if (not path.is_file() or any(p in {"before", "__pycache__"} for p in path.relative_to(base).parts)
                    or path.name.endswith((".index", ".index.lock"))):
                continue
            name = path.relative_to(ROOT).as_posix()
            own.append(name)
            stage(env, name, path.read_bytes())
    if git("rev-parse", "HEAD").decode().strip() != head or git("ls-files", "--stage", "-z") != index_before:
        raise RuntimeError("HEAD或暂存状态发生变化，请重新准备")
    git("diff", "--cached", "--check", env=env)
    print(git("diff", "--cached", "--stat", env=env).decode("utf-8"))
    print(git("commit", "-m", "test: add read-only K1 detection depth and TF coordinate probe", env=env).decode("utf-8"))
    commit = git("rev-parse", "HEAD").decode().strip()
    for name in own:
        stage(None, name, git("show", commit + ":" + name))
    for name in SHARED:
        stage(None, name, update(name, original[name]))
    (TASK / "before/commit_receipt.json").write_text(json.dumps(
        {"commit": commit, "parent": head, "staging_preserved": True, "task_files": own},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print("Commit: " + commit + "; prior staging preserved")
