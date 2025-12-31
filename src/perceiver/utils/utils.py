# Standard imports
import os
import hashlib
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

# Third party imports
from dotenv import load_dotenv

# Perceiver imports
from perceiver.utils.logger import logger

####################################################################################################

def normalize_url(url: str) -> str:
    """
    Normalize a URL for cache key generation.
    
    Strips non-essential parts like fragments, trailing slashes, and 
    normalizes query parameters.

    Args:
        url (str): The URL to normalize.

    Returns:
        (str): The normalized URL suitable for use as a cache key.
    """
    parsed = urlparse(url)
    
    # Normalize scheme to lowercase
    scheme = parsed.scheme.lower()
    
    # Normalize netloc to lowercase
    netloc = parsed.netloc.lower()
    
    # Remove default ports
    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    elif netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]
    
    # Normalize path - remove trailing slashes (except for root)
    path = parsed.path
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    
    # Sort query parameters for consistent ordering
    query_params = parse_qs(parsed.query, keep_blank_values = True)
    sorted_query = urlencode(
        sorted([(k, v[0] if len(v) == 1 else v) for k, v in query_params.items()]),
        doseq = True
    )
    
    # Rebuild URL without fragment
    normalized = urlunparse((
        scheme,
        netloc,
        path,
        "",  # params
        sorted_query,
        ""  # fragment (stripped)
    ))
    
    return normalized

####################################################################################################

def compute_file_hash(file_path: str, algorithm: str = "xxhash") -> str:
    """
    Compute a hash of a file for cache key generation.
    
    Uses xxhash by default for speed, falls back to SHA-256 if xxhash is not available.

    Args:
        file_path (str): The path to the file.
        algorithm (str): The hash algorithm to use ("xxhash" or "sha256").

    Returns:
        (str): The hex digest of the file hash.
    
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if algorithm == "xxhash":
        try:
            import xxhash
            hasher = xxhash.xxh64()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except ImportError:
            # Fall back to SHA-256 if xxhash is not available
            logger.warning(f"xxhash is not available, falling back to sha256")
            algorithm = "sha256"
    
    if algorithm == "sha256":
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    raise ValueError(f"Unsupported hash algorithm: {algorithm}")

####################################################################################################


def get_env_variable(variable_name: str, default_value: str = None) -> str:
    """
    Get an environment variable from the .env file.
    
    Args:
        variable_name (str): The name of the environment variable to get.
        default_value (str): The default value to return if the environment variable is not set.
        
    Returns:
        (str): The environment variable value.
    """
    load_dotenv()
    return os.getenv(variable_name, default_value)

####################################################################################################