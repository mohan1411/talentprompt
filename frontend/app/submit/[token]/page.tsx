"use client"

import { useState, useEffect } from "react"
import { useParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select-simple"
import { Checkbox } from "@/components/ui/checkbox"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Upload, CheckCircle, XCircle, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface SubmissionInfo {
  status: string
  submission_type: string
  expires_at: string
  recruiter_name?: string
  company_name?: string
  campaign_name?: string
  is_expired: boolean
}

interface FormData {
  email: string
  first_name: string
  last_name: string
  phone: string
  linkedin_url: string
  availability: string
  salary_min: string
  salary_max: string
  salary_currency: string
  remote_preference: boolean
  hybrid_preference: boolean
  onsite_preference: boolean
  preferred_locations: string
  resume_text: string
  resume_file?: File
}

export default function SubmitPage() {
  const params = useParams()
  const token = params.token as string
  
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submissionInfo, setSubmissionInfo] = useState<SubmissionInfo | null>(null)
  
  const [formData, setFormData] = useState<FormData>({
    email: "",
    first_name: "",
    last_name: "",
    phone: "",
    linkedin_url: "",
    availability: "not_looking",
    salary_min: "",
    salary_max: "",
    salary_currency: "USD",
    remote_preference: false,
    hybrid_preference: false,
    onsite_preference: false,
    preferred_locations: "",
    resume_text: ""
  })
  
  const [dragActive, setDragActive] = useState(false)
  
  useEffect(() => {
    fetchSubmissionInfo()
  }, [token])
  
  const fetchSubmissionInfo = async () => {
    try {
      // Try backend first, fallback to test API
      let response
      try {
        response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/submissions/submit/${token}`)
      } catch (backendError) {
        // If backend is not available, use test API
        console.log("Backend not available, using test API")
        response = await fetch(`/api/test-submission?token=${token}`)
      }
      
      if (!response.ok) {
        throw new Error("Invalid submission link")
      }
      
      const data = await response.json()
      setSubmissionInfo(data)
      
      if (data.is_expired) {
        setError("This submission link has expired.")
      } else if (data.status !== "pending") {
        setError("This submission has already been completed.")
      }
    } catch (err) {
      setError("Invalid or expired submission link.")
    } finally {
      setLoading(false)
    }
  }
  
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }
  
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0])
    }
  }
  
  const handleFileUpload = (file: File) => {
    if (file.size > 10 * 1024 * 1024) {
      setError("File size must be less than 10MB")
      return
    }
    
    if (!file.name.match(/\.(pdf|doc|docx)$/)) {
      setError("Please upload a PDF or Word document")
      return
    }
    
    setFormData({ ...formData, resume_file: file })
    setError(null)
  }
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    
    try {
      // Prepare submission data
      const submitData = {
        email: formData.email,
        first_name: formData.first_name,
        last_name: formData.last_name,
        phone: formData.phone,
        linkedin_url: formData.linkedin_url,
        availability: formData.availability,
        salary_expectations: {
          min: formData.salary_min ? parseInt(formData.salary_min) : null,
          max: formData.salary_max ? parseInt(formData.salary_max) : null,
          currency: formData.salary_currency
        },
        location_preferences: {
          remote: formData.remote_preference,
          hybrid: formData.hybrid_preference,
          onsite: formData.onsite_preference,
          locations: formData.preferred_locations.split(",").map(l => l.trim()).filter(Boolean)
        },
        resume_text: formData.resume_text
      }
      
      // If file uploaded, convert to base64
      if (formData.resume_file) {
        const reader = new FileReader()
        reader.onload = async (e) => {
          const base64 = e.target?.result as string
          submitData.resume_file = base64.split(",")[1] // Remove data:... prefix
          
          await submitToAPI(submitData)
        }
        reader.readAsDataURL(formData.resume_file)
      } else {
        await submitToAPI(submitData)
      }
    } catch (err) {
      setError("Failed to submit. Please try again.")
      setSubmitting(false)
    }
  }
  
  const submitToAPI = async (data: any) => {
    let response
    try {
      response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/submissions/submit/${token}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
      })
    } catch (backendError) {
      // If backend is not available, use test API
      console.log("Backend not available, using test API for submission")
      response = await fetch(`/api/test-submission?token=${token}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
      })
    }
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || "Submission failed")
    }
    
    setSubmitted(true)
    setSubmitting(false)
  }
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }
  
  if (submitted) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6">
            <div className="text-center">
              <CheckCircle className="h-16 w-16 text-green-600 mx-auto mb-4" />
              <h2 className="text-2xl font-bold mb-2">Submission Successful!</h2>
              <p className="text-muted-foreground">
                Thank you for submitting your profile. {submissionInfo?.recruiter_name} will review it and get back to you soon.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }
  
  if (error && (submissionInfo?.is_expired || submissionInfo?.status !== "pending")) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6">
            <div className="text-center">
              <XCircle className="h-16 w-16 text-red-600 mx-auto mb-4" />
              <h2 className="text-2xl font-bold mb-2">Submission Unavailable</h2>
              <p className="text-muted-foreground">{error}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }
  
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-2xl mx-auto px-4">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-primary mb-2">Promtitude</h1>
          <p className="text-muted-foreground">AI-Powered Recruitment Platform</p>
        </div>
        
        <Card>
          <CardHeader>
            <CardTitle>
              {submissionInfo?.submission_type === "update" ? "Update Your Profile" : "Submit Your Profile"}
            </CardTitle>
            <CardDescription>
              {submissionInfo?.recruiter_name} from {submissionInfo?.company_name} has invited you to {submissionInfo?.submission_type === "update" ? "update" : "submit"} your profile.
              {submissionInfo?.campaign_name && ` Campaign: ${submissionInfo.campaign_name}`}
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            {error && (
              <Alert variant="destructive" className="mb-6">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Basic Information */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Basic Information</h3>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="first_name">First Name *</Label>
                    <Input
                      id="first_name"
                      required
                      value={formData.first_name}
                      onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="last_name">Last Name *</Label>
                    <Input
                      id="last_name"
                      required
                      value={formData.last_name}
                      onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                    />
                  </div>
                </div>
                
                <div>
                  <Label htmlFor="email">Email *</Label>
                  <Input
                    id="email"
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  />
                </div>
                
                <div>
                  <Label htmlFor="phone">Phone</Label>
                  <Input
                    id="phone"
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  />
                </div>
                
                <div>
                  <Label htmlFor="linkedin_url">LinkedIn Profile</Label>
                  <Input
                    id="linkedin_url"
                    type="url"
                    placeholder="https://linkedin.com/in/yourprofile"
                    value={formData.linkedin_url}
                    onChange={(e) => setFormData({ ...formData, linkedin_url: e.target.value })}
                  />
                </div>
              </div>
              
              {/* Resume Upload */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Resume/CV</h3>
                
                <div
                  className={cn(
                    "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
                    dragActive ? "border-primary bg-primary/5" : "border-gray-300 hover:border-gray-400",
                    formData.resume_file && "bg-green-50 border-green-500"
                  )}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                  onClick={() => document.getElementById("resume-upload")?.click()}
                >
                  <Upload className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  {formData.resume_file ? (
                    <p className="text-sm text-green-600">
                      {formData.resume_file.name} uploaded
                    </p>
                  ) : (
                    <>
                      <p className="text-sm text-gray-600 mb-2">
                        Drag and drop your resume here, or click to browse
                      </p>
                      <p className="text-xs text-gray-500">
                        PDF or Word format, max 10MB
                      </p>
                    </>
                  )}
                  <input
                    id="resume-upload"
                    type="file"
                    className="hidden"
                    accept=".pdf,.doc,.docx"
                    onChange={(e) => {
                      if (e.target.files?.[0]) {
                        handleFileUpload(e.target.files[0])
                      }
                    }}
                  />
                </div>
                
                <div>
                  <Label htmlFor="resume_text">Or paste your resume text</Label>
                  <Textarea
                    id="resume_text"
                    rows={6}
                    placeholder="Paste your resume content here..."
                    value={formData.resume_text}
                    onChange={(e) => setFormData({ ...formData, resume_text: e.target.value })}
                  />
                </div>
              </div>
              
              {/* Availability & Preferences */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Availability & Preferences</h3>
                
                <div>
                  <Label htmlFor="availability">Current Availability</Label>
                  <Select
                    value={formData.availability}
                    onValueChange={(value) => setFormData({ ...formData, availability: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="immediate">Immediate</SelectItem>
                      <SelectItem value="1_month">Within 1 month</SelectItem>
                      <SelectItem value="3_months">Within 3 months</SelectItem>
                      <SelectItem value="not_looking">Not actively looking</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label>Salary Expectations</Label>
                  <div className="grid grid-cols-3 gap-2">
                    <Input
                      type="number"
                      placeholder="Min"
                      value={formData.salary_min}
                      onChange={(e) => setFormData({ ...formData, salary_min: e.target.value })}
                    />
                    <Input
                      type="number"
                      placeholder="Max"
                      value={formData.salary_max}
                      onChange={(e) => setFormData({ ...formData, salary_max: e.target.value })}
                    />
                    <Select
                      value={formData.salary_currency}
                      onValueChange={(value) => setFormData({ ...formData, salary_currency: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="USD">USD</SelectItem>
                        <SelectItem value="EUR">EUR</SelectItem>
                        <SelectItem value="GBP">GBP</SelectItem>
                        <SelectItem value="INR">INR</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                <div>
                  <Label>Work Preferences</Label>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="remote"
                        checked={formData.remote_preference}
                        onCheckedChange={(checked) => 
                          setFormData({ ...formData, remote_preference: checked as boolean })
                        }
                      />
                      <label htmlFor="remote" className="text-sm">Remote</label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="hybrid"
                        checked={formData.hybrid_preference}
                        onCheckedChange={(checked) => 
                          setFormData({ ...formData, hybrid_preference: checked as boolean })
                        }
                      />
                      <label htmlFor="hybrid" className="text-sm">Hybrid</label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="onsite"
                        checked={formData.onsite_preference}
                        onCheckedChange={(checked) => 
                          setFormData({ ...formData, onsite_preference: checked as boolean })
                        }
                      />
                      <label htmlFor="onsite" className="text-sm">On-site</label>
                    </div>
                  </div>
                </div>
                
                <div>
                  <Label htmlFor="preferred_locations">Preferred Locations</Label>
                  <Input
                    id="preferred_locations"
                    placeholder="e.g., New York, San Francisco, London"
                    value={formData.preferred_locations}
                    onChange={(e) => setFormData({ ...formData, preferred_locations: e.target.value })}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Separate multiple locations with commas
                  </p>
                </div>
              </div>
              
              <div className="pt-6">
                <Button
                  type="submit"
                  className="w-full"
                  size="lg"
                  disabled={submitting || !formData.first_name || !formData.last_name || !formData.email}
                >
                  {submitting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Submitting...
                    </>
                  ) : (
                    "Submit Profile"
                  )}
                </Button>
              </div>
              
              <p className="text-xs text-center text-muted-foreground">
                Your information will only be accessible to {submissionInfo?.recruiter_name} and their team at {submissionInfo?.company_name}.
                By submitting, you agree to our privacy policy.
              </p>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}