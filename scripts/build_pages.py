from pathlib import Path
import base64
import gzip
import hashlib
import json
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


def build_v20():
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
    html = html_bytes.decode("utf-8")
    (SITE / "index.html").write_text(html, encoding="utf-8")
    (SITE / "DO_融合工作台_V2.0.html").write_text(html, encoding="utf-8")
    shutil.copy2(ACCEPTANCE, SITE / "DO_融合工作台_V2.0_验收表.xlsx")
    shutil.copy2(STATUS_TRACE, SITE / "DO_完成归档与待优化_对话需求追溯.md")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")


def verify():
    hub = (SITE / "index.html").read_text(encoding="utf-8")
    assert "DO 融合工作台 V2.0" in hub
    assert "DEV_ARCHIVE_HTML" not in hub
    assert 'data-page="archive"' not in hub
    assert "任务状态 · 四状态" in hub
    assert "v20ArchiveBrief" in hub
    assert "annotationFeedback" in hub
    assert "lp00102@hotmail.com" in hub
    assert "rocstarliu-crypto/do/issues/new" in hub
    assert "height:max(900px,calc(100vh - 128px))" in hub
    assert "return typeof supabase!==\"undefined\"?supabase:null" in hub
    assert "persistSession:true,autoRefreshToken:true,detectSessionInUrl:true" in hub
    assert "PASSWORD_RECOVERY" in hub and "updateUser({password})" in hub
    assert "page==='brainstorm')ws.innerHTML=brainstormHTML()" in hub
    assert "把想法整理成可连接的流程图" in hub
    assert "数据保存在当前浏览器；已加入外层全站 Excel 备份。" not in hub
    assert "height:max(820px,calc(100vh - 118px))" in hub
    for label in ["我的一天", "计划内", "全部任务", "日程", "任务状态", "专项任务", "头脑风暴"]:
        assert label in hub
    assert ACCEPTANCE.exists() and ACCEPTANCE.stat().st_size > 50_000
    assert STATUS_TRACE.exists() and STATUS_TRACE.stat().st_size > 2_000


if __name__ == "__main__":
    prepare_site()
    build_v20()
    verify()
    print("DO 融合工作台 V2.0 GitHub Pages build verification passed")
