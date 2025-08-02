'use client';

import { useState, useEffect } from 'react';
import { X, GitBranch, Plus } from 'lucide-react';
import { pipelineApi } from '@/lib/api/client';
import { Pipeline } from '@/types/pipeline';
import { CreatePipelineModal } from './CreatePipelineModal';
import { toast } from 'react-hot-toast';

interface AddToPipelineModalProps {
  isOpen: boolean;
  onClose: () => void;
  candidate: {
    id: string;
    name: string;
    title: string;
    email?: string;
  };
  onSuccess?: () => void;
}

export function AddToPipelineModal({ isOpen, onClose, candidate, onSuccess }: AddToPipelineModalProps) {
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [selectedPipeline, setSelectedPipeline] = useState<string>('');
  const [assigneeId, setAssigneeId] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [loadingPipelines, setLoadingPipelines] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadPipelines();
    }
  }, [isOpen]);

  const loadPipelines = async () => {
    try {
      setLoadingPipelines(true);
      const data = await pipelineApi.getPipelines();
      setPipelines(data);
      
      // Select default pipeline if available
      const defaultPipeline = data.find(p => p.is_default);
      if (defaultPipeline) {
        setSelectedPipeline(defaultPipeline.id);
      }
    } catch (error) {
      console.error('Error loading pipelines:', error);
      toast.error('Failed to load pipelines');
    } finally {
      setLoadingPipelines(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedPipeline) {
      toast.error('Please select a pipeline');
      return;
    }

    try {
      setLoading(true);
      
      await pipelineApi.addCandidateToPipeline({
        candidate_id: candidate.id,
        pipeline_id: selectedPipeline,
        assigned_to: assigneeId || undefined,
      });

      toast.success(`${candidate.name} added to pipeline`);
      onSuccess?.();
      onClose();
    } catch (error: any) {
      console.error('Error adding to pipeline:', error);
      toast.error(error.detail || 'Failed to add candidate to pipeline');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={onClose} />
        
        <div className="relative w-full max-w-md transform rounded-lg bg-white p-6 shadow-xl">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Add to Pipeline</h3>
            <button
              onClick={onClose}
              className="rounded-lg p-1 hover:bg-gray-100"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <div className="mb-2 flex items-center gap-2 text-sm text-gray-600">
                <GitBranch className="h-4 w-4" />
                <span>Adding {candidate.name}</span>
              </div>
              {candidate.title && (
                <p className="text-sm text-gray-500">{candidate.title}</p>
              )}
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Select Pipeline
                </label>
                {loadingPipelines ? (
                  <div className="flex items-center justify-center py-4">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <select
                      value={selectedPipeline}
                      onChange={(e) => setSelectedPipeline(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
                      required
                    >
                      <option value="">Choose a pipeline...</option>
                      {pipelines.map((pipeline) => (
                        <option key={pipeline.id} value={pipeline.id}>
                          {pipeline.name}
                          {pipeline.is_default && ' (Default)'}
                        </option>
                      ))}
                    </select>
                    
                    {pipelines.length === 0 && (
                      <div className="text-center py-2">
                        <p className="text-sm text-gray-500 mb-2">No pipelines available</p>
                        <button
                          type="button"
                          onClick={() => setShowCreateModal(true)}
                          className="inline-flex items-center text-sm text-blue-600 hover:text-blue-700"
                        >
                          <Plus className="h-4 w-4 mr-1" />
                          Create New Pipeline
                        </button>
                      </div>
                    )}
                    
                    {pipelines.length > 0 && (
                      <button
                        type="button"
                        onClick={() => setShowCreateModal(true)}
                        className="inline-flex items-center text-sm text-blue-600 hover:text-blue-700"
                      >
                        <Plus className="h-4 w-4 mr-1" />
                        Create New Pipeline
                      </button>
                    )}
                  </div>
                )}
              </div>

              {selectedPipeline && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Assign To (Optional)
                  </label>
                  <input
                    type="text"
                    value={assigneeId}
                    onChange={(e) => setAssigneeId(e.target.value)}
                    placeholder="Enter user ID or leave blank"
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Leave blank to add without assignment
                  </p>
                </div>
              )}
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading || !selectedPipeline}
                className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Adding...' : 'Add to Pipeline'}
              </button>
            </div>
          </form>
        </div>
      </div>

      <CreatePipelineModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={() => {
          setShowCreateModal(false);
          loadPipelines();
        }}
      />
    </div>
  );
}