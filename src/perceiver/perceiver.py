# Standard imports
import os
import time

# Third party imports
import tiktoken

# Perceiver imports
from perceiver.factories.adapter_factory import AdapterFactory
from perceiver.utils.utils import normalize_url, compute_file_hash, get_env_variable
from perceiver.models.perception import Perception
from perceiver.utils.logger import logger

# Optional MongoDB imports
try:
    from pymongo import AsyncMongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    from beanie import init_beanie
    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False

####################################################################################################

class Perceiver:
    """
    Main Perceiver class for ingesting data sources and outputting them as text.
    
    Supports:
    - Local files (text, code, documents, images, audio)
    - URLs (YouTube, GitHub repos, generic web pages)
    - Automatic caching based on normalized URL or file hash
    """

    ####################################################################################################
    
    _beanie_initialized: bool = False

    ####################################################################################################

    async def _init_beanie(self) -> bool:
        """
        Initialize Beanie with MongoDB connection.
        
        Returns:
            bool: True if initialization succeeded, False otherwise.
        """
        if not MONGO_AVAILABLE:
            logger.debug("MongoDB libraries not installed, caching disabled")
            return False
        
        if Perceiver._beanie_initialized:
            return True
        
        try:
            mongo_uri = get_env_variable("MONGODB_URI", "mongodb://localhost:27017")
            db_name = get_env_variable("MONGODB_DB", "perceiver")
            
            client = AsyncMongoClient(mongo_uri)
            await init_beanie(database=client[db_name], document_models=[Perception])
            Perceiver._beanie_initialized = True
            logger.debug("Beanie initialized successfully")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as conn_err:
            logger.debug(f"MongoDB connection error: {conn_err}")
            return False
        except Exception as e:
            logger.debug(f"Failed to initialize MongoDB: {e}")
            return False
    
    ####################################################################################################

    async def ingest(self, source: str, bypass_cache: bool = False) -> Perception:
        """
        Ingest a data source and return its extracted content.

        Args:
            source (str): The URL or file path to ingest.
            bypass_cache (bool): If True, force re-ingestion even if cached.

        Returns:
            (Perception): The Perception document containing extracted content.
        
        Raises:
            FileNotFoundError: If a local file does not exist.
            ValueError: If the source type is not supported.
        """
        start_time = time.time()
        
        # Initialize database (gracefully handle if unavailable)
        db_available = await self._init_beanie()
        
        # Determine cache ID
        is_url = source.startswith("http://") or source.startswith("https://")
        
        if is_url:
            cache_id = normalize_url(source)
        else:
            # Expand path to absolute
            source = os.path.abspath(os.path.expanduser(source))
            if not os.path.exists(source):
                raise FileNotFoundError(f"File not found: {source}")
            cache_id = compute_file_hash(source)
        
        logger.debug(f"Cache ID: {cache_id}")
        
        # Check cache
        if not bypass_cache and db_available:
            try:
                cached = await Perception.find_one(Perception.cache_id == cache_id)
                if cached:
                    elapsed = time.time() - start_time
                    logger.info(f"Cache hit for: {source}")
                    self._log_stats(cached.contents, elapsed, cached.extraction_method, is_cache_hit = True)
                    return cached
            except Exception as e:
                logger.debug(f"Cache lookup failed: {e}")
        
        # Get appropriate adapter
        adapter, temp_file_path = await AdapterFactory.get_adapter(source)
        
        try:
            # Extract content
            extraction_source = temp_file_path if temp_file_path else source
            logger.info(f"Extracting content using {adapter.name} adapter")
            
            contents = await adapter.extract_content(extraction_source)
            
            # Create or update perception
            metadata = {
                "original_source": source,
                "is_url": is_url
            }
            
            perception = Perception(
                source=source,
                cache_id=cache_id,
                contents=contents,
                extraction_method=adapter.name,
                metadata=metadata
            )
            
            # Try to persist to database
            if db_available:
                try:
                    # Update existing or insert new
                    existing = await Perception.find_one(Perception.cache_id == cache_id)
                    if existing:
                        existing.source = source
                        existing.contents = contents
                        existing.extraction_method = adapter.name
                        existing.metadata = metadata
                        await existing.save()
                        perception = existing
                    else:
                        await perception.insert()
                except Exception as e:
                    logger.debug(f"Failed to save perception to database: {e}")
            
            elapsed = time.time() - start_time
            logger.info(f"Successfully ingested: {source}")
            self._log_stats(contents, elapsed, adapter.name, is_cache_hit = False)
            
            return perception
            
        finally:
            # Clean up temporary file if created
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    ####################################################################################################

    def _log_stats(
        self, 
        contents: str, 
        elapsed_seconds: float, 
        extraction_method: str | None,
        is_cache_hit: bool
    ) -> None:
        """
        Log statistics about the extracted content.

        Args:
            contents (str): The extracted text content.
            elapsed_seconds (float): Time taken to extract.
            extraction_method (str | None): The method used for extraction.
            is_cache_hit (bool): Whether this was a cache hit.
        """
        # Calculate stats
        num_chars = len(contents)
        num_words = len(contents.split())
        num_lines = contents.count("\n") + 1 if contents else 0
        size_mb = num_chars / (1024 * 1024)
        
        # Count tokens using tiktoken
        try:
            encoding = tiktoken.encoding_for_model("gpt-4o")
            num_tokens = len(encoding.encode(contents))
        except Exception:
            num_tokens = "N/A"
        
        source_type = "cache hit" if is_cache_hit else extraction_method or "unknown"
        
        stats = (
            f"Stats: {num_chars:,} chars | {num_words:,} words | {num_lines:,} lines | "
            f"{num_tokens:,} tokens | {size_mb:.4f} MB | {elapsed_seconds:.2f}s | "
            f"method: {source_type}"
        )
        logger.info(stats)

    ####################################################################################################

####################################################################################################
