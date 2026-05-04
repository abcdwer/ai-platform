'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useMultiAgentStore } from '@/stores/multiAgentStore';
import { MODE_DESCRIPTIONS, MEMBER_ROLE_COLORS, AgentMessage } from '@/types/multi-agent';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { MessageBubble } from '@/components/multi-agent/message-bubble';
import { MemberAvatar } from '@/components/multi-agent/member-avatar';
import { 
  ArrowLeft, 
  Send, 
  Square, 
  Pause, 
  Play,
  RefreshCw,
  Users,
  Loader2,
} from 'lucide-react';

export default function SessionPage() {
  const params = useParams();
  const router = useRouter();
  const groupId = params.id as string;
  
  const {
    groups,
    currentGroup,
    setCurrentGroup,
    loadGroups,
    currentSession,
    setCurrentSession,
    messages,
    isExecuting,
    executionError,
    executeSession,
    stopSession,
    pauseSession,
    resumeSession,
    clearMessages,
  } = useMultiAgentStore();
  
  const [userInput, setUserInput] = useState('');
  const [isLoadingGroup, setIsLoadingGroup] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Load group
  useEffect(() => {
    const load = async () => {
      if (groups.length === 0) {
        await loadGroups();
      }
      setIsLoadingGroup(false);
    };
    load();
  }, [groups.length, loadGroups]);
  
  useEffect(() => {
    const group = groups.find((g) => g.id === groupId);
    if (group) {
      setCurrentGroup(group);
      clearMessages();
    }
  }, [groupId, groups, setCurrentGroup, clearMessages]);
  
  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userInput.trim() || isExecuting) return;
    
    const input = userInput;
    setUserInput('');
    
    // Add user message to UI immediately
    const userMessage: AgentMessage = {
      id: `temp-${Date.now()}`,
      session_id: '',
      member_id: undefined,
      member_name: undefined,
      message_type: 'user_input',
      content: input,
      turn: 0,
      iteration: 0,
      created_at: new Date().toISOString(),
    };
    
    // Optimistically add user message
    useMultiAgentStore.setState((state) => ({
      messages: [...state.messages, userMessage],
    }));
    
    // Execute session
    const result = await executeSession(groupId, {
      user_input: input,
      continue_session: true,
    });
    
    if (result) {
      setCurrentSession({
        id: result.session_id,
        group_id: groupId,
        user_id: '',
        status: result.status,
        initial_input: input,
        current_turn: result.current_turn,
        completed_iterations: 0,
        created_at: new Date().toISOString(),
        messages: result.messages,
      });
    }
  };
  
  const handleStop = async () => {
    if (currentSession) {
      await stopSession(currentSession.id);
    }
  };
  
  const handlePause = async () => {
    if (currentSession) {
      await pauseSession(currentSession.id);
    }
  };
  
  const handleResume = async () => {
    if (currentSession) {
      await resumeSession(currentSession.id);
    }
  };
  
  const handleNewSession = () => {
    setCurrentSession(null);
    clearMessages();
  };
  
  if (isLoadingGroup) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }
  
  if (!currentGroup) {
    return (
      <div className="container mx-auto py-8">
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Users className="w-16 h-16 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">Group not found</h3>
            <Button onClick={() => router.push('/multi-agent')}>
              Back to Groups
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }
  
  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* Header */}
      <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex items-center justify-between py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => router.push('/multi-agent')}>
              <ArrowLeft className="w-4 h-4" />
            </Button>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold">{currentGroup.name}</h1>
                <Badge variant="outline" className="text-xs">
                  {MODE_DESCRIPTIONS[currentGroup.mode]?.icon} {MODE_DESCRIPTIONS[currentGroup.mode]?.title}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">
                {currentGroup.members?.length || 0} agents participating
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {isExecuting && (
              <>
                <Button variant="outline" size="sm" onClick={handleStop}>
                  <Square className="w-4 h-4 mr-2" />
                  Stop
                </Button>
                <Button variant="outline" size="sm" onClick={handlePause}>
                  <Pause className="w-4 h-4 mr-2" />
                  Pause
                </Button>
              </>
            )}
            {!isExecuting && currentSession?.status === 'paused' && (
              <Button variant="outline" size="sm" onClick={handleResume}>
                <Play className="w-4 h-4 mr-2" />
                Resume
              </Button>
            )}
            <Button variant="outline" size="sm" onClick={handleNewSession}>
              <RefreshCw className="w-4 h-4 mr-2" />
              New Session
            </Button>
          </div>
        </div>
      </div>
      
      {/* Members bar */}
      <div className="border-b bg-muted/30">
        <div className="container py-3">
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">Participants:</span>
            <div className="flex items-center gap-2">
              {currentGroup.members?.map((member) => (
                <div key={member.id} className="flex items-center gap-1">
                  <MemberAvatar member={member} size="sm" />
                  <span className="text-sm">{member.name}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
      
      {/* Messages area */}
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="container py-4 space-y-4">
            {messages.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-16">
                  <div className="text-4xl mb-4">
                    {MODE_DESCRIPTIONS[currentGroup.mode]?.icon}
                  </div>
                  <h3 className="text-lg font-medium mb-2">Ready to collaborate</h3>
                  <p className="text-muted-foreground text-center mb-4 max-w-md">
                    {MODE_DESCRIPTIONS[currentGroup.mode]?.description}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Enter your task below to start the collaboration session
                  </p>
                </CardContent>
              </Card>
            ) : (
              <>
                {messages.map((message) => (
                  <MessageBubble
                    key={message.id}
                    message={message}
                    members={currentGroup.members || []}
                  />
                ))}
                {isExecuting && (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Agents are thinking...</span>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>
        </ScrollArea>
      </div>
      
      {/* Error display */}
      {executionError && (
        <div className="px-4 py-2 bg-destructive/10 text-destructive text-sm">
          {executionError}
        </div>
      )}
      
      {/* Input area */}
      <div className="border-t bg-background">
        <div className="container py-4">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              placeholder="Enter your task or question..."
              disabled={isExecuting}
              className="flex-1"
            />
            <Button type="submit" disabled={!userInput.trim() || isExecuting}>
              {isExecuting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
