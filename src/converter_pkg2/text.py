from .utils import markdown_escape

def are_runs_similar(run1, run2):
    return (run1.bold == run2.bold and
            run1.italic == run2.italic and
            run1.underline == run2.underline and
            run1.font.name == run2.font.name and
            run1.font.size == run2.font.size)

def format_runs_in_paragraph(paragraph):
    """Форматирует текст параграфа и добавляет ТОЧНЫЕ комментарии из старого кода."""
    merged_runs = []
    current_text = ''
    current_run = None

    for run in paragraph.runs:
        if current_run is None:
            current_run = run
            current_text = run.text
        elif are_runs_similar(current_run, run):
            current_text += run.text
        else:
            merged_runs.append((current_text, current_run))
            current_run = run
            current_text = run.text

    if current_run is not None:
        merged_runs.append((current_text, current_run))

    result = ''
    for run_text, run in merged_runs:
        escaped = markdown_escape(run_text)
        
        # Markdown-форматирование
        if run.bold and run.italic:
            content = f'**{escaped}**'
        elif run.bold:
            content = f'**{escaped}**'
        elif run.italic:
            content = f'*{escaped}*'
        elif run.underline:
            content = f'<u>{escaped}</u>'
        else:
            content = escaped

        # --- ТОЧНАЯ ЛОГИКА ИЗВЛЕЧЕНИЯ МЕТАДАННЫХ (как в старом LaTeX) ---
        font_name = run.font.name
        font_size = run.font.size
        if font_size is not None:
            font_size = font_size.pt

        line_spacing = paragraph.paragraph_format.line_spacing
        line_spacing_rule = paragraph.paragraph_format.line_spacing_rule

        if line_spacing is not None:
            if isinstance(line_spacing, (int, float)):
                if line_spacing_rule in [3, 4]:
                    line_spacing_pt = round(line_spacing / 12700, 2)
                else:
                    line_spacing_pt = line_spacing
            else:
                line_spacing_pt = str(line_spacing)
        else:
            line_spacing_pt = None

        # Комментарий сохраняется в формате HTML (стандарт MD), но с теми же полями
        meta_comment = f'<!-- Шрифт-{font_name} Размер шрифта-{font_size} Межстрочный интервал-{line_spacing_pt} Правило-{line_spacing_rule} -->'
        result += f"{meta_comment}{content}"

    return result

def parse_paragraph(paragraph, md_lines):
    if paragraph.style.name.startswith("Heading"):
        try:
            level = int(paragraph.style.name.split()[1])
        except (IndexError, ValueError):
            level = 1
        prefix = '#' * min(level, 6)
        md_lines.append(f"\n{prefix} {paragraph.text}\n")
        return

    text = format_runs_in_paragraph(paragraph)
    if text.strip():
        md_lines.append(f"{text}\n\n")