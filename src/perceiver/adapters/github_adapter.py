# Standard imports
import os
import re
import shutil
import tempfile
import subprocess
from typing import ClassVar
from urllib.parse import urlparse

# Perceiver imports
from perceiver.adapters.base_adapter import BaseAdapter
from perceiver.utils.logger import logger

####################################################################################################

class GitHubAdapter(BaseAdapter):
    """
    Adapter for extracting content from GitHub repositories.
    
    Uses git clone and Repomix to dump repository contents to markdown.
    """
    
    name: ClassVar[str] = "github"
    
    # File extensions to include in the Repomix output
    INCLUDE_EXTENSIONS: ClassVar[list[str]] = [
        "**/*.sh", "**/*.bat", "**/*.ps1", "**/*.js", "**/*.css", "**/*.ts", "**/*.jsx", "**/*.tsx",
        "**/*.py", "**/*.java", "**/*.c", "**/*.cpp", "**/*.h", "**/*.cs", "**/*.go", "**/*.rs",
        "**/*.rb", "**/*.php", "**/*.swift", "**/*.kt", "**/*.sql", 
        "**/Dockerfile", "**/Makefile", "**/README.md"
    ]

    ####################################################################################################

    async def extract_content(self, source: str) -> str:
        """
        Extracts content from a GitHub repository using git clone and Repomix.

        Args:
            source (str): The GitHub repository URL.

        Returns:
            (str): The repository contents as markdown.
        
        Raises:
            ValueError: If the URL is invalid or cloning fails.
        """
        logger.debug(f"GitHubAdapter extracting content from: {source}")
        
        # Normalize GitHub URL
        repo_url = self._normalize_github_url(source)
        if not repo_url:
            raise ValueError(f"Invalid GitHub URL: {source}")
        
        # Create a temporary directory for cloning
        temp_dir = tempfile.mkdtemp(prefix = "perceiver_github_")
        
        try:
            # Clone the repository
            clone_path = os.path.join(temp_dir, "repo")
            logger.debug(f"Cloning repository to: {clone_path}")
            
            clone_result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, clone_path],
                capture_output = True,
                text = True,
                timeout = 300  # 5 minute timeout
            )
            
            if clone_result.returncode != 0:
                raise ValueError(f"Failed to clone repository: {clone_result.stderr}")
            
            # Run Repomix on the cloned repository
            output_file = os.path.join(temp_dir, "output.md")
            include_patterns = ",".join(self.INCLUDE_EXTENSIONS)
            
            logger.debug(f"Running Repomix on cloned repository")
            
            repomix_result = subprocess.run(
                [
                    "repomix",
                    "--style", "markdown",
                    "--include", include_patterns,
                    "--no-file-summary",
                    "--output", output_file,
                    "--quiet",
                    clone_path
                ],
                capture_output = True,
                text = True,
                timeout = 300  # 5 minute timeout
            )
            
            if repomix_result.returncode != 0:
                raise ValueError(f"Failed to run Repomix: {repomix_result.stderr}")
            
            # Read the output file
            with open(output_file, "r", encoding = "utf-8") as f:
                content = f.read()
            
            logger.debug(f"GitHubAdapter extracted {len(content)} characters")
            return content.strip()
            
        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors = True)

    ####################################################################################################

    @classmethod
    def supports_source(cls, source: str, content_type: str | None = None) -> bool:
        """
        Checks if the source is a GitHub repository URL.

        Args:
            source (str): The URL to check.
            content_type (str | None): The HTTP Content-Type header (ignored for GitHub).

        Returns:
            (bool): True if this is a GitHub repository URL.
        """
        return cls._is_github_repo_url(source)

    ####################################################################################################

    @classmethod
    def _is_github_repo_url(cls, url: str) -> bool:
        """
        Check if a URL is a GitHub repository URL.

        Args:
            url (str): The URL to check.

        Returns:
            (bool): True if this is a GitHub repository URL.
        """
        parsed = urlparse(url)
        
        if "github.com" not in parsed.netloc:
            return False
        
        # Check if it looks like a repo URL (has at least owner/repo pattern)
        path_parts = [p for p in parsed.path.split("/") if p]
        
        # Must have at least owner and repo name
        if len(path_parts) < 2:
            return False
        
        # Exclude non-repo paths like /settings, /notifications, etc.
        excluded_paths = {"settings", "notifications", "pulls", "issues", "marketplace", "explore"}
        if path_parts[0] in excluded_paths:
            return False
        
        return True

    ####################################################################################################

    @classmethod
    def _normalize_github_url(cls, url: str) -> str | None:
        """
        Normalize a GitHub URL to a clonable format.

        Args:
            url (str): The GitHub URL.

        Returns:
            (str | None): The normalized clone URL or None if invalid.
        """
        parsed = urlparse(url)
        
        if "github.com" not in parsed.netloc:
            return None
        
        # Extract owner and repo from path
        path_parts = [p for p in parsed.path.split("/") if p]
        
        if len(path_parts) < 2:
            return None
        
        owner = path_parts[0]
        repo = path_parts[1]
        
        # Remove .git suffix if present
        if repo.endswith(".git"):
            repo = repo[:-4]
        
        return f"https://github.com/{owner}/{repo}.git"

    ####################################################################################################

####################################################################################################

