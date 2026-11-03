"""本轮导航与隔离提交。保留原始数据、用户删包状态和其他任务暂存。"""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
TITLE = "足球坐标首份回读（2026-11-03）"
GEOMETRY_TITLE = "足球单目几何迁移（2026-11-03）"
BASE = "04-shared/sdk-tests/足球坐标只读测试"
REPORT = BASE + "/结果回读/球位_20261103_113057_624030_回读.md"
SHARED = ["AGENTS.md", "INDEX.md", "CHANGELOG.md", "01-booster-kb/07-tech-platform/_index.md"]
OLD_TASK = "99-task-contexts/20261103-足球坐标只读测试"
GEOMETRY_TASK = "99-task-contexts/20261103-足球单目几何迁移"


def git(*args, data=None, env=None):
    result = subprocess.run(["git", *args], cwd=ROOT, input=data, capture_output=True, env=env)
    if result.returncode:
        raise RuntimeError((result.stdout + result.stderr).decode("utf-8", "replace"))
    return result.stdout


def add_entry(name, raw, title, report, detail):
    newline = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8").replace("\r\n", "\n")
    if title in text:
        return raw
    link = ("../../" if name.endswith("/_index.md") else "") + report
    if name == "CHANGELOG.md":
        added = "## 2026-11-03｜" + title + "\n\n" + detail + "[说明与产物](" + link + ")。原始提交文件保留，新版工具另包，用户已删除的旧ZIP不恢复。\n\n"
    else:
        added = "> **" + title + "**：[说明与产物](" + link + ")。" + detail + "\n\n"
    if name.endswith("/_index.md"):
        anchor = "# 技术平台\n\n"
        assert text.count(anchor) == 1
        text = text.replace(anchor, anchor + added, 1)
    else:
        position = text.index("\n\n") + 2
        text = text[:position] + added + text[position:]
    return text.replace("\n", newline).encode("utf-8")


def update(name, raw):
    raw = add_entry(name, raw, TITLE, REPORT,
        "用户首份快照检测与TF取得，球面RMS约11.49cm、同点云平面RMS约1.11cm，"
        "原[3.072,-0.207,-0.526]米拒用。用户补充球直径约20cm、身高90cm，2.5米从脚底量起；"
        "不能把trunk.x与脚底量测直接相减当定位误差。深度工具v0.1.1增加fit_rejected与独立诊断值，"
        "19项离线检查通过，未新增机器人运行或课程确认。")
    return add_entry(name, raw, GEOMETRY_TITLE, BASE + "/单目几何测试说明.md",
        "按用户要求沿用工训课chapter12底部取点、相机射线与地面求交，OS SDK负责取数和检测。"
        "原高度来自/head_pose与相机外参，没有写死90cm；保留旧位姿入口，完整相机到身体TF入口另补镜头离地高度。"
        "仅有头部帧时明确缺少身体参考。独立v0.2.0工具包、9格/3代码Notebook及20项离线检查完成；"
        "原始现场文件保留，未运行机器人、修改正式课程或确认踢出。")


def stage(env, name, data):
    blob = git("hash-object", "-w", "--path", name, "--stdin", data=data).decode().strip()
    git("update-index", "--add", "--cacheinfo", "100644", blob, name, env=env)


if "--commit" not in sys.argv:
    for name in SHARED:
        p = ROOT / name
        before = TASK / "before" / name
        before.parent.mkdir(parents=True, exist_ok=True)
        if not before.exists():
            before.write_bytes(p.read_bytes())
        p.write_bytes(update(name, p.read_bytes()))
    print("Navigation updated.")
else:
    head = git("rev-parse", "HEAD").decode().strip()
    staged_before = git("ls-files", "--stage", "-z")
    shared_index = {name: git("show", ":" + name) for name in SHARED}
    env = dict(os.environ, GIT_INDEX_FILE=str(TASK / "review.index"))
    git("read-tree", head, env=env)
    for name in SHARED:
        stage(env, name, update(name, git("show", head + ":" + name)))
    own = [BASE + "/" + name for name in ["probe_ball_coordinates.py", "README.md", "K1足球坐标_只读测试.ipynb", "K1足球坐标_测试工具包_v0.1.1.zip",
        "geometry_ball_coordinates.py", "单目几何测试说明.md", "K1足球坐标_单目几何测试.ipynb", "几何迁移_旧快照复算.json", "K1足球坐标_单目几何工具包_v0.2.0.zip"]]
    own += [OLD_TASK + "/" + name for name in ["build_delivery.py", "tests/test_probe.py", "离线检查输出.txt", "校验结果.json"]]
    for directory in [ROOT / BASE / "K1足球坐标_测试工具包", ROOT / BASE / "结果回读", TASK, ROOT / GEOMETRY_TASK]:
        for p in directory.rglob("*"):
            if (p.is_file() and not any(part in {"before", "__pycache__"} for part in p.relative_to(directory).parts)
                    and not p.name.endswith((".index", ".index.lock"))):
                own.append(p.relative_to(ROOT).as_posix())
    own = sorted(set(own))
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in own}
    for name in own:
        stage(env, name, (ROOT / name).read_bytes())
    assert git("rev-parse", "HEAD").decode().strip() == head
    assert git("ls-files", "--stage", "-z") == staged_before
    git("diff", "--cached", "--check", env=env)
    print(git("diff", "--cached", "--stat", env=env).decode("utf-8"))
    print(git("commit", "-m", "feat: reuse K1 course ground-ray geometry for OS SDK coordinate tests", env=env).decode("utf-8"))
    commit = git("rev-parse", "HEAD").decode().strip()
    for name in own:
        stage(None, name, git("show", commit + ":" + name))
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == hashes[name]
    for name in SHARED:
        stage(None, name, update(name, shared_index[name]))
    def entries(raw):
        return {line.split(b"\t", 1)[1]: line for line in raw.split(b"\0") if line}
    previous = entries(staged_before)
    current = entries(git("ls-files", "--stage", "-z"))
    task_paths = {p.encode("utf-8") for p in own + SHARED}
    assert {p:v for p,v in previous.items() if p not in task_paths} == {p:v for p,v in current.items() if p not in task_paths}
    (TASK / "before/commit_receipt.json").write_text(json.dumps(
        {"commit": commit, "parent": head, "staging_preserved": True, "task_files": own,
         "input_files_byte_preserved": True, "old_zip_deletion_preserved": True},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print("Commit: " + commit + "; input bytes and pre-existing staging preserved")
