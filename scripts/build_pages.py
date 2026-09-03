from pathlib import Path
import base64
import gzip
import hashlib
import shutil

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / '_site'
R41_PAYLOAD = ROOT / 'release' / 'v2.3-r4.1' / 'full.b64'
R41_SHA256 = 'e590951c382d6f7d21a648c57a22e4126fdac6889bc631e94057ad5cb9e4126c'
V30_SHA256 = '27e2b20d965a80a130e2ab16b7c3a6158fd4f2a3579eb4c28415547d493f3d88'

V30_OVERRIDE = r'''/* ===== V3.0：仅删除“我的一天”右侧今明状态中的“归档”列 =====
   基线：DO_融合工作台_V2.3_R4.1_专项空间扩展_空白版_2026-09-03.html
   修改边界：只影响“我的一天”右侧今天/明天状态缩略视图；任务状态页五栏、生命周期、账号、专项、画布等全部保持原样。
*/
window.__DO_V3_0__={id:'DO_V3_0_MYDAY_NO_ARCHIVE_COLUMN_2026_09_03',base:'V2.3_R4.1',date:'2026-09-03'};
const V30_MYDAY_STATUS_STATES=['未开展','进行中','已完成','完成待优化'];
compactStatusDayHTML=function(date,label){
 const cls={'未开展':'notstarted','进行中':'doing','已完成':'done','完成待优化':'optimize'};
 const ids=new Set();V30_MYDAY_STATUS_STATES.forEach(st=>p1BoardItems(st,date).forEach(t=>ids.add(t.id)));
 return `<div class="status-day-card"><div class="status-day-head"><strong>${label}</strong><span class="status-total">共 ${ids.size} 项</span></div><div class="status-mini-grid">${V30_MYDAY_STATUS_STATES.map(st=>`<div class="status-mini ${cls[st]}" data-dash-status="${st}" data-dash-date="${date}" title="点击进入任务状态查看详情"><b>${st}</b><span class="n">${p1BoardItems(st,date).length}</span></div>`).join('')}</div></div>`;
};
const v30MyDayOnlyStyle=document.createElement('style');
v30MyDayOnlyStyle.id='do-v30-myday-no-archive-column';
v30MyDayOnlyStyle.textContent='.workspace[data-page="today"] .status-mini-grid{grid-template-columns:repeat(4,minmax(0,1fr))!important}';
document.head.appendChild(v30MyDayOnlyStyle);'''

STARTUP = "lifecycleMigrate();p35FinalMigrate();autoArchiveCompleted();scheduleMidnightArchive();normalizePastTasks();bumpVisit();render();updateSidebarCounts();if(location.protocol!=='file:'&&navigator.onLine)setTimeout(()=>initOuterCloud(),1200);"


def decode_r41(payload_text: str) -> str:
    raw = gzip.decompress(base64.b64decode(payload_text.strip()))
    sha = hashlib.sha256(raw).hexdigest()
    if sha != R41_SHA256:
        raise RuntimeError(f'R4.1 SHA mismatch: {sha}')
    return raw.decode('utf-8')


def make_v30(r41: str) -> str:
    old_title = '<title>DO 融合工作台 V2.3 · 阶段3-5 · 正式候选版</title>'
    new_title = '<title>DO 融合工作台 V3.0</title>'
    if r41.count(old_title) != 1:
        raise RuntimeError('R4.1 title marker mismatch')
    html = r41.replace(old_title, new_title, 1)
    if html.count(STARTUP) != 1:
        raise RuntimeError('R4.1 startup marker mismatch')
    html = html.replace(STARTUP, '\n\n' + V30_OVERRIDE + '\n\n' + STARTUP, 1)
    sha = hashlib.sha256(html.encode('utf-8')).hexdigest()
    if sha != V30_SHA256:
        raise RuntimeError(f'V3.0 SHA mismatch: {sha}')
    return html


def main():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    r41 = decode_r41(R41_PAYLOAD.read_text(encoding='utf-8'))
    v30 = make_v30(r41)
    (SITE / 'index.html').write_text(v30, encoding='utf-8')
    (SITE / 'DO_融合工作台_V3.0.html').write_text(v30, encoding='utf-8')
    (SITE / 'DO_融合工作台_V2.3_R4.1.html').write_text(r41, encoding='utf-8')
    (SITE / '.nojekyll').write_text('', encoding='utf-8')

    checks = [
        'DO 融合工作台 V3.0',
        "const V30_MYDAY_STATUS_STATES=['未开展','进行中','已完成','完成待优化'];",
        '.auth.signUp(',
        '.auth.resetPasswordForEmail(',
        'PASSWORD_RECOVERY',
        'updateUser({password})',
        'direct-source-shadow-root',
    ]
    for token in checks:
        if token not in v30:
            raise RuntimeError(f'missing required marker: {token}')
    print('DO 融合工作台 V3.0 Pages build verification passed')


if __name__ == '__main__':
    main()
