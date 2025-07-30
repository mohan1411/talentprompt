import { NextResponse } from 'next/server'

// Mock submission data for testing
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const token = searchParams.get('token')
  
  if (token === 'test-token-123') {
    return NextResponse.json({
      status: 'pending',
      submission_type: 'new',
      expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      recruiter_name: 'John Smith',
      company_name: 'Tech Corp',
      campaign_name: 'Q1 2025 Engineering Hiring',
      is_expired: false
    })
  }
  
  return NextResponse.json({ error: 'Invalid token' }, { status: 404 })
}

// Mock submission endpoint
export async function POST(request: Request) {
  const data = await request.json()
  
  console.log('Received submission:', data)
  
  return NextResponse.json({
    message: 'Submission received successfully',
    submission_id: 'test-submission-id'
  })
}