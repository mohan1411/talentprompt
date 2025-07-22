'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Progress } from '@/components/ui/progress-simple'
import { 
  UploadIcon, 
  FileAudioIcon, 
  CheckCircleIcon, 
  AlertCircleIcon,
  Loader2Icon,
  XIcon
} from 'lucide-react'
import { interviewsApi } from '@/lib/api/interviews'

interface UploadRecordingDialogProps {
  sessionId: string
  onClose: () => void
  onUploadComplete: (transcript: any) => void
}

export function UploadRecordingDialog({
  sessionId,
  onClose,
  onUploadComplete
}: UploadRecordingDialogProps) {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [transcript, setTranscript] = useState<any>(null)

  const allowedTypes = ['audio/mp3', 'audio/mp4', 'audio/wav', 'audio/m4a', 'audio/webm', 'audio/ogg', 'audio/mpeg', 'video/mp4', 'video/webm']
  const maxSize = 500 * 1024 * 1024 // 500MB

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (!selectedFile) return

    // Validate file type
    if (!allowedTypes.includes(selectedFile.type)) {
      setError('Invalid file type. Please upload an audio or video file.')
      return
    }

    // Validate file size
    if (selectedFile.size > maxSize) {
      setError('File too large. Maximum size is 500MB.')
      return
    }

    setFile(selectedFile)
    setError(null)
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setError(null)
    setUploadProgress(0)

    try {
      // Create form data
      const formData = new FormData()
      formData.append('file', file)

      // Upload with progress tracking
      const response = await fetch(`/api/v1/interviews/sessions/${sessionId}/upload-recording`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Upload failed')
      }

      const result = await response.json()
      
      // Handle different response statuses
      if (result.status === 'processing') {
        // Show processing message
        setUploadProgress(50)
        setSuccess(true)
        setTranscript({
          message: 'Recording is being processed. This may take a few minutes.',
          status: 'processing'
        })
      } else if (result.status === 'completed') {
        // Show completed transcript
        setUploadProgress(100)
        setSuccess(true)
        setTranscript(result.transcript)
        setTimeout(() => {
          onUploadComplete(result.transcript)
        }, 2000)
      } else if (result.status === 'error') {
        throw new Error(result.error || 'Transcription failed')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
      setUploading(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Upload Interview Recording</DialogTitle>
          <DialogDescription>
            Upload an audio or video recording of the interview for transcription and analysis.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {!success ? (
            <>
              {/* File Input */}
              <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6">
                <input
                  type="file"
                  accept="audio/*,video/*"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="file-upload"
                  disabled={uploading}
                />
                <label
                  htmlFor="file-upload"
                  className="flex flex-col items-center cursor-pointer"
                >
                  {file ? (
                    <>
                      <FileAudioIcon className="h-12 w-12 text-muted-foreground mb-2" />
                      <p className="text-sm font-medium">{file.name}</p>
                      <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
                    </>
                  ) : (
                    <>
                      <UploadIcon className="h-12 w-12 text-muted-foreground mb-2" />
                      <p className="text-sm font-medium">Click to upload recording</p>
                      <p className="text-xs text-muted-foreground">MP3, MP4, WAV, M4A up to 500MB</p>
                    </>
                  )}
                </label>
              </div>

              {/* Error Alert */}
              {error && (
                <Alert variant="destructive">
                  <AlertCircleIcon className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {/* Upload Progress */}
              {uploading && (
                <div className="space-y-2">
                  <Progress value={uploadProgress} />
                  <p className="text-sm text-muted-foreground text-center">
                    Uploading and processing...
                  </p>
                </div>
              )}

              {/* Actions */}
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={onClose} disabled={uploading}>
                  Cancel
                </Button>
                <Button onClick={handleUpload} disabled={!file || uploading}>
                  {uploading ? (
                    <>
                      <Loader2Icon className="h-4 w-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <UploadIcon className="h-4 w-4 mr-2" />
                      Upload & Transcribe
                    </>
                  )}
                </Button>
              </div>
            </>
          ) : (
            /* Success State */
            <div className="text-center py-6">
              <CheckCircleIcon className="h-16 w-16 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Upload Successful!</h3>
              <p className="text-muted-foreground mb-4">
                {transcript?.message || 'Your recording has been processed successfully.'}
              </p>
              
              {transcript?.speakers && (
                <div className="text-left bg-muted/50 rounded-lg p-4 mb-4">
                  <h4 className="font-medium mb-2">Detected Speakers:</h4>
                  {Object.entries(transcript.speakers).map(([id, speaker]: [string, any]) => (
                    <div key={id} className="text-sm">
                      <span className="font-medium">Speaker {id}:</span>{' '}
                      <span className="text-muted-foreground">
                        {speaker.likely_role} (confidence: {(speaker.confidence * 100).toFixed(0)}%)
                      </span>
                    </div>
                  ))}
                </div>
              )}
              
              <Button onClick={() => onUploadComplete(transcript)}>
                View Analysis
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}