-- Add interview_category column to interview_sessions table
-- Run this script on your production database

ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS interview_category VARCHAR;