'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { Sidebar } from '@/components/sidebar';
import { ModeToggle } from '@/components/mode-toggle';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  MessageSquare,
  BookOpen,
  Workflow as WorkflowIcon,
  Bot,
  Sparkles,
  Puzzle,
  ArrowRight,
  CheckCircle2,
  XCircle,
  Loader2,
  Zap,
  Shield,
  Globe,
  Cpu,
  Clock,
  FileText,
  Users,
  Layers,
  Settings,
} from 'lucide-react';
import { useChatStore, useKnowledgeStore, useWorkflowStore, useMultiAgentStore, useFinetuneStore, useMCPStore } from '@/stores';
import { useAuthStore } from '@/stores/authStore';
import { WelcomeGuide } from '@/components/welcome-guide';

// Module card interface
interface ModuleCardProps {
  title: string;
  description: string;
  href: string;
  icon: React.ElementType;
  color: string;
  stats?: { label: string; value: string | number };
  isLoading?: boolean;
}

function cn(...classes: (string | undefined | null | false)[]) {
  return classes.filter(Boolean).join(' ');
}

// Module Card Component
function ModuleCard({ title, description, href, icon: Icon, color, stats, isLoading }: ModuleCardProps) {
  return (
    <Link href={href}>
      <Card className="hover:border-primary/50 hover:shadow-lg transition-all duration-300 cursor-pointer h-full group">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className={cn('w-12 h-12 rounded-xl flex items-center justify-center mb-3 transition-transform group-hover:scale-110', color)}>
              <Icon className="h-6 w-6" />
            </div>
            <ArrowRight className="h-5 w-5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
          <CardTitle className="text-lg">{title}</CardTitle>
          <CardDescription className="text-sm">{description}</CardDescription>
        </CardHeader>
        <CardContent>
          {stats && (
            <div className="flex items-center gap-2 text-sm">
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              ) : (
                <>
                  <span className="font-medium">{stats.value}</span>
                  <span className="text-muted-foreground">{stats.label}</span>
                </>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}

// Status Indicator Component
function StatusIndicator({ status, label }: { status: 'online' | 'offline' | 'degraded'; label: string }) {
  const statusConfig = {
    online: { icon: CheckCircle2, color: 'text-green-500', text: 'Online' },
    offline: { icon: XCircle, color: 'text-red-500', text: 'Offline' },
    degraded: { icon: Loader2, color: 'text-yellow-500', text: 'Degraded' },
  };
  
  const config = statusConfig[status];
  
  return (
    <div className="flex items-center gap-2">
      <config.icon className={cn('h-4 w-4', config.color, status === 'degraded' && 'animate-spin')} />
      <span className="text-sm">{label}: {config.text}</span>
    </div>
  );
}

// Quick Start Step Component
function QuickStartStep({ number, title, description }: { number: number; title: string; description: string }) {
  return (
    <div className="flex gap-4">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-semibold text-sm">
        {number}
      </div>
      <div>
        <h4 className="font-medium text-sm">{title}</h4>
        <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { isAuthenticated } = useAuthStore();
  const [isLoading, setIsLoading] = useState(true);
  const [moduleStats, setModuleStats] = useState({
    chat: { conversations: 0 },
    knowledge: { bases: 0 },
    workflow: { workflows: 0 },
    multiAgent: { agents: 0 },
    finetune: { models: 0 },
    mcp: { servers: 0 },
  });
  
  const [systemStatus, setSystemStatus] = useState({
    api: 'online' as 'online' | 'offline' | 'degraded',
    chat: 'online' as 'online' | 'offline' | 'degraded',
    knowledge: 'online' as 'online' | 'offline' | 'degraded',
    workflow: 'online' as 'online' | 'offline' | 'degraded',
    mcp: 'online' as 'online' | 'offline' | 'degraded',
  });

  // Store hooks
  const { conversations, loadConversations } = useChatStore();
  const { knowledgeBases, loadKnowledgeBases } = useKnowledgeStore();
  const { workflows, loadWorkflows } = useWorkflowStore();
  const { agents, loadAgents } = useMultiAgentStore();
  const { models: finetuneModels, loadModels } = useFinetuneStore();
  const { servers: mcpServers, loadServers } = useMCPStore();

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      try {
        await Promise.allSettled([
          loadConversations(),
          loadKnowledgeBases(),
          loadWorkflows(),
          loadAgents(),
          loadModels(),
          loadServers(),
        ]);
      } catch (error) {
        console.error('Failed to load some data:', error);
      }
      setIsLoading(false);
    };
    
    loadData();
  }, []);

  // Update stats when data changes
  useEffect(() => {
    setModuleStats({
      chat: { conversations: conversations.length },
      knowledge: { bases: knowledgeBases.length },
      workflow: { workflows: workflows.length },
      multiAgent: { agents: agents.filter(a => a.is_active).length },
      finetune: { models: finetuneModels.length },
      mcp: { servers: mcpServers.length },
    });
  }, [conversations, knowledgeBases, workflows, agents, finetuneModels, mcpServers]);

  // 6大模块配置
  const modules = [
    {
      title: '对话聊天',
      titleEn: 'Chat',
      description: '与 AI 进行自然语言对话，支持多模型切换',
      href: '/chat',
      icon: MessageSquare,
      color: 'bg-blue-500/10 text-blue-600 dark:bg-blue-500/20',
      stats: { label: '会话', value: moduleStats.chat.conversations },
    },
    {
      title: '知识库',
      titleEn: 'Knowledge',
      description: '构建私有知识库，支持 RAG 检索增强',
      href: '/knowledge',
      icon: BookOpen,
      color: 'bg-emerald-500/10 text-emerald-600 dark:bg-emerald-500/20',
      stats: { label: '知识库', value: moduleStats.knowledge.bases },
    },
    {
      title: '工作流',
      titleEn: 'Workflow',
      description: '可视化编排 AI 工作流，自动化任务',
      href: '/workflows',
      icon: WorkflowIcon,
      color: 'bg-orange-500/10 text-orange-600 dark:bg-orange-500/20',
      stats: { label: '工作流', value: moduleStats.workflow.workflows },
    },
    {
      title: '多智能体',
      titleEn: 'Multi-Agent',
      description: '创建多个 AI 智能体协同工作',
      href: '/multi-agent',
      icon: Users,
      color: 'bg-purple-500/10 text-purple-600 dark:bg-purple-500/20',
      stats: { label: '活跃智能体', value: moduleStats.multiAgent.agents },
    },
    {
      title: 'LoRA 微调',
      titleEn: 'Finetune',
      description: '使用 LoRA 技术微调私有模型',
      href: '/finetune/models',
      icon: Sparkles,
      color: 'bg-pink-500/10 text-pink-600 dark:bg-pink-500/20',
      stats: { label: '微调模型', value: moduleStats.finetune.models },
    },
    {
      title: 'MCP 接口',
      titleEn: 'MCP',
      description: '管理 MCP 服务器，扩展 AI 工具能力',
      href: '/mcp/servers',
      icon: Puzzle,
      color: 'bg-cyan-500/10 text-cyan-600 dark:bg-cyan-500/20',
      stats: { label: 'MCP 服务', value: moduleStats.mcp.servers },
    },
  ];

  const quickStartSteps = [
    { title: '开始对话', description: '在聊天模块与 AI 开始对话' },
    { title: '创建知识库', description: '上传文档构建私有知识库' },
    { title: '设计工作流', description: '编排自动化 AI 工作流' },
    { title: '探索更多', description: '尝试多智能体和 LoRA 微调' },
  ];

  const usefulLinks = [
    { title: '文档中心', href: '/settings', icon: FileText },
    { title: '系统设置', href: '/settings', icon: Settings },
    { title: '模型管理', href: '/models', icon: Cpu },
  ];

  return (
    <div className="flex h-screen">
      <Sidebar />
      
      <main className="flex-1 overflow-y-auto">
        {/* Header */}
        <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-10">
          <div className="container mx-auto px-6 py-4 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">AI Platform</h1>
              <p className="text-muted-foreground text-sm">智能协作平台 · 全模块入口</p>
            </div>
            <div className="flex items-center gap-4">
              <ModeToggle />
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="container mx-auto px-6 py-8 space-y-10">
          {/* Welcome Guide for authenticated users */}
          {isAuthenticated && <WelcomeGuide />}

          {/* Hero Section */}
          <section className="text-center py-8">
            <h2 className="text-3xl font-bold mb-3">欢迎使用 AI Platform</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              统一的 AI 协作平台，集成对话、知识库、工作流、多智能体、LoRA 微调、MCP 接口等核心功能
            </p>
          </section>

          {/* Module Cards */}
          <section>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold">模块中心</h2>
                <p className="text-sm text-muted-foreground">选择您需要的功能模块</p>
              </div>
              <Badge variant="outline" className="text-xs">
                {modules.length} 模块
              </Badge>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {modules.map((module) => (
                <ModuleCard
                  key={module.href}
                  title={module.title}
                  description={module.description}
                  href={module.href}
                  icon={module.icon}
                  color={module.color}
                  stats={module.stats}
                  isLoading={isLoading}
                />
              ))}
            </div>
          </section>

          {/* System Status */}
          <section>
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Cpu className="h-5 w-5" />
              服务状态
            </h2>
            <Card>
              <CardContent className="pt-6">
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <StatusIndicator status={systemStatus.api} label="API 服务" />
                  <StatusIndicator status={systemStatus.chat} label="对话服务" />
                  <StatusIndicator status={systemStatus.knowledge} label="知识库" />
                  <StatusIndicator status={systemStatus.workflow} label="工作流" />
                  <StatusIndicator status={systemStatus.mcp} label="MCP" />
                </div>
              </CardContent>
            </Card>
          </section>

          {/* Quick Start & Useful Links */}
          <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Quick Start */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5 text-primary" />
                  快速开始
                </CardTitle>
                <CardDescription>新用户友好的入门指南</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {quickStartSteps.map((step, index) => (
                    <QuickStartStep
                      key={index}
                      number={index + 1}
                      title={step.title}
                      description={step.description}
                    />
                  ))}
                </div>
                <div className="mt-6 pt-4 border-t">
                  <Link href="/chat">
                    <Button className="w-full gap-2">
                      <MessageSquare className="h-4 w-4" />
                      开始对话
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>

            {/* Useful Links */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Globe className="h-5 w-5 text-primary" />
                  常用入口
                </CardTitle>
                <CardDescription>快速访问系统功能</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 gap-3">
                  {usefulLinks.map((link) => (
                    <Link key={link.href} href={link.href}>
                      <div className="flex items-center justify-between p-3 rounded-lg hover:bg-muted transition-colors cursor-pointer group">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center">
                            <link.icon className="h-4 w-4 text-muted-foreground" />
                          </div>
                          <span className="text-sm font-medium">{link.title}</span>
                        </div>
                        <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                    </Link>
                  ))}
                </div>
              </CardContent>
            </Card>
          </section>

          {/* Features Overview */}
          <section>
            <h2 className="text-xl font-semibold mb-4">平台特性</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <Shield className="h-8 w-8 text-primary mb-2" />
                  <CardTitle className="text-base">安全可靠</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">私有化部署，数据完全可控</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <Globe className="h-8 w-8 text-primary mb-2" />
                  <CardTitle className="text-base">多模型支持</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">支持 Ollama、OpenAI 等多种模型</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <Layers className="h-8 w-8 text-primary mb-2" />
                  <CardTitle className="text-base">模块化设计</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">各模块独立又可协同工作</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <Zap className="h-8 w-8 text-primary mb-2" />
                  <CardTitle className="text-base">高性能</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">流式响应，低延迟体验</p>
                </CardContent>
              </Card>
            </div>
          </section>

          {/* Footer */}
          <footer className="border-t pt-8 text-center text-sm text-muted-foreground">
            <p>AI Platform · 全栈智能协作平台</p>
            <p className="mt-1 text-xs">Powered by FastAPI + Next.js</p>
          </footer>
        </div>
      </main>
    </div>
  );
}
