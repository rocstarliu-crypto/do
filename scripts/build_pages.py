from pathlib import Path
import base64, gzip, lzma, re, shutil, tarfile, urllib.request, json, hashlib

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'_site'
TMP=ROOT/'.v20_restore_tmp'
ARCHIVE=TMP/'project-progress-manager.tar.gz'
SOURCE=TMP/'project-progress-manager'
V111=ROOT/'release'/'v1.11'
V20=ROOT/'release'/'v2.0-chat'
TARGET_SHA='c820550908acc126700a0faeba1409f6c96c749901aafebcd19fec694af901a6'
TARGET_SPECIAL_SHA='a2897b93c201706a2dfbe61cd295c34071105a1f556931601289ffd2d90ffe7b'
TARGET_CANVAS_SHA='ddad338c6675b64911d6198c600de8baabc9bafa8b932d14a6847a8527b58c00'
CSS_FILES=['css/style.css','css/cloud.css','css/projects.css','css/password-reset.css','css/history.css','css/chart-align.css']
ACTIVE_JS=['libs/xlsx.full.min.js','libs/exceljs.min.js','js/app.js']
INERT_JS=['libs/supabase.min.js','js/cloud-config.js','js/cloud.js']
SOURCE_ORDER=['index.html']+CSS_FILES+['libs/xlsx.full.min.js','libs/exceljs.min.js','libs/supabase.min.js','js/app.js','js/cloud-config.js','js/cloud.js']

def sha256_bytes(b): return hashlib.sha256(b).hexdigest()

def prepare():
    if SITE.exists(): shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    if TMP.exists(): shutil.rmtree(TMP)
    TMP.mkdir(parents=True)

def download_special_source():
    url='https://github.com/rocstarliu-crypto/project-progress-manager/archive/refs/heads/main.tar.gz'
    urllib.request.urlretrieve(url,ARCHIVE)
    SOURCE.mkdir()
    with tarfile.open(ARCHIVE,'r:gz') as tf:
        members=tf.getmembers(); prefix=members[0].name.split('/',1)[0]+'/'
        for m in members:
            if not m.name.startswith(prefix) or m.name==prefix.rstrip('/'): continue
            m.name=m.name[len(prefix):]
            tf.extract(m,SOURCE,filter='data')

def load_v111():
    chunks=sorted(V111.glob('*.b64'))
    if [p.name for p in chunks] != [f'{i:02d}.b64' for i in range(6)]: raise RuntimeError('V1.11 payload incomplete')
    payload=''.join(p.read_text(encoding='utf8').strip() for p in chunks)
    html=gzip.decompress(base64.b64decode(payload)).decode('utf8')
    html=html.replace("const VERSION='V1.10-LIFECYCLE-PREVIEW';","const VERSION='V1.11';")
    return html

def patch_special_app(s):
    s=s.replace("const WORKSPACE_STORAGE_KEY = 'project-progress-manager-v1.4.1-workspace';","const WORKSPACE_STORAGE_KEY = 'do-v2-special-workspace';")
    s=re.sub(r"const PREVIOUS_WORKSPACE_STORAGE_KEYS = \[[^\n]*\];","const PREVIOUS_WORKSPACE_STORAGE_KEYS = [];",s,count=1)
    s=re.sub(r"const LEGACY_STORAGE_KEY = '[^']*';","const LEGACY_STORAGE_KEY = 'idea-task-hub-special-legacy-unused';",s,count=1)
    s=s.replace("  if (window.CloudSync && !window.CloudSync.isApplyingRemote()) window.CloudSync.scheduleSave();","  /* DO V2: specialized module cloud sync is owned by outer account */")
    pattern=r"function createDefaultWorkspace\(\) \{.*?\n\}\n\nfunction mergedWorkspaceColumns"
    replacement="""function createDefaultWorkspace() {
  const columns=defaultColumns();
  return {kind:WORKSPACE_KIND,version:2,appVersion:APP_VERSION,nextProjectId:2,activeProjectId:'project_1',columns:columns,projects:[
    {id:'project_1',name:'项目一',state:createEmptyState(columns)}
  ]};
}

function mergedWorkspaceColumns"""
    s,n=re.subn(pattern,replacement,s,count=1,flags=re.S)
    if n!=1: raise RuntimeError('special createDefaultWorkspace patch failed')
    return s

def build_special():
    source_hashes={rel:sha256_bytes((SOURCE/rel).read_bytes()) for rel in SOURCE_ORDER}
    print('special source hashes',json.dumps(source_hashes,ensure_ascii=False))
    html=(SOURCE/'index.html').read_text(encoding='utf8')
    html=html.replace('<title>项目进度管理 V1.4.1</title>','<title>专项任务 · 项目进度管理 V1.4.1 · DO V2.0 本地融合模块</title>',1)
    html=html.replace('<div class="brand"><span class="brand-mark">◆</span><span>项目进度管理</span><em>V1.4.1</em></div>','<div class="brand"><span class="brand-mark">◆</span><span>专项任务</span><em>原项目进度管理 V1.4.1 · 本地融合</em></div>',1)
    for rel in CSS_FILES:
        css=(SOURCE/rel).read_text(encoding='utf8')
        pat=re.compile(rf'<link\s+rel=["\']stylesheet["\']\s+href=["\']{re.escape(rel)}["\']\s*/?>',re.I)
        html,n=pat.subn(f'<style data-v2-source="{rel}">\n{css}\n</style>',html,count=1)
        if n!=1: raise RuntimeError('CSS marker missing '+rel)
    app=patch_special_app((SOURCE/'js/app.js').read_text(encoding='utf8'))
    active={'libs/xlsx.full.min.js':(SOURCE/'libs/xlsx.full.min.js').read_text(encoding='utf8'),'libs/exceljs.min.js':(SOURCE/'libs/exceljs.min.js').read_text(encoding='utf8'),'js/app.js':app}
    for rel,js in active.items():
        pat=re.compile(rf'<script\s+src=["\']{re.escape(rel)}["\']\s*>\s*</script>',re.I)
        html,n=pat.subn(lambda _m:f'<script data-v2-source="{rel}">\n{js}\n</script>',html,count=1)
        if n!=1: raise RuntimeError('active script marker missing '+rel)
    for rel in INERT_JS:
        b64=base64.b64encode((SOURCE/rel).read_bytes()).decode('ascii')
        inert=f'<script type="application/x-v2-original-source" data-path="{rel}" data-encoding="base64">{b64}</script>'
        pat=re.compile(rf'<script\s+src=["\']{re.escape(rel)}["\']\s*>\s*</script>',re.I)
        html,n=pat.subn(inert,html,count=1)
        if n!=1: raise RuntimeError('inert script marker missing '+rel)
    integration='''<style id="doV2SpecialIntegration">
/* DO V2.0 integration: one app / one account. Specialized business logic remains local. */
.cloud-toolbar,#cloudModal,#passwordResetModal,#loginHistoryModal,#projectHistoryModal{display:none!important}
.app-header{padding-right:12px}
.brand em{max-width:none}
body::before{content:"本地模块 · 账号由 DO V2.0 统一管理";position:fixed;right:12px;bottom:8px;z-index:9999;background:#eef4ff;color:#315fae;border:1px solid #c9d9f5;border-radius:999px;padding:4px 9px;font:11px Microsoft YaHei,Arial;pointer-events:none}
</style>'''
    html=html.replace('</head>','\n'+integration+'\n</head>',1)
    manifest='<script type="application/json" id="doV2SpecialSourceManifest">'+json.dumps(source_hashes,ensure_ascii=False)+'</script>'
    html=html.replace('</body>',manifest+'\n</body>',1)
    got=sha256_bytes(html.encode('utf8')); print('special generated sha',got,'len',len(html.encode('utf8')))
    if got!=TARGET_SPECIAL_SHA: raise RuntimeError('special exact hash mismatch: '+got)
    return html

def load_canvas():
    parts=[]
    for p in sorted(V20.glob('canvas_*.b64')): parts.append(p.read_text(encoding='utf8').strip())
    if not parts: raise RuntimeError('canvas payload missing')
    data=lzma.decompress(base64.b64decode(''.join(parts)))
    got=sha256_bytes(data); print('canvas sha',got,'len',len(data))
    if got!=TARGET_CANVAS_SHA: raise RuntimeError('canvas hash mismatch: '+got)
    return data.decode('utf8')

def load_outer_patch():
    b64=(V20/'outer_patch.xz.b64').read_text(encoding='utf8').strip()
    return json.loads(lzma.decompress(base64.b64decode(b64)).decode('utf8'))

def patch_outer(v1,special,canvas,supabase):
    v1=re.sub(r"const SPECIAL_FUSED_V141_B64='[^']*';","const SPECIAL_FUSED_V141_B64='__SPECIAL__';",v1)
    lines=v1.splitlines(); offset=0
    for op in load_outer_patch():
        a,b=op['a']+offset,op['b']+offset; old=op['old']; new=op['new']
        if lines[a:b]!=old: raise RuntimeError(f'outer patch mismatch {op["tag"]} {a}:{b}')
        if new==['__INSERT_SUPABASE__']:
            new=(f'<script id="doV2BundledSupabase" data-source="project-progress-manager/libs/supabase.min.js">\n{supabase}\n</script>').splitlines()
        lines[a:b]=new; offset+=len(new)-(b-a)
    out='\n'.join(lines)+'\n'
    out=out.replace("const SPECIAL_FUSED_V141_B64='__SPECIAL__';","const SPECIAL_FUSED_V141_B64='"+base64.b64encode(special.encode()).decode('ascii')+"';",1)
    out=out.replace("const BRAINSTORM_V113_B64='__BRAIN__';","const BRAINSTORM_V113_B64='"+base64.b64encode(canvas.encode()).decode('ascii')+"';",1)
    return out

def main():
    prepare(); download_special_source()
    v1=load_v111(); special=build_special(); canvas=load_canvas(); supabase=(SOURCE/'libs/supabase.min.js').read_text(encoding='utf8')
    final=patch_outer(v1,special,canvas,supabase)
    got=sha256_bytes(final.encode('utf8')); print('FINAL V2.0 SHA',got,'len',len(final.encode('utf8')))
    if got!=TARGET_SHA: raise RuntimeError('V2.0 exact hash mismatch: '+got)
    (SITE/'index.html').write_text(final,encoding='utf8')
    (SITE/'DO_进度管理_V2.0_聊天模式三模块融合.html').write_text(final,encoding='utf8')
    (SITE/'.nojekyll').write_text('',encoding='utf8')
    print('V2.0 chat restore verification passed')
if __name__=='__main__': main()
