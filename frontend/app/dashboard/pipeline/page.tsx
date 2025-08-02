'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { pipelineApi } from '@/lib/api/client';
import { Pipeline, CandidateInPipeline } from '@/types/pipeline';
import PipelineBoard from '@/components/pipeline/PipelineBoard';
import PipelineHeader from '@/components/pipeline/PipelineHeader';
import PipelineHelp from '@/components/pipeline/PipelineHelp';
import CandidateDetailsDrawer from '@/components/pipeline/CandidateDetailsDrawer';
import { CreatePipelineModal } from '@/components/pipeline/CreatePipelineModal';
import { Button } from '@/components/ui/button';
import { PlusIcon } from 'lucide-react';
import { toast } from 'react-hot-toast';

export default function PipelinePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [pipeline, setPipeline] = useState<Pipeline | null>(null);
  const [candidates, setCandidates] = useState<CandidateInPipeline[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateInPipeline | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [currentOffset, setCurrentOffset] = useState(0);
  const BATCH_SIZE = 50; // Load 50 candidates at a time

  useEffect(() => {
    loadPipelineData();
  }, []);

  const loadPipelineData = async (pipelineId?: string, reset = true) => {
    try {
      setLoading(true);
      
      // Get all pipelines
      const allPipelines = await pipelineApi.getPipelines();
      setPipelines(allPipelines);
      
      // Select pipeline to display
      let selectedPipeline = null;
      if (pipelineId) {
        selectedPipeline = allPipelines.find(p => p.id === pipelineId);
      } else {
        // Try to get default pipeline first
        selectedPipeline = allPipelines.find(p => p.is_default);
        // If no default, use the first pipeline
        if (!selectedPipeline && allPipelines.length > 0) {
          selectedPipeline = allPipelines[0];
        }
      }
      
      setPipeline(selectedPipeline);
      
      // Get initial batch of candidates
      if (selectedPipeline) {
        const candidatesData = await pipelineApi.getPipelineCandidates(selectedPipeline.id, {
          limit: BATCH_SIZE,
          offset: 0
        });
        
        setCandidates(candidatesData);
        setCurrentOffset(BATCH_SIZE);
        setHasMore(candidatesData.length === BATCH_SIZE);
      }
    } catch (error: any) {
      console.error('Error loading pipeline:', error);
      toast.error('Failed to load pipeline data');
    } finally {
      setLoading(false);
    }
  };
  
  const loadMoreCandidates = async () => {
    if (!pipeline || loadingMore || !hasMore) return;
    
    try {
      setLoadingMore(true);
      
      const moreCandidates = await pipelineApi.getPipelineCandidates(pipeline.id, {
        limit: BATCH_SIZE,
        offset: currentOffset
      });
      
      if (moreCandidates.length > 0) {
        setCandidates(prev => [...prev, ...moreCandidates]);
        setCurrentOffset(prev => prev + moreCandidates.length);
        setHasMore(moreCandidates.length === BATCH_SIZE);
      } else {
        setHasMore(false);
      }
    } catch (error: any) {
      console.error('Error loading more candidates:', error);
      toast.error('Failed to load more candidates');
    } finally {
      setLoadingMore(false);
    }
  };

  const handleCandidateMove = async (
    candidateId: string,
    fromStage: string,
    toStage: string
  ) => {
    try {
      // Find the candidate
      const candidate = candidates.find(c => c.id === candidateId);
      if (!candidate) return;

      // Define stage order for validation
      const stageOrder: Record<string, number> = {
        'applied': 1,
        'screening': 2,
        'interview': 3,
        'offer': 4,
        'hired': 5,
        'rejected': 0, // Can move to rejected from any stage
        'withdrawn': 0 // Can move to withdrawn from any stage
      };

      const fromOrder = stageOrder[fromStage] || 0;
      const toOrder = stageOrder[toStage] || 0;

      // Check if this is an unusual move that skips stages
      let needsConfirmation = false;
      let warningMessage = '';

      // Moving FROM rejected or withdrawn (re-engaging candidates)
      if (fromStage === 'rejected') {
        if (toStage === 'withdrawn') {
          // Reclassification between terminal states - allow without warning
          needsConfirmation = false;
        } else if (toStage === 'applied' || toStage === 'screening') {
          needsConfirmation = true;
          warningMessage = `⚠️ Reconsidering rejected candidate: Moving ${candidate.first_name} ${candidate.last_name} back from Rejected stage. This candidate was previously rejected.\n\nAre you sure you want to give them another chance?`;
        } else if (toStage === 'interview') {
          needsConfirmation = true;
          warningMessage = `⚠️ Unusual: Moving ${candidate.first_name} ${candidate.last_name} from Rejected directly to Interview. This skips the normal re-evaluation process.\n\nAre you sure you want to proceed?`;
        } else if (toStage === 'offer' || toStage === 'hired') {
          needsConfirmation = true;
          warningMessage = `🚨 HIGHLY UNUSUAL: Moving ${candidate.first_name} ${candidate.last_name} from Rejected directly to ${toStage === 'offer' ? 'Offer' : 'Hired'}. This is extremely rare and requires strong justification.\n\nAre you absolutely sure you want to proceed?`;
        }
      }
      // Moving FROM withdrawn
      else if (fromStage === 'withdrawn') {
        if (toStage === 'rejected') {
          // Reclassification between terminal states - allow without warning
          needsConfirmation = false;
        } else if (toStage === 'applied' || toStage === 'screening') {
          needsConfirmation = true;
          warningMessage = `⚠️ Re-engaging withdrawn candidate: ${candidate.first_name} ${candidate.last_name} previously withdrew from the process. Make sure they're interested in re-applying.\n\nAre you sure you want to proceed?`;
        } else if (toStage === 'interview' || toStage === 'offer') {
          needsConfirmation = true;
          warningMessage = `🚨 UNUSUAL: Moving ${candidate.first_name} ${candidate.last_name} from Withdrawn directly to ${toStage === 'interview' ? 'Interview' : 'Offer'}. Ensure the candidate has explicitly expressed renewed interest.\n\nAre you sure you want to proceed?`;
        } else if (toStage === 'hired') {
          needsConfirmation = true;
          warningMessage = `🚨 EXTREME: Moving ${candidate.first_name} ${candidate.last_name} from Withdrawn directly to Hired. This should only be done if the candidate has formally re-engaged.\n\nAre you absolutely sure you want to proceed?`;
        }
      }
      // Moving TO rejected
      else if (toStage === 'rejected') {
        if (fromStage === 'offer') {
          needsConfirmation = true;
          warningMessage = `⚠️ Withdrawing offer: Moving ${candidate.first_name} ${candidate.last_name} to Rejected after extending an offer. This may have legal implications.\n\nAre you sure you want to reject after making an offer?`;
        } else if (fromStage === 'hired') {
          needsConfirmation = true;
          warningMessage = `🚨 CRITICAL ACTION: Moving ${candidate.first_name} ${candidate.last_name} from Hired to Rejected. This is extremely unusual and may have serious legal and reputational consequences.\n\nThis action should only be taken after consulting with HR and Legal.\n\nAre you absolutely certain you want to proceed?`;
        } else {
          // Normal rejection from early stages
          needsConfirmation = false;
        }
      }
      // Moving TO withdrawn
      else if (toStage === 'withdrawn') {
        if (fromStage === 'offer') {
          needsConfirmation = true;
          warningMessage = `⚠️ Candidate withdrawal after offer: Recording that ${candidate.first_name} ${candidate.last_name} withdrew after receiving an offer. This is important for analytics.\n\nConfirm the candidate has withdrawn?`;
        } else if (fromStage === 'hired') {
          needsConfirmation = true;
          warningMessage = `🚨 Post-hire withdrawal: Recording that ${candidate.first_name} ${candidate.last_name} withdrew after being hired. This is very unusual and should be documented.\n\nConfirm the candidate has withdrawn after hiring?`;
        } else {
          // Normal withdrawal from early stages
          needsConfirmation = false;
        }
      }
      // Skipping from screening directly to hired (skipping interview AND offer)
      else if (fromStage === 'screening' && toStage === 'hired') {
        needsConfirmation = true;
        warningMessage = `⚠️ EXTREME SKIP: Moving ${candidate.first_name} ${candidate.last_name} directly to Hired stage will skip BOTH the interview AND offer process. This is highly unusual and should only be done in very exceptional cases (e.g., rehiring a former employee).\n\nAre you absolutely sure you want to proceed?`;
      }
      // Skipping from screening directly to offer (skipping interview)
      else if (fromStage === 'screening' && toStage === 'offer') {
        needsConfirmation = true;
        warningMessage = `Moving ${candidate.first_name} ${candidate.last_name} directly to Offer stage will skip the interview process. This is unusual and should only be done in exceptional cases.\n\nAre you sure you want to proceed?`;
      }
      // Skipping from applied directly to hired
      else if (fromStage === 'applied' && toStage === 'hired') {
        needsConfirmation = true;
        warningMessage = `⚠️ EXTREME SKIP: Moving ${candidate.first_name} ${candidate.last_name} directly from Applied to Hired skips the ENTIRE hiring process. This should never be done unless there's an exceptional circumstance.\n\nAre you absolutely sure you want to proceed?`;
      }
      // Skipping from applied directly to offer
      else if (fromStage === 'applied' && toStage === 'offer') {
        needsConfirmation = true;
        warningMessage = `Moving ${candidate.first_name} ${candidate.last_name} directly from Applied to Offer stage skips both screening and interview. This is very unusual.\n\nAre you sure you want to proceed?`;
      }
      // Skipping from applied directly to interview
      else if (fromStage === 'applied' && toStage === 'interview') {
        needsConfirmation = true;
        warningMessage = `Moving ${candidate.first_name} ${candidate.last_name} directly from Applied to Interview stage skips the screening process.\n\nAre you sure you want to proceed?`;
      }
      // Skipping from interview directly to hired (skipping offer)
      else if (fromStage === 'interview' && toStage === 'hired') {
        needsConfirmation = true;
        warningMessage = `Moving ${candidate.first_name} ${candidate.last_name} directly to Hired stage will skip the offer negotiation process. This is unusual.\n\nAre you sure you want to proceed?`;
      }
      // Any other forward skip of multiple stages
      else if (toOrder > fromOrder + 1 && toOrder > 0 && fromOrder > 0) {
        needsConfirmation = true;
        const skippedStages = toOrder - fromOrder - 1;
        warningMessage = `Moving ${candidate.first_name} ${candidate.last_name} from ${fromStage} to ${toStage} will skip ${skippedStages} stage(s). This is unusual.\n\nAre you sure you want to proceed?`;
      }
      // Moving backwards in the pipeline (except to rejected/withdrawn)
      else if (fromOrder > toOrder && toOrder > 0) {
        needsConfirmation = true;
        warningMessage = `Moving ${candidate.first_name} ${candidate.last_name} backwards from ${fromStage} to ${toStage} stage. This will reset their progress.\n\nAre you sure you want to proceed?`;
      }

      // Show confirmation dialog for unusual moves
      if (needsConfirmation) {
        const confirmed = window.confirm(warningMessage);
        if (!confirmed) {
          return; // User cancelled the move
        }
      }

      // Optimistic update
      setCandidates(prev => 
        prev.map(c => 
          c.id === candidateId 
            ? { ...c, current_stage: toStage }
            : c
        )
      );

      // API call with reason for unusual moves
      const moveData: any = {
        new_stage_id: toStage,
      };
      
      if (needsConfirmation) {
        moveData.reason = 'Manual override - exceptional case';
      }

      await pipelineApi.moveCandidateStage(candidate.pipeline_state_id, moveData);

      toast.success('Candidate moved successfully');
    } catch (error) {
      console.error('Error moving candidate:', error);
      toast.error('Failed to move candidate');
      // Revert on error
      loadPipelineData();
    }
  };

  const handleCandidateClick = (candidate: CandidateInPipeline) => {
    setSelectedCandidate(candidate);
    setDrawerOpen(true);
  };

  const handleAssigneeChange = async (candidateId: string, assigneeId: string | null) => {
    try {
      const candidate = candidates.find(c => c.id === candidateId);
      if (!candidate) return;

      await pipelineApi.assignCandidate(candidate.pipeline_state_id, assigneeId);
      
      // Reload to get updated data
      loadPipelineData(pipeline?.id);
      toast.success('Assignment updated');
    } catch (error) {
      console.error('Error updating assignment:', error);
      toast.error('Failed to update assignment');
    }
  };

  const handlePipelineChange = (pipelineId: string) => {
    if (pipelineId && pipelineId !== pipeline?.id) {
      loadPipelineData(pipelineId);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!pipeline && pipelines.length === 0) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900">No Pipeline Found</h2>
        <p className="mt-2 text-gray-600">Please create a pipeline to get started.</p>
        <Button
          className="mt-4"
          onClick={() => setShowCreateModal(true)}
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Create Pipeline
        </Button>
        
        <CreatePipelineModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            loadPipelineData();
          }}
        />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {pipeline && (
        <PipelineHeader 
          pipeline={pipeline}
          pipelines={pipelines}
          candidateCount={candidates.length}
          onRefresh={() => loadPipelineData(pipeline?.id)}
          onPipelineChange={handlePipelineChange}
        />
      )}
      
      <div className="flex-1 flex flex-col overflow-hidden">
        {pipeline && (
          <div className="px-6 pt-2">
            <PipelineHelp />
          </div>
        )}
        
        <div className="flex-1 overflow-hidden flex flex-col">
          {pipeline ? (
            <>
              <div className="flex-1 overflow-hidden">
                <PipelineBoard
                  pipeline={pipeline}
                  candidates={candidates}
                  onCandidateMove={handleCandidateMove}
                  onCandidateClick={handleCandidateClick}
                />
              </div>
              
              {/* Load More Button */}
              {hasMore && (
                <div className="flex justify-center p-4 border-t bg-white">
                  <Button
                    onClick={loadMoreCandidates}
                    disabled={loadingMore}
                    variant="outline"
                    className="min-w-[200px]"
                  >
                    {loadingMore ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                        Loading more...
                      </>
                    ) : (
                      `Load More Candidates (${candidates.length} loaded)`
                    )}
                  </Button>
                </div>
              )}
            </>
          ) : (
            <div className="flex items-center justify-center h-full">
              <p className="text-gray-500">Select a pipeline to view candidates</p>
            </div>
          )}
        </div>
      </div>

      <CandidateDetailsDrawer
        candidate={selectedCandidate}
        isOpen={drawerOpen}
        onClose={() => {
          setDrawerOpen(false);
          setSelectedCandidate(null);
        }}
        onAssigneeChange={handleAssigneeChange}
        onStageChange={(newStage) => {
          if (selectedCandidate) {
            handleCandidateMove(selectedCandidate.id, selectedCandidate.current_stage, newStage);
          }
        }}
      />
    </div>
  );
}