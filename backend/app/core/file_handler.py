import os
import uuid
from fastapi import HTTPException, UploadFile, status

ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a"}
ALLOWED_TRANSCRIPT_EXTENSIONS = {".txt", ".pdf", ".docx"}

BASE_UPLOAD_DIR = "/app/uploads"
AUDIO_DIR = os.path.join(BASE_UPLOAD_DIR, "audio")
TRANSCRIPT_DIR = os.path.join(BASE_UPLOAD_DIR, "transcripts")


def _get_extension(filename: str) -> str:
    return os.path.splitext(filename)[-1].lower()


def validate_audio_file(file: UploadFile) -> None:
    ext = _get_extension(file.filename or "")
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid audio file type '{ext}'. Allowed: mp3, wav, m4a.",
        )


def validate_transcript_file(file: UploadFile) -> None:
    ext = _get_extension(file.filename or "")
    if ext not in ALLOWED_TRANSCRIPT_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transcript file type '{ext}'. Allowed: txt, pdf, docx.",
        )


def save_file(file: UploadFile, directory: str) -> tuple[str, str]:
    os.makedirs(directory, exist_ok=True)
    ext = _get_extension(file.filename or "")
    unique_name = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(directory, unique_name)
    content = file.file.read()
    with open(save_path, "wb") as f:
        f.write(content)
    file.file.seek(0)
    return save_path, file.filename or unique_name


def extract_text_from_file(file: UploadFile) -> str:
    ext = _get_extension(file.filename or "")
    content = file.file.read()
    file.file.seek(0)

    if ext == ".txt":
        return content.decode("utf-8", errors="replace")
    if ext == ".pdf":
        return _extract_pdf(content)
    if ext == ".docx":
        return _extract_docx(content)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported transcript format.",
    )


def _extract_pdf(content: bytes) -> str:
    try:
        import pypdf
        import io
        reader = pypdf.PdfReader(io.BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not extract text from PDF: {exc}")


def _extract_docx(content: bytes) -> str:
    try:
        import docx
        import io
        doc = docx.Document(io.BytesIO(content))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs).strip()
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not extract text from DOCX: {exc}")
