'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  Zap,
  AlertCircle,
  MessageSquare,
  CheckCircle,
  XCircle,
  TrendingUp,
  TrendingDown,
  Sparkles,
  Eye,
  Lightbulb,
  Activity,
  User,
  Volume2,
  Gauge,
  ThumbsUp,
  Info,
  RefreshCw
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area-simple';
import { Progress } from '@/components/ui/progress-simple';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs-simple';

interface CopilotInsight {
  id: string;
  type: 'question' | 'fact_check' | 'sentiment' | 'tip' | 'warning' | 'highlight';
  icon: React.ElementType;
  color: string;
  title: string;
  content: string;
  timestamp: Date;
  priority: 'high' | 'medium' | 'low';
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface FactCheckItem {
  claim: string;
  verified: boolean | null;
  explanation: string;
  confidence: number;
}

interface SentimentData {
  overall: 'positive' | 'neutral' | 'negative' | 'stressed';
  confidence: number;
  indicators: string[];
  trend: 'improving' | 'stable' | 'declining';
}

interface AIInterviewCopilotProps {
  transcript: string;
  currentQuestion: any;
  candidateInfo: any;
  isRecording: boolean;
  onUseQuestion: (question: string) => void;
  onInsightAction?: (insight: CopilotInsight) => void;
}

export default function AIInterviewCopilot({
  transcript,
  currentQuestion,
  candidateInfo,
  isRecording,
  onUseQuestion,
  onInsightAction
}: AIInterviewCopilotProps) {
  const [insights, setInsights] = useState<CopilotInsight[]>([]);
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
  const [factChecks, setFactChecks] = useState<FactCheckItem[]>([]);
  const [sentiment, setSentiment] = useState<SentimentData>({
    overall: 'neutral',
    confidence: 0,
    indicators: [],
    trend: 'stable'
  });
  const [keyMoments, setKeyMoments] = useState<string[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [activeTab, setActiveTab] = useState('insights');
  
  const lastAnalyzedRef = useRef('');
  const analysisTimeoutRef = useRef<NodeJS.Timeout>();

  // Analyze transcript when it changes
  useEffect(() => {
    if (!transcript || transcript === lastAnalyzedRef.current || !isRecording) return;
    
    // Debounce analysis
    clearTimeout(analysisTimeoutRef.current);
    analysisTimeoutRef.current = setTimeout(() => {
      analyzeTranscript(transcript);
      lastAnalyzedRef.current = transcript;
    }, 2000); // Wait 2 seconds of silence before analyzing
    
    return () => clearTimeout(analysisTimeoutRef.current);
  }, [transcript, isRecording]);

  const analyzeTranscript = async (text: string) => {
    setIsAnalyzing(true);
    
    try {
      // Simulate AI analysis - in production, this would call your backend
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/interviews/copilot/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          transcript: text,
          currentQuestion: currentQuestion?.question_text,
          candidateInfo,
          context: {
            expectedPoints: currentQuestion?.expected_answer_points || [],
            category: currentQuestion?.category
          }
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        
        // Update suggested questions
        if (data.suggestedQuestions) {
          setSuggestedQuestions(data.suggestedQuestions);
        }
        
        // Update fact checks
        if (data.factChecks) {
          setFactChecks(data.factChecks);
        }
        
        // Update sentiment
        if (data.sentiment) {
          setSentiment(data.sentiment);
        }
        
        // Add new insights
        if (data.insights) {
          const newInsights = data.insights.map((insight: any) => ({
            ...insight,
            id: `insight-${Date.now()}-${Math.random()}`,
            timestamp: new Date(),
            icon: getIconForType(insight.type),
            color: getColorForType(insight.type)
          }));
          setInsights(prev => [...newInsights, ...prev].slice(0, 10)); // Keep last 10
        }
        
        // Update key moments
        if (data.keyMoments) {
          setKeyMoments(data.keyMoments);
        }
      }
    } catch (error) {
      console.error('Copilot analysis error:', error);
      // Fallback to local analysis
      performLocalAnalysis(text);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const performLocalAnalysis = (text: string) => {
    // Local analysis as fallback
    const recentText = text.slice(-500); // Last 500 chars
    const words = recentText.toLowerCase().split(/\s+/);
    
    // Simple sentiment detection
    const positiveWords = ['excellent', 'great', 'love', 'passionate', 'excited', 'achieved'];
    const negativeWords = ['difficult', 'challenge', 'struggle', 'hard', 'problem', 'issue'];
    const stressWords = ['um', 'uh', 'well', 'actually', 'like', 'you know'];
    
    const positiveCount = words.filter(w => positiveWords.includes(w)).length;
    const negativeCount = words.filter(w => negativeWords.includes(w)).length;
    const stressCount = words.filter(w => stressWords.includes(w)).length;
    
    // Update sentiment
    let overallSentiment: SentimentData['overall'] = 'neutral';
    if (stressCount > 5) overallSentiment = 'stressed';
    else if (positiveCount > negativeCount + 2) overallSentiment = 'positive';
    else if (negativeCount > positiveCount + 2) overallSentiment = 'negative';
    
    setSentiment({
      overall: overallSentiment,
      confidence: 0.7,
      indicators: stressCount > 5 ? ['High filler word usage', 'Possible nervousness'] : [],
      trend: 'stable'
    });
    
    // Generate insights based on patterns
    const newInsights: CopilotInsight[] = [];
    
    // Check for incomplete answers
    if (recentText.length < 100 && currentQuestion) {
      newInsights.push({
        id: `insight-${Date.now()}-1`,
        type: 'tip',
        icon: Lightbulb,
        color: 'text-blue-600',
        title: 'Short Response Detected',
        content: 'Consider asking a follow-up question to get more detail.',
        timestamp: new Date(),
        priority: 'medium'
      });
    }
    
    // Check for technical terms that might need verification
    const techTerms = ['built', 'implemented', 'designed', 'architected', 'led', 'managed'];
    const mentionedTech = words.filter(w => techTerms.includes(w)).length;
    if (mentionedTech > 0) {
      newInsights.push({
        id: `insight-${Date.now()}-2`,
        type: 'fact_check',
        icon: CheckCircle,
        color: 'text-green-600',
        title: 'Technical Claims Made',
        content: 'Candidate mentioned technical achievements. Consider probing for specifics.',
        timestamp: new Date(),
        priority: 'high'
      });
    }
    
    // Add suggested follow-ups based on category
    if (currentQuestion?.category === 'technical') {
      setSuggestedQuestions([
        'Can you walk me through the technical architecture?',
        'What specific technologies did you use?',
        'How did you handle scalability?'
      ]);
    } else if (currentQuestion?.category === 'behavioral') {
      setSuggestedQuestions([
        'What was the outcome of that situation?',
        'How did your team respond?',
        'What would you do differently?'
      ]);
    }
    
    if (newInsights.length > 0) {
      setInsights(prev => [...newInsights, ...prev].slice(0, 10));
    }
  };

  const getIconForType = (type: string): React.ElementType => {
    switch (type) {
      case 'question': return MessageSquare;
      case 'fact_check': return CheckCircle;
      case 'sentiment': return Activity;
      case 'tip': return Lightbulb;
      case 'warning': return AlertCircle;
      case 'highlight': return Eye;
      default: return Info;
    }
  };

  const getColorForType = (type: string): string => {
    switch (type) {
      case 'question': return 'text-blue-600';
      case 'fact_check': return 'text-green-600';
      case 'sentiment': return 'text-purple-600';
      case 'tip': return 'text-amber-600';
      case 'warning': return 'text-red-600';
      case 'highlight': return 'text-indigo-600';
      default: return 'text-gray-600';
    }
  };

  const getSentimentIcon = () => {
    switch (sentiment.overall) {
      case 'positive': return ThumbsUp;
      case 'negative': return TrendingDown;
      case 'stressed': return AlertCircle;
      default: return Activity;
    }
  };

  const getSentimentColor = () => {
    switch (sentiment.overall) {
      case 'positive': return 'text-green-600';
      case 'negative': return 'text-red-600';
      case 'stressed': return 'text-amber-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="h-full flex flex-col">
      <Card className="flex-1 overflow-hidden">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-primary" />
              AI Copilot
              {isRecording && (
                <Badge variant="outline" className="text-xs animate-pulse">
                  <Volume2 className="h-3 w-3 mr-1" />
                  Live
                </Badge>
              )}
            </div>
            {isAnalyzing && (
              <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex-1 overflow-hidden">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="insights" className="text-xs">Insights</TabsTrigger>
              <TabsTrigger value="questions" className="text-xs">Questions</TabsTrigger>
              <TabsTrigger value="facts" className="text-xs">Fact Check</TabsTrigger>
              <TabsTrigger value="sentiment" className="text-xs">Sentiment</TabsTrigger>
            </TabsList>
            
            <div className="flex-1 overflow-hidden mt-4">
              <TabsContent value="insights" className="h-full">
                <ScrollArea className="h-full">
                  <div className="space-y-3">
                    {insights.length === 0 ? (
                      <div className="text-center py-8 text-muted-foreground">
                        <Brain className="h-12 w-12 mx-auto mb-2 opacity-20" />
                        <p className="text-sm">Start recording to see real-time insights</p>
                      </div>
                    ) : (
                      <AnimatePresence>
                        {insights.map((insight) => (
                          <motion.div
                            key={insight.id}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                            className={`p-3 rounded-lg border ${
                              insight.priority === 'high' ? 'border-primary bg-primary/5' :
                              insight.priority === 'medium' ? 'border-amber-200 bg-amber-50' :
                              'border-gray-200 bg-gray-50'
                            }`}
                          >
                            <div className="flex items-start gap-3">
                              <insight.icon className={`h-5 w-5 ${insight.color} mt-0.5`} />
                              <div className="flex-1">
                                <h4 className="font-medium text-sm">{insight.title}</h4>
                                <p className="text-xs text-muted-foreground mt-1">
                                  {insight.content}
                                </p>
                                {insight.action && (
                                  <Button
                                    size="sm"
                                    variant="link"
                                    className="h-auto p-0 mt-2 text-xs"
                                    onClick={insight.action.onClick}
                                  >
                                    {insight.action.label} →
                                  </Button>
                                )}
                              </div>
                            </div>
                          </motion.div>
                        ))}
                      </AnimatePresence>
                    )}
                  </div>
                </ScrollArea>
              </TabsContent>
              
              <TabsContent value="questions" className="h-full">
                <ScrollArea className="h-full">
                  <div className="space-y-3">
                    <Alert className="mb-3">
                      <Sparkles className="h-4 w-4" />
                      <AlertDescription className="text-xs">
                        AI-suggested follow-up questions based on the conversation
                      </AlertDescription>
                    </Alert>
                    
                    {suggestedQuestions.length === 0 ? (
                      <div className="text-center py-8 text-muted-foreground">
                        <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-20" />
                        <p className="text-sm">Questions will appear as the interview progresses</p>
                      </div>
                    ) : (
                      suggestedQuestions.map((question, idx) => (
                        <Card key={idx} className="p-3 hover:shadow-sm transition-shadow cursor-pointer"
                              onClick={() => onUseQuestion(question)}>
                          <div className="flex items-start gap-3">
                            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                              <span className="text-xs font-medium text-primary">{idx + 1}</span>
                            </div>
                            <div className="flex-1">
                              <p className="text-sm">{question}</p>
                              <p className="text-xs text-muted-foreground mt-1">
                                Click to use this question
                              </p>
                            </div>
                          </div>
                        </Card>
                      ))
                    )}
                  </div>
                </ScrollArea>
              </TabsContent>
              
              <TabsContent value="facts" className="h-full">
                <ScrollArea className="h-full">
                  <div className="space-y-3">
                    {factChecks.length === 0 ? (
                      <div className="text-center py-8 text-muted-foreground">
                        <CheckCircle className="h-12 w-12 mx-auto mb-2 opacity-20" />
                        <p className="text-sm">Technical claims will be verified here</p>
                      </div>
                    ) : (
                      factChecks.map((fact, idx) => (
                        <Card key={idx} className="p-3">
                          <div className="flex items-start gap-3">
                            {fact.verified === true ? (
                              <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                            ) : fact.verified === false ? (
                              <XCircle className="h-5 w-5 text-red-600 mt-0.5" />
                            ) : (
                              <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5" />
                            )}
                            <div className="flex-1">
                              <p className="text-sm font-medium">{fact.claim}</p>
                              <p className="text-xs text-muted-foreground mt-1">
                                {fact.explanation}
                              </p>
                              <div className="flex items-center gap-2 mt-2">
                                <Gauge className="h-3 w-3 text-muted-foreground" />
                                <span className="text-xs text-muted-foreground">
                                  Confidence: {Math.round(fact.confidence * 100)}%
                                </span>
                              </div>
                            </div>
                          </div>
                        </Card>
                      ))
                    )}
                  </div>
                </ScrollArea>
              </TabsContent>
              
              <TabsContent value="sentiment" className="h-full">
                <div className="space-y-4">
                  {/* Overall Sentiment */}
                  <Card className="p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-sm font-medium">Overall Sentiment</h4>
                      {sentiment.trend === 'improving' && (
                        <TrendingUp className="h-4 w-4 text-green-600" />
                      )}
                      {sentiment.trend === 'declining' && (
                        <TrendingDown className="h-4 w-4 text-red-600" />
                      )}
                    </div>
                    <div className="flex items-center gap-3">
                      {React.createElement(getSentimentIcon(), {
                        className: `h-8 w-8 ${getSentimentColor()}`
                      })}
                      <div>
                        <p className="font-medium capitalize">{sentiment.overall}</p>
                        <p className="text-xs text-muted-foreground">
                          {sentiment.confidence > 0 ? `${Math.round(sentiment.confidence * 100)}% confidence` : 'Analyzing...'}
                        </p>
                      </div>
                    </div>
                  </Card>
                  
                  {/* Indicators */}
                  {sentiment.indicators.length > 0 && (
                    <Card className="p-4">
                      <h4 className="text-sm font-medium mb-3">Behavioral Indicators</h4>
                      <div className="space-y-2">
                        {sentiment.indicators.map((indicator, idx) => (
                          <div key={idx} className="flex items-center gap-2">
                            <Activity className="h-4 w-4 text-muted-foreground" />
                            <span className="text-xs">{indicator}</span>
                          </div>
                        ))}
                      </div>
                    </Card>
                  )}
                  
                  {/* Key Moments */}
                  {keyMoments.length > 0 && (
                    <Card className="p-4">
                      <h4 className="text-sm font-medium mb-3">Key Moments</h4>
                      <div className="space-y-2">
                        {keyMoments.map((moment, idx) => (
                          <div key={idx} className="flex items-start gap-2">
                            <Eye className="h-4 w-4 text-primary mt-0.5" />
                            <p className="text-xs">{moment}</p>
                          </div>
                        ))}
                      </div>
                    </Card>
                  )}
                  
                  {/* Tips */}
                  <Alert>
                    <Lightbulb className="h-4 w-4" />
                    <AlertDescription className="text-xs">
                      {sentiment.overall === 'stressed' 
                        ? 'Consider a lighter question to help the candidate relax'
                        : sentiment.overall === 'negative'
                        ? 'Try highlighting something positive from their experience'
                        : 'Candidate seems engaged - good time for deeper questions'}
                    </AlertDescription>
                  </Alert>
                </div>
              </TabsContent>
            </div>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}