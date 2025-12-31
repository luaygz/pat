# Standard imports
import os
from typing import ClassVar

# Perceiver imports
from perceiver.adapters.base_adapter import BaseAdapter
from perceiver.utils.logger import logger

####################################################################################################

class TextAdapter(BaseAdapter):
    """
    Adapter for extracting content from plain text and code files.
    
    Returns raw file contents for text-based files like .txt, .md, .py, .js, etc.
    Also handles files without known extensions if they are not binary.
    """
    
    name: ClassVar[str] = "text"
    
    # Extensions that should be read as raw text
    TEXT_EXTENSIONS: ClassVar[set[str]] = {
        ".txt", ".md", ".sh", ".bat", ".ps1", ".js", ".css", ".ts", ".jsx", ".tsx",
        ".py", ".java", ".c", ".cpp", ".h", ".cs", ".go", ".rs", ".rb", ".php",
        ".swift", ".kt", ".json", ".yaml", ".yml", ".xml", ".sql", ".env",
        ".html", ".htm", ".csv", ".log", ".ini", ".cfg", ".conf", ".toml",
        ".rst", ".tex", ".r", ".scala", ".groovy", ".pl", ".pm", ".lua",
        ".vim", ".zsh", ".bash", ".fish", ".awk", ".sed"
    }
    
    # Filenames without extensions that should be treated as text
    TEXT_FILENAMES: ClassVar[set[str]] = {
        "dockerfile", "makefile", "gemfile", "rakefile", "procfile",
        "vagrantfile", "jenkinsfile", "readme", "license", "changelog",
        "authors", "contributors", "copying", "install", "news", "todo",
        ".gitignore", ".gitattributes", ".dockerignore", ".editorconfig",
        ".eslintrc", ".prettierrc", ".babelrc", ".npmrc", ".yarnrc",
        ".env.example", ".env.local", ".env.development", ".env.production"
    }

    ####################################################################################################

    async def extract_content(self, source: str) -> str:
        """
        Extracts content from a text or code file.

        Args:
            source (str): The path to the text file.

        Returns:
            (str): The raw file contents.
        
        Raises:
            FileNotFoundError: If the file does not exist.
            UnicodeDecodeError: If the file cannot be decoded as text.
        """
        logger.debug(f"TextAdapter extracting content from: {source}")
        
        if not os.path.exists(source):
            raise FileNotFoundError(f"File not found: {source}")
        
        # Try to read as UTF-8 first, then fall back to other encodings
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        
        for encoding in encodings:
            try:
                with open(source, "r", encoding = encoding) as f:
                    content = f.read()
                logger.debug(f"TextAdapter successfully read file with {encoding} encoding")
                return content
            except UnicodeDecodeError:
                continue
        
        raise UnicodeDecodeError(
            "utf-8", b"", 0, 1,
            f"Could not decode file {source} with any supported encoding"
        )

    ####################################################################################################

    @classmethod
    def supports_source(cls, source: str, content_type: str | None = None) -> bool:
        """
        Checks if the source is a text or code file.

        Args:
            source (str): The file path to check.
            content_type (str | None): The HTTP Content-Type header (for URLs).

        Returns:
            (bool): True if this is a text file.
        """
        # Check if it's a URL (we only handle local files)
        if source.startswith("http://") or source.startswith("https://"):
            # For URLs, check content type
            if content_type and content_type.startswith("text/"):
                return True
            return False
        
        # Check extension
        _, ext = os.path.splitext(source.lower())
        if ext in cls.TEXT_EXTENSIONS:
            return True
        
        # Check filename
        basename = os.path.basename(source.lower())
        if basename in cls.TEXT_FILENAMES:
            return True
        
        # For files without known extensions, check if they're binary
        if os.path.isfile(source) and not ext:
            return not cls._is_binary(source)
        
        return False

    ####################################################################################################

    @classmethod
    def _is_binary(cls, file_path: str) -> bool:
        """
        Check if a file is binary by reading its first few bytes.

        Args:
            file_path (str): The path to the file.

        Returns:
            (bool): True if the file appears to be binary.
        """
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(8192)
            
            # Check for null bytes (common in binary files)
            if b"\x00" in chunk:
                return True
            
            # Try to decode as UTF-8
            try:
                chunk.decode("utf-8")
                return False
            except UnicodeDecodeError:
                return True
        except Exception:
            return True

    ####################################################################################################

####################################################################################################

