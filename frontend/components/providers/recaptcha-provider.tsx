'use client';

import { GoogleReCaptchaProvider } from 'react-google-recaptcha-v3';

interface RecaptchaProviderProps {
  children: React.ReactNode;
}

export function RecaptchaProvider({ children }: RecaptchaProviderProps) {
  const siteKey = process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY;

  // If no site key is configured, just return children without reCAPTCHA
  if (!siteKey || siteKey === 'your_recaptcha_site_key_here') {
    console.warn('reCAPTCHA site key not configured. CAPTCHA protection disabled.');
    return <>{children}</>;
  }

  return (
    <GoogleReCaptchaProvider
      reCaptchaKey={siteKey}
      scriptProps={{
        async: true,
        defer: true,
        appendTo: 'body',
      }}
      container={{
        parameters: {
          badge: 'bottomright',
          theme: 'dark',
        },
      }}
    >
      {children}
    </GoogleReCaptchaProvider>
  );
}