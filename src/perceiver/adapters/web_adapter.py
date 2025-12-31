# Standard imports
import os
from typing import ClassVar

# Third party imports
from parallel import Parallel

# Perceiver imports
from perceiver.adapters.base_adapter import BaseAdapter
from perceiver.utils.utils import get_env_variable
from perceiver.utils.logger import logger

####################################################################################################

class WebAdapter(BaseAdapter):
    """
    Adapter for extracting content from generic web pages using Parallel AI Extract API.
    
    This is the fallback adapter for URLs that don't match any other specialized adapter.
    """
    
    name: ClassVar[str] = "web"

    ####################################################################################################

    async def extract_content(self, source: str) -> str:
        """
        Extracts content from a web page using Parallel AI Extract API.

        Args:
            source (str): The URL to extract content from.

        Returns:
            (str): The extracted web page content.
        
        Raises:
            ValueError: If extraction fails.
        """
        logger.debug(f"WebAdapter extracting content from: {source}")
        
        client = Parallel(api_key = get_env_variable("PARALLEL_API_KEY"))
        
        try:
            extract = client.beta.extract(
                urls = [source],
                excerpts = False,
                full_content = True
            )
            
            # Check for errors
            if extract.errors:
                for error in extract.errors:
                    if error.url == source:
                        raise ValueError(
                            f"Failed to extract content: {error.error_type} - {error.content}"
                        )
            
            # Get the result for our URL
            for result in extract.results:
                if result.url == source:
                    content = result.full_content or ""
                    logger.debug(f"WebAdapter extracted {len(content)} characters")
                    return content.strip()
            
            raise ValueError(f"No result returned for URL: {source}")
            
        except Exception as e:
            if "Failed to extract content" in str(e):
                raise
            raise ValueError(f"Web extraction failed: {str(e)}")

    ####################################################################################################

    @classmethod
    def supports_source(cls, source: str, content_type: str | None = None) -> bool:
        """
        Checks if the source is a web URL (fallback for any HTTP/HTTPS URL).

        Args:
            source (str): The URL to check.
            content_type (str | None): The HTTP Content-Type header.

        Returns:
            (bool): True if this is an HTTP/HTTPS URL.
        """
        return source.startswith("http://") or source.startswith("https://")

    ####################################################################################################

####################################################################################################

