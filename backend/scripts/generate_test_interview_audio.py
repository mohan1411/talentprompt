#!/usr/bin/env python3
"""
Generate a test interview audio file for testing the transcription feature.
Creates a 10-minute mock job interview with two speakers.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from gtts import gTTS
    from pydub import AudioSegment
    from pydub.generators import Sine
except ImportError:
    print("Installing required packages...")
    os.system("pip install gtts pydub")
    from gtts import gTTS
    from pydub import AudioSegment
    from pydub.generators import Sine

import tempfile
import random

# Interview script with questions and answers
INTERVIEW_SCRIPT = [
    {
        "interviewer": "Good morning! Thank you for coming in today. I'm Sarah from the HR department. How are you doing today?",
        "candidate": "Good morning Sarah! I'm doing great, thank you. I'm excited to be here and learn more about this opportunity.",
        "pause": 1000
    },
    {
        "interviewer": "Wonderful! Let's start with a simple question. Can you tell me a little bit about yourself and your background?",
        "candidate": "Of course! I'm a software engineer with five years of experience in full-stack development. I graduated from State University with a degree in Computer Science. In my current role at Tech Corp, I've been leading a team of three developers working on our e-commerce platform. I'm particularly passionate about creating scalable solutions and mentoring junior developers.",
        "pause": 1500
    },
    {
        "interviewer": "That sounds impressive! What made you interested in applying for this position at our company?",
        "candidate": "I've been following your company's growth for the past two years, and I'm really impressed by your commitment to innovation in the fintech space. The role aligns perfectly with my experience in building secure, scalable applications. I'm particularly excited about the opportunity to work with your payment processing system and contribute to the mobile app development that was mentioned in the job description.",
        "pause": 1200
    },
    {
        "interviewer": "Can you describe a challenging project you've worked on recently and how you overcame the challenges?",
        "candidate": "Certainly! Last quarter, we had to migrate our entire payment infrastructure to a new provider with zero downtime. The challenge was that we processed over 10,000 transactions daily. I led the effort to design a parallel-run strategy where we gradually shifted traffic between systems. We implemented comprehensive monitoring and rollback procedures. The migration was completed successfully over a weekend with no customer impact.",
        "pause": 1500
    },
    {
        "interviewer": "That's exactly the kind of problem-solving we value here. How do you approach working in a team environment?",
        "candidate": "I believe effective teamwork starts with clear communication and mutual respect. In my current role, I hold daily stand-ups with my team and ensure everyone's voice is heard. I also believe in knowledge sharing - I regularly conduct code reviews and technical sessions. When conflicts arise, I focus on finding solutions that benefit the project rather than individual preferences.",
        "pause": 1000
    },
    {
        "interviewer": "Speaking of technical skills, what programming languages and technologies are you most proficient in?",
        "candidate": "My primary languages are Python and JavaScript. I use Python for backend development with FastAPI and Django, and JavaScript with React and Node.js for frontend and full-stack applications. I'm also experienced with PostgreSQL, Redis, Docker, and AWS services. Recently, I've been working with Kubernetes for container orchestration and have completed several certifications in cloud architecture.",
        "pause": 1200
    },
    {
        "interviewer": "How do you stay updated with the latest technology trends and continue learning?",
        "candidate": "I'm a firm believer in continuous learning. I dedicate time each week to reading technical blogs and documentation. I'm active on GitHub and contribute to open-source projects. I also attend local meetups and have presented at two conferences last year. Additionally, I take online courses - I recently completed a course on machine learning to understand how AI can enhance our applications.",
        "pause": 1000
    },
    {
        "interviewer": "Where do you see yourself professionally in the next five years?",
        "candidate": "In five years, I see myself in a senior technical leadership role, possibly as a principal engineer or engineering manager. I want to be designing system architectures that solve complex business problems while mentoring the next generation of developers. I'm also interested in contributing more to the tech community through speaking engagements and open-source projects.",
        "pause": 1500
    },
    {
        "interviewer": "What would you say is your biggest professional weakness?",
        "candidate": "I tend to be a perfectionist, which sometimes means I spend more time than necessary on certain tasks. I've been working on balancing quality with efficiency by setting clear deadlines for myself and focusing on MVP approaches first. I've also learned to better delegate tasks and trust my team members, which has helped me manage my time more effectively.",
        "pause": 1200
    },
    {
        "interviewer": "Do you have any questions for me about the role or the company?",
        "candidate": "Yes, I do have a few questions. First, can you tell me more about the team I'd be working with? Also, what are the biggest technical challenges the team is currently facing? And finally, how does the company support professional development and growth for its engineers?",
        "pause": 1000
    },
    {
        "interviewer": "Great questions! Our team consists of eight engineers with diverse backgrounds. We're currently working on scaling our infrastructure to handle international expansion. As for professional development, we offer learning budgets, conference attendance, and dedicated time for personal projects. Is there anything else you'd like to know?",
        "candidate": "That sounds fantastic! I think you've covered everything I wanted to know. This seems like an excellent opportunity, and I'm very interested in moving forward with the process.",
        "pause": 800
    },
    {
        "interviewer": "Wonderful! We'll be in touch within the next few days with the next steps. Thank you so much for your time today, and it was great meeting you!",
        "candidate": "Thank you so much, Sarah! I really enjoyed our conversation and learning more about the role. I look forward to hearing from you. Have a great rest of your day!",
        "pause": 500
    }
]


def generate_interview_audio(output_path="test_interview_10min.mp3"):
    """Generate a mock interview audio file."""
    print("Generating mock interview audio...")
    
    # Create temporary directory for intermediate files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Initialize the final audio
        final_audio = AudioSegment.empty()
        
        # Process each exchange in the script
        for i, exchange in enumerate(INTERVIEW_SCRIPT):
            print(f"Processing exchange {i+1}/{len(INTERVIEW_SCRIPT)}...")
            
            # Generate interviewer audio (female voice)
            if "interviewer" in exchange:
                interviewer_tts = gTTS(text=exchange["interviewer"], lang='en', tld='com')
                interviewer_file = temp_path / f"interviewer_{i}.mp3"
                interviewer_tts.save(str(interviewer_file))
                
                # Load and adjust interviewer audio (slightly higher pitch for variety)
                interviewer_audio = AudioSegment.from_mp3(str(interviewer_file))
                interviewer_audio = interviewer_audio.speedup(playback_speed=1.05)
                
                final_audio += interviewer_audio
                final_audio += AudioSegment.silent(duration=500)  # Brief pause
            
            # Generate candidate audio (male voice) 
            if "candidate" in exchange:
                candidate_tts = gTTS(text=exchange["candidate"], lang='en', tld='co.uk')
                candidate_file = temp_path / f"candidate_{i}.mp3"
                candidate_tts.save(str(candidate_file))
                
                # Load and adjust candidate audio (slightly lower pitch for variety)
                candidate_audio = AudioSegment.from_mp3(str(candidate_file))
                candidate_audio = candidate_audio.speedup(playback_speed=0.95)
                
                final_audio += candidate_audio
            
            # Add pause between exchanges
            pause_duration = exchange.get("pause", 1000)
            final_audio += AudioSegment.silent(duration=pause_duration)
        
        # Check duration and add padding if needed to reach ~10 minutes
        current_duration = len(final_audio)
        target_duration = 10 * 60 * 1000  # 10 minutes in milliseconds
        
        if current_duration < target_duration:
            # Add some ambient silence at the end
            padding = target_duration - current_duration
            print(f"Adding {padding/1000:.1f} seconds of padding...")
            final_audio += AudioSegment.silent(duration=padding)
        
        # Add a subtle background ambience (optional - very quiet office sound)
        # This helps make it sound more realistic
        duration_seconds = len(final_audio) / 1000
        
        # Export the final audio
        print(f"Exporting audio file (duration: {duration_seconds/60:.1f} minutes)...")
        final_audio.export(output_path, format="mp3", bitrate="128k")
        
    print(f"✅ Mock interview audio generated successfully!")
    print(f"📁 File saved as: {output_path}")
    print(f"⏱️ Duration: {duration_seconds/60:.1f} minutes")
    print(f"💾 File size: {os.path.getsize(output_path) / (1024*1024):.1f} MB")
    

if __name__ == "__main__":
    # Generate the audio file
    output_file = "test_interview_10min.mp3"
    
    # Check if user provided a custom output path
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    
    generate_interview_audio(output_file)
    print("\n🎯 You can now use this file to test the interview upload feature!")