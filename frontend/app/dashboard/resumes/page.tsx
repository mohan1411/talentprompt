'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { 
  FileText, 
  Search, 
  Calendar, 
  MapPin, 
  Briefcase,
  Eye,
  Trash2,
  Download,
  CheckCircle,
  Clock,
  XCircle,
  Users,
  Linkedin,
  Mail
} from 'lucide-react';
import { resumeApi } from '@/lib/api/client';
import type { Resume } from '@/lib/api/client';
import { OutreachModal } from '@/components/outreach/OutreachModal';

export default function ResumesPage() {
  const router = useRouter();
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedResume, setSelectedResume] = useState<string | null>(null);
  const [selectedResumes, setSelectedResumes] = useState<Set<string>>(new Set());
  const [showBulkPositionModal, setShowBulkPositionModal] = useState(false);
  const [bulkJobPosition, setBulkJobPosition] = useState('');
  const [showOutreachModal, setShowOutreachModal] = useState(false);
  const [outreachCandidate, setOutreachCandidate] = useState<Resume | null>(null);

  useEffect(() => {
    fetchResumes();
  }, []);

  const fetchResumes = async () => {
    try {
      const data = await resumeApi.getMyResumes();
      setResumes(data);
    } catch (error) {
      console.error('Failed to fetch resumes:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (resumeId: string) => {
    if (!confirm('Are you sure you want to delete this resume?')) return;

    try {
      await resumeApi.deleteResume(resumeId);
      setResumes(resumes.filter(r => r.id !== resumeId));
    } catch (error) {
      console.error('Failed to delete resume:', error);
      alert('Failed to delete resume. Please try again.');
    }
  };

  const handleBulkDelete = async () => {
    if (selectedResumes.size === 0) return;
    
    if (!confirm(`Are you sure you want to delete ${selectedResumes.size} resume(s)?`)) return;

    try {
      await resumeApi.bulkDelete(Array.from(selectedResumes));
      setResumes(resumes.filter(r => !selectedResumes.has(r.id)));
      setSelectedResumes(new Set());
    } catch (error) {
      console.error('Failed to bulk delete resumes:', error);
      alert('Failed to delete resumes. Please try again.');
    }
  };

  const handleBulkUpdatePosition = async () => {
    if (selectedResumes.size === 0 || !bulkJobPosition.trim()) return;

    try {
      await resumeApi.bulkUpdatePosition(Array.from(selectedResumes), bulkJobPosition);
      // Refresh resumes to show updated positions
      await fetchResumes();
      setSelectedResumes(new Set());
      setShowBulkPositionModal(false);
      setBulkJobPosition('');
    } catch (error) {
      console.error('Failed to update positions:', error);
      alert('Failed to update positions. Please try again.');
    }
  };

  const toggleResumeSelection = (resumeId: string) => {
    const newSelection = new Set(selectedResumes);
    if (newSelection.has(resumeId)) {
      newSelection.delete(resumeId);
    } else {
      newSelection.add(resumeId);
    }
    setSelectedResumes(newSelection);
  };

  const toggleSelectAll = () => {
    if (selectedResumes.size === resumes.length) {
      setSelectedResumes(new Set());
    } else {
      setSelectedResumes(new Set(resumes.map(r => r.id)));
    }
  };

  const handleFindSimilar = (resume: Resume) => {
    // Navigate to search page with similar results
    router.push(`/dashboard/search/similar/${resume.id}?name=${encodeURIComponent(`${resume.first_name} ${resume.last_name}`)}`);
  };

  const handleGenerateOutreach = (resume: Resume) => {
    setOutreachCandidate(resume);
    setShowOutreachModal(true);
  };

  const getStatusBadge = (parseStatus: string) => {
    switch (parseStatus) {
      case 'completed':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
            <CheckCircle className="w-3 h-3 mr-1" />
            Processed
          </span>
        );
      case 'processing':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
            <Clock className="w-3 h-3 mr-1 animate-spin" />
            Processing
          </span>
        );
      case 'pending':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400">
            <Clock className="w-3 h-3 mr-1" />
            Pending
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">
            <XCircle className="w-3 h-3 mr-1" />
            Failed
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              My Resumes
            </h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Manage your uploaded resumes and track their processing status
            </p>
          </div>
          <Link
            href="/dashboard/upload"
            className="btn-primary"
          >
            Upload New Resume
          </Link>
        </div>
        
        {/* Bulk Actions */}
        {resumes.length > 0 && (
          <div className="flex items-center gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <input
              type="checkbox"
              checked={selectedResumes.size === resumes.length && resumes.length > 0}
              onChange={toggleSelectAll}
              className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
            />
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {selectedResumes.size === 0 
                ? 'Select all' 
                : `${selectedResumes.size} selected`}
            </span>
            
            {selectedResumes.size > 0 && (
              <>
                <button
                  onClick={handleBulkDelete}
                  className="ml-auto text-sm text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 flex items-center gap-1"
                >
                  <Trash2 className="h-4 w-4" />
                  Delete Selected
                </button>
                <button
                  onClick={() => setShowBulkPositionModal(true)}
                  className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 flex items-center gap-1"
                >
                  <Briefcase className="h-4 w-4" />
                  Update Position
                </button>
              </>
            )}
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      ) : resumes.length === 0 ? (
        <div className="text-center py-12 card">
          <FileText className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-lg font-medium text-gray-900 dark:text-white">
            No resumes yet
          </h3>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Get started by uploading your first resume.
          </p>
          <div className="mt-6">
            <Link
              href="/dashboard/upload"
              className="btn-primary"
            >
              Upload Resume
            </Link>
          </div>
        </div>
      ) : (
        <>
          <div className="mb-4 flex items-center justify-between">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Showing {resumes.length} resume{resumes.length !== 1 ? 's' : ''} • Sorted by newest first
            </p>
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {resumes.map((resume) => (
            <div
              key={resume.id}
              className="card p-6 hover:shadow-lg transition-shadow relative"
            >
              <div className="absolute top-4 left-4">
                <input
                  type="checkbox"
                  checked={selectedResumes.has(resume.id)}
                  onChange={() => toggleResumeSelection(resume.id)}
                  className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
                />
              </div>
              
              <div className="flex items-start justify-between mb-4 pl-8">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                      {resume.first_name} {resume.last_name}
                    </h3>
                    {/* New badge for recently uploaded resumes */}
                    {(() => {
                      const daysSinceUpload = Math.floor((Date.now() - new Date(resume.created_at).getTime()) / (1000 * 60 * 60 * 24));
                      return daysSinceUpload <= 7 ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100">
                          NEW
                        </span>
                      ) : null;
                    })()}
                  </div>
                  {resume.current_title && (
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {resume.current_title}
                    </p>
                  )}
                </div>
                {getStatusBadge(resume.parse_status)}
              </div>

              <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                {resume.email && (
                  <div className="flex items-center">
                    <span className="font-medium mr-2">Email:</span>
                    {resume.email}
                  </div>
                )}
                
                {resume.job_position && (
                  <div className="flex items-center">
                    <Briefcase className="h-4 w-4 mr-2" />
                    Position: {resume.job_position}
                  </div>
                )}
                
                {resume.location && (
                  <div className="flex items-center">
                    <MapPin className="h-4 w-4 mr-2" />
                    {resume.location}
                  </div>
                )}
                
                {resume.years_experience !== null && (
                  <div className="flex items-center">
                    <Briefcase className="h-4 w-4 mr-2" />
                    {resume.years_experience} years experience
                  </div>
                )}
                
                <div className="flex items-center">
                  <Calendar className="h-4 w-4 mr-2" />
                  Uploaded {new Date(resume.created_at).toLocaleDateString()}
                </div>
                
                {resume.view_count > 0 && (
                  <div className="flex items-center">
                    <Eye className="h-4 w-4 mr-2" />
                    {resume.view_count} views
                  </div>
                )}
              </div>

              {resume.skills && resume.skills.length > 0 && (
                <div className="mt-4">
                  <div className="flex flex-wrap gap-1">
                    {resume.skills.slice(0, 3).map((skill, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300"
                      >
                        {skill}
                      </span>
                    ))}
                    {resume.skills.length > 3 && (
                      <span className="text-xs text-gray-500">
                        +{resume.skills.length - 3} more
                      </span>
                    )}
                  </div>
                </div>
              )}

              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <div className="text-xs text-gray-500">
                    {resume.linkedin_url ? (
                      <div className="flex items-center gap-1">
                        <Linkedin className="h-3 w-3" />
                        <span>LinkedIn Import</span>
                      </div>
                    ) : (
                      resume.original_filename
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => router.push(`/dashboard/resumes/${resume.id}`)}
                      className="text-gray-600 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                      title="View details"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleFindSimilar(resume)}
                      className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                      title="Find similar candidates"
                    >
                      <Users className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleGenerateOutreach(resume)}
                      className="text-purple-600 hover:text-purple-700 dark:text-purple-400 dark:hover:text-purple-300"
                      title="Generate outreach message"
                    >
                      <Mail className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(resume.id)}
                      className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                      title="Delete resume"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
        </>
      )}

      {/* Bulk Position Update Modal */}
      {showBulkPositionModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Update Job Position
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Update the job position for {selectedResumes.size} selected resume(s)
            </p>
            <input
              type="text"
              value={bulkJobPosition}
              onChange={(e) => setBulkJobPosition(e.target.value)}
              placeholder="e.g., Senior Software Engineer"
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary dark:bg-gray-700 dark:border-gray-600 dark:text-white mb-4"
              autoFocus
            />
            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowBulkPositionModal(false);
                  setBulkJobPosition('');
                }}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleBulkUpdatePosition}
                className="btn-primary"
                disabled={!bulkJobPosition.trim()}
              >
                Update Position
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Outreach Modal */}
      {showOutreachModal && outreachCandidate && (
        <OutreachModal
          isOpen={showOutreachModal}
          onClose={() => {
            setShowOutreachModal(false);
            setOutreachCandidate(null);
          }}
          candidate={{
            id: outreachCandidate.id,
            name: `${outreachCandidate.first_name} ${outreachCandidate.last_name}`,
            title: outreachCandidate.current_title || '',
            skills: outreachCandidate.skills,
            experience: outreachCandidate.years_experience || undefined
          }}
        />
      )}
    </div>
  );
}