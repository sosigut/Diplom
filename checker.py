import argparse
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional

try:
    import win32com.client as win32
except Exception as e:
    win32 = None
    WIN32_IMPORT_ERROR = e
else:
    WIN32_IMPORT_ERROR = None


CM_TO_PT = 28.3464567
WD_ALIGN_CENTER = 1
WD_WITHIN_TABLE = 12
WD_HEADER_FOOTER_PRIMARY = 1
WD_STATISTIC_PAGES = 2
WD_LINE_SPACE_SINGLE = 0


def pt_to_cm(pt):
    return pt / CM_TO_PT


@dataclass
class CheckIssue:
    rule: str
    severity: str
    location: str
    message: str
    priority: int = 3


@dataclass
class CheckReport:
    issues: List[CheckIssue] = field(default_factory=list)

    def to_text(self) -> str:
        if not self.issues:
            return "✅ Ошибок не найдено."

        self.issues.sort(key=lambda x: (x.priority, x.severity))

        lines = []
        for i, issue in enumerate(self.issues, 1):
            icon = {"ERROR": "❌", "WARNING": "⚠️", "INFO": "ℹ️"}.get(issue.severity, "")
            lines.append(f"{icon} Ошибка #{i}")
            lines.append(f"   📌 Раздел: {issue.rule}")
            lines.append(f"   📍 Где: {issue.location}")
            lines.append(f"   💬 Проблема: {issue.message}")
            lines.append("")
        return "\n".join(lines)

    def summary(self) -> str:
        errors = sum(1 for x in self.issues if x.severity == "ERROR")
        warnings = sum(1 for x in self.issues if x.severity == "WARNING")

        status = "✅ Документ в порядке"
        if errors > 0:
            status = "❌ Есть критические ошибки"
        elif warnings > 0:
            status = "⚠️ Есть предупреждения"

        return (
            f"\n📊 Итог:\n"
            f"   ❌ Ошибки: {errors}\n"
            f"   ⚠️ Предупреждения: {warnings}\n"
            f"\n👉 Статус: {status}"
        )


class WordMethodicalChecker:
    def __init__(self, visible=False):
        if win32 is None:
            raise RuntimeError(f"pywin32 не установлен: {WIN32_IMPORT_ERROR}")
        self.word = None
        self.visible = visible

    def __enter__(self):
        self.word = win32.gencache.EnsureDispatch("Word.Application")
        self.word.Visible = self.visible
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.word:
            self.word.Quit(False)

    def open_document(self, path):
        return self.word.Documents.Open(os.path.abspath(path), ReadOnly=True)

    def check(self, path):
        report = CheckReport()
        doc = self.open_document(path)

        try:
            self._check_paragraphs(doc, report)
            self._check_margins(doc, report)
            self._check_page_numbers(doc, report)
        finally:
            doc.Close(False)

        return report

    # ===================== ПАРАГРАФЫ =====================

    def _check_paragraphs(self, doc, report):
        font_issue = None
        size_issue = None
        indent_issue = None
        spacing_issue = None

        for i in range(1, doc.Paragraphs.Count + 1):
            p = doc.Paragraphs(i)
            text = (p.Range.Text or "").strip()

            if not text or self._skip_paragraph_for_body_rules(p):
                continue

            page = p.Range.Information(3)
            font = str(p.Range.Font.Name).strip()
            size = float(p.Range.Font.Size)
            indent = pt_to_cm(p.Range.ParagraphFormat.FirstLineIndent)
            spacing = int(p.Range.ParagraphFormat.LineSpacingRule)

            # ---------- ШРИФТ ----------
            font_issue = self._process_range(
                report, font_issue, font != "Times New Roman",
                font, i, page,
                lambda v: f"Используется шрифт {v}, требуется Times New Roman."
            )

            # ---------- РАЗМЕР ----------
            size_issue = self._process_range(
                report, size_issue, abs(size - 16) > 0.2,
                size, i, page,
                lambda v: f"Размер шрифта {v} pt, требуется 16 pt."
            )

            # ---------- ОТСТУП ----------
            indent_issue = self._process_range(
                report, indent_issue, abs(indent - 1.25) > 0.05,
                round(indent, 2), i, page,
                lambda v: f"Абзацный отступ {v} см, требуется 1.25 см."
            )

            # ---------- ИНТЕРВАЛ ----------
            spacing_issue = self._process_range(
                report, spacing_issue, spacing != WD_LINE_SPACE_SINGLE,
                spacing, i, page,
                lambda v: "Межстрочный интервал не одинарный."
            )

        # закрываем все
        for issue in [font_issue, size_issue, indent_issue, spacing_issue]:
            if issue:
                self._flush(issue, report)

    def _process_range(self, report, current, is_error, value, i, page, message_func):
        if is_error:
            if current and current["value"] == value:
                current["end_par"] = i
                current["end_page"] = page
            else:
                if current:
                    self._flush(current, report)
                return {
                    "value": value,
                    "start_par": i,
                    "start_page": page,
                    "end_par": i,
                    "end_page": page,
                    "message": message_func(value)
                }
        else:
            if current:
                self._flush(current, report)
            return None

        return current

    def _flush(self, data, report):
        location = (
            f"Абзац {data['start_par']} (стр. {data['start_page']}) - "
            f"Абзац {data['end_par']} (стр. {data['end_page']})"
        )

        report.issues.append(CheckIssue(
            rule="3",
            severity="ERROR",
            location=location,
            message=data["message"],
            priority=1
        ))

    # ===================== ПОЛЯ =====================

    def _check_margins(self, doc, report):
        for i in range(1, doc.Sections.Count + 1):
            sec = doc.Sections(i)
            ps = sec.PageSetup

            margins = [
                ("верхнее", pt_to_cm(ps.TopMargin), 3.0),
                ("нижнее", pt_to_cm(ps.BottomMargin), 2.25),
                ("левое", pt_to_cm(ps.LeftMargin), 2.2),
                ("правое", pt_to_cm(ps.RightMargin), 2.3),
            ]

            for name, val, req in margins:
                if abs(val - req) > 0.05:
                    report.issues.append(CheckIssue(
                        rule="3",
                        severity="ERROR",
                        location=f"Раздел {i}",
                        message=f"{name.capitalize()} поле {val:.2f} см, требуется {req} см.",
                        priority=1
                    ))

    # ===================== НУМЕРАЦИЯ =====================

    def _check_page_numbers(self, doc, report):
        found_top = False
        found_bottom = False
        issues = []

        for i in range(1, doc.Sections.Count + 1):
            sec = doc.Sections(i)

            header = sec.Headers(WD_HEADER_FOOTER_PRIMARY)
            footer = sec.Footers(WD_HEADER_FOOTER_PRIMARY)

            # Проверяем поля верхнего колонтитула
            for field in header.Range.Fields:
                if field.Type == 33:  # wdFieldPage
                    found_top = True
                    try:
                        para = field.Result.Paragraphs(1)
                        align = int(para.Alignment)
                        font = str(para.Range.Font.Name).strip()
                        size = float(para.Range.Font.Size)
                    except Exception:
                        issues.append("не удалось определить параметры номера страницы")
                        continue

                    if align != WD_ALIGN_CENTER:
                        issues.append("номер страницы вверху не по центру")
                    if font.lower() != "times new roman":
                        issues.append(f"шрифт номера страницы '{font}', требуется Times New Roman")
                    if abs(size - 16) > 0.2:
                        issues.append(f"размер номера страницы {size} pt, требуется 16 pt")

            # Проверяем нижний колонтитул
            if footer.PageNumbers.Count > 0:
                found_bottom = True

        if not found_top and not found_bottom:
            report.issues.append(CheckIssue(
                rule="4",
                severity="ERROR",
                location="Документ",
                message="Нумерация страниц отсутствует.",
                priority=1
            ))
            return

        if not found_top and found_bottom:
            report.issues.append(CheckIssue(
                rule="4",
                severity="ERROR",
                location="Колонтитул",
                message="Номер страницы расположен внизу, должен быть вверху по центру.",
                priority=1
            ))
            return

        if issues:
            report.issues.append(CheckIssue(
                rule="4",
                severity="ERROR",
                location="Верхний колонтитул",
                message="; ".join(issues),
                priority=1
            ))

    def _skip_paragraph_for_body_rules(self, paragraph):
        try:
            if paragraph.Range.Information(WD_WITHIN_TABLE):
                return True
        except:
            pass

        text = (paragraph.Range.Text or "").strip()
        return not text


def ensure_supported_file(path):
    if not os.path.exists(path):
        raise SystemExit(f"❌ Файл не найден: {path}")
    if not path.lower().endswith((".doc", ".docx")):
        raise SystemExit("❌ Только .doc/.docx")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?", default=None)
    args = parser.parse_args()

    if args.file is None:
        args.file = input("Введите путь к файлу: ").strip('"')

    ensure_supported_file(args.file)

    with WordMethodicalChecker() as checker:
        report = checker.check(args.file)
        print(report.to_text())
        print(report.summary())


if __name__ == "__main__":
    main()