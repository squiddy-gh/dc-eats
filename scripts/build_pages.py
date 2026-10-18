"""Package the static map for GitHub Pages using the shared dining-guide configuration."""
import argparse
import json
from pathlib import Path
import shutil

PUBLIC_FILES = ('index.html', 'map.js', 'styles.css', 'vendor/leaflet.css', 'guides.json')


def build(source: Path, output: Path):
    source = source.resolve()
    if output.is_symlink():
        raise ValueError('Output must not be a symbolic link.')
    output = output.resolve()
    if output == source or source.is_relative_to(output):
        raise ValueError('Output must not contain the source repository.')
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError('Output must be a new or empty directory.')
    config = json.loads((source / 'guides.json').read_text(encoding='utf-8'))
    guides = config['sources']
    if not isinstance(guides, list) or not guides:
        raise ValueError('guides.json must contain a nonempty sources array.')
    ids = set()
    paths = []
    for guide in guides:
        guide_id, filename = guide['id'], guide['file']
        if guide_id in ids:
            raise ValueError(f'Duplicate guide id: {guide_id}')
        ids.add(guide_id)
        relative = Path(filename)
        if relative.is_absolute() or '..' in relative.parts or relative.suffix.lower() != '.csv' or relative.parts[0] != 'data':
            raise ValueError(f'Invalid guide CSV path: {filename}')
        paths.append(filename)
    names = (*PUBLIC_FILES, *paths)
    for name in names:
        path = source / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f'Missing or linked public file: {name}')
    output.mkdir(parents=True, exist_ok=True)
    for name in dict.fromkeys(names):
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, target)
    (output / '.nojekyll').write_text('', encoding='utf-8')
    print(f'Packaged {len(set(names))} public files and {len(guides)} guides into {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('_site'))
    args = parser.parse_args()
    try:
        build(Path(__file__).resolve().parents[1], args.output)
    except (ValueError, KeyError, json.JSONDecodeError, OSError) as error:
        parser.exit(1, f'{error}\n')
