# Standard imports
from uuid import uuid4
from datetime import datetime, timezone
from typing import Optional

# Third party imports
from pydantic import Field
from beanie import Document

####################################################################################################

class Perception(Document):
    """
    A Perception represents ingested/extracted text content from a data source.
    
    Used to cache extracted content from URLs and files to avoid re-extraction.
    The cache_id is used to check for cache hits:
    - For URLs: normalized URL (stripped of fragments, trailing slashes, sorted query params)
    - For files: file hash (using xxhash for speed, fallback to sha256)
    """
    id: str = Field(default_factory = lambda: str(uuid4()))
    timestamp: str = Field(default_factory = lambda: str(datetime.now(timezone.utc)))
    source: str  # The original URL or file path
    cache_id: str  # The ID used to check for cache hits (normalized URL or file hash)
    contents: str  # The extracted text content
    extraction_method: Optional[str] = None  # The method used to extract the content
    metadata: Optional[dict] = None  # Additional metadata about the extraction

    class Settings:
        name = "perceptions"
        validate_on_save = True

    ####################################################################################################

####################################################################################################
