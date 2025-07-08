import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <Link href="/" className="text-2xl font-bold">
            TalentPrompt
          </Link>
          <nav className="flex gap-4">
            <Link href="/login">
              <Button variant="ghost">Login</Button>
            </Link>
            <Link href="/register">
              <Button>Get Started</Button>
            </Link>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <section className="container mx-auto px-4 py-24 text-center">
          <h1 className="mb-6 text-5xl font-bold tracking-tight">
            Find Perfect Candidates with{' '}
            <span className="text-primary">Natural Language</span>
          </h1>
          <p className="mx-auto mb-8 max-w-2xl text-xl text-muted-foreground">
            Simply describe what you&apos;re looking for in plain English, and our AI-powered system
            will instantly surface the most relevant matches from your talent pool.
          </p>
          <div className="flex justify-center gap-4">
            <Link href="/register">
              <Button size="lg">Start Free Trial</Button>
            </Link>
            <Link href="/demo">
              <Button size="lg" variant="outline">
                Watch Demo
              </Button>
            </Link>
          </div>
        </section>

        <section className="border-t bg-secondary/20 py-24">
          <div className="container mx-auto px-4">
            <h2 className="mb-12 text-center text-3xl font-bold">How It Works</h2>
            <div className="grid gap-8 md:grid-cols-3">
              <div className="text-center">
                <div className="mb-4 text-4xl">🔍</div>
                <h3 className="mb-2 text-xl font-semibold">Natural Language Search</h3>
                <p className="text-muted-foreground">
                  &quot;Find me a senior Python developer with AWS experience and leadership skills&quot;
                </p>
              </div>
              <div className="text-center">
                <div className="mb-4 text-4xl">🤖</div>
                <h3 className="mb-2 text-xl font-semibold">AI-Powered Matching</h3>
                <p className="text-muted-foreground">
                  Advanced semantic understanding using state-of-the-art AI models
                </p>
              </div>
              <div className="text-center">
                <div className="mb-4 text-4xl">⚡</div>
                <h3 className="mb-2 text-xl font-semibold">Instant Results</h3>
                <p className="text-muted-foreground">
                  Sub-second search across millions of resumes with smart ranking
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t py-8">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          © 2025 TalentPrompt. All rights reserved.
        </div>
      </footer>
    </div>
  );
}