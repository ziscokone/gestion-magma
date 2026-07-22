"""PDF du module Stock : rapport d'inventaire et ticket de vente."""

from io import BytesIO

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from core.pdf import ACCENT, BORDER, ROW_ALT, badge_mode_paiement, bandeau_entete, pied_de_page
from core.utils import format_fcfa

LARGEUR = 170 * mm
TICKET_LARGEUR = 150 * mm


def generer_inventaire_pdf(produits, libelle_filtre):
    """`produits` : itérable de Produit déjà filtré/trié. `libelle_filtre` :
    texte affiché sous le titre pour rappeler le filtre actif (ex: « Stock épuisé »)."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=15 * mm, bottomMargin=15 * mm, leftMargin=20 * mm, rightMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    elements = []

    elements.append(bandeau_entete(
        LARGEUR,
        f"<b>INVENTAIRE DES PRODUITS</b><br/>Émis le {timezone.now():%d/%m/%Y à %H:%M}",
    ))
    elements.append(Spacer(1, 4 * mm))

    sous_titre_style = ParagraphStyle('sous_titre', parent=styles['Normal'], fontSize=9,
                                       textColor=colors.grey, spaceAfter=0)
    elements.append(Paragraph(f"Filtre : {libelle_filtre}", sous_titre_style))
    elements.append(Spacer(1, 6 * mm))

    header = ['Produit', 'Catégorie', 'Stock', 'Prix d\'achat', 'Valeur du stock']
    data = [header]
    valeur_totale = 0
    for produit in produits:
        valeur_totale += produit.valeur_stock
        data.append([
            produit.nom,
            produit.categorie.nom,
            f"{produit.stock_actuel} {produit.get_unite_display()}",
            format_fcfa(produit.prix_achat),
            format_fcfa(produit.valeur_stock),
        ])

    if len(data) == 1:
        data.append(['—', '—', '—', '—', '—'])

    table = Table(data, colWidths=[45 * mm, 35 * mm, 30 * mm, 30 * mm, 30 * mm], repeatRows=1)
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(('BACKGROUND', (0, i), (-1, i), ROW_ALT))
    table.setStyle(TableStyle(style))
    elements.append(table)
    elements.append(Spacer(1, 6 * mm))

    recap = Table(
        [[f"{len(produits)} produit{'s' if len(produits) != 1 else ''}", 'VALORISATION TOTALE', format_fcfa(valeur_totale)]],
        colWidths=[50 * mm, 70 * mm, 50 * mm],
    )
    recap.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eef2ff')),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.grey),
        ('TEXTCOLOR', (1, 0), (-1, 0), ACCENT),
        ('FONTNAME', (1, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 9),
        ('FONTSIZE', (1, 0), (-1, 0), 12),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (0, 0), 8),
        ('RIGHTPADDING', (-1, 0), (-1, 0), 8),
    ]))
    elements.append(recap)
    elements.append(Spacer(1, 6 * mm))
    elements.extend(pied_de_page(styles))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generer_ticket_vente_pdf(vente):
    """Ticket de caisse pour une vente — une ligne par produit du panier."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm, leftMargin=30 * mm, rightMargin=30 * mm,
    )
    styles = getSampleStyleSheet()
    elements = []

    elements.append(bandeau_entete(
        TICKET_LARGEUR,
        f"<b>TICKET DE VENTE</b><br/>Réf. {vente.numero_vente}",
    ))
    elements.append(Spacer(1, 10 * mm))

    elements.append(Paragraph(f"Vente du {vente.date:%d/%m/%Y à %H:%M}", styles['Normal']))
    elements.append(Spacer(1, 6 * mm))

    header = ['Produit', 'Quantité', 'Prix unitaire', 'Total']
    data = [header]
    for ligne in vente.lignes.select_related('produit').all():
        data.append([
            ligne.produit.nom,
            f"{ligne.quantite} {ligne.produit.get_unite_display()}",
            format_fcfa(ligne.prix_unitaire),
            format_fcfa(ligne.montant),
        ])

    table = Table(data, colWidths=[50 * mm, 35 * mm, 30 * mm, 35 * mm], repeatRows=1)
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(('BACKGROUND', (0, i), (-1, i), ROW_ALT))
    table.setStyle(TableStyle(style))
    elements.append(table)
    elements.append(Spacer(1, 6 * mm))

    montant_table = Table([[f"MONTANT TOTAL : {format_fcfa(vente.montant_total)}"]], colWidths=[TICKET_LARGEUR])
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
    elements.append(Spacer(1, 5 * mm))

    mode_paiement_ligne = Table(
        [[Paragraph("Mode de paiement", ParagraphStyle('mp', parent=styles['Normal'], fontSize=9,
                                                          textColor=colors.grey)),
          badge_mode_paiement(vente)]],
        colWidths=[TICKET_LARGEUR - 40 * mm, 40 * mm],
    )
    mode_paiement_ligne.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ALIGN', (1, 0), (1, 0), 'LEFT')]))
    elements.append(mode_paiement_ligne)
    elements.append(Spacer(1, 10 * mm))
    elements.extend(pied_de_page(styles, mention="Merci pour votre achat !"))

    doc.build(elements)
    buffer.seek(0)
    return buffer
