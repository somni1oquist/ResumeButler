"""
Document parsing strategy pattern for Resume Butler.
Supports multiple parsing strategies with Azure Document Intelligence as primary.
"""

from abc import ABC, abstractmethod
from azure.ai.documentintelligence.models import AnalyzeResult
from streamlit.runtime.uploaded_file_manager import UploadedFile
import os
from dotenv import load_dotenv


class DocumentParserStrategy(ABC):
    """Abstract base class for document parsing strategies."""
    
    @abstractmethod
    def can_parse(self, file: UploadedFile) -> bool:
        pass
    
    @abstractmethod
    def parse(self, file: UploadedFile) -> str:
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        pass


class AzureDocumentIntelligenceParser(DocumentParserStrategy):
    """Azure Document Intelligence parser for structured document analysis."""
    
    def __init__(self):
        load_dotenv()
        self.endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        self.api_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_API_KEY")
        self._client = None
        
    def _get_client(self):
        if self._client is None:
            if not self.endpoint or not self.api_key:
                raise ValueError("Azure Document Intelligence credentials not configured")
            
            from azure.core.credentials import AzureKeyCredential
            from azure.ai.documentintelligence import DocumentIntelligenceClient
            
            self._client = DocumentIntelligenceClient(
                endpoint=self.endpoint, 
                credential=AzureKeyCredential(self.api_key)
            )
        return self._client
    
    def can_parse(self, file: UploadedFile) -> bool:
        try:
            import mimetypes
            mime_type, _ = mimetypes.guess_type(file.name)
            supported_types = {
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword",
                "image/jpeg",
                "image/png",
                "image/tiff",
                "image/bmp"
            }
            return (mime_type in supported_types and 
                    bool(self.endpoint) and 
                    bool(self.api_key))
        except Exception:
            return False
    
    def parse(self, file: UploadedFile) -> str:
        try:
            client = self._get_client()
            file.seek(0)
            file_bytes = file.read()
            from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

            poller = client.begin_analyze_document(
                "prebuilt-layout", 
                AnalyzeDocumentRequest(bytes_source=file_bytes)
            )
            result = poller.result()
            return self._format_result(result)
        except Exception as e:
            raise ValueError(f"Azure Document Intelligence parsing failed: {str(e)}")
    
    def _format_result(self, result: AnalyzeResult) -> str:
        if not result or not result.pages:
            return "No content found in document."
        
        formatted_content = []

        for page in result.pages:
            formatted_content.append(f"# Page {page.page_number}")
            if page.lines:
                for line in page.lines:
                    formatted_content.append(line.content)
            elif page.words:
                formatted_content.append("\n## Words")
                formatted_content.append(" ".join(word.content for word in page.words))
            if page.selection_marks:
                formatted_content.append("\n## Selection Marks")
                for mark in page.selection_marks:
                    formatted_content.append(f"- {mark.state}")
        
        if result.tables:
            formatted_content.append("\n## Tables")
            for table_idx, table in enumerate(result.tables):
                formatted_content.append(f"\n### Table {table_idx + 1}")
                
                table_rows = {}
                for cell in table.cells:
                    row_key = cell.row_index
                    if row_key not in table_rows:
                        table_rows[row_key] = {}
                    table_rows[row_key][cell.column_index] = cell.content
                
                for row_idx in sorted(table_rows.keys()):
                    row_cells = table_rows[row_idx]
                    row_content = " | ".join(row_cells.get(col_idx, "") for col_idx in sorted(row_cells.keys()))
                    formatted_content.append(f"| {row_content} |")

        return "\n".join(formatted_content)
    
    def get_priority(self) -> int:
        return 1


class PyMuPDFParser(DocumentParserStrategy):
    """Parser for PDF files using PyMuPDF."""
    
    def can_parse(self, file: UploadedFile) -> bool:
        try:
            import mimetypes
            mime_type, _ = mimetypes.guess_type(file.name)
            return mime_type == "application/pdf"
        except Exception:
            return False
    
    def parse(self, file: UploadedFile) -> str:
        try:
            import pymupdf4llm, pymupdf

            file.seek(0)
            file_bytes = file.read()

            with pymupdf.open(stream=file_bytes, filetype="pdf") as doc:
                md_text = pymupdf4llm.to_markdown(doc)
                if not md_text.strip():
                    raise ValueError("Failed to extract text from PDF")
                return md_text

        except Exception as e:
            raise ValueError(f"PyMuPDF parsing failed: {str(e)}")
    
    def get_priority(self) -> int:
        return 2


class DocxParser(DocumentParserStrategy):
    """Parser for Word DOCX documents."""

    def can_parse(self, file: UploadedFile) -> bool:
        try:
            import mimetypes
            file_name = getattr(file, 'name', '')
            if not file_name:
                return False
            mime_type, _ = mimetypes.guess_type(file_name)
            valid_mimes = {
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword"
            }
            return mime_type in valid_mimes or file_name.lower().endswith(".docx")
        except Exception:
            return False
    
    def parse(self, file: UploadedFile) -> str:
        try:
            import docx2txt

            file.seek(0)
            content = docx2txt.process(file)
            if not content.strip():
                raise ValueError("Empty DOCX file")
            return content

        except Exception as e:
            raise ValueError(f"DOCX parsing failed: {str(e)}")
    
    def get_priority(self) -> int:
        return 3


class TextParser(DocumentParserStrategy):
    """Parser for plain text files."""
    
    def can_parse(self, file: UploadedFile) -> bool:
        try:
            import mimetypes
            mime_type, _ = mimetypes.guess_type(file.name)
            return mime_type == "text/plain"
        except Exception:
            return False
    
    def parse(self, file: UploadedFile) -> str:
        try:
            file.seek(0)
            content = file.read().decode('utf-8').strip()
            if not content:
                raise ValueError("Empty text file")
            return content
        except Exception as e:
            raise ValueError(f"Text parsing failed: {str(e)}")
    
    def get_priority(self) -> int:
        return 4


class DocumentParserManager:
    """Manages document parsing strategies with fallback support."""
    
    def __init__(self):
        self.parsers = [
            AzureDocumentIntelligenceParser(),
            PyMuPDFParser(),
            DocxParser(),
            TextParser()
        ]
        self.parsers.sort(key=lambda p: p.get_priority())
    
    def parse_document(self, file: UploadedFile) -> str:
        errors = []
        for parser in self.parsers:
            if parser.can_parse(file):
                try:
                    result = parser.parse(file)
                    if result.strip():
                        return result
                except Exception as e:
                    errors.append(f"{parser.__class__.__name__}: {str(e)}")
        raise ValueError(f"All parsing strategies failed:\n{chr(10).join(errors) if errors else 'No parsers available for '} {file.name}")

# Global parser manager instance
_parser_manager = DocumentParserManager()


def get_parser_manager() -> DocumentParserManager:
    return _parser_manager
