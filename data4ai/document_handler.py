"""Document file operations for Data4AI - Extract and process PDF, DOCX, MD, and TXT files."""

import logging
import re
from pathlib import Path
from typing import Any, Optional

from data4ai.exceptions import ValidationError

logger = logging.getLogger("data4ai")

# Check for optional dependencies
try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False


class DocumentHandler:
    """Handle document file operations for dataset generation."""

    @staticmethod
    def detect_document_type(file_path: Path) -> str:
        """Detect document type from file extension.
        
        Args:
            file_path: Path to document file
            
        Returns:
            Document type (pdf, docx, md, txt)
            
        Raises:
            ValidationError: If file type is not supported
        """
        suffix = file_path.suffix.lower()
        
        if suffix == ".pdf":
            return "pdf"
        elif suffix in [".docx", ".doc"]:
            return "docx"
        elif suffix in [".md", ".markdown"]:
            return "md"
        elif suffix in [".txt", ".text"]:
            return "txt"
        else:
            raise ValidationError(
                f"Unsupported document type: {suffix}. "
                "Supported types: .pdf, .docx, .md, .txt"
            )

    @staticmethod
    def extract_text(file_path: Path, use_advanced: bool = False) -> str:
        """Extract text from document file.
        
        Args:
            file_path: Path to document file
            use_advanced: Use advanced extraction (pdfplumber for PDFs)
            
        Returns:
            Extracted text content
            
        Raises:
            ValidationError: If extraction fails or dependencies missing
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
            
        doc_type = DocumentHandler.detect_document_type(file_path)
        
        if doc_type == "pdf":
            return DocumentHandler._extract_pdf_text(file_path, use_advanced)
        elif doc_type == "docx":
            return DocumentHandler._extract_docx_text(file_path)
        elif doc_type == "md":
            return DocumentHandler._extract_markdown_text(file_path)
        elif doc_type == "txt":
            return DocumentHandler._extract_txt_text(file_path)
        else:
            raise ValidationError(f"Unsupported document type: {doc_type}")

    @staticmethod
    def _extract_pdf_text(file_path: Path, use_advanced: bool = False) -> str:
        """Extract text from PDF file.
        
        Args:
            file_path: Path to PDF file
            use_advanced: Use pdfplumber for better extraction
            
        Returns:
            Extracted text
        """
        if use_advanced and PDFPLUMBER_AVAILABLE:
            logger.info("Using pdfplumber for advanced PDF extraction")
            try:
                import pdfplumber
                text_parts = []
                
                with pdfplumber.open(file_path) as pdf:
                    for page_num, page in enumerate(pdf.pages, 1):
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(f"--- Page {page_num} ---\n{page_text}")
                            
                return "\n\n".join(text_parts)
            except Exception as e:
                logger.warning(f"pdfplumber extraction failed: {e}, falling back to pypdf")
                # Fall back to pypdf
                
        if not PYPDF_AVAILABLE:
            raise ValidationError(
                "PDF support not available. Please install with: "
                "pip install data4ai[docs] or pip install pypdf"
            )
            
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            text_parts = []
            
            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"--- Page {page_num} ---\n{page_text}")
                    
            return "\n\n".join(text_parts)
        except Exception as e:
            raise ValidationError(f"Failed to extract PDF text: {str(e)}") from e

    @staticmethod
    def _extract_docx_text(file_path: Path) -> str:
        """Extract text from DOCX file.
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Extracted text
        """
        if not DOCX_AVAILABLE:
            raise ValidationError(
                "DOCX support not available. Please install with: "
                "pip install data4ai[docs] or pip install python-docx"
            )
            
        try:
            doc = Document(file_path)
            paragraphs = []
            
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text)
                    
            # Also extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells)
                    if row_text.strip():
                        paragraphs.append(row_text)
                        
            return "\n\n".join(paragraphs)
        except Exception as e:
            raise ValidationError(f"Failed to extract DOCX text: {str(e)}") from e

    @staticmethod
    def _extract_markdown_text(file_path: Path) -> str:
        """Extract text from Markdown file.
        
        Args:
            file_path: Path to Markdown file
            
        Returns:
            Plain text (with markdown stripped if library available)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            if MARKDOWN_AVAILABLE:
                # Convert markdown to HTML then strip tags
                import markdown
                from html.parser import HTMLParser
                
                class HTMLStripper(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.reset()
                        self.strict = False
                        self.convert_charrefs = True
                        self.text = []
                        
                    def handle_data(self, data):
                        self.text.append(data)
                        
                    def get_text(self):
                        return "".join(self.text)
                
                html = markdown.markdown(content)
                stripper = HTMLStripper()
                stripper.feed(html)
                return stripper.get_text()
            else:
                # Basic markdown stripping
                # Remove code blocks
                content = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
                content = re.sub(r"`[^`]+`", "", content)
                # Remove headers
                content = re.sub(r"^#+\s+", "", content, flags=re.MULTILINE)
                # Remove emphasis
                content = re.sub(r"[*_]{1,2}([^*_]+)[*_]{1,2}", r"\1", content)
                # Remove links
                content = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", content)
                # Remove images
                content = re.sub(r"!\[([^\]]*)\]\([^)]+\)", "", content)
                
                return content
        except Exception as e:
            raise ValidationError(f"Failed to extract Markdown text: {str(e)}") from e

    @staticmethod
    def _extract_txt_text(file_path: Path) -> str:
        """Extract text from TXT file.
        
        Args:
            file_path: Path to TXT file
            
        Returns:
            File content
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    return f.read()
            except Exception as e:
                raise ValidationError(f"Failed to extract text: {str(e)}") from e
        except Exception as e:
            raise ValidationError(f"Failed to extract text: {str(e)}") from e

    @staticmethod
    def extract_chunks(
        file_path: Path,
        chunk_size: int = 1000,
        overlap: int = 200,
        use_advanced: bool = False
    ) -> list[dict[str, Any]]:
        """Extract text in chunks for processing.
        
        Args:
            file_path: Path to document file
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks for context
            use_advanced: Use advanced extraction
            
        Returns:
            List of chunks with metadata
        """
        text = DocumentHandler.extract_text(file_path, use_advanced)
        
        if not text:
            return []
            
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            
            # Try to find a good break point (sentence end)
            if end < len(text):
                # Look for sentence endings
                for sep in [".\n", ". ", "!\n", "! ", "?\n", "? "]:
                    last_sep = text.rfind(sep, start, end)
                    if last_sep != -1:
                        end = last_sep + len(sep)
                        break
                        
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunks.append({
                    "id": chunk_id,
                    "text": chunk_text,
                    "start": start,
                    "end": end,
                    "source": file_path.name,
                })
                chunk_id += 1
                
            # Move start position with overlap
            start = end - overlap if end < len(text) else end
            
        logger.info(f"Extracted {len(chunks)} chunks from {file_path.name}")
        return chunks

    @staticmethod
    def prepare_for_generation(
        file_path: Path,
        extraction_type: str = "qa",
        chunk_size: int = 1000,
        use_advanced: bool = False
    ) -> dict[str, Any]:
        """Prepare document for dataset generation.
        
        Args:
            file_path: Path to document file
            extraction_type: Type of extraction (qa, summary, instruction)
            chunk_size: Size of chunks for processing
            use_advanced: Use advanced extraction
            
        Returns:
            Prepared data for generation
        """
        doc_type = DocumentHandler.detect_document_type(file_path)
        chunks = DocumentHandler.extract_chunks(
            file_path, chunk_size=chunk_size, use_advanced=use_advanced
        )
        
        return {
            "document_type": doc_type,
            "document_name": file_path.name,
            "extraction_type": extraction_type,
            "chunks": chunks,
            "total_chunks": len(chunks),
            "metadata": {
                "chunk_size": chunk_size,
                "file_size": file_path.stat().st_size,
                "advanced_extraction": use_advanced,
            }
        }