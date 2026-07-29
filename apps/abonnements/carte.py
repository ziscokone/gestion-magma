"""
Carte de membre au format image (PNG) — pensée pour être présentée
directement à l'écran du téléphone à l'entrée de la salle et scannée, sans
passer par un lecteur PDF. Même design que l'aperçu HTML de la fiche
abonnement, dessiné avec Pillow (déjà une dépendance du projet).

Utilise les polices DejaVu Sans embarquées dans static/fonts/ plutôt que
des polices système, pour un rendu identique quel que soit le serveur de
déploiement (et un vrai support des caractères accentués français).
"""

from io import BytesIO
from pathlib import Path

from django.conf import settings
from PIL import Image, ImageDraw, ImageFont

from apps.etablissement.models import Etablissement
from core.qr import qr_code_image

FONT_DIR = Path(settings.BASE_DIR) / 'static' / 'fonts'
FONT_BOLD = FONT_DIR / 'DejaVuSans-Bold.ttf'
FONT_REGULAR = FONT_DIR / 'DejaVuSans.ttf'

LARGEUR, HAUTEUR = 1000, 630
MARGE = 50
RAYON = 34


def _police(taille, gras=False):
    return ImageFont.truetype(str(FONT_BOLD if gras else FONT_REGULAR), taille)


def _texte_centre(draw, texte, font, cx, cy, fill):
    x0, y0, x1, y1 = draw.textbbox((0, 0), texte, font=font)
    largeur, hauteur = x1 - x0, y1 - y0
    draw.text((cx - largeur / 2 - x0, cy - hauteur / 2 - y0), texte, font=font, fill=fill)


def generer_carte_abonnement_png(abonnement):
    """Retourne un buffer PNG (85.6:53.98, ratio carte ID-1) prêt à être
    envoyé en réponse HTTP ou partagé tel quel."""
    etablissement = Etablissement.get_instance()
    nom_etab = etablissement.nom if etablissement else 'MAGMA FITNESS'
    couleur_principale = etablissement.couleur_principale if etablissement and etablissement.couleur_principale else '#386745'
    couleur_accent = etablissement.couleur_accent if etablissement and etablissement.couleur_accent else '#F46722'
    couleur_secondaire = etablissement.couleur_secondaire if etablissement and etablissement.couleur_secondaire else '#FDF7E5'

    actif = abonnement.statut == 'actif'
    statut_libelle = 'ACTIF' if actif else 'EXPIRÉ'
    statut_bg = '#eafaf0' if actif else '#fdecea'
    statut_texte = '#2a6b45' if actif else '#a83a32'

    image = Image.new('RGB', (LARGEUR, HAUTEUR), couleur_principale)
    draw = ImageDraw.Draw(image)

    # Bandeau décoratif "lave" en bas à droite, écho du pictogramme volcan
    draw.polygon(
        [(LARGEUR, HAUTEUR), (LARGEUR - 0.304 * LARGEUR, HAUTEUR), (LARGEUR, HAUTEUR - 0.482 * HAUTEUR)],
        fill=couleur_accent,
    )

    # Logo + nom de l'établissement
    texte_x = MARGE
    if etablissement and etablissement.logo:
        try:
            logo = Image.open(etablissement.logo.path).convert('RGBA')
            logo.thumbnail((90, 90))
            image.paste(logo, (MARGE, MARGE), logo)
            texte_x = MARGE + 90 + 18
        except Exception:
            pass

    draw.text((texte_x, MARGE), nom_etab, font=_police(40, gras=True), fill='white')
    draw.text((texte_x, MARGE + 54), 'CARTE DE MEMBRE', font=_police(20), fill=couleur_secondaire)

    # Pastille de statut (haut droit)
    pill_w, pill_h = 210, 62
    px0, py0 = LARGEUR - MARGE - pill_w, MARGE
    draw.rounded_rectangle((px0, py0, px0 + pill_w, py0 + pill_h), radius=31, fill=statut_bg)
    _texte_centre(draw, statut_libelle, _police(28, gras=True), px0 + pill_w / 2, py0 + pill_h / 2, statut_texte)

    # Identité du client
    nom_client = abonnement.client.nom_complet
    if len(nom_client) > 28:
        nom_client = nom_client[:27] + '…'
    y = 230
    draw.text((MARGE, y), nom_client, font=_police(52, gras=True), fill='white')
    y += 74
    draw.text((MARGE, y), abonnement.client.telephone, font=_police(28), fill=couleur_secondaire)
    y += 64
    draw.text((MARGE, y), abonnement.type_abonnement.nom, font=_police(32, gras=True), fill='white')
    y += 48
    periode = f"Valable du {abonnement.date_debut:%d/%m/%Y} au {abonnement.date_fin:%d/%m/%Y}"
    draw.text((MARGE, y), periode, font=_police(24), fill=couleur_secondaire)

    # QR de vérification, sur fond blanc pour un scan fiable
    qr_img = qr_code_image(abonnement.texte_carte_membre, taille_px=190)
    qx = LARGEUR - MARGE - qr_img.width
    qy = HAUTEUR - MARGE - qr_img.height
    pad = 14
    draw.rounded_rectangle(
        (qx - pad, qy - pad, qx + qr_img.width + pad, qy + qr_img.height + pad), radius=18, fill='white',
    )
    image.paste(qr_img, (qx, qy))

    # Coins arrondis : masque appliqué en dernier, quel que soit ce qui a été dessiné dessus/dessous
    masque = Image.new('L', (LARGEUR, HAUTEUR), 0)
    ImageDraw.Draw(masque).rounded_rectangle((0, 0, LARGEUR, HAUTEUR), radius=RAYON, fill=255)
    image_rgba = image.convert('RGBA')
    image_rgba.putalpha(masque)

    buffer = BytesIO()
    image_rgba.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer
