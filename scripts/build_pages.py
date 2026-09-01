from pathlib import Path
import base64, gzip, hashlib, json, re, shutil, tarfile, urllib.request

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
TMP = ROOT / ".pages_tmp"
ARCHIVE = TMP / "project-progress-manager.tar.gz"
SOURCE = TMP / "project-progress-manager"
RELEASE = ROOT / "release" / "v2.0.1"
SPECIAL_COMMIT = "d765e2f6ef8b571c5de948754ef05c4fe1b5709f"
EXPECTED_TEMPLATE_SHA256 = "ecd19cf0fbac63d41ebfc9b602fef7e9d9ae30bd3787eb70738703cbb9782bbf"
EXPECTED_SPECIAL_SHA256 = "a2897b93c201706a2dfbe61cd295c34071105a1f556931601289ffd2d90ffe7b"
EXPECTED_FINAL_SHA256 = "2fd811a0a8aff69b682feeca6bb90150d1e7f067972ea501efd8b76f75dc3864"

SPECIAL_SOURCE_PATHS = [
    "index.html", "css/style.css", "css/cloud.css", "css/projects.css",
    "css/password-reset.css", "css/history.css", "css/chart-align.css",
    "libs/xlsx.full.min.js", "libs/exceljs.min.js", "libs/supabase.min.js",
    "js/app.js", "js/cloud-config.js", "js/cloud.js",
]


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def prepare_site():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)


def download_special():
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True)
    url = f"https://github.com/rocstarliu-crypto/project-progress-manager/archive/{SPECIAL_COMMIT}.tar.gz"
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


def patch_special_source():
    app = SOURCE / "js" / "app.js"
    s = app.read_text(encoding="utf-8")
    s = s.replace(
        "const WORKSPACE_STORAGE_KEY = 'project-progress-manager-v1.4.1-workspace';",
        "const WORKSPACE_STORAGE_KEY = 'idea-task-hub-special-v1.4.1-workspace';",
    )
    s = re.sub(r"const PREVIOUS_WORKSPACE_STORAGE_KEYS = \[[^\n]*\];", "const PREVIOUS_WORKSPACE_STORAGE_KEYS = [];", s, count=1)
    s = re.sub(r"const LEGACY_STORAGE_KEY = '[^']*';", "const LEGACY_STORAGE_KEY = 'idea-task-hub-special-legacy-unused';", s, count=1)
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


def build_special_single_file():
    manifest = {p: sha256_bytes((SOURCE / p).read_bytes()) for p in SPECIAL_SOURCE_PATHS}
    html = (SOURCE / "index.html").read_text(encoding="utf-8")
    html = html.replace("<title>项目进度管理 V1.4.1</title>", "<title>专项任务 · 项目进度管理 V1.4.1 · DO V2.0 本地融合模块</title>")
    for p in SPECIAL_SOURCE_PATHS[1:7]:
        css = (SOURCE / p).read_text(encoding="utf-8")
        html = html.replace(f'<link rel="stylesheet" href="{p}">', f'<style data-v2-source="{p}">\n{css}\n</style>')
    integration_css = '''
<style id="doV2SpecialIntegration">
/* DO V2.0 integration: one app / one account. Specialized business logic remains local. */
.cloud-toolbar,#cloudModal,#passwordResetModal,#loginHistoryModal,#projectHistoryModal{display:none!important}
.app-header{padding-right:12px}
.brand em{max-width:none}
body::before{content:"本地模块 · 账号由 DO V2.0 统一管理";position:fixed;right:12px;bottom:8px;z-index:9999;background:#eef4ff;color:#315fae;border:1px solid #c9d9f5;border-radius:999px;padding:4px 9px;font:11px Microsoft YaHei,Arial;pointer-events:none}
</style>'''
    html = html.replace("</head>", integration_css + "\n</head>")
    html = html.replace(
        '<div class="brand"><span class="brand-mark">◆</span><span>项目进度管理</span><em>V1.4.1</em></div>',
        '<div class="brand"><span class="brand-mark">◆</span><span>专项任务</span><em>原项目进度管理 V1.4.1 · 本地融合</em></div>',
    )
    for p in ["libs/xlsx.full.min.js", "libs/exceljs.min.js"]:
        code = (SOURCE / p).read_text(encoding="utf-8")
        html = html.replace(f'<script src="{p}"></script>', f'<script data-v2-source="{p}">\n{code}\n</script>')
    for p in ["libs/supabase.min.js", "js/cloud-config.js", "js/cloud.js"]:
        b64 = base64.b64encode((SOURCE / p).read_bytes()).decode("ascii")
        html = html.replace(
            f'<script src="{p}"></script>',
            f'<script type="application/x-v2-original-source" data-path="{p}" data-encoding="base64">{b64}</script>',
        )
    app = (SOURCE / "js" / "app.js").read_text(encoding="utf-8")
    app = app.replace("const WORKSPACE_STORAGE_KEY = 'idea-task-hub-special-v1.4.1-workspace';", "const WORKSPACE_STORAGE_KEY = 'do-v2-special-workspace';")
    app = app.replace("  if (window.CloudSync && !window.CloudSync.isApplyingRemote()) window.CloudSync.scheduleSave();", "  /* DO V2: specialized module cloud sync is owned by outer account */")
    app = app.replace("const marker='<script src=\"js/app.js\"></script>';", "const marker='<script src=\"js/app.js\"><\\/script>';", 1)
    app = app.replace("const tag='<script src=\"'+path+'\"></script>';", "const tag='<script src=\"'+path+'\"><\\/script>';", 1)
    html = html.replace('<script src="js/app.js"></script>', f'<script data-v2-source="js/app.js">\n{app}\n</script>')
    man = json.dumps(manifest, ensure_ascii=False)
    head, tail = html.rsplit("</body>", 1)
    html = head + f'<script type="application/json" id="doV2SpecialSourceManifest">{man}</script>\n</body>' + tail
    data = html.encode("utf-8")
    if sha256_bytes(data) != EXPECTED_SPECIAL_SHA256:
        raise RuntimeError(f"special fused hash mismatch: {sha256_bytes(data)}")
    return html


def load_template():
    chunks = sorted(RELEASE.glob("*.b64"))
    if not chunks:
        raise RuntimeError("V2.0.1 template chunks missing")
    payload = "".join(p.read_text(encoding="utf-8").strip() for p in chunks)
    data = gzip.decompress(base64.b64decode(payload))
    if sha256_bytes(data) != EXPECTED_TEMPLATE_SHA256:
        raise RuntimeError(f"template hash mismatch: {sha256_bytes(data)}")
    return data.decode("utf-8")


def build_v201():
    special = build_special_single_file()
    template = load_template()
    if "__SPECIAL_PAYLOAD__" not in template:
        raise RuntimeError("special placeholder missing")
    special_b64 = base64.b64encode(special.encode("utf-8")).decode("ascii")
    html = template.replace("__SPECIAL_PAYLOAD__", special_b64, 1)
    data = html.encode("utf-8")
    if sha256_bytes(data) != EXPECTED_FINAL_SHA256:
        raise RuntimeError(f"final V2.0.1 hash mismatch: {sha256_bytes(data)}")
    (SITE / "index.html").write_bytes(data)
    (SITE / "DO_进度管理_V2.0.1.html").write_bytes(data)
    (SITE / ".nojekyll").write_text("", encoding="utf-8")


def verify():
    hub = (SITE / "index.html").read_text(encoding="utf-8")
    assert "const VERSION='V2.0.1';" in hub
    assert "开发档案" not in hub
    assert '<button data-page="board"><span class="ico">⌘</span><span>四状态</span></button>' in hub
    assert 'function specialTasksHTML(){return `<section class="special-integrated special-integrated-clean"><iframe' in hub
    assert "lp00102@hotmail.com" in hub
    assert "https://github.com/rocstarliu-crypto/do/issues/new?title=" in hub
    assert "function fitSpecialFrame()" in hub and "actualNeed" in hub
    assert "signUp({email,password" in hub and "signInWithPassword" in hub and "resetPasswordForEmail" in hub
    print("V2.0.1 GitHub Pages build verification passed")


if __name__ == "__main__":
    prepare_site()
    download_special()
    patch_special_source()
    build_v201()
    verify()
