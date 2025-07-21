'use client';

export default function TestEnvPage() {
  const siteKey = process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY;
  
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Environment Variable Test</h1>
      <div className="space-y-2">
        <p><strong>NEXT_PUBLIC_RECAPTCHA_SITE_KEY:</strong></p>
        <pre className="bg-gray-100 p-4 rounded">
          {JSON.stringify({
            value: siteKey,
            type: typeof siteKey,
            isUndefined: siteKey === undefined,
            isEmptyString: siteKey === '',
            equalsPlaceholder: siteKey === 'your_recaptcha_site_key_here'
          }, null, 2)}
        </pre>
      </div>
    </div>
  );
}