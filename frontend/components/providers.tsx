'use client';

import { AuthProvider } from '@/lib/auth/context';
import { ToastProvider } from '@/components/ui/use-toast';
import { RecaptchaProvider } from '@/components/providers/recaptcha-provider';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <RecaptchaProvider>
        <ToastProvider>
          {children}
        </ToastProvider>
      </RecaptchaProvider>
    </AuthProvider>
  );
}