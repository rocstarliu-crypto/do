from pathlib import Path
import hashlib
import shutil

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / '_site'
BASE = ROOT / 'app-v343-base.html'
EXPECTED_SHA256 = 'b68a3e463f3d0610bbdd3dad15472cf38f46dd403cc3ab6bf809da87e79a6eda'


def replace_one(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 marker, got {count}')
    return text.replace(old, new, 1)


def make_v344(text):
    text = text.replace('V3.4.3', 'V3.4.4').replace('头脑风暴', '思维导图/流程图')
    text = replace_one(text,
        '<option value="flow">标准流程</option><option value="org">上下组织结构</option><option value="water">水平衡分流</option><option value="material">物料平衡汇流</option>',
        '<option value="flow">标准流程</option><option value="org">上下组织结构</option><option value="orgUnit">单位组织架构（思维导图）</option><option value="water">水平衡分流</option><option value="material">物料平衡汇流</option>',
        'template option')
    text = replace_one(text,
        "if(type==='org'){state.settings.layoutDir='TB';",
        "if(type==='orgUnit'){state.settings.layoutDir='TB';state.settings.mode='mind';const unit=make('单位名称'),leader=make('负责人',unit.id),a=make('综合管理部',leader.id),b=make('财务部',leader.id),c=make('技术部',leader.id),d=make('生产部',leader.id),e=make('安全环保部',leader.id);make('行政/人事',a.id);make('后勤/档案',a.id);make('财务管理',b.id);make('成本/核算',b.id);make('技术管理',c.id);make('研发/工艺',c.id);make('生产车间1',d.id);make('生产车间2',d.id);make('安全管理',e.id);make('环保管理',e.id)}else if(type==='org'){state.settings.layoutDir='TB';",
        'org unit template')
    text = replace_one(text,
        "type==='org'?'上下组织结构':type==='material'?'物料平衡汇流':type==='water'?'水平衡分流':'标准流程'",
        "type==='orgUnit'?'单位组织架构（思维导图）':type==='org'?'上下组织结构':type==='material'?'物料平衡汇流':type==='water'?'水平衡分流':'标准流程'",
        'template toast')
    text = replace_one(text,
        "$('#layoutDir').value=state.settings.layoutDir;fitAll()}",
        "$('#layoutDir').value=state.settings.layoutDir;$('#canvasMode').value=state.settings.mode||'flow';fitAll()}",
        'template display mode')
    text = replace_one(text,
        ",s=JSON.parse(raw||'null');if(s?.nodes?.length){",
        ",s=JSON.parse(raw||'null'),builtInExample=s?.nodes?.length===4&&['A 总用水','B1 生产用水','B2 辅助用水','C 废水去向'].every(t=>s.nodes.some(n=>n.text===t));if(s?.nodes?.length&&!builtInExample){",
        'blank default detection')
    text = replace_one(text,
        "}else loadExample(false)}catch{loadExample(false)}selectedNode=state.nodes.find(n=>n.text==='B1 生产用水')?.id||state.nodes[0]?.id||null;",
        "}else{state.nodes=[];state.edges=[];selectedNode=null;persist()}}catch{state.nodes=[];state.edges=[];selectedNode=null;persist()}selectedNode=state.nodes[0]?.id||null;",
        'blank default reset')
    return text


def main():
    if not BASE.exists():
        raise RuntimeError('missing V3.4.3 full base file')
    html = make_v344(BASE.read_text(encoding='utf-8'))
    sha = hashlib.sha256(html.encode('utf-8')).hexdigest()
    if sha != EXPECTED_SHA256:
        raise RuntimeError(f'V3.4.4 SHA mismatch: {sha}')

    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    (SITE / 'index.html').write_text(html, encoding='utf-8')
    (SITE / '.nojekyll').write_text('', encoding='utf-8')
    print('DO 融合工作台 V3.4.4 full single-file Pages build passed')


if __name__ == '__main__':
    main()
