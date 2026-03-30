import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Spacer, Paragraph, Table, TableStyle

from app.service.checker import CheckReport


def generate_error_report_pdf(report: CheckReport, source_filename: str, output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=24,
        textColor=colors.HexColor("#1f2937"),
        spaceAfter=10,
    )

    meta_style = ParagraphStyle(
        "MetaCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4b5563"),
        spaceAfter=6,
    )

    section_style = ParagraphStyle(
        "SectionCustom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=18,
        textColor=colors.HexColor("#111827"),
        spaceBefore=10,
        spaceAfter=8,
    )

    body_style = ParagraphStyle(
        "BodyCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.black,
    )

    elements = []

    errors_count = sum(1 for issue in report.issues if issue.severity == "ERROR")
    warnings_count = sum(1 for issue in report.issues if issue.severity == "WARNING")

    elements.append(Paragraph("Отчёт по проверке методички", title_style))
    elements.append(Paragraph(f"Файл: {source_filename}", meta_style))
    elements.append(Paragraph(f"Дата проверки: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}", meta_style))
    elements.append(Paragraph(f"Ошибки: {errors_count} | Предупреждения: {warnings_count}", meta_style))
    elements.append(Spacer(1, 8))

    if not report.issues:
        elements.append(Paragraph("Ошибки не найдены.", section_style))
        elements.append(Paragraph("Документ успешно прошёл проверку.", body_style))
    else:
        elements.append(Paragraph("Найденные замечания", section_style))

        table_data = [["#", "Раздел", "Тип", "Где", "Описание"]]

        for idx, issue in enumerate(report.issues, start=1):
            table_data.append([
                str(idx),
                issue.rule,
                issue.severity,
                issue.location,
                issue.message,
            ])

        table = Table(
            table_data,
            colWidths=[10 * mm, 20 * mm, 22 * mm, 50 * mm, 75 * mm],
            repeatRows=1,
        )

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("LEADING", (0, 0), (-1, -1), 12),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (2, 1), (2, -1), "CENTER"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))

        for row_idx, issue in enumerate(report.issues, start=1):
            if issue.severity == "ERROR":
                table.setStyle(TableStyle([
                    ("BACKGROUND", (2, row_idx), (2, row_idx), colors.HexColor("#fee2e2")),
                    ("TEXTCOLOR", (2, row_idx), (2, row_idx), colors.HexColor("#991b1b")),
                ]))
            elif issue.severity == "WARNING":
                table.setStyle(TableStyle([
                    ("BACKGROUND", (2, row_idx), (2, row_idx), colors.HexColor("#fef3c7")),
                    ("TEXTCOLOR", (2, row_idx), (2, row_idx), colors.HexColor("#92400e")),
                ]))

        elements.append(table)

    doc.build(elements)
    return output_path