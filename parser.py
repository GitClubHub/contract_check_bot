import PyPDF2
from docx import Document

def extract_text(file_path, file_type):
    """Извлекает текст из файла"""
    
    if file_type == 'pdf':
        return extract_from_pdf(file_path)
    elif file_type in ['docx', 'doc']:
        return extract_from_docx(file_path)
    elif file_type == 'txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        raise ValueError(f"Неподдерживаемый формат: {file_type}")

def extract_from_pdf(file_path):
    """Извлекает текст из PDF"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n\n"
    except Exception as e:
        text = f"Ошибка при чтении PDF: {str(e)}"
    return text

def extract_from_docx(file_path):
    """Извлекает текст из DOCX"""
    try:
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        return f"Ошибка при чтении DOCX: {str(e)}"
