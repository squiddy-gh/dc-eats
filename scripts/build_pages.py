"""Package the static map for GitHub Pages, excluding research and cache files."""
import argparse
from pathlib import Path
import shutil

PUBLIC_FILES = (
    'index.html', 'map.js', 'styles.css', 'vendor/leaflet.css',
    'data/best_of_loudoun.csv',
    'data/washingtonian_best_cheap_eats_2026.csv',
    'data/washington_post_40_essential_dc_dishes_2026.csv',
    'data/michelin_dc_area_2026.csv',
)


def build(source: Path, output: Path):
    source = source.resolve()
    if output.is_symlink():
        raise ValueError('Output must not be a symbolic link.')
    output = output.resolve()
    if output == source or source.is_relative_to(output):
        raise ValueError('Output must not contain the source repository.')
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError('Output must be a new or empty directory.')
    for name in PUBLIC_FILES:
        path = source / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f'Missing or linked public file: {name}')
    output.mkdir(parents=True, exist_ok=True)
    for name in PUBLIC_FILES:
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, target)
    (output / '.nojekyll').write_text('', encoding='utf-8')
    print(f'Packaged {len(PUBLIC_FILES)} public files into {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('_site'))
    args = parser.parse_args()
    try:
        build(Path(__file__).resolve().parents[1], args.output)
    except ValueError as error:
        parser.exit(1, f'{error}\n')
