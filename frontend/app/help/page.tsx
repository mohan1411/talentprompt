'use client';

import Link from 'next/link';
import { 
  ArrowLeft, 
  HelpCircle, 
  Chrome, 
  Download, 
  Upload, 
  Search,
  MessageSquare,
  Shield,
  Zap,
  Mail,
  ExternalLink
} from 'lucide-react';

export default function HelpPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="mb-8">
          <Link
            href="/"
            className="inline-flex items-center text-sm text-gray-600 dark:text-gray-400 hover:text-primary mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Home
          </Link>
          
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
            <HelpCircle className="h-8 w-8" />
            Help Center
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Get help with the Promtitude Chrome Extension and platform
          </p>
        </div>

        {/* Chrome Extension Help */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow mb-8">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <Chrome className="h-5 w-5" />
              Chrome Extension Guide
            </h2>
          </div>
          
          <div className="p-6 space-y-6">
            {/* Installation */}
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                <Download className="h-4 w-4" />
                Installation
              </h3>
              <ol className="list-decimal list-inside space-y-2 text-gray-600 dark:text-gray-400">
                <li>Visit the Chrome Web Store and search for "Promtitude"</li>
                <li>Click "Add to Chrome" button</li>
                <li>Confirm the installation when prompted</li>
                <li>The Promtitude icon will appear in your browser toolbar</li>
              </ol>
            </div>

            {/* Getting Started */}
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                <Zap className="h-4 w-4" />
                Getting Started
              </h3>
              <ol className="list-decimal list-inside space-y-2 text-gray-600 dark:text-gray-400">
                <li>Click the Promtitude icon in your toolbar</li>
                <li>Sign in with your Promtitude account (or create one free)</li>
                <li>Navigate to any LinkedIn profile</li>
                <li>Click "Import Profile" to add candidates to your database</li>
              </ol>
            </div>

            {/* Importing Profiles */}
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                <Upload className="h-4 w-4" />
                Importing LinkedIn Profiles
              </h3>
              <ul className="list-disc list-inside space-y-2 text-gray-600 dark:text-gray-400">
                <li>The extension automatically detects when you're on a LinkedIn profile</li>
                <li>Click "Import Profile" to add the candidate to your database</li>
                <li>Duplicate profiles are automatically detected and prevented</li>
                <li>You can import multiple profiles from search results</li>
                <li>All data is securely stored in your Promtitude account</li>
              </ul>
            </div>

            {/* Authentication */}
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                <Shield className="h-4 w-4" />
                OAuth Authentication
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-2">
                If you signed up with Google or GitHub, you'll need to use an access code:
              </p>
              <ol className="list-decimal list-inside space-y-2 text-gray-600 dark:text-gray-400">
                <li>Enter your email address</li>
                <li>Click "Get Code" button</li>
                <li>A browser tab will open - sign in with your OAuth provider</li>
                <li>Copy the 6-character code shown</li>
                <li>Paste it in the extension and click "Sign In"</li>
              </ol>
            </div>
          </div>
        </div>

        {/* Platform Features */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow mb-8">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Platform Features</h2>
          </div>
          
          <div className="p-6 space-y-6">
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                <Search className="h-4 w-4" />
                Mind Reader Search
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Use natural language to search for candidates. The AI understands context, 
                corrects typos, and expands skill synonyms automatically.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                <MessageSquare className="h-4 w-4" />
                AI Interview Copilot
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Get real-time assistance during interviews with live transcription, 
                suggested questions, and instant insights.
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                <Mail className="h-4 w-4" />
                AI Outreach Messages
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Generate personalized outreach messages that match the candidate's 
                background and your job requirements.
              </p>
            </div>
          </div>
        </div>

        {/* Troubleshooting */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow mb-8">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Troubleshooting</h2>
          </div>
          
          <div className="p-6 space-y-4">
            <div className="border-l-4 border-blue-500 pl-4">
              <h4 className="font-semibold text-gray-900 dark:text-white">Extension not working on LinkedIn?</h4>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Make sure you're on linkedin.com (not a local version). Try refreshing the page or reinstalling the extension.
              </p>
            </div>

            <div className="border-l-4 border-blue-500 pl-4">
              <h4 className="font-semibold text-gray-900 dark:text-white">Can't sign in with OAuth?</h4>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Make sure pop-ups are allowed for promtitude.com. Use the "Get Code" button to generate an access code.
              </p>
            </div>

            <div className="border-l-4 border-blue-500 pl-4">
              <h4 className="font-semibold text-gray-900 dark:text-white">Import button not appearing?</h4>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                The extension only works on public LinkedIn profiles. Make sure you're signed in to LinkedIn.
              </p>
            </div>
          </div>
        </div>

        {/* Contact Support */}
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6 text-center">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Need More Help?
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Our support team is here to help you get the most out of Promtitude.
          </p>
          <div className="flex justify-center gap-4">
            <a
              href="mailto:support@promtitude.com"
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90 transition-colors"
            >
              <Mail className="h-4 w-4" />
              Email Support
            </a>
            <Link
              href="/contact"
              className="inline-flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-white rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              Contact Form
              <ExternalLink className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}