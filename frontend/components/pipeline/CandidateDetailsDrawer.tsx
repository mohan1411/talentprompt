'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { X, User, Mail, Phone, Calendar, MessageSquare, Star, Video } from 'lucide-react';
import { CandidateInPipeline, CandidateNote, PipelineActivity } from '@/types/pipeline';
import { pipelineApi } from '@/lib/api/client';
import { formatDistanceToNow } from 'date-fns';
import { toast } from 'react-hot-toast';

interface CandidateDetailsDrawerProps {
  candidate: CandidateInPipeline | null;
  isOpen: boolean;
  onClose: () => void;
  onAssigneeChange: (candidateId: string, assigneeId: string | null) => void;
  onStageChange: (newStage: string) => void;
}

export default function CandidateDetailsDrawer({
  candidate,
  isOpen,
  onClose,
  onAssigneeChange,
  onStageChange,
}: CandidateDetailsDrawerProps) {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'timeline' | 'notes' | 'evaluation'>('timeline');
  const [timeline, setTimeline] = useState<PipelineActivity[]>([]);
  const [notes, setNotes] = useState<CandidateNote[]>([]);
  const [newNote, setNewNote] = useState('');
  const [loading, setLoading] = useState(false);
  const [schedulingInterview, setSchedulingInterview] = useState(false);

  useEffect(() => {
    if (candidate && isOpen) {
      loadCandidateData();
    }
  }, [candidate, isOpen]);

  const loadCandidateData = async () => {
    if (!candidate) return;

    try {
      setLoading(true);
      const [timelineData, notesData] = await Promise.all([
        pipelineApi.getCandidateTimeline(candidate.id, candidate.pipeline_state_id),
        pipelineApi.getNotes(candidate.id, candidate.pipeline_state_id),
      ]);
      setTimeline(timelineData);
      setNotes(notesData);
    } catch (error) {
      console.error('Error loading candidate data:', error);
      toast.error('Failed to load candidate details');
    } finally {
      setLoading(false);
    }
  };

  const handleAddNote = async () => {
    if (!candidate || !newNote.trim()) return;

    try {
      await pipelineApi.addNote(
        candidate.id,
        { content: newNote, is_private: false },
        candidate.pipeline_state_id
      );
      setNewNote('');
      loadCandidateData();
      toast.success('Note added');
    } catch (error) {
      console.error('Error adding note:', error);
      toast.error('Failed to add note');
    }
  };

  const handleScheduleInterview = async () => {
    if (!candidate) return;
    
    console.log('Schedule Interview clicked for candidate:', {
      id: candidate.id,
      resume_id: candidate.resume_id,
      name: `${candidate.first_name} ${candidate.last_name}`,
      pipeline_state_id: candidate.pipeline_state_id,
      current_stage: candidate.current_stage
    });
    
    if (!candidate.pipeline_state_id) {
      console.error('No pipeline_state_id found for candidate!');
      toast.error('Pipeline state not found. Please refresh and try again.');
      return;
    }
    
    setSchedulingInterview(true);
    try {
      // Store pipeline context in sessionStorage for the interview page
      sessionStorage.setItem('interviewPipelineContext', JSON.stringify({
        candidateId: candidate.id,
        pipelineStateId: candidate.pipeline_state_id,
        candidateName: `${candidate.first_name} ${candidate.last_name}`,
        currentStage: candidate.current_stage
      }));
      
      // Navigate to existing AI Interview Copilot preparation page
      // Use resume_id if available, otherwise fall back to candidate.id
      const resumeId = candidate.resume_id || candidate.id;
      router.push(`/dashboard/interviews/prepare?resumeId=${resumeId}&pipeline_state_id=${candidate.pipeline_state_id}`);
    } catch (error) {
      console.error('Error scheduling interview:', error);
      toast.error('Failed to schedule interview');
      setSchedulingInterview(false);
    }
  };

  if (!isOpen || !candidate) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div className="absolute inset-0 bg-gray-500 bg-opacity-75" onClick={onClose} />
      
      <div className="fixed right-0 top-0 h-full w-full max-w-md bg-white shadow-xl">
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="border-b px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  {candidate.first_name} {candidate.last_name}
                </h2>
                {candidate.current_title && (
                  <p className="text-sm text-gray-600">{candidate.current_title}</p>
                )}
              </div>
              <button
                onClick={onClose}
                className="rounded-lg p-2 hover:bg-gray-100"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="border-b px-6 py-4">
            <div className="flex gap-2">
              <button
                onClick={handleScheduleInterview}
                disabled={schedulingInterview}
                className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                <Video className="h-4 w-4" />
                {schedulingInterview ? 'Preparing...' : 'Prepare Interview'}
              </button>
            </div>
          </div>

          {/* Contact Info */}
          <div className="border-b px-6 py-4">
            <div className="space-y-2 text-sm">
              {candidate.email && (
                <div className="flex items-center text-gray-600">
                  <Mail className="mr-2 h-4 w-4" />
                  <span>{candidate.email}</span>
                </div>
              )}
              <div className="flex items-center text-gray-600">
                <Calendar className="mr-2 h-4 w-4" />
                <span>In stage for {formatDistanceToNow(new Date(candidate.entered_stage_at))}</span>
              </div>
              {candidate.assigned_to && (
                <div className="flex items-center text-gray-600">
                  <User className="mr-2 h-4 w-4" />
                  <span>Assigned to {candidate.assigned_to.name}</span>
                </div>
              )}
            </div>
          </div>

          {/* Tabs */}
          <div className="border-b">
            <div className="flex">
              {(['timeline', 'notes', 'evaluation'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`flex-1 px-4 py-3 text-sm font-medium ${
                    activeTab === tab
                      ? 'border-b-2 border-blue-600 text-blue-600'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : (
              <>
                {activeTab === 'timeline' && (
                  <div className="px-6 py-4">
                    <div className="space-y-4">
                      {timeline.map((activity) => (
                        <div key={activity.id} className="flex gap-3">
                          <div className="mt-1">
                            <div className="h-2 w-2 rounded-full bg-gray-400" />
                          </div>
                          <div className="flex-1">
                            <p className="text-sm text-gray-900">
                              <span className="font-medium">{activity.user.name}</span>
                              {' '}
                              {activity.type === 'stage_changed' && (
                                <>moved from {activity.from_stage} to {activity.to_stage}</>
                              )}
                              {activity.type === 'note_added' && <>added a note</>}
                              {activity.type === 'assigned' && <>assigned this candidate</>}
                            </p>
                            {activity.content && (
                              <p className="mt-1 text-sm text-gray-600">{activity.content}</p>
                            )}
                            <p className="mt-1 text-xs text-gray-500">
                              {formatDistanceToNow(new Date(activity.created_at), { addSuffix: true })}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {activeTab === 'notes' && (
                  <div className="px-6 py-4">
                    <div className="space-y-4">
                      <div>
                        <textarea
                          value={newNote}
                          onChange={(e) => setNewNote(e.target.value)}
                          placeholder="Add a note..."
                          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                          rows={3}
                        />
                        <button
                          onClick={handleAddNote}
                          disabled={!newNote.trim()}
                          className="mt-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                        >
                          Add Note
                        </button>
                      </div>

                      <div className="space-y-3">
                        {notes.map((note) => (
                          <div key={note.id} className="rounded-lg border bg-gray-50 p-3">
                            <div className="flex items-start justify-between">
                              <div>
                                <p className="text-sm font-medium text-gray-900">
                                  {note.user.name}
                                </p>
                                <p className="text-xs text-gray-500">
                                  {formatDistanceToNow(new Date(note.created_at), { addSuffix: true })}
                                </p>
                              </div>
                              {note.is_private && (
                                <span className="rounded bg-gray-200 px-2 py-0.5 text-xs text-gray-600">
                                  Private
                                </span>
                              )}
                            </div>
                            <p className="mt-2 text-sm text-gray-700">{note.content}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'evaluation' && (
                  <div className="px-6 py-4">
                    <p className="text-sm text-gray-600">No evaluations yet</p>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}