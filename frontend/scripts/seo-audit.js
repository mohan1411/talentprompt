#!/usr/bin/env node

/**
 * SEO Audit Script for Promtitude
 * Run this script to check SEO implementation status
 */

const fs = require('fs');
const path = require('path');

const checks = {
  'robots.txt': {
    path: 'public/robots.txt',
    required: true,
    description: 'Robots.txt file for search engine crawlers'
  },
  'sitemap': {
    path: 'app/sitemap.ts',
    required: true,
    description: 'Dynamic sitemap generation'
  },
  'manifest.json': {
    path: 'public/manifest.json',
    required: true,
    description: 'Web app manifest for PWA support'
  },
  'seo-config': {
    path: 'lib/seo/config.ts',
    required: true,
    description: 'SEO configuration file'
  },
  'og-image': {
    path: 'public/og-image.png',
    required: false,
    description: 'Open Graph image (1200x630px)'
  },
  'twitter-image': {
    path: 'public/twitter-image.png',
    required: false,
    description: 'Twitter Card image (1200x630px)'
  },
  'favicon': {
    path: 'public/favicon.svg',
    required: true,
    description: 'Site favicon'
  }
};

console.log('🔍 Running SEO Audit for Promtitude...\n');

let passCount = 0;
let failCount = 0;
let warnings = [];

// Check each file
Object.entries(checks).forEach(([name, check]) => {
  const filePath = path.join(process.cwd(), check.path);
  const exists = fs.existsSync(filePath);
  
  if (exists) {
    console.log(`✅ ${name}: ${check.description}`);
    passCount++;
  } else if (check.required) {
    console.log(`❌ ${name}: ${check.description} [MISSING - REQUIRED]`);
    failCount++;
  } else {
    console.log(`⚠️  ${name}: ${check.description} [MISSING - RECOMMENDED]`);
    warnings.push(name);
  }
});

console.log('\n📊 SEO Audit Summary:');
console.log(`   Passed: ${passCount}`);
console.log(`   Failed: ${failCount}`);
console.log(`   Warnings: ${warnings.length}`);

// Additional recommendations
console.log('\n💡 SEO Recommendations:');
console.log('   1. Create og-image.png and twitter-image.png (1200x630px)');
console.log('   2. Add Google Search Console verification');
console.log('   3. Submit sitemap to Google Search Console');
console.log('   4. Set up Google Analytics or alternative');
console.log('   5. Monitor Core Web Vitals regularly');
console.log('   6. Create content strategy for blog/resources');
console.log('   7. Build quality backlinks from HR/tech sites');
console.log('   8. Optimize page load speed (<3s target)');

// Check meta descriptions length
console.log('\n📝 Content Guidelines:');
console.log('   - Title tags: 50-60 characters');
console.log('   - Meta descriptions: 150-160 characters');
console.log('   - H1 tags: One per page, include primary keyword');
console.log('   - Alt text: Descriptive text for all images');
console.log('   - URL structure: Clean, keyword-rich URLs');

process.exit(failCount > 0 ? 1 : 0);