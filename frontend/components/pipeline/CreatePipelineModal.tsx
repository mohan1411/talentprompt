'use client'

import React, { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { PlusIcon, XIcon, GripVerticalIcon } from 'lucide-react'
import { pipelineApi } from '@/lib/api/client'
import toast from 'react-hot-toast'

interface PipelineStage {
  id: string
  name: string
  order: number
  color: string
  type?: string
  actions?: string[]
}

interface CreatePipelineModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess?: () => void
}

const DEFAULT_STAGES: PipelineStage[] = [
  { id: 'applied', name: 'Applied', order: 1, color: '#9ca3af', type: 'initial' },
  { id: 'screening', name: 'Screening', order: 2, color: '#3b82f6', type: 'review' },
  { id: 'interview', name: 'Interview', order: 3, color: '#8b5cf6', type: 'interview' },
  { id: 'offer', name: 'Offer', order: 4, color: '#f59e0b', type: 'decision' },
  { id: 'hired', name: 'Hired', order: 5, color: '#10b981', type: 'final' },
  { id: 'rejected', name: 'Rejected', order: 6, color: '#ef4444', type: 'final' },
  { id: 'withdrawn', name: 'Withdrawn', order: 7, color: '#6b7280', type: 'final' },
]

export function CreatePipelineModal({
  isOpen,
  onClose,
  onSuccess,
}: CreatePipelineModalProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [stages, setStages] = useState<PipelineStage[]>(DEFAULT_STAGES)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [editingStage, setEditingStage] = useState<string | null>(null)

  const handleAddStage = () => {
    const newStage: PipelineStage = {
      id: `stage_${Date.now()}`,
      name: 'New Stage',
      order: stages.length + 1,
      color: '#6b7280',
    }
    setStages([...stages, newStage])
    setEditingStage(newStage.id)
  }

  const handleRemoveStage = (stageId: string) => {
    setStages(stages.filter(s => s.id !== stageId))
  }

  const handleUpdateStage = (stageId: string, updates: Partial<PipelineStage>) => {
    setStages(stages.map(s => s.id === stageId ? { ...s, ...updates } : s))
  }

  const handleMoveStage = (index: number, direction: 'up' | 'down') => {
    const newStages = [...stages]
    const newIndex = direction === 'up' ? index - 1 : index + 1
    
    if (newIndex >= 0 && newIndex < stages.length) {
      [newStages[index], newStages[newIndex]] = [newStages[newIndex], newStages[index]]
      // Update order numbers
      newStages.forEach((stage, idx) => {
        stage.order = idx + 1
      })
      setStages(newStages)
    }
  }

  const handleSubmit = async () => {
    if (!name.trim()) {
      setError('Pipeline name is required')
      return
    }

    if (stages.length === 0) {
      setError('At least one stage is required')
      return
    }

    try {
      setIsLoading(true)
      setError(null)

      await pipelineApi.createPipeline({
        name: name.trim(),
        description: description.trim() || undefined,
        stages: stages.map((stage, index) => ({
          ...stage,
          order: index + 1,
        })),
        is_default: false,
      })

      toast.success('Pipeline created successfully')
      onSuccess?.()
      handleClose()
    } catch (err: any) {
      console.error('Failed to create pipeline:', err)
      setError(err.detail || 'Failed to create pipeline')
    } finally {
      setIsLoading(false)
    }
  }

  const handleClose = () => {
    setName('')
    setDescription('')
    setStages(DEFAULT_STAGES)
    setError(null)
    setEditingStage(null)
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New Pipeline</DialogTitle>
          <DialogDescription>
            Define the stages candidates will move through in your hiring process
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="space-y-2">
            <Label htmlFor="name">Pipeline Name</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Engineering Hiring Process"
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description (Optional)</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the purpose of this pipeline..."
              rows={3}
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Pipeline Stages</Label>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={handleAddStage}
                disabled={isLoading}
              >
                <PlusIcon className="h-4 w-4 mr-1" />
                Add Stage
              </Button>
            </div>

            <div className="space-y-2">
              {stages.map((stage, index) => (
                <div
                  key={stage.id}
                  className="flex items-center gap-2 p-3 border rounded-lg"
                >
                  <button
                    type="button"
                    className="cursor-move text-muted-foreground hover:text-foreground"
                    disabled={isLoading}
                  >
                    <GripVerticalIcon className="h-4 w-4" />
                  </button>

                  <div className="flex items-center gap-2 flex-1">
                    {editingStage === stage.id ? (
                      <>
                        <Input
                          value={stage.name}
                          onChange={(e) => handleUpdateStage(stage.id, { name: e.target.value })}
                          onBlur={() => setEditingStage(null)}
                          onKeyPress={(e) => e.key === 'Enter' && setEditingStage(null)}
                          className="h-8"
                          autoFocus
                        />
                        <input
                          type="color"
                          value={stage.color}
                          onChange={(e) => handleUpdateStage(stage.id, { color: e.target.value })}
                          className="h-8 w-8 border rounded cursor-pointer"
                        />
                      </>
                    ) : (
                      <>
                        <div
                          className="h-8 w-8 rounded-full border-2"
                          style={{ backgroundColor: stage.color, borderColor: stage.color }}
                        />
                        <span
                          className="cursor-text"
                          onClick={() => setEditingStage(stage.id)}
                        >
                          {stage.name}
                        </span>
                      </>
                    )}
                  </div>

                  <div className="flex items-center gap-1">
                    <Button
                      type="button"
                      size="icon"
                      variant="ghost"
                      className="h-8 w-8"
                      onClick={() => handleMoveStage(index, 'up')}
                      disabled={isLoading || index === 0}
                    >
                      ↑
                    </Button>
                    <Button
                      type="button"
                      size="icon"
                      variant="ghost"
                      className="h-8 w-8"
                      onClick={() => handleMoveStage(index, 'down')}
                      disabled={isLoading || index === stages.length - 1}
                    >
                      ↓
                    </Button>
                    <Button
                      type="button"
                      size="icon"
                      variant="ghost"
                      className="h-8 w-8 text-destructive"
                      onClick={() => handleRemoveStage(stage.id)}
                      disabled={isLoading || stages.length === 1}
                    >
                      <XIcon className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={isLoading}
          >
            {isLoading ? 'Creating...' : 'Create Pipeline'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}