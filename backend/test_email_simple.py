#!/usr/bin/env python3
"""Simple test to check email service output."""

import sys
import os

# Test print statements
print("\n" + "="*50 + " DIRECT PRINT TEST " + "="*50)
print("This is a direct print statement")
print("If you see this, prints are working")

# Test logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("\n" + "="*50 + " LOGGING TEST " + "="*50)
logger.debug("This is a DEBUG log")
logger.info("This is an INFO log")
logger.warning("This is a WARNING log")
logger.error("This is an ERROR log")

print("\n" + "="*50 + " END TEST " + "="*50)