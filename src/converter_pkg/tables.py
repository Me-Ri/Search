from pylatex import NoEscape

from .utils import get_column_alignment, latex_special_chars
from .text import format_runs_in_paragraph


def parse_table(table, latex_doc):
    num_rows = len(table.rows)
    num_cols = len(table.columns)

    #Получаем размеры столбцов
    col_widths = []
    for j in range(num_cols):
        max_width = 0
        for i in range(num_rows):
            row = table.rows[i]
        
            if i != len(row.cells):
                continue
            cell = table.cell(i, j)
            if hasattr(cell._tc.tcPr, 'tcW') and cell._tc.tcPr.tcW is not None:
                w = cell._tc.tcPr.tcW
                if w.type == 'dxa':
                    if hasattr(w, 'w') and w.w is not None:
                        width_inch = float(w.w) / 1440
                        width_cm = width_inch * 2.54
                        max_width = max(max_width, width_cm)
                    elif hasattr(w, 'val') and w.val is not None:
                        width_inch = float(w.val) / 1440
                        width_cm = width_inch * 2.54
                        max_width = max(max_width, width_cm)


        if max_width == 0:
            max_width = 3.0

        col_widths.append(max_width)

    #Создаем разметку таблицы
    col_spec_parts = []
    for j, width in enumerate(col_widths):
        
        col_exists = any(j < len(row.cells) for row in table.rows)
    
        if col_exists:
            alignment = get_column_alignment(table, j)
        else:
            alignment = 'l'

        if alignment == 'c':
            spec = f'>{{\\centering\\arraybackslash}}p{{{width}cm}}'
        elif alignment == 'r':
            spec = f'>{{\\raggedleft\\arraybackslash}}p{{{width}cm}}'
        else:
            spec = f'>{{\\raggedright\\arraybackslash}}p{{{width}cm}}'

        col_spec_parts.append(spec)

    col_spec = '|' + '|'.join(col_spec_parts) + '|'

    latex_doc.append(NoEscape(f'\\begin{{longtable}}{{{col_spec}}}'))
    latex_doc.append(NoEscape('\\hline'))

    for i, row in enumerate(table.rows):
        row_data = []
        for cell in row.cells:
            paragraphs_latex = []
            for para in cell.paragraphs:
                para_latex = format_runs_in_paragraph(para, latex_special_chars)
                paragraphs_latex.append(para_latex)

            cell_content = ' \\newline '.join(paragraphs_latex) if paragraphs_latex else ''
            row_data.append(cell_content)

        row_str = ' & '.join(row_data) + ' \\\\ \\hline'

        if i == 0:
            latex_doc.append(NoEscape(row_str + ' \\endfirsthead'))
            latex_doc.append(NoEscape('\\hline'))
        else:
            latex_doc.append(NoEscape(row_str))

    latex_doc.append(NoEscape('\\end{longtable}'))
