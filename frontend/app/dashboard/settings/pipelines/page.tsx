'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  WorkflowIcon,
  PlusIcon,
  EditIcon,
  ToggleLeftIcon,
  ToggleRightIcon,
  AlertCircleIcon,
  Loader2Icon,
  TrashIcon
} from 'lucide-react'
import { pipelineApi } from '@/lib/api/pipelines'
import { CreatePipelineModal } from '@/components/pipeline/CreatePipelineModal'

interface PipelineStage {
  id: string
  name: string
  order: number
  color: string
  type?: string
  actions?: string[]
}

interface Pipeline {
  id: string
  name: string
  description?: string
  stages: PipelineStage[]
  team_id?: string
  is_default: boolean
  is_active: boolean
  created_by: string
  created_at: string
  updated_at: string
}

export default function PipelineSettingsPage() {
  const [pipelines, setPipelines] = useState<Pipeline[]>([])
  const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)

  useEffect(() => {
    loadPipelines()
  }, [])

  const loadPipelines = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await pipelineApi.getPipelines()
      setPipelines(data || [])
      if (data && data.length > 0 && !selectedPipeline) {
        setSelectedPipeline(data[0])
      }
    } catch (error: any) {
      console.error('Failed to load pipelines:', error)
      setError('Failed to load workflow pipelines')
      setPipelines([])
    } finally {
      setIsLoading(false)
    }
  }

  const togglePipelineStatus = async (pipeline: Pipeline) => {
    try {
      await pipelineApi.updatePipeline(pipeline.id, {
        name: pipeline.name,
        stages: pipeline.stages
      })
      await loadPipelines()
    } catch (error) {
      console.error('Failed to update pipeline:', error)
      setError('Failed to update pipeline status')
    }
  }

  if (isLoading) {
    return (
      <div className="container mx-auto py-6 px-4 max-w-6xl">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <Loader2Icon className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
            <p className="text-sm text-muted-foreground mt-2">Loading pipelines...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-6 px-4 max-w-6xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Workflow Pipeline Settings</h1>
        <p className="text-muted-foreground mt-1">
          Configure candidate workflow stages for your hiring process
        </p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircleIcon className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pipeline List */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Pipelines</span>
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => setShowCreateModal(true)}
                >
                  <PlusIcon className="h-4 w-4 mr-1" />
                  New
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {pipelines && pipelines.length > 0 ? (
                pipelines.map((pipeline) => (
                  <div
                    key={pipeline.id}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedPipeline?.id === pipeline.id
                        ? 'border-primary bg-primary/10'
                        : 'hover:bg-muted/50'
                    }`}
                    onClick={() => setSelectedPipeline(pipeline)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium">{pipeline.name}</h4>
                        {pipeline.description && (
                          <p className="text-sm text-muted-foreground mt-1">{pipeline.description}</p>
                        )}
                        <div className="flex items-center gap-2 mt-2">
                          <Badge variant={pipeline.is_active ? 'default' : 'secondary'}>
                            {pipeline.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                          {pipeline.is_default && (
                            <Badge variant="outline">Default</Badge>
                          )}
                          <span className="text-xs text-muted-foreground">
                            {pipeline.stages?.length || 0} stages
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <WorkflowIcon className="h-8 w-8 mx-auto mb-2" />
                  <p className="text-sm">No pipelines configured yet</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Pipeline Details */}
        <div className="lg:col-span-2">
          {selectedPipeline ? (
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle>{selectedPipeline.name}</CardTitle>
                    {selectedPipeline.description && (
                      <CardDescription className="mt-1">
                        {selectedPipeline.description}
                      </CardDescription>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => togglePipelineStatus(selectedPipeline)}
                    >
                      {selectedPipeline.is_active ? (
                        <>
                          <ToggleRightIcon className="h-4 w-4 mr-1" />
                          Active
                        </>
                      ) : (
                        <>
                          <ToggleLeftIcon className="h-4 w-4 mr-1" />
                          Inactive
                        </>
                      )}
                    </Button>
                    <Button size="sm" variant="outline">
                      <EditIcon className="h-4 w-4 mr-1" />
                      Edit
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h3 className="font-medium mb-3">Workflow Stages</h3>
                    <div className="space-y-3">
                      {selectedPipeline.stages && selectedPipeline.stages.length > 0 ? (
                        selectedPipeline.stages
                          .sort((a, b) => a.order - b.order)
                          .map((stage, index) => (
                          <div key={stage.id} className="relative">
                            {index > 0 && (
                              <div className="absolute -top-3 left-6 h-3 w-0.5 bg-gray-200" />
                            )}
                            <div className="flex items-start gap-3">
                              <div 
                                className="flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center"
                                style={{ backgroundColor: stage.color + '20' }}
                              >
                                <span className="text-sm font-semibold">{stage.order}</span>
                              </div>
                              <div className="flex-1 border rounded-lg p-4">
                                <div className="flex items-start justify-between mb-2">
                                  <div>
                                    <h4 className="font-medium">{stage.name}</h4>
                                    <div className="flex items-center gap-2 mt-1">
                                      <div 
                                        className="w-3 h-3 rounded-full" 
                                        style={{ backgroundColor: stage.color }}
                                      />
                                      <span className="text-sm text-muted-foreground">
                                        Color: {stage.color}
                                      </span>
                                      {stage.type && (
                                        <>
                                          <span className="text-muted-foreground">•</span>
                                          <span className="text-sm text-muted-foreground">
                                            Type: {stage.type}
                                          </span>
                                        </>
                                      )}
                                    </div>
                                  </div>
                                </div>
                                {stage.actions && stage.actions.length > 0 && (
                                  <div className="mt-2">
                                    <span className="text-sm text-muted-foreground">Actions: </span>
                                    <span className="text-sm">
                                      {stage.actions.join(', ')}
                                    </span>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="text-center py-8 text-muted-foreground">
                          <p className="text-sm">No stages configured</p>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="pt-4 border-t">
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>Created: {new Date(selectedPipeline.created_at).toLocaleDateString()}</span>
                      <span>•</span>
                      <span>Updated: {new Date(selectedPipeline.updated_at).toLocaleDateString()}</span>
                      {selectedPipeline.is_default && (
                        <>
                          <span>•</span>
                          <Badge variant="outline" className="text-xs">Default Pipeline</Badge>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="flex items-center justify-center min-h-[400px]">
                <div className="text-center text-muted-foreground">
                  <WorkflowIcon className="h-12 w-12 mx-auto mb-4" />
                  <p>Select a pipeline to view details</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      <CreatePipelineModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={() => {
          setShowCreateModal(false)
          loadPipelines()
        }}
      />
    </div>
  )
}