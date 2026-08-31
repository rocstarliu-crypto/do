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


def build_v15_from_v14():
    src = SITE / "Idea_Task_Hub_V1.4.html"
    if not src.exists():
        raise RuntimeError("Idea_Task_Hub_V1.4.html missing")
    s = src.read_text(encoding="utf-8")
    s = s.replace('<title>进度管理 - 任务与工作日志</title>', '<title>DO · 进度管理 - 任务 · 工作日志 · 专项任务</title>')
    s = s.replace('Idea Task Hub V1.4：我的一天、计划内任务、今明四状态、完成日志、专项任务、头脑风暴与全站Excel备份。', 'DO · 进度管理 V1.5：任务、工作日志、专项任务融合工作台；支持自定义品牌、我的一天、计划内任务、今明四状态、完成归档与全站Excel备份。')
    s = s.replace("const VERSION='V1.4';", "const VERSION='V1.5';")

    old_css = '.brand{display:flex;align-items:center;gap:10px;padding:4px 7px 12px}.brand-mark{width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,#657eea,#5d68d8);color:#fff;display:grid;place-items:center;font-size:18px}.brand-text{min-width:0}.brand-title{border:0;background:transparent;font-weight:800;font-size:15px;width:150px;padding:0;outline:none}.brand small{display:block;color:#9aa3b3;margin-top:3px;font-size:10px}'
    new_css = '.brand{position:relative;display:flex;align-items:center;gap:10px;padding:5px 7px 13px;border-radius:12px;cursor:default}.brand:hover{background:#f8faff}.brand-mark{width:44px;height:44px;border-radius:13px;background:linear-gradient(145deg,#58a8f4 0%,#596df0 58%,#7836e8 100%);color:#fff;display:grid;place-items:center;font-size:18px;font-weight:800;letter-spacing:-.5px;box-shadow:0 5px 13px rgba(83,100,224,.22);flex:none}.brand-text{min-width:0;line-height:1.05}.brand-kicker{display:block;font-weight:900;font-size:11px;letter-spacing:.4px;color:#111827;margin:0 0 2px}.brand-title-view{font-weight:900;font-size:16px;color:#111827;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:128px}.brand small{display:block;color:#8e97a7;margin-top:4px;font-size:9px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:142px}.brand-edit{position:absolute;right:2px;top:2px;border:0;background:#fff;color:#8792a5;width:24px;height:24px;border-radius:7px;opacity:0;transition:.15s}.brand:hover .brand-edit{opacity:1}.brand-edit:hover{background:#edf2ff;color:var(--blue)}.brand-preview{display:flex;align-items:center;gap:12px;background:#f8faff;border:1px solid #e1e7f1;border-radius:12px;padding:12px;margin-top:10px}.brand-preview .brand-mark{width:46px;height:46px}.brand-settings-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.brand-settings-grid .field.wide{grid-column:1/-1}'
    if old_css not in s:
        raise RuntimeError("V1.4 brand CSS signature missing")
    s = s.replace(old_css, new_css)

    old_html = '    <div class="brand"><span class="brand-mark">✣</span><div class="brand-text"><input id="brandTitle" class="brand-title" value="进度管理" title="双击或直接编辑网站名称"><small>任务与工作日志</small></div></div>'
    new_html = '    <div class="brand" id="brandBlock" title="双击自定义名称和标志"><span class="brand-mark" id="brandMark">DO</span><div class="brand-text"><span class="brand-kicker" id="brandKicker">DO</span><div id="brandTitleView" class="brand-title-view">进度管理</div><small id="brandSubtitle">任务 · 工作日志 · 专项任务</small></div><button class="brand-edit" id="brandEdit" title="自定义品牌">⚙</button></div>'
    if old_html not in s:
        raise RuntimeError("V1.4 brand HTML signature missing")
    s = s.replace(old_html, new_html)

    s = s.replace("return {version:VERSION,brand:'进度管理',tasks:[],categories:cats,manualLogs:{},activities:[],recycle:[],settings:{currentCategoryId:cats[0].id,boardLimit:15,boardFont:'12',lastPage:'today',completedCollapsed:false,allGroupCollapsed:{}},seq:0,visitStats:{total:0,days:{},firstVisit:nowISO(),lastVisit:nowISO()}};", "return {version:VERSION,brand:'进度管理',tasks:[],categories:cats,manualLogs:{},activities:[],recycle:[],settings:{brandMark:'DO',brandKicker:'DO',brandSubtitle:'任务 · 工作日志 · 专项任务',currentCategoryId:cats[0].id,boardLimit:15,boardFont:'12',lastPage:'today',completedCollapsed:false,allGroupCollapsed:{}},seq:0,visitStats:{total:0,days:{},firstVisit:nowISO(),lastVisit:nowISO()}};")
    s = s.replace("s.settings=Object.assign({currentCategoryId:s.categories[0]?.id||null,boardLimit:15,boardFont:'12',lastPage:'today',completedCollapsed:false,allGroupCollapsed:{}},s.settings||{});", "s.settings=Object.assign({brandMark:'DO',brandKicker:'DO',brandSubtitle:'任务 · 工作日志 · 专项任务',currentCategoryId:s.categories[0]?.id||null,boardLimit:15,boardFont:'12',lastPage:'today',completedCollapsed:false,allGroupCollapsed:{}},s.settings||{});")

    old_render = "function renderSidebar(){document.getElementById('brandTitle').value=state.brand||'进度管理';document.querySelectorAll('#nav button').forEach"
    new_render = "function renderSidebar(){const title=state.brand||'进度管理',mark=state.settings.brandMark||'DO',kicker=state.settings.brandKicker||'DO',subtitle=state.settings.brandSubtitle||'任务 · 工作日志 · 专项任务';document.getElementById('brandMark').textContent=mark;document.getElementById('brandKicker').textContent=kicker;document.getElementById('brandTitleView').textContent=title;document.getElementById('brandSubtitle').textContent=subtitle;document.title=`${kicker} · ${title} - ${subtitle}`;document.querySelectorAll('#nav button').forEach"
    if old_render not in s:
        raise RuntimeError("renderSidebar signature missing")
    s = s.replace(old_render, new_render)

    brand_func = r'''function openBrandSettings(){
 const mark=state.settings.brandMark||'DO',kicker=state.settings.brandKicker||'DO',title=state.brand||'进度管理',subtitle=state.settings.brandSubtitle||'任务 · 工作日志 · 专项任务';
 openModal('自定义名称与标志',`<div class="brand-settings-grid"><div class="field"><label>标志文字（1–3字符）</label><input id="brandMarkInput" maxlength="3" value="${esc(mark)}"></div><div class="field"><label>顶部简称</label><input id="brandKickerInput" maxlength="12" value="${esc(kicker)}"></div><div class="field wide"><label>主名称</label><input id="brandMainInput" maxlength="24" value="${esc(title)}"></div><div class="field wide"><label>副标题</label><input id="brandSubInput" maxlength="40" value="${esc(subtitle)}"></div></div><div class="brand-preview"><span class="brand-mark" id="brandPreviewMark">${esc(mark)}</span><div class="brand-text"><span class="brand-kicker" id="brandPreviewKicker">${esc(kicker)}</span><div class="brand-title-view" id="brandPreviewTitle">${esc(title)}</div><small id="brandPreviewSub">${esc(subtitle)}</small></div></div><p style="font-size:10px;color:#8b95a8;line-height:1.6;margin:10px 0 0">默认设计：DO / 进度管理 / 任务 · 工作日志 · 专项任务。只修改显示名称，不影响任务、日志、专项任务数据。</p>`,`<button data-close>取消</button><button class="primary" id="saveBrandSettings">保存</button>`,'small');
 const sync=()=>{document.getElementById('brandPreviewMark').textContent=document.getElementById('brandMarkInput').value.trim()||'DO';document.getElementById('brandPreviewKicker').textContent=document.getElementById('brandKickerInput').value.trim()||'DO';document.getElementById('brandPreviewTitle').textContent=document.getElementById('brandMainInput').value.trim()||'进度管理';document.getElementById('brandPreviewSub').textContent=document.getElementById('brandSubInput').value.trim()||'任务 · 工作日志 · 专项任务'};
 ['brandMarkInput','brandKickerInput','brandMainInput','brandSubInput'].forEach(id=>document.getElementById(id).addEventListener('input',sync));
 document.getElementById('saveBrandSettings').onclick=()=>{snapshot();state.settings.brandMark=document.getElementById('brandMarkInput').value.trim()||'DO';state.settings.brandKicker=document.getElementById('brandKickerInput').value.trim()||'DO';state.brand=document.getElementById('brandMainInput').value.trim()||'进度管理';state.settings.brandSubtitle=document.getElementById('brandSubInput').value.trim()||'任务 · 工作日志 · 专项任务';save();closeModal();render();toast('名称与标志已更新')};
}
'''
    anchor = "function openCategories(){"
    if anchor not in s:
        raise RuntimeError("openCategories anchor missing")
    s = s.replace(anchor, brand_func + anchor, 1)

    old_bind = "document.getElementById('brandTitle').onchange=e=>{snapshot();state.brand=e.target.value.trim()||'进度管理';save();render()};document.getElementById('brandTitle').ondblclick=e=>e.target.select();document.getElementById('manageCategories').onclick=openCategories;"
    new_bind = "document.getElementById('brandEdit').onclick=e=>{e.stopPropagation();openBrandSettings()};document.getElementById('brandBlock').ondblclick=e=>{if(e.target.id!=='brandEdit')openBrandSettings()};document.getElementById('manageCategories').onclick=openCategories;"
    if old_bind not in s:
        raise RuntimeError("old brand binding missing")
    s = s.replace(old_bind, new_bind)

    old_set = "const setRows=[['键','值'],['网站名称',state.brand],['当前分类',catById(state.settings.currentCategoryId)?.name||''],['四状态每列显示',state.settings.boardLimit],['本地访问次数',state.visitStats.total],['版本',VERSION]];"
    new_set = "const setRows=[['键','值'],['品牌标志',state.settings.brandMark||'DO'],['品牌简称',state.settings.brandKicker||'DO'],['网站名称',state.brand],['品牌副标题',state.settings.brandSubtitle||'任务 · 工作日志 · 专项任务'],['当前分类',catById(state.settings.currentCategoryId)?.name||''],['四状态每列显示',state.settings.boardLimit],['本地访问次数',state.visitStats.total],['版本',VERSION]];"
    if old_set not in s:
        raise RuntimeError("settings export signature missing")
    s = s.replace(old_set, new_set)

    s = s.replace('src="https://rocstarliu-crypto.github.io/project-progress-manager/"', 'src="./special/"')
    s = s.replace("const SPECIAL_WORKSPACE_KEY='project-progress-manager-v1.4.1-workspace';", "const SPECIAL_WORKSPACE_KEY='idea-task-hub-special-v1.4.1-workspace';")
    s = re.sub(r"const SPECIAL_PREV_KEYS=\[[^\n]*\];", "const SPECIAL_PREV_KEYS=[];", s, count=1)
    s = s.replace("const STORAGE='idea_task_hub_v1_1';", "const STORAGE='idea_task_hub_v1_5_do_public';")

    (SITE / "Idea_Task_Hub_V1.5.html").write_text(s, encoding="utf-8")
    (SITE / "index.html").write_text(s, encoding="utf-8")


def patch_special():
    app = SITE / "special" / "js" / "app.js"
    s = app.read_text(encoding="utf-8")
    s = s.replace("const WORKSPACE_STORAGE_KEY = 'project-progress-manager-v1.4.1-workspace';", "const WORKSPACE_STORAGE_KEY = 'idea-task-hub-special-v1.4.1-workspace';")
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


def verify():
    hub = (SITE / "index.html").read_text(encoding="utf-8")
    app = (SITE / "special" / "js" / "app.js").read_text(encoding="utf-8")
    assert "const VERSION='V1.5'" in hub
    assert 'id="brandMark">DO</span>' in hub
    assert '任务 · 工作日志 · 专项任务' in hub
    assert 'function openBrandSettings()' in hub
    assert 'src="./special/"' in hub
    assert "idea-task-hub-special-v1.4.1-workspace" in hub
    assert "idea-task-hub-special-v1.4.1-workspace" in app
    assert "idea_task_hub_v1_5_do_public" in hub
    block = app.split("function createDefaultWorkspace()", 1)[1].split("function mergedWorkspaceColumns", 1)[0]
    assert "createDemoCategoryState" not in block
    assert "state:createEmptyState(columns)" in block
    print("PASS: V1.5 full app + DO brand + blank isolated Special Tasks.")


if __name__ == "__main__":
    copy_hub()
    download_special()
    build_v15_from_v14()
    patch_special()
    verify()
