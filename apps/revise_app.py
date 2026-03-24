import streamlit as st
import tempfile
import os
import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from converter_pkg import convert_to_latex
from llm_pkg import compare_documents


def save_uploaded_file(uploaded_file, suffix: str) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(uploaded_file.getvalue())
        return f.name


def convert_docx_to_latex(docx_path: str) -> tuple:
    latex_path = tempfile.mktemp(suffix='.tex')
    images_dir = tempfile.mkdtemp(prefix='images_')
    convert_to_latex(docx_path, latex_path, images_dir)
    with open(latex_path, 'r', encoding='utf-8') as f:
        return f.read(), latex_path, images_dir


def display_error_card(error: dict):
    severity_emojis = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}
    severity_colors = {'critical': '#ff4444', 'high': '#ff9900', 'medium': '#ffcc00', 'low': '#66cc66'}

    section = error.get('section', 'Общий')
    error_type = error.get('error_type', error.get('type', 'неизвестно'))
    severity = error.get('severity', 'medium')
    
    with st.expander(f"{severity_emojis.get(severity, '⚪')} {section} - {error_type}", expanded=True):
        st.markdown(f"**Описание:** {error['description']}")
        st.markdown(f"**Важность:** <span style='color: {severity_colors.get(severity, 'gray')}; font-weight: bold;'>{severity.upper()}</span>", unsafe_allow_html=True)


st.set_page_config(page_title="Проверка документов", page_icon="📄", layout="wide")

st.title("Проверка документов по шаблону")
st.markdown("Загрузите шаблон и документ для проверки структуры, содержания **и форматирования**")

with st.sidebar:
    st.header("Настройки")
    compare_model = st.selectbox("Модель для сравнения:", ["qwen3-coder-plus", "qwen3:8b"], index=0)

col1, col2 = st.columns(2)
with col1:
    template_file = st.file_uploader("Шаблон (эталон)", type=['docx'], key="template")
    if template_file:
        st.caption(f"{template_file.name}")
with col2:
    document_file = st.file_uploader("Документ для проверки", type=['docx'], key="document")
    if document_file:
        st.caption(f"{document_file.name}")

if st.button("Запустить проверку", type="primary", disabled=not (template_file and document_file)):
    with st.spinner("Проверка..."):
        progress = st.progress(0)

        try:
            template_path = save_uploaded_file(template_file, '.docx')
            document_path = save_uploaded_file(document_file, '.docx')
            progress.progress(20)

            template_latex, _, _ = convert_docx_to_latex(template_path)
            document_latex, _, _ = convert_docx_to_latex(document_path)
            progress.progress(60)

            comparison = compare_documents(template_latex, document_latex, compare_model)
            progress.progress(100)
            
            if 'error' in comparison:
                st.error(f"Ошибка сравнения: {comparison['error']}")
                st.code(comparison.get('raw_response', ''), language='text')
                st.stop()

            st.markdown("---")
            st.header("📊 Результаты проверки")

            errors = comparison.get('errors', [])
            score = comparison.get('compliance_score', 'N/A')

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Ошибок всего", len(errors))
            m2.metric("Структурных", len([e for e in errors if e.get('error_type') == 'structural']))
            m3.metric("Форматирования", len([e for e in errors if e.get('error_type') == 'formatting']))
            m4.metric("Соответствие", f"{score}%")

            if errors:
                st.markdown("### 📋 Детализация ошибок")
                
                error_types = {
                    'structural': 'Структура',
                    'formatting': 'Форматирование',
                    'content': 'Содержание',
                    'typography': 'Типографика'
                }
                
                for err_type, label in error_types.items():
                    filtered = [e for e in errors if e.get('error_type') == err_type]
                    if filtered:
                        with st.expander(f"{label} ({len(filtered)})", expanded=(err_type in ['structural', 'formatting'])):
                            for severity in ['critical', 'high', 'medium', 'low']:
                                sev_errors = [e for e in filtered if e.get('severity') == severity]
                                if sev_errors:
                                    severity_emojis = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}
                                    st.markdown(f"#### {severity_emojis[severity]} {severity.upper()}")
                                    for err in sev_errors:
                                        display_error_card(err)
            else:
                st.success("Ошибок не найдено! Документ полностью соответствует шаблону.")

            st.markdown("---")
            st.subheader("Заключение эксперта")
            st.write(comparison.get('summary', 'Нет заключения'))

            report = {
                "template": template_file.name,
                "document": document_file.name,
                "model": compare_model,
                "result": comparison,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "checked_formatting": True
            }

            st.download_button(
                "Скачать отчёт (JSON)",
                data=json.dumps(report, indent=2, ensure_ascii=False),
                file_name=f"report_{time.strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

            for path in [template_path, document_path]:
                if os.path.exists(path):
                    os.unlink(path)

        except Exception as e:
            st.error(f"Ошибка: {e}")
            import traceback
            st.code(traceback.format_exc())

elif not template_file or not document_file:
    st.info("⬆Загрузите оба файла для проверки")
