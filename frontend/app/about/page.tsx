import type { Metadata } from 'next';
import Link from 'next/link';
import { 
  Target, Sparkles, Shield, Heart, ArrowRight, Users 
} from 'lucide-react';
import { pageMetadata } from '@/lib/seo/config';

export const metadata: Metadata = {
  title: pageMetadata.about.title,
  description: pageMetadata.about.description,
  keywords: pageMetadata.about.keywords,
};

export default function AboutPage() {
  const values = [
    {
      icon: Heart,
      title: 'Human-First AI',
      description: 'We believe AI should enhance human judgment, not replace it. Our tools empower recruiters to make better decisions faster.'
    },
    {
      icon: Shield,
      title: 'Privacy by Design',
      description: 'Candidate data is sacred. We\'ve built privacy and security into every layer of our platform from day one.'
    },
    {
      icon: Sparkles,
      title: 'Continuous Innovation',
      description: 'The recruiting landscape evolves daily. We\'re committed to staying ahead with cutting-edge AI research and development.'
    },
    {
      icon: Users,
      title: 'Community Driven',
      description: 'Our best features come from recruiter feedback. We\'re building Promtitude together with our users.'
    }
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
            <Link href="/features" className="text-sm text-gray-600 dark:text-gray-400 hover:text-primary">
              Features
            </Link>
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
            Building the Future of 
            <span className="text-blue-600 dark:text-blue-400"> Human-Centered</span> Recruiting
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400 mb-8">
            We're on a mission to make hiring faster, fairer, and more human by combining 
            the best of AI technology with recruiter expertise.
          </p>
        </div>
      </section>

      {/* Mission Section */}
      <section className="py-16 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-800">
        <div className="container mx-auto px-4">
          <div className="max-w-6xl mx-auto grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">
                Our Mission
              </h2>
              <p className="text-lg text-gray-600 dark:text-gray-400 mb-6">
                Every great company is built on great people. Yet finding those people has become 
                increasingly complex and time-consuming.
              </p>
              <p className="text-lg text-gray-600 dark:text-gray-400 mb-6">
                We believe recruiters should spend their time building relationships and making 
                strategic decisions, not wrestling with Boolean queries or drowning in administrative tasks.
              </p>
              <p className="text-lg text-gray-600 dark:text-gray-400">
                That's why we're building Promtitude – to give recruiters superpowers through AI, 
                so they can focus on what really matters: finding and connecting with amazing talent.
              </p>
            </div>
            <div className="relative">
              <div className="bg-white dark:bg-gray-700 rounded-lg p-8 shadow-lg">
                <Target className="h-12 w-12 text-blue-600 dark:text-blue-400 mb-4" />
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                  By 2027, we aim to:
                </h3>
                <ul className="space-y-3">
                  <li className="flex items-start gap-2">
                    <div className="w-6 h-6 bg-blue-100 dark:bg-blue-900/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-xs font-bold text-blue-600 dark:text-blue-400">1</span>
                    </div>
                    <span className="text-gray-700 dark:text-gray-300">
                      Help 100,000+ recruiters find their perfect candidates
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <div className="w-6 h-6 bg-blue-100 dark:bg-blue-900/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-xs font-bold text-blue-600 dark:text-blue-400">2</span>
                    </div>
                    <span className="text-gray-700 dark:text-gray-300">
                      Reduce average time-to-hire by 50% industry-wide
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <div className="w-6 h-6 bg-blue-100 dark:bg-blue-900/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-xs font-bold text-blue-600 dark:text-blue-400">3</span>
                    </div>
                    <span className="text-gray-700 dark:text-gray-300">
                      Create 10 million meaningful career connections
                    </span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Values Section */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              Our Values
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400">
              These principles guide every decision we make and every feature we build.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
            {values.map((value, index) => (
              <div key={index} className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                <div className="w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center mb-4">
                  <value.icon className="h-6 w-6 text-gray-700 dark:text-gray-300" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  {value.title}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {value.description}
                </p>
              </div>
            ))}
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
            Join thousands of recruiters who are building the future of hiring with Promtitude.
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/register" className="bg-white text-blue-600 px-8 py-3 rounded-lg font-medium hover:bg-gray-100 transition-colors inline-flex items-center gap-2">
              Start Free Trial
              <ArrowRight className="h-5 w-5" />
            </Link>
            <Link href="/contact" className="border-2 border-white text-white px-8 py-3 rounded-lg font-medium hover:bg-white/10 transition-colors">
              Get in Touch
            </Link>
          </div>
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