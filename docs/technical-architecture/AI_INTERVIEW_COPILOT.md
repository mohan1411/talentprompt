# AI Interview Copilot Technical Architecture

## Table of Contents
1. [How AI Interview Copilot Works](#how-ai-interview-copilot-works)
2. [System Architecture](#system-architecture)
3. [Real-Time Transcription](#real-time-transcription)
4. [AI Analysis Pipeline](#ai-analysis-pipeline)
5. [WebSocket Implementation](#websocket-implementation)
6. [User Interface Design](#user-interface-design)
7. [Performance & Latency](#performance--latency)
8. [Security & Privacy](#security--privacy)

## How AI Interview Copilot Works

The AI Interview Copilot provides real-time assistance during interviews, analyzing conversation, suggesting questions, and detecting important moments.

### User Experience

```
┌─────────────────────────────────────────────────────────┐
│                  Interview Session                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Interviewer: "Tell me about your experience with AWS" │
│                                                         │
│  Candidate: "I've worked with AWS for 3 years..."     │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                   AI Copilot Panel                      │
├─────────────┬────────────┬─────────────┬───────────────┤
│  Insights   │ Questions  │ Fact Check  │  Sentiment    │
├─────────────┴────────────┴─────────────┴───────────────┤
│ 💡 Candidate mentioned     │ 🎯 Follow-up Questions:   │
│    3 years AWS experience │                            │
│                           │ 1. "Which AWS services    │
│ ⚡ Key Skills Detected:   │     did you use most?"    │
│    • EC2, S3, Lambda      │                            │
│    • CloudFormation       │ 2. "Can you describe a    │
│                           │     complex AWS           │
│ ⚠️  Vague on scaling     │     architecture you      │
│    experience - probe     │     designed?"            │
│    deeper                 │                            │
└───────────────────────────┴────────────────────────────┘
```

### Feature Overview

1. **Live Transcription** - Real-time speech-to-text
2. **Smart Insights** - Context-aware observations
3. **Question Suggestions** - Dynamic follow-ups
4. **Fact Checking** - Verify claims instantly
5. **Sentiment Analysis** - Emotional state tracking

## System Architecture

### High-Level Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Audio Stream   │────▶│ Transcription   │────▶│  AI Analysis    │
│  (Browser)      │     │  Service        │     │  (GPT-4o-mini)  │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         │                       ▼                       ▼
         │              ┌─────────────────┐     ┌─────────────────┐
         │              │                 │     │                 │
         └─────────────▶│  WebSocket      │────▶│  UI Updates     │
                        │  Server         │     │  (React)        │
                        │                 │     │                 │
                        └─────────────────┘     └─────────────────┘
```

### Component Details

```python
# Core Services Architecture
class InterviewCopilotSystem:
    """Main system orchestrator"""
    
    def __init__(self):
        self.transcription_service = TranscriptionService()
        self.ai_analyzer = AIAnalyzer()
        self.websocket_manager = WebSocketManager()
        self.insight_generator = InsightGenerator()
        self.cache_manager = CacheManager()
    
    async def process_audio_stream(self, audio_stream):
        """Main processing pipeline"""
        
        # 1. Transcribe audio
        transcript = await self.transcription_service.transcribe(audio_stream)
        
        # 2. Buffer and analyze
        if self.should_analyze(transcript):
            analysis = await self.ai_analyzer.analyze(transcript)
            
            # 3. Generate insights
            insights = self.insight_generator.process(analysis)
            
            # 4. Send to UI
            await self.websocket_manager.broadcast(insights)
```

## Real-Time Transcription

### Audio Processing Pipeline

```python
class TranscriptionService:
    """Handles real-time speech-to-text conversion"""
    
    def __init__(self):
        self.buffer_size = 1024  # Audio chunk size
        self.sample_rate = 16000  # 16kHz for speech
        self.channels = 1  # Mono audio
        
    async def transcribe_stream(self, audio_stream):
        """Process audio stream in real-time"""
        
        # Initialize speech recognition
        recognizer = self._init_recognizer()
        
        # Process audio chunks
        async for audio_chunk in audio_stream:
            # Convert to proper format
            processed_chunk = self._process_audio(audio_chunk)
            
            # Send to recognition service
            partial_result = await recognizer.process_chunk(processed_chunk)
            
            if partial_result:
                yield {
                    'type': 'partial',
                    'text': partial_result.text,
                    'confidence': partial_result.confidence,
                    'timestamp': time.time()
                }
            
            # Check for final results
            if recognizer.is_final():
                final_result = recognizer.get_final()
                yield {
                    'type': 'final',
                    'text': final_result.text,
                    'confidence': final_result.confidence,
                    'timestamp': time.time(),
                    'speaker': self._identify_speaker(final_result)
                }
```

### WebSocket Audio Streaming

```typescript
// Frontend audio capture and streaming
class AudioStreamer {
  private mediaRecorder: MediaRecorder;
  private websocket: WebSocket;
  
  async startRecording() {
    // Get user permission
    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        sampleRate: 16000
      } 
    });
    
    // Create MediaRecorder
    this.mediaRecorder = new MediaRecorder(stream, {
      mimeType: 'audio/webm',
      audioBitsPerSecond: 128000
    });
    
    // Stream audio chunks
    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0 && this.websocket.readyState === WebSocket.OPEN) {
        this.websocket.send(event.data);
      }
    };
    
    // Start recording in 100ms chunks
    this.mediaRecorder.start(100);
  }
}
```

## AI Analysis Pipeline

### GPT-4o-mini Integration

```python
class AIAnalyzer:
    """Real-time interview analysis using GPT-4o-mini"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.context_window = 2000  # Characters to analyze
        self.analysis_interval = 5  # Seconds between analyses
        
    async def analyze_transcript(
        self,
        transcript: str,
        current_question: Optional[str] = None,
        candidate_info: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Analyze interview segment with AI"""
        
        # Build context
        context = self._build_context(transcript, current_question, candidate_info)
        
        # Create analysis prompt
        prompt = f"""
        You are an expert interview copilot. Analyze this interview segment:
        
        {context}
        
        Provide JSON response with:
        1. Key insights about the candidate's response
        2. Suggested follow-up questions (3-5)
        3. Any claims that should be fact-checked
        4. Sentiment analysis (positive/neutral/negative/stressed)
        5. Important moments or red flags
        
        Focus on:
        - Technical accuracy
        - Communication clarity
        - Experience depth
        - Cultural fit indicators
        """
        
        # Call GPT-4o-mini
        response = await self._call_ai(prompt)
        
        # Parse and structure response
        return self._parse_ai_response(response)
    
    async def _call_ai(self, prompt: str) -> str:
        """Call OpenAI API with retry logic"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert interview assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Low temperature for consistency
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
            
        except RateLimitError:
            # Fallback to cached insights
            return await self._get_cached_insights()
```

### Insight Generation

```python
class InsightGenerator:
    """Generate actionable insights from AI analysis"""
    
    def process(self, ai_analysis: Dict) -> List[Dict]:
        """Convert AI analysis into UI-ready insights"""
        
        insights = []
        timestamp = datetime.now()
        
        # Process suggested questions
        for question in ai_analysis.get('suggestedQuestions', []):
            insights.append({
                'id': str(uuid.uuid4()),
                'type': 'question',
                'icon': 'QuestionMarkCircleIcon',
                'color': 'blue',
                'title': 'Suggested Question',
                'content': question,
                'timestamp': timestamp,
                'priority': 'medium'
            })
        
        # Process fact checks
        for fact in ai_analysis.get('factChecks', []):
            if not fact.get('verified', True):
                insights.append({
                    'id': str(uuid.uuid4()),
                    'type': 'fact_check',
                    'icon': 'ExclamationTriangleIcon',
                    'color': 'yellow',
                    'title': 'Verify Claim',
                    'content': f"{fact['claim']} - {fact['explanation']}",
                    'timestamp': timestamp,
                    'priority': 'high'
                })
        
        # Process sentiment
        sentiment = ai_analysis.get('sentiment', {})
        if sentiment.get('overall') == 'stressed':
            insights.append({
                'id': str(uuid.uuid4()),
                'type': 'warning',
                'icon': 'HeartIcon',
                'color': 'orange',
                'title': 'Candidate Stress Detected',
                'content': 'Consider a lighter question or brief break',
                'timestamp': timestamp,
                'priority': 'high'
            })
        
        # Add key moments
        for moment in ai_analysis.get('keyMoments', []):
            insights.append({
                'id': str(uuid.uuid4()),
                'type': 'highlight',
                'icon': 'StarIcon',
                'color': 'green',
                'title': 'Key Moment',
                'content': moment,
                'timestamp': timestamp,
                'priority': 'low'
            })
        
        return sorted(insights, key=lambda x: 
                     {'high': 0, 'medium': 1, 'low': 2}[x['priority']])
```

### Sentiment Analysis

```python
def analyze_sentiment(self, transcript_segment: str) -> Dict:
    """Analyze emotional state and communication patterns"""
    
    # Linguistic markers
    stress_indicators = {
        'verbal': ['um', 'uh', 'well', 'actually', 'like', 'you know'],
        'patterns': ['repetition', 'incomplete_sentences', 'long_pauses'],
        'defensive': ['but', 'however', 'that said', 'to be honest']
    }
    
    positive_indicators = {
        'confidence': ['definitely', 'absolutely', 'certainly', 'I achieved'],
        'enthusiasm': ['excited', 'passionate', 'love', 'enjoy'],
        'clarity': ['specifically', 'for example', 'resulted in']
    }
    
    # Analyze patterns
    words = transcript_segment.lower().split()
    
    stress_score = sum(
        words.count(indicator) 
        for indicator in stress_indicators['verbal']
    )
    
    positive_score = sum(
        words.count(indicator) 
        for indicator in positive_indicators['confidence'] + 
                       positive_indicators['enthusiasm']
    )
    
    # Calculate overall sentiment
    if stress_score > 10:
        sentiment = 'stressed'
        confidence = 0.8
    elif positive_score > stress_score * 2:
        sentiment = 'positive'
        confidence = 0.85
    elif stress_score > positive_score:
        sentiment = 'negative'
        confidence = 0.7
    else:
        sentiment = 'neutral'
        confidence = 0.6
    
    return {
        'overall': sentiment,
        'confidence': confidence,
        'indicators': self._extract_indicators(transcript_segment),
        'trend': self._calculate_trend()
    }
```

## WebSocket Implementation

### Server-Side WebSocket Handler

```python
class InterviewWebSocketHandler:
    """Handles WebSocket connections for interview sessions"""
    
    def __init__(self):
        self.active_sessions = {}
        self.transcription_buffers = {}
        
    async def handle_connection(self, websocket: WebSocket, session_id: str):
        """Handle new WebSocket connection"""
        
        await websocket.accept()
        
        # Initialize session
        self.active_sessions[session_id] = {
            'websocket': websocket,
            'start_time': datetime.now(),
            'transcript': [],
            'insights': [],
            'analysis_task': None
        }
        
        try:
            # Start analysis loop
            analysis_task = asyncio.create_task(
                self._analysis_loop(session_id)
            )
            self.active_sessions[session_id]['analysis_task'] = analysis_task
            
            # Handle incoming messages
            while True:
                data = await websocket.receive()
                
                if data['type'] == 'websocket.receive':
                    await self._handle_message(session_id, data)
                elif data['type'] == 'websocket.disconnect':
                    break
                    
        finally:
            await self._cleanup_session(session_id)
    
    async def _handle_message(self, session_id: str, data: Dict):
        """Process incoming WebSocket messages"""
        
        message = data.get('bytes') or data.get('text')
        
        if isinstance(message, bytes):
            # Audio data
            await self._process_audio(session_id, message)
        else:
            # Control message
            message_data = json.loads(message)
            await self._handle_control_message(session_id, message_data)
    
    async def _analysis_loop(self, session_id: str):
        """Continuous analysis loop for session"""
        
        while session_id in self.active_sessions:
            try:
                # Wait for analysis interval
                await asyncio.sleep(5)
                
                # Get recent transcript
                session = self.active_sessions[session_id]
                recent_transcript = self._get_recent_transcript(session)
                
                if recent_transcript:
                    # Analyze with AI
                    analysis = await self.ai_analyzer.analyze_transcript(
                        recent_transcript
                    )
                    
                    # Generate insights
                    insights = self.insight_generator.process(analysis)
                    
                    # Send to client
                    await self._send_insights(session_id, insights)
                    
            except Exception as e:
                logger.error(f"Analysis error: {e}")
```

### Client-Side WebSocket

```typescript
// React hook for WebSocket connection
export const useInterviewCopilot = (sessionId: string) => {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const [transcript, setTranscript] = useState<string>('');
  
  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/interview/${sessionId}`);
    
    ws.onopen = () => {
      setConnectionStatus('connected');
      console.log('Copilot connected');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'insights':
          setInsights(prev => [...data.insights, ...prev].slice(0, 50));
          break;
          
        case 'transcript':
          setTranscript(prev => prev + ' ' + data.text);
          break;
          
        case 'sentiment':
          updateSentimentDisplay(data.sentiment);
          break;
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('disconnected');
    };
    
    return () => {
      ws.close();
    };
  }, [sessionId]);
  
  return { insights, connectionStatus, transcript };
};
```

## User Interface Design

### React Component Architecture

```typescript
// Main Copilot Component
export const AIInterviewCopilot: React.FC<CopilotProps> = ({ sessionId }) => {
  const { insights, connectionStatus } = useInterviewCopilot(sessionId);
  const [activeTab, setActiveTab] = useState<'insights' | 'questions' | 'factcheck' | 'sentiment'>('insights');
  
  // Filter insights by type
  const filteredInsights = useMemo(() => {
    switch (activeTab) {
      case 'questions':
        return insights.filter(i => i.type === 'question');
      case 'factcheck':
        return insights.filter(i => i.type === 'fact_check');
      case 'sentiment':
        return insights.filter(i => i.type === 'sentiment' || i.type === 'warning');
      default:
        return insights;
    }
  }, [insights, activeTab]);
  
  return (
    <div className="bg-white rounded-lg shadow-lg h-full flex flex-col">
      {/* Header */}
      <div className="border-b p-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">AI Interview Copilot</h3>
          <ConnectionStatus status={connectionStatus} />
        </div>
      </div>
      
      {/* Tabs */}
      <div className="border-b">
        <nav className="flex space-x-8 px-4">
          {tabs.map((tab) => (
            <TabButton
              key={tab.id}
              active={activeTab === tab.id}
              onClick={() => setActiveTab(tab.id)}
              icon={tab.icon}
              label={tab.label}
              count={tab.getCount(insights)}
            />
          ))}
        </nav>
      </div>
      
      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        <AnimatePresence mode="wait">
          {filteredInsights.length > 0 ? (
            <motion.div className="space-y-3">
              {filteredInsights.map((insight) => (
                <InsightCard key={insight.id} insight={insight} />
              ))}
            </motion.div>
          ) : (
            <EmptyState tab={activeTab} />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};
```

### Insight Card Component

```typescript
const InsightCard: React.FC<{ insight: Insight }> = ({ insight }) => {
  const Icon = iconMap[insight.icon];
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
    yellow: 'bg-yellow-50 text-yellow-700 border-yellow-200',
    green: 'bg-green-50 text-green-700 border-green-200',
    orange: 'bg-orange-50 text-orange-700 border-orange-200',
    red: 'bg-red-50 text-red-700 border-red-200'
  };
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className={`p-4 rounded-lg border ${colorClasses[insight.color]}`}
    >
      <div className="flex items-start space-x-3">
        <Icon className="h-5 w-5 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <h4 className="font-medium">{insight.title}</h4>
          <p className="mt-1 text-sm">{insight.content}</p>
          <p className="mt-2 text-xs opacity-70">
            {formatRelativeTime(insight.timestamp)}
          </p>
        </div>
        {insight.priority === 'high' && (
          <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-700 rounded">
            High Priority
          </span>
        )}
      </div>
    </motion.div>
  );
};
```

## Performance & Latency

### Performance Metrics

```python
# System Performance Benchmarks
PERFORMANCE_METRICS = {
    "transcription_latency": {
        "average": 150,  # ms from speech to text
        "p95": 250,
        "p99": 400
    },
    "ai_analysis_latency": {
        "average": 1200,  # ms for GPT-4o-mini
        "p95": 1800,
        "p99": 2500
    },
    "insight_delivery": {
        "average": 50,   # ms from analysis to UI
        "p95": 100,
        "p99": 200
    },
    "total_pipeline": {
        "average": 1400,  # ms total
        "p95": 2150,
        "p99": 3100
    }
}

# Optimization Strategies
class PerformanceOptimizer:
    def __init__(self):
        self.cache = LRUCache(maxsize=1000)
        self.prediction_model = None
        
    async def optimize_analysis(self, transcript: str) -> Dict:
        """Optimize AI analysis for speed"""
        
        # 1. Check cache for similar questions
        cache_key = self._generate_cache_key(transcript)
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        # 2. Use predictive pre-fetching
        predicted_questions = await self._predict_next_questions(transcript)
        
        # 3. Batch API calls when possible
        if len(self.pending_analyses) >= 3:
            return await self._batch_analyze()
        
        # 4. Use streaming for long responses
        return await self._stream_analysis(transcript)
```

### Latency Reduction Techniques

```python
class LatencyReducer:
    """Techniques to minimize perceived latency"""
    
    def __init__(self):
        self.local_analyzer = LocalAnalyzer()  # Fallback
        self.insight_predictor = InsightPredictor()
        
    async def provide_instant_feedback(self, transcript: str) -> List[Dict]:
        """Provide immediate insights while waiting for AI"""
        
        instant_insights = []
        
        # 1. Local pattern matching
        patterns = self.local_analyzer.find_patterns(transcript)
        for pattern in patterns:
            instant_insights.append({
                'type': 'tip',
                'title': pattern['title'],
                'content': pattern['suggestion'],
                'is_preliminary': True
            })
        
        # 2. Historical insights
        similar_context = await self.find_similar_context(transcript)
        if similar_context:
            instant_insights.extend(similar_context['insights'])
        
        # 3. Predictive insights
        predicted = self.insight_predictor.predict(transcript)
        instant_insights.extend(predicted)
        
        return instant_insights
```

## Security & Privacy

### Data Protection

```python
class SecurityManager:
    """Handles security and privacy for interview data"""
    
    def __init__(self):
        self.encryption = AESEncryption()
        self.anonymizer = DataAnonymizer()
        
    async def secure_transcript(self, transcript: str, session_id: str) -> str:
        """Secure transcript data"""
        
        # 1. Anonymize PII
        anonymized = self.anonymizer.remove_pii(transcript)
        
        # 2. Encrypt for storage
        encrypted = self.encryption.encrypt(anonymized, session_id)
        
        # 3. Set expiration
        await self.set_expiration(session_id, hours=24)
        
        return encrypted
    
    def remove_pii(self, text: str) -> str:
        """Remove personally identifiable information"""
        
        # Email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                     '[EMAIL]', text)
        
        # Phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        
        # SSN
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
        
        # Names (using NER)
        entities = self.ner_model.extract_entities(text)
        for entity in entities:
            if entity['type'] == 'PERSON':
                text = text.replace(entity['text'], '[NAME]')
        
        return text
```

### Access Control

```python
class AccessController:
    """Manage access to interview sessions"""
    
    async def verify_access(self, user_id: str, session_id: str) -> bool:
        """Verify user has access to session"""
        
        session = await self.get_session(session_id)
        
        # Check ownership
        if session['interviewer_id'] == user_id:
            return True
        
        # Check shared access
        if user_id in session.get('shared_with', []):
            return True
        
        # Check organization access
        if await self.check_org_access(user_id, session['org_id']):
            return True
        
        return False
```

## Future Enhancements

### 1. Multi-Language Support

```python
class MultiLanguageSupport:
    """Support for non-English interviews"""
    
    async def process_multilingual(self, audio_stream, language: str):
        # Transcribe in native language
        transcript = await self.transcribe(audio_stream, language)
        
        # Translate for analysis
        translated = await self.translate(transcript, target='en')
        
        # Analyze in English
        analysis = await self.analyze(translated)
        
        # Translate insights back
        localized_insights = await self.translate_insights(
            analysis, target=language
        )
        
        return localized_insights
```

### 2. Advanced Analytics

```python
class AdvancedAnalytics:
    """Deep interview analytics"""
    
    def analyze_interview_quality(self, session_data: Dict) -> Dict:
        return {
            'question_quality': self._rate_questions(session_data),
            'conversation_flow': self._analyze_flow(session_data),
            'candidate_engagement': self._measure_engagement(session_data),
            'missed_opportunities': self._find_missed_topics(session_data),
            'interview_effectiveness': self._calculate_effectiveness(session_data)
        }
```

### 3. Integration with ATS

```python
class ATSIntegration:
    """Integrate with Applicant Tracking Systems"""
    
    async def sync_to_ats(self, session_id: str, ats_config: Dict):
        # Get interview summary
        summary = await self.generate_summary(session_id)
        
        # Map to ATS format
        ats_data = self.map_to_ats_format(summary, ats_config['format'])
        
        # Push to ATS
        await self.push_to_ats(ats_data, ats_config['api_endpoint'])
```

This AI Interview Copilot provides real-time assistance that enhances interview quality, ensures comprehensive evaluation, and helps interviewers make better hiring decisions.