from pathlib import Path
import base64
import gzip
import hashlib
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
RELEASE = ROOT / "release" / "v2.0"
MANIFEST = RELEASE / "manifest.json"
ACCEPTANCE = ROOT / "docs" / "DO_融合工作台_V2.0_三模块需求分类与验收表_2026-09-02.xlsx"
STATUS_TRACE = ROOT / "docs" / "DO_完成归档与待优化_对话需求追溯_2026-09-02.md"


def prepare_site():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)


def read_v20():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected = [f"{i:02d}.b64" for i in range(manifest["chunk_count"])]
    chunks = sorted(RELEASE.glob("*.b64"))
    if [p.name for p in chunks] != expected:
        raise RuntimeError(f"V2.0 payload incomplete: {[p.name for p in chunks]}")
    payload = "".join(p.read_text(encoding="utf-8").strip() for p in chunks)
    html_bytes = gzip.decompress(base64.b64decode(payload))
    actual_sha = hashlib.sha256(html_bytes).hexdigest()
    if actual_sha != manifest["html_sha256"]:
        raise RuntimeError(f"V2.0 SHA-256 mismatch: {actual_sha}")
    return html_bytes.decode("utf-8")


def public_patch(html):
    # 公共版启用新的空白数据空间：不删除旧数据，只是不再自动读取用户之前填写的内容。
    html = html.replace("const STORAGE='do_progress_v2_0';", "const STORAGE='do_progress_v2_0_public_clean_20260903';", 1)
    html = html.replace("const PREV_STORAGE='idea_task_hub_public';", "const PREV_STORAGE='do_progress_public_clean_no_legacy';", 1)
    html = html.replace("const ANNOTATION_STORAGE='do_v17_annotation_notes';", "const ANNOTATION_STORAGE='do_v20_public_annotation_clean_20260903';", 1)
    html = html.replace("return 'do-v2-special-v1.4.1:'+(outerCloudSession?.user?.id||'guest')", "return 'do-v20-public-special-v1.4.1:'+(outerCloudSession?.user?.id||'guest')", 1)
    html = html.replace("return 'do-v2-canvas-v1.13:'+(outerCloudSession?.user?.id||'guest')", "return 'do-v20-public-canvas-v1.13:'+(outerCloudSession?.user?.id||'guest')", 1)

    # 专项任务：模块底部默认延伸到当前页面底部，扩大中间任务区域。
    marker = "function bindSpecial(){const frame=document.getElementById('specialFrame');"
    if marker not in html:
        raise RuntimeError('bindSpecial marker not found')
    replacement = """function syncPublicSpecialHeight(){if(page!=='special')return;const frame=document.getElementById('specialFrame');if(!frame)return;const top=frame.getBoundingClientRect().top;frame.style.height=Math.max(620,Math.floor(window.innerHeight-top-8))+'px';frame.style.minHeight='0'}\nfunction bindSpecial(){const frame=document.getElementById('specialFrame');"""
    html = html.replace(marker, replacement, 1)
    html = html.replace("frame.onload=()=>{frame.dataset.ready='1';try{const z=(fontZones().special||15)/15;frame.contentDocument.body.style.zoom=String(Math.max(.8,Math.min(1.6,z)))}catch(e){}};try{frame.srcdoc=specialBundleHTML()}", "frame.onload=()=>{frame.dataset.ready='1';try{const z=(fontZones().special||15)/15;frame.contentDocument.body.style.zoom=String(Math.max(.8,Math.min(1.6,z)))}catch(e){}syncPublicSpecialHeight()};try{frame.srcdoc=specialBundleHTML();requestAnimationFrame(syncPublicSpecialHeight);setTimeout(syncPublicSpecialHeight,80)}", 1)
    html = html.replace("window.addEventListener('keydown',e=>{", "window.addEventListener('resize',syncPublicSpecialHeight);\nwindow.addEventListener('keydown',e=>{", 1)
    html = html.replace(".workspace[data-page=\"special\"] .special-integrated{margin:0 0 96px}", ".workspace[data-page=\"special\"] .special-integrated{margin:0 0 96px}.workspace[data-page=\"special\"]{padding-bottom:86px}", 1)
    return html


def build_v20():
    original = read_v20()
    public = public_patch(original)

    # 主页发布本次优化后的空白公共版；冻结 V2.0 原文件继续保留，便于回退。
    (SITE / "index.html").write_text(public, encoding="utf-8")
    (SITE / "DO_融合工作台_V2.0_专项空间优化空白版.html").write_text(public, encoding="utf-8")
    (SITE / "DO_融合工作台_V2.0.html").write_text(original, encoding="utf-8")
    shutil.copy2(ACCEPTANCE, SITE / "DO_融合工作台_V2.0_验收表.xlsx")
    shutil.copy2(STATUS_TRACE, SITE / "DO_完成归档与待优化_对话需求追溯.md")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")


def verify():
    hub = (SITE / "index.html").read_text(encoding="utf-8")
    assert "DO 融合工作台 V2.0" in hub
    assert "syncPublicSpecialHeight" in hub
    assert "do_progress_v2_0_public_clean_20260903" in hub
    assert "do-v20-public-special-v1.4.1:" in hub
    assert "do-v20-public-canvas-v1.13:" in hub

    # 账号注册、找回密码和恢复链接设置新密码必须保留。
    assert ".auth.signUp(" in hub
    assert ".auth.resetPasswordForEmail(" in hub
    assert "PASSWORD_RECOVERY" in hub
    assert "updateUser({password})" in hub

    for label in ["我的一天", "计划内", "全部任务", "日程", "任务状态", "专项任务", "头脑风暴"]:
        assert label in hub
    assert ACCEPTANCE.exists() and ACCEPTANCE.stat().st_size > 50_000
    assert STATUS_TRACE.exists() and STATUS_TRACE.stat().st_size > 2_000


if __name__ == "__main__":
    prepare_site()
    build_v20()
    verify()
    print("DO 融合工作台 GitHub Pages public blank/special-space verification passed")
