from .utils import get_md_alignment
from .text import format_runs_in_paragraph

def parse_table(table, md_lines):
    if not table.rows:
        return
    md_lines.append("\n")
    num_cols = len(table.columns)

    # Заголовок
    header = []
    for cell in table.rows[0].cells[:num_cols]:
        cell_text = format_runs_in_paragraph(cell.paragraphs[0]) if cell.paragraphs else ''
        header.append(cell_text.strip() or ' ')
    md_lines.append("| " + " | ".join(header) + " |\n")

    # Разделитель с выравниванием
    sep = [get_md_alignment(table, j) for j in range(num_cols)]
    md_lines.append("| " + " | ".join(sep) + " |\n")

    # Данные
    for row in table.rows[1:]:
        row_data = []
        for cell in row.cells[:num_cols]:
            # Переносы строк внутри ячейки через <br>
            cell_text = " <br> ".join(
                format_runs_in_paragraph(p) for p in cell.paragraphs
            ).strip()
            row_data.append(cell_text or ' ')
        md_lines.append("| " + " | ".join(row_data) + " |\n")
    md_lines.append("\n")