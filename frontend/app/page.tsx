'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth/context';
import { 
  Search, Chrome, Clock, Check, ChevronRight,
  FileText, Mic, Mail, Shield, DollarSign
} from 'lucide-react';

export default function HomePage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [showResults, setShowResults] = useState(false);
  const [demoTyping, setDemoTyping] = useState('');

  // Redirect authenticated users to dashboard
  useEffect(() => {
    if (!isLoading && user) {
      router.push('/dashboard');
    }
  }, [user, isLoading, router]);

  // Demo typing effect
  useEffect(() => {
    const demoQuery = "Senior Python developer with AWS experience";
    let index = 0;
    const timer = setInterval(() => {
      if (index <= demoQuery.length) {
        setDemoTyping(demoQuery.slice(0, index));
        index++;
      } else {
        clearInterval(timer);
        setTimeout(() => setShowResults(true), 500);
      }
    }, 50);
    
    return () => clearInterval(timer);
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    router.push('/register');
  };

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900">
      {/* Header */}
      <header className="border-b bg-white dark:bg-gray-900 sticky top-0 z-50">
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
              href="https://chromewebstore.google.com/detail/promtitude-linkedin-profi/hioainkifmclnejpkdhplemgfdpeddio" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-sm text-gray-600 dark:text-gray-400 hover:text-primary flex items-center gap-1"
            >
              <Chrome className="h-4 w-4" />
              <span className="hidden sm:inline">Chrome Extension</span>
            </a>
            <Link href="/login" className="btn-secondary">
              Login
            </Link>
            <Link href="/register" className="btn-primary">
              Try It Free
            </Link>
          </nav>
        </div>
      </header>

      <main>
        {/* Hero Section with Working Demo */}
        <section className="container mx-auto px-4 py-16 lg:py-24">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-4">
              Natural Language Resume Search for Recruiters
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-400 mb-8">
              Find candidates by describing what you need. No Boolean queries.
            </p>

            {/* Interactive Search Demo */}
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 mb-8">
              <form onSubmit={handleSearch} className="mb-6">
                <div className="relative max-w-2xl mx-auto">
                  <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    value={searchQuery || demoTyping}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Try: Python developer with AWS experience"
                    className="w-full pl-12 pr-4 py-4 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  />
                  <button 
                    type="submit"
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  >
                    Search
                  </button>
                </div>
              </form>

              {/* Demo Results */}
              {showResults && (
                <div className="space-y-3 max-w-2xl mx-auto">
                  <div className="text-left p-4 bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-semibold text-gray-900 dark:text-white">Sarah Chen</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Senior Python Developer • 8 years exp</p>
                        <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                          Python, AWS, Django, PostgreSQL, Docker
                        </p>
                      </div>
                      <span className="text-sm font-semibold text-green-600 dark:text-green-400">92% match</span>
                    </div>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Found 47 matching candidates in 0.3 seconds
                    </p>
                  </div>
                </div>
              )}
            </div>

            <Link
              href="/register"
              className="inline-flex items-center px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-lg font-medium"
            >
              Try It Free - No Credit Card
              <ChevronRight className="ml-2 h-5 w-5" />
            </Link>

            <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">
              Free tier: 20 resumes, 10 searches/month
            </p>
          </div>
        </section>

        {/* Value Metrics */}
        <section className="border-y bg-gray-50 dark:bg-gray-800/50 py-12">
          <div className="container mx-auto px-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
              <div>
                <div className="text-3xl font-bold text-gray-900 dark:text-white">0.3s</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Average search time</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-gray-900 dark:text-white">85-90%</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Relevance accuracy</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-gray-900 dark:text-white">70%</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Time saved screening</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-gray-900 dark:text-white">$1.27</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Per resume/month</div>
              </div>
            </div>
          </div>
        </section>

        {/* Problem/Solution Comparison */}
        <section className="py-16 lg:py-24">
          <div className="container mx-auto px-4">
            <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-12">
              The Screening Time Problem
            </h2>
            
            <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
              {/* Traditional Way */}
              <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-6">
                <h3 className="text-xl font-semibold text-red-900 dark:text-red-400 mb-4">
                  Traditional Screening
                </h3>
                <ul className="space-y-3">
                  <li className="flex items-start gap-2">
                    <Clock className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" />
                    <span className="text-gray-700 dark:text-gray-300">
                      <strong>15 minutes</strong> per resume manual review
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Clock className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" />
                    <span className="text-gray-700 dark:text-gray-300">
                      <strong>3 hours</strong> for 100 resumes
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Clock className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" />
                    <span className="text-gray-700 dark:text-gray-300">
                      Boolean search complexity
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Clock className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" />
                    <span className="text-gray-700 dark:text-gray-300">
                      Miss candidates due to typos
                    </span>
                  </li>
                </ul>
              </div>

              {/* With Promtitude */}
              <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-6">
                <h3 className="text-xl font-semibold text-green-900 dark:text-green-400 mb-4">
                  With Promtitude
                </h3>
                <ul className="space-y-3">
                  <li className="flex items-start gap-2">
                    <Check className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5" />
                    <span className="text-gray-700 dark:text-gray-300">
                      <strong>5 minutes</strong> per resume with AI assist
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Check className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5" />
                    <span className="text-gray-700 dark:text-gray-300">
                      <strong>30 minutes</strong> for 100 resumes
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Check className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5" />
                    <span className="text-gray-700 dark:text-gray-300">
                      Natural language search
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Check className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5" />
                    <span className="text-gray-700 dark:text-gray-300">
                      Auto-corrects typos
                    </span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Core Features with Proof */}
        <section className="py-16 lg:py-24 bg-gray-50 dark:bg-gray-800/50">
          <div className="container mx-auto px-4">
            <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-12">
              Three Features That Save You Time
            </h2>

            <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
              {/* Mind Reader Search */}
              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
                <div className="mb-4">
                  <Search className="h-10 w-10 text-blue-600 dark:text-blue-400" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">
                  Natural Language Search
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  Search like you think. Our AI understands context and corrects typos automatically.
                </p>
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded p-3 text-sm">
                  <p className="text-gray-600 dark:text-gray-400 mb-1">You type:</p>
                  <p className="font-mono text-red-600 dark:text-red-400">"Pythonn developr"</p>
                  <p className="text-gray-600 dark:text-gray-400 mt-2 mb-1">We search for:</p>
                  <p className="font-mono text-green-600 dark:text-green-400">"Python developer"</p>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-3">
                  <strong>Time saved:</strong> 70% faster than Boolean
                </p>
              </div>

              {/* Chrome Extension */}
              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
                <div className="mb-4">
                  <Chrome className="h-10 w-10 text-blue-600 dark:text-blue-400" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">
                  One-Click Import
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  Import LinkedIn profiles instantly with our Chrome extension. No copy-paste needed.
                </p>
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded p-3">
                  <ol className="text-sm space-y-2">
                    <li className="flex items-start gap-2">
                      <span className="font-semibold text-gray-700 dark:text-gray-300">1.</span>
                      <span className="text-gray-600 dark:text-gray-400">Visit LinkedIn profile</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="font-semibold text-gray-700 dark:text-gray-300">2.</span>
                      <span className="text-gray-600 dark:text-gray-400">Click extension button</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="font-semibold text-gray-700 dark:text-gray-300">3.</span>
                      <span className="text-gray-600 dark:text-gray-400">Profile imported!</span>
                    </li>
                  </ol>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-3">
                  <strong>Time saved:</strong> 2 minutes per profile
                </p>
              </div>

              {/* AI Interview Assistant */}
              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
                <div className="mb-4">
                  <Mic className="h-10 w-10 text-blue-600 dark:text-blue-400" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">
                  Interview Assistant
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  Real-time transcription and AI suggestions during interviews. Never miss important details.
                </p>
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded p-3 space-y-2">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm text-gray-600 dark:text-gray-400">Live transcription</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm text-gray-600 dark:text-gray-400">Smart follow-ups</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm text-gray-600 dark:text-gray-400">Auto scorecard</span>
                  </div>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-3">
                  <strong>Cost:</strong> $0.50 per 30-min interview
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Pricing Preview */}
        <section className="py-16 lg:py-24">
          <div className="container mx-auto px-4">
            <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-12">
              Simple, Transparent Pricing
            </h2>

            <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
              {/* Free Tier */}
              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Free</h3>
                <p className="text-3xl font-bold text-gray-900 dark:text-white mb-4">$0<span className="text-lg font-normal text-gray-600 dark:text-gray-400">/month</span></p>
                <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                  <li>• 20 resumes</li>
                  <li>• 10 searches/month</li>
                  <li>• Chrome extension</li>
                  <li>• Basic support</li>
                </ul>
              </div>

              {/* Starter */}
              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border-2 border-blue-500 relative">
                <span className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-blue-500 text-white text-xs px-2 py-1 rounded">Most Popular</span>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Starter</h3>
                <p className="text-3xl font-bold text-gray-900 dark:text-white mb-4">$199<span className="text-lg font-normal text-gray-600 dark:text-gray-400">/month</span></p>
                <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                  <li>• 100 resumes</li>
                  <li>• 50 AI searches/month</li>
                  <li>• 100 outreach messages</li>
                  <li>• Email support</li>
                </ul>
              </div>

              {/* Professional */}
              <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Professional</h3>
                <p className="text-3xl font-bold text-gray-900 dark:text-white mb-4">$499<span className="text-lg font-normal text-gray-600 dark:text-gray-400">/month</span></p>
                <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                  <li>• 500 resumes</li>
                  <li>• 200 AI searches/month</li>
                  <li>• 10 AI interviews</li>
                  <li>• Priority support</li>
                </ul>
              </div>
            </div>

            <div className="text-center mt-8">
              <Link href="/register" className="text-blue-600 hover:text-blue-700 font-medium">
                See detailed pricing →
              </Link>
            </div>
          </div>
        </section>

        {/* Technical Transparency */}
        <section className="py-12 bg-gray-50 dark:bg-gray-800/50">
          <div className="container mx-auto px-4">
            <div className="max-w-3xl mx-auto text-center">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Built with Trust and Transparency
              </h3>
              <div className="flex flex-wrap justify-center gap-6 text-sm text-gray-600 dark:text-gray-400">
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4" />
                  <span>GDPR Compliant</span>
                </div>
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  <span>OpenAI GPT-4.1-mini</span>
                </div>
                <div className="flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  <span>No hidden fees</span>
                </div>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-500 mt-4">
                Best for teams hiring 5-50 people/year. Not a full ATS replacement.
              </p>
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="py-16">
          <div className="container mx-auto px-4 text-center">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              Start Finding Better Candidates Today
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400 mb-8 max-w-2xl mx-auto">
              Join recruiters who save 2.5 hours per 100 resumes with natural language search.
            </p>
            <Link
              href="/register"
              className="inline-flex items-center px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-lg font-medium"
            >
              Start Free - Find 20 Candidates
              <ChevronRight className="ml-2 h-5 w-5" />
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