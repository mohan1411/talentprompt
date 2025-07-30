# Promtitude Pricing Analysis & Strategy

## Executive Summary

This document provides a comprehensive cost analysis and pricing strategy for Promtitude, focusing on the economics of processing 100 resumes as a baseline metric.

---

## 1. Cost Breakdown for Processing 100 Resumes

### 1.1 AI/API Costs (Variable Costs)

#### Resume Import & Processing
- **OpenAI Embeddings (text-embedding-ada-002)**
  - Cost: $0.0001 per 1K tokens
  - Average resume: ~2,000 tokens
  - Cost per resume: $0.0002
  - **100 resumes: $0.02**

#### Search Operations (Per Query)
- **AI Typo Correction (GPT-4-turbo)**
  - Tokens: ~200 per query
  - Cost: ~$0.002 per search

- **Query Analysis (GPT-4.1-mini)**
  - Tokens: ~500 per query
  - Cost: ~$0.005 per search

- **Query Embedding**
  - Cost: ~$0.0001 per search

- **Result Enhancement (Top 10 candidates)**
  - Tokens: ~400 per candidate
  - Cost: ~$0.004 per candidate
  - Total: ~$0.04 per search

- **Total cost per AI-enhanced search: ~$0.06**

#### Additional AI Features
- **AI Interview Copilot**
  - Cost: $0.50-$1.00 per 30-minute interview
  - Includes: Real-time transcription + GPT-4 analysis

- **Personalized Outreach**
  - Cost: ~$0.01 per message
  - Includes: Profile analysis + message generation

- **Comparative Analysis**
  - Cost: ~$0.10 for comparing 5 candidates

### 1.2 Infrastructure Costs (Fixed Costs)

#### Monthly Infrastructure Breakdown

| Component | Minimal Setup | Standard Setup | Enterprise Setup |
|-----------|--------------|----------------|------------------|
| **Backend API Server** | $10 | $30 | $100 |
| **Frontend (Next.js)** | $0 (Vercel free) | $20 | $20 |
| **PostgreSQL Database** | $0 (free tier) | $25 | $50 |
| **Qdrant Vector DB** | $0 (self-hosted) | $25 | $100 |
| **Redis Cache** | $0 (free tier) | $10 | $30 |
| **Object Storage** | $1 | $5 | $20 |
| **Total Infrastructure** | $11/month | $115/month | $320/month |

### 1.3 Total Cost Analysis

#### For 100 Resumes (Standard Setup)

**One-time costs:**
- Resume import & embedding: $0.02
- Initial storage: $0.01

**Monthly operational costs:**
- Infrastructure: $115.00
- 50 searches: $3.00
- 100 outreach messages: $1.00
- 10 AI interviews: $7.50
- **Total monthly: $126.53**

**Cost per resume per month: $1.27**

---

## 2. Recommended Pricing Strategy

### 2.1 Pricing Philosophy

1. **Value-based pricing**: Price based on value delivered, not just costs
2. **Market positioning**: Premium-affordable (below enterprise, above basic tools)
3. **Target margin**: 70-80% gross margin for SaaS sustainability

### 2.2 Pricing Tiers

#### Starter Plan - $199/month
- **Includes:**
  - 100 resume imports/month
  - 50 AI-powered searches
  - 100 personalized outreach messages
  - Basic analytics dashboard
  - Email support
- **Gross margin**: 36%
- **Target**: Individual recruiters, freelancers

#### Professional Plan - $499/month ⭐ RECOMMENDED
- **Includes:**
  - 500 resume imports/month
  - 200 AI-powered searches
  - 500 personalized outreach messages
  - 10 AI Interview Copilot sessions
  - Advanced analytics & insights
  - Career DNA analysis
  - Priority support
- **Gross margin**: 74%
- **Target**: Growing agencies, in-house recruiting teams

#### Enterprise Plan - $999/month
- **Includes:**
  - 2,000 resume imports/month
  - Unlimited AI searches
  - Unlimited outreach
  - Unlimited AI interviews
  - API access
  - Custom integrations
  - Dedicated success manager
  - SLA guarantee
- **Gross margin**: 87%
- **Target**: Large agencies, enterprise HR departments

### 2.3 Cost vs. Price Analysis (100 Resumes)

| Metric | Your Cost | Customer Price | Margin |
|--------|-----------|----------------|---------|
| Starter Plan | $126.53 | $199 | 36% |
| Professional Plan | $126.53 | $499 | 74% |
| Enterprise Plan | $126.53 | $999 | 87% |

---

## 3. ROI Justification for Customers

### 3.1 Time Savings Calculation

**Traditional Process:**
- Manual resume screening: 15 minutes/resume
- 100 resumes = 25 hours
- Cost at $100/hour: $2,500

**With Promtitude:**
- AI-enhanced screening: 5 minutes/resume
- 100 resumes = 8.3 hours
- Cost at $100/hour: $830
- **Time saved: 16.7 hours ($1,670 value)**

### 3.2 Quality Improvements

- **Better candidate matches**: Reduces bad hires by 50%
- **Cost of one bad hire**: $15,000-$30,000
- **Risk reduction value**: $7,500-$15,000 annually

### 3.3 Total ROI for Customer

**Monthly Investment**: $499 (Professional Plan)
**Monthly Value Delivered**:
- Time savings: $1,670
- Risk reduction: $625 (annualized)
- Efficiency gains: $500
- **Total value: $2,795**

**ROI: 460% monthly return**

---

## 4. Competitive Analysis

| Feature | LinkedIn Recruiter | SeekOut | HireEZ | Promtitude |
|---------|-------------------|---------|---------|------------|
| **Price/month** | $825 | $1,000+ | $800+ | $499 |
| **Natural Language Search** | ❌ | Limited | Limited | ✅ Full AI |
| **AI Interview Assistant** | ❌ | ❌ | ❌ | ✅ |
| **Typo Correction** | ❌ | ❌ | ❌ | ✅ |
| **Progressive Search** | ❌ | ❌ | ❌ | ✅ |
| **Career DNA Analysis** | ❌ | ❌ | ❌ | ✅ |

**Promtitude Advantage**: 40% cheaper with more AI features

---

## 5. Alternative Pricing Models

### 5.1 Usage-Based Pricing
```
Resume import: $0.50 each
AI search: $1.00 each
Outreach message: $0.50 each
AI interview: $10.00 each

Example: 100 resumes + 50 searches + 100 messages = $150
```

### 5.2 Credits System
```
1 credit = $1.00
- Resume import: 0.5 credits
- AI search: 1 credit
- Outreach: 0.5 credits
- AI interview: 10 credits

Bulk discounts:
- 100 credits: $90 (10% off)
- 500 credits: $400 (20% off)
- 1000 credits: $700 (30% off)
```

### 5.3 Success-Based Pricing
```
Base fee: $99/month
Per successful hire: $500
Unlimited usage within reason
```

---

## 6. Pricing Implementation Strategy

### 6.1 Launch Strategy
1. **Free Trial**: 14 days with 20 resume imports
2. **Early Bird Discount**: 50% off for first 100 customers
3. **Annual Discount**: 20% off for annual prepayment

### 6.2 Psychological Pricing Tactics
1. **Anchor with Enterprise**: Show $999 first to make $499 seem reasonable
2. **Value Stacking**: List features worth "$2,000/month"
3. **Social Proof**: "Join 500+ recruiters saving 17 hours/week"
4. **Urgency**: "Prices increase January 1st"

### 6.3 Upsell Opportunities
- Additional resume imports: $0.30 each
- Extra AI interviews: $8 each
- Custom AI training: $500 one-time
- White-label option: $2,000/month

---

## 7. Financial Projections

### 7.1 Break-Even Analysis
- **Fixed costs**: $115/month (infrastructure)
- **Break-even**: 1 Professional customer or 3 Starter customers
- **Target**: 100 customers in Year 1

### 7.2 Revenue Projections (Year 1)
```
Month 1-3: 10 customers avg × $499 = $4,990/month
Month 4-6: 25 customers avg × $499 = $12,475/month
Month 7-9: 50 customers avg × $499 = $24,950/month
Month 10-12: 100 customers avg × $499 = $49,900/month

Year 1 Total Revenue: ~$276,945
Year 1 Gross Profit: ~$204,940 (74% margin)
```

---

## 8. Key Takeaways

1. **Optimal price point**: $499/month for 500 resumes provides best value/margin balance
2. **Cost per 100 resumes**: $126.53 (including all infrastructure)
3. **Recommended margin**: 74% allows for growth and R&D investment
4. **Customer ROI**: 460% monthly return justifies premium pricing
5. **Market position**: 40% below competitors with superior features

---

## 9. Pricing Decision Matrix

| If Customer Needs | Recommend | Price | Why |
|------------------|-----------|-------|-----|
| < 50 resumes/month | Starter | $199 | Entry-level pricing |
| 100-500 resumes/month | Professional | $499 | Best value |
| > 500 resumes/month | Enterprise | $999 | Volume efficiency |
| Pay-per-use | Credits | Variable | Flexibility |
| Risk mitigation | Success-based | $99 + $500/hire | Aligned incentives |

---

*Last Updated: December 2024*
*Next Review: Q1 2025*