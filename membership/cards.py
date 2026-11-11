"""ID-1 template. Replace this layout when the approved card artwork is supplied."""
import io
import os
from pathlib import Path

import reportlab
from PIL import Image, ImageOps
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import mm

WIDTH, HEIGHT = 85.60 * mm, 53.98 * mm
SLOGAN = 'RÉSEAUX · PARTENARIATS · SOLUTIONS'
DEEP, GREEN = HexColor('#075889'), HexColor('#4b9824')

fonts = Path(reportlab.__file__).parent / 'fonts'
for name, filename in (('LNH', 'Vera.ttf'), ('LNH-Bold', 'VeraBd.ttf'), ('LNH-Italic', 'VeraIt.ttf')):
    if name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(name, str(fonts / filename)))


def lines(text, font, size, width):
    result, line = [], ''
    for word in text.split():
        candidate = (line + ' ' + word).strip()
        if pdfmetrics.stringWidth(candidate, font, size) <= width:
            line = candidate
        else:
            if line:
                result.append(line)
            line = ''
            for char in word:
                if pdfmetrics.stringWidth(line + char, font, size) > width:
                    result.append(line)
                    line = ''
                line += char
    if line:
        result.append(line)
    return result


def fit_text(text, width, size=9, max_lines=3, font='LNH'):
    while size > 5.5 and len(lines(text, font, size, width)) > max_lines:
        size -= .25
    wrapped = lines(text, font, size, width)
    if len(wrapped) > max_lines:
        raise ValueError('Texte trop long pour la carte.')
    return size, wrapped


def validate_card_text(member):
    fit_text(member['first_name'] + ' ' + member['last_name'], WIDTH - 80, 9.2, 3, 'LNH-Bold')
    if not os.environ.get('LNH_SIGNATURE_PATH'):
        fit_text(member['first_name'] + ' ' + member['last_name'], 140, 8.5, 2, 'LNH-Italic')
    fit_text(member.get('function', ''), WIDTH - 80, 7.1, 2)
    if pdfmetrics.stringWidth(member['category'].upper(), 'LNH', 5.5) > WIDTH - 123:
        raise ValueError('Catégorie trop longue pour la carte.')


def block(c, text, x, y, width, size=9, max_lines=3, font='LNH'):
    size, wrapped = fit_text(text, width, size, max_lines, font)
    c.setFont(font, size)
    for index, line in enumerate(wrapped):
        c.drawString(x, y - index * (size + 2), line)


def make_card(member, settings, output):
    validate_card_text(member)
    logo = settings.root / 'adhesion' / 'assets' / 'logo.png'
    if not logo.is_file():
        raise ValueError('Logo officiel manquant.')
    tmp = output.with_suffix('.tmp')
    try:
        c = Canvas(str(tmp), pagesize=(WIDTH, HEIGHT), pageCompression=1)
        c.setTitle('Carte de membre ' + member['member_number'])
        c.setAuthor('La Nature et l’Humain')
        c.setSubject('ID-1 85,60 × 53,98 mm - recto puis verso - impression à 100 %')
        c.setFillColor(white)
        c.rect(0, 0, WIDTH, HEIGHT, fill=1, stroke=0)
        c.drawImage(str(logo), 10, HEIGHT - 39, 31, 31, preserveAspectRatio=True, anchor='c', mask='auto')
        c.setFillColor(DEEP)
        c.setFont('LNH', 9.2)
        c.drawString(47, HEIGHT - 21, 'La Nature et l’Humain')
        c.setFont('LNH', 5.4)
        c.drawString(47, HEIGHT - 33, SLOGAN)
        c.setFillColor(DEEP)
        c.rect(0, HEIGHT - 56, WIDTH, 13, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont('LNH', 6.7)
        c.drawString(12, HEIGHT - 52, 'CARTE DE MEMBRE')
        c.setFont('LNH', 5.5)
        c.drawRightString(WIDTH - 12, HEIGHT - 52, member['category'].upper())
        with Image.open(settings.data / member['photo_path']) as image:
            crop = ImageOps.fit(image, (450, 600), method=Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            crop.save(buffer, 'PNG')
            c.drawImage(ImageReader(buffer), 12, 24, 45, 60)
        c.setFillColor(HexColor('#151515'))
        fullname = member['first_name'] + ' ' + member['last_name']
        block(c, fullname, 68, 84, WIDTH - 80, 9.2, 3, 'LNH-Bold')
        c.setFillColor(DEEP)
        block(c, member['function'], 68, 47, WIDTH - 80, 7.1, 2)
        c.setFillColor(GREEN)
        c.rect(12, 11, 45, 2, fill=1, stroke=0)
        c.setFillColor(DEEP)
        c.setFont('LNH-Bold', 9)
        c.drawString(68, 16, member['member_number'])
        c.showPage()

        c.setFillColor(DEEP)
        c.rect(0, HEIGHT - 34, WIDTH, 34, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont('LNH', 9)
        c.drawString(12, HEIGHT - 16, 'La Nature et l’Humain')
        c.setFont('LNH', 5.6)
        c.drawString(12, HEIGHT - 27, SLOGAN)
        c.setFillColor(HexColor('#62625e'))
        for title, value, y in (
            ('DATE D’ADHÉSION', member['joined_on'], 101),
            ('VALABLE JUSQU’AU', member['expires_on'], 73)):
            c.setFont('LNH', 5.6)
            c.drawString(12, y, title)
            c.setFont('LNH-Bold', 8.5)
            c.drawString(12, y - 12, '.'.join(reversed(value.split('-'))))

        target = settings.website + '/' if settings.qr_mode == 'website' else settings.origin + '/membre/' + member['member_number']
        widget = QrCodeWidget(target, barLevel='M', barBorder=4)
        x1, y1, x2, y2 = widget.getBounds()
        side = 58
        drawing = Drawing(side, side, transform=[side / (x2 - x1), 0, 0, side / (y2 - y1), 0, 0])
        drawing.add(widget)
        renderPDF.draw(drawing, c, WIDTH - 72, 49)
        c.setFont('LNH', 5.3)
        c.drawCentredString(WIDTH - 43, 43, 'Site de l’association' if settings.qr_mode == 'website' else 'Vérifier la carte')
        signature = os.environ.get('LNH_SIGNATURE_PATH', '')
        if signature:
            c.drawImage(signature, 12, 30, 98, 22, preserveAspectRatio=True, mask='auto')
            label = 'Signature autorisée de l’association'
        else:
            block(c, fullname, 12, 37, 140, 8.5, 2, 'LNH-Italic')
            label = 'Signature du membre (simulée)'
        c.setFont('LNH', 4.8)
        c.drawString(12, 16, label)
        c.setFillColor(DEEP)
        c.setFont('LNH', 4.9)
        c.drawRightString(WIDTH - 12, 16, 'Carte personnelle · usage associatif')
        c.save()
        tmp.replace(output)
    finally:
        tmp.unlink(missing_ok=True)
