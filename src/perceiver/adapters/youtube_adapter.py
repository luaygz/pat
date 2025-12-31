# Standard imports
import re
from typing import ClassVar
from urllib.parse import urlparse, parse_qs

# Third party imports
from youtube_transcript_api import YouTubeTranscriptApi

# Perceiver imports
from perceiver.adapters.base_adapter import BaseAdapter
from perceiver.utils.logger import logger

####################################################################################################

class YouTubeAdapter(BaseAdapter):
    """
    Adapter for extracting transcripts from YouTube videos.
    
    Uses youtube-transcript-api to fetch video transcripts.
    """
    
    name: ClassVar[str] = "youtube"

    ####################################################################################################

    async def extract_content(self, source: str) -> str:
        """
        Extracts transcript from a YouTube video.

        Args:
            source (str): The YouTube video URL.

        Returns:
            (str): The video transcript.
        
        Raises:
            ValueError: If the URL is invalid or transcript is unavailable.
        """
        logger.debug(f"YouTubeAdapter extracting transcript from: {source}")
        
        video_id = self._extract_video_id(source)
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {source}")
        
        logger.debug(f"Extracted video ID: {video_id}")
        
        try:
            ytt_api = YouTubeTranscriptApi()
            
            # Try to fetch English transcript first
            try:
                fetched_transcript = ytt_api.fetch(video_id, languages = ["en", "en-US", "en-GB"])
            except Exception:
                # If English not available, get any available transcript
                logger.debug("English transcript not available, fetching any available language")
                fetched_transcript = ytt_api.fetch(video_id)
            
            # Join all transcript snippets into a single text
            transcript_text = " ".join([snippet.text.strip() for snippet in fetched_transcript if snippet.text.strip()])
            
            logger.debug(f"YouTubeAdapter extracted {len(transcript_text)} characters")
            return transcript_text.strip()
            
        except Exception as e:
            raise ValueError(f"Failed to fetch YouTube transcript: {str(e)}")

    ####################################################################################################

    @classmethod
    def supports_source(cls, source: str, content_type: str | None = None) -> bool:
        """
        Checks if the source is a YouTube video URL.

        Args:
            source (str): The URL to check.
            content_type (str | None): The HTTP Content-Type header (ignored for YouTube).

        Returns:
            (bool): True if this is a YouTube URL.
        """
        return cls._is_youtube_url(source)

    ####################################################################################################

    @classmethod
    def _is_youtube_url(cls, url: str) -> bool:
        """
        Check if a URL is a YouTube video URL.

        Args:
            url (str): The URL to check.

        Returns:
            (bool): True if this is a YouTube URL.
        """
        youtube_patterns = [
            r"(youtube\.com/watch\?v=)",
            r"(youtube\.com/embed/)",
            r"(youtube\.com/v/)",
            r"(youtu\.be/)",
            r"(youtube\.com/shorts/)"
        ]
        
        for pattern in youtube_patterns:
            if re.search(pattern, url):
                return True
        
        return False

    ####################################################################################################

    @classmethod
    def _extract_video_id(cls, url: str) -> str | None:
        """
        Extract the video ID from a YouTube URL.

        Args:
            url (str): The YouTube URL.

        Returns:
            (str | None): The video ID or None if not found.
        """
        parsed = urlparse(url)
        
        # Handle youtu.be short URLs
        if "youtu.be" in parsed.netloc:
            return parsed.path.lstrip("/").split("/")[0]
        
        # Handle youtube.com URLs
        if "youtube.com" in parsed.netloc:
            # Handle /watch?v= format
            if parsed.path == "/watch":
                query_params = parse_qs(parsed.query)
                return query_params.get("v", [None])[0]
            
            # Handle /embed/, /v/, /shorts/ formats
            path_patterns = ["/embed/", "/v/", "/shorts/"]
            for pattern in path_patterns:
                if pattern in parsed.path:
                    return parsed.path.split(pattern)[1].split("/")[0].split("?")[0]
        
        return None

    ####################################################################################################

####################################################################################################

