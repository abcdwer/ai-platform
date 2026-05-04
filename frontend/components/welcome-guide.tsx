'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuthStore } from '@/stores/authStore';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Check, ChevronRight, Sparkles, MessageSquare, Bot, Database, Workflow } from 'lucide-react';
import { cn } from '@/lib/utils';

interface OnboardingData {
  welcome_message: string;
  checklist: ChecklistItem[];
  is_new_user: boolean;
}

interface ChecklistItem {
  id: string;
  title: string;
  description: string;
  action: string;
  completed: boolean;
}

const QUICK_START_ITEMS = [
  {
    icon: MessageSquare,
    title: 'Start Chatting',
    description: 'Have a conversation with AI',
    href: '/chat',
    color: 'bg-blue-500/10 text-blue-500',
  },
  {
    icon: Bot,
    title: 'Create Agent',
    description: 'Build a custom AI assistant',
    href: '/agents',
    color: 'bg-purple-500/10 text-purple-500',
  },
  {
    icon: Database,
    title: 'Add Knowledge',
    description: 'Upload documents for AI to learn',
    href: '/knowledge',
    color: 'bg-green-500/10 text-green-500',
  },
  {
    icon: Workflow,
    title: 'Try Workflow',
    description: 'Automate complex tasks',
    href: '/workflows',
    color: 'bg-orange-500/10 text-orange-500',
  },
];

export function WelcomeGuide() {
  const { user, isAuthenticated } = useAuthStore();
  const [onboardingData, setOnboardingData] = useState<OnboardingData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    if (isAuthenticated) {
      fetchOnboardingData();
    }
  }, [isAuthenticated]);

  const fetchOnboardingData = async () => {
    try {
      const token = useAuthStore.getState().token;
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/onboarding`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        setOnboardingData(data);
      }
    } catch (error) {
      console.error('Failed to fetch onboarding data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const initializeSamples = async () => {
    try {
      const token = useAuthStore.getState().token;
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/init-samples`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );
      
      if (response.ok) {
        // Refresh onboarding data
        await fetchOnboardingData();
      }
    } catch (error) {
      console.error('Failed to initialize samples:', error);
    }
  };

  if (!isAuthenticated || isLoading || !onboardingData) {
    return null;
  }

  // If user has data, don't show welcome
  if (!onboardingData.is_new_user && currentStep === 0) {
    return null;
  }

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div className="text-center space-y-4">
        <div className="mx-auto w-20 h-20 rounded-3xl bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center shadow-lg shadow-primary/20 animate-in zoom-in duration-500">
          <Sparkles className="w-10 h-10 text-primary-foreground" />
        </div>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Welcome{user?.full_name ? `, ${user.full_name.split(' ')[0]}` : ''}! 👋
          </h1>
          <p className="text-muted-foreground mt-2 text-lg">
            Let's get you started with AI Platform
          </p>
        </div>
      </div>

      {/* Quick Start Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {QUICK_START_ITEMS.map((item, index) => (
          <Link key={item.href} href={item.href}>
            <Card className="group cursor-pointer hover:border-primary/50 transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
              <CardHeader className="pb-3">
                <div className={cn('w-12 h-12 rounded-xl flex items-center justify-center mb-3 group-hover:scale-110 transition-transform', item.color)}>
                  <item.icon className="w-6 h-6" />
                </div>
                <CardTitle className="text-lg group-hover:text-primary transition-colors">
                  {item.title}
                </CardTitle>
                <CardDescription className="text-sm">
                  {item.description}
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-0">
                <Button variant="ghost" className="w-full group-hover:bg-primary/5 group-hover:text-primary">
                  Get Started
                  <ChevronRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                </Button>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* Onboarding Checklist */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Check className="w-5 h-5 text-primary" />
            Your Checklist
          </CardTitle>
          <CardDescription>
            Complete these steps to get the most out of AI Platform
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {onboardingData.checklist.map((item, index) => (
              <div
                key={item.id}
                className={cn(
                  'flex items-center justify-between p-4 rounded-lg border transition-all',
                  item.completed 
                    ? 'bg-primary/5 border-primary/20' 
                    : 'hover:bg-muted/50'
                )}
              >
                <div className="flex items-center gap-4">
                  <div className={cn(
                    'w-8 h-8 rounded-full flex items-center justify-center',
                    item.completed 
                      ? 'bg-primary text-primary-foreground' 
                      : 'bg-muted text-muted-foreground'
                  )}>
                    {item.completed ? (
                      <Check className="w-4 h-4" />
                    ) : (
                      <span className="text-sm font-medium">{index + 1}</span>
                    )}
                  </div>
                  <div>
                    <p className={cn(
                      'font-medium',
                      item.completed && 'text-muted-foreground line-through'
                    )}>
                      {item.title}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {item.description}
                    </p>
                  </div>
                </div>
                <Button variant="ghost" size="sm" asChild>
                  <Link href={item.action}>
                    {item.completed ? 'View' : 'Start'}
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Link>
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Initialize Sample Data Button */}
      {onboardingData.is_new_user && (
        <div className="text-center">
          <p className="text-sm text-muted-foreground mb-4">
            Want to see examples? Initialize sample data to explore features.
          </p>
          <Button onClick={initializeSamples} variant="outline">
            <Sparkles className="w-4 h-4 mr-2" />
            Load Sample Data
          </Button>
        </div>
      )}
    </div>
  );
}
