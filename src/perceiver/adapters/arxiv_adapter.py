# Standard imports
import os
import re
import tempfile
import aiohttp
from typing import ClassVar

# Perceiver imports
from perceiver.adapters.document_ocr_adapter import DocumentOCRAdapter
from perceiver.adapters.base_adapter import BaseAdapter
from perceiver.utils.logger import logger

####################################################################################################

class ArxivAdapter(BaseAdapter):
    """
    Adapter for extracting content from arXiv papers.
    
    Handles URLs in the following formats:
    - https://arxiv.org/pdf/2308.09687
    - https://arxiv.org/abs/2308.09687
    - https://arxiv.org/html/2308.09687
    
    Downloads the PDF version and processes it using Mistral OCR.
    """
    
    name: ClassVar[str] = "arxiv"
    
    # Default User-Agent to use for HTTP requests
    DEFAULT_USER_AGENT: ClassVar[str] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    
    # Pattern to match arXiv URLs and extract the paper ID
    ARXIV_PATTERN: ClassVar[re.Pattern] = re.compile(
        r"arxiv\.org/(?:pdf|abs|html)/(\d+\.\d+(?:v\d+)?)"
    )

    ####################################################################################################

    async def extract_content(self, source: str) -> str:
        """
        Extracts content from an arXiv paper by downloading the PDF and OCR processing it.

        Args:
            source (str): The arXiv URL (pdf, abs, or html format).

        Returns:
            (str): The extracted text content from the paper.
        
        Raises:
            ValueError: If the URL is invalid or download fails.
        """
        logger.debug(f"ArxivAdapter extracting content from: {source}")
        
        # Extract paper ID from URL
        paper_id = self._extract_paper_id(source)
        if not paper_id:
            raise ValueError(f"Could not extract arXiv paper ID from URL: {source}")
        
        logger.debug(f"Extracted arXiv paper ID: {paper_id}")
        
        # Construct PDF URL
        pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"
        logger.debug(f"Downloading PDF from: {pdf_url}")
        
        # Download PDF to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete = False, suffix = ".pdf")
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            await self._download_pdf(pdf_url, temp_path)
            
            # Use DocumentOCRAdapter to process the PDF
            document_adapter = DocumentOCRAdapter()
            content = await document_adapter.extract_content(temp_path)
            
            logger.debug(f"ArxivAdapter extracted {len(content)} characters")
            return content
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    ####################################################################################################

    async def _download_pdf(self, url: str, dest_path: str) -> None:
        """
        Download a PDF from arXiv.

        Args:
            url (str): The PDF URL.
            dest_path (str): The destination file path.
        
        Raises:
            Exception: If download fails.
        """
        headers = {"User-Agent": self.DEFAULT_USER_AGENT}
        
        async with aiohttp.ClientSession(headers = headers) as session:
            async with session.get(url, timeout = aiohttp.ClientTimeout(total = 300)) as response:
                response.raise_for_status()
                
                with open(dest_path, "wb") as f:
                    async for chunk in response.content.iter_chunked(65536):
                        f.write(chunk)
        
        logger.debug(f"Downloaded arXiv PDF to: {dest_path}")

    ####################################################################################################

    @classmethod
    def supports_source(cls, source: str, content_type: str | None = None) -> bool:
        """
        Checks if the source is an arXiv URL.

        Args:
            source (str): The URL to check.
            content_type (str | None): The HTTP Content-Type header (ignored for arXiv).

        Returns:
            (bool): True if this is an arXiv URL.
        """
        return cls._is_arxiv_url(source)

    ####################################################################################################

    @classmethod
    def _is_arxiv_url(cls, url: str) -> bool:
        """
        Check if a URL is an arXiv paper URL.

        Args:
            url (str): The URL to check.

        Returns:
            (bool): True if this is an arXiv URL.
        """
        return bool(cls.ARXIV_PATTERN.search(url))

    ####################################################################################################

    @classmethod
    def _extract_paper_id(cls, url: str) -> str | None:
        """
        Extract the paper ID from an arXiv URL.

        Args:
            url (str): The arXiv URL.

        Returns:
            (str | None): The paper ID or None if not found.
        """
        match = cls.ARXIV_PATTERN.search(url)
        if match:
            return match.group(1)
        return None

    ####################################################################################################

####################################################################################################

