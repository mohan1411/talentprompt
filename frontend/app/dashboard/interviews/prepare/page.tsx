'use client'

import React, { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select-simple'
import { Slider } from '@/components/ui/slider-simple'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs-simple'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  SearchIcon, 
  SparklesIcon,
  BrainIcon,
  TargetIcon,
  ClockIcon,
  AlertCircleIcon,
  CheckCircleIcon,
  XCircleIcon,
  PlusIcon,
  XIcon,
  Loader2Icon
} from 'lucide-react'
import { resumeApi, Resume } from '@/lib/api/client'
import { interviewsApi } from '@/lib/api/interviews'

export default function PrepareInterviewPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [selectedResume, setSelectedResume] = useState<Resume | null>(null)
  const [resumes, setResumes] = useState<Resume[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<Resume[]>([])
  const [displayLimit, setDisplayLimit] = useState(10)
  const [jobPosition, setJobPosition] = useState('')
  const [jobRequirements, setJobRequirements] = useState('')
  const [interviewMode, setInterviewMode] = useState<'IN_PERSON' | 'VIRTUAL' | 'PHONE' | null>(null)  // IN_PERSON, VIRTUAL, PHONE
  const [interviewCategory, setInterviewCategory] = useState('general')  // general, technical, behavioral, final
  const [difficultyLevel, setDifficultyLevel] = useState([3])
  const [numQuestions, setNumQuestions] = useState([10])
  const [focusAreas, setFocusAreas] = useState<string[]>([])
  const [newFocusArea, setNewFocusArea] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [isLoadingResumes, setIsLoadingResumes] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Load resumes on mount
  useEffect(() => {
    loadResumes()
  }, [])
  
  // Handle URL parameters only once on mount
  useEffect(() => {
    // Handle template parameters from URL
    const template = searchParams.get('template')
    const position = searchParams.get('position')
    const type = searchParams.get('type')
    const focusAreasParam = searchParams.get('focusAreas')
    const resumeId = searchParams.get('resumeId')
    
    if (position) {
      setJobPosition(position)
    }
    
    if (type) {
      setInterviewCategory(type)
    }
    
    if (focusAreasParam) {
      try {
        const areas = JSON.parse(focusAreasParam)
        if (Array.isArray(areas)) {
          setFocusAreas(areas)
        }
      } catch (e) {
        console.error('Failed to parse focus areas:', e)
      }
    }
    
    // Set template-specific defaults
    if (template === 'software-engineer') {
      setJobRequirements('• Strong programming skills in one or more languages\n• Experience with software development best practices\n• Problem-solving and analytical thinking\n• Team collaboration and communication skills')
      setDifficultyLevel([4])
      setNumQuestions([12])
    } else if (template === 'product-manager') {
      setJobRequirements('• Product strategy and roadmap development\n• Data-driven decision making\n• Cross-functional team leadership\n• Customer-centric mindset\n• Excellent communication skills')
      setDifficultyLevel([3])
      setNumQuestions([10])
    } else if (template === 'sales-representative') {
      setJobRequirements('• Proven sales track record\n• Excellent communication and interpersonal skills\n• Customer relationship management\n• Negotiation and closing skills\n• Self-motivated and target-driven')
      setDifficultyLevel([3])
      setNumQuestions([8])
    } else if (template === 'data-scientist') {
      setJobRequirements('• Strong statistical and mathematical background\n• Proficiency in Python/R and SQL\n• Machine learning and data modeling experience\n• Data visualization and storytelling\n• Business acumen and problem-solving skills')
      setDifficultyLevel([4])
      setNumQuestions([12])
    }
    
    // Store resumeId for later use
    if (resumeId) {
      sessionStorage.setItem('pendingResumeId', resumeId)
    }
  }, []) // Empty dependency array - only run once on mount
  
  // Handle resume selection after resumes are loaded
  useEffect(() => {
    const pendingResumeId = sessionStorage.getItem('pendingResumeId')
    if (pendingResumeId && resumes.length > 0) {
      const resume = resumes.find(r => r.id === pendingResumeId)
      if (resume) {
        setSelectedResume(resume)
        sessionStorage.removeItem('pendingResumeId')
      }
    }
  }, [resumes])
  
  const loadResumes = async () => {
    try {
      setIsLoadingResumes(true)
      setError(null)
      const data = await resumeApi.getMyResumes(0, 100)
      
      // Check if we got valid data
      if (!Array.isArray(data)) {
        console.error('Invalid resume data received:', data)
        setError('Invalid data received from server')
        return
      }
      
      // Filter out any invalid resumes
      const validResumes = data.filter(resume => 
        resume && 
        typeof resume.id === 'string' && 
        resume.id.length > 30 // UUID should be 36 chars with dashes
      )
      
      if (validResumes.length === 0 && data.length > 0) {
        console.warn('No valid resumes found. Data:', data)
        setError('No valid candidates found. Please upload some resumes first.')
      }
      
      setResumes(validResumes)
      setSearchResults(validResumes)
    } catch (error: any) {
      console.error('Failed to load resumes:', error)
      const errorMessage = error?.detail || error?.message || 'Failed to load candidates'
      setError(typeof errorMessage === 'string' ? errorMessage : 'Failed to load candidates. Please make sure you have uploaded some resumes.')
    } finally {
      setIsLoadingResumes(false)
    }
  }

  // Search candidates by name or email
  const searchCandidates = (query: string) => {
    if (!query.trim()) {
      setSearchResults(resumes)
      return
    }
    
    const lowercaseQuery = query.toLowerCase()
    const filtered = resumes.filter(resume => {
      const fullName = `${resume.first_name} ${resume.last_name}`.toLowerCase()
      const email = resume.email?.toLowerCase() || ''
      const title = resume.current_title?.toLowerCase() || ''
      
      return fullName.includes(lowercaseQuery) ||
             email.includes(lowercaseQuery) ||
             title.includes(lowercaseQuery)
    })
    setSearchResults(filtered)
  }

  // Handle search input change
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value
    setSearchQuery(query)
    searchCandidates(query)
    setDisplayLimit(10) // Reset to show first 10 results when searching
  }

  // Update search results when resumes change
  React.useEffect(() => {
    if (!searchQuery) {
      setSearchResults(resumes)
    }
  }, [resumes, searchQuery])

  const handlePrepareInterview = async () => {
    if (!selectedResume) {
      setError('Please select a candidate')
      return
    }
    
    if (!jobPosition.trim()) {
      setError('Please enter a job position')
      return
    }
    
    if (!interviewMode) {
      setError('Please select an interview mode')
      return
    }
    
    // Validate resume ID is a proper UUID
    if (!selectedResume.id || selectedResume.id.length < 32) {
      console.error('Invalid resume ID:', selectedResume)
      setError('Selected candidate has an invalid ID. Please select another candidate.')
      return
    }
    
    setIsGenerating(true)
    setError(null)
    
    try {
      console.log('Preparing interview with resume:', selectedResume.id, 'position:', jobPosition)
      
      // Call the real API to prepare interview
      const response = await interviewsApi.prepareInterview({
        resume_id: selectedResume.id,
        job_position: jobPosition,
        job_requirements: jobRequirements ? { description: jobRequirements } : undefined,
        interview_type: interviewMode,  // Mode: IN_PERSON, VIRTUAL, PHONE
        interview_category: interviewCategory,  // Category: general, technical, behavioral, final
        difficulty_level: difficultyLevel[0],
        num_questions: numQuestions[0],
        focus_areas: focusAreas,
        company_culture: undefined // Could add this field to the form
      })
      
      console.log('Interview preparation response:', response)
      
      if (!response || !response.session_id) {
        throw new Error('Invalid response from server - missing session_id')
      }
      
      // Store minimal data for session page
      sessionStorage.setItem('interviewSessionId', response.session_id)
      
      // Navigate to the session page
      router.push(`/dashboard/interviews/${response.session_id}/session`)
    } catch (error: any) {
      console.error('Failed to prepare interview:', error)
      const errorMessage = error?.detail || error?.message || 'Failed to generate interview. Please try again.'
      setError(typeof errorMessage === 'string' ? errorMessage : 'Failed to generate interview. Please try again.')
      setIsGenerating(false)
    }
  }

  const addFocusArea = () => {
    if (newFocusArea && !focusAreas.includes(newFocusArea)) {
      setFocusAreas([...focusAreas, newFocusArea])
      setNewFocusArea('')
    }
  }

  const removeFocusArea = (area: string) => {
    setFocusAreas(focusAreas.filter(a => a !== area))
  }

  return (
    <div className="container mx-auto py-6 px-4 max-w-6xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Prepare Interview</h1>
        <p className="text-muted-foreground mt-1">
          AI will help you prepare tailored interview questions and insights
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Setup */}
        <div className="lg:col-span-2 space-y-6">
          {/* Candidate Selection */}
          <Card>
            <CardHeader>
              <CardTitle>Select Candidate</CardTitle>
              <CardDescription>Choose the candidate you'll be interviewing</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="relative">
                    <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                    <Input
                      placeholder="Search by name or email..."
                      className="pl-10"
                      value={searchQuery}
                      onChange={handleSearchChange}
                    />
                  </div>
                  {selectedResume && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">
                        Selected: <span className="font-medium text-foreground">{selectedResume.first_name} {selectedResume.last_name}</span>
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedResume(null)}
                        className="h-6 text-xs"
                      >
                        Clear selection
                      </Button>
                    </div>
                  )}
                </div>
                
                <div className="space-y-2 max-h-[400px] overflow-y-auto">
                  {isLoadingResumes ? (
                    <div className="text-center py-8">
                      <Loader2Icon className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
                      <p className="text-sm text-muted-foreground mt-2">Loading candidates...</p>
                    </div>
                  ) : error ? (
                    <Alert variant="destructive">
                      <AlertCircleIcon className="h-4 w-4" />
                      <AlertDescription>{error}</AlertDescription>
                    </Alert>
                  ) : searchResults.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      {searchQuery ? `No candidates found matching "${searchQuery}"` : 'No candidates available'}
                      {!searchQuery && resumes.length === 0 && (
                        <div className="mt-4">
                          <p className="text-sm mb-2">You need to upload resumes before you can prepare interviews.</p>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => router.push('/dashboard/resumes')}
                          >
                            Upload Resumes
                          </Button>
                        </div>
                      )}
                    </div>
                  ) : (
                    <>
                      {searchResults.slice(0, displayLimit).map((candidate) => (
                        <div
                          key={candidate.id}
                          className={`border rounded-lg p-3 cursor-pointer transition-all ${
                            selectedResume?.id === candidate.id
                              ? 'border-primary bg-primary/10 ring-1 ring-primary/20'
                              : 'hover:bg-muted/50'
                          }`}
                          onClick={() => setSelectedResume(candidate)}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <h4 className="font-medium">{candidate.first_name} {candidate.last_name}</h4>
                              <p className="text-sm text-muted-foreground">{candidate.current_title || 'No title'}</p>
                              <p className="text-xs text-muted-foreground">{candidate.email || 'No email'}</p>
                              {selectedResume?.id === candidate.id && candidate.skills && (
                                <div className="flex gap-2 mt-2 flex-wrap">
                                  {candidate.skills.slice(0, 3).map((skill: string) => (
                                    <Badge key={skill} variant="secondary" className="text-xs">
                                      {skill}
                                    </Badge>
                                  ))}
                                  {candidate.skills.length > 3 && (
                                    <Badge variant="outline" className="text-xs">
                                      +{candidate.skills.length - 3} more
                                    </Badge>
                                  )}
                                </div>
                              )}
                            </div>
                            {selectedResume?.id === candidate.id && (
                              <Badge variant="default" className="ml-2">
                                Selected
                              </Badge>
                            )}
                          </div>
                        </div>
                      ))}
                      {/* Show selected candidate if it's outside the display limit */}
                      {selectedResume && 
                       !searchResults.slice(0, displayLimit).find(c => c.id === selectedResume.id) &&
                       searchResults.find(c => c.id === selectedResume.id) && (
                        <>
                          <div className="text-center text-xs text-muted-foreground">• • •</div>
                          <div
                            className="border rounded-lg p-3 border-primary bg-primary/10 ring-1 ring-primary/20"
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <h4 className="font-medium">{selectedResume.first_name} {selectedResume.last_name}</h4>
                                <p className="text-sm text-muted-foreground">{selectedResume.current_title || 'No title'}</p>
                                <p className="text-xs text-muted-foreground">{selectedResume.email || 'No email'}</p>
                                {selectedResume.skills && (
                                  <div className="flex gap-2 mt-2 flex-wrap">
                                    {selectedResume.skills.slice(0, 3).map((skill: string) => (
                                      <Badge key={skill} variant="secondary" className="text-xs">
                                        {skill}
                                      </Badge>
                                    ))}
                                    {selectedResume.skills.length > 3 && (
                                      <Badge variant="outline" className="text-xs">
                                        +{selectedResume.skills.length - 3} more
                                      </Badge>
                                    )}
                                  </div>
                                )}
                              </div>
                              <Badge variant="default" className="ml-2">
                                Selected
                              </Badge>
                            </div>
                          </div>
                        </>
                      )}
                    </>
                  )}
                </div>
                
                {/* Show more button and count */}
                {searchResults.length > 0 && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">
                      Showing {Math.min(displayLimit, searchResults.length)} of {searchResults.length} candidates
                    </span>
                    {searchResults.length > displayLimit && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setDisplayLimit(displayLimit + 10)}
                        className="h-8"
                      >
                        Show more
                      </Button>
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Job Details */}
          <Card>
            <CardHeader>
              <CardTitle>Job Details</CardTitle>
              <CardDescription>Provide information about the position</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="position">Job Position</Label>
                <Input
                  id="position"
                  placeholder="e.g., Senior Software Engineer"
                  value={jobPosition}
                  onChange={(e) => setJobPosition(e.target.value)}
                />
              </div>
              
              <div>
                <Label htmlFor="requirements">Job Requirements & Responsibilities</Label>
                <Textarea
                  id="requirements"
                  placeholder="List key requirements, skills, and responsibilities..."
                  rows={4}
                  value={jobRequirements}
                  onChange={(e) => setJobRequirements(e.target.value)}
                />
              </div>

              <div>
                <Label htmlFor="interview-mode">Interview Mode</Label>
                <Select value={interviewMode || ''} onValueChange={(value) => setInterviewMode(value as 'IN_PERSON' | 'VIRTUAL' | 'PHONE')}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select interview mode" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="IN_PERSON">In-Person Interview</SelectItem>
                    <SelectItem value="VIRTUAL">Virtual Interview (Video)</SelectItem>
                    <SelectItem value="PHONE">Phone Interview</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="interview-category">Interview Category</Label>
                <Select value={interviewCategory} onValueChange={setInterviewCategory}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select interview category" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="general">General Interview</SelectItem>
                    <SelectItem value="technical">Technical Assessment</SelectItem>
                    <SelectItem value="behavioral">Behavioral Interview</SelectItem>
                    <SelectItem value="final">Final Round</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Interview Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>Interview Configuration</CardTitle>
              <CardDescription>Customize the interview parameters</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <div className="flex justify-between mb-2">
                  <Label>Difficulty Level</Label>
                  <span className="text-sm text-muted-foreground">{difficultyLevel[0]}/5</span>
                </div>
                <Slider
                  value={difficultyLevel}
                  onValueChange={setDifficultyLevel}
                  min={1}
                  max={5}
                  step={1}
                  className="w-full"
                />
              </div>

              <div>
                <div className="flex justify-between mb-2">
                  <Label>Number of Questions</Label>
                  <span className="text-sm text-muted-foreground">{numQuestions[0]}</span>
                </div>
                <Slider
                  value={numQuestions}
                  onValueChange={setNumQuestions}
                  min={5}
                  max={30}
                  step={5}
                  className="w-full"
                />
              </div>

              <div>
                <Label>Focus Areas</Label>
                <div className="flex gap-2 mt-2 mb-2">
                  <Input
                    placeholder="Add a focus area..."
                    value={newFocusArea}
                    onChange={(e) => setNewFocusArea(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addFocusArea())}
                  />
                  <Button
                    type="button"
                    size="sm"
                    onClick={addFocusArea}
                  >
                    <PlusIcon className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {focusAreas.map((area) => (
                    <Badge key={area} variant="secondary" className="pr-1">
                      {area}
                      <button
                        onClick={() => removeFocusArea(area)}
                        className="ml-1 hover:text-destructive"
                      >
                        <XIcon className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column - AI Insights Preview */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <SparklesIcon className="h-5 w-5" />
                AI Preparation Preview
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium flex items-center gap-2 mb-2">
                    <BrainIcon className="h-4 w-4" />
                    What AI Will Generate
                  </h4>
                  <ul className="space-y-1 text-sm text-muted-foreground">
                    <li className="flex items-center gap-2">
                      <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      Personalized interview questions
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      Candidate strength analysis
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      Areas to explore
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      Red flags to watch for
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      Interview structure & timing
                    </li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-medium flex items-center gap-2 mb-2">
                    <ClockIcon className="h-4 w-4" />
                    Estimated Duration
                  </h4>
                  <p className="text-sm text-muted-foreground">
                    {numQuestions[0] * 3 + 20} minutes
                  </p>
                </div>

                <div>
                  <h4 className="font-medium flex items-center gap-2 mb-2">
                    <TargetIcon className="h-4 w-4" />
                    Interview Goals
                  </h4>
                  <ul className="space-y-1 text-sm text-muted-foreground">
                    <li>• Assess technical competence</li>
                    <li>• Evaluate culture fit</li>
                    <li>• Understand career goals</li>
                    <li>• Gauge problem-solving skills</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          {error && (
            <Alert variant="destructive">
              <AlertCircleIcon className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Button
            className="w-full"
            size="lg"
            onClick={handlePrepareInterview}
            disabled={!selectedResume || !jobPosition || isGenerating}
          >
            {isGenerating ? (
              <>
                <SparklesIcon className="mr-2 h-4 w-4 animate-pulse" />
                Generating Interview...
              </>
            ) : (
              <>
                <SparklesIcon className="mr-2 h-4 w-4" />
                Generate Interview Prep
              </>
            )}
          </Button>

          <p className="text-xs text-center text-muted-foreground">
            AI will analyze the candidate's resume and generate tailored questions
            based on the job requirements and your specifications.
          </p>
        </div>
      </div>
    </div>
  )
}