import os
import shutil
from docx import Document
from docx.shared import Pt, Cm

BASE_FILE = "archive\q.docx"
OUTPUT_DIR = "test_referats"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_doc():
    return Document(BASE_FILE)

def delete_paragraph(paragraph):
    p = paragraph._element
    p.getparent().remove(p)
    p._p = None
    p._element = None

def clear_section(doc, heading_text):
    in_section = False
    to_delete = []
    for p in doc.paragraphs:
        if heading_text.strip().lower() in p.text.strip().lower():
            in_section = True
            continue
        if in_section and any(h.strip().lower() in p.text.strip().lower() for h in ["ВВЕДЕНИЕ", "ЗАКЛЮЧЕНИЕ", "СПИСОК", "СОДЕРЖАНИЕ", "РАЗДЕЛ"]):
            break
        if in_section:
            to_delete.append(p)
    for p in reversed(to_delete):
        delete_paragraph(p)

def change_font(doc, font_name):
    for p in doc.paragraphs:
        for run in p.runs:
            run.font.name = font_name
            run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)

def change_spacing_indent(doc, spacing, indent_cm):
    for p in doc.paragraphs:
        p.paragraph_format.line_spacing = spacing
        p.paragraph_format.first_line_indent = Cm(indent_cm)

def change_margins(doc, left, right, top, bottom):
    sec = doc.sections[0]
    sec.left_margin = Cm(left)
    sec.right_margin = Cm(right)
    sec.top_margin = Cm(top)
    sec.bottom_margin = Cm(bottom)

def truncate_sources(doc, keep_count):
    in_refs = False
    count = 0
    to_delete = []
    for p in doc.paragraphs:
        if "СПИСОК" in p.text.upper():
            in_refs = True
            continue
        if in_refs and p.text.strip().startswith("1."):
            count += 1
            if count > keep_count:
                to_delete.append(p)
    for p in reversed(to_delete):
        delete_paragraph(p)

def swap_sources(doc):
    refs = [p for p in doc.paragraphs if p.text.strip().startswith(("1.", "2.", "3.", "4."))]
    if len(refs) >= 2:
        t1, t2 = refs[0].text, refs[1].text
        refs[0].text = t2
        refs[1].text = t1

def clear_title_fields(doc, fields_to_clear):
    for p in doc.paragraphs:
        for field in fields_to_clear:
            if field in p.text:
                p.text = p.text.replace(field, "").strip()

# === КОНФИГУРАЦИЯ ТЕСТОВ ===
tests = [
    {"name": "01_Missing_Conclusion", "func": lambda d: clear_section(d, "ЗАКЛЮЧЕНИЕ"), "desc": "Отсутствует раздел Заключение"},
    {"name": "02_Wrong_Section_Order", "func": lambda d: change_margins(d, 3, 1.5, 2, 2) or clear_section(d, "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ"), "desc": "Нарушен порядок: библиография удалена, имитация перемещения"},
    {"name": "03_Empty_Intro", "func": lambda d: clear_section(d, "ВВЕДЕНИЕ"), "desc": "Введение пустое (нет актуальности, цели, задач)"},
    {"name": "04_TOC_Mismatch", "func": lambda d: [setattr(p, 'text', "РАЗДЕЛ 10. СЕКРЕТНЫЕ МАТЕРИАЛЫ") for p in d.paragraphs if "РАЗДЕЛ 1." in p.text], "desc": "Оглавление не соответствует реальной структуре"},
    {"name": "05_Wrong_Font", "func": lambda d: change_font(d, "Arial"), "desc": "Шрифт Arial вместо Times New Roman"},
    {"name": "06_Wrong_Formatting", "func": lambda d: change_spacing_indent(d, 1.0, 0), "desc": "Интервал 1.0, отступ 0 см (должно 1.5 и 1.25)"},
    {"name": "07_Wrong_Margins", "func": lambda d: change_margins(d, 1.5, 2.5, 1.5, 2.5), "desc": "Неверные поля (слева 1.5 см, справа 2.5 см)"},
    {"name": "08_Less_Sources", "func": lambda d: truncate_sources(d, 3), "desc": "В списке источников только 3 записи (нужно ≥5)"},
    {"name": "09_Non_Alphabetical", "func": lambda d: swap_sources(d), "desc": "Источники идут не в алфавитном порядке"},
    {"name": "10_Incomplete_Title", "func": lambda d: clear_title_fields(d, ["Выполнила:", "Группа:", "Преподаватель:"]), "desc": "На титульном листе стерты ФИО, группа и преподаватель"}
]

# === ГЕНЕРАЦИЯ ===
from docx.oxml.ns import qn  # импорт для шрифтов

for test in tests:
    doc = load_doc()
    test["func"](doc)
    out_path = os.path.join(OUTPUT_DIR, f"{test['name']}.docx")
    doc.save(out_path)
    print(f"✅ Создан: {out_path} | Ошибка: {test['desc']}")