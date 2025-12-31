# Standard imports
import os
from typing import Optional
from datetime import datetime
import inspect

# Third-party imports
from colorama import Fore, Style

####################################################################################################

class Logger:

    LEVEL_HIERARCHY = {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50,
        "NONE": 60,
    }
    
    LEVELS_COLORS = {
        "DEBUG": Fore.CYAN + Style.BRIGHT,
        "INFO": Fore.GREEN + Style.BRIGHT,
        "WARNING": Fore.YELLOW + Style.BRIGHT,
        "ERROR": Fore.RED + Style.BRIGHT,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }

    TIMESTAMP_COLOR = Fore.LIGHTBLUE_EX + Style.BRIGHT
    CALLER_COLOR = Fore.LIGHTMAGENTA_EX + Style.BRIGHT
    MESSAGE_COLOR = Style.BRIGHT
    
    ####################################################################################################
    
    _instance: Optional["Logger"] = None
    _initialized: bool = False

    ####################################################################################################

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    ####################################################################################################

    def __init__(self, log_level: str = "DEBUG"):
        if not self._initialized:
            self.log_level = log_level
            self._initialized = True

    ####################################################################################################

    def set_log_level(self, level: str):
        """
        Set the minimum log level for messages to be displayed.
        
        Args:
            level (str): The minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        if level in self.LEVEL_HIERARCHY:
            self.log_level = level
        else:
            raise ValueError(f"Invalid log level: {level}. Valid levels are: {list(self.LEVEL_HIERARCHY.keys())}")
    
    ####################################################################################################
    
    def _should_log(self, level: str):
        """
        Check if a message at the given level should be logged based on current LOG_LEVEL.
        
        Args:
            level (str): The log level to check
            
        Returns:
            bool: True if the message should be logged, False otherwise
        """
        return self.LEVEL_HIERARCHY.get(level, 0) >= self.LEVEL_HIERARCHY.get(self.log_level, 0)
    
    ####################################################################################################
    
    def _get_caller_info(self):
        """Get the class name and method name of the caller."""
        # We need to go back 3 frames:
        # Current frame -> _get_caller_info
        # Parent frame -> _log
        # Grandparent frame -> info/warning/etc.
        # Great-grandparent frame -> actual caller
        frame = inspect.currentframe()
        try:
            # Navigate to the frame where logger was called
            frame = frame.f_back.f_back.f_back
            frame_info = inspect.getframeinfo(frame)
            
            # Get the calling class name if available
            if "self" in frame.f_locals:
                class_name = frame.f_locals["self"].__class__.__name__
            else:
                class_name = ""
            
            method_name = frame_info.function

            # If the caller is the main module (i.e. outside of any class or method),
            # use the file name instead
            if method_name == "<module>":
                file_name = os.path.basename(frame_info.filename)
                return f"<{file_name}>"
            else:
                return f"{class_name}.{method_name}"
        except Exception:
            return "Unknown.unknown"
        finally:
            # Clear references to frames to prevent reference cycles
            del frame
    
    ####################################################################################################
    
    def _log(self, level: str, message: str):
        """
        Main logging method that handles formatting and output.
        
        Args:
            level (str): The log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message (str): The message to log
        """
        # Check if this message should be logged based on current log level
        if not self._should_log(level):
            return
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        caller_info = self._get_caller_info()
        
        formatted_timestamp = f"{self.TIMESTAMP_COLOR}{timestamp}{Style.RESET_ALL}"
        formatted_level = f"{self.LEVELS_COLORS[level]}{level}{Style.RESET_ALL}"
        formatted_caller = f"{self.CALLER_COLOR}{caller_info}{Style.RESET_ALL}"
        formatted_message = f"{self.MESSAGE_COLOR}{message}{Style.RESET_ALL}"
        print(f"{formatted_timestamp} - {formatted_level} - {formatted_caller} - {formatted_message}")
    
    ####################################################################################################
    
    def debug(self, message: str):
        """Log a debug message."""
        self._log("DEBUG", message)
    
    ####################################################################################################
    
    def info(self, message: str):
        """Log an info message."""
        self._log("INFO", message)
    
    ####################################################################################################
    
    def warning(self, message: str):
        """Log a warning message."""
        self._log("WARNING", message)
    
    ####################################################################################################
    
    def error(self, message: str):
        """Log an error message."""
        self._log("ERROR", message)
    
    ####################################################################################################
    
    def critical(self, message: str):
        """Log a critical message."""
        self._log("CRITICAL", message)

    ####################################################################################################

####################################################################################################
    
# For direct import
# from perceiver.utils.logger import logger
logger = Logger()