import argparse
import os
import shutil
from dataclasses import dataclass, field
from typing import List

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
WD_LINE_SPACE_SINGLE = 0
WD_STATISTIC_PAGES = 2

WD_COLOR_RED = 255
WD_COLOR_YELLOW = 7

WD_FIELD_PAGE = 33


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

        self.issues.sort(key=lambda x: (x.priority, x.severity, x.location))

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
    def __init__(self, visible: bool = False, mark_document: bool = True):
        if win32 is None:
            raise RuntimeError(f"pywin32 не установлен: {WIN32_IMPORT_ERROR}")
        self.word = None
        self.visible = visible
        self.mark_document = mark_document

    def __enter__(self):
        self.word = win32.gencache.EnsureDispatch("Word.Application")
        self.word.Visible = self.visible
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.word:
            self.word.Quit(False)

    def open_document(self, path, readonly=True):
        return self.word.Documents.Open(os.path.abspath(path), ReadOnly=readonly)

    def check(self, path):
        report = CheckReport()

        checked_path = None
        open_path = path
        readonly = True

        if self.mark_document:
            base, ext = os.path.splitext(path)
            checked_path = base + "_checked" + ext
            shutil.copy(path, checked_path)
            open_path = checked_path
            readonly = False

        doc = self.open_document(open_path, readonly=readonly)

        try:
            self._check_paragraphs(doc, report)
            self._check_margins(doc, report)
            self._check_page_numbers(doc, report)

            if self.mark_document:
                doc.Save()
        finally:
            doc.Close(False)

        return report, checked_path

    # ===================== ПОДСВЕТКА =====================

    def _mark_range(self, doc, start_par, end_par, severity, message):
        if not self.mark_document:
            return

        try:
            start = doc.Paragraphs(start_par).Range.Start
            end = doc.Paragraphs(end_par).Range.End
            rng = doc.Range(start, end)

            if severity == "ERROR":
                rng.Font.Color = WD_COLOR_RED
            else:
                rng.HighlightColorIndex = WD_COLOR_YELLOW

            doc.Comments.Add(rng, message)
        except Exception:
            pass

    def _mark_page(self, doc, page, severity, message):
        if not self.mark_document:
            return

        try:
            start = doc.GoTo(1, 1, page).Start
            try:
                end = doc.GoTo(1, 1, page + 1).Start
            except Exception:
                end = doc.Content.End

            rng = doc.Range(start, end)

            if severity == "ERROR":
                rng.Font.Color = WD_COLOR_RED
            else:
                rng.HighlightColorIndex = WD_COLOR_YELLOW

            doc.Comments.Add(rng, message)
        except Exception:
            pass

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

            indent = p.Range.ParagraphFormat.FirstLineIndent
            if abs(indent) < 0.01:
                try:
                    indent = p.Range.Style.ParagraphFormat.FirstLineIndent
                except Exception:
                    pass
            indent_cm = pt_to_cm(indent)

            spacing = int(p.Range.ParagraphFormat.LineSpacingRule)

            font_issue = self._process_range(
                current=font_issue,
                is_error=(font != "Times New Roman"),
                value=font,
                i=i,
                page=page,
                message_func=lambda v: f"Используется шрифт '{v}', требуется Times New Roman.",
                report=report,
                doc=doc,
                severity="ERROR"
            )

            size_issue = self._process_range(
                current=size_issue,
                is_error=(abs(size - 16) > 0.2),
                value=size,
                i=i,
                page=page,
                message_func=lambda v: f"Размер шрифта {v} pt, требуется 16 pt.",
                report=report,
                doc=doc,
                severity="WARNING"
            )

            indent_issue = self._process_range(
                current=indent_issue,
                is_error=(abs(indent_cm - 1.25) > 0.05),
                value=round(indent_cm, 2),
                i=i,
                page=page,
                message_func=lambda v: f"Абзацный отступ {v} см, требуется 1.25 см.",
                report=report,
                doc=doc,
                severity="ERROR"
            )

            spacing_issue = self._process_range(
                current=spacing_issue,
                is_error=(spacing != WD_LINE_SPACE_SINGLE),
                value=spacing,
                i=i,
                page=page,
                message_func=lambda v: "Межстрочный интервал не одинарный.",
                report=report,
                doc=doc,
                severity="WARNING"
            )

        for issue in [font_issue, size_issue, indent_issue, spacing_issue]:
            if issue:
                self._flush(issue, report, doc)

    def _process_range(self, current, is_error, value, i, page, message_func, report, doc, severity):
        if is_error:
            if current and current["value"] == value and current["severity"] == severity:
                current["end_par"] = i
                current["end_page"] = page
            else:
                if current:
                    self._flush(current, report, doc)
                return {
                    "value": value,
                    "start_par": i,
                    "start_page": page,
                    "end_par": i,
                    "end_page": page,
                    "message": message_func(value),
                    "severity": severity,
                }
        else:
            if current:
                self._flush(current, report, doc)
            return None

        return current

    def _flush(self, data, report, doc):
        location = (
            f"Абзац {data['start_par']} (стр. {data['start_page']}) - "
            f"Абзац {data['end_par']} (стр. {data['end_page']})"
        )

        report.issues.append(CheckIssue(
            rule="3",
            severity=data["severity"],
            location=location,
            message=data["message"],
            priority=1
        ))

        self._mark_range(
            doc,
            data["start_par"],
            data["end_par"],
            data["severity"],
            data["message"]
        )

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

            section_has_error = False

            for name, val, req in margins:
                if abs(val - req) > 0.05:
                    section_has_error = True
                    report.issues.append(CheckIssue(
                        rule="3",
                        severity="ERROR",
                        location=f"Раздел {i}",
                        message=f"{name.capitalize()} поле {val:.2f} см, требуется {req} см.",
                        priority=1
                    ))

            if section_has_error:
                self._mark_page(doc, i, "ERROR", "Ошибка полей страницы")

    # ===================== НУМЕРАЦИЯ =====================

    def _check_page_numbers(self, doc, report):
        total_pages = doc.ComputeStatistics(WD_STATISTIC_PAGES)

        found_top = False
        found_bottom = False
        issues = []

        for i in range(1, doc.Sections.Count + 1):
            sec = doc.Sections(i)

            header = sec.Headers(WD_HEADER_FOOTER_PRIMARY)
            footer = sec.Footers(WD_HEADER_FOOTER_PRIMARY)

            for field in header.Range.Fields:
                if field.Type == WD_FIELD_PAGE:
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

            if footer.PageNumbers.Count > 0:
                found_bottom = True

        location = f"Стр. 1 - Стр. {total_pages}"

        if not found_top and not found_bottom:
            report.issues.append(CheckIssue(
                rule="4",
                severity="ERROR",
                location=location,
                message="Нумерация страниц отсутствует.",
                priority=1
            ))
            self._mark_page(doc, 1, "ERROR", "Нумерация страниц отсутствует")
            return

        if not found_top and found_bottom:
            report.issues.append(CheckIssue(
                rule="4",
                severity="ERROR",
                location=location,
                message="Номер страницы расположен внизу, должен быть вверху по центру.",
                priority=1
            ))
            self._mark_page(doc, 1, "ERROR", "Номер страницы расположен внизу")
            return

        if issues:
            report.issues.append(CheckIssue(
                rule="4",
                severity="ERROR",
                location=location,
                message="; ".join(issues),
                priority=1
            ))
            self._mark_page(doc, 1, "ERROR", "Ошибка оформления нумерации страниц")

    # ===================== ВСПОМОГАТЕЛЬНОЕ =====================

    def _skip_paragraph_for_body_rules(self, paragraph):
        try:
            if paragraph.Range.Information(WD_WITHIN_TABLE):
                return True
        except Exception:
            pass

        text = (paragraph.Range.Text or "").strip()
        if not text or len(text) < 2:
            return True

        try:
            style_name = str(paragraph.Range.Style.NameLocal).lower()
            if "heading" in style_name or "заголов" in style_name:
                return True
        except Exception:
            pass

        return False


def ensure_supported_file(path):
    if not os.path.exists(path):
        raise SystemExit(f"❌ Файл не найден: {path}")
    if not path.lower().endswith((".doc", ".docx")):
        raise SystemExit("❌ Поддерживаются только .doc и .docx")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?", default=None)
    args = parser.parse_args()

    if args.file is None:
        args.file = input("Введите путь к файлу: ").strip('"')

    ensure_supported_file(args.file)

    with WordMethodicalChecker(visible=False, mark_document=True) as checker:
        report, checked_path = checker.check(args.file)
        print(report.to_text())
        print(report.summary())

        if checked_path:
            print(f"\n📄 Размеченная копия сохранена: {checked_path}")


if __name__ == "__main__":
    main()