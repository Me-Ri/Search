import g4f
import json

from .prompts import SYSTEM_PROMPT, build_user_prompt
from .parser import parse_llm_response, create_error_response


def compare_documents(template_content, document_content, model="qwen3-coder-plus"):
    user_prompt = build_user_prompt(template_content, document_content)

    try:
        response = g4f.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            provider="QwenCode",
            stream=False
        )

        response_text = response.strip() if isinstance(response, str) else str(response)

        result = parse_llm_response(response_text)

        return result

    except json.JSONDecodeError as e:
        return create_error_response(f'Ошибка парсинга JSON: {e}', response_text if 'response_text' in locals() else None)
    except Exception as e:
        return create_error_response(str(e))
