"""
Génération du reçu PDF d'un abonnement : paiement unique, en espèces, à la
souscription.

Utilise reportlab (platypus) pour un rendu imprimable propre, avec la charte
graphique du projet (couleur d'accent) et quelques éléments de standing
(bandeau d'en-tête, montant en lettres, QR code d'authenticité, zone
signature/cachet).
"""

from io import BytesIO

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.fne.services import derniere_certification
from core.pdf import BORDER, ROW_ALT, bandeau_entete, get_couleur_principale, pied_de_page
from core.qr import qr_drawing
from core.utils import format_fcfa, montant_en_lettres

FICHE_LARGEUR = 170 * mm

MENTION_LEGALE = "Ce document ne constitue pas une facture normalisée. Merci de votre confiance."


def _pied_de_page(styles, certifie):
    """Mention légale de repli seulement si la facture n'est pas certifiée
    FNE — une facture certifiée porte déjà sa propre référence officielle
    (bandeau `_sticker_fne`), la mention "non normalisée" serait fausse."""
    return pied_de_page(styles, mention=None if certifie else MENTION_LEGALE)


def _sticker_fne(couleur, largeur, certification):
    """Bandeau de certification FNE (DGI) : QR de vérification officiel (le
    `token` renvoyé par la plateforme) + référence — n'apparaît que si la
    certification a réellement réussi, jamais deviné ou pré-affiché."""
    qr = qr_drawing(certification.token_verification, taille=16 * mm)
    texte = Paragraph(
        "<b>FACTURE NORMALISÉE ÉLECTRONIQUE</b><br/>"
        f"<font size=8>Certifiée DGI — Référence {certification.reference_fne}</font>",
        ParagraphStyle('fne_sticker_texte', fontName='Helvetica-Bold', fontSize=10.5,
                        textColor=colors.white, leading=13),
    )
    bloc = Table([[qr, texte]], colWidths=[22 * mm, largeur - 22 * mm])
    bloc.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), couleur),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, -1), 8),
        ('LEFTPADDING', (1, 0), (1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ]))
    return bloc


def _bloc_signature(largeur):
    demi = (largeur - 10 * mm) / 2
    table = Table(
        [['', '', ''], ['Le client', '', "Le/la responsable (cachet)"]],
        colWidths=[demi, 10 * mm, demi],
        rowHeights=[14 * mm, None],
    )
    table.setStyle(TableStyle([
        ('LINEABOVE', (0, 1), (0, 1), 0.75, colors.grey),
        ('LINEABOVE', (2, 1), (2, 1), 0.75, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 1), (-1, 1), 9),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.grey),
        ('TOPPADDING', (0, 1), (-1, 1), 4),
    ]))
    return table


def _pied_avec_qr(styles, largeur, qr_data):
    """Pied de page + zone signature/cachet + QR code d'authenticité, alignés sur une même ligne."""
    signature = _bloc_signature(largeur * 0.62)
    qr = qr_drawing(qr_data, taille=20 * mm)
    qr_legende = Paragraph(
        "Scanner pour<br/>vérifier ce document",
        ParagraphStyle('qr_legende', parent=styles['Normal'], alignment=TA_CENTER,
                        fontSize=7, textColor=colors.grey, leading=9),
    )
    bloc_qr = Table([[qr], [qr_legende]], colWidths=[largeur * 0.38])
    bloc_qr.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))

    ligne = Table([[signature, bloc_qr]], colWidths=[largeur * 0.62, largeur * 0.38])
    ligne.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'BOTTOM')]))
    return ligne


def _styles_bloc_info(couleur):
    """Hiérarchie typographique façon facture professionnelle : petit
    intitulé de section en couleur d'accent, valeur principale en gras plus
    grande, puis lignes secondaires grisées avec leur propre micro-légende."""
    return {
        'eyebrow': ParagraphStyle('bi_eyebrow', fontName='Helvetica-Bold', fontSize=8,
                                   textColor=couleur, leading=10, spaceAfter=5),
        'titre': ParagraphStyle('bi_titre', fontName='Helvetica-Bold', fontSize=12.5,
                                 textColor=colors.HexColor('#1a1a1a'), leading=15, spaceAfter=2),
        'meta': ParagraphStyle('bi_meta', fontName='Helvetica', fontSize=9.5,
                                textColor=colors.HexColor('#5a5a5a'), leading=13),
        'label': ParagraphStyle('bi_label', fontName='Helvetica-Bold', fontSize=7,
                                 textColor=colors.HexColor('#9a9a9a'), leading=9, spaceBefore=5),
    }


def _bloc_info(largeur, couleur, eyebrow, titre, lignes):
    """Une carte arrondie, liseré de couleur à gauche : intitulé de section,
    valeur principale, puis paires (micro-légende, valeur) optionnelles."""
    s = _styles_bloc_info(couleur)
    contenu = [Paragraph(eyebrow, s['eyebrow']), Paragraph(titre, s['titre'])]
    for label, valeur in lignes:
        if label:
            contenu.append(Paragraph(label, s['label']))
        contenu.append(Paragraph(valeur, s['meta']))

    carte = Table([[contenu]], colWidths=[largeur])
    carte.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), ROW_ALT),
        ('LINEBEFORE', (0, 0), (0, 0), 2.5, couleur),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ]))
    return carte


def _montant_en_lettres_bloc(styles, largeur, intro, montant):
    style = ParagraphStyle('lettres', parent=styles['Normal'], fontName='Helvetica-Oblique',
                            fontSize=9, textColor=colors.HexColor('#495057'), leading=13)
    texte = montant_en_lettres(montant)
    phrase = f"{intro} : <b>{texte[:1].upper()}{texte[1:]}</b>."
    bloc = Table([[Paragraph(phrase, style)]], colWidths=[largeur])
    bloc.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, -1), 0.5, BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    return bloc


def generer_fiche_abonnement_pdf(abonnement):
    """Reçu de l'abonnement : infos client/abonnement + montant payé en espèces."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=15 * mm, bottomMargin=15 * mm, leftMargin=20 * mm, rightMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    elements = []
    couleur_principale = get_couleur_principale()
    certification = derniere_certification(abonnement)
    certifie = certification is not None and certification.statut == 'succes'

    elements.append(bandeau_entete(
        FICHE_LARGEUR,
        f"<b>REÇU N° {abonnement.numero_recu}</b><br/>Émis le {timezone.now():%d/%m/%Y}",
    ))
    elements.append(Spacer(1, 6 * mm) if certifie else Spacer(1, 14 * mm))
    if certifie:
        elements.append(_sticker_fne(couleur_principale, FICHE_LARGEUR, certification))
        elements.append(Spacer(1, 8 * mm))

    largeur_carte = (FICHE_LARGEUR - 6 * mm) / 2
    carte_client = _bloc_info(
        largeur_carte, couleur_principale, 'CLIENT', abonnement.client.nom_complet,
        [(None, abonnement.client.telephone)],
    )
    carte_abonnement = _bloc_info(
        largeur_carte, couleur_principale, 'ABONNEMENT', abonnement.type_abonnement.nom,
        [
            ('PÉRIODE', f"{abonnement.date_debut:%d/%m/%Y} → {abonnement.date_fin:%d/%m/%Y}"),
            ('SOUSCRIT LE', f"{abonnement.date_souscription:%d/%m/%Y}"),
        ],
    )
    infos = Table([[carte_client, '', carte_abonnement]], colWidths=[largeur_carte, 6 * mm, largeur_carte])
    infos.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(infos)
    elements.append(Spacer(1, 8 * mm))

    montant_table = Table(
        [[f"MONTANT PAYÉ ({abonnement.mode_paiement_affiche.upper()}) : {format_fcfa(abonnement.montant)}"]],
        colWidths=[FICHE_LARGEUR],
    )
    montant_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eef2ff')),
        ('TEXTCOLOR', (0, 0), (-1, -1), couleur_principale),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(montant_table)
    elements.append(Spacer(1, 4 * mm))
    elements.append(_montant_en_lettres_bloc(
        styles, FICHE_LARGEUR, "Arrêté le présent reçu à la somme de", abonnement.montant,
    ))

    elements.append(Spacer(1, 14 * mm))
    elements.append(_pied_avec_qr(styles, FICHE_LARGEUR, f"MAGMA — Reçu abonnement N° {abonnement.numero_recu}"))
    elements.append(Spacer(1, 8 * mm))
    elements.extend(_pied_de_page(styles, certifie))

    doc.build(elements)
    buffer.seek(0)
    return buffer
