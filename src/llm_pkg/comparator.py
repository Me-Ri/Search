import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from .prompts import SYSTEM_PROMPT, build_user_prompt
from .parser import parse_llm_response, create_error_response


def _run_single_check(template: str, document: str, check_type: str, model: str, url: str) -> dict:
    user_prompt = build_user_prompt(template, document, check_type=check_type)
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        if not response.ok:
            return {"check_type": check_type, "error": f"HTTP {response.status_code}", "data": None}
        
        response_data = response.json()
        response_text = response_data.get("message", {}).get("content", "").strip()
        
        if not response_text:
            return {"check_type": check_type, "error": "Пустой ответ", "data": None}
        
        parsed = parse_llm_response(response_text)
        return {"check_type": check_type, "error": None, "data": parsed}
        
    except Exception as e:
        return {"check_type": check_type, "error": str(e), "data": None}


def _merge_results(structure: dict, content: dict, formatting: dict) -> dict:
    all_errors = []
    scores = {"structure": 100, "content": 100, "formatting": 100}
    summaries = []
    
    for result in [structure, content, formatting]:
        check_type = result["check_type"]
        
        if result["error"]:
            all_errors.append({
                "section": "Общий документ",
                "error_type": "structural" if check_type == "structure" else ("content" if check_type == "content" else "formatting"),
                "description": f"Ошибка проверки {check_type}: {result['error']}",
                "severity": "high"
            })
            scores[check_type] = 50
            summaries.append(f"{check_type}: ошибка запроса")
        elif result["data"]:
            data = result["data"]
            if isinstance(data, dict) and "errors" in data:
                all_errors.extend(data["errors"])
                scores[check_type] = data.get("compliance_score", 100)
                summaries.append(f"{check_type}: {data.get('summary', 'OK')}")
            else:
                scores[check_type] = 0
                summaries.append(f"{check_type}: некорректный формат ответа")
        else:
            scores[check_type] = 0
            summaries.append(f"{check_type}: нет данных")
    
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    all_errors.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 4))
    
    fmt_summary = next((s for s in summaries if "formatting:" in s.lower()), "")
    if "не проверено" in fmt_summary.lower() or "нет данных" in fmt_summary.lower():
        final_score = round(scores["structure"] * 0.5 + scores["content"] * 0.5)
    else:
        final_score = round(
            scores["structure"] * 0.4 + 
            scores["content"] * 0.4 + 
            scores["formatting"] * 0.2
        )
    
    return {
        "errors": all_errors,
        "compliance_score": final_score,
        "summary": " | ".join(summaries)
    }


def compare_documents(template_content, document_content, model="gpt-oss:120b-cloud", parallel: bool = True):
    url = "http://localhost:11434/api/chat"
    check_types = ["structure", "content", "formatting"]
    
    if parallel:
        results = {}
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_check = {
                executor.submit(_run_single_check, template_content, document_content, ct, model, url): ct 
                for ct in check_types
            }
            for future in as_completed(future_to_check):
                result = future.result()
                results[result["check_type"]] = result
    else:
        results = {}
        for ct in check_types:
            results[ct] = _run_single_check(template_content, document_content, ct, model, url)
    
    return _merge_results(
        structure=results.get("structure", {"check_type": "structure", "error": "Не выполнено", "data": None}),
        content=results.get("content", {"check_type": "content", "error": "Не выполнено", "data": None}),
        formatting=results.get("formatting", {"check_type": "formatting", "error": "Не выполнено", "data": None})
    )