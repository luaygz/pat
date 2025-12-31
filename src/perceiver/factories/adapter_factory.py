# Standard imports
import os
import tempfile
import aiohttp
from typing import Type
from urllib.parse import urlparse

# Perceiver imports
from perceiver.adapters.base_adapter import BaseAdapter
from perceiver.adapters.text_adapter import TextAdapter
from perceiver.adapters.document_ocr_adapter import DocumentOCRAdapter
from perceiver.adapters.image_ocr_adapter import ImageOCRAdapter
from perceiver.adapters.audio_adapter import AudioAdapter
from perceiver.adapters.youtube_adapter import YouTubeAdapter
from perceiver.adapters.github_adapter import GitHubAdapter
from perceiver.adapters.arxiv_adapter import ArxivAdapter
from perceiver.adapters.web_adapter import WebAdapter
from perceiver.utils.logger import logger

####################################################################################################

class AdapterFactory:
    """
    Factory for selecting and instantiating the appropriate adapter for a data source.
    
    The factory determines the correct adapter based on:
    1. URL patterns (for special types like YouTube, GitHub)
    2. File extensions (for local files)
    3. HTTP Content-Type headers (for URLs returning files)
    """
    
    # Default User-Agent to use for HTTP requests
    DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    
    # Ordered list of adapters to check (order matters for priority)
    # Special URL adapters come first, then file type adapters, then fallback
    ADAPTERS: list[Type[BaseAdapter]] = [
        # Special URL patterns (checked first)
        YouTubeAdapter,
        GitHubAdapter,
        ArxivAdapter,
        # File type adapters
        TextAdapter,
        DocumentOCRAdapter,
        ImageOCRAdapter,
        AudioAdapter,
        # Fallback for generic web pages (checked last)
        WebAdapter,
    ]

    ####################################################################################################

    @classmethod
    async def get_adapter(cls, source: str) -> tuple[BaseAdapter, str | None]:
        """
        Get the appropriate adapter for a data source.
        
        For URLs, this may fetch headers to determine content type.

        Args:
            source (str): The URL or file path.

        Returns:
            (tuple[BaseAdapter, str | None]): A tuple of (adapter instance, temp_file_path).
                The temp_file_path is None for local files, or the path to a downloaded
                file for URLs that need to be processed locally.
        
        Raises:
            ValueError: If no adapter supports the source.
        """
        logger.debug(f"AdapterFactory selecting adapter for: {source}")
        
        is_url = source.startswith("http://") or source.startswith("https://")
        content_type = None
        temp_file_path = None
        
        if is_url:
            # Check special URL patterns first (YouTube, GitHub, arXiv)
            for adapter_class in [YouTubeAdapter, GitHubAdapter, ArxivAdapter]:
                if adapter_class.supports_source(source):
                    logger.debug(f"Selected adapter: {adapter_class.name}")
                    return adapter_class(), None
            
            # Check if URL has a file extension that maps to a file-type adapter
            # This takes priority over content-type because URLs with extensions are explicit
            url_ext = cls._get_url_extension(source)
            
            if url_ext:
                logger.debug(f"URL has file extension: {url_ext}")
                
                # Check file-type adapters based on URL extension
                for adapter_class in [DocumentOCRAdapter, ImageOCRAdapter, AudioAdapter, TextAdapter]:
                    if adapter_class.supports_source(f"file{url_ext}"):  # Check extension support
                        # Fetch content type for download
                        content_type = await cls._fetch_content_type(source)
                        temp_file_path = await cls._download_file(source, content_type)
                        logger.debug(f"Selected adapter: {adapter_class.name} (downloaded to {temp_file_path})")
                        return adapter_class(), temp_file_path
            
            # For URLs without recognized file extensions, check content-type
            # but only for non-HTML/text content types (actual file downloads)
            content_type = await cls._fetch_content_type(source)
            logger.debug(f"URL content type: {content_type}")
            
            if content_type:
                base_content_type = content_type.split(";")[0].strip().lower()
                
                # Only use file adapters for explicit file content types
                # Exclude text/html, text/plain as these are typically web pages
                if not base_content_type.startswith("text/"):
                    for adapter_class in [DocumentOCRAdapter, ImageOCRAdapter, AudioAdapter]:
                        if adapter_class.supports_source(source, content_type):
                            temp_file_path = await cls._download_file(source, content_type)
                            logger.debug(f"Selected adapter: {adapter_class.name} (downloaded to {temp_file_path})")
                            return adapter_class(), temp_file_path
            
            # Fall back to web adapter for generic web pages
            logger.debug(f"Selected adapter: {WebAdapter.name}")
            return WebAdapter(), None
        
        else:
            # Local file - check file type adapters
            for adapter_class in [TextAdapter, DocumentOCRAdapter, ImageOCRAdapter, AudioAdapter]:
                if adapter_class.supports_source(source):
                    logger.debug(f"Selected adapter: {adapter_class.name}")
                    return adapter_class(), None
            
            # Check if it's a non-binary file without known extension
            if os.path.isfile(source):
                if not cls._is_binary(source):
                    logger.debug(f"Selected adapter: {TextAdapter.name} (unknown non-binary file)")
                    return TextAdapter(), None
                else:
                    raise ValueError(f"Binary file type not supported: {source}")
            
            raise ValueError(f"No adapter found for source: {source}")

    ####################################################################################################

    @classmethod
    def _get_url_extension(cls, url: str) -> str | None:
        """
        Extract file extension from a URL path.

        Args:
            url (str): The URL.

        Returns:
            (str | None): The file extension (with leading dot) or None if not found.
        """
        parsed = urlparse(url)
        path = parsed.path
        
        # Remove query string artifacts that might be in the path
        if "?" in path:
            path = path.split("?")[0]
        
        _, ext = os.path.splitext(path)
        
        if ext and len(ext) > 1 and len(ext) <= 10:  # Reasonable extension length
            return ext.lower()
        
        return None

    ####################################################################################################

    @classmethod
    async def _fetch_content_type(cls, url: str) -> str | None:
        """
        Fetch the Content-Type header from a URL.

        Args:
            url (str): The URL to fetch headers from.

        Returns:
            (str | None): The Content-Type header value or None.
        """
        headers = {"User-Agent": cls.DEFAULT_USER_AGENT}
        try:
            async with aiohttp.ClientSession(headers = headers) as session:
                async with session.head(url, allow_redirects = True, timeout = aiohttp.ClientTimeout(total = 30)) as response:
                    return response.headers.get("Content-Type")
        except Exception as e:
            logger.warning(f"Failed to fetch content type for {url}: {e}")
            return None

    ####################################################################################################

    @classmethod
    async def _download_file(cls, url: str, content_type: str | None) -> str:
        """
        Download a file from a URL to a temporary location.

        Args:
            url (str): The URL to download.
            content_type (str | None): The Content-Type header.

        Returns:
            (str): The path to the downloaded temporary file.
        
        Raises:
            Exception: If download fails.
        """
        # Determine file extension from URL or content type
        ext = cls._get_extension(url, content_type)
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete = False, suffix = ext)
        temp_path = temp_file.name
        temp_file.close()
        
        headers = {"User-Agent": cls.DEFAULT_USER_AGENT}
        try:
            async with aiohttp.ClientSession(headers = headers) as session:
                async with session.get(url, timeout = aiohttp.ClientTimeout(total = 300)) as response:
                    response.raise_for_status()
                    with open(temp_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(65536):
                            f.write(chunk)
            
            logger.debug(f"Downloaded file to: {temp_path}")
            return temp_path
        except Exception as e:
            # Clean up on failure
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    ####################################################################################################

    @classmethod
    def _get_extension(cls, url: str, content_type: str | None) -> str:
        """
        Determine file extension from URL or content type.

        Args:
            url (str): The URL.
            content_type (str | None): The Content-Type header.

        Returns:
            (str): The file extension (with leading dot).
        """
        # Try to get extension from URL
        parsed = urlparse(url)
        path = parsed.path
        _, ext = os.path.splitext(path)
        if ext:
            return ext.lower()
        
        # Map content types to extensions
        content_type_map = {
            "application/pdf": ".pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
            "application/epub+zip": ".epub",
            "application/vnd.oasis.opendocument.text": ".odt",
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "image/bmp": ".bmp",
            "audio/mpeg": ".mp3",
            "audio/mp3": ".mp3",
            "audio/flac": ".flac",
            "audio/wav": ".wav",
            "audio/ogg": ".ogg",
            "audio/webm": ".webm",
            "audio/mp4": ".m4a",
            "audio/m4a": ".m4a",
            "video/mp4": ".mp4",
            "video/mpeg": ".mpeg",
            "video/webm": ".webm",
            "text/plain": ".txt",
            "text/html": ".html",
        }
        
        if content_type:
            base_type = content_type.split(";")[0].strip().lower()
            if base_type in content_type_map:
                return content_type_map[base_type]
        
        return ""

    ####################################################################################################

    @classmethod
    def _is_binary(cls, file_path: str) -> bool:
        """
        Check if a file is binary.

        Args:
            file_path (str): The path to the file.

        Returns:
            (bool): True if the file is binary.
        """
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(8192)
            
            if b"\x00" in chunk:
                return True
            
            try:
                chunk.decode("utf-8")
                return False
            except UnicodeDecodeError:
                return True
        except Exception:
            return True

    ####################################################################################################

####################################################################################################

