'use client';

import Link from 'next/link';
import { useState } from 'react';
import { ChevronDown, ChevronUp, Search, HelpCircle } from 'lucide-react';

interface FAQItem {
  question: string;
  answer: string;
  category: string;
}

const faqs: FAQItem[] = [
  // Getting Started
  {
    category: 'Getting Started',
    question: 'What is Promtitude?',
    answer: 'Promtitude is an AI-powered recruitment platform that helps you find perfect candidates faster using natural language search, AI interview assistance, and automated outreach. Our platform uses advanced AI from OpenAI and Anthropic to revolutionize how you hire.'
  },
  {
    category: 'Getting Started',
    question: 'How do I get started with Promtitude?',
    answer: 'Getting started is easy! Simply sign up for a free 14-day trial, upload your first resumes, and start searching using natural language. No credit card required. Our onboarding wizard will guide you through the setup process.'
  },
  {
    category: 'Getting Started',
    question: 'Do I need technical knowledge to use Promtitude?',
    answer: 'Not at all! Promtitude is designed for recruiters and HR professionals. You can search for candidates by describing what you need in plain English, just like talking to a colleague.'
  },
  // Features
  {
    category: 'Features',
    question: 'How does natural language search work?',
    answer: 'Instead of using complex boolean queries, you can search naturally. For example: "Find me a senior React developer with 5+ years experience who has worked on e-commerce projects". Our AI understands context and finds the best matches.'
  },
  {
    category: 'Features',
    question: 'What is the AI Interview Copilot?',
    answer: 'The AI Interview Copilot provides real-time assistance during interviews. It offers live transcription, suggests follow-up questions, detects key skills mentioned, and generates instant scorecards. It\'s like having an expert recruiter assistant in every interview.'
  },
  {
    category: 'Features',
    question: 'How does AI outreach message generation work?',
    answer: 'Based on a candidate\'s profile and your job requirements, our AI generates personalized outreach messages. You can choose between casual, professional, or technical tones. Messages are crafted to maximize response rates while maintaining authenticity.'
  },
  {
    category: 'Features',
    question: 'Can I import profiles from LinkedIn?',
    answer: 'Yes! Our Chrome extension allows you to import LinkedIn profiles with one click. The extension extracts publicly available information and adds it to your candidate database for easy searching and outreach.'
  },
  // Pricing & Plans
  {
    category: 'Pricing & Plans',
    question: 'What pricing plans do you offer?',
    answer: 'We offer flexible pricing plans starting from $99/month for small teams. All plans include core features like natural language search and AI assistance. Enterprise plans include advanced features like API access and dedicated support. Contact sales for custom pricing.'
  },
  {
    category: 'Pricing & Plans',
    question: 'Is there a free trial?',
    answer: 'Yes! We offer a 14-day free trial with full access to all features. No credit card required. You can upload up to 100 resumes and conduct unlimited searches during the trial period.'
  },
  {
    category: 'Pricing & Plans',
    question: 'Can I change or cancel my plan anytime?',
    answer: 'Absolutely! You can upgrade, downgrade, or cancel your subscription at any time from your account settings. If you cancel, you\'ll retain access until the end of your billing period.'
  },
  // Privacy & Security
  {
    category: 'Privacy & Security',
    question: 'How secure is my data?',
    answer: 'We take security seriously. All data is encrypted in transit and at rest. We use industry-standard security practices, regular security audits, and are working towards SOC 2 compliance. Your candidate data is never shared or sold.'
  },
  {
    category: 'Privacy & Security',
    question: 'Are you GDPR compliant?',
    answer: 'Yes, we are GDPR compliant. We have comprehensive privacy policies, data processing agreements, and give users full control over their data. You can export or delete your data at any time from your account settings.'
  },
  {
    category: 'Privacy & Security',
    question: 'Where is my data stored?',
    answer: 'Your data is securely stored in AWS data centers with automatic backups and disaster recovery. We use industry-leading infrastructure providers to ensure high availability and data protection.'
  },
  // Technical
  {
    category: 'Technical',
    question: 'What file formats can I upload?',
    answer: 'We support PDF, DOC, DOCX, and TXT formats for resume uploads. Our AI automatically parses and extracts relevant information regardless of the resume format or layout.'
  },
  {
    category: 'Technical',
    question: 'Is there an API available?',
    answer: 'Yes! Our Enterprise plans include API access for integrating Promtitude with your existing HR systems. The API supports resume upload, search, and candidate management operations.'
  },
  {
    category: 'Technical',
    question: 'What browsers are supported?',
    answer: 'Promtitude works on all modern browsers including Chrome, Firefox, Safari, and Edge. Our Chrome extension for LinkedIn import is currently only available for Google Chrome.'
  },
  // Support
  {
    category: 'Support',
    question: 'How can I get help?',
    answer: 'We offer multiple support channels: email support at support@promtitude.com, comprehensive documentation, and live chat for paid plans. Enterprise customers get dedicated account managers and priority support.'
  },
  {
    category: 'Support',
    question: 'Do you offer training?',
    answer: 'Yes! We provide onboarding sessions for new customers, video tutorials, and regular webinars on best practices. Enterprise customers can request custom training sessions for their teams.'
  }
];

export default function FAQPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [openItems, setOpenItems] = useState<number[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  const categories = ['All', ...Array.from(new Set(faqs.map(faq => faq.category)))];

  const filteredFAQs = faqs.filter(faq => {
    const matchesSearch = faq.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         faq.answer.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'All' || faq.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const toggleItem = (index: number) => {
    setOpenItems(prev =>
      prev.includes(index)
        ? prev.filter(i => i !== index)
        : [...prev, index]
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-12 max-w-5xl">
        <Link href="/" className="text-blue-600 hover:text-blue-800 dark:text-blue-400 mb-8 inline-block">
          ← Back to Home
        </Link>
        
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4 text-gray-900 dark:text-white">
            Frequently Asked Questions
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400">
            Everything you need to know about Promtitude
          </p>
        </div>

        {/* Search Bar */}
        <div className="mb-8">
          <div className="relative max-w-2xl mx-auto">
            <input
              type="text"
              placeholder="Search FAQs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-3 pl-12 pr-4 text-gray-900 dark:text-white bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          </div>
        </div>

        {/* Category Filter */}
        <div className="mb-8 flex flex-wrap justify-center gap-2">
          {categories.map(category => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                selectedCategory === category
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              {category}
            </button>
          ))}
        </div>

        {/* FAQ Items */}
        <div className="space-y-4">
          {filteredFAQs.length === 0 ? (
            <div className="text-center py-12">
              <HelpCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400">
                No FAQs found matching your search. Try different keywords or browse all categories.
              </p>
            </div>
          ) : (
            filteredFAQs.map((faq, index) => (
              <div
                key={index}
                className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden"
              >
                <button
                  onClick={() => toggleItem(index)}
                  className="w-full px-6 py-4 text-left flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <div className="flex-1 pr-4">
                    <p className="text-sm text-blue-600 dark:text-blue-400 mb-1">{faq.category}</p>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      {faq.question}
                    </h3>
                  </div>
                  {openItems.includes(index) ? (
                    <ChevronUp className="h-5 w-5 text-gray-500 flex-shrink-0" />
                  ) : (
                    <ChevronDown className="h-5 w-5 text-gray-500 flex-shrink-0" />
                  )}
                </button>
                {openItems.includes(index) && (
                  <div className="px-6 pb-4 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-gray-700 dark:text-gray-300 mt-4 leading-relaxed">
                      {faq.answer}
                    </p>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Contact Section */}
        <div className="mt-16 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-8 text-center">
          <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">
            Still have questions?
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Can't find the answer you're looking for? Our support team is here to help.
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <Link
              href="/contact"
              className="btn-primary px-6 py-2"
            >
              Contact Support
            </Link>
            <a
              href="mailto:support@promtitude.com"
              className="btn-secondary px-6 py-2"
            >
              Email Us
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}