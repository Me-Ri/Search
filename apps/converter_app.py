import streamlit as st
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Добавляем src в путь импорта
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from converter_pkg import convert_to_latex

def main():
    st.set_page_config(
        page_title="DOCX to LaTeX Converter",
        page_icon="📄",
        layout="wide"
    )
    
    st.title("📄 DOCX to LaTeX Converter")
    st.markdown("### Преобразуйте ваши документы Word в формат LaTeX")
    
    # Создаем временную директорию
    with tempfile.TemporaryDirectory() as temp_dir:
        uploaded_file = st.file_uploader(
            "Выберите файл .docx для конвертации",
            type=['docx'],
            help="Загрузите документ в формате .docx"
        )
        
        if uploaded_file is not None:
            st.success(f"Загружен файл: {uploaded_file.name}")
            
            docx_path = os.path.join(temp_dir, uploaded_file.name)
            with open(docx_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            image_dir = os.path.join(temp_dir, 'images')
            os.makedirs(image_dir, exist_ok=True)
            
            output_filename = os.path.splitext(uploaded_file.name)[0] + '.tex'
            output_path = os.path.join(temp_dir, output_filename)
            
            if st.button("🚀 Конвертировать в LaTeX", type="primary"):
                with st.spinner("Конвертация документа... Пожалуйста, подождите"):
                    try:
                        convert_to_latex(docx_path, output_path, image_dir)
                        
                        st.success("✅ Конвертация завершена успешно!")
                        
                        # Предпросмотр
                        with open(output_path, 'r', encoding='utf-8') as f:
                            latex_content = f.read()
                        
                        with st.expander("🔍 Предпросмотр LaTeX кода", expanded=False):
                            st.code(latex_content, language='latex')
                        
                        # Архив
                        zip_path = os.path.join(temp_dir, 'latex_output.zip')
                        shutil.make_archive(
                            os.path.join(temp_dir, 'latex_output'),
                            'zip',
                            temp_dir,
                            '.'
                        )
                        
                        st.download_button(
                            label="📥 Скачать результат (ZIP архив)",
                            data=open(zip_path, 'rb').read(),
                            file_name='latex_output.zip',
                            mime='application/zip',
                            help="Скачать архив со всеми файлами: .tex документ и изображения"
                        )

                        st.download_button(
                            label="📄 Скачать только .tex файл",
                            data=latex_content,
                            file_name=output_filename,
                            mime='text/plain',
                            help="Скачать только LaTeX документ без изображений"
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Ошибка при конвертации: {str(e)}")
                        st.exception(e)
        
        # Информация о приложении
        with st.expander("ℹ️ Информация о конвертере"):
            st.markdown("""
            ### Возможности конвертера:
            
            - ✅ Преобразование текста с форматированием (жирный, курсив, подчеркивание)
            - ✅ Поддержка заголовков (разделы, подразделы)
            - ✅ Обработка списков (маркированных и нумерованных)
            - ✅ Конвертация таблиц с сохранением выравнивания
            - ✅ Извлечение и вставка изображений
            - ✅ Поддержка русского языка
            - ✅ Экранирование специальных символов LaTeX
            
            ### Использование:
            
            1. Загрузите ваш .docx файл
            2. Нажмите кнопку "Конвертировать в LaTeX"
            3. Скачайте результат в виде .tex файла или полного архива
            
            ### Примечания:
            
            - Для корректной работы таблиц рекомендуется использовать пакет `longtable`
            - Изображения сохраняются в отдельную папку
            - Специальные символы LaTeX автоматически экранируются
            """)

if __name__ == "__main__":
    main()