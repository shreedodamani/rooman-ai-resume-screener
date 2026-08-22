import os

def parse_txt(file_path):
    """Reads a plain text file."""
    for encoding in ('utf-8', 'latin-1', 'cp1252'):
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode text file {file_path} with standard encodings.")

def parse_pdf(file_path):
    """Extracts text from a PDF file using pypdf."""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError(
            "pypdf library not found! Please install it using 'pip install pypdf' "
            "to enable PDF parsing, or convert your resumes to plain text files (.txt)."
        )

    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        raise ValueError(f"Failed to parse PDF file {file_path}: {e}")

def parse_docx(file_path):
    """Extracts text from a DOCX file using python-docx."""
    try:
        import docx
    except ImportError:
        raise ImportError(
            "python-docx library not found! Please install it using 'pip install python-docx' "
            "to enable Word file parsing, or convert your resumes to plain text files (.txt)."
        )

    try:
        doc = docx.Document(file_path)
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        return "\n".join(text)
    except Exception as e:
        raise ValueError(f"Failed to parse DOCX file {file_path}: {e}")

def parse_resume(file_path):
    """Detects file type and extracts text from resume."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    _, ext = os.path.splitext(file_path.lower())
    
    if ext == '.txt':
        return parse_txt(file_path)
    elif ext == '.pdf':
        return parse_pdf(file_path)
    elif ext in ('.docx', '.doc'):
        return parse_docx(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Supported formats are .txt, .pdf, .docx")
