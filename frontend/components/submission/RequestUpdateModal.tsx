'use client';

import { useState } from 'react';
import { X, Send, Calendar, FileText } from 'lucide-react';
import { submissionApi } from '@/lib/api/client';
import type { Resume } from '@/lib/api/client';

interface RequestUpdateModalProps {
  isOpen: boolean;
  onClose: () => void;
  candidate: {
    id: string;
    name: string;
    email?: string;
    title?: string;
  };
  onSuccess?: () => void;
}

export function RequestUpdateModal({ isOpen, onClose, candidate, onSuccess }: RequestUpdateModalProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [candidateName, setCandidateName] = useState(candidate.name);
  const [candidateEmail, setCandidateEmail] = useState(candidate.email || '');
  const isNewCandidate = !candidate.id;
  
  const [message, setMessage] = useState(
    isNewCandidate 
      ? `We're building a talent pool for exciting opportunities and would love to have your profile on file.

Would you be interested in submitting your resume and professional information? This will help us match you with relevant positions as they become available.

The process is quick and doesn't require creating an account.`
      : `I hope this message finds you well. We'd like to ensure we have your most current information on file.

Would you mind taking a few minutes to update your profile with:
- Your current employment status and role
- Any new skills or certifications
- Your current location and availability
- Updated contact information

This helps us match you with the most relevant opportunities.`
  );
  const [deadline, setDeadline] = useState(7); // Default 7 days

  const handleSubmit = async () => {
    const emailToUse = isNewCandidate ? candidateEmail : candidate.email;
    const nameToUse = isNewCandidate ? candidateName : candidate.name;
    
    if (!emailToUse) {
      alert('Please provide an email address.');
      return;
    }
    
    if (isNewCandidate && !nameToUse) {
      alert('Please provide a candidate name.');
      return;
    }

    setIsLoading(true);
    try {
      await submissionApi.createSubmission({
        submission_type: isNewCandidate ? 'new' : 'update',
        candidate_id: isNewCandidate ? undefined : candidate.id,
        candidate_email: emailToUse,
        candidate_name: nameToUse,
        message,
        deadline_days: deadline
      });

      alert(`${isNewCandidate ? 'Invitation' : 'Update request'} sent successfully!`);
      onSuccess?.();
      onClose();
    } catch (error) {
      console.error(`Failed to send ${isNewCandidate ? 'invitation' : 'update request'}:`, error);
      alert(`Failed to send ${isNewCandidate ? 'invitation' : 'update request'}. Please try again.`);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              {isNewCandidate ? 'Invite New Candidate' : 'Request Profile Update'}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="p-6 space-y-4 overflow-y-auto max-h-[calc(90vh-200px)]">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Candidate
            </label>
            {isNewCandidate ? (
              <div className="space-y-3">
                <input
                  type="text"
                  value={candidateName}
                  onChange={(e) => setCandidateName(e.target.value)}
                  placeholder="Candidate Name"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
                <input
                  type="email"
                  value={candidateEmail}
                  onChange={(e) => setCandidateEmail(e.target.value)}
                  placeholder="Email Address"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
            ) : (
              <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
                <p className="font-medium text-gray-900 dark:text-white">{candidate.name}</p>
                {candidate.title && (
                  <p className="text-sm text-gray-600 dark:text-gray-400">{candidate.title}</p>
                )}
                {candidate.email && (
                  <p className="text-sm text-gray-600 dark:text-gray-400">{candidate.email}</p>
                )}
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              <FileText className="inline h-4 w-4 mr-1" />
              Message to Candidate
            </label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={8}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              placeholder="Personalize your message..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              <Calendar className="inline h-4 w-4 mr-1" />
              Response Deadline
            </label>
            <select
              value={deadline}
              onChange={(e) => setDeadline(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            >
              <option value={3}>3 days</option>
              <option value={7}>7 days (recommended)</option>
              <option value={14}>14 days</option>
              <option value={30}>30 days</option>
            </select>
          </div>

          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-md">
            <p className="text-sm text-blue-800 dark:text-blue-300">
              <strong>What happens next:</strong>
            </p>
            <ul className="mt-2 text-sm text-blue-700 dark:text-blue-400 space-y-1">
              <li>• The candidate will receive an email with a secure link</li>
              <li>• They can {isNewCandidate ? 'submit their profile' : 'update their information'} without creating an account</li>
              <li>• You'll be notified when they submit</li>
              <li>• The link expires after {deadline} days</li>
            </ul>
          </div>
        </div>

        <div className="p-6 border-t border-gray-200 dark:border-gray-700">
          <div className="flex justify-end space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={isLoading || !message.trim()}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                  <span>Sending...</span>
                </>
              ) : (
                <>
                  <Send className="h-4 w-4" />
                  <span>Send {isNewCandidate ? 'Invitation' : 'Request'}</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}