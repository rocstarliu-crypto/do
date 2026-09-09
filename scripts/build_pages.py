from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / '_site'

FILES = [
    ('index.html', 'index.html'),
    ('app-v343-base.html', 'app-v343-base.html'),
    ('assets/ui-name-patch-v343.js', 'assets/ui-name-patch-v343.js'),
]


def main():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)

    for src_rel, dst_rel in FILES:
        src = ROOT / src_rel
        dst = SITE / dst_rel
        if not src.exists():
            raise RuntimeError(f'missing publish file: {src_rel}')
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    nojekyll = ROOT / '.nojekyll'
    if nojekyll.exists():
        shutil.copy2(nojekyll, SITE / '.nojekyll')
    else:
        (SITE / '.nojekyll').write_text('', encoding='utf-8')

    loader = (ROOT / 'index.html').read_text(encoding='utf-8')
    base = (ROOT / 'app-v343-base.html').read_text(encoding='utf-8')
    patch = (ROOT / 'assets/ui-name-patch-v343.js').read_text(encoding='utf-8')

    if 'app-v343-base.html' not in loader or 'ui-name-patch-v343.js' not in loader:
        raise RuntimeError('V3.4.3 loader marker missing')
    if '<title>DO 融合工作台 V3.4.3</title>' not in base:
        raise RuntimeError('V3.4.3 base marker missing')
    if "const OLD='头脑风暴', NEW='思维导图/流程图';" not in patch:
        raise RuntimeError('module display-name patch marker missing')

    print('DO 融合工作台 V3.4.3 Pages build verification passed')


if __name__ == '__main__':
    main()
