"""
Document parsing strategy pattern for Resume Butler.
Supports multiple parsing strategies with Azure Document Intelligence as primary.
"""

from abc import ABC, abstractmethod
from typing import Protocol, Union
from streamlit.runtime.uploaded_file_manager import UploadedFile
import os
import tempfile
from dotenv import load_dotenv


class DocumentParserStrategy(ABC):
    """Abstract base class for document parsing strategies."""
    
    @abstractmethod
    def can_parse(self, file: UploadedFile) -> bool:
        """Check if this strategy can parse the given file."""
        pass
    
    @abstractmethod
    def parse(self, file: UploadedFile) -> str:
        """Parse the document and return structured content."""
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """Get the priority of this parser (lower number = higher priority)."""
        pass


class AzureDocumentIntelligenceParser(DocumentParserStrategy):
    """Azure Document Intelligence parser for structured document analysis."""
    
    def __init__(self):
        load_dotenv()
        self.endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        self.api_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_API_KEY")
        self._client = None
        
    def _get_client(self):
        """Lazy initialization of Azure Document Intelligence client."""
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
        """Check if Azure Document Intelligence can parse this file."""
        try:
            import mimetypes
            mime_type, _ = mimetypes.guess_type(file.name)
            
            # Azure Document Intelligence supports these formats
            supported_types = [
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword",
                "image/jpeg",
                "image/png",
                "image/tiff",
                "image/bmp"
            ]
            
            return (mime_type in supported_types and 
                    self.endpoint and 
                    self.api_key)
        except Exception:
            return False
    
    def parse(self, file: UploadedFile) -> str:
        """Parse document using Azure Document Intelligence."""
        try:
            client = self._get_client()
            
            # Reset file pointer
            file.seek(0)
            file_bytes = file.read()
            
            from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
            
            # Start analysis
            poller = client.begin_analyze_document(
                "prebuilt-layout", 
                AnalyzeDocumentRequest(bytes_source=file_bytes)
            )
            
            result = poller.result()
            
            # Format the result into structured text
            return self._format_result(result)
            
        except Exception as e:
            raise ValueError(f"Azure Document Intelligence parsing failed: {str(e)}")
    
    def _format_result(self, result) -> str:
        """Format Azure Document Intelligence result into structured text."""
        if not result or not result.pages:
            return "No content found in document."
        
        formatted_content = []
        
        # Process pages
        for page in result.pages:
            formatted_content.append(f"# Page {page.page_number}")
            
            # Add lines with proper structure
            if page.lines:
                for line in page.lines:
                    formatted_content.append(line.content)
            
            # Add selection marks (checkboxes, etc.)
            if page.selection_marks:
                formatted_content.append("\n## Selection Marks")
                for mark in page.selection_marks:
                    formatted_content.append(f"- {mark.state}")
        
        # Process tables
        if result.tables:
            formatted_content.append("\n## Tables")
            for table_idx, table in enumerate(result.tables):
                formatted_content.append(f"\n### Table {table_idx + 1}")
                
                # Create a simple table representation
                table_rows = {}
                for cell in table.cells:
                    row_key = cell.row_index
                    if row_key not in table_rows:
                        table_rows[row_key] = {}
                    table_rows[row_key][cell.column_index] = cell.content
                
                # Format table
                for row_idx in sorted(table_rows.keys()):
                    row_cells = table_rows[row_idx]
                    row_content = " | ".join(row_cells.get(col_idx, "") for col_idx in sorted(row_cells.keys()))
                    formatted_content.append(f"| {row_content} |")
        
        return "\n".join(formatted_content)
    
    def get_priority(self) -> int:
        """Azure Document Intelligence has highest priority."""
        return 1


class PyMuPDFParser(DocumentParserStrategy):
    """PyMuPDF parser for PDF files (fallback)."""
    
    def can_parse(self, file: UploadedFile) -> bool:
        """Check if this is a PDF file."""
        try:
            import mimetypes
            mime_type, _ = mimetypes.guess_type(file.name)
            return mime_type == "application/pdf"
        except Exception:
            return False
    
    def parse(self, file: UploadedFile) -> str:
        """Parse PDF using PyMuPDF."""
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
        """PyMuPDF has medium priority."""
        return 2


class DocxParser(DocumentParserStrategy):
    """DOCX parser for Word documents (fallback)."""
    
    def can_parse(self, file: UploadedFile) -> bool:
        """Check if this is a DOCX file."""
        try:
            import mimetypes
            mime_type, _ = mimetypes.guess_type(file.name)
            return mime_type in [
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword"
            ]
        except Exception:
            return False
    
    def parse(self, file: UploadedFile) -> str:
        """Parse DOCX using docx2txt."""
        try:
            import docx2txt
            
            file.seek(0)
            content = docx2txt.process(file)
            if not content.strip():
                raise ValueError("Failed to extract text from DOCX")
            return content
            
        except Exception as e:
            raise ValueError(f"DOCX parsing failed: {str(e)}")
    
    def get_priority(self) -> int:
        """DOCX parser has medium priority."""
        return 3


class TextParser(DocumentParserStrategy):
    """Plain text parser (fallback)."""
    
    def can_parse(self, file: UploadedFile) -> bool:
        """Check if this is a text file."""
        try:
            import mimetypes
            mime_type, _ = mimetypes.guess_type(file.name)
            return mime_type == "text/plain"
        except Exception:
            return False
    
    def parse(self, file: UploadedFile) -> str:
        """Parse plain text file."""
        try:
            file.seek(0)
            content = file.read().decode('utf-8').strip()
            if not content:
                raise ValueError("Empty text file")
            return content
            
        except Exception as e:
            raise ValueError(f"Text parsing failed: {str(e)}")
    
    def get_priority(self) -> int:
        """Text parser has lowest priority."""
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
        # Sort by priority (lower number = higher priority)
        self.parsers.sort(key=lambda p: p.get_priority())
    
    def parse_document(self, file: UploadedFile) -> str:
        """Parse document using the best available strategy."""
        errors = []
        
        # Try each parser in priority order
        for parser in self.parsers:
            if parser.can_parse(file):
                try:
                    result = parser.parse(file)
                    if result.strip():
                        return result
                except Exception as e:
                    errors.append(f"{parser.__class__.__name__}: {str(e)}")
                    continue
        
        # If all parsers failed, raise with details
        error_msg = "All parsing strategies failed:\n" + "\n".join(errors)
        raise ValueError(error_msg)


# Global instance
_parser_manager = DocumentParserManager()


def get_parser_manager() -> DocumentParserManager:
    """Get the global document parser manager."""
    return _parser_manager