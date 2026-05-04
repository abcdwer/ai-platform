import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { ThemeProvider } from '@/components/theme-provider';
import { Toaster } from '@/components/ui/toaster';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'AI Platform - Unified Interface for AI Models',
  description: 'Chat with AI, create agents, and manage models in one unified platform. Supports Ollama, OpenAI, and more.',
  keywords: ['AI', 'Chat', 'Agents', 'LLM', 'Ollama', 'OpenAI', 'Machine Learning'],
  authors: [{ name: 'AI Platform Team' }],
  icons: {
    icon: '/favicon.ico',
  },
};

// Script to prevent theme flash
const themeScript = `
  (function() {
    const theme = localStorage.getItem('ai-platform-theme') || 'system';
    const resolved = theme === 'system' 
      ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
      : theme;
    document.documentElement.classList.add(resolved);
  })();
`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  );
}
