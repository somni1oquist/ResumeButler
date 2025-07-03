import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult, AnalyzeDocumentRequest, AnalyzedDocument, DocumentPage, DocumentLine


def get_di_client() -> DocumentIntelligenceClient:
    """
    Create a Document Intelligence client using the Azure Key Credential.
    """
    load_dotenv()
    endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_API_KEY")
    
    if not endpoint or not key:
        raise ValueError("Please set the AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_KEY environment variables.")
    
    return DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

def analyze_document(di_client: DocumentIntelligenceClient, doc_path: str):

    if not os.path.exists(doc_path):
        raise FileNotFoundError(f"The document at {doc_path} does not exist.")
    
    if not os.path.isfile(doc_path):
        raise ValueError(f"The path {doc_path} is not a valid file.")
    
    poller = None
    with open(doc_path, "rb") as doc_file:
        poller = di_client.begin_analyze_document(
            "prebuilt-layout", AnalyzeDocumentRequest(bytes_source=doc_file.read())
        )

    if not poller:
        raise RuntimeError("Failed to start the document analysis.")

    result: AnalyzeResult = poller.result()
    return result

def reform_result(result: AnalyzeResult) -> str:
    """
    Reformats the AnalyzeResult into a human-readable string.
    """
    if not result or not result.pages:
        return "No documents found in the analysis result."

    text_result = []
    for page in result.pages:
        text_result.append(f"Page {page.page_number}:")
        if page.lines:
            for line in page.lines:
                text_result.append(line.content)
        if page.selection_marks:
            for mark in page.selection_marks:
                text_result.append(mark.state)
    if result.tables:
        for table_idx, table in enumerate(result.tables):
            text_result.append(f"Table {table_idx + 1}:")
            for cell in table.cells:
                text_result.append(f"Cell({cell.row_index}, {cell.column_index}): {cell.content}")
    return "\n".join(text_result)

def main():
    """
    Main function to run the document analysis.
    """
    di_client = get_di_client()
    doc_path = "Resume_July.pdf"  # Replace with your document path

    try:
        result = analyze_document(di_client, doc_path)
        formatted_result = reform_result(result)
        print(formatted_result)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()