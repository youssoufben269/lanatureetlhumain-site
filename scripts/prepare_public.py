"""Create the Pages artifact from an explicit list, never the repository root."""
import shutil
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = ('index.html', 'CNAME', 'robots.txt', 'sitemap.xml',
         'adhesion/index.html', 'adhesion/confidentialite.html', 'adhesion/settings.json')
ASSET_TYPES = {'.css', '.js', '.mjs', '.png', '.jpg', '.webp'}
FORM_ASSETS = {'app.css', 'common.js', 'config.js', 'email.js', 'logo.png', 'privacy.js', 'public.js'}


def public_files(root=ROOT):
    for name in FILES:
        path = root / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f'Fichier public manquant ou lien non autorisé : {name}')
        yield path
    for folder in ('assets', 'adhesion/assets'):
        for path in sorted((root / folder).iterdir()):
            if path.is_symlink() or not path.is_file() or path.suffix not in ASSET_TYPES:
                raise ValueError(f'Ressource publique inattendue : {path.name}')
            if folder != 'adhesion/assets' or path.name in FORM_ASSETS:
                yield path


def main():
    settings = json.loads((ROOT / 'adhesion/settings.json').read_text(encoding='utf-8'))
    if not settings.get('emailRecipient'):
        raise ValueError('Renseigner l’adresse de réception des demandes avant publication.')
    output = ROOT / '.pages-build'
    output.mkdir(exist_ok=True)
    expected = set()
    for source in public_files():
        relative = source.relative_to(ROOT)
        expected.add(relative)
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    (output / 'adhesion/assets/config.js').write_text("window.LNH_API_BASE = '';\nwindow.LNH_MEMBERSHIP_MODE = 'email';\n", encoding='utf-8')
    actual = {path.relative_to(output) for path in output.rglob('*') if path.is_file()}
    if actual != expected:
        raise ValueError('Le dossier .pages-build contient des fichiers inattendus. Utiliser un dossier de compilation propre.')
    print(f'{len(expected)} fichiers publics préparés, aucune donnée privée copiée.')


if __name__ == '__main__':
    main()
