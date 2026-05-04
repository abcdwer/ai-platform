'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { useMultiAgentStore } from '@/stores/multiAgentStore';
import { MODE_DESCRIPTIONS, MODE_COLORS, MEMBER_ROLE_COLORS, CollaborationMode } from '@/types/multi-agent';
import type { AgentGroup, AgentMember } from '@/types/multi-agent';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MemberEditorDialog } from '@/components/multi-agent/member-editor-dialog';
import { ModeConfigCard } from '@/components/multi-agent/mode-config-card';
import { 
  ArrowLeft, 
  Play, 
  Save, 
  Users, 
  Settings, 
  GripVertical,
  Plus,
  Trash2,
  ChevronRight,
} from 'lucide-react';

export default function EditGroupPage() {
  const params = useParams();
  const router = useRouter();
  const groupId = params.id as string;
  
  const {
    groups,
    currentGroup,
    setCurrentGroup,
    loadGroups,
    updateGroup,
    addMember,
    updateMember,
    deleteMember,
    reorderMembers,
    showMemberDialog,
    setShowMemberDialog,
    editingMember,
    setEditingMember,
  } = useMultiAgentStore();
  
  const [isSaving, setIsSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('members');
  
  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [mode, setMode] = useState<CollaborationMode>('sequential');
  const [maxIterations, setMaxIterations] = useState(10);
  
  useEffect(() => {
    if (groups.length === 0) {
      loadGroups();
    }
  }, [groups.length, loadGroups]);
  
  useEffect(() => {
    const group = groups.find((g) => g.id === groupId);
    if (group) {
      setCurrentGroup(group);
      setName(group.name);
      setDescription(group.description || '');
      setMode(group.mode as CollaborationMode);
      setMaxIterations(group.max_iterations);
    }
  }, [groupId, groups, setCurrentGroup]);
  
  const handleSave = async () => {
    setIsSaving(true);
    await updateGroup(groupId, {
      name,
      description,
      mode,
      max_iterations: maxIterations,
    });
    setIsSaving(false);
  };
  
  const handleAddMember = () => {
    setEditingMember(null);
    setShowMemberDialog(true);
  };
  
  const handleEditMember = (member: AgentMember) => {
    setEditingMember(member);
    setShowMemberDialog(true);
  };
  
  const handleDeleteMember = async (memberId: string) => {
    if (confirm('Are you sure you want to delete this member?')) {
      await deleteMember(groupId, memberId);
    }
  };
  
  const handleMemberSave = async (data: any) => {
    if (editingMember) {
      await updateMember(groupId, editingMember.id, data);
    } else {
      await addMember(groupId, data);
    }
    setShowMemberDialog(false);
    setEditingMember(null);
  };
  
  if (!currentGroup) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }
  
  return (
    <div className="container mx-auto py-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <Button variant="ghost" size="icon" onClick={() => router.push('/multi-agent')}>
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <div className="flex-1">
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="text-2xl font-bold border-none p-0 h-auto focus:ring-0"
            placeholder="Group Name"
          />
          <p className="text-muted-foreground mt-1">
            {MODE_DESCRIPTIONS[mode]?.icon} {MODE_DESCRIPTIONS[mode]?.title} mode
          </p>
        </div>
        <Button variant="outline" onClick={() => router.push(`/multi-agent/${groupId}/session`)}>
          <Play className="w-4 h-4 mr-2" />
          Start Session
        </Button>
        <Button onClick={handleSave} disabled={isSaving}>
          <Save className="w-4 h-4 mr-2" />
          {isSaving ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>
      
      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="members">
            <Users className="w-4 h-4 mr-2" />
            Members
          </TabsTrigger>
          <TabsTrigger value="settings">
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </TabsTrigger>
          <TabsTrigger value="mode">
            <ChevronRight className="w-4 h-4 mr-2" />
            Mode Config
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="members" className="mt-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-medium">Team Members</h3>
              <p className="text-sm text-muted-foreground">
                Configure the agents that will collaborate in this group
              </p>
            </div>
            <Button onClick={handleAddMember}>
              <Plus className="w-4 h-4 mr-2" />
              Add Member
            </Button>
          </div>
          
          {currentGroup.members && currentGroup.members.length > 0 ? (
            <div className="space-y-4">
              {currentGroup.members.map((member, index) => (
                <Card key={member.id} className="relative group">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-4">
                      <div className="flex items-center gap-2 cursor-move text-muted-foreground">
                        <GripVertical className="w-4 h-4" />
                        <span className="text-sm font-medium">{index + 1}</span>
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <div 
                            className="w-3 h-3 rounded-full" 
                            style={{ backgroundColor: member.color || MEMBER_ROLE_COLORS[member.role] }}
                          />
                          <span className="font-medium">{member.name}</span>
                          <Badge 
                            variant="outline" 
                            className="text-xs"
                            style={{ borderColor: MEMBER_ROLE_COLORS[member.role] + '60' }}
                          >
                            {member.role}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground line-clamp-1">
                          {member.system_prompt}
                        </p>
                        <div className="flex gap-4 mt-2 text-xs text-muted-foreground">
                          <span>Model: {member.model || 'default'}</span>
                          <span>Temp: {member.temperature}</span>
                          <span>Max tokens: {member.max_tokens}</span>
                        </div>
                      </div>
                      
                      <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => handleEditMember(member)}
                        >
                          Edit
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          className="text-destructive hover:text-destructive"
                          onClick={() => handleDeleteMember(member.id)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Users className="w-12 h-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">No members yet</h3>
                <p className="text-muted-foreground text-center mb-4">
                  Add agents to your team to start collaborating
                </p>
                <Button onClick={handleAddMember}>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Member
                </Button>
              </CardContent>
            </Card>
          )}
          
          {/* Mode visualization */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="text-lg">Collaboration Flow</CardTitle>
              <CardDescription>
                How agents will interact based on {MODE_DESCRIPTIONS[mode]?.title} mode
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ModeFlowVisualization 
                mode={mode} 
                members={currentGroup.members || []} 
              />
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="settings" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Group Settings</CardTitle>
              <CardDescription>
                Configure the basic settings for this agent group
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe the purpose of this agent team..."
                  rows={3}
                />
              </div>
              
              <Separator />
              
              <div className="space-y-2">
                <Label htmlFor="mode">Collaboration Mode</Label>
                <div className="flex flex-wrap gap-2">
                  {(Object.keys(MODE_DESCRIPTIONS) as CollaborationMode[]).map((m) => (
                    <Card 
                      key={m}
                      className={`cursor-pointer transition-all ${
                        mode === m 
                          ? 'ring-2 ring-primary' 
                          : 'hover:border-primary/50'
                      }`}
                      onClick={() => setMode(m)}
                    >
                      <CardContent className="p-3">
                        <div className="flex items-center gap-2">
                          <span className="text-xl">{MODE_DESCRIPTIONS[m].icon}</span>
                          <div>
                            <p className="font-medium text-sm">{MODE_DESCRIPTIONS[m].title}</p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
                <p className="text-sm text-muted-foreground mt-2">
                  {MODE_DESCRIPTIONS[mode]?.description}
                </p>
              </div>
              
              <Separator />
              
              <div className="space-y-2">
                <Label htmlFor="maxIterations">Max Iterations</Label>
                <Input
                  id="maxIterations"
                  type="number"
                  value={maxIterations}
                  onChange={(e) => setMaxIterations(parseInt(e.target.value) || 10)}
                  min={1}
                  max={100}
                  className="w-32"
                />
                <p className="text-sm text-muted-foreground">
                  Maximum number of collaboration rounds before stopping
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="mode" className="mt-6">
          <ModeConfigCard 
            mode={mode}
            config={currentGroup.mode_config || {}}
            onChange={(config) => updateGroup(groupId, { mode_config: config })}
          />
        </TabsContent>
      </Tabs>
      
      <MemberEditorDialog
        open={showMemberDialog}
        onOpenChange={setShowMemberDialog}
        member={editingMember}
        onSave={handleMemberSave}
      />
    </div>
  );
}

// Simple flow visualization component
function ModeFlowVisualization({ 
  mode, 
  members 
}: { 
  mode: CollaborationMode; 
  members: AgentMember[]; 
}) {
  if (members.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-8">
        Add members to see the collaboration flow
      </div>
    );
  }
  
  const renderSequentialFlow = () => (
    <div className="flex items-center justify-center gap-2 flex-wrap">
      {members.map((member, i) => (
        <div key={member.id} className="flex items-center gap-2">
          <div 
            className="px-4 py-2 rounded-lg border-2"
            style={{ 
              borderColor: member.color || MEMBER_ROLE_COLORS[member.role],
              backgroundColor: (member.color || MEMBER_ROLE_COLORS[member.role]) + '10'
            }}
          >
            <span className="font-medium text-sm">{member.name}</span>
          </div>
          {i < members.length - 1 && <ChevronRight className="w-4 h-4 text-muted-foreground" />}
        </div>
      ))}
    </div>
  );
  
  const renderParallelFlow = () => (
    <div className="flex flex-col items-center gap-4">
      <div className="text-sm text-muted-foreground mb-2">Same task →</div>
      <div className="flex gap-2 flex-wrap justify-center">
        {members.map((member) => (
          <div 
            key={member.id}
            className="px-4 py-2 rounded-lg border-2"
            style={{ 
              borderColor: member.color || MEMBER_ROLE_COLORS[member.role],
              backgroundColor: (member.color || MEMBER_ROLE_COLORS[member.role]) + '10'
            }}
          >
            <span className="font-medium text-sm">{member.name}</span>
          </div>
        ))}
      </div>
      <div className="text-muted-foreground">↓ Aggregate</div>
    </div>
  );
  
  const renderDebateFlow = () => {
    const pro = members.find((m) => m.role === 'supporter');
    const con = members.find((m) => m.role === 'opponent');
    const judge = members.find((m) => m.role === 'judge');
    
    return (
      <div className="flex flex-col items-center gap-4">
        <div className="flex gap-8">
          {pro && (
            <div 
              className="px-4 py-2 rounded-lg border-2 border-green-500 bg-green-50"
            >
              <span className="font-medium text-sm text-green-700">PRO</span>
              <p className="text-xs mt-1">{pro.name}</p>
            </div>
          )}
          <div className="text-muted-foreground flex items-center">VS</div>
          {con && (
            <div 
              className="px-4 py-2 rounded-lg border-2 border-red-500 bg-red-50"
            >
              <span className="font-medium text-sm text-red-700">CON</span>
              <p className="text-xs mt-1">{con.name}</p>
            </div>
          )}
        </div>
        {judge && (
          <div className="flex flex-col items-center">
            <div className="text-muted-foreground mb-2">↓</div>
            <div 
              className="px-4 py-2 rounded-lg border-2 border-amber-500 bg-amber-50"
            >
              <span className="font-medium text-sm text-amber-700">JUDGE</span>
              <p className="text-xs mt-1">{judge.name}</p>
            </div>
          </div>
        )}
      </div>
    );
  };
  
  const renderHierarchicalFlow = () => {
    const leader = members.find((m) => m.role === 'leader') || members[0];
    const subs = members.filter((m) => m.id !== leader?.id);
    
    return (
      <div className="flex flex-col items-center gap-4">
        <div 
          className="px-4 py-2 rounded-lg border-2 border-purple-500 bg-purple-50"
        >
          <span className="font-medium text-sm text-purple-700">LEADER</span>
          <p className="text-xs mt-1">{leader?.name}</p>
        </div>
        <div className="text-muted-foreground">↓ Delegates</div>
        <div className="flex gap-2 flex-wrap justify-center">
          {subs.map((member) => (
            <div 
              key={member.id}
              className="px-4 py-2 rounded-lg border-2"
              style={{ 
                borderColor: member.color || MEMBER_ROLE_COLORS[member.role],
                backgroundColor: (member.color || MEMBER_ROLE_COLORS[member.role]) + '10'
              }}
            >
              <span className="font-medium text-sm">{member.name}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };
  
  const renderRoundRobinFlow = () => (
    <div className="flex items-center justify-center gap-2 flex-wrap">
      {members.map((member, i) => (
        <div key={member.id} className="flex items-center gap-2">
          <div 
            className="px-4 py-2 rounded-lg border-2"
            style={{ 
              borderColor: member.color || MEMBER_ROLE_COLORS[member.role],
              backgroundColor: (member.color || MEMBER_ROLE_COLORS[member.role]) + '10'
            }}
          >
            <span className="font-medium text-sm">{member.name}</span>
            <span className="text-xs text-muted-foreground ml-1">#{i + 1}</span>
          </div>
          <ChevronRight className="w-4 h-4 text-muted-foreground" />
        </div>
      ))}
      <span className="text-sm text-muted-foreground ml-2">→ Loop</span>
    </div>
  );
  
  switch (mode) {
    case 'sequential':
      return renderSequentialFlow();
    case 'parallel':
      return renderParallelFlow();
    case 'debate':
      return renderDebateFlow();
    case 'hierarchical':
      return renderHierarchicalFlow();
    case 'round_robin':
      return renderRoundRobinFlow();
    default:
      return null;
  }
}
