'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  Mail,
  Phone,
  MapPin,
  Briefcase,
  Calendar,
  Eye,
  Download,
  Edit,
  Trash2,
} from 'lucide-react';
import { resumeApi } from '@/lib/api/client';
import type { Resume } from '@/lib/api/client';

export default function ResumeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [resume, setResume] = useState<Resume | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (params.id) {
      fetchResume(params.id as string);
    }
  }, [params.id]);

  const fetchResume = async (id: string) => {
    try {
      const data = await resumeApi.getResume(id);
      setResume(data);
    } catch (error) {
      console.error('Failed to fetch resume:', error);
      // Redirect to resumes list if not found
      router.push('/dashboard/resumes');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!resume || !confirm('Are you sure you want to delete this resume?')) return;

    setIsDeleting(true);
    try {
      await resumeApi.deleteResume(resume.id);
      router.push('/dashboard/resumes');
    } catch (error) {
      console.error('Failed to delete resume:', error);
      alert('Failed to delete resume. Please try again.');
      setIsDeleting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const statusStyles = {
      completed: 'bg-green-100 text-green-800',
      processing: 'bg-yellow-100 text-yellow-800',
      pending: 'bg-gray-100 text-gray-800',
      failed: 'bg-red-100 text-red-800',
    };

    return (
      <span className={`badge ${statusStyles[status as keyof typeof statusStyles] || statusStyles.pending}`}>
        {status}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!resume) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
          Resume not found
        </h2>
        <button 
          onClick={() => {
            if (window.history.length > 1) {
              router.back();
            } else {
              router.push('/dashboard/resumes');
            }
          }}
          className="btn-primary mt-4"
        >
          Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => router.back()}
          className="inline-flex items-center text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </button>

        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              {resume.first_name} {resume.last_name}
            </h1>
            {resume.current_title && (
              <p className="text-xl text-gray-600 dark:text-gray-400 mt-1">
                {resume.current_title}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2">
            {getStatusBadge(resume.parse_status)}
            <button
              onClick={handleDelete}
              disabled={isDeleting}
              className="btn-secondary text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
              title="Delete resume"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Contact Information */}
      <div className="card p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Contact Information
        </h2>
        <div className="grid gap-3">
          {resume.email && (
            <div className="flex items-center text-gray-700 dark:text-gray-300">
              <Mail className="h-4 w-4 mr-3 text-gray-400" />
              <a href={`mailto:${resume.email}`} className="hover:underline">
                {resume.email}
              </a>
            </div>
          )}
          {resume.phone && (
            <div className="flex items-center text-gray-700 dark:text-gray-300">
              <Phone className="h-4 w-4 mr-3 text-gray-400" />
              <a href={`tel:${resume.phone}`} className="hover:underline">
                {resume.phone}
              </a>
            </div>
          )}
          {resume.location && (
            <div className="flex items-center text-gray-700 dark:text-gray-300">
              <MapPin className="h-4 w-4 mr-3 text-gray-400" />
              {resume.location}
            </div>
          )}
          {resume.years_experience !== null && (
            <div className="flex items-center text-gray-700 dark:text-gray-300">
              <Briefcase className="h-4 w-4 mr-3 text-gray-400" />
              {resume.years_experience} years of experience
            </div>
          )}
          {resume.job_position && (
            <div className="flex items-center text-gray-700 dark:text-gray-300">
              <Briefcase className="h-4 w-4 mr-3 text-gray-400" />
              Applied for: {resume.job_position}
            </div>
          )}
        </div>
      </div>

      {/* Professional Summary */}
      {resume.summary && (
        <div className="card p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Professional Summary
          </h2>
          <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
            {resume.summary}
          </p>
        </div>
      )}

      {/* Skills */}
      {resume.skills && resume.skills.length > 0 && (
        <div className="card p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Skills
          </h2>
          <div className="flex flex-wrap gap-2">
            {resume.skills.map((skill, index) => (
              <span
                key={index}
                className="badge bg-primary/10 text-primary"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Keywords */}
      {resume.keywords && resume.keywords.length > 0 && (
        <div className="card p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Keywords
          </h2>
          <div className="flex flex-wrap gap-2">
            {resume.keywords.map((keyword, index) => (
              <span
                key={index}
                className="badge bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
              >
                {keyword}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Metadata */}
      <div className="card p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Resume Details
        </h2>
        <div className="grid gap-3 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-gray-600 dark:text-gray-400">Original File:</span>
            <span className="text-gray-900 dark:text-white">{resume.original_filename}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-600 dark:text-gray-400">File Size:</span>
            <span className="text-gray-900 dark:text-white">
              {resume.file_size ? `${(resume.file_size / 1024).toFixed(1)} KB` : 'N/A'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-600 dark:text-gray-400">Uploaded:</span>
            <span className="text-gray-900 dark:text-white">
              {new Date(resume.created_at).toLocaleDateString()}
            </span>
          </div>
          {resume.parsed_at && (
            <div className="flex items-center justify-between">
              <span className="text-gray-600 dark:text-gray-400">Parsed:</span>
              <span className="text-gray-900 dark:text-white">
                {new Date(resume.parsed_at).toLocaleDateString()}
              </span>
            </div>
          )}
          <div className="flex items-center justify-between">
            <span className="text-gray-600 dark:text-gray-400">View Count:</span>
            <span className="text-gray-900 dark:text-white">{resume.view_count}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-600 dark:text-gray-400">Search Appearances:</span>
            <span className="text-gray-900 dark:text-white">{resume.search_appearance_count}</span>
          </div>
        </div>
      </div>

      {/* Full Resume Text */}
      {resume.raw_text && (
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Full Resume Text
          </h2>
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 max-h-96 overflow-y-auto">
            <pre className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono">
              {resume.raw_text}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}