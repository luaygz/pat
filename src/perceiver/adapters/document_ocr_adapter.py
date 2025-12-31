# Standard imports
import os
import re
from typing import ClassVar

# Third party imports
from mistralai import Mistral

# Perceiver imports
from perceiver.adapters.base_adapter import BaseAdapter
from perceiver.utils.utils import get_env_variable
from perceiver.utils.logger import logger

####################################################################################################

class DocumentOCRAdapter(BaseAdapter):
    """
    Adapter for extracting content from documents using Mistral AI OCR API.
    
    Supports PDF, DOCX, PPTX, EPUB, and ODT files.
    """
    
    name: ClassVar[str] = "document_ocr"
    
    # Extensions that should be processed with document OCR
    DOCUMENT_EXTENSIONS: ClassVar[set[str]] = {
        ".pdf", ".docx", ".pptx", ".epub", ".odt"
    }
    
    # Content types that map to document OCR
    DOCUMENT_CONTENT_TYPES: ClassVar[set[str]] = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/epub+zip",
        "application/vnd.oasis.opendocument.text"
    }

    ####################################################################################################

    async def extract_content(self, source: str) -> str:
        """
        Extracts content from a document using Mistral AI OCR API.

        Args:
            source (str): The path to the document file.

        Returns:
            (str): The extracted text content.
        
        Raises:
            FileNotFoundError: If the file does not exist.
            Exception: If OCR processing fails.
        """
        logger.debug(f"DocumentOCRAdapter extracting content from: {source}")
        
        if not os.path.exists(source):
            raise FileNotFoundError(f"File not found: {source}")
        
        async with Mistral(api_key = get_env_variable("MISTRAL_API_KEY")) as client:
            # Upload the document file to the Mistral API
            _, file_extension = os.path.splitext(source)
            
            logger.debug(f"Uploading document to Mistral API: {source}")
            uploaded_document = await client.files.upload_async(
                file = {
                    "file_name": "uploaded_file" + file_extension,
                    "content": open(source, "rb"),
                },
                purpose = "ocr"
            )

            # Get the URL for the uploaded document
            document_url = (
                await client.files.get_signed_url_async(file_id = uploaded_document.id)
            ).url

            # Process the document with the Mistral OCR API
            logger.debug(f"Processing document with Mistral OCR API")
            ocr_response = await client.ocr.process_async(
                model = "mistral-ocr-latest",
                document = {
                    "type": "document_url",
                    "document_url": document_url
                },
                include_image_base64 = False
            )

            text = "\n".join([page.markdown for page in ocr_response.pages])

            # Remove markdown images e.g. ![alt_text](image_path)
            text = re.sub(r'!\[.*?\]\(.*?\)', '', text)

            logger.debug(f"DocumentOCRAdapter extracted {len(text)} characters")
            return text.strip()

    ####################################################################################################

    @classmethod
    def supports_source(cls, source: str, content_type: str | None = None) -> bool:
        """
        Checks if the source is a document file suitable for OCR.

        Args:
            source (str): The file path or URL to check.
            content_type (str | None): The HTTP Content-Type header (for URLs).

        Returns:
            (bool): True if this is a document file.
        """
        # Check content type for URLs
        if content_type:
            base_content_type = content_type.split(";")[0].strip().lower()
            if base_content_type in cls.DOCUMENT_CONTENT_TYPES:
                return True
        
        # Check file extension
        _, ext = os.path.splitext(source.lower())
        return ext in cls.DOCUMENT_EXTENSIONS

    ####################################################################################################

####################################################################################################

