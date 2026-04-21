import os
import tempfile
from uuid import uuid4

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Cm


MINISTRY_NAME = "МИНОБРНАУКИ РОССИИ"
UNIVERSITY_FULL_NAME = (
    "Федеральное государственное бюджетное образовательное учреждение "
    "высшего образования"
)
UNIVERSITY_SHORT_NAME = "«Юго-Западный государственный университет» (ЮЗГУ)"


def set_font(run, size=16, bold=False):
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    run.font.size = Pt(size)
    run.bold = bold


def remove_table_borders(table):
    tbl = table._tbl
    tbl_pr = tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)

    for border_name in ("top", "left", "bottom", "right", "insideH", "insideV"):
        border = borders.find(qn(f"w:{border_name}"))
        if border is None:
            border = OxmlElement(f"w:{border_name}")
            borders.append(border)
        border.set(qn("w:val"), "nil")


def add_paragraph(
    doc: Document,
    text: str = "",
    align: int = WD_ALIGN_PARAGRAPH.LEFT,
    size: int = 16,
    bold: bool = False,
    space_before: int = 0,
    space_after: int = 0,
    first_line_indent_cm: float | None = None,
):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.0
    if first_line_indent_cm is not None:
        p.paragraph_format.first_line_indent = Cm(first_line_indent_cm)

    run = p.add_run(text)
    set_font(run, size=size, bold=bold)
    return p


def normalize_department_name(name: str) -> str:
    name = (name or "").strip()
    if name.lower().startswith("кафедра "):
        return name[8:].strip()
    return name


def add_approval_block(doc: Document, year: int):
    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    remove_table_borders(table)

    left_cell = table.cell(0, 0)
    right_cell = table.cell(0, 1)

    left_cell.width = Cm(9.5)
    right_cell.width = Cm(7.0)

    left_cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
    right_cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP

    left_cell.text = ""
    right_cell.text = ""

    p = right_cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run("УТВЕРЖДАЮ:")
    set_font(run, size=16, bold=False)

    p = right_cell.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run("Проректор по учебной работе")
    set_font(run, size=16)

    p = right_cell.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run("_______________ О.Г. Локтионова")
    set_font(run, size=16)

    p = right_cell.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(f'«___» __________ {year} г.')
    set_font(run, size=16)


def generate_title_page_docx(
    manual_title: str,
    discipline_name: str,
    audience: str,
    direction_code: str,
    direction_name: str,
    department_name: str,
    city: str,
    year: int,
) -> str:
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
    normal_style.font.size = Pt(16)

    clean_department_name = normalize_department_name(department_name)

    add_paragraph(
        doc,
        MINISTRY_NAME,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=16,
        bold=True,
        space_after=4,
    )
    add_paragraph(
        doc,
        UNIVERSITY_FULL_NAME,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=16,
        space_after=4,
    )
    add_paragraph(
        doc,
        UNIVERSITY_SHORT_NAME,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=16,
        space_after=12,
    )
    add_paragraph(
        doc,
        f"Кафедра {clean_department_name}",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=16,
        space_after=28,
    )

    add_approval_block(doc, year)

    add_paragraph(doc, "", space_after=70)

    add_paragraph(
        doc,
        manual_title.upper(),
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=16,
        bold=True,
        space_after=14,
    )

    add_paragraph(
        doc,
        (
            "Методические указания для выполнения лабораторной работы "
            f'по дисциплине «{discipline_name}» для {audience} '
            f"направления подготовки {direction_code} {direction_name}"
        ),
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=16,
        space_after=0,
    )

    add_paragraph(doc, "", space_after=220)

    add_paragraph(
        doc,
        f"{city} - {year}",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=16,
    )

    doc.save(output_path)
    return output_path