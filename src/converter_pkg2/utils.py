from docx.enum.text import WD_ALIGN_PARAGRAPH

def markdown_escape(text):
    """Экранирует спецсимволы Markdown."""
    if text is None:
        return ""
    for c, esc in [('\\', '\\\\'), ('`', '\\`'), ('*', '\\*'), ('_', '\\_'),
                   ('{', '\\{'), ('}', '\\}'), ('[', '\\['), (']', '\\]'),
                   ('(', '\\('), (')', '\\)'), ('#', '\\#'), ('+', '\\+'),
                   ('-', '\\-'), ('.', '\\.'), ('!', '\\!'), ('|', '\\|')]:
        text = text.replace(c, esc)
    return text

def get_md_alignment(table, col_index):
    """Возвращает спецификатор выравнивания для MD-таблиц."""
    for row in table.rows:
        if col_index >= len(row.cells):
            continue
        cell = row.cells[col_index]
        if cell.paragraphs:
            para = cell.paragraphs[0]
            if para.alignment == WD_ALIGN_PARAGRAPH.CENTER:
                return ':--:'
            elif para.alignment == WD_ALIGN_PARAGRAPH.RIGHT:
                return '--:'
            return '---'
    return '---'