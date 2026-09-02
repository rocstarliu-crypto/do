from pathlib import Path
import base64, gzip, lzma, re, shutil, tarfile, urllib.request

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / '_site'
TMP = ROOT / '.pages_tmp'
ARCHIVE = TMP / 'project-progress-manager.tar.gz'
SOURCE = TMP / 'project-progress-manager'
V111 = ROOT / 'release' / 'v1.11'
V201 = ROOT / 'release' / 'v2.0.1'

CSS_FILES = ['css/style.css','css/cloud.css','css/projects.css','css/password-reset.css','css/history.css','css/chart-align.css']
INERT_JS = ['libs/supabase.min.js','js/cloud-config.js','js/cloud.js']


def prepare_site():
    if SITE.exists(): shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    if TMP.exists(): shutil.rmtree(TMP)
    TMP.mkdir(parents=True)


def download_special():
    url='https://github.com/rocstarliu-crypto/project-progress-manager/archive/refs/heads/main.tar.gz'
    urllib.request.urlretrieve(url, ARCHIVE)
    SOURCE.mkdir()
    with tarfile.open(ARCHIVE,'r:gz') as tf:
        members=tf.getmembers(); prefix=members[0].name.split('/',1)[0]+'/'
        for m in members:
            if not m.name.startswith(prefix) or m.name==prefix.rstrip('/'): continue
            m.name=m.name[len(prefix):]
            tf.extract(m,SOURCE,filter='data')


def load_v111():
    chunks=sorted(V111.glob('*.b64'))
    if not chunks: raise RuntimeError('V1.11 payload missing')
    payload=''.join(p.read_text(encoding='utf-8').strip() for p in chunks)
    html=gzip.decompress(base64.b64decode(payload)).decode('utf-8')
    html=html.replace("const VERSION='V1.10-LIFECYCLE-PREVIEW';", "const VERSION='V1.11';")
    return html


def load_canvas():
    parts=[]
    for name in ['canvas_00.b64','canvas_01.b64']:
        p=V201/name
        if not p.exists(): raise RuntimeError(f'missing {name}')
        parts.append(p.read_text(encoding='utf-8').strip())
    return lzma.decompress(base64.b64decode(''.join(parts))).decode('utf-8')


def patch_special_app(s):
    s=s.replace("const WORKSPACE_STORAGE_KEY = 'project-progress-manager-v1.4.1-workspace';", "const WORKSPACE_STORAGE_KEY = 'do-v2-special-workspace';")
    s=re.sub(r"const PREVIOUS_WORKSPACE_STORAGE_KEYS = \[[^\n]*\];", "const PREVIOUS_WORKSPACE_STORAGE_KEYS = [];", s, count=1)
    s=re.sub(r"const LEGACY_STORAGE_KEY = '[^']*';", "const LEGACY_STORAGE_KEY = 'do-v2-special-legacy-unused';", s, count=1)
    pattern=r"function createDefaultWorkspace\(\) \{.*?\n\}\n\nfunction mergedWorkspaceColumns"
    replacement="""function createDefaultWorkspace() {
  const columns=defaultColumns();
  return {kind:WORKSPACE_KIND,version:2,appVersion:APP_VERSION,nextProjectId:2,activeProjectId:'project_1',columns:columns,projects:[
    {id:'project_1',name:'项目一',state:createEmptyState(columns)}
  ]};
}

function mergedWorkspaceColumns"""
    s,n=re.subn(pattern,replacement,s,count=1,flags=re.S)
    if n!=1: raise RuntimeError('special default workspace patch failed')
    return s


def build_special_fused():
    html=(SOURCE/'index.html').read_text(encoding='utf-8')
    app=patch_special_app((SOURCE/'js/app.js').read_text(encoding='utf-8'))
    for rel in CSS_FILES:
        css=(SOURCE/rel).read_text(encoding='utf-8')
        pat=re.compile(rf'<link\s+rel=["\']stylesheet["\']\s+href=["\']{re.escape(rel)}["\']\s*/?>', re.I)
        html,n=pat.subn(f'<style data-v2-source="{rel}">\n{css}\n</style>',html,count=1)
        if n!=1: raise RuntimeError(f'special CSS link not found: {rel}')
    active_map={
        'libs/xlsx.full.min.js':(SOURCE/'libs/xlsx.full.min.js').read_text(encoding='utf-8'),
        'libs/exceljs.min.js':(SOURCE/'libs/exceljs.min.js').read_text(encoding='utf-8'),
        'js/app.js':app,
    }
    for rel,js in active_map.items():
        pat=re.compile(rf'<script\s+src=["\']{re.escape(rel)}["\']\s*>\s*</script>',re.I)
        html,n=pat.subn(lambda m:f'<script data-v2-source="{rel}">\n{js}\n</script>',html,count=1)
        if n!=1: raise RuntimeError(f'special active script not found: {rel}')
    for rel in INERT_JS:
        b64=base64.b64encode((SOURCE/rel).read_bytes()).decode('ascii')
        inert=f'<script type="application/x-v2-original-source" data-path="{rel}" data-encoding="base64">{b64}</script>'
        pat=re.compile(rf'<script\s+src=["\']{re.escape(rel)}["\']\s*>\s*</script>',re.I)
        html,n=pat.subn(inert,html,count=1)
        if n!=1: raise RuntimeError(f'special inert script not found: {rel}')
    css='''<style data-v2-integration="special">
html,body,#app{height:100%!important;min-height:100%!important}body{margin:0!important;overflow:hidden!important}#app.app-shell{display:flex!important;flex-direction:column!important;height:100vh!important;min-height:720px!important}.workspace{flex:1 1 auto!important;min-height:420px!important;height:auto!important;overflow:hidden!important}.table-panel,.chart-panel,.table-scroll,.chart-scroll{min-height:0!important;height:100%!important}.project-tabs-bar,.statusbar{flex:0 0 auto!important}.cloud-toolbar,#cloudModal,#passwordResetModal,#loginHistoryModal,#projectHistoryModal{display:none!important}
</style>'''
    html=html.replace('</head>',css+'</head>',1)
    html=html.replace('<title>项目进度管理 V1.4.1</title>','<title>专项任务 V1.4.1</title>')
    return html


def patch_outer(html,special_html,canvas_html):
    html=html.replace("const VERSION='V1.11';", "const VERSION='V2.0.1';",1)
    html=html.replace('DO · 进度管理','DO 融合工作台',1)
    html=html.replace('DO 进度管理 V1.11 五视图统一修复版','DO 融合工作台 V2.0.1',2)
    html=html.replace('DO_进度管理_V1.11_网页批注.txt','DO_融合工作台_V2.0.1_网页批注.txt')
    html=html.replace('<h2>今明两天任务状态</h2>','<h2>今明两天四状态</h2>')

    special_b64=base64.b64encode(special_html.encode('utf-8')).decode('ascii')
    canvas_b64=base64.b64encode(canvas_html.encode('utf-8')).decode('ascii')
    a=html.find('async function specialBundleHTML(){'); b=html.find('\nfunction specialActiveProject()',a)
    if a<0 or b<0: raise RuntimeError('specialBundleHTML block missing')
    bundle=f'''const SPECIAL_FUSED_V141_B64='{special_b64}';
const BRAINSTORM_V113_B64='{canvas_b64}';
function decodeV2B64(v){{const bin=atob(v),buf=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)buf[i]=bin.charCodeAt(i);return new TextDecoder('utf-8').decode(buf)}}
function specialStorageKey(){{return 'do-v2-special-workspace:'+(outerCloudSession?.user?.id||accountScope||'guest')}}
function specialBundleHTML(){{return decodeV2B64(SPECIAL_FUSED_V141_B64).replaceAll('do-v2-special-workspace',specialStorageKey())}}
function brainstormBundleHTML(){{return decodeV2B64(BRAINSTORM_V113_B64)}}'''
    html=html[:a]+bundle+html[b:]

    a=html.find('function specialTasksHTML(){'); b=html.find('\n\nfunction dashboardTaskHTML',a)
    if a<0 or b<0: raise RuntimeError('special/brainstorm HTML block missing')
    clean='''function specialTasksHTML(){return `<section class="special-integrated-clean"><iframe id="specialFrame" class="special-fused-frame" title="专项任务"></iframe></section>`}
function brainstormHTML(){return `<section class="brainstorm-integrated"><iframe id="brainstormFrame" class="special-fused-frame" title="流程画布 V1.13"></iframe></section>`}'''
    html=html[:a]+clean+html[b:]

    a=html.find('function bindSpecial(){'); b=html.find('\nfunction openSpecialCloudProject()',a)
    if a<0 or b<0: raise RuntimeError('bindSpecial block missing')
    binds='''function bindSpecial(){const frame=document.getElementById('specialFrame');if(!frame)return;frame.onload=()=>{frame.dataset.ready='1';try{const z=(fontZones().special||15)/15;frame.contentDocument.body.style.zoom=String(Math.max(.8,Math.min(1.6,z)))}catch(e){}};try{frame.srcdoc=specialBundleHTML()}catch(e){console.error(e);frame.srcdoc='<main style="font-family:Microsoft YaHei,Arial;padding:28px"><h3>专项任务加载失败</h3><p>'+esc(String(e))+'</p></main>'}}
function bindBrainstorm(){const frame=document.getElementById('brainstormFrame');if(!frame)return;frame.onload=()=>{frame.dataset.ready='1'};try{frame.srcdoc=brainstormBundleHTML()}catch(e){console.error(e);frame.srcdoc='<main style="font-family:Microsoft YaHei,Arial;padding:28px"><h3>头脑风暴加载失败</h3><p>'+esc(String(e))+'</p></main>'}}'''
    html=html[:a]+binds+html[b:]
    html=html.replace("if(page==='special')bindSpecial();updateUndoButtons()", "if(page==='special')bindSpecial();if(page==='brainstorm')bindBrainstorm();updateUndoButtons()",1)

    old='<button id="annotationExport" title="下载 TXT 批注清单">⇩ 导出</button>'
    if old not in html: raise RuntimeError('annotation export button missing')
    html=html.replace(old,old+'<button id="annotationFeedback" title="把当前批注意见发送为反馈">✉ 反馈</button>',1)
    feedback=r'''
function annotationFeedbackPackage(){return annotationMessage()}
async function copyFeedbackPackage(){const txt=annotationFeedbackPackage();try{await navigator.clipboard.writeText(txt)}catch(e){const ta=document.createElement('textarea');ta.value=txt;document.body.appendChild(ta);ta.select();document.execCommand('copy');ta.remove()}return txt}
async function sendAnnotationEmail(){const txt=await copyFeedbackPackage(),subject='DO 融合工作台 V2.0.1 网页批注意见';const body=txt.length>5000?txt.slice(0,4800)+'\n\n【完整批注已自动复制到剪贴板，请粘贴到邮件正文】':txt;location.href='mailto:lp00102@hotmail.com?subject='+encodeURIComponent(subject)+'&body='+encodeURIComponent(body)}
async function sendAnnotationGithub(){const txt=await copyFeedbackPackage(),title='DO 融合工作台 V2.0.1 网页批注意见';const body=txt.length>7000?txt.slice(0,6800)+'\n\n【完整批注已复制到剪贴板，可继续粘贴补充】':txt;window.open('https://github.com/rocstarliu-crypto/do/issues/new?title='+encodeURIComponent(title)+'&body='+encodeURIComponent(body),'_blank','noopener')}
function openAnnotationFeedback(){openModal('反馈批注意见',`<div style="line-height:1.8;color:#526079"><p>系统会自动整理当前全部批注。</p><p><b>邮件反馈：</b>打开邮件客户端，收件人为 lp00102@hotmail.com。</p><p><b>GitHub反馈：</b>打开 do 仓库的新 Issue，标题和批注内容已预填。</p><p style="font-size:12px;color:#8893a5">为避免泄露账号密钥，静态网页不会保存邮箱密码或 GitHub Token。</p></div>`,`<button data-close>取消</button><button id="feedbackMail">邮件反馈</button><button class="primary" id="feedbackGithub">GitHub 反馈</button>`,'small');document.getElementById('feedbackMail').onclick=sendAnnotationEmail;document.getElementById('feedbackGithub').onclick=sendAnnotationGithub}
'''
    marker='function locateAnnotation(id){'; pos=html.find(marker)
    if pos<0: raise RuntimeError('annotation locate marker missing')
    html=html[:pos]+feedback+html[pos:]
    bind="document.getElementById('annotationExport').onclick=exportAnnotationText;"
    if bind not in html: raise RuntimeError('annotation export binding missing')
    html=html.replace(bind,bind+"\ndocument.getElementById('annotationFeedback').onclick=openAnnotationFeedback;",1)
    css='''<style data-v201-layout>
.workspace[data-page="special"],.workspace[data-page="brainstorm"]{padding:0!important;overflow:hidden!important}.special-integrated-clean,.brainstorm-integrated{width:100%;height:calc(100vh - 150px);min-height:720px;background:#fff;overflow:hidden}.special-integrated-clean .special-fused-frame,.brainstorm-integrated .special-fused-frame{width:100%;height:100%;min-height:720px;border:0;display:block;background:#fff}#annotationFeedback{font-weight:800}
</style>'''
    return html.replace('</head>',css+'</head>',1)


def verify(h):
    assert "const VERSION='V2.0.1'" in h
    assert 'data-page="board"' in h and '>四状态<' in h
    assert '◈ 开发档案' not in h and '>开发档案<' not in h
    assert '本地验收范围：' not in h
    assert '原“项目进度管理 V1.4.1”已融合为当前网站内部模块' not in h
    assert "fetch('./special/index.html'" not in h
    assert 'SPECIAL_FUSED_V141_B64=' in h and 'BRAINSTORM_V113_B64=' in h
    assert 'height:calc(100vh - 150px)' in h
    assert 'annotationFeedback' in h and 'lp00102@hotmail.com' in h
    assert 'github.com/rocstarliu-crypto/do/issues/new' in h
    for auth in ['signUp({email,password','signInWithPassword','resetPasswordForEmail']: assert auth in h
    for page in ['我的一天','计划内','全部任务','日程','四状态','工作日志','专项任务','头脑风暴']: assert page in h


def main():
    prepare_site();download_special()
    final=patch_outer(load_v111(),build_special_fused(),load_canvas());verify(final)
    (SITE/'index.html').write_text(final,encoding='utf-8')
    (SITE/'DO_融合工作台_V2.0.1.html').write_text(final,encoding='utf-8')
    (SITE/'.nojekyll').write_text('',encoding='utf-8')
    print('V2.0.1 build verification passed',len(final))

if __name__=='__main__': main()
