'use client';

import { useState, useEffect } from 'react';
import { Sidebar } from '@/components/sidebar';
import { ModeToggle } from '@/components/mode-toggle';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { SystemMonitor } from '@/components/monitoring/system-monitor';
import { useAuthStore } from '@/stores/authStore';
import {
  Settings,
  User,
  Bell,
  Shield,
  Palette,
  Database,
  Key,
  Save,
  Loader2,
  Check,
  AlertCircle,
  Trash2,
  Activity,
} from 'lucide-react';
import { useTheme } from 'next-themes';

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const { user, updateProfile, isLoading, error } = useAuthStore();
  
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  
  const [profileData, setProfileData] = useState({
    email: '',
    username: '',
    full_name: '',
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  
  const [settings, setSettings] = useState({
    // General
    defaultModel: 'llama2',
    defaultProvider: 'ollama',
    
    // API Keys
    openaiKey: '',
    
    // Notifications
    notificationsEnabled: true,
    soundEnabled: true,
    
    // Display
    compactMode: false,
    showTimestamps: true,
  });
  
  // Load user data
  useEffect(() => {
    if (user) {
      setProfileData({
        email: user.email || '',
        username: user.username || '',
        full_name: user.full_name || '',
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
    }
  }, [user]);
  
  const handleProfileSave = async () => {
    setIsSaving(true);
    setSaveSuccess(false);
    
    try {
      const updateData: any = {};
      if (profileData.email !== user?.email) updateData.email = profileData.email;
      if (profileData.username !== user?.username) updateData.username = profileData.username;
      if (profileData.full_name !== user?.full_name) updateData.full_name = profileData.full_name;
      if (profileData.new_password) {
        if (profileData.new_password !== profileData.confirm_password) {
          alert('Passwords do not match');
          setIsSaving(false);
          return;
        }
        updateData.password = profileData.new_password;
      }
      
      if (Object.keys(updateData).length > 0) {
        await updateProfile(updateData);
        setSaveSuccess(true);
        setProfileData({
          ...profileData,
          current_password: '',
          new_password: '',
          confirm_password: '',
        });
      }
    } catch (err) {
      console.error('Failed to update profile:', err);
    }
    
    setIsSaving(false);
  };
  
  const handleSettingsSave = async () => {
    setIsSaving(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsSaving(false);
    setSaveSuccess(true);
  };

  return (
    <div className="flex h-screen">
      <Sidebar />
      
      <main className="flex-1 overflow-y-auto">
        {/* Header */}
        <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-10">
          <div className="container mx-auto px-6 py-4 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Settings</h1>
              <p className="text-muted-foreground">Manage your preferences and configuration</p>
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="container mx-auto px-6 py-8">
          <Tabs defaultValue="profile" className="w-full">
            <TabsList className="grid w-full grid-cols-7 mb-8">
              <TabsTrigger value="profile" className="gap-2">
                <User className="h-4 w-4" />
                Profile
              </TabsTrigger>
              <TabsTrigger value="general" className="gap-2">
                <Settings className="h-4 w-4" />
                General
              </TabsTrigger>
              <TabsTrigger value="appearance" className="gap-2">
                <Palette className="h-4 w-4" />
                Appearance
              </TabsTrigger>
              <TabsTrigger value="api" className="gap-2">
                <Key className="h-4 w-4" />
                API Keys
              </TabsTrigger>
              <TabsTrigger value="notifications" className="gap-2">
                <Bell className="h-4 w-4" />
                Notifications
              </TabsTrigger>
              <TabsTrigger value="data" className="gap-2">
                <Database className="h-4 w-4" />
                Data
              </TabsTrigger>
              <TabsTrigger value="monitoring" className="gap-2">
                <Activity className="h-4 w-4" />
                Monitor
              </TabsTrigger>
            </TabsList>

            {/* Profile Settings */}
            <TabsContent value="profile">
              <div className="space-y-6">
                {error && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}
                
                {saveSuccess && (
                  <Alert variant="success" className="border-green-500/50 bg-green-500/10">
                    <Check className="h-4 w-4" />
                    <AlertDescription>Changes saved successfully!</AlertDescription>
                  </Alert>
                )}
                
                {/* Avatar Section */}
                <Card>
                  <CardHeader>
                    <CardTitle>Profile Picture</CardTitle>
                    <CardDescription>
                      This is your public avatar displayed across the platform
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-6">
                      <Avatar size="xl">
                        <AvatarImage src={user?.avatar_url} />
                        <AvatarFallback className="text-xl">
                          {user?.username?.slice(0, 2).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <div className="space-y-2">
                        <Button variant="outline" disabled>
                          Upload Image
                        </Button>
                        <p className="text-xs text-muted-foreground">
                          JPG, PNG or GIF. Max size 2MB.
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                
                {/* Profile Info */}
                <Card>
                  <CardHeader>
                    <CardTitle>Profile Information</CardTitle>
                    <CardDescription>
                      Update your account information
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="username">Username</Label>
                        <Input
                          id="username"
                          value={profileData.username}
                          onChange={(e) => setProfileData({...profileData, username: e.target.value})}
                          disabled={isLoading}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="full_name">Full Name</Label>
                        <Input
                          id="full_name"
                          value={profileData.full_name}
                          onChange={(e) => setProfileData({...profileData, full_name: e.target.value})}
                          disabled={isLoading}
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email">Email</Label>
                      <Input
                        id="email"
                        type="email"
                        value={profileData.email}
                        onChange={(e) => setProfileData({...profileData, email: e.target.value})}
                        disabled={isLoading}
                      />
                    </div>
                  </CardContent>
                </Card>
                
                {/* Password Change */}
                <Card>
                  <CardHeader>
                    <CardTitle>Change Password</CardTitle>
                    <CardDescription>
                      Leave blank to keep your current password
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="current_password">Current Password</Label>
                      <Input
                        id="current_password"
                        type="password"
                        value={profileData.current_password}
                        onChange={(e) => setProfileData({...profileData, current_password: e.target.value})}
                        disabled={isLoading}
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="new_password">New Password</Label>
                        <Input
                          id="new_password"
                          type="password"
                          value={profileData.new_password}
                          onChange={(e) => setProfileData({...profileData, new_password: e.target.value})}
                          disabled={isLoading}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="confirm_password">Confirm New Password</Label>
                        <Input
                          id="confirm_password"
                          type="password"
                          value={profileData.confirm_password}
                          onChange={(e) => setProfileData({...profileData, confirm_password: e.target.value})}
                          disabled={isLoading}
                        />
                      </div>
                    </div>
                  </CardContent>
                  <CardContent>
                    <Button onClick={handleProfileSave} disabled={isLoading}>
                      {isLoading ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Save className="h-4 w-4 mr-2" />
                      )}
                      Save Changes
                    </Button>
                  </CardContent>
                </Card>
                
                {/* Danger Zone */}
                <Card className="border-destructive/50">
                  <CardHeader>
                    <CardTitle className="text-destructive">Danger Zone</CardTitle>
                    <CardDescription>
                      Irreversible and destructive actions
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button variant="destructive">
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete Account
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* General Settings */}
            <TabsContent value="general">
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Default Model</CardTitle>
                    <CardDescription>
                      Configure your default AI model for new conversations
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="provider">Provider</Label>
                        <select
                          id="provider"
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                          value={settings.defaultProvider}
                          onChange={(e) => setSettings({...settings, defaultProvider: e.target.value})}
                        >
                          <option value="ollama">Ollama (Local)</option>
                          <option value="openai">OpenAI</option>
                        </select>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="model">Model</Label>
                        <select
                          id="model"
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                          value={settings.defaultModel}
                          onChange={(e) => setSettings({...settings, defaultModel: e.target.value})}
                        >
                          <option value="llama2">Llama 2</option>
                          <option value="mistral">Mistral</option>
                          <option value="codellama">Code Llama</option>
                          <option value="gpt-4">GPT-4</option>
                          <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                        </select>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Display Options</CardTitle>
                    <CardDescription>
                      Customize how conversations are displayed
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <Label>Compact Mode</Label>
                        <p className="text-sm text-muted-foreground">
                          Use a more compact layout for messages
                        </p>
                      </div>
                      <Switch
                        checked={settings.compactMode}
                        onCheckedChange={(checked) => setSettings({...settings, compactMode: checked})}
                      />
                    </div>
                    <Separator />
                    <div className="flex items-center justify-between">
                      <div>
                        <Label>Show Timestamps</Label>
                        <p className="text-sm text-muted-foreground">
                          Display time stamps on messages
                        </p>
                      </div>
                      <Switch
                        checked={settings.showTimestamps}
                        onCheckedChange={(checked) => setSettings({...settings, showTimestamps: checked})}
                      />
                    </div>
                  </CardContent>
                  <CardContent>
                    <Button onClick={handleSettingsSave} disabled={isSaving}>
                      {isSaving ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Save className="h-4 w-4 mr-2" />
                      )}
                      Save Changes
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Appearance */}
            <TabsContent value="appearance">
              <Card>
                <CardHeader>
                  <CardTitle>Theme</CardTitle>
                  <CardDescription>
                    Select your preferred color theme
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-3 gap-4">
                    <button
                      onClick={() => setTheme('light')}
                      className={`flex flex-col items-center justify-center p-4 rounded-lg border-2 transition-colors ${
                        theme === 'light' ? 'border-primary' : 'border-transparent'
                      }`}
                    >
                      <div className="w-full h-20 rounded-md bg-white border flex items-center justify-center">
                        <div className="w-8 h-8 rounded-full bg-gray-200" />
                      </div>
                      <span className="mt-2 text-sm">Light</span>
                    </button>
                    <button
                      onClick={() => setTheme('dark')}
                      className={`flex flex-col items-center justify-center p-4 rounded-lg border-2 transition-colors ${
                        theme === 'dark' ? 'border-primary' : 'border-transparent'
                      }`}
                    >
                      <div className="w-full h-20 rounded-md bg-gray-900 border border-gray-700 flex items-center justify-center">
                        <div className="w-8 h-8 rounded-full bg-gray-700" />
                      </div>
                      <span className="mt-2 text-sm">Dark</span>
                    </button>
                    <button
                      onClick={() => setTheme('system')}
                      className={`flex flex-col items-center justify-center p-4 rounded-lg border-2 transition-colors ${
                        theme === 'system' ? 'border-primary' : 'border-transparent'
                      }`}
                    >
                      <div className="w-full h-20 rounded-md bg-gradient-to-r from-white to-gray-900 border flex items-center justify-center">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-gray-200 to-gray-700" />
                      </div>
                      <span className="mt-2 text-sm">System</span>
                    </button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* API Keys */}
            <TabsContent value="api">
              <Card>
                <CardHeader>
                  <CardTitle>API Keys</CardTitle>
                  <CardDescription>
                    Configure your API keys for external AI providers
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="openai-key">OpenAI API Key</Label>
                    <Input
                      id="openai-key"
                      type="password"
                      placeholder="sk-..."
                      value={settings.openaiKey}
                      onChange={(e) => setSettings({...settings, openaiKey: e.target.value})}
                    />
                    <p className="text-xs text-muted-foreground">
                      Get your API key from{' '}
                      <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" className="underline">
                        OpenAI Dashboard
                      </a>
                    </p>
                  </div>
                </CardContent>
                <CardContent>
                  <Button onClick={handleSettingsSave} disabled={isSaving}>
                    {isSaving ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Save className="h-4 w-4 mr-2" />
                    )}
                    Save API Key
                  </Button>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Notifications */}
            <TabsContent value="notifications">
              <Card>
                <CardHeader>
                  <CardTitle>Notification Preferences</CardTitle>
                  <CardDescription>
                    Choose how you want to be notified
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Push Notifications</Label>
                      <p className="text-sm text-muted-foreground">
                        Receive notifications when important events occur
                      </p>
                    </div>
                    <Switch
                      checked={settings.notificationsEnabled}
                      onCheckedChange={(checked) => setSettings({...settings, notificationsEnabled: checked})}
                    />
                  </div>
                  <Separator />
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Sound Effects</Label>
                      <p className="text-sm text-muted-foreground">
                        Play sounds for new messages
                      </p>
                    </div>
                    <Switch
                      checked={settings.soundEnabled}
                      onCheckedChange={(checked) => setSettings({...settings, soundEnabled: checked})}
                    />
                  </div>
                </CardContent>
                <CardContent>
                  <Button onClick={handleSettingsSave} disabled={isSaving}>
                    {isSaving ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Save className="h-4 w-4 mr-2" />
                    )}
                    Save Preferences
                  </Button>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Data */}
            <TabsContent value="data">
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Export Data</CardTitle>
                    <CardDescription>
                      Download a copy of your data
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button variant="outline">
                      Export All Data
                    </Button>
                  </CardContent>
                </Card>
                
                <Card className="border-destructive/50">
                  <CardHeader>
                    <CardTitle className="text-destructive">Clear Data</CardTitle>
                    <CardDescription>
                      Remove all your conversations and settings
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">
                      This will permanently delete all your conversations, agents, and settings. This action cannot be undone.
                    </p>
                    <Button variant="destructive">
                      <Trash2 className="h-4 w-4 mr-2" />
                      Clear All Data
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* System Monitoring */}
            <TabsContent value="monitoring">
              <SystemMonitor />
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
}
