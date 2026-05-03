import sys
import re
from docx import Document as DocxDocument
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.text.paragraph import Paragraph
from docx.table import Table
from .text import parse_paragraph, format_runs_in_paragraph
from .tables import parse_table

def iter_block_items(parent):
    from docx.document import Document as DocxDocType
    if isinstance(parent, DocxDocType):
        parent_elm = parent.element.body
    else:
        raise ValueError("parent must be a Document")

    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)

def convert_to_latex(docx_path, output_path):
    document = DocxDocument(docx_path)
    md_lines = []

    in_list = False
    list_counter = 0
    list_type = None

    for block in iter_block_items(document):
        if isinstance(block, Paragraph):
            is_list = block.style.name in ['List Bullet', 'List Number', 'List Paragraph']

            if is_list:
                if not in_list:
                    in_list = True
                    list_type = block.style.name
                    list_counter = 0

                formatted = format_runs_in_paragraph(block)
                if list_type == 'List Bullet':
                    md_lines.append(f"- {formatted}\n")
                else:
                    list_counter += 1
                    md_lines.append(f"{list_counter}. {formatted}\n")
            else:
                if in_list:
                    md_lines.append("\n")
                    in_list = False
                    list_counter = 0
                parse_paragraph(block, md_lines)

        elif isinstance(block, Table):
            if in_list:
                md_lines.append("\n")
                in_list = False
                list_counter = 0
            parse_table(block, md_lines)

    # Очистка от лишних пустых строк
    result = "\n".join(line.rstrip() for line in md_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)

def main():
    if len(sys.argv) < 3:
        print("Usage: python -m your_package.main <input.docx> <output.md>")
        sys.exit(1)
    convert_to_latex(sys.argv[1], sys.argv[2])
    print(f"✅ Результат сохранен в {sys.argv[2]}")

if __name__ == "__main__":
    main()