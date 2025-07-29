# Promtitude Metrics Tracking Guide 📊

## Overview

What gets measured gets managed. This guide outlines the key metrics to track, tools to use, and how to make data-driven decisions as a solo founder.

## 🎯 North Star Metric

**Monthly Recurring Revenue (MRR)**

Why MRR is your North Star:
- Predictable revenue stream
- Clear growth indicator  
- Easy to track and understand
- Directly tied to business health

Formula: 
```
MRR = (# of customers) × (average revenue per customer)
```

## 📈 Key Metrics Framework

### 1. Acquisition Metrics

**Website Visitors → Signups**
- Target: 8% conversion rate
- Track: Daily unique visitors
- Optimize: Landing page copy, CTAs
- Tools: Google Analytics, Hotjar

**Signup → Activation**
- Definition: User completes first search
- Target: 40% within 24 hours
- Track: Time to first search
- Optimize: Onboarding flow

**Traffic Sources Performance**
```
Organic Search: 40% of traffic, 12% conversion
Social Media: 25% of traffic, 6% conversion  
Direct: 20% of traffic, 15% conversion
Referral: 15% of traffic, 18% conversion
```

### 2. Activation Metrics

**Key Activation Events** (in order):
1. Sign up ✓
2. Install Chrome extension
3. Import first resume
4. Complete first search
5. View AI insights
6. Invite team member
7. Use Interview Copilot

**Activation Funnel**:
```
100 signups
├── 70 install extension (70%)
├── 50 import resume (50%)
├── 40 complete search (40%)
├── 25 view insights (25%)
├── 15 invite team (15%)
└── 10 use copilot (10%)
```

### 3. Engagement Metrics

**Daily Active Users (DAU)**
- Definition: Unique users who search per day
- Target: 20% of total users
- Benchmark: Top SaaS is 10-30%

**Weekly Active Users (WAU)**
- Definition: Unique users who search per week
- Target: 60% of total users
- Health indicator: WAU/MAU ratio > 0.6

**Feature Adoption Rates**
```
Natural Language Search: 100% (core feature)
Chrome Extension: 70%
AI Interview Copilot: 30%
Career DNA Matching: 45%
Team Collaboration: 20%
API Usage: 10%
```

### 4. Revenue Metrics

**Monthly Recurring Revenue (MRR)**
```
New MRR: Revenue from new customers
Expansion MRR: Upgrades & additional seats
Contraction MRR: Downgrades
Churned MRR: Cancellations
Net New MRR = New + Expansion - Contraction - Churned
```

**Average Revenue Per User (ARPU)**
```
ARPU = Total MRR / Total Paying Customers
Target ARPU: $45/month
Current tiers impact:
- Pro ($29): 70% of customers
- Team ($99): 25% of customers  
- Enterprise: 5% of customers
```

**Customer Acquisition Cost (CAC)**
```
CAC = Total Sales & Marketing Costs / New Customers
Target: < $50 per customer
Payback period: < 3 months
```

**Lifetime Value (LTV)**
```
LTV = ARPU × Average Customer Lifetime (months)
Target LTV: $540 (12 months × $45)
LTV:CAC Ratio Target: > 3:1
```

### 5. Retention Metrics

**Monthly Churn Rate**
```
Churn = (Customers lost this month / Total customers at start) × 100
Target: < 5% monthly
Benchmark: Good SaaS is 3-7%
```

**Retention Cohorts**
```
Month 1: 85% retained
Month 3: 70% retained
Month 6: 60% retained
Month 12: 50% retained
```

**Net Revenue Retention (NRR)**
```
NRR = (Starting MRR + Expansion - Contraction - Churn) / Starting MRR
Target: > 100% (negative churn)
Current: Track by cohort
```

## 📊 Weekly Metrics Dashboard

### Monday Morning Metrics (30 min review)

**Growth Metrics**
```markdown
## Week of [Date]

### Acquisition
- Website visitors: 1,234 (↑ 12% WoW)
- Signups: 98 (↑ 8% WoW)
- Conversion rate: 7.9% (→ 0% WoW)

### Activation  
- New users activated: 39/98 (39.8%)
- Time to activation: 3.2 hours (↓ 0.5h)
- Extension installs: 68 (69.4%)

### Revenue
- New MRR: $1,421
- Total MRR: $8,234 (↑ 3.2% WoW)
- New customers: 49
- Upgrades: 12
- Churn: 8

### Engagement
- DAU: 234 (18.9% of total)
- WAU: 743 (60.1% of total)
- Searches per user: 12.3/week
```

### Daily Metrics Habits (10 min)

**Morning Check** (5 min):
- MRR changes
- New signups
- Churn alerts
- Support tickets

**Evening Review** (5 min):
- Daily active users
- Feature usage
- Conversion funnel
- Tomorrow's focus

## 🛠️ Tools Setup

### 1. Analytics Stack

**Google Analytics 4** (Free)
- User acquisition
- Behavior flow
- Conversion tracking
- Custom events

Setup checklist:
- [ ] Install GA4 tag
- [ ] Configure conversion events
- [ ] Set up audiences
- [ ] Create custom reports
- [ ] Link to Search Console

**Mixpanel** (Free tier)
- Product analytics
- User journeys
- Cohort analysis
- Feature adoption

Key events to track:
```javascript
// Signup flow
mixpanel.track('Signup Started')
mixpanel.track('Signup Completed', {
  method: 'google|linkedin|email',
  referrer: document.referrer
})

// Activation events
mixpanel.track('Extension Installed')
mixpanel.track('First Resume Imported')
mixpanel.track('First Search Completed', {
  query_type: 'natural_language',
  results_count: 10
})

// Revenue events
mixpanel.track('Trial Started', {
  plan: 'professional'
})
mixpanel.track('Subscription Created', {
  plan: 'professional',
  interval: 'monthly',
  amount: 29
})
```

### 2. Revenue Analytics

**Stripe Dashboard** (Built-in)
- MRR tracking
- Churn analysis
- Payment failures
- Customer segments

**ChartMogul** (Optional)
- Advanced MRR analytics
- Cohort analysis
- LTV calculations
- Churn predictions

### 3. Customer Analytics

**Segment** (Customer Data Platform)
- Unified tracking
- Data warehouse
- Tool integrations
- User profiles

**Amplitude** (Product Analytics)
- User paths
- Retention analysis
- Behavioral cohorts
- Predictive analytics

## 📉 Metrics That Matter vs Vanity Metrics

### Focus On These ✅

**Revenue Metrics**:
- MRR growth rate
- Customer acquisition cost
- Churn rate
- Net revenue retention

**Product Metrics**:
- Activation rate
- Feature adoption
- Time to value
- Support tickets

**Business Health**:
- Runway (months)
- Burn rate
- Unit economics
- Market share

### Ignore These ❌

**Vanity Metrics**:
- Total signups (without activation)
- Page views (without conversion)
- Social media followers
- App store ratings
- Total searches (without outcomes)

## 🎯 OKRs Framework

### Q1 2025 OKRs

**Objective 1: Achieve Product-Market Fit**
- KR1: Reach $10K MRR
- KR2: Get to 100 paying customers
- KR3: Achieve <5% monthly churn
- KR4: NPS score >50

**Objective 2: Build Sustainable Growth Engine**
- KR1: CAC < $50
- KR2: Organic traffic 50% of total
- KR3: Referral rate >0.5
- KR4: Content pieces: 20 published

**Objective 3: Deliver Exceptional Product**
- KR1: <24hr support response
- KR2: 99.9% uptime
- KR3: <2s search response time
- KR4: Mobile app launched

## 📊 Reporting Templates

### Weekly Investor Update

```markdown
# Promtitude Weekly Update - [Date]

## Highlights
- 🎯 MRR: $8,234 (+3.2% WoW)
- 👥 Customers: 183 (+12 this week)
- 📈 Growth rate: 15% MoM
- 💰 Runway: 18 months

## Wins
1. Shipped AI Interview Copilot
2. First enterprise lead ($500/mo)
3. Product Hunt #3 in HR Tech

## Challenges  
1. Churn spike in free tier
2. Chrome extension bug affecting 10% 
3. Support backlog growing

## Next Week
1. Fix extension bug
2. Launch referral program
3. Publish 2 blog posts

## Ask
- Intro to [Company] for partnership
- Feedback on pricing strategy
```

### Monthly Board Report

```markdown
# Promtitude Monthly Report - [Month]

## Executive Summary
[1 paragraph overview]

## Key Metrics
[Dashboard screenshot]

## Progress Against OKRs
[Table with status]

## Financial Performance
- Revenue: $X
- Expenses: $Y  
- Burn: $Z
- Runway: N months

## Product Development
[Features shipped]

## Customer Insights
[Key learnings]

## Next Month Focus
[Top 3 priorities]
```

## 🚨 Alert Thresholds

### Automated Alerts Setup

**Critical Alerts** (Immediate action):
- Churn rate >10% daily
- Site downtime >5 minutes
- Payment failures >5%
- CAC >$100

**Warning Alerts** (Within 24h):
- DAU drops >20%
- Support backlog >24h
- Activation rate <30%
- NPS drops below 40

**Info Alerts** (Weekly review):
- Feature adoption changes
- Traffic source shifts
- Competitor activities
- Market trends

## 📈 Growth Experiments Tracking

### Experiment Template

```markdown
## Experiment: [Name]

**Hypothesis**: If we [change], then [metric] will [increase/decrease] by [X%] because [reasoning]

**Setup**:
- Control: [Current state]
- Variant: [Change]
- Sample size: [N users]
- Duration: [X weeks]

**Success Criteria**: [Specific metric + threshold]

**Results**:
- Control: [X]
- Variant: [Y]  
- Statistical significance: [Yes/No]
- Decision: [Ship/Iterate/Kill]

**Learnings**: [What we learned]
```

### Current Experiments Queue

1. **Onboarding Video**
   - Hypothesis: Video increases activation 20%
   - Status: Running
   - Duration: 2 weeks

2. **Annual Plan Discount**
   - Hypothesis: 25% discount increases LTV
   - Status: Planned
   - Duration: 1 month

3. **Referral Program**
   - Hypothesis: 2-sided incentive drives 30% growth
   - Status: In development
   - Duration: Ongoing

## 💡 Data-Driven Decision Framework

### When to Make Decisions

**Daily Decisions** (Gut + Data):
- Feature priorities
- Bug fixes
- Content topics
- Support responses

**Weekly Decisions** (Mostly Data):
- Marketing spend
- Pricing tests
- Feature launches
- Hiring needs

**Monthly Decisions** (Pure Data):
- Strategy pivots
- Major investments
- Market expansion
- Fundraising

### Decision Log Template

```markdown
**Decision**: [What was decided]
**Date**: [When]
**Data Used**: [Metrics consulted]
**Alternatives**: [Other options]
**Outcome**: [What happened]
**Learning**: [What we learned]
```

---

Remember: **Perfect data tomorrow is worse than good data today.** Start tracking, start learning, start growing.