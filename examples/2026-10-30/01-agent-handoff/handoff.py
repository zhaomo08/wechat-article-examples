"""在临时仓库创建并恢复自造补丁；不访问 Jules 或任何真实项目。"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def git(cwd, *args):
    env = os.environ.copy()
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    return subprocess.run(
        ["git", "-c", "core.hooksPath=" + os.devnull,
         "-c", "commit.gpgsign=false", "-c", "user.name=Demo",
         "-c", "user.email=demo@example.com", *args],
        cwd=cwd, env=env, check=True, capture_output=True, text=True,
    ).stdout


def main():
    with tempfile.TemporaryDirectory(prefix="agent-handoff-") as directory:
        work = Path(directory)
        source, target = work / "source", work / "target"
        source.mkdir()
        git(source, "init", "-q", "-b", "main")
        (source / "app.py").write_text('print("hello")\n')
        git(source, "add", "app.py")
        git(source, "commit", "-q", "-m", "base")
        base = git(source, "rev-parse", "HEAD").strip()
        git(source, "checkout", "-q", "-b", "agent-sample")
        (source / "app.py").write_text('print("hello from patch")\n')
        git(source, "add", "app.py")
        git(source, "commit", "-q", "-m", "change greeting")
        patch = work / "0001-change.patch"
        patch.write_text(git(source, "format-patch", "-1", "--stdout"))
        (work / "task.md").write_text(
            f"# 自造交接记录\n\n基线：{base}\n\n目标：修改问候语。"
            "\n\n验证：python3 app.py\n\n剩余工作：无。\n"
        )
        git(work, "clone", "-q", "--no-local", "--single-branch",
            "--branch", "main", str(source), str(target))
        assert git(target, "rev-parse", "HEAD").strip() == base
        git(target, "am", str(patch))
        output = subprocess.check_output([sys.executable, "app.py"], cwd=target, text=True).strip()
        same = (source / "app.py").read_bytes() == (target / "app.py").read_bytes()
        clean = not git(target, "status", "--porcelain").strip()
        print("patches=1")
        print("app_output=" + output)
        print("source_matches_target=" + str(same).lower())
        print("target_worktree_clean=" + str(clean).lower())
        assert output == "hello from patch" and same and clean


if __name__ == "__main__":
    main()
