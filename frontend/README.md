# TalentPrompt Frontend

Next.js 14 frontend for the TalentPrompt AI recruitment platform.

## Quick Start

### Local Development

1. Install dependencies:
```bash
npm install
```

2. Copy environment variables:
```bash
cp .env.example .env.local
# Edit .env.local with your configuration
```

3. Run the development server:
```bash
npm run dev
```

Open http://localhost:3000 to view the application.

### Docker Development

Use Docker Compose from the project root:
```bash
docker-compose up frontend
```

## Project Structure

```
frontend/
├── app/               # Next.js App Router pages
├── components/        # React components
│   ├── ui/           # Shadcn/UI components
│   ├── forms/        # Form components
│   └── layouts/      # Layout components
├── lib/              # Utility functions
│   ├── api/          # API client
│   ├── hooks/        # Custom React hooks
│   └── store/        # Redux store
├── public/           # Static assets
└── styles/           # Global styles
```

## Key Features

- Next.js 14 with App Router
- TypeScript for type safety
- Tailwind CSS for styling
- Shadcn/UI component library
- Redux Toolkit for state management
- RTK Query for API calls
- React Hook Form for forms
- Zod for validation

## Available Scripts

```bash
npm run dev        # Start development server
npm run build      # Build for production
npm run start      # Start production server
npm run lint       # Run ESLint
npm run type-check # Run TypeScript compiler
npm run format     # Format code with Prettier
```

## Testing

Run tests:
```bash
npm test
npm run test:coverage  # With coverage
```

## Building for Production

```bash
npm run build
npm start
```

Or with Docker:
```bash
docker build -t talentprompt-frontend .
docker run -p 3000:3000 talentprompt-frontend
```