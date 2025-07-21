'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth/context';
import { 
  Search, Zap, Brain, Shield, Users, BarChart, 
  Mic, FileText, Sparkles, Target, Upload, Tags, 
  Headphones, FileCheck, TrendingUp, MessageSquare,
  Calendar, Bot, Check, Mail, Chrome, LineChart
} from 'lucide-react';

export default function HomePage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [showSearchPrompt, setShowSearchPrompt] = useState(false);

  useEffect(() => {
    if (!isLoading && user) {
      router.push('/dashboard');
    }
  }, [user, isLoading, router]);

  const handleSearchClick = () => {
    setShowSearchPrompt(true);
    setTimeout(() => {
      router.push('/register');
    }, 1500);
  };

  const features = [
    // Search & Discovery
    {
      icon: Search,
      title: 'Natural Language Search',
      description: 'Find candidates by describing what you need in plain English',
      category: 'search',
    },
    {
      icon: Tags,
      title: 'Smart Filters & Tags',
      description: 'Advanced filtering with tag clouds and skill matching',
      category: 'search',
    },
    {
      icon: Upload,
      title: 'Bulk Resume Upload',
      description: 'Process hundreds of resumes at once with AI parsing',
      category: 'search',
    },
    // AI Interview Suite
    {
      icon: Bot,
      title: 'AI Interview Copilot',
      description: 'Conduct smarter interviews with real-time AI assistance',
      category: 'interview',
      isNew: true,
    },
    {
      icon: Mic,
      title: 'Live Transcription',
      description: 'Real-time transcription powered by OpenAI Whisper',
      category: 'interview',
      isNew: true,
    },
    {
      icon: Sparkles,
      title: 'Live Coaching',
      description: 'Get real-time suggestions and follow-up questions',
      category: 'interview',
      isNew: true,
    },
    {
      icon: FileCheck,
      title: 'Smart Scorecards',
      description: 'AI-generated scorecards that adapt to your interviews',
      category: 'interview',
      isNew: true,
    },
    // Intelligence & Analytics
    {
      icon: Brain,
      title: 'Interview Intelligence',
      description: 'Comprehensive analytics and insights dashboard',
      category: 'analytics',
    },
    {
      icon: TrendingUp,
      title: 'Sentiment Analysis',
      description: 'Track candidate engagement and emotional cues',
      category: 'analytics',
      isNew: true,
    },
    {
      icon: FileText,
      title: 'Interview Templates',
      description: 'Pre-built templates for different roles and levels',
      category: 'analytics',
    },
    // Outreach & Communication
    {
      icon: Mail,
      title: 'AI Outreach Messages',
      description: 'Generate personalized outreach with GPT-4 in multiple tones',
      category: 'outreach',
      isNew: true,
    },
    {
      icon: Chrome,
      title: 'LinkedIn Chrome Extension',
      description: 'Import profiles instantly with one-click browser extension',
      category: 'outreach',
      isNew: true,
    },
    // Platform & Security
    {
      icon: Shield,
      title: 'Enterprise Security',
      description: 'Privacy-focused, secure data handling, end-to-end encryption',
      category: 'platform',
    },
    {
      icon: Users,
      title: 'Team Collaboration',
      description: 'Share candidates, interviews, and insights with your team',
      category: 'platform',
    },
    {
      icon: LineChart,
      title: 'Usage Analytics',
      description: 'Track platform usage, popular searches, and performance',
      category: 'platform',
      isNew: true,
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <header className="border-b bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <Link href="/" className="flex items-center">
            <img 
              src="/logo-horizontal.svg" 
              alt="Promtitude" 
              className="h-10 w-auto"
            />
          </Link>
          <nav className="flex gap-4 items-center">
            <a 
              href="https://chrome.google.com/webstore" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-sm text-gray-600 dark:text-gray-400 hover:text-primary flex items-center gap-1"
            >
              <Chrome className="h-4 w-4" />
              <span className="hidden sm:inline">Chrome Extension</span>
            </a>
            <Link
              href="/login"
              className="btn-secondary"
            >
              Login
            </Link>
            <Link
              href="/register"
              className="btn-primary"
            >
              Get Started
            </Link>
          </nav>
        </div>
      </header>

      <main>
        {/* Hero Section */}
        <section className="container mx-auto px-4 py-24 text-center">
          <div className="animate-fade-in">
            <h1 className="mb-6 text-5xl md:text-6xl font-bold tracking-tight text-gray-900 dark:text-white">
              Where{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">
                AI Meets Aptitude
              </span>
            </h1>
            <p className="mx-auto mb-8 max-w-3xl text-xl text-gray-600 dark:text-gray-400">
              The complete AI-powered recruitment platform. Search candidates with natural language, 
              conduct interviews with AI assistance, craft personalized outreach messages, and make data-driven hiring decisions.
            </p>
            
            {/* Demo Search Bar */}
            <div className="mx-auto max-w-2xl mb-8">
              <div className="relative group">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5 z-10 pointer-events-none" />
                <input
                  type="text"
                  placeholder="Try: Product manager with B2B SaaS experience and strong analytics skills..."
                  className="w-full pl-12 pr-4 py-4 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm group-hover:shadow-md transition-all cursor-pointer hover:border-blue-500 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  onClick={handleSearchClick}
                  onFocus={handleSearchClick}
                  readOnly
                />
                {showSearchPrompt && (
                  <div className="absolute top-full left-0 right-0 mt-2 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg shadow-lg animate-fade-in">
                    <p className="text-sm text-blue-700 dark:text-blue-300 font-medium">
                      🚀 Sign up to unlock powerful AI search capabilities!
                    </p>
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-center gap-4 flex-wrap">
              <Link
                href="/register"
                className="btn-primary px-8 py-3 text-lg"
              >
                Start Free Trial
              </Link>
              <Link
                href="#interview-copilot"
                className="btn-secondary px-8 py-3 text-lg flex items-center gap-2"
              >
                <MessageSquare className="h-5 w-5" />
                See AI Copilot in Action
              </Link>
              <Link
                href="#features"
                className="btn-secondary px-8 py-3 text-lg"
              >
                Learn More
              </Link>
            </div>
          </div>
        </section>

        {/* How It Works */}
        <section className="py-24 bg-gray-50 dark:bg-gray-800/50">
          <div className="container mx-auto px-4">
            <h2 className="mb-12 text-center text-3xl font-bold text-gray-900 dark:text-white">
              How It Works
            </h2>
            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
              <div className="text-center animate-fade-in" style={{ animationDelay: '0.1s' }}>
                <div className="mb-4 inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-100 dark:bg-blue-900/30">
                  <Upload className="h-8 w-8 text-blue-600 dark:text-blue-400" />
                </div>
                <h3 className="mb-2 text-xl font-semibold text-gray-900 dark:text-white">
                  Upload & Organize
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Bulk upload resumes. AI automatically parses and organizes candidate data.
                </p>
              </div>
              <div className="text-center animate-fade-in" style={{ animationDelay: '0.2s' }}>
                <div className="mb-4 inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30">
                  <Search className="h-8 w-8 text-green-600 dark:text-green-400" />
                </div>
                <h3 className="mb-2 text-xl font-semibold text-gray-900 dark:text-white">
                  Search with AI
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Use natural language to find perfect matches with advanced filters.
                </p>
              </div>
              <div className="text-center animate-fade-in" style={{ animationDelay: '0.3s' }}>
                <div className="mb-4 inline-flex items-center justify-center w-16 h-16 rounded-full bg-purple-100 dark:bg-purple-900/30">
                  <Bot className="h-8 w-8 text-purple-600 dark:text-purple-400" />
                </div>
                <h3 className="mb-2 text-xl font-semibold text-gray-900 dark:text-white">
                  Interview Smarter
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  AI Copilot assists with live transcription and smart suggestions.
                </p>
              </div>
              <div className="text-center animate-fade-in" style={{ animationDelay: '0.4s' }}>
                <div className="mb-4 inline-flex items-center justify-center w-16 h-16 rounded-full bg-orange-100 dark:bg-orange-900/30">
                  <FileCheck className="h-8 w-8 text-orange-600 dark:text-orange-400" />
                </div>
                <h3 className="mb-2 text-xl font-semibold text-gray-900 dark:text-white">
                  Hire with Confidence
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  AI-generated scorecards and analytics help you make better decisions.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="py-16 border-y border-gray-200 dark:border-gray-700">
          <div className="container mx-auto px-4">
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-8 text-center">
              <div className="animate-fade-in" style={{ animationDelay: '0.1s' }}>
                <div className="text-4xl font-bold text-primary mb-2">1000+</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Resumes Processed</div>
              </div>
              <div className="animate-fade-in" style={{ animationDelay: '0.2s' }}>
                <div className="text-4xl font-bold text-primary mb-2">200+</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Interviews Conducted</div>
              </div>
              <div className="animate-fade-in" style={{ animationDelay: '0.3s' }}>
                <div className="text-4xl font-bold text-primary mb-2">&lt;300ms</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Search Response</div>
              </div>
              <div className="animate-fade-in" style={{ animationDelay: '0.4s' }}>
                <div className="text-4xl font-bold text-primary mb-2">95%</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Match Accuracy</div>
              </div>
              <div className="animate-fade-in" style={{ animationDelay: '0.5s' }}>
                <div className="text-4xl font-bold text-primary mb-2">500+</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Outreach Messages</div>
              </div>
              <div className="animate-fade-in" style={{ animationDelay: '0.6s' }}>
                <div className="text-4xl font-bold text-primary mb-2">3x</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Response Rate</div>
              </div>
            </div>
          </div>
        </section>

        {/* Features */}
        <section id="features" className="py-24">
          <div className="container mx-auto px-4">
            <h2 className="mb-4 text-center text-3xl font-bold text-gray-900 dark:text-white">
              Everything You Need to Hire Better
            </h2>
            <p className="mb-12 text-center text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
              From finding candidates to making hiring decisions, Promptitude has you covered with AI-powered features.
            </p>
            
            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {features.map((feature, index) => {
                const getCategoryColor = (category: string) => {
                  switch(category) {
                    case 'search': return 'from-blue-500/10 to-blue-600/10 border-blue-500/20';
                    case 'interview': return 'from-purple-500/10 to-purple-600/10 border-purple-500/20';
                    case 'analytics': return 'from-green-500/10 to-green-600/10 border-green-500/20';
                    case 'outreach': return 'from-orange-500/10 to-orange-600/10 border-orange-500/20';
                    case 'platform': return 'from-gray-500/10 to-gray-600/10 border-gray-500/20';
                    default: return 'from-gray-500/10 to-gray-600/10 border-gray-500/20';
                  }
                };

                const getIconColor = (category: string) => {
                  switch(category) {
                    case 'search': return 'text-blue-600 dark:text-blue-400';
                    case 'interview': return 'text-purple-600 dark:text-purple-400';
                    case 'analytics': return 'text-green-600 dark:text-green-400';
                    case 'outreach': return 'text-orange-600 dark:text-orange-400';
                    case 'platform': return 'text-gray-600 dark:text-gray-400';
                    default: return 'text-gray-600 dark:text-gray-400';
                  }
                };

                return (
                  <div
                    key={feature.title}
                    className={`relative card p-6 hover:shadow-xl transition-all duration-300 hover:-translate-y-1 animate-fade-in bg-gradient-to-br ${getCategoryColor(feature.category)} border`}
                    style={{ animationDelay: `${index * 0.05}s` }}
                  >
                    {feature.isNew && (
                      <span className="absolute -top-2 -right-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white text-xs font-bold px-2 py-1 rounded-full">
                        NEW
                      </span>
                    )}
                    <feature.icon className={`h-10 w-10 mb-4 ${getIconColor(feature.category)}`} />
                    <h3 className="mb-2 text-lg font-semibold text-gray-900 dark:text-white">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {feature.description}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* AI Interview Copilot Showcase */}
        <section id="interview-copilot" className="py-24 bg-gradient-to-r from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20">
          <div className="container mx-auto px-4">
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div className="animate-fade-in">
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800 dark:bg-purple-800/30 dark:text-purple-300 mb-4">
                  <Sparkles className="h-4 w-4 mr-1" />
                  Game-Changing Feature
                </span>
                <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-6">
                  AI Interview Copilot
                </h2>
                <p className="text-xl text-gray-600 dark:text-gray-400 mb-8">
                  Transform your interviews with real-time AI assistance. Never miss important questions, 
                  get instant insights, and make better hiring decisions.
                </p>
                
                <div className="space-y-4 mb-8">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-500 flex items-center justify-center">
                      <Check className="h-4 w-4 text-white" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">Live Transcription</h4>
                      <p className="text-gray-600 dark:text-gray-400">Real-time transcription with speaker identification and timestamps</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-500 flex items-center justify-center">
                      <Check className="h-4 w-4 text-white" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">Smart Suggestions</h4>
                      <p className="text-gray-600 dark:text-gray-400">AI-powered follow-up questions and red flag alerts</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-500 flex items-center justify-center">
                      <Check className="h-4 w-4 text-white" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">Instant Scorecards</h4>
                      <p className="text-gray-600 dark:text-gray-400">Auto-generated scorecards based on actual interview content</p>
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-6 mb-8">
                  <div>
                    <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">70%</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Time Saved</div>
                  </div>
                  <div>
                    <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">$0.27</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Per Interview</div>
                  </div>
                  <div>
                    <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">95%</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Accuracy</div>
                  </div>
                </div>

                <Link href="/register" className="btn-primary inline-flex items-center gap-2 px-6 py-3">
                  <Bot className="h-5 w-5" />
                  Try AI Copilot Free
                </Link>
              </div>
              
              <div className="relative animate-fade-in" style={{ animationDelay: '0.2s' }}>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl p-6">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="flex-shrink-0">
                      <div className="w-12 h-12 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-full flex items-center justify-center">
                        <Bot className="h-6 w-6 text-white" />
                      </div>
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white">Interview Assistant</h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">AI-powered live assistance</p>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-1">
                        <Mic className="h-4 w-4 text-red-500" />
                        <span className="text-xs font-medium text-gray-600 dark:text-gray-400">Recording</span>
                      </div>
                      <p className="text-sm text-gray-700 dark:text-gray-300">"Tell me about your experience with React and TypeScript..."</p>
                    </div>
                    
                    <div className="bg-purple-50 dark:bg-purple-900/30 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-1">
                        <Sparkles className="h-4 w-4 text-purple-500" />
                        <span className="text-xs font-medium text-purple-600 dark:text-purple-400">AI Suggestion</span>
                      </div>
                      <p className="text-sm text-purple-700 dark:text-purple-300">Ask about their experience with state management libraries</p>
                    </div>
                    
                    <div className="bg-green-50 dark:bg-green-900/30 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-1">
                        <TrendingUp className="h-4 w-4 text-green-500" />
                        <span className="text-xs font-medium text-green-600 dark:text-green-400">Sentiment</span>
                      </div>
                      <p className="text-sm text-green-700 dark:text-green-300">Candidate showing high engagement and enthusiasm</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* AI Outreach & Engagement Showcase */}
        <section className="py-24 bg-gradient-to-r from-orange-50 to-amber-50 dark:from-orange-900/20 dark:to-amber-900/20">
          <div className="container mx-auto px-4">
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div className="order-2 lg:order-1 relative animate-fade-in" style={{ animationDelay: '0.2s' }}>
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl p-6">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="flex-shrink-0">
                      <div className="w-12 h-12 bg-gradient-to-r from-orange-600 to-amber-600 rounded-full flex items-center justify-center">
                        <Mail className="h-6 w-6 text-white" />
                      </div>
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white">AI Outreach Generator</h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Personalized messages in seconds</p>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs font-medium text-gray-600 dark:text-gray-400">Candidate Profile</span>
                      </div>
                      <p className="text-sm text-gray-700 dark:text-gray-300 font-medium">Sarah Chen - Senior Frontend Engineer</p>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">React, TypeScript, 8 years experience</p>
                    </div>
                    
                    <div className="bg-orange-50 dark:bg-orange-900/30 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <Sparkles className="h-4 w-4 text-orange-500" />
                        <span className="text-xs font-medium text-orange-600 dark:text-orange-400">AI Generated - Professional Tone</span>
                      </div>
                      <p className="text-sm text-gray-700 dark:text-gray-300">
                        "Hi Sarah, I came across your impressive background in React and TypeScript. 
                        We're looking for a Senior Frontend Engineer to lead our UI architecture initiative. 
                        Your experience with design systems particularly caught my attention..."
                      </p>
                    </div>
                    
                    <div className="flex gap-2">
                      <button className="text-xs px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
                        Casual
                      </button>
                      <button className="text-xs px-3 py-1 rounded-full bg-orange-100 dark:bg-orange-900/50 text-orange-600 dark:text-orange-400 font-medium">
                        Professional
                      </button>
                      <button className="text-xs px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
                        Technical
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="order-1 lg:order-2 animate-fade-in">
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-orange-100 text-orange-800 dark:bg-orange-800/30 dark:text-orange-300 mb-4">
                  <Mail className="h-4 w-4 mr-1" />
                  Boost Response Rates
                </span>
                <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-6">
                  AI-Powered Outreach Messages
                </h2>
                <p className="text-xl text-gray-600 dark:text-gray-400 mb-8">
                  Stop spending hours crafting personalized messages. Our AI generates compelling, 
                  contextual outreach in seconds, with multiple tone options to match your style.
                </p>
                
                <div className="space-y-4 mb-8">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-500 flex items-center justify-center">
                      <Check className="h-4 w-4 text-white" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">Personalized at Scale</h4>
                      <p className="text-gray-600 dark:text-gray-400">Generate unique messages based on each candidate's profile</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-500 flex items-center justify-center">
                      <Check className="h-4 w-4 text-white" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">Multiple Tones</h4>
                      <p className="text-gray-600 dark:text-gray-400">Choose between casual, professional, or technical messaging styles</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-500 flex items-center justify-center">
                      <Check className="h-4 w-4 text-white" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">Chrome Extension</h4>
                      <p className="text-gray-600 dark:text-gray-400">Import LinkedIn profiles instantly with our browser extension</p>
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-6 mb-8">
                  <div>
                    <div className="text-3xl font-bold text-orange-600 dark:text-orange-400">3x</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Higher Response Rate</div>
                  </div>
                  <div>
                    <div className="text-3xl font-bold text-orange-600 dark:text-orange-400">10s</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Per Message</div>
                  </div>
                  <div>
                    <div className="text-3xl font-bold text-orange-600 dark:text-orange-400">GPT-4</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Powered</div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-4">
                  <Link href="/register" className="btn-primary inline-flex items-center gap-2 px-6 py-3">
                    <Mail className="h-5 w-5" />
                    Try AI Outreach Free
                  </Link>
                  <a 
                    href="https://chrome.google.com/webstore" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="btn-secondary inline-flex items-center gap-2 px-6 py-3"
                  >
                    <Chrome className="h-5 w-5" />
                    Get Chrome Extension
                  </a>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-24 bg-primary text-white">
          <div className="container mx-auto px-4 text-center">
            <h2 className="mb-6 text-3xl font-bold">
              Ready to Transform Your Hiring Process?
            </h2>
            <p className="mx-auto mb-8 max-w-2xl text-xl opacity-90">
              Join thousands of recruiters who are finding better candidates faster with Promtitude.
            </p>
            <Link
              href="/register"
              className="inline-flex items-center px-8 py-3 bg-white text-primary hover:bg-gray-100 rounded-md font-medium transition-colors"
            >
              Start Your Free Trial
            </Link>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t py-8 bg-white dark:bg-gray-900">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="mb-4 md:mb-0">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                © 2025 Promtitude. All rights reserved.
              </p>
            </div>
            <nav className="flex gap-6">
              <Link
                href="/privacy"
                className="text-sm text-gray-600 dark:text-gray-400 hover:text-primary"
              >
                Privacy Policy
              </Link>
              <Link
                href="/terms"
                className="text-sm text-gray-600 dark:text-gray-400 hover:text-primary"
              >
                Terms of Service
              </Link>
              <Link
                href="/contact"
                className="text-sm text-gray-600 dark:text-gray-400 hover:text-primary"
              >
                Contact
              </Link>
            </nav>
          </div>
        </div>
      </footer>
    </div>
  );
}