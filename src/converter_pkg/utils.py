from docx.enum.text import WD_ALIGN_PARAGRAPH


def latex_special_chars(text):
    if text is None:
        return ""

    replace_chars = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\^{}',
        '\\': r'\textbackslash{}',
        '>': r'$>$',
        '<': r'$<$'
    }

    for char, new_char in replace_chars.items():
        text = text.replace(char, new_char)

    return text


def get_column_alignment(table, col_index):
    for row in table.rows:
        if col_index >= len(row.cells):
            continue
        cell = row.cells[col_index]
        if cell.paragraphs:
            para = cell.paragraphs[0]
            if para.alignment is not None:
                if para.alignment == WD_ALIGN_PARAGRAPH.CENTER:
                    return 'c'
                elif para.alignment == WD_ALIGN_PARAGRAPH.RIGHT:
                    return 'r'
                else:
                    return 'l'
    return 'l'
