#!/usr/bin/env python3
"""
Download sample interview audio files from free sources.
"""

import os
import requests
from pathlib import Path


def download_file(url, filename):
    """Download a file from URL."""
    print(f"Downloading {filename}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    file_size = os.path.getsize(filename) / (1024 * 1024)
    print(f"✅ Downloaded: {filename} ({file_size:.1f} MB)")


def main():
    """Download sample interview audio files."""
    print("Sample Interview Audio Downloader")
    print("=" * 40)
    
    # Create downloads directory
    download_dir = Path("sample_interviews")
    download_dir.mkdir(exist_ok=True)
    
    print("\nHere are some free sources for interview audio:")
    print("\n1. Wikimedia Commons - Interview Audio Files")
    print("   URL: https://commons.wikimedia.org/wiki/Category:Audio_files_of_interviews")
    print("   - Browse and download various interview recordings")
    print("   - Look for files marked as 10+ minutes")
    
    print("\n2. ESL-Lounge - Job Interview Audio")
    print("   URL: https://www.esl-lounge.com/student/listening/2L3-job-interview.php")
    print("   - Contains 'The Job Interview' audio file")
    
    print("\n3. Library of Congress - Interview Recordings")
    print("   URL: https://www.loc.gov/audio/?fa=subject:interviews")
    print("   - Various oral history interviews")
    
    print("\n4. Internet Archive - Interview Collections")
    print("   URL: https://archive.org/search.php?query=interview&and[]=mediatype%3A%22audio%22")
    print("   - Thousands of interview recordings")
    print("   - Filter by duration for 10+ minute files")
    
    print("\n5. BBC Learning English - Job Interview")
    print("   URL: https://www.bbc.co.uk/learningenglish/english/features/english-at-work")
    print("   - Professional interview scenarios")
    
    # Example: Download a sample file from Internet Archive (if available)
    sample_urls = {
        "internet_archive_sample": "https://archive.org/download/SAMPLE_INTERVIEW_AUDIO/interview.mp3",
        # Add more direct download URLs here as you find them
    }
    
    print("\n" + "=" * 40)
    print("Manual Download Instructions:")
    print("1. Visit any of the above URLs")
    print("2. Find an interview audio that's ~10 minutes long")
    print("3. Download the MP3/WAV file")
    print("4. Use it to test the upload feature")
    
    print("\nAlternatively, you can:")
    print("- Use YouTube with a YouTube-to-MP3 converter")
    print("- Search for 'mock job interview' or 'behavioral interview practice'")
    print("- Look for videos that are 10-15 minutes long")
    
    print("\nRecommended YouTube searches:")
    print('- "mock job interview full"')
    print('- "job interview practice session"')
    print('- "behavioral interview examples"')
    print('- "STAR method interview practice"')


if __name__ == "__main__":
    main()