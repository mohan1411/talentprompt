'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs-simple'
import { 
  WorkflowIcon,
  PlusIcon,
  EditIcon,
  ToggleLeftIcon,
  ToggleRightIcon,
  AlertCircleIcon,
  Loader2Icon,
  CheckCircleIcon,
  ArrowRightIcon
} from 'lucide-react'
import { pipelineApi } from '@/lib/api/pipelines'

interface PipelineStage {
  order: number
  name: string
  type: string
  required: boolean
  min_score: number
  prerequisites: string[]
  description?: string
}

interface Pipeline {
  id: string
  name: string
  description?: string
  job_role?: string
  is_active: boolean
  stages: PipelineStage[]
  min_overall_score: number
  auto_reject_on_fail: boolean
  auto_approve_on_pass: boolean
  created_at: string
  updated_at: string
}

export default function PipelineSettingsPage() {
  const [pipelines, setPipelines] = useState<Pipeline[]>([])
  const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadPipelines()
  }, [])

  const loadPipelines = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await pipelineApi.getPipelines()
      setPipelines(data)
      if (data.length > 0 && !selectedPipeline) {
        setSelectedPipeline(data[0])
      }
    } catch (error: any) {
      console.error('Failed to load pipelines:', error)
      setError('Failed to load interview pipelines')
    } finally {
      setIsLoading(false)
    }
  }

  const togglePipelineStatus = async (pipeline: Pipeline) => {
    try {
      await pipelineApi.updatePipeline(pipeline.id, {
        is_active: !pipeline.is_active
      })
      await loadPipelines()
    } catch (error) {
      console.error('Failed to update pipeline:', error)
      setError('Failed to update pipeline status')
    }
  }

  const getStageTypeColor = (type: string) => {
    switch (type) {
      case 'general': return 'bg-blue-100 text-blue-800'
      case 'technical': return 'bg-purple-100 text-purple-800'
      case 'behavioral': return 'bg-green-100 text-green-800'
      case 'final': return 'bg-amber-100 text-amber-800'
      default: return 'bg-gray-100 text-gray-800'
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
        <h1 className="text-3xl font-bold">Interview Pipeline Settings</h1>
        <p className="text-muted-foreground mt-1">
          Configure multi-stage interview processes for different roles
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
                <Button size="sm" variant="outline">
                  <PlusIcon className="h-4 w-4 mr-1" />
                  New
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {pipelines.map((pipeline) => (
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
                      {pipeline.job_role && (
                        <p className="text-sm text-muted-foreground">{pipeline.job_role}</p>
                      )}
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant={pipeline.is_active ? 'default' : 'secondary'}>
                          {pipeline.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {pipeline.stages.length} stages
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
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
                <Tabs defaultValue="stages">
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="stages">Interview Stages</TabsTrigger>
                    <TabsTrigger value="scoring">Scoring Rules</TabsTrigger>
                    <TabsTrigger value="automation">Automation</TabsTrigger>
                  </TabsList>

                  <TabsContent value="stages" className="space-y-4 mt-4">
                    <div className="space-y-4">
                      {selectedPipeline.stages
                        .sort((a, b) => a.order - b.order)
                        .map((stage, index) => (
                          <div key={stage.name} className="relative">
                            {index > 0 && (
                              <div className="absolute -top-4 left-6 h-4 w-0.5 bg-gray-200" />
                            )}
                            <div className="flex items-start gap-3">
                              <div className="flex-shrink-0 w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                                <span className="text-sm font-semibold">{stage.order}</span>
                              </div>
                              <div className="flex-1 border rounded-lg p-4">
                                <div className="flex items-start justify-between mb-2">
                                  <div>
                                    <h4 className="font-medium">{stage.name}</h4>
                                    <div className="flex items-center gap-2 mt-1">
                                      <Badge className={getStageTypeColor(stage.type)}>
                                        {stage.type}
                                      </Badge>
                                      {stage.required && (
                                        <Badge variant="outline">Required</Badge>
                                      )}
                                      <span className="text-sm text-muted-foreground">
                                        Min score: {stage.min_score}/5
                                      </span>
                                    </div>
                                  </div>
                                </div>
                                {stage.prerequisites.length > 0 && (
                                  <div className="mt-2 text-sm">
                                    <span className="text-muted-foreground">Prerequisites: </span>
                                    {stage.prerequisites.map((prereq, idx) => (
                                      <span key={prereq}>
                                        {prereq}
                                        {idx < stage.prerequisites.length - 1 && ', '}
                                      </span>
                                    ))}
                                  </div>
                                )}
                                {stage.description && (
                                  <p className="text-sm text-muted-foreground mt-2">
                                    {stage.description}
                                  </p>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                    </div>
                  </TabsContent>

                  <TabsContent value="scoring" className="space-y-4 mt-4">
                    <Card>
                      <CardContent className="pt-6">
                        <div className="space-y-4">
                          <div>
                            <h4 className="font-medium mb-2">Minimum Overall Score</h4>
                            <div className="flex items-center gap-4">
                              <div className="text-3xl font-bold">
                                {selectedPipeline.min_overall_score}/5
                              </div>
                              <p className="text-sm text-muted-foreground">
                                Candidates must achieve this average score across all interviews
                              </p>
                            </div>
                          </div>
                          
                          <div>
                            <h4 className="font-medium mb-2">Stage Requirements</h4>
                            <div className="space-y-2">
                              {selectedPipeline.stages.map((stage) => (
                                <div key={stage.name} className="flex items-center justify-between py-2 border-b">
                                  <span className="text-sm">{stage.name}</span>
                                  <div className="flex items-center gap-2">
                                    <span className="text-sm text-muted-foreground">Min:</span>
                                    <Badge variant="outline">{stage.min_score}/5</Badge>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </TabsContent>

                  <TabsContent value="automation" className="space-y-4 mt-4">
                    <Card>
                      <CardContent className="pt-6 space-y-4">
                        <div className="flex items-center justify-between py-3 border-b">
                          <div>
                            <h4 className="font-medium">Auto-reject on Failure</h4>
                            <p className="text-sm text-muted-foreground">
                              Automatically reject candidates who fail any required stage
                            </p>
                          </div>
                          <Badge variant={selectedPipeline.auto_reject_on_fail ? 'default' : 'secondary'}>
                            {selectedPipeline.auto_reject_on_fail ? 'Enabled' : 'Disabled'}
                          </Badge>
                        </div>
                        
                        <div className="flex items-center justify-between py-3 border-b">
                          <div>
                            <h4 className="font-medium">Auto-approve on Success</h4>
                            <p className="text-sm text-muted-foreground">
                              Automatically approve candidates who pass all stages
                            </p>
                          </div>
                          <Badge variant={selectedPipeline.auto_approve_on_pass ? 'default' : 'secondary'}>
                            {selectedPipeline.auto_approve_on_pass ? 'Enabled' : 'Disabled'}
                          </Badge>
                        </div>
                        
                        <Alert>
                          <AlertCircleIcon className="h-4 w-4" />
                          <AlertDescription>
                            Automation rules help streamline the hiring process but can be overridden
                            by manual decisions at any time.
                          </AlertDescription>
                        </Alert>
                      </CardContent>
                    </Card>
                  </TabsContent>
                </Tabs>
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
    </div>
  )
}