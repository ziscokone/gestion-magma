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
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.pdf import ACCENT, BORDER, bandeau_entete, pied_de_page
from core.utils import format_fcfa, montant_en_lettres

FICHE_LARGEUR = 170 * mm

MENTION_LEGALE = "Ce document ne constitue pas une facture normalisée. Merci de votre confiance."


def _pied_de_page(styles):
    return pied_de_page(styles, mention=MENTION_LEGALE)


def _qr_code(data, taille=22 * mm):
    widget = QrCodeWidget(data)
    x1, y1, x2, y2 = widget.getBounds()
    largeur, hauteur = x2 - x1, y2 - y1
    dessin = Drawing(taille, taille, transform=[taille / largeur, 0, 0, taille / hauteur, 0, 0])
    dessin.add(widget)
    return dessin


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
    qr = _qr_code(qr_data, taille=20 * mm)
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

    elements.append(bandeau_entete(
        FICHE_LARGEUR,
        f"<b>REÇU N° {abonnement.numero_recu}</b><br/>Émis le {timezone.now():%d/%m/%Y}",
    ))
    elements.append(Spacer(1, 8 * mm))

    infos = Table(
        [[
            Paragraph(
                f"<b>CLIENT</b><br/>{abonnement.client.nom_complet}<br/>{abonnement.client.telephone}",
                styles['Normal'],
            ),
            Paragraph(
                f"<b>ABONNEMENT</b><br/>{abonnement.type_abonnement.nom}<br/>"
                f"Du {abonnement.date_debut:%d/%m/%Y} au {abonnement.date_fin:%d/%m/%Y}<br/>"
                f"Souscrit le {abonnement.date_souscription:%d/%m/%Y}",
                styles['Normal'],
            ),
        ]],
        colWidths=[FICHE_LARGEUR / 2, FICHE_LARGEUR / 2],
    )
    elements.append(infos)
    elements.append(Spacer(1, 8 * mm))

    montant_table = Table(
        [[f"MONTANT PAYÉ EN ESPÈCES : {format_fcfa(abonnement.montant)}"]],
        colWidths=[FICHE_LARGEUR],
    )
    montant_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eef2ff')),
        ('TEXTCOLOR', (0, 0), (-1, -1), ACCENT),
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
    elements.extend(_pied_de_page(styles))

    doc.build(elements)
    buffer.seek(0)
    return buffer
