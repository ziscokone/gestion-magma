"""
Génération des reçus PDF liés aux abonnements :
- fiche complète de l'abonnement (tout l'historique des versements)
- petit reçu individuel pour un versement précis

Utilise reportlab (platypus) pour un rendu imprimable propre, avec la charte
graphique du projet (couleur d'accent, couleurs de statut) et quelques
éléments de standing (bandeau d'en-tête, montant en lettres, QR code
d'authenticité, badges opérateur, zone signature/cachet).
"""

from io import BytesIO

from django.utils import timezone
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.pdf import ACCENT, BORDER, ROW_ALT, badge_mode_paiement, bandeau_entete, pied_de_page
from core.utils import format_fcfa, montant_en_lettres

SUCCESS_BG = colors.HexColor('#D4EDDA')
SUCCESS_TEXT = colors.HexColor('#155724')
WARNING_BG = colors.HexColor('#FFF3CD')
WARNING_TEXT = colors.HexColor('#856404')

FICHE_LARGEUR = 170 * mm
RECU_LARGEUR = 150 * mm

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


def _statut_paiement_bloc(abonnement, largeur):
    if abonnement.montant_restant > 0:
        texte = f"RESTE À PAYER : {format_fcfa(abonnement.montant_restant)}"
        bg, fg = WARNING_BG, WARNING_TEXT
    else:
        texte = "PAYÉ INTÉGRALEMENT"
        bg, fg = SUCCESS_BG, SUCCESS_TEXT

    table = Table([[texte]], colWidths=[largeur])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg),
        ('TEXTCOLOR', (0, 0), (-1, -1), fg),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 13),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    return table


def _table_versements(paiements, styles):
    header = ['Date', 'Montant', 'Mode de paiement']
    data = [header]
    if paiements:
        for p in paiements:
            data.append([p.date.strftime('%d/%m/%Y %H:%M'), format_fcfa(p.montant), badge_mode_paiement(p)])
    else:
        data.append(['—', '—', 'Aucun versement enregistré'])

    table = Table(data, colWidths=[45 * mm, 35 * mm, 90 * mm])
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(('BACKGROUND', (0, i), (-1, i), ROW_ALT))
    table.setStyle(TableStyle(style))
    return table


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
    """Fiche complète : infos client/abonnement + historique des versements + statut."""
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

    elements.append(Paragraph("<b>DÉTAIL DES VERSEMENTS</b>", styles['Normal']))
    elements.append(Spacer(1, 3 * mm))
    elements.append(_table_versements(list(abonnement.paiements.all()), styles))
    elements.append(Spacer(1, 6 * mm))

    recap = Table(
        [['Prix total', format_fcfa(abonnement.montant), 'Payé', format_fcfa(abonnement.montant_paye)]],
        colWidths=[35 * mm, 50 * mm, 35 * mm, 50 * mm],
    )
    recap.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
    ]))
    elements.append(recap)
    elements.append(Spacer(1, 4 * mm))
    elements.append(_statut_paiement_bloc(abonnement, FICHE_LARGEUR))
    elements.append(Spacer(1, 3 * mm))

    if abonnement.montant_paye > 0:
        elements.append(_montant_en_lettres_bloc(
            styles, FICHE_LARGEUR, "Soit la somme versée à ce jour de", abonnement.montant_paye,
        ))

    elements.append(Spacer(1, 14 * mm))
    elements.append(_pied_avec_qr(styles, FICHE_LARGEUR, f"MAGMA — Fiche abonnement N° {abonnement.numero_recu}"))
    elements.append(Spacer(1, 8 * mm))
    elements.extend(_pied_de_page(styles))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generer_recu_versement_pdf(paiement):
    """Petit reçu individuel pour un versement précis."""
    abonnement = paiement.abonnement
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm, leftMargin=30 * mm, rightMargin=30 * mm,
    )
    styles = getSampleStyleSheet()
    elements = []

    elements.append(bandeau_entete(
        RECU_LARGEUR,
        f"<b>REÇU DE VERSEMENT</b><br/>Réf. {paiement.numero_recu}",
    ))
    elements.append(Spacer(1, 10 * mm))

    elements.append(Paragraph(
        f"Client : <b>{abonnement.client.nom_complet}</b><br/>"
        f"Abonnement : {abonnement.type_abonnement.nom}<br/>"
        f"Versement du {paiement.date:%d/%m/%Y à %H:%M}",
        styles['Normal'],
    ))
    elements.append(Spacer(1, 8 * mm))

    montant_table = Table(
        [[f"MONTANT VERSÉ : {format_fcfa(paiement.montant)}"]],
        colWidths=[RECU_LARGEUR],
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
        styles, RECU_LARGEUR, "Arrêté le présent reçu à la somme de", paiement.montant,
    ))
    elements.append(Spacer(1, 5 * mm))

    mode_paiement_ligne = Table(
        [[Paragraph("Mode de paiement", ParagraphStyle('mp', parent=styles['Normal'], fontSize=9,
                                                          textColor=colors.grey)),
          badge_mode_paiement(paiement)]],
        colWidths=[RECU_LARGEUR - 40 * mm, 40 * mm],
    )
    mode_paiement_ligne.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ALIGN', (1, 0), (1, 0), 'LEFT')]))
    elements.append(mode_paiement_ligne)
    elements.append(Spacer(1, 8 * mm))

    recap = Table(
        [['Total payé à ce jour', format_fcfa(abonnement.montant_paye)],
         ['Reste à payer', format_fcfa(abonnement.montant_restant)]],
        colWidths=[RECU_LARGEUR / 2, RECU_LARGEUR / 2],
    )
    recap.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(recap)
    elements.append(Spacer(1, 16 * mm))
    elements.append(_pied_avec_qr(styles, RECU_LARGEUR, f"MAGMA — Reçu N° {paiement.numero_recu}"))
    elements.append(Spacer(1, 8 * mm))
    elements.extend(_pied_de_page(styles))

    doc.build(elements)
    buffer.seek(0)
    return buffer
