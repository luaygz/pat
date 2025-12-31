# Standard imports
import os
from typing import ClassVar

# Third party imports
from openai import AsyncOpenAI

# Perceiver imports
from perceiver.adapters.base_adapter import BaseAdapter
from perceiver.utils.utils import get_env_variable
from perceiver.utils.logger import logger

####################################################################################################

class AudioAdapter(BaseAdapter):
    """
    Adapter for extracting content from audio files using OpenAI Translation API.
    
    Automatically translates audio to English using Whisper.
    Supports FLAC, MP3, MP4, MPEG, MPGA, M4A, OGG, WAV, and WEBM files.
    """
    
    name: ClassVar[str] = "audio"
    
    # Extensions that should be processed with audio transcription
    AUDIO_EXTENSIONS: ClassVar[set[str]] = {
        ".flac", ".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".ogg", ".wav", ".webm"
    }
    
    # Content types that map to audio processing
    AUDIO_CONTENT_TYPES: ClassVar[set[str]] = {
        "audio/flac",
        "audio/mpeg",
        "audio/mp3",
        "audio/mp4",
        "audio/m4a",
        "audio/ogg",
        "audio/wav",
        "audio/webm",
        "video/mp4",
        "video/mpeg",
        "video/webm"
    }

    ####################################################################################################

    async def extract_content(self, source: str, model: str = "whisper-1") -> str:
        """
        Extracts content from an audio file using OpenAI Translation API.

        Args:
            source (str): The path to the audio file.
            model (str): The Whisper model to use.

        Returns:
            (str): The transcribed and translated text content.
        
        Raises:
            FileNotFoundError: If the file does not exist.
            Exception: If transcription fails.
        """
        logger.debug(f"AudioAdapter extracting content from: {source}")
        
        if not os.path.exists(source):
            raise FileNotFoundError(f"File not found: {source}")
        
        client = AsyncOpenAI(api_key = get_env_variable("OPENAI_API_KEY"))
        
        with open(source, "rb") as audio_file:
            logger.debug(f"Transcribing audio file with OpenAI Whisper API")
            
            # Use translations endpoint - automatically translates to English
            response = await client.audio.translations.create(
                model = model,
                file = audio_file,
                response_format = "text"
            )
        
        logger.debug(f"AudioAdapter extracted {len(response)} characters")
        return response.strip()

    ####################################################################################################

    @classmethod
    def supports_source(cls, source: str, content_type: str | None = None) -> bool:
        """
        Checks if the source is an audio file.

        Args:
            source (str): The file path or URL to check.
            content_type (str | None): The HTTP Content-Type header (for URLs).

        Returns:
            (bool): True if this is an audio file.
        """
        # Check content type for URLs
        if content_type:
            base_content_type = content_type.split(";")[0].strip().lower()
            if base_content_type in cls.AUDIO_CONTENT_TYPES:
                return True
        
        # Check file extension
        _, ext = os.path.splitext(source.lower())
        return ext in cls.AUDIO_EXTENSIONS

    ####################################################################################################

####################################################################################################

