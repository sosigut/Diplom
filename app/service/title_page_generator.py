import os
import tempfile
from uuid import uuid4

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, Cm


MINISTRY_NAME = "МИНОБРНАУКИ РОССИИ"
UNIVERSITY_FULL_NAME = "Федеральное государственное бюджетное образовательное учреждение высшего образования"
UNIVERSITY_SHORT_NAME = "«Юго-Западный государственный университет» (ЮЗГУ)"


def set_font(run, size=16, bold=False):
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    run.font.size = Pt(size)
    run.bold = bold


def add_paragraph(
    doc: Document,
    text: str = "",
    align: int = WD_ALIGN_PARAGRAPH.LEFT,
    size: int = 16,
    bold: bool = False,
    space_before: int = 0,
    space_after: int = 0,
    line_spacing: float = 1.0,
):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing

    run = p.add_run(text)
    set_font(run, size=size, bold=bold)
    return p


def add_empty_paragraphs(doc: Document, count: int, size: int = 16):
    for _ in range(count):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        run = p.add_run("")
        set_font(run, size=size)


def normalize_department_name(name: str) -> str:
    name = (name or "").strip()
    lower_name = name.lower()
    if lower_name.startswith("кафедра "):
        return name[8:].strip()
    return name


def generate_title_page_docx(
    manual_title: str,
    discipline_name: str,
    audience: str,
    direction_code: str,
    direction_name: str,
    department_name: str,
    city: str,
    year: int,
    udk: str,
    compiler_name: str,
    reviewer_name: str,
    reviewer_degree: str,
    description: str,
) -> str:
    output_dir = os.path.join(tempfile.gettempdir(), "title_pages")
    os.makedirs(output_dir, exist_ok=True)

    filename = f"title_page_{uuid4().hex}.docx"
    output_path = os.path.join(output_dir, filename)

    doc = Document()

    section = doc.sections[0]
    section.top_margin = Cm(3)
    section.bottom_margin = Cm(2.25)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.3)

    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Times New Roman"
    normal_style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal_style.font.size = Pt(16)

    clean_department_name = normalize_department_name(department_name)

    # =========================
    # 1 СТРАНИЦА
    # =========================
    add_paragraph(doc, MINISTRY_NAME, align=WD_ALIGN_PARAGRAPH.CENTER, size=16)
    add_paragraph(doc, UNIVERSITY_FULL_NAME, align=WD_ALIGN_PARAGRAPH.CENTER, size=16)
    add_paragraph(doc, UNIVERSITY_SHORT_NAME, align=WD_ALIGN_PARAGRAPH.CENTER, size=16)
    add_paragraph(
        doc,
        f"Кафедра {clean_department_name}",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=16,
    )

    # Блок УТВЕРЖДАЮ
    add_empty_paragraphs(doc, 1)

    add_paragraph(
        doc,
        "УТВЕРЖДАЮ",
        align=WD_ALIGN_PARAGRAPH.RIGHT,
        size=16,
        bold=True,
    )
    add_paragraph(
        doc,
        "Заведующий кафедрой __________",
        align=WD_ALIGN_PARAGRAPH.RIGHT,
        size=16,
    )
    add_paragraph(
        doc,
        "______________________________",
        align=WD_ALIGN_PARAGRAPH.RIGHT,
        size=16,
    )
    add_paragraph(
        doc,
        '"____" __________ 20____ г.',
        align=WD_ALIGN_PARAGRAPH.RIGHT,
        size=16,
    )

    # Подгонка вниз до заголовка
    add_empty_paragraphs(doc, 3)

    add_paragraph(
        doc,
        manual_title.upper(),
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=16,
        bold=True,
        space_after=6,
    )

    add_paragraph(
        doc,
        (
            f"Методические указания для выполнения лабораторной работы "
            f"по дисциплине «{discipline_name}» для {audience} "
            f"направления подготовки {direction_code} {direction_name}"
        ),
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=16,
        line_spacing=1.0,
    )

    # ВОТ ЭТОТ БЛОК ГЛАВНЫЙ:
    # именно он опускает "Курск - год" вниз страницы
    add_empty_paragraphs(doc, 7)

    add_paragraph(
        doc,
        f"{city} - {year}",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=16,
    )

    # =========================
    # 2 СТРАНИЦА
    # =========================
    doc.add_page_break()

    add_paragraph(doc, f"УДК  {udk}", size=16, space_after=0)
    add_paragraph(doc, f"Составитель:  {compiler_name}", size=16, space_after=6)

    add_paragraph(doc, "Рецензент", size=16, space_after=0)
    add_paragraph(
        doc,
        f"{reviewer_degree}  {reviewer_name}",
        size=16,
        space_after=6,
    )

    add_paragraph(
        doc,
        (
            f"{manual_title}: методические указания для выполнения  лабораторной работы "
            f"по дисциплине «{discipline_name}» для {audience} "
            f"направления подготовки {direction_code} {direction_name}/ "
            f"Юго-Зап. гос. ун-т; сост. {compiler_name}. "
            f"{city}, {year}. 19 с."
        ),
        size=16,
        line_spacing=1.0,
        space_after=6,
    )

    add_paragraph(
        doc,
        (
            f"Составлены в соответствии с федеральным государственным образовательным стандартом "
            f"высшего образования направления подготовки {direction_code} {direction_name} "
            f"и на основании учебного плана направления подготовки {direction_code} {direction_name}."
        ),
        size=16,
        line_spacing=1.0,
        space_after=6,
    )

    add_paragraph(
        doc,
        description,
        size=16,
        line_spacing=1.0,
        space_after=6,
    )

    add_paragraph(
        doc,
        (
            f"Предназначены для {audience}, обучающихся направления подготовки "
            f"{direction_code} {direction_name} "
            f"(профиль «Разработка программноинформационных систем») всех форм обучения."
        ),
        size=16,
        line_spacing=1.0,
        space_after=8,
    )

    add_paragraph(
        doc,
        "Текст печатается в авторской редакции",
        size=16,
        space_after=12,
    )

    add_paragraph(
        doc,
        (
            "Подписано в печать __________. Формат 60x84 1/16. "
            "Усл. печ. л. ____. Уч.-изд. л. 2,0. "
            "Тираж ___ экз. Заказ ________. Бесплатно."
        ),
        size=16,
        line_spacing=1.0,
        space_after=6,
    )

    add_paragraph(
        doc,
        "Юго-Западный государственный университет.",
        size=16,
        line_spacing=1.0,
        space_after=0,
    )

    add_paragraph(
        doc,
        "305040, г. Курск, ул. 50 лет Октября, 94.",
        size=16,
        line_spacing=1.0,
        space_after=0,
    )

    doc.save(output_path)
    return output_path