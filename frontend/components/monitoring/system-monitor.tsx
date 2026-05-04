'use client';

import { useEffect } from 'react';
import { useMonitoringStore, ServiceHealth } from '@/stores/monitoringStore';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Activity,
  Database,
  Server,
  Globe,
  Cpu,
  Clock,
  Users,
  MessageSquare,
  Bot,
  BookOpen,
  FileText,
  Workflow,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  RefreshCw,
} from 'lucide-react';

interface StatusBadgeProps {
  status: 'online' | 'offline' | 'degraded';
}

function StatusBadge({ status }: StatusBadgeProps) {
  const config = {
    online: { icon: CheckCircle2, className: 'text-green-500 bg-green-500/10' },
    offline: { icon: XCircle, className: 'text-red-500 bg-red-500/10' },
    degraded: { icon: AlertTriangle, className: 'text-yellow-500 bg-yellow-500/10' },
  };
  
  const { icon: Icon, className } = config[status];
  
  return (
    <Badge variant="outline" className={`gap-1 ${className}`}>
      <Icon className="h-3 w-3" />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </Badge>
  );
}

interface ServiceCardProps {
  service: ServiceHealth;
}

function ServiceCard({ service }: ServiceCardProps) {
  const iconMap: Record<string, typeof Server> = {
    api: Activity,
    database: Database,
    redis: Server,
    chromadb: Database,
    ollama: Cpu,
  };
  
  const Icon = iconMap[service.name] || Server;
  
  return (
    <Card className="relative overflow-hidden">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icon className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-base">{service.name.toUpperCase()}</CardTitle>
          </div>
          <StatusBadge status={service.status} />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 text-sm">
          {service.latency_ms !== undefined && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Latency</span>
              <span className="font-mono">{service.latency_ms.toFixed(2)}ms</span>
            </div>
          )}
          {service.error && (
            <div className="mt-2 p-2 rounded bg-destructive/10 text-destructive text-xs">
              {service.error}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

interface StatCardProps {
  title: string;
  value: number;
  icon: typeof Users;
  description?: string;
}

function StatCard({ title, value, icon: Icon, description }: StatCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value.toLocaleString()}</div>
        {description && (
          <p className="text-xs text-muted-foreground">{description}</p>
        )}
      </CardContent>
    </Card>
  );
}

export function SystemMonitor() {
  const { health, metrics, isLoading, error, lastUpdated, fetchAll } = useMonitoringStore();
  
  useEffect(() => {
    // Initial fetch
    fetchAll();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchAll, 30000);
    
    return () => clearInterval(interval);
  }, [fetchAll]);
  
  const handleRefresh = () => {
    fetchAll();
  };
  
  if (error) {
    return (
      <Card className="border-destructive">
        <CardContent className="flex items-center gap-2 p-4">
          <AlertTriangle className="h-5 w-5 text-destructive" />
          <span className="text-destructive">{error}</span>
          <button
            onClick={handleRefresh}
            className="ml-auto p-2 hover:bg-destructive/10 rounded"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <div className="space-y-6">
      {/* Status Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                System Status
              </CardTitle>
              <CardDescription>
                {lastUpdated && (
                  <span className="flex items-center gap-1 mt-1">
                    <Clock className="h-3 w-3" />
                    Last updated: {lastUpdated.toLocaleTimeString()}
                  </span>
                )}
              </CardDescription>
            </div>
            <button
              onClick={handleRefresh}
              disabled={isLoading}
              className="p-2 hover:bg-accent rounded-md transition-colors"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Overall Status */}
          <div className="flex items-center gap-4 mb-6">
            {health && (
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${
                  health.status === 'healthy' ? 'bg-green-500' :
                  health.status === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'
                }`} />
                <span className="font-medium capitalize">{health.status}</span>
              </div>
            )}
            {health && (
              <div className="text-sm text-muted-foreground">
                Uptime: {formatUptime(health.uptime_seconds)}
              </div>
            )}
          </div>
          
          {/* Services Grid */}
          {health ? (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {Object.entries(health.services).map(([name, service]) => (
                <ServiceCard key={name} service={service} />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-32" />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Statistics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Statistics
          </CardTitle>
          <CardDescription>System usage statistics</CardDescription>
        </CardHeader>
        <CardContent>
          {metrics ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard
                title="Users"
                value={metrics.statistics.users}
                icon={Users}
              />
              <StatCard
                title="Conversations"
                value={metrics.statistics.conversations}
                icon={MessageSquare}
              />
              <StatCard
                title="Agents"
                value={metrics.statistics.agents}
                icon={Bot}
              />
              <StatCard
                title="Knowledge Bases"
                value={metrics.statistics.knowledge_bases}
                icon={BookOpen}
              />
              <StatCard
                title="Documents"
                value={metrics.statistics.documents}
                icon={FileText}
              />
              <StatCard
                title="Workflows"
                value={metrics.statistics.workflows}
                icon={Workflow}
              />
              <StatCard
                title="Executions"
                value={metrics.statistics.workflow_executions}
                icon={Activity}
              />
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[...Array(4)].map((_, i) => (
                <Skeleton key={i} className="h-24" />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Request Metrics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5" />
            Request Metrics
          </CardTitle>
          <CardDescription>API request statistics</CardDescription>
        </CardHeader>
        <CardContent>
          {metrics ? (
            <div className="space-y-6">
              {/* Request Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Total Requests</p>
                  <p className="text-2xl font-bold">{metrics.requests.total.toLocaleString()}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Errors</p>
                  <p className="text-2xl font-bold text-destructive">{metrics.requests.errors.toLocaleString()}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Error Rate</p>
                  <p className="text-2xl font-bold">{metrics.requests.error_rate_percent.toFixed(1)}%</p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Avg Response Time</p>
                  <p className="text-2xl font-bold">{metrics.requests.avg_response_time_ms.toFixed(0)}ms</p>
                </div>
              </div>
              
              {/* Error Rate Progress */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Error Rate</span>
                  <span>{metrics.requests.error_rate_percent.toFixed(1)}%</span>
                </div>
                <Progress
                  value={metrics.requests.error_rate_percent}
                  className="h-2"
                />
              </div>
              
              {/* Requests by Method */}
              <div className="space-y-2">
                <p className="text-sm font-medium">Requests by Method</p>
                <div className="flex gap-4">
                  {Object.entries(metrics.requests.by_method).map(([method, count]) => (
                    <div key={method} className="flex items-center gap-2">
                      <Badge variant="outline">{method}</Badge>
                      <span className="text-sm">{count.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-4 gap-4">
                {[...Array(4)].map((_, i) => (
                  <Skeleton key={i} className="h-16" />
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  if (days > 0) {
    return `${days}d ${hours}h ${minutes}m`;
  } else if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else {
    return `${minutes}m`;
  }
}
