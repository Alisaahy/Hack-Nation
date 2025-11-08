"""
PDF Parser Utility
Extracts text from PDF files
"""

import PyPDF2
import re


def extract_text_from_pdf(filepath):
    """
    Extract text from PDF file

    Args:
        filepath: Path to PDF file

    Returns:
        Extracted text as string, or None if extraction fails
    """
    try:
        text = ""

        with open(filepath, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)

            # Extract text from all pages
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"

        # Clean up text
        text = clean_text(text)

        return text if text.strip() else None

    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return None


def clean_text(text):
    """
    Clean extracted text by removing extra whitespace and fixing common issues

    Args:
        text: Raw extracted text

    Returns:
        Cleaned text
    """
    # Remove multiple spaces
    text = re.sub(r' +', ' ', text)

    # Remove multiple newlines (keep max 2)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Fix hyphenated words at line breaks
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

    # Remove page numbers (simple pattern)
    text = re.sub(r'\n\d+\n', '\n', text)

    return text.strip()


def extract_metadata(filepath):
    """
    Extract PDF metadata (title, author, etc.)

    Args:
        filepath: Path to PDF file

    Returns:
        Dictionary of metadata
    """
    try:
        with open(filepath, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            metadata = pdf_reader.metadata

            return {
                'title': metadata.get('/Title', ''),
                'author': metadata.get('/Author', ''),
                'subject': metadata.get('/Subject', ''),
                'creator': metadata.get('/Creator', ''),
                'producer': metadata.get('/Producer', ''),
                'num_pages': len(pdf_reader.pages)
            }
    except Exception as e:
        print(f"Error extracting PDF metadata: {e}")
        return {}
