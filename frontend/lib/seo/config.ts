export const seoConfig = {
  defaultTitle: 'Promtitude - AI Recruitment Platform | Natural Language Resume Search',
  titleTemplate: '%s | Promtitude',
  defaultDescription: 'Find perfect candidates 10x faster with AI-powered natural language search. No complex queries needed. Start your free trial today.',
  siteUrl: 'https://promtitude.com',
  siteName: 'Promtitude',
  locale: 'en_US',
  twitter: {
    handle: '@promtitude',
    site: '@promtitude',
    cardType: 'summary_large_image',
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    siteName: 'Promtitude',
  },
  robotsProps: {
    maxImagePreview: 'large',
    maxSnippet: -1,
    maxVideoPreview: -1,
  },
  additionalMetaTags: [
    {
      name: 'viewport',
      content: 'width=device-width, initial-scale=1',
    },
    {
      name: 'apple-mobile-web-app-capable',
      content: 'yes',
    },
    {
      name: 'apple-mobile-web-app-status-bar-style',
      content: 'black-translucent',
    },
    {
      name: 'keywords',
      content: 'AI recruitment, natural language resume search, AI hiring platform, recruitment automation, intelligent candidate search, AI-powered recruiting, resume screening AI, talent acquisition software',
    },
  ],
  additionalLinkTags: [
    {
      rel: 'icon',
      href: '/favicon.svg',
    },
    {
      rel: 'apple-touch-icon',
      href: '/logo-icon.svg',
      sizes: '180x180',
    },
    {
      rel: 'manifest',
      href: '/manifest.json',
    },
  ],
};

export const pageMetadata = {
  home: {
    title: 'AI Recruitment Platform | Natural Language Resume Search',
    description: 'Find perfect candidates 10x faster with AI-powered natural language search. No Boolean queries needed. Try Promtitude free.',
    keywords: 'AI recruitment platform, natural language resume search, AI hiring software, recruitment automation',
  },
  register: {
    title: 'Start Free Trial - AI-Powered Recruiting',
    description: 'Join thousands of recruiters using AI to find better candidates faster. Start your 14-day free trial of Promtitude today.',
    keywords: 'recruitment software free trial, AI recruiting platform trial, hiring software signup',
  },
  login: {
    title: 'Sign In',
    description: 'Access your Promtitude account to continue finding amazing talent with AI-powered search.',
    keywords: 'promtitude login, recruitment platform signin',
  },
  features: {
    title: 'Features - AI Interview Assistant & Smart Search',
    description: 'Discover how Promtitude\'s AI-powered features help you hire better: natural language search, interview assistant, Chrome extension & more.',
    keywords: 'AI recruitment features, interview transcription software, candidate search AI, recruiting chrome extension',
  },
  pricing: {
    title: 'Pricing - Simple, Transparent Plans',
    description: 'Choose the perfect Promtitude plan for your team. All plans include AI-powered search, interview assistant, and Chrome extension.',
    keywords: 'recruitment software pricing, AI hiring platform cost, recruiting tool plans',
  },
  about: {
    title: 'About Us - Building the Future of Recruiting',
    description: 'Learn how Promtitude is revolutionizing recruitment with AI. Our mission is to make hiring faster, fairer, and more human.',
    keywords: 'about promtitude, AI recruitment company, hiring platform story',
  },
  contact: {
    title: 'Contact Us - Get in Touch',
    description: 'Have questions about Promtitude? Our team is here to help you revolutionize your hiring process with AI.',
    keywords: 'contact promtitude, recruitment software support, AI hiring help',
  },
};

export const structuredData = {
  organization: {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'Promtitude',
    url: 'https://promtitude.com',
    logo: 'https://promtitude.com/logo-promtitude.svg',
    sameAs: [
      'https://twitter.com/promtitude',
      'https://linkedin.com/company/promtitude',
    ],
    contactPoint: {
      '@type': 'ContactPoint',
      telephone: '+1-XXX-XXX-XXXX',
      contactType: 'customer service',
      email: 'support@promtitude.com',
      availableLanguage: ['English'],
    },
  },
  softwareApplication: {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: 'Promtitude',
    applicationCategory: 'BusinessApplication',
    operatingSystem: 'Web',
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'USD',
      priceValidUntil: '2025-12-31',
      availability: 'https://schema.org/InStock',
      seller: {
        '@type': 'Organization',
        name: 'Promtitude',
      },
    },
    aggregateRating: {
      '@type': 'AggregateRating',
      ratingValue: '4.8',
      reviewCount: '127',
    },
    featureList: [
      'Natural Language Resume Search',
      'AI Interview Assistant',
      'Real-time Transcription',
      'Chrome Extension for LinkedIn',
      'Automated Candidate Scoring',
      'Team Collaboration Tools',
    ],
  },
  webApplication: {
    '@context': 'https://schema.org',
    '@type': 'WebApplication',
    name: 'Promtitude',
    url: 'https://promtitude.com',
    description: 'AI-powered recruitment platform with natural language search',
    applicationCategory: 'Recruitment Software',
    operatingSystem: 'Any',
    browserRequirements: 'Requires JavaScript. Works best in Chrome, Firefox, Safari, or Edge.',
    permissions: 'microphone (for interview assistant)',
    screenshot: 'https://promtitude.com/screenshots/dashboard.png',
  },
};