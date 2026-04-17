import os
import tempfile
from uuid import uuid4

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Cm


MINISTRY_NAME = "МИНОБРНАУКИ РОССИИ"
UNIVERSITY_FULL_NAME = "Федеральное государственное бюджетное образовательное учреждение"
UNIVERSITY_FULL_NAME_2 = "высшего образования"
UNIVERSITY_SHORT_NAME = "«Юго-Западный государственный университет»"
UNIVERSITY_ABBR = "(ЮЗГУ)"


def set_font(run, size=14, bold=False):
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    run.font.size = Pt(size)
    run.bold = bold


def remove_table_borders(table):
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = tblPr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tblPr.append(borders)

    for border_name in ("top", "left", "bottom", "right", "insideH", "insideV"):
        border = borders.find(qn(f"w:{border_name}"))
        if border is None:
            border = OxmlElement(f"w:{border_name}")
            borders.append(border)
        border.set(qn("w:val"), "nil")


def add_paragraph(doc, text="", align=WD_ALIGN_PARAGRAPH.LEFT, size=14, bold=False, space_before=0, space_after=0):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    run = p.add_run(text)
    set_font(run, size=size, bold=bold)
    return p


def normalize_department_name(name: str) -> str:
    name = (name or "").strip()
    lower_name = name.lower()
    if lower_name.startswith("кафедра "):
        return name[len("Кафедра "):].strip()
    return name


def generate_title_page_docx(
    manual_title: str,
    discipline_name: str,
    audience: str,
    department_name: str,
    department_code: int,
    city: str,
    year: int,
) -> str:
    print("TITLE PAGE GENERATOR V2 LOADED FROM:", __file__)

    output_dir = os.path.join(tempfile.gettempdir(), "title_pages")
    os.makedirs(output_dir, exist_ok=True)

    filename = f"title_page_{uuid4().hex}.docx"
    output_path = os.path.join(output_dir, filename)

    doc = Document()

    section = doc.sections[0]
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(3)
    section.right_margin = Cm(1.5)

    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Times New Roman"
    normal_style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal_style.font.size = Pt(14)

    clean_department_name = normalize_department_name(department_name)

    # Верхний блок
    add_paragraph(doc, MINISTRY_NAME, align=WD_ALIGN_PARAGRAPH.CENTER, size=14)
    add_paragraph(doc, UNIVERSITY_FULL_NAME, align=WD_ALIGN_PARAGRAPH.CENTER, size=14, space_after=0)
    add_paragraph(doc, UNIVERSITY_FULL_NAME_2, align=WD_ALIGN_PARAGRAPH.CENTER, size=14, space_after=0)
    add_paragraph(doc, UNIVERSITY_SHORT_NAME, align=WD_ALIGN_PARAGRAPH.CENTER, size=14, space_after=0)
    add_paragraph(doc, UNIVERSITY_ABBR, align=WD_ALIGN_PARAGRAPH.CENTER, size=14, space_after=8)

    # Кафедра
    add_paragraph(
        doc,
        f"Кафедра {clean_department_name}",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=14,
        space_after=8,
    )

    # Блок "УТВЕРЖДАЮ"
    approval_table = doc.add_table(rows=1, cols=2)
    approval_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    approval_table.autofit = False
    remove_table_borders(approval_table)

    approval_table.columns[0].width = Cm(9.5)
    approval_table.columns[1].width = Cm(7)

    right_cell = approval_table.cell(0, 1)
    p = right_cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    run = p.add_run("УТВЕРЖДАЮ")
    set_font(run, size=14)

    p = right_cell.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("Проректор по учебной работе")
    set_font(run, size=14)

    p = right_cell.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("______________ О.Г. Локтионова")
    set_font(run, size=14)

    p = right_cell.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"«___» __________ {year} г.")
    set_font(run, size=14)

    # Отступ вниз
    for _ in range(7):
        doc.add_paragraph()

    # Заголовок
    add_paragraph(
        doc,
        manual_title,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=15,
        bold=True,
        space_after=8,
    )

    # Основной блок описания
    add_paragraph(
        doc,
        "методические указания к лабораторным занятиям",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=14,
        space_after=0,
    )

    add_paragraph(
        doc,
        f"для {audience}",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=14,
        space_after=0,
    )

    add_paragraph(
        doc,
        f'направления {department_code} «{clean_department_name}»',
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=14,
        space_after=0,
    )

    add_paragraph(
        doc,
        f'по дисциплине «{discipline_name}»',
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=14,
        space_after=0,
    )

    # Нижний блок
    for _ in range(12):
        doc.add_paragraph()

    add_paragraph(doc, f"{city} {year}", align=WD_ALIGN_PARAGRAPH.CENTER, size=14)

    doc.save(output_path)
    return output_path