import sys
from pathlib import Path

# Добавляем src в путь
src_path = Path(__file__).parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from llm_pkg.comparator import compare_documents

class ComparatorService:
    @staticmethod
    def compare(
        template_content: str,
        document_content: str,
        model: str = "gpt-oss:120b-cloud",
        parallel: bool = True
    ) -> dict:
        try:
            result = compare_documents(
                template_content=template_content,
                document_content=document_content,
                model=model,
                parallel=parallel
            )
            return {"success": True, "data": result, "error": None}
        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}