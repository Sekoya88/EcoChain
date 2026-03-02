#!/usr/bin/env python3
"""EcoChain AI — Generate realistic logistics PDF test documents.

Creates 5 professional PDF documents (invoices + delivery notes) in data/pdfs/
with varied routes, transport modes, weights, and distances.
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


# ── Color palette ────────────────────────────────────────
DARK_BG = colors.HexColor("#1a1d26")
ACCENT = colors.HexColor("#10b981")
ACCENT_DARK = colors.HexColor("#059669")
TEXT_DARK = colors.HexColor("#1f2937")
TEXT_MUTED = colors.HexColor("#6b7280")
BORDER = colors.HexColor("#d1d5db")
HEADER_BG = colors.HexColor("#f0fdf4")
ROW_ALT = colors.HexColor("#f9fafb")

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "pdfs"

# ── Document data ────────────────────────────────────────
DOCUMENTS = [
    {
        "type": "invoice",
        "filename": "invoice_eco_001.pdf",
        "json_filename": "invoice_eco_001.json",
        "doc_number": "INV-2024-EC-0147",
        "date": "2024-06-15",
        "shipper": {"name": "Europarts Manufacturing GmbH", "address": "Industriestraße 42, 70173 Stuttgart, Germany", "vat": "DE 283 746 192"},
        "receiver": {"name": "Mediterranean Auto Components SRL", "address": "Via della Meccanica 8, 10135 Torino, Italy", "vat": "IT 09384756201"},
        "origin": "Stuttgart",
        "destination": "Torino",
        "goods": "Composants de transmission automobile (arbres à cames, roulements)",
        "quantity": 480,
        "unit_weight_kg": 2.5,
        "total_weight_kg": 1200.0,
        "volume_m3": 4.2,
        "transport_mode": "road",
        "distance_km": 620.0,
        "departure_date": "2024-06-15",
        "arrival_date": "2024-06-16",
        "unit_price": 45.00,
        "total_cost": 21600.00,
        "currency": "EUR",
        "incoterms": "DAP",
        "carrier": "Schenker DB AG",
        "tracking": "SCH-2024-884712",
    },
    {
        "type": "delivery_note",
        "filename": "delivery_note_eco_002.pdf",
        "json_filename": "delivery_note_eco_002.json",
        "doc_number": "DN-2024-EC-0298",
        "date": "2024-07-22",
        "shipper": {"name": "Atlantic Seafood Processing SA", "address": "Zone Portuaire Sud, 44600 Saint-Nazaire, France", "vat": "FR 82 493 028 715"},
        "receiver": {"name": "Nordic Fresh Distribution AB", "address": "Fiskhamnen 12, 414 58 Göteborg, Sweden", "vat": "SE 556012-3456"},
        "origin": "Saint-Nazaire",
        "destination": "Göteborg",
        "goods": "Produits de la mer surgelés (cabillaud, crevettes, saumon fumé)",
        "quantity": 120,
        "unit_weight_kg": 25.0,
        "total_weight_kg": 3000.0,
        "volume_m3": 8.5,
        "transport_mode": "maritime",
        "distance_km": 2800.0,
        "departure_date": "2024-07-22",
        "arrival_date": "2024-07-28",
        "unit_price": 180.00,
        "total_cost": 21600.00,
        "currency": "EUR",
        "incoterms": "CIF",
        "carrier": "CMA CGM Group",
        "tracking": "CMAU-2024-7741902",
    },
    {
        "type": "invoice",
        "filename": "invoice_eco_003.pdf",
        "json_filename": "invoice_eco_003.json",
        "doc_number": "INV-2024-EC-0562",
        "date": "2024-08-10",
        "shipper": {"name": "Shenzhen MicroElec Co. Ltd", "address": "Building 7, Nanshan Hi-Tech Park, Shenzhen 518057, China", "vat": "CN 91440300MA5G4XYZ01"},
        "receiver": {"name": "TechnoDistrib SAS", "address": "ZAC des Hauts de Bièvre, 91940 Les Ulis, France", "vat": "FR 47 912 345 678"},
        "origin": "Shenzhen",
        "destination": "Paris CDG",
        "goods": "Semiconducteurs et composants électroniques (FPGA, DRAM modules)",
        "quantity": 5000,
        "unit_weight_kg": 0.05,
        "total_weight_kg": 250.0,
        "volume_m3": 1.8,
        "transport_mode": "air",
        "distance_km": 9500.0,
        "departure_date": "2024-08-10",
        "arrival_date": "2024-08-12",
        "unit_price": 22.50,
        "total_cost": 112500.00,
        "currency": "USD",
        "incoterms": "FCA",
        "carrier": "Air France Cargo",
        "tracking": "AF-CARGO-2024-88341",
    },
    {
        "type": "delivery_note",
        "filename": "delivery_note_eco_004.pdf",
        "json_filename": "delivery_note_eco_004.json",
        "doc_number": "DN-2024-EC-0731",
        "date": "2024-09-05",
        "shipper": {"name": "Baltic Timber Industries OÜ", "address": "Pärnu mnt 158, 11317 Tallinn, Estonia", "vat": "EE 100 456 789"},
        "receiver": {"name": "RheinBau Holzwerke GmbH", "address": "Am Güterbahnhof 3, 47059 Duisburg, Germany", "vat": "DE 119 345 678"},
        "origin": "Tallinn",
        "destination": "Duisburg",
        "goods": "Bois de construction certification PEFC (poutres lamellé-collé, OSB)",
        "quantity": 45,
        "unit_weight_kg": 800.0,
        "total_weight_kg": 36000.0,
        "volume_m3": 95.0,
        "transport_mode": "rail",
        "distance_km": 1850.0,
        "departure_date": "2024-09-05",
        "arrival_date": "2024-09-09",
        "unit_price": 320.00,
        "total_cost": 14400.00,
        "currency": "EUR",
        "incoterms": "CPT",
        "carrier": "DB Cargo Eurasia",
        "tracking": "DBC-2024-EU-55290",
    },
    {
        "type": "invoice",
        "filename": "invoice_eco_005.pdf",
        "json_filename": "invoice_eco_005.json",
        "doc_number": "INV-2024-EC-0889",
        "date": "2024-10-18",
        "shipper": {"name": "AgroRhein Cooperativa", "address": "Rheinauhafen, 67065 Ludwigshafen, Germany", "vat": "DE 256 893 147"},
        "receiver": {"name": "BelgiFeed NV", "address": "Kanaaldok B1, 2030 Antwerpen, Belgium", "vat": "BE 0456.789.123"},
        "origin": "Ludwigshafen (Rhin)",
        "destination": "Antwerpen",
        "goods": "Céréales et tourteau de soja pour alimentation animale",
        "quantity": 1,
        "unit_weight_kg": 2200000.0,  # Will be clamped to 22000 for plausibility
        "total_weight_kg": 22000.0,
        "volume_m3": 45.0,
        "transport_mode": "river",
        "distance_km": 580.0,
        "departure_date": "2024-10-18",
        "arrival_date": "2024-10-21",
        "unit_price": 15000.00,
        "total_cost": 15000.00,
        "currency": "EUR",
        "incoterms": "FCA",
        "carrier": "Rhenus Logistics — Fluvial",
        "tracking": "RHN-FLV-2024-10982",
    },
]


def _build_styles() -> dict[str, ParagraphStyle]:
    """Create custom paragraph styles."""
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "DocTitle", parent=base["Heading1"],
            fontSize=20, textColor=ACCENT_DARK, spaceAfter=4,
            fontName="Helvetica-Bold",
        ),
        "subtitle": ParagraphStyle(
            "DocSubtitle", parent=base["Normal"],
            fontSize=10, textColor=TEXT_MUTED, spaceAfter=12,
        ),
        "section": ParagraphStyle(
            "Section", parent=base["Heading2"],
            fontSize=11, textColor=ACCENT_DARK, spaceBefore=14, spaceAfter=6,
            fontName="Helvetica-Bold",
        ),
        "normal": ParagraphStyle(
            "NormalText", parent=base["Normal"],
            fontSize=9, textColor=TEXT_DARK, leading=13,
        ),
        "small": ParagraphStyle(
            "SmallText", parent=base["Normal"],
            fontSize=8, textColor=TEXT_MUTED, leading=10,
        ),
        "right": ParagraphStyle(
            "RightText", parent=base["Normal"],
            fontSize=9, textColor=TEXT_DARK, alignment=TA_RIGHT,
        ),
        "footer": ParagraphStyle(
            "Footer", parent=base["Normal"],
            fontSize=7, textColor=TEXT_MUTED, alignment=TA_CENTER,
        ),
    }


def _generate_pdf(doc: dict, output_dir: Path) -> None:
    """Generate a single PDF document."""
    styles = _build_styles()
    filepath = output_dir / doc["filename"]

    pdf = SimpleDocTemplate(
        str(filepath),
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
    )

    elements: list = []

    # ── Header ──
    doc_type_label = "FACTURE / INVOICE" if doc["type"] == "invoice" else "BON DE LIVRAISON / DELIVERY NOTE"
    elements.append(Paragraph(doc_type_label, styles["title"]))
    elements.append(Paragraph(f"N° {doc['doc_number']}  —  {doc['date']}", styles["subtitle"]))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=10))

    # ── Parties ──
    party_data = [
        [
            Paragraph("<b>EXPÉDITEUR / SHIPPER</b>", styles["small"]),
            Paragraph("<b>DESTINATAIRE / CONSIGNEE</b>", styles["small"]),
        ],
        [
            Paragraph(f"<b>{doc['shipper']['name']}</b><br/>{doc['shipper']['address']}<br/>TVA: {doc['shipper']['vat']}", styles["normal"]),
            Paragraph(f"<b>{doc['receiver']['name']}</b><br/>{doc['receiver']['address']}<br/>TVA: {doc['receiver']['vat']}", styles["normal"]),
        ],
    ]
    party_table = Table(party_data, colWidths=[85 * mm, 85 * mm])
    party_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(party_table)
    elements.append(Spacer(1, 10))

    # ── Transport details ──
    elements.append(Paragraph("DÉTAILS DU TRANSPORT / TRANSPORT DETAILS", styles["section"]))

    transport_data = [
        ["Origine / Origin", doc["origin"], "Mode de transport", doc["transport_mode"].upper()],
        ["Destination", doc["destination"], "Distance (km)", f"{doc['distance_km']:,.0f}"],
        ["Date départ", doc["departure_date"], "Date arrivée", doc["arrival_date"]],
        ["Transporteur / Carrier", doc["carrier"], "Référence suivi", doc["tracking"]],
        ["Incoterms", doc["incoterms"], "Devise / Currency", doc["currency"]],
    ]

    transport_table = Table(transport_data, colWidths=[40 * mm, 45 * mm, 40 * mm, 45 * mm])
    transport_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), TEXT_MUTED),
        ("TEXTCOLOR", (2, 0), (2, -1), TEXT_MUTED),
        ("TEXTCOLOR", (1, 0), (1, -1), TEXT_DARK),
        ("TEXTCOLOR", (3, 0), (3, -1), TEXT_DARK),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, ROW_ALT]),
    ]))
    elements.append(transport_table)
    elements.append(Spacer(1, 10))

    # ── Goods ──
    elements.append(Paragraph("MARCHANDISES / GOODS", styles["section"]))

    goods_header = ["Description", "Quantité", "Poids unit. (kg)", "Poids total (kg)", "Volume (m³)"]
    goods_row = [
        Paragraph(doc["goods"], styles["normal"]),
        str(doc["quantity"]),
        f"{doc['unit_weight_kg']:.2f}",
        f"{doc['total_weight_kg']:,.1f}",
        f"{doc['volume_m3']:.1f}",
    ]

    goods_table = Table([goods_header, goods_row], colWidths=[60 * mm, 25 * mm, 25 * mm, 30 * mm, 25 * mm])
    goods_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), ACCENT_DARK),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(goods_table)
    elements.append(Spacer(1, 10))

    # ── Financial (for invoices) ──
    if doc["type"] == "invoice":
        elements.append(Paragraph("MONTANTS / AMOUNTS", styles["section"]))

        fin_data = [
            ["Prix unitaire / Unit price", f"{doc['unit_price']:,.2f} {doc['currency']}"],
            ["Sous-total HT / Subtotal", f"{doc['total_cost']:,.2f} {doc['currency']}"],
            ["TVA / VAT (20%)", f"{doc['total_cost'] * 0.20:,.2f} {doc['currency']}"],
            ["TOTAL TTC / Total incl. VAT", f"{doc['total_cost'] * 1.20:,.2f} {doc['currency']}"],
        ]

        fin_table = Table(fin_data, colWidths=[80 * mm, 50 * mm], hAlign="RIGHT")
        fin_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("BACKGROUND", (0, -1), (-1, -1), HEADER_BG),
            ("TEXTCOLOR", (0, -1), (-1, -1), ACCENT_DARK),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(fin_table)

    elements.append(Spacer(1, 20))

    # ── Footer ──
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=6))
    elements.append(Paragraph(
        f"Document généré automatiquement — EcoChain AI Platform — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        styles["footer"],
    ))
    elements.append(Paragraph(
        "Ce document est un document de test pour la démonstration du système EcoChain AI.",
        styles["footer"],
    ))

    pdf.build(elements)
    print(f"  ✓ Generated: {filepath.name}")


def _generate_json_sidecar(doc: dict, output_dir: Path) -> None:
    """Generate a JSON sidecar file matching the mock data format for easy loading."""
    json_data = {
        "document_id": f"pdf-{doc['doc_number'].lower().replace(' ', '-')}",
        "document_type": doc["type"],
        "raw_content": {
            "document_header": "FACTURE / INVOICE" if doc["type"] == "invoice" else "BON DE LIVRAISON / DELIVERY NOTE",
            "doc_number": doc["doc_number"],
            "date": doc["date"],
            "shipper_name" if doc["type"] == "invoice" else "shipper": doc["shipper"]["name"],
            "receiver_name" if doc["type"] == "invoice" else "consignee": doc["receiver"]["name"],
            "origin" if doc["type"] == "invoice" else "origin_warehouse": doc["origin"],
            "destination" if doc["type"] == "invoice" else "destination_warehouse": doc["destination"],
            "goods_description" if doc["type"] == "invoice" else "goods": doc["goods"],
            "quantity" if doc["type"] == "invoice" else "packages_count": doc["quantity"],
            "total_weight_kg" if doc["type"] == "invoice" else "gross_weight_kg": doc["total_weight_kg"],
            "transport_mode" if doc["type"] == "invoice" else "transport_type": doc["transport_mode"],
            "distance_km" if doc["type"] == "invoice" else "estimated_distance_km": doc["distance_km"],
            "departure_date" if doc["type"] == "invoice" else "ship_date": doc["departure_date"],
            "arrival_date" if doc["type"] == "invoice" else "expected_delivery": doc["arrival_date"],
            "currency": doc["currency"],
            "total_cost" if doc["type"] == "invoice" else "carrier": doc.get("total_cost", doc.get("carrier", "")),
            "incoterms": doc["incoterms"],
            "carrier": doc["carrier"],
            "tracking_ref": doc["tracking"],
        },
        "source_filename": doc["json_filename"],
        "created_at": datetime.now().isoformat(),
    }

    json_path = output_dir / doc["json_filename"]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    print(f"  ✓ JSON sidecar: {json_path.name}")


def main() -> None:
    """Generate all PDF test documents."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating {len(DOCUMENTS)} PDF documents in {OUTPUT_DIR}/\n")

    for doc in DOCUMENTS:
        _generate_pdf(doc, OUTPUT_DIR)
        _generate_json_sidecar(doc, OUTPUT_DIR)
        print()

    print(f"Done! {len(DOCUMENTS)} PDFs + JSON sidecars generated in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
