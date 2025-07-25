'use client';

import Link from 'next/link';

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-12 max-w-4xl">
        <Link href="/" className="text-blue-600 hover:text-blue-800 dark:text-blue-400 mb-8 inline-block">
          ← Back to Home
        </Link>
        
        <h1 className="text-4xl font-bold mb-8 text-gray-900 dark:text-white">Privacy Policy</h1>
        
        <div className="prose prose-lg dark:prose-invert max-w-none">
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Last updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
          </p>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">1. Introduction</h2>
            <p className="text-gray-700 dark:text-gray-300 mb-4">
              Promtitude ("we," "our," or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our recruitment platform, web application, and Chrome browser extension.
            </p>
            <p className="text-gray-700 dark:text-gray-300">
              By using Promtitude, you agree to the collection and use of information in accordance with this policy. If you do not agree with our policies and practices, please do not use our services.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">2. Information We Collect</h2>
            
            <h3 className="text-xl font-medium mb-3 text-gray-800 dark:text-gray-200">2.1 Information You Provide</h3>
            <ul className="list-disc pl-6 mb-4 text-gray-700 dark:text-gray-300">
              <li>Account information (name, email, company, job title)</li>
              <li>Password (encrypted) or OAuth tokens (for Google Sign-in users)</li>
              <li>Resume data and candidate information you upload</li>
              <li>Interview recordings and transcriptions</li>
              <li>Messages and communications through our platform</li>
              <li>Payment information (processed securely through third-party providers)</li>
            </ul>

            <h3 className="text-xl font-medium mb-3 text-gray-800 dark:text-gray-200">2.2 Chrome Extension Data</h3>
            <p className="text-gray-700 dark:text-gray-300 mb-3">When using the Promtitude Chrome Extension, we collect:</p>
            <ul className="list-disc pl-6 mb-4 text-gray-700 dark:text-gray-300">
              <li>Publicly visible LinkedIn profile information (name, headline, location, experience, education, skills)</li>
              <li>LinkedIn profile URLs</li>
              <li>Import queue data and import statistics</li>
              <li>Browser storage data for user preferences and authentication</li>
            </ul>

            <h3 className="text-xl font-medium mb-3 text-gray-800 dark:text-gray-200">2.3 Information We Collect Automatically</h3>
            <ul className="list-disc pl-6 mb-4 text-gray-700 dark:text-gray-300">
              <li>Usage data (features used, searches performed, time spent)</li>
              <li>Device information (browser type, operating system)</li>
              <li>IP address and approximate location</li>
              <li>Cookies and similar tracking technologies</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">3. How We Use Your Information</h2>
            <p className="text-gray-700 dark:text-gray-300 mb-4">We use the collected information to:</p>
            <ul className="list-disc pl-6 mb-4 text-gray-700 dark:text-gray-300">
              <li>Provide and maintain our services</li>
              <li>Process and analyze resumes using AI</li>
              <li>Generate interview insights and recommendations</li>
              <li>Improve our AI models and service quality</li>
              <li>Communicate with you about our services</li>
              <li>Ensure platform security and prevent fraud</li>
              <li>Comply with legal obligations</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">4. Data Isolation and Security</h2>
            <p className="text-gray-700 dark:text-gray-300 mb-4">We implement strict data isolation and security measures:</p>
            <ul className="list-disc pl-6 mb-4 text-gray-700 dark:text-gray-300">
              <li><strong>User Data Isolation:</strong> Each user's data is strictly isolated - you can only see profiles and data you've imported</li>
              <li><strong>Shared Browser Protection:</strong> In shared browser environments, user data remains private to each account</li>
              <li><strong>Chrome Extension Security:</strong> Extension data is stored per-user and isolated between accounts</li>
              <li><strong>Encryption:</strong> All data transmission is encrypted using HTTPS/TLS</li>
              <li><strong>Secure Storage:</strong> Authentication tokens are securely stored and never exposed</li>
              <li><strong>Password Security:</strong> Passwords are hashed using industry-standard bcrypt algorithm</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">5. Third-Party Data Sources</h2>
            <p className="text-gray-700 dark:text-gray-300 mb-4">Regarding LinkedIn data collection through our Chrome Extension:</p>
            <ul className="list-disc pl-6 mb-4 text-gray-700 dark:text-gray-300">
              <li>We only access publicly visible LinkedIn information</li>
              <li>We do not access private LinkedIn messages, connections, or non-public data</li>
              <li>Profile data is collected only through user-initiated actions</li>
              <li>We comply with LinkedIn's terms of service</li>
              <li>You control which profiles to import and can delete them at any time</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">6. Data Sharing and Third Parties</h2>
            <p className="text-gray-700 dark:text-gray-300 mb-4">We may share your information with:</p>
            <ul className="list-disc pl-6 mb-4 text-gray-700 dark:text-gray-300">
              <li><strong>AI Service Providers:</strong> OpenAI (for GPT models) and Anthropic (for Claude models) to power our AI features</li>
              <li><strong>Cloud Infrastructure:</strong> AWS, Railway, and Vercel for hosting and data storage</li>
              <li><strong>Analytics Services:</strong> To understand usage patterns and improve our service</li>
              <li><strong>Legal Requirements:</strong> When required by law or to protect our rights</li>
            </ul>
            <p className="text-gray-700 dark:text-gray-300">
              We do not sell, trade, or rent your personal information to third parties.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">7. Your Rights (GDPR)</h2>
            <p className="text-gray-700 dark:text-gray-300 mb-4">Under the General Data Protection Regulation (GDPR), you have the right to:</p>
            <ul className="list-disc pl-6 mb-4 text-gray-700 dark:text-gray-300">
              <li><strong>Access:</strong> Request a copy of your personal data</li>
              <li><strong>Rectification:</strong> Correct inaccurate or incomplete data</li>
              <li><strong>Erasure:</strong> Request deletion of your personal data</li>
              <li><strong>Portability:</strong> Receive your data in a machine-readable format</li>
              <li><strong>Object:</strong> Object to certain types of processing</li>
              <li><strong>Restrict:</strong> Request limited processing of your data</li>
            </ul>
            <p className="text-gray-700 dark:text-gray-300">
              To exercise these rights, please contact us at promtitude@gmail.com.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">8. Data Security</h2>
            <p className="text-gray-700 dark:text-gray-300 mb-4">
              We implement appropriate technical and organizational measures to protect your data, including:
            </p>
            <ul className="list-disc pl-6 mb-4 text-gray-700 dark:text-gray-300">
              <li>Encryption of data in transit and at rest</li>
              <li>Regular security audits and penetration testing</li>
              <li>Access controls and authentication</li>
              <li>Employee training on data protection</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">9. Data Retention</h2>
            <p className="text-gray-700 dark:text-gray-300 mb-4">
              We retain your personal data only for as long as necessary to fulfill the purposes outlined in this policy:
            </p>
            <ul className="list-disc pl-6 mb-4 text-gray-700 dark:text-gray-300">
              <li>Profile data is retained until you delete it</li>
              <li>Resume data is retained for 2 years after last activity, unless you request earlier deletion</li>
              <li>Account data is retained for 5 years after account closure for legal and compliance purposes</li>
              <li>Authentication tokens expire after 30 days of inactivity</li>
              <li>Chrome Extension import queue data is cleared after successful processing</li>
              <li>Deleted data is permanently removed from our systems within 30 days</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">10. International Data Transfers</h2>
            <p className="text-gray-700 dark:text-gray-300">
              Your information may be transferred to and processed in countries other than your country of residence. We ensure appropriate safeguards are in place to protect your data in accordance with this policy.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">11. Children's Privacy</h2>
            <p className="text-gray-700 dark:text-gray-300">
              Our services are not directed to individuals under 16. We do not knowingly collect personal information from children under 16. If you become aware that a child has provided us with personal information, please contact us.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">12. Changes to This Policy</h2>
            <p className="text-gray-700 dark:text-gray-300">
              We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and updating the "Last updated" date.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">13. Contact Us</h2>
            <p className="text-gray-700 dark:text-gray-300 mb-4">
              If you have questions about this Privacy Policy or our data practices, please contact us:
            </p>
            <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg text-gray-700 dark:text-gray-300">
              <p><strong>Email:</strong> privacy@promtitude.com</p>
              <p><strong>Support:</strong> support@promtitude.com</p>
              <p><strong>Data Protection Officer:</strong> privacy@promtitude.com</p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}