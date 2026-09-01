from pathlib import Path
import base64
import gzip
import re
import shutil
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
TMP = ROOT / ".pages_tmp"
ARCHIVE = TMP / "project-progress-manager.tar.gz"
SOURCE = TMP / "project-progress-manager"
RELEASE = ROOT / "release" / "v1.11"


def prepare_site():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)


def download_special():
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True)
    url = "https://github.com/rocstarliu-crypto/project-progress-manager/archive/refs/heads/main.tar.gz"
    urllib.request.urlretrieve(url, ARCHIVE)
    SOURCE.mkdir()
    with tarfile.open(ARCHIVE, "r:gz") as tf:
        members = tf.getmembers()
        prefix = members[0].name.split("/", 1)[0] + "/"
        for member in members:
            if not member.name.startswith(prefix) or member.name == prefix.rstrip("/"):
                continue
            member.name = member.name[len(prefix):]
            tf.extract(member, SOURCE, filter="data")
    shutil.copytree(SOURCE, SITE / "special")


def patch_special():
    app = SITE / "special" / "js" / "app.js"
    s = app.read_text(encoding="utf-8")
    s = s.replace(
        "const WORKSPACE_STORAGE_KEY = 'project-progress-manager-v1.4.1-workspace';",
        "const WORKSPACE_STORAGE_KEY = 'idea-task-hub-special-v1.4.1-workspace';",
    )
    s = re.sub(
        r"const PREVIOUS_WORKSPACE_STORAGE_KEYS = \[[^\n]*\];",
        "const PREVIOUS_WORKSPACE_STORAGE_KEYS = [];",
        s,
        count=1,
    )
    s = re.sub(
        r"const LEGACY_STORAGE_KEY = '[^']*';",
        "const LEGACY_STORAGE_KEY = 'idea-task-hub-special-legacy-unused';",
        s,
        count=1,
    )
    pattern = r"function createDefaultWorkspace\(\) \{.*?\n\}\n\nfunction mergedWorkspaceColumns"
    replacement = """function createDefaultWorkspace() {
  const columns=defaultColumns();
  return {kind:WORKSPACE_KIND,version:2,appVersion:APP_VERSION,nextProjectId:2,activeProjectId:'project_1',columns:columns,projects:[
    {id:'project_1',name:'项目一',state:createEmptyState(columns)}
  ]};
}

function mergedWorkspaceColumns"""
    s, count = re.subn(pattern, replacement, s, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError("createDefaultWorkspace patch failed")
    app.write_text(s, encoding="utf-8")


def build_v111():
    chunks = sorted(RELEASE.glob("*.b64"))
    if [p.name for p in chunks] != [f"{i:02d}.b64" for i in range(6)]:
        raise RuntimeError(f"V1.11 payload incomplete: {[p.name for p in chunks]}")
    payload = "".join(p.read_text(encoding="utf-8").strip() for p in chunks)
    html = gzip.decompress(base64.b64decode(payload)).decode("utf-8")
    (SITE / "index.html").write_text(html, encoding="utf-8")
    (SITE / "DO_进度管理_V1.11.html").write_text(html, encoding="utf-8")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")


def verify():
    hub = (SITE / "index.html").read_text(encoding="utf-8")
    special = (SITE / "special" / "js" / "app.js").read_text(encoding="utf-8")

    assert "const VERSION='V1.11'" in hub
    assert "function v111RootTasks()" in hub
    assert "五视图统一数据逻辑" in hub
    for label in ["我的一天", "计划内", "全部任务", "日程", "任务状态"]:
        assert label in hub
    for status in ["未开展", "进行中", "已完成", "归档", "完成待优化"]:
        assert status in hub

    assert "signUp({email,password" in hub
    assert "signInWithPassword" in hub
    assert "resetPasswordForEmail" in hub
    assert "注册账号" in hub and "忘记密码" in hub

    assert "fetch('./special/index.html'" in hub or 'fetch("./special/index.html"' in hub
    assert "idea-task-hub-special-v1.4.1-workspace" in special
    block = special.split("function createDefaultWorkspace()", 1)[1].split("function mergedWorkspaceColumns", 1)[0]
    assert "createEmptyState(columns)" in block
    assert "createDemoCategoryState" not in block


if __name__ == "__main__":
    prepare_site()
    download_special()
    patch_special()
    build_v111()
    verify()
    print("V1.11 GitHub Pages build verification passed")
