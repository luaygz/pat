#!/usr/bin/env python3

# Standard imports
import asyncio
import argparse
import sys
from contextlib import redirect_stdout

# Perceiver imports
from perceiver.perceiver import Perceiver
from perceiver.utils.logger import logger

####################################################################################################

async def main():
    """
    CLI entry point for the Perceiver.
    """
    # Detect if output is being piped to another process
    is_being_piped = not sys.stdout.isatty()
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description = "Perceiver - Ingest data sources and output them as text",
        formatter_class = argparse.RawDescriptionHelpFormatter,
        epilog = """
Examples:
  python perceiver.py /home/user/file.txt
  python perceiver.py https://www.youtube.com/watch?v=VIDEO_ID
  python perceiver.py https://github.com/owner/repo
  python perceiver.py --bypass-cache https://edition.cnn.com
  python perceiver.py /home/user/document.pdf
        """
    )
    parser.add_argument(
        "source",
        help = "The URL or file path to ingest"
    )
    parser.add_argument(
        "--bypass-cache",
        action = "store_true",
        help = "Force re-ingestion even if cached"
    )
    
    args = parser.parse_args()
    
    # When piping output, redirect all console output to stderr
    # to keep stdout clean for the next process
    with redirect_stdout(sys.stderr if is_being_piped else sys.stdout):
        perceiver = Perceiver()
        
        try:
            perception = await perceiver.ingest(
                source = args.source,
                bypass_cache = args.bypass_cache
            )
            
            # Log success
            logger.info(f"Perception ID: {perception.id}")
            
        except FileNotFoundError as e:
            logger.error(str(e))
            sys.exit(1)
        except ValueError as e:
            logger.error(str(e))
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            sys.exit(1)
    
    # Output content to stdout (will be piped to next process if piping)
    if is_being_piped:
        print(perception.contents)
    else:
        # When not piping, also print the content but with a separator
        print("\n" + "=" * 80)
        print("EXTRACTED CONTENT:")
        print("=" * 80 + "\n")
        print(perception.contents)

####################################################################################################

if __name__ == "__main__":
    asyncio.run(main())

####################################################################################################
