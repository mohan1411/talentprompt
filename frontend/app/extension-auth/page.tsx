'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { 
  CopyIcon, 
  CheckIcon, 
  ClockIcon, 
  AlertCircleIcon,
  ChromeIcon,
  RefreshCwIcon,
  Loader2Icon
} from 'lucide-react'
import { authApi } from '@/lib/api/auth'
import { useAuth } from '@/lib/auth/context'

export default function ExtensionAuthPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { user, isLoading: authLoading } = useAuth()
  
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isCopied, setIsCopied] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [ttl, setTtl] = useState<number>(0)
  const [tokenStatus, setTokenStatus] = useState<any>(null)
  
  const email = searchParams.get('email')
  
  useEffect(() => {
    // Check if user is logged in
    if (!authLoading && !user) {
      // Redirect to login with return URL
      router.push(`/login?return=${encodeURIComponent(window.location.pathname + window.location.search)}`)
    }
  }, [user, authLoading, router])
  
  useEffect(() => {
    // Check token status on load
    if (user) {
      checkTokenStatus()
    }
  }, [user])
  
  useEffect(() => {
    // Update TTL countdown
    if (ttl > 0) {
      const timer = setTimeout(() => {
        setTtl(ttl - 1)
      }, 1000)
      return () => clearTimeout(timer)
    }
  }, [ttl])
  
  const checkTokenStatus = async () => {
    try {
      const status = await authApi.getExtensionTokenStatus()
      setTokenStatus(status)
      if (status.has_token) {
        setTtl(status.ttl)
      }
    } catch (err) {
      console.error('Failed to check token status:', err)
    }
  }
  
  const generateToken = async () => {
    setIsGenerating(true)
    setError(null)
    
    try {
      console.log('Generating extension token...')
      const response = await authApi.generateExtensionToken()
      console.log('Token response:', response)
      setAccessToken(response.access_token)
      setTtl(response.expires_in)
      await checkTokenStatus()
    } catch (err: any) {
      console.error('Failed to generate token:', err)
      setError(err.detail || 'Failed to generate access token')
    } finally {
      setIsGenerating(false)
    }
  }
  
  const copyToClipboard = async () => {
    if (!accessToken) return
    
    try {
      await navigator.clipboard.writeText(accessToken)
      setIsCopied(true)
      setTimeout(() => setIsCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }
  
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }
  
  if (authLoading) {
    return (
      <div className="container mx-auto flex items-center justify-center min-h-screen">
        <Loader2Icon className="h-8 w-8 animate-spin" />
      </div>
    )
  }
  
  if (!user) {
    return null // Will redirect to login
  }
  
  // Check if user is OAuth user
  const isOAuthUser = tokenStatus?.is_oauth_user
  
  if (tokenStatus && !isOAuthUser) {
    return (
      <div className="container mx-auto py-12 px-4 max-w-2xl">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ChromeIcon className="h-6 w-6" />
              Chrome Extension Login
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Alert>
              <AlertCircleIcon className="h-4 w-4" />
              <AlertTitle>Password Authentication</AlertTitle>
              <AlertDescription>
                You can log into the Chrome extension using your email and password directly.
                Access tokens are only needed for users who signed up with Google or LinkedIn.
              </AlertDescription>
            </Alert>
            
            <div className="mt-4">
              <Button variant="outline" onClick={() => router.push('/profile')}>
                Go to Profile
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }
  
  return (
    <div className="container mx-auto py-12 px-4 max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ChromeIcon className="h-6 w-6" />
            Chrome Extension Access Code
          </CardTitle>
          <CardDescription>
            Generate a temporary access code to log into the Promtitude Chrome extension
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Email info */}
          {email && email !== user.email && (
            <Alert>
              <AlertCircleIcon className="h-4 w-4" />
              <AlertDescription>
                You're logged in as <strong>{user.email}</strong> but trying to get a code for <strong>{email}</strong>.
                Please log in with the correct account.
              </AlertDescription>
            </Alert>
          )}
          
          {/* Error message */}
          {error && (
            <Alert variant="destructive">
              <AlertCircleIcon className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          
          {/* Token display */}
          {accessToken ? (
            <div className="space-y-4">
              <div className="bg-slate-100 dark:bg-slate-800 rounded-lg p-6 text-center">
                <p className="text-sm text-muted-foreground mb-2">Your access code:</p>
                <div className="flex items-center justify-center gap-4">
                  <code className="text-3xl font-mono font-bold tracking-wider">
                    {accessToken}
                  </code>
                  <Button
                    size="icon"
                    variant="outline"
                    onClick={copyToClipboard}
                    className="flex-shrink-0"
                  >
                    {isCopied ? (
                      <CheckIcon className="h-4 w-4 text-green-600" />
                    ) : (
                      <CopyIcon className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
              
              {/* Timer */}
              <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                <ClockIcon className="h-4 w-4" />
                <span>Expires in {formatTime(ttl)}</span>
              </div>
              
              {/* Instructions */}
              <Alert>
                <AlertTitle className="mb-2">How to use this code:</AlertTitle>
                <AlertDescription asChild>
                  <ol className="list-decimal list-inside space-y-1">
                    <li>Open the Promtitude Chrome extension</li>
                    <li>Enter your email: <strong>{user.email}</strong></li>
                    <li>In the password field, enter: <strong>{accessToken}</strong></li>
                    <li>Click Login</li>
                  </ol>
                </AlertDescription>
              </Alert>
              
              {/* Generate new button */}
              <Button
                onClick={generateToken}
                disabled={isGenerating || ttl > 540} // Can't regenerate if more than 9 mins left
                variant="outline"
                className="w-full"
              >
                {isGenerating ? (
                  <>
                    <Loader2Icon className="h-4 w-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <RefreshCwIcon className="h-4 w-4 mr-2" />
                    Generate New Code
                  </>
                )}
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {/* No token state */}
              <Alert>
                <AlertDescription>
                  Click the button below to generate a temporary access code for the Chrome extension.
                  The code will be valid for 10 minutes.
                </AlertDescription>
              </Alert>
              
              <Button
                onClick={generateToken}
                disabled={isGenerating}
                size="lg"
                className="w-full"
              >
                {isGenerating ? (
                  <>
                    <Loader2Icon className="h-4 w-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  'Generate Access Code'
                )}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}