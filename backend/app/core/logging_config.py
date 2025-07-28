"""Logging configuration for the application."""

import logging
import sys

# Configure logging
def configure_logging():
    """Configure logging for the application."""
    # Set up root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Ensure our app loggers are set to INFO
    logging.getLogger("app").setLevel(logging.INFO)
    logging.getLogger("app.services").setLevel(logging.INFO)
    logging.getLogger("app.api").setLevel(logging.INFO)
    
    # Also enable print statements
    print("Logging configured with INFO level")