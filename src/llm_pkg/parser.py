import json


def parse_llm_response(response_text: str) -> dict:
    if response_text.startswith('```json'):
        response_text = response_text[7:]
    if response_text.startswith('```'):
        response_text = response_text[3:]
    if response_text.endswith('```'):
        response_text = response_text[:-3]

    response_text = response_text.strip()

    result = json.loads(response_text.strip())

    return result


def create_error_response(error_message: str, raw_response: str = None) -> dict:
    return {
        'error': error_message,
        'raw_response': raw_response,
        'errors': [],
        'compliance_score': 0,
        'summary': 'Ошибка при анализе документа'
    }
