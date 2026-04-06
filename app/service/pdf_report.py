import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Spacer, Paragraph, Table, TableStyle

from app.service.checker import CheckReport


def register_fonts():
    fonts_dir = os.path.join("app", "fonts")

    pdfmetrics.registerFont(TTFont("TimesNewRoman", os.path.join(fonts_dir, "times.ttf")))
    pdfmetrics.registerFont(TTFont("TimesNewRoman-Bold", os.path.join(fonts_dir, "timesbd.ttf")))
    pdfmetrics.registerFont(TTFont("TimesNewRoman-Italic", os.path.join(fonts_dir, "timesi.ttf")))
    pdfmetrics.registerFont(TTFont("TimesNewRoman-BoldItalic", os.path.join(fonts_dir, "timesbi.ttf")))


def generate_error_report_pdf(report: CheckReport, source_filename: str, output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    register_fonts()

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
        fontName="TimesNewRoman-Bold",
        fontSize=18,
        leading=24,
        textColor=colors.HexColor("#1f2937"),
        spaceAfter=10,
    )

    meta_style = ParagraphStyle(
        "MetaCustom",
        parent=styles["Normal"],
        fontName="TimesNewRoman",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#4b5563"),
        spaceAfter=6,
    )

    section_style = ParagraphStyle(
        "SectionCustom",
        parent=styles["Heading2"],
        fontName="TimesNewRoman-Bold",
        fontSize=13,
        leading=18,
        textColor=colors.HexColor("#111827"),
        spaceBefore=10,
        spaceAfter=8,
    )

    body_style = ParagraphStyle(
        "BodyCustom",
        parent=styles["Normal"],
        fontName="TimesNewRoman",
        fontSize=10,
        leading=14,
        textColor=colors.black,
    )

    elements = []

    errors_count = sum(1 for issue in report.issues if issue.severity == "ERROR")
    warnings_count = sum(1 for issue in report.issues if issue.severity == "WARNING")

    if errors_count > 0:
        status_text = "Статус: документ содержит критические ошибки"
        status_color = "#991b1b"
    elif warnings_count > 0:
        status_text = "Статус: документ содержит предупреждения"
        status_color = "#92400e"
    else:
        status_text = "Статус: документ соответствует требованиям"
        status_color = "#166534"

    status_style = ParagraphStyle(
        "StatusCustom",
        parent=styles["Normal"],
        fontName="TimesNewRoman-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor(status_color),
        spaceAfter=10,
    )

    elements.append(Paragraph("Отчёт по проверке методички", title_style))
    elements.append(Paragraph(f"Файл: {source_filename}", meta_style))
    elements.append(Paragraph(f"Дата проверки: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}", meta_style))
    elements.append(Paragraph(f"Ошибки: {errors_count} | Предупреждения: {warnings_count}", meta_style))
    elements.append(Paragraph(status_text, status_style))
    elements.append(Spacer(1, 8))

    if not report.issues:
        elements.append(Paragraph("Ошибки не найдены", section_style))
        elements.append(Paragraph("Документ успешно прошёл автоматическую проверку оформления.", body_style))
    else:
        elements.append(Paragraph("Найденные замечания", section_style))

        table_data = [["#", "Раздел", "Тип", "Где", "Описание"]]

        for idx, issue in enumerate(report.issues, start=1):
            severity_text = "Ошибка" if issue.severity == "ERROR" else "Предупреждение"

            table_data.append([
                str(idx),
                issue.rule,
                severity_text,
                issue.location,
                issue.message,
            ])

        table = Table(
            table_data,
            colWidths=[10 * mm, 20 * mm, 30 * mm, 50 * mm, 68 * mm],
            repeatRows=1,
        )

        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "TimesNewRoman-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "TimesNewRoman"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("LEADING", (0, 0), (-1, -1), 12),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
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