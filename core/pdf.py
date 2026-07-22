"""
Éléments PDF partagés entre les modules (bandeau d'en-tête et pied de page
aux couleurs de l'établissement), pour ne pas dupliquer ce code entre les
reçus d'abonnement et les rapports du module Stock.
"""

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, Spacer, Table, TableStyle

from apps.etablissement.models import Etablissement

ACCENT = colors.HexColor('#1e3260')
BORDER = colors.HexColor('#DEE2E6')
ROW_ALT = colors.HexColor('#FAFBFC')
BADGE_NEUTRE = colors.HexColor('#6c757d')


def bandeau_entete(largeur, titre_droite):
    """Bandeau plein cadre en couleur d'accent : logo + nom/slogan en blanc à
    gauche, référence du document en blanc à droite."""
    etablissement = Etablissement.get_instance()
    nom = etablissement.nom if etablissement else 'MAGMA'
    slogan = etablissement.slogan if etablissement and etablissement.slogan else ''

    largeur_logo = 18 * mm if (etablissement and etablissement.logo) else 0
    largeur_gauche = largeur * 0.58
    largeur_droite = largeur - largeur_gauche

    nom_style = ParagraphStyle('bandeau_nom', textColor=colors.white, fontSize=15,
                                fontName='Helvetica-Bold', leading=18)
    droite_style = ParagraphStyle('bandeau_droite', textColor=colors.white, fontSize=10,
                                   alignment=TA_RIGHT, leading=13)

    texte_nom = Paragraph(
        f"<b>{nom}</b>" + (f"<br/><font size=8 color='#c9d6ec'>{slogan}</font>" if slogan else ''),
        nom_style,
    )

    logo_cell = None
    if largeur_logo:
        try:
            logo_cell = Image(etablissement.logo.path, width=16 * mm, height=16 * mm, kind='proportional')
        except Exception:
            logo_cell = None

    if logo_cell:
        gauche = Table([[logo_cell, texte_nom]], colWidths=[largeur_logo, largeur_gauche - largeur_logo])
        gauche.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (0, 0), 0),
        ]))
    else:
        gauche = texte_nom

    bandeau = Table([[gauche, Paragraph(titre_droite, droite_style)]], colWidths=[largeur_gauche, largeur_droite])
    bandeau.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), ACCENT),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, -1), 12),
        ('RIGHTPADDING', (-1, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    return bandeau


def pied_de_page(styles, mention=None):
    etablissement = Etablissement.get_instance()
    lignes = [etablissement.nom if etablissement else 'MAGMA']
    if etablissement:
        if etablissement.adresse:
            lignes.append(etablissement.adresse)
        coord = ' — '.join(filter(None, [etablissement.telephone, etablissement.email]))
        if coord:
            lignes.append(coord)

    style = ParagraphStyle('footer', parent=styles['Normal'], alignment=TA_CENTER,
                            fontSize=8, textColor=colors.grey, leading=11)
    mention_style = ParagraphStyle('mention', parent=styles['Normal'], alignment=TA_CENTER,
                                    fontSize=7, textColor=colors.HexColor('#adb5bd'), leading=10)
    elements = [Paragraph('<br/>'.join(lignes), style)]
    if mention:
        elements.append(Spacer(1, 2 * mm))
        elements.append(Paragraph(mention, mention_style))
    return elements


def badge_mode_paiement(objet):
    """Petit badge coloré (même charte que les badges opérateur de l'app) —
    fonctionne pour tout objet héritant de `core.models.ModePaiementMixin`."""
    if objet.mode_paiement == 'mobile_money' and objet.operateur_mobile_money:
        bg = colors.HexColor(objet.operateur_couleur)
        fg = colors.black if objet.operateur_mobile_money == 'mtn' else colors.white
    else:
        bg = BADGE_NEUTRE
        fg = colors.white

    badge = Table([[objet.mode_paiement_affiche]])
    badge.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg),
        ('TEXTCOLOR', (0, 0), (-1, -1), fg),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ]))
    return badge
