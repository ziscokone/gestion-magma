"""
QR code réutilisable entre les PDF (dessin vectoriel reportlab, pas de
rendu bitmap requis) et les aperçus HTML (data URI SVG) — pas de dépendance
supplémentaire (pas de lib `qrcode`, pas de rendu PNG qui nécessiterait
rlPyCairo, absent de l'environnement).
"""

import base64

from reportlab.graphics import renderSVG
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing


def qr_drawing(data, taille):
    """Widget QR code prêt à être dessiné sur un canvas/document reportlab
    (`taille` en points — 1 mm ≈ 2.83 pt)."""
    widget = QrCodeWidget(data)
    x1, y1, x2, y2 = widget.getBounds()
    largeur, hauteur = x2 - x1, y2 - y1
    dessin = Drawing(taille, taille, transform=[taille / largeur, 0, 0, taille / hauteur, 0, 0])
    dessin.add(widget)
    return dessin


def qr_code_data_uri(data, taille_px=180):
    """QR code encodé en data URI SVG, pour l'intégrer directement dans un
    <img> HTML (aperçu de la carte de membre) sans fichier ni endpoint dédié."""
    svg = renderSVG.drawToString(qr_drawing(data, taille_px))
    b64 = base64.b64encode(svg.encode('utf-8')).decode('ascii')
    return f'data:image/svg+xml;base64,{b64}'


def qr_code_image(data, taille_px=200):
    """QR code en image Pillow (RGB, fond blanc) — dessiné module par module
    à partir de la matrice reportlab, sans passer par un rasteriseur externe
    (renderPM nécessiterait rlPyCairo, absent de l'environnement)."""
    from PIL import Image

    widget = QrCodeWidget(data)
    widget.qr.make()
    nb_modules = widget.qr.getModuleCount()
    echelle = max(1, taille_px // nb_modules)
    taille_reelle = nb_modules * echelle

    image = Image.new('RGB', (taille_reelle, taille_reelle), 'white')
    pixels = image.load()
    for row in range(nb_modules):
        for col in range(nb_modules):
            if widget.qr.isDark(row, col):
                for dy in range(echelle):
                    for dx in range(echelle):
                        pixels[col * echelle + dx, row * echelle + dy] = (0, 0, 0)
    return image
