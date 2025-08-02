'use client';

import { useState, useEffect, useMemo } from 'react';
import { DragDropContext, Droppable, Draggable, DropResult, DragStart } from '@hello-pangea/dnd';
import { Pipeline, CandidateInPipeline, PipelineStage } from '@/types/pipeline';
import CandidateCard from './CandidateCard';

interface PipelineBoardProps {
  pipeline: Pipeline;
  candidates: CandidateInPipeline[];
  onCandidateMove: (candidateId: string, fromStage: string, toStage: string) => void;
  onCandidateClick: (candidate: CandidateInPipeline) => void;
}

export default function PipelineBoard({
  pipeline,
  candidates,
  onCandidateMove,
  onCandidateClick,
}: PipelineBoardProps) {
  const [draggingCandidate, setDraggingCandidate] = useState<CandidateInPipeline | null>(null);
  const [draggingFromStage, setDraggingFromStage] = useState<string | null>(null);
  
  // Check if we have many stages (for responsive text sizing)
  const hasManyStages = pipeline.stages.length >= 7;
  
  // Group candidates by stage
  const candidatesByStage = candidates.reduce((acc, candidate) => {
    const stage = candidate.current_stage;
    if (!acc[stage]) {
      acc[stage] = [];
    }
    acc[stage].push(candidate);
    return acc;
  }, {} as Record<string, CandidateInPipeline[]>);

  // Check if a stage transition requires warning
  const isUnusualMove = (fromStage: string, toStage: string): boolean => {
    const stageOrder: Record<string, number> = {
      'applied': 1,
      'screening': 2,
      'interview': 3,
      'offer': 4,
      'hired': 5,
      'rejected': 0,
      'withdrawn': 0
    };

    const fromOrder = stageOrder[fromStage] || 0;
    const toOrder = stageOrder[toStage] || 0;

    // Moving FROM rejected/withdrawn to active pipeline
    if (fromStage === 'rejected' || fromStage === 'withdrawn') {
      // Allow reclassification between terminal states
      if (toStage === 'rejected' || toStage === 'withdrawn') return false;
      // Any move from terminal back to active is unusual
      return true;
    }
    
    // Moving TO rejected from late stages
    if (toStage === 'rejected' && (fromStage === 'offer' || fromStage === 'hired')) {
      return true;
    }
    
    // Moving TO withdrawn from late stages
    if (toStage === 'withdrawn' && (fromStage === 'offer' || fromStage === 'hired')) {
      return true;
    }
    
    // Normal rejection/withdrawal from early stages
    if ((toStage === 'rejected' || toStage === 'withdrawn') && 
        (fromStage === 'applied' || fromStage === 'screening' || fromStage === 'interview')) {
      return false;
    }
    
    // Any skip of stages forward (not just adjacent move)
    if (toOrder > fromOrder + 1 && toOrder > 0 && fromOrder > 0) return true;
    
    // Moving backwards (except to rejected/withdrawn)
    if (fromOrder > toOrder && toOrder > 0) return true;
    
    return false;
  };
  
  // Check if this is an extreme skip (shows red instead of yellow)
  const isExtremeSkip = (fromStage: string, toStage: string): boolean => {
    // Moving from hired to rejected is critical
    if (fromStage === 'hired' && toStage === 'rejected') return true;
    
    // Moving from hired to withdrawn is very unusual
    if (fromStage === 'hired' && toStage === 'withdrawn') return true;
    
    // Moving from rejected/withdrawn to late stages
    if ((fromStage === 'rejected' || fromStage === 'withdrawn') && 
        (toStage === 'offer' || toStage === 'hired')) return true;
    
    // Skipping 2+ stages or going directly to hired from early stages
    if ((fromStage === 'applied' || fromStage === 'screening') && toStage === 'hired') return true;
    if (fromStage === 'applied' && toStage === 'offer') return true;
    
    return false;
  };

  const handleDragStart = (start: DragStart) => {
    const candidate = candidates.find(c => c.id === start.draggableId);
    if (candidate) {
      setDraggingCandidate(candidate);
      setDraggingFromStage(start.source.droppableId);
    }
  };

  const handleDragEnd = (result: DropResult) => {
    // Clear dragging state
    setDraggingCandidate(null);
    setDraggingFromStage(null);

    if (!result.destination) return;

    const candidateId = result.draggableId;
    const fromStage = result.source.droppableId;
    const toStage = result.destination.droppableId;

    if (fromStage !== toStage) {
      onCandidateMove(candidateId, fromStage, toStage);
    }
  };

  // Helper function to render a stage column
  const renderStageColumn = (stage: any) => {
    const isUnusual = draggingFromStage && isUnusualMove(draggingFromStage, stage.id);
    const isExtreme = draggingFromStage && isExtremeSkip(draggingFromStage, stage.id);
    const isTerminal = stage.id === 'rejected' || stage.id === 'withdrawn';
    
    return (
      <div
        key={stage.id}
        className="bg-gray-50 rounded-lg flex flex-col h-full overflow-hidden"
        style={{ 
          minWidth: 0 // Allow grid to shrink columns as needed
        }}
      >
        <div
          className={`px-2 py-2 border-b ${isTerminal ? 'bg-gray-100' : ''}`}
          style={{ borderColor: stage.color }}
        >
          <div className="flex items-center justify-between">
            <h3 className={`font-semibold ${hasManyStages ? 'text-xs' : 'text-sm'} text-gray-900 truncate`}>
              {stage.name}
            </h3>
            <span className="text-xs text-gray-500 bg-gray-200 px-1 py-0.5 rounded-sm flex-shrink-0 ml-1">
              {candidatesByStage[stage.id]?.length || 0}
            </span>
          </div>
        </div>

        <Droppable droppableId={stage.id}>
          {(provided, snapshot) => {
            let dropZoneClass = 'p-1.5 flex-1 transition-colors duration-200 overflow-y-auto';
            
            if (snapshot.isDraggingOver) {
              // Currently hovering over this drop zone
              if (isExtreme) {
                dropZoneClass += ' bg-red-100 border-2 border-red-400 border-dashed';
              } else if (isUnusual) {
                dropZoneClass += ' bg-yellow-100 border-2 border-yellow-400 border-dashed';
              } else {
                dropZoneClass += ' bg-green-50 border-2 border-green-400 border-dashed';
              }
            } else if (draggingCandidate && draggingFromStage !== stage.id) {
              // Dragging but not hovering - show subtle indicator
              if (isExtreme) {
                dropZoneClass += ' bg-red-50 border-2 border-red-200 border-dashed';
              } else if (isUnusual) {
                dropZoneClass += ' bg-yellow-50 border-2 border-yellow-200 border-dashed';
              } else {
                dropZoneClass += ' bg-gray-50';
              }
            }
            
            return (
              <div
                ref={provided.innerRef}
                {...provided.droppableProps}
                className={dropZoneClass}
              >
                {candidatesByStage[stage.id]?.map((candidate, index) => (
                  <Draggable
                    key={candidate.id}
                    draggableId={candidate.id}
                    index={index}
                  >
                    {(provided, snapshot) => (
                      <div
                        ref={provided.innerRef}
                        {...provided.draggableProps}
                        {...provided.dragHandleProps}
                        className={`mb-1.5 ${
                          snapshot.isDragging ? 'opacity-50' : ''
                        }`}
                      >
                        <CandidateCard
                          candidate={candidate}
                          onClick={() => onCandidateClick(candidate)}
                          stageColor={stage.color}
                        />
                      </div>
                    )}
                  </Draggable>
                ))}
                {provided.placeholder}
              </div>
            );
          }}
        </Droppable>
      </div>
    );
  };

  return (
    <DragDropContext onDragEnd={handleDragEnd} onDragStart={handleDragStart}>
      <div className="h-full overflow-hidden pipeline-container">
        {/* Use CSS Grid to guarantee all stages fit */}
        <div className="h-full p-3">
          <div 
            className="h-full"
            style={{ 
              display: 'grid',
              gridTemplateColumns: `repeat(${pipeline.stages.length}, 1fr)`,
              gap: '6px',
              maxWidth: '100%'
            }}
          >
            {pipeline.stages.map((stage) => renderStageColumn(stage))}
          </div>
        </div>
      </div>
    </DragDropContext>
  );
}