"""PDF utility functions for creating download links"""
import base64
from typing import BinaryIO


def get_pdf_download_link(pdf_bytes: bytes, filename: str, text: str) -> str:
    """
    Generate a download link for the PDF report
    
    Args:
        pdf_bytes: PDF content as bytes
        filename: Name for the downloaded file
        text: Link text to display
        
    Returns:
        str: HTML download link
    """
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" class="download-button">{text}</a>'
    return href