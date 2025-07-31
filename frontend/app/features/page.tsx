import type { Metadata } from 'next';
import Link from 'next/link';
import { 
  Search, Brain, Chrome, Mic, Zap, Shield, 
  MessageSquare, BarChart3, Clock, Users,
  CheckCircle, ArrowRight, Sparkles
} from 'lucide-react';
import { pageMetadata } from '@/lib/seo/config';

export const metadata: Metadata = {
  title: pageMetadata.features.title,
  description: pageMetadata.features.description,
  keywords: pageMetadata.features.keywords,
};

export default function FeaturesPage() {
  const features = [
    {
      icon: Search,
      title: 'Mind Reader Search',
      subtitle: 'Natural Language Understanding',
      description: 'Search for candidates the way you think. No complex Boolean queries needed.',
      benefits: [
        'Auto-corrects typos and understands context',
        'Identifies primary and secondary skills',
        'Suggests related technologies automatically',
        'Works with incomplete or vague descriptions'
      ],
      color: 'blue'
    },
    {
      icon: Brain,
      title: 'AI Interview Assistant',
      subtitle: 'Real-time Interview Support',
      description: 'Get AI-powered assistance during interviews with live transcription and smart suggestions.',
      benefits: [
        'Real-time transcription of conversations',
        'Suggested follow-up questions',
        'Automatic scorecard generation',
        'Key moment highlighting'
      ],
      color: 'purple'
    },
    {
      icon: Chrome,
      title: 'Chrome Extension',
      subtitle: 'One-Click LinkedIn Import',
      description: 'Import candidate profiles from LinkedIn with a single click. No copy-paste needed.',
      benefits: [
        'Works on any LinkedIn profile',
        'Extracts complete work history',
        'Captures skills and endorsements',
        'Syncs instantly with your database'
      ],
      color: 'green'
    },
    {
      icon: MessageSquare,
      title: 'Smart Outreach',
      subtitle: 'AI-Generated Messages',
      description: 'Create personalized outreach messages that actually get responses.',
      benefits: [
        'Personalized for each candidate',
        'Multiple tone options available',
        'A/B test different approaches',
        'Track open and response rates'
      ],
      color: 'orange'
    },
    {
      icon: BarChart3,
      title: 'Intelligent Analytics',
      subtitle: 'Data-Driven Insights',
      description: 'Understand your hiring funnel with AI-powered analytics and predictions.',
      benefits: [
        'Candidate availability scoring',
        'Career trajectory analysis',
        'Skill gap identification',
        'Time-to-hire predictions'
      ],
      color: 'indigo'
    },
    {
      icon: Shield,
      title: 'Privacy & Compliance',
      subtitle: 'Enterprise-Ready Security',
      description: 'Built with privacy and compliance at the core. Your data is always secure.',
      benefits: [
        'GDPR & CCPA compliant',
        'End-to-end encryption',
        'Role-based access control',
        'Audit trail for all actions'
      ],
      color: 'gray'
    }
  ];

  const integrations = [
    { name: 'LinkedIn', icon: '🔗' },
    { name: 'Google Calendar', icon: '📅' },
    { name: 'Slack', icon: '💬' },
    { name: 'Microsoft Teams', icon: '👥' },
    { name: 'Gmail', icon: '📧' },
    { name: 'Outlook', icon: '📨' }
  ];

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900">
      {/* Header */}
      <header className="border-b bg-white dark:bg-gray-900 sticky top-0 z-50">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <Link href="/" className="flex items-center">
            <img 
              src="/logo-horizontal.svg" 
              alt="Promtitude - AI Recruitment Platform" 
              className="h-10 w-auto"
            />
          </Link>
          <nav className="flex gap-4 items-center">
            <Link href="/pricing" className="text-sm text-gray-600 dark:text-gray-400 hover:text-primary">
              Pricing
            </Link>
            <Link href="/login" className="btn-secondary">
              Login
            </Link>
            <Link href="/register" className="btn-primary">
              Start Free Trial
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 lg:py-24">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-6">
            Every Feature Built to Make Recruiting 
            <span className="text-blue-600 dark:text-blue-400"> 10x Faster</span>
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400 mb-8">
            From AI-powered search to real-time interview assistance, discover how Promtitude 
            transforms every step of your recruiting workflow.
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/register" className="btn-primary px-6 py-3 text-lg">
              Start 14-Day Free Trial
            </Link>
            <Link href="/demo" className="btn-secondary px-6 py-3 text-lg">
              Watch Demo
            </Link>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="container mx-auto px-4 py-16">
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="group relative bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100 dark:border-gray-700">
              <div className={`w-12 h-12 bg-${feature.color}-100 dark:bg-${feature.color}-900/20 rounded-lg flex items-center justify-center mb-4`}>
                <feature.icon className={`h-6 w-6 text-${feature.color}-600 dark:text-${feature.color}-400`} />
              </div>
              
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                {feature.title}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                {feature.subtitle}
              </p>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                {feature.description}
              </p>
              
              <ul className="space-y-2">
                {feature.benefits.map((benefit, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>{benefit}</span>
                  </li>
                ))}
              </ul>
              
              <div className="absolute top-6 right-6 opacity-0 group-hover:opacity-100 transition-opacity">
                <Sparkles className="h-5 w-5 text-yellow-500" />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Detailed Feature Sections */}
      <section className="py-16 bg-gray-50 dark:bg-gray-800/50">
        <div className="container mx-auto px-4">
          {/* Mind Reader Search Detail */}
          <div className="max-w-6xl mx-auto mb-24">
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-100 dark:bg-blue-900/20 rounded-full mb-4">
                  <Search className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                  <span className="text-sm text-blue-600 dark:text-blue-400 font-medium">Mind Reader Search</span>
                </div>
                <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
                  Search Like You Think, Find Who You Need
                </h2>
                <p className="text-lg text-gray-600 dark:text-gray-400 mb-6">
                  Our AI understands what you're looking for, even when you don't use the exact terms. 
                  It's like having a senior recruiter who knows every skill synonym and related technology.
                </p>
                
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/20 rounded-full flex items-center justify-center flex-shrink-0">
                      <span className="text-sm font-bold text-blue-600 dark:text-blue-400">1</span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">Type naturally</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        "Python developer with cloud experience" or even with typos like "Pythn developr"
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/20 rounded-full flex items-center justify-center flex-shrink-0">
                      <span className="text-sm font-bold text-blue-600 dark:text-blue-400">2</span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">AI understands context</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Automatically identifies AWS, Docker, Kubernetes as related cloud skills
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/20 rounded-full flex items-center justify-center flex-shrink-0">
                      <span className="text-sm font-bold text-blue-600 dark:text-blue-400">3</span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">Get perfect matches</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Ranked by relevance with clear explanations for each match
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-900 rounded-lg p-6 shadow-xl">
                <div className="bg-gray-800 rounded-lg p-4 mb-4">
                  <p className="text-sm text-gray-400 mb-2">You search for:</p>
                  <p className="text-white font-mono">"Senior React developer with Node"</p>
                </div>
                <div className="space-y-3">
                  <div className="bg-gray-800 rounded-lg p-3">
                    <p className="text-xs text-gray-400 mb-1">AI identifies:</p>
                    <div className="flex flex-wrap gap-2">
                      <span className="px-2 py-1 bg-blue-600 text-white text-xs rounded">React</span>
                      <span className="px-2 py-1 bg-blue-600 text-white text-xs rounded">Node.js</span>
                      <span className="px-2 py-1 bg-blue-400 text-white text-xs rounded">JavaScript</span>
                      <span className="px-2 py-1 bg-blue-400 text-white text-xs rounded">TypeScript</span>
                      <span className="px-2 py-1 bg-gray-600 text-white text-xs rounded">Redux</span>
                      <span className="px-2 py-1 bg-gray-600 text-white text-xs rounded">Express</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* AI Interview Assistant Detail */}
          <div className="max-w-6xl mx-auto mb-24">
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div className="order-2 lg:order-1">
                <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Interview in progress</span>
                    <Clock className="h-4 w-4 text-gray-400 ml-auto" />
                    <span className="text-sm text-gray-600 dark:text-gray-400">24:35</span>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="bg-gray-50 dark:bg-gray-700 rounded p-3">
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        <span className="font-medium">Candidate:</span> "I've worked extensively with microservices architecture..."
                      </p>
                    </div>
                    
                    <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded p-3">
                      <p className="text-xs text-blue-600 dark:text-blue-400 font-medium mb-1">
                        <Brain className="h-3 w-3 inline mr-1" />
                        AI Suggestion
                      </p>
                      <p className="text-sm text-blue-700 dark:text-blue-300">
                        Ask about specific microservices patterns they've implemented
                      </p>
                    </div>
                    
                    <div className="flex gap-2">
                      <button className="flex-1 py-2 bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded text-sm font-medium">
                        Strong Answer
                      </button>
                      <button className="flex-1 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded text-sm font-medium">
                        Needs Clarification
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="order-1 lg:order-2">
                <div className="inline-flex items-center gap-2 px-3 py-1 bg-purple-100 dark:bg-purple-900/20 rounded-full mb-4">
                  <Brain className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                  <span className="text-sm text-purple-600 dark:text-purple-400 font-medium">AI Interview Assistant</span>
                </div>
                <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
                  Never Miss Important Details During Interviews
                </h2>
                <p className="text-lg text-gray-600 dark:text-gray-400 mb-6">
                  Focus on the conversation while AI handles the notes. Get real-time transcription, 
                  smart follow-up suggestions, and automatic scorecards.
                </p>
                
                <ul className="space-y-3">
                  <li className="flex items-start gap-3">
                    <Mic className="h-5 w-5 text-purple-600 dark:text-purple-400 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">Live Transcription</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Every word captured and searchable later
                      </p>
                    </div>
                  </li>
                  <li className="flex items-start gap-3">
                    <Zap className="h-5 w-5 text-purple-600 dark:text-purple-400 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">Smart Suggestions</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        AI suggests follow-up questions based on responses
                      </p>
                    </div>
                  </li>
                  <li className="flex items-start gap-3">
                    <BarChart3 className="h-5 w-5 text-purple-600 dark:text-purple-400 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-white">Instant Scorecards</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Automated evaluation based on your criteria
                      </p>
                    </div>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Integrations */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              Works With Your Existing Tools
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400 mb-12">
              Promtitude integrates seamlessly with the tools you already use every day.
            </p>
            
            <div className="grid grid-cols-3 md:grid-cols-6 gap-6">
              {integrations.map((integration, index) => (
                <div key={index} className="flex flex-col items-center gap-2">
                  <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center text-2xl">
                    {integration.icon}
                  </div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">{integration.name}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-gradient-to-r from-blue-600 to-indigo-700">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Transform Your Recruiting?
          </h2>
          <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
            Join thousands of recruiters who are finding better candidates faster with AI.
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/register" className="bg-white text-blue-600 px-8 py-3 rounded-lg font-medium hover:bg-gray-100 transition-colors inline-flex items-center gap-2">
              Start Free Trial
              <ArrowRight className="h-5 w-5" />
            </Link>
            <Link href="/pricing" className="border-2 border-white text-white px-8 py-3 rounded-lg font-medium hover:bg-white/10 transition-colors">
              View Pricing
            </Link>
          </div>
          <p className="text-sm text-blue-200 mt-4">
            No credit card required • 14-day free trial • Cancel anytime
          </p>
        </div>
      </section>

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
              <Link href="/privacy" className="text-sm text-gray-600 dark:text-gray-400 hover:text-primary">
                Privacy Policy
              </Link>
              <Link href="/terms" className="text-sm text-gray-600 dark:text-gray-400 hover:text-primary">
                Terms of Service
              </Link>
              <Link href="/contact" className="text-sm text-gray-600 dark:text-gray-400 hover:text-primary">
                Contact
              </Link>
            </nav>
          </div>
        </div>
      </footer>
    </div>
  );
}