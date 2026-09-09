from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / '_site'
SOURCE = ROOT / 'index.html'


def main():
    if not SOURCE.exists():
        raise RuntimeError('missing root index.html')
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    shutil.copy2(SOURCE, SITE / 'index.html')
    (SITE / '.nojekyll').write_text('', encoding='utf-8')
    print('GitHub Pages: publish root index.html directly')


if __name__ == '__main__':
    main()
