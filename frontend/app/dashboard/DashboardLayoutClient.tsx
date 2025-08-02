'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth/context';
import { ModernSidebar } from '@/components/dashboard/ModernSidebar';
import { MobileBottomNav } from '@/components/dashboard/MobileBottomNav';
import { CommandPalette } from '@/components/ui/command-palette';
import { cn } from '@/lib/utils';

export default function DashboardLayoutClient({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [sidebarWidth, setSidebarWidth] = useState(256);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [user, isLoading, router]);

  // Listen for sidebar width changes
  useEffect(() => {
    const checkSidebarWidth = () => {
      const savedState = localStorage.getItem('sidebar-collapsed');
      const isCollapsed = savedState ? JSON.parse(savedState) : false;
      setSidebarWidth(isCollapsed ? 80 : 256);
    };

    checkSidebarWidth();
    
    // Listen for storage changes
    window.addEventListener('storage', checkSidebarWidth);
    
    // Also check on focus (in case localStorage changed in another tab)
    window.addEventListener('focus', checkSidebarWidth);
    
    // Custom event for immediate updates
    window.addEventListener('sidebar-toggle', checkSidebarWidth);

    return () => {
      window.removeEventListener('storage', checkSidebarWidth);
      window.removeEventListener('focus', checkSidebarWidth);
      window.removeEventListener('sidebar-toggle', checkSidebarWidth);
    };
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
        <div className="relative">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          <div className="absolute inset-0 rounded-full h-12 w-12 border-b-2 border-primary/30 animate-ping"></div>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-gray-50 to-gray-100 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800">
      <ModernSidebar />
      <MobileBottomNav />
      <CommandPalette />
      
      {/* Main content with dynamic padding */}
      <div 
        className={cn(
          "transition-all duration-300 ease-in-out",
          "lg:pl-64",
          "pb-16 lg:pb-0" // Add padding bottom for mobile bottom nav
        )}
        style={{
          paddingLeft: typeof window !== 'undefined' && window.innerWidth >= 1024 ? `${sidebarWidth}px` : undefined
        }}
      >
        <main className="min-h-screen">
          <div className="px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}