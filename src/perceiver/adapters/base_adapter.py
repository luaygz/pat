# Standard imports
from abc import ABC, abstractmethod
from typing import ClassVar

####################################################################################################

class BaseAdapter(ABC):
    """
    Abstract base class for all adapters that extract content from data sources.
    
    Adapters are responsible for ingesting a particular data source type and
    extracting its textual content.
    
    To add a new adapter:
    1. Create a new class that inherits from BaseAdapter
    2. Implement the `extract_content` and `supports_source` methods
    3. Set the `name` class variable to identify the adapter
    4. Register the adapter in the AdapterFactory
    """
    
    name: ClassVar[str] = "base"  # Human-readable name for logging/metadata

    ####################################################################################################

    @abstractmethod
    async def extract_content(self, source: str) -> str:
        """
        Extracts textual content from the given source.

        Args:
            source (str): The URL or file path to extract content from.

        Returns:
            (str): The extracted textual content.
        
        Raises:
            Exception: If extraction fails.
        """
        pass

    ####################################################################################################

    @classmethod
    @abstractmethod
    def supports_source(cls, source: str, content_type: str | None = None) -> bool:
        """
        Checks if this adapter supports the given source.

        Args:
            source (str): The URL or file path to check.
            content_type (str | None): The HTTP Content-Type header (for URLs).

        Returns:
            (bool): True if this adapter can handle the source.
        """
        pass

    ####################################################################################################

####################################################################################################

