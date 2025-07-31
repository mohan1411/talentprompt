'use client';

import { useState } from 'react';
import type { Metadata } from 'next';
import Link from 'next/link';
import { Check, X, HelpCircle, Zap, Building2, Rocket, ArrowRight } from 'lucide-react';
import { pageMetadata } from '@/lib/seo/config';

// export const metadata: Metadata = {
//   title: pageMetadata.pricing.title,
//   description: pageMetadata.pricing.description,
//   keywords: pageMetadata.pricing.keywords,
// };

export default function PricingPage() {
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'annual'>('monthly');

  const plans = [
    {
      name: 'Starter',
      description: 'Perfect for individual recruiters and small teams',
      price: {
        monthly: 49,
        annual: 39
      },
      features: [
        { name: 'Up to 100 active candidates', included: true },
        { name: 'Natural language search', included: true },
        { name: 'Chrome extension', included: true },
        { name: '10 AI interview sessions/month', included: true },
        { name: 'Basic analytics', included: true },
        { name: 'Email support', included: true },
        { name: 'API access', included: false },
        { name: 'Custom integrations', included: false },
        { name: 'Dedicated account manager', included: false }
      ],
      cta: 'Start Free Trial',
      popular: false,
      icon: Zap
    },
    {
      name: 'Professional',
      description: 'For growing teams who need more power',
      price: {
        monthly: 149,
        annual: 119
      },
      features: [
        { name: 'Up to 1,000 active candidates', included: true },
        { name: 'Natural language search', included: true },
        { name: 'Chrome extension', included: true },
        { name: 'Unlimited AI interview sessions', included: true },
        { name: 'Advanced analytics & insights', included: true },
        { name: 'Priority email & chat support', included: true },
        { name: 'API access', included: true },
        { name: 'Custom integrations', included: false },
        { name: 'Dedicated account manager', included: false }
      ],
      cta: 'Start Free Trial',
      popular: true,
      icon: Rocket
    },
    {
      name: 'Enterprise',
      description: 'For large teams with custom needs',
      price: {
        monthly: 'Custom',
        annual: 'Custom'
      },
      features: [
        { name: 'Unlimited candidates', included: true },
        { name: 'Natural language search', included: true },
        { name: 'Chrome extension', included: true },
        { name: 'Unlimited AI interview sessions', included: true },
        { name: 'Advanced analytics & insights', included: true },
        { name: '24/7 phone & email support', included: true },
        { name: 'API access', included: true },
        { name: 'Custom integrations', included: true },
        { name: 'Dedicated account manager', included: true }
      ],
      cta: 'Contact Sales',
      popular: false,
      icon: Building2
    }
  ];

  const faqs = [
    {
      question: 'Can I change plans anytime?',
      answer: 'Yes! You can upgrade or downgrade your plan at any time. Changes take effect at the next billing cycle.'
    },
    {
      question: 'What happens after my free trial?',
      answer: 'After your 14-day free trial, you\'ll be automatically enrolled in your selected plan. You can cancel anytime during the trial without being charged.'
    },
    {
      question: 'Do you offer discounts for non-profits?',
      answer: 'Yes, we offer a 30% discount for registered non-profit organizations. Contact our sales team with your non-profit documentation.'
    },
    {
      question: 'Is my data secure?',
      answer: 'Absolutely. We use bank-level encryption, are SOC 2 Type II certified, and fully GDPR compliant. Your data is never shared with third parties.'
    },
    {
      question: 'Can I import my existing candidate database?',
      answer: 'Yes! We support bulk imports from CSV, Excel, and most major ATS systems. Our team can help with the migration process.'
    },
    {
      question: 'What counts as an "active candidate"?',
      answer: 'Active candidates are those you\'ve interacted with in the last 90 days. Archived candidates don\'t count against your limit.'
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
            Simple, Transparent Pricing
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400 mb-8">
            Start with a 14-day free trial. No credit card required.
          </p>
          
          {/* Billing Toggle */}
          <div className="inline-flex items-center gap-4 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg">
            <button
              onClick={() => setBillingPeriod('monthly')}
              className={`px-4 py-2 rounded-md font-medium transition-colors ${
                billingPeriod === 'monthly'
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400'
              }`}
            >
              Monthly billing
            </button>
            <button
              onClick={() => setBillingPeriod('annual')}
              className={`px-4 py-2 rounded-md font-medium transition-colors ${
                billingPeriod === 'annual'
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400'
              }`}
            >
              Annual billing
              <span className="ml-2 text-xs text-green-600 dark:text-green-400">Save 20%</span>
            </button>
          </div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="container mx-auto px-4 pb-16">
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {plans.map((plan, index) => (
            <div
              key={index}
              className={`relative bg-white dark:bg-gray-800 rounded-xl p-6 ${
                plan.popular
                  ? 'ring-2 ring-blue-600 shadow-lg scale-105'
                  : 'border border-gray-200 dark:border-gray-700'
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <span className="bg-blue-600 text-white text-xs font-bold px-3 py-1 rounded-full">
                    MOST POPULAR
                  </span>
                </div>
              )}
              
              <div className="text-center mb-6">
                <div className="w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <plan.icon className="h-6 w-6 text-gray-700 dark:text-gray-300" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                  {plan.name}
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  {plan.description}
                </p>
              </div>
              
              <div className="text-center mb-6">
                {typeof plan.price === 'object' ? (
                  <>
                    <div className="text-4xl font-bold text-gray-900 dark:text-white">
                      ${plan.price[billingPeriod]}
                    </div>
                    <div className="text-gray-600 dark:text-gray-400">
                      per user/month
                    </div>
                  </>
                ) : (
                  <div className="text-4xl font-bold text-gray-900 dark:text-white">
                    {plan.price}
                  </div>
                )}
              </div>
              
              <ul className="space-y-3 mb-6">
                {plan.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    {feature.included ? (
                      <Check className="h-5 w-5 text-green-500 flex-shrink-0" />
                    ) : (
                      <X className="h-5 w-5 text-gray-300 dark:text-gray-600 flex-shrink-0" />
                    )}
                    <span className={`text-sm ${
                      feature.included
                        ? 'text-gray-700 dark:text-gray-300'
                        : 'text-gray-400 dark:text-gray-600'
                    }`}>
                      {feature.name}
                    </span>
                  </li>
                ))}
              </ul>
              
              <Link
                href={plan.cta === 'Contact Sales' ? '/contact' : '/register'}
                className={`w-full py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 ${
                  plan.popular
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                {plan.cta}
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* Enterprise Section */}
      <section className="py-16 bg-gray-50 dark:bg-gray-800/50">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              Need a Custom Solution?
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">
              We offer flexible plans for teams with specific requirements, 
              including on-premise deployment, custom integrations, and dedicated support.
            </p>
            <div className="grid md:grid-cols-3 gap-6 mb-8">
              <div className="bg-white dark:bg-gray-800 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                  Volume Discounts
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Special pricing for teams with 50+ users
                </p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                  On-Premise Option
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Deploy Promtitude on your own infrastructure
                </p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                  Custom Training
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Personalized onboarding for your team
                </p>
              </div>
            </div>
            <Link href="/contact" className="btn-primary px-8 py-3 text-lg inline-flex items-center gap-2">
              Talk to Sales
              <ArrowRight className="h-5 w-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* FAQs */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-12">
              Frequently Asked Questions
            </h2>
            <div className="space-y-6">
              {faqs.map((faq, index) => (
                <div key={index} className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 flex items-start gap-2">
                    <HelpCircle className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                    {faq.question}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 pl-7">
                    {faq.answer}
                  </p>
                </div>
              ))}
            </div>
            <div className="text-center mt-8">
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Still have questions?
              </p>
              <Link href="/contact" className="text-blue-600 dark:text-blue-400 font-medium hover:underline">
                Contact our sales team →
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-gradient-to-r from-blue-600 to-indigo-700">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Start Your 14-Day Free Trial
          </h2>
          <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
            No credit card required. Full access to all features. Cancel anytime.
          </p>
          <Link href="/register" className="bg-white text-blue-600 px-8 py-3 rounded-lg font-medium hover:bg-gray-100 transition-colors inline-flex items-center gap-2">
            Get Started Free
            <ArrowRight className="h-5 w-5" />
          </Link>
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