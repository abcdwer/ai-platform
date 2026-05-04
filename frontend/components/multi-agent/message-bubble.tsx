'use client';

import { MEMBER_ROLE_COLORS, AgentMessage } from '@/types/multi-agent';
import type { AgentMember } from '@/types/multi-agent';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface MessageBubbleProps {
  message: AgentMessage;
  members: AgentMember[];
}

export function MessageBubble({ message, members }: MessageBubbleProps) {
  const member = message.member_id 
    ? members.find((m) => m.id === message.member_id)
    : null;
  
  const color = message.member_color || member?.color || (member ? MEMBER_ROLE_COLORS[member.role] : '#6b7280');
  
  const isUser = message.message_type === 'user_input';
  const isSystem = message.message_type === 'system';
  
  if (isSystem) {
    return (
      <div className="flex justify-center">
        <Badge variant="secondary" className="text-xs">
          {message.content}
        </Badge>
      </div>
    );
  }
  
  return (
    <div className={cn("flex gap-3", isUser && "flex-row-reverse")}>
      {/* Avatar */}
      <div 
        className="w-10 h-10 rounded-full flex items-center justify-center text-white font-medium text-sm flex-shrink-0"
        style={{ backgroundColor: isUser ? '#6b7280' : color }}
      >
        {isUser ? (
          'U'
        ) : (
          <span>
            {message.member_name?.charAt(0).toUpperCase() || 'A'}
          </span>
        )}
      </div>
      
      {/* Content */}
      <div className={cn("flex-1 max-w-[80%]", isUser && "flex flex-col items-end")}>
        <div className="flex items-center gap-2 mb-1">
          <span className="font-medium text-sm">
            {isUser ? 'You' : message.member_name || 'Agent'}
          </span>
          {!isUser && member && (
            <Badge 
              variant="outline" 
              className="text-xs"
              style={{ 
                borderColor: color + '60',
                color: color,
              }}
            >
              {member.role}
            </Badge>
          )}
          <span className="text-xs text-muted-foreground">
            Turn {message.turn + 1}
            {message.iteration > 0 && ` (iter ${message.iteration + 1})`}
          </span>
        </div>
        
        <Card className={cn(
          "border-l-4",
          isUser ? "bg-muted border-l-gray-500" : ""
        )}>
          <CardContent className="p-3">
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <p className="whitespace-pre-wrap">{message.content}</p>
            </div>
            
            {/* Metadata */}
            {(message.model_used || message.tokens_used || message.execution_time_ms) && (
              <div className="flex gap-3 mt-2 pt-2 border-t text-xs text-muted-foreground">
                {message.model_used && (
                  <span>Model: {message.model_used}</span>
                )}
                {message.tokens_used && (
                  <span>Tokens: {message.tokens_used}</span>
                )}
                {message.execution_time_ms && (
                  <span>{Math.round(message.execution_time_ms / 1000)}s</span>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
