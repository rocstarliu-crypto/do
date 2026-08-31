from pathlib import Path
import re
import shutil
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
TMP = ROOT / ".pages_tmp"
ARCHIVE = TMP / "project-progress-manager.tar.gz"
SOURCE = TMP / "project-progress-manager"


def copy_hub():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    excluded = {".git", ".github", "_site", ".pages_tmp"}
    for item in ROOT.iterdir():
        if item.name in excluded:
            continue
        target = SITE / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


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


def patch_hub():
    for name in ("index.html", "Idea_Task_Hub_V1.4.html"):
        p = SITE / name
        if not p.exists():
            continue
        s = p.read_text(encoding="utf-8")
        s = s.replace(
            'src="https://rocstarliu-crypto.github.io/project-progress-manager/"',
            'src="./special/"',
        )
        s = s.replace(
            "const SPECIAL_WORKSPACE_KEY='project-progress-manager-v1.4.1-workspace';",
            "const SPECIAL_WORKSPACE_KEY='idea-task-hub-special-v1.4.1-workspace';",
        )
        s = re.sub(
            r"const SPECIAL_PREV_KEYS=\[[^\n]*\];",
            "const SPECIAL_PREV_KEYS=[];",
            s,
            count=1,
        )
        p.write_text(s, encoding="utf-8")


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


def verify():
    hub = (SITE / "Idea_Task_Hub_V1.4.html").read_text(encoding="utf-8")
    app = (SITE / "special" / "js" / "app.js").read_text(encoding="utf-8")
    assert 'src="./special/"' in hub
    assert "idea-task-hub-special-v1.4.1-workspace" in hub
    assert "idea-task-hub-special-v1.4.1-workspace" in app
    block = app.split("function createDefaultWorkspace()", 1)[1].split("function mergedWorkspaceColumns", 1)[0]
    assert "createDemoCategoryState" not in block
    assert "state:createEmptyState(columns)" in block
    print("PASS: Special Tasks defaults to one empty project with isolated storage.")


if __name__ == "__main__":
    copy_hub()
    download_special()
    patch_hub()
    patch_special()
    verify()
