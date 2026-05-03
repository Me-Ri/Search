from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
import tempfile
from pathlib import Path

from .schemas import ConvertResponse, CompareRequest, CompareResponse, HealthResponse, ErrorItem
from ..services.converter import ConverterService
from ..services.comparator import ComparatorService

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

@router.post("/api/convert", response_model=ConvertResponse)
async def convert_docx(docx_file: UploadFile = File(...)):
    if not docx_file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="Только .docx файлы")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        docx_path = Path(tmpdir) / docx_file.filename
        output_path = Path(tmpdir) / docx_file.filename.replace('.docx', '.tex')
        image_dir = Path(tmpdir) / "images"
        image_dir.mkdir(exist_ok=True)
        
        with docx_path.open("wb") as buffer:
            shutil.copyfileobj(docx_file.file, buffer)
        
        result = ConverterService.convert_docx_to_latex(
            docx_path=str(docx_path),
            output_path=str(output_path),
            image_dir=str(image_dir)
        )
        return ConvertResponse(**result)

@router.post("/api/compare", response_model=CompareResponse)
async def compare_documents(req: CompareRequest):
    try:
        result = ComparatorService.compare(
            template_content=req.template_content,
            document_content=req.document_content,
            model=req.model,
            parallel=req.parallel
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        data = result["data"]
        errors = [
            ErrorItem(
                section=err.get("section", "Общий документ"),
                error_type=err.get("error_type", "structural"),
                description=err.get("description", ""),
                severity=err.get("severity", "low")
            )
            for err in data.get("errors", [])
        ]
        
        return CompareResponse(
            errors=errors,
            compliance_score=data.get("compliance_score", 0),
            summary=data.get("summary", "")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/validate-upload")
async def validate_and_compare(
    template_file: UploadFile = File(...),
    document_file: UploadFile = File(...),
    model: str = "gpt-oss:120b-cloud"
):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        image_dir = tmpdir / "images"
        image_dir.mkdir(exist_ok=True)
        
        # Сохраняем файлы
        tpl_path = tmpdir / f"tpl_{template_file.filename}"
        doc_path = tmpdir / f"doc_{document_file.filename}"
        
        with tpl_path.open("wb") as f:
            shutil.copyfileobj(template_file.file, f)
        with doc_path.open("wb") as f:
            shutil.copyfileobj(document_file.file, f)
        
        # Конвертируем
        tpl_tex = tmpdir / "template.tex"
        doc_tex = tmpdir / "document.tex"
        
        tpl_res = ConverterService.convert_docx_to_latex(str(tpl_path), str(tpl_tex), str(image_dir))
        doc_res = ConverterService.convert_docx_to_latex(str(doc_path), str(doc_tex), str(image_dir))
        
        if not tpl_res["success"]:
            raise HTTPException(status_code=500, detail=f"Шаблон: {tpl_res['error']}")
        if not doc_res["success"]:
            raise HTTPException(status_code=500, detail=f"Документ: {doc_res['error']}")
        
        # Сравниваем
        result = ComparatorService.compare(
            template_content=tpl_res["latex_content"],
            document_content=doc_res["latex_content"],
            model=model
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        data = result["data"]
        errors = [
            ErrorItem(
                section=err.get("section", "Общий документ"),
                error_type=err.get("error_type", "structural"),
                description=err.get("description", ""),
                severity=err.get("severity", "low")
            )
            for err in data.get("errors", [])
        ]
        
        return CompareResponse(
            errors=errors,
            compliance_score=data.get("compliance_score", 0),
            summary=data.get("summary", "")
        )