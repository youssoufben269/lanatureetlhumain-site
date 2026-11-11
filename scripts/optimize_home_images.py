"""Extract existing homepage images; preserve subjects, logo bytes and credits."""
import base64
import io
import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def main():
    page = ROOT / 'index.html'
    html = page.read_text(encoding='utf-8')
    images = list(dict.fromkeys(re.findall(r'data:image/[^;]+;base64,[A-Za-z0-9+/=]+', html)))
    target = ROOT / 'assets'
    target.mkdir(exist_ok=True)
    photo_index = 0
    for uri in images:
        raw = base64.b64decode(uri.split(',', 1)[1])
        with Image.open(io.BytesIO(raw)) as image:
            if image.width == image.height:
                name = 'logo-officiel.jpg'
                (target / name).write_bytes(raw)
            else:
                photo_index += 1
                name = f'accueil-{photo_index}.webp'
                photo = image.convert('RGB')
                photo.thumbnail((1920, 1440), Image.Resampling.LANCZOS)
                photo.save(target / name, 'WEBP', quality=82, method=6)
        html = html.replace(uri, 'assets/' + name)
    page.write_text(html, encoding='utf-8', newline='\n')
    print(f'Accueil : {page.stat().st_size:,} octets ; {len(images)} images extraites.')


if __name__ == '__main__':
    main()
