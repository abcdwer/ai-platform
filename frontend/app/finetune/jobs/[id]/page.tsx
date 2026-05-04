'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useFinetuneStore } from '@/stores/finetuneStore';

export default function JobDetailPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;
  
  const {
    currentJob,
    lossCurve,
    getJob,
    loadJobStatus,
    subscribeToJobProgress,
    unsubscribeFromJobProgress,
    pauseJob,
    resumeJob,
    stopJob,
  } = useFinetuneStore();
  
  const [gpuStats, setGpuStats] = useState<any>(null);
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    loadJobStatus(jobId);
    
    // Poll for updates
    const interval = setInterval(() => {
      loadJobStatus(jobId);
    }, 5000);
    setRefreshInterval(interval);
    
    // Subscribe to SSE for real-time updates
    subscribeToJobProgress(jobId);
    
    return () => {
      unsubscribeFromJobProgress();
      if (refreshInterval) clearInterval(refreshInterval);
    };
  }, [jobId, loadJobStatus, subscribeToJobProgress, unsubscribeFromJobProgress]);

  // Draw loss curve
  useEffect(() => {
    if (!canvasRef.current || lossCurve.steps.length === 0) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const width = canvas.width;
    const height = canvas.height;
    const padding = 40;
    
    // Clear canvas
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, width, height);
    
    // Draw grid
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
      const y = padding + (height - 2 * padding) * (i / 5);
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(width - padding, y);
      ctx.stroke();
    }
    
    // Get data
    const steps = lossCurve.steps;
    const losses = lossCurve.losses;
    
    if (steps.length === 0) return;
    
    // Calculate bounds
    const minLoss = Math.min(...losses);
    const maxLoss = Math.max(...losses);
    const minStep = Math.min(...steps);
    const maxStep = Math.max(...steps);
    
    // Scale functions
    const scaleX = (step: number) => padding + ((step - minStep) / (maxStep - minStep || 1)) * (width - 2 * padding);
    const scaleY = (loss: number) => padding + ((maxLoss - loss) / (maxLoss - minLoss || 1)) * (height - 2 * padding);
    
    // Draw loss curve
    ctx.strokeStyle = '#3b82f6';
    ctx.lineWidth = 2;
    ctx.beginPath();
    
    steps.forEach((step, i) => {
      const x = scaleX(step);
      const y = scaleY(losses[i]);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
    
    // Draw points
    ctx.fillStyle = '#3b82f6';
    steps.forEach((step, i) => {
      const x = scaleX(step);
      const y = scaleY(losses[i]);
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fill();
    });
    
    // Draw labels
    ctx.fillStyle = '#6b7280';
    ctx.font = '12px sans-serif';
    ctx.fillText(`Loss: ${minLoss.toFixed(4)} - ${maxLoss.toFixed(4)}`, padding, height - 10);
    ctx.fillText(`Steps: ${minStep} - ${maxStep}`, width / 2 - 50, height - 10);
  }, [lossCurve]);

  if (!currentJob) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-gray-500',
      running: 'bg-green-500',
      paused: 'bg-yellow-500',
      completed: 'bg-green-600',
      failed: 'bg-red-500',
      cancelled: 'bg-gray-400',
    };
    return colors[status] || 'bg-gray-500';
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <button
            onClick={() => router.push('/finetune/jobs')}
            className="text-sm text-blue-600 hover:text-blue-800 mb-2"
          >
            ← Back to Jobs
          </button>
          <h1 className="text-2xl font-bold text-gray-900">{currentJob.name}</h1>
          <div className="flex items-center mt-2 space-x-4">
            <div className="flex items-center">
              <div className={`w-3 h-3 rounded-full ${getStatusColor(currentJob.status)} mr-2`}></div>
              <span className="text-gray-600 capitalize">{currentJob.status}</span>
            </div>
            <span className="text-gray-400">•</span>
            <span className="text-gray-600">{currentJob.base_model}</span>
          </div>
        </div>
        
        {/* Actions */}
        <div className="flex space-x-2">
          {currentJob.status === 'running' && (
            <>
              <button
                onClick={() => pauseJob(jobId)}
                className="px-4 py-2 border border-yellow-500 text-yellow-600 rounded-lg hover:bg-yellow-50"
              >
                Pause
              </button>
              <button
                onClick={() => stopJob(jobId)}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                Stop
              </button>
            </>
          )}
          {currentJob.status === 'paused' && (
            <button
              onClick={() => resumeJob(jobId)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Resume
            </button>
          )}
        </div>
      </div>

      {/* Progress Overview */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Progress</div>
          <div className="text-2xl font-bold text-gray-900">{currentJob.progress_pct.toFixed(1)}%</div>
          <div className="text-sm text-gray-500">Step {currentJob.current_step} / {currentJob.total_steps}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Current Loss</div>
          <div className="text-2xl font-bold text-gray-900">{currentJob.current_loss?.toFixed(4) || '-'}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Best Loss</div>
          <div className="text-2xl font-bold text-green-600">{currentJob.best_loss?.toFixed(4) || '-'}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Learning Rate</div>
          <div className="text-2xl font-bold text-gray-900">
            {currentJob.learning_rate ? `${(currentJob.learning_rate * 10000).toFixed(2)}e-4` : '-'}
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex justify-between text-sm mb-2">
          <span>Training Progress</span>
          <span>Epoch {currentJob.current_epoch} / {currentJob.total_epochs}</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-4">
          <div
            className="h-4 rounded-full bg-blue-600 transition-all duration-500"
            style={{ width: `${currentJob.progress_pct}%` }}
          ></div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Loss Curve */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Loss Curve</h3>
          <canvas
            ref={canvasRef}
            width={500}
            height={300}
            className="w-full"
          ></canvas>
        </div>

        {/* GPU Stats */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-lg font-medium text-gray-900 mb-4">GPU Utilization</h3>
          {gpuStats ? (
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Memory</span>
                  <span>{gpuStats.memoryUsed || '8.0'} GB / {gpuStats.memoryTotal || '24.0'} GB</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="h-2 rounded-full bg-green-500"
                    style={{ width: `${((gpuStats.memoryUsed || 8) / (gpuStats.memoryTotal || 24)) * 100}%` }}
                  ></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Utilization</span>
                  <span>{gpuStats.utilization || 85}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="h-2 rounded-full bg-blue-500"
                    style={{ width: `${gpuStats.utilization || 85}%` }}
                  ></div>
                </div>
              </div>
              <div className="pt-4 border-t">
                <div className="text-sm text-gray-500">Temperature</div>
                <div className="text-lg font-medium">{gpuStats.temperature || 65}°C</div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-400">
              GPU monitoring will appear when training starts
            </div>
          )}
        </div>
      </div>

      {/* Training Log */}
      <div className="bg-white rounded-lg shadow p-4 mt-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Training Log</h3>
        <div className="bg-gray-900 rounded-lg p-4 h-64 overflow-y-auto font-mono text-sm text-green-400">
          <div>[{new Date().toLocaleTimeString()}] Initializing training...</div>
          <div>[{new Date().toLocaleTimeString()}] Loading model: {currentJob.base_model}</div>
          <div>[{new Date().toLocaleTimeString()}] Loading dataset...</div>
          {currentJob.status === 'running' && (
            <>
              <div>[{new Date().toLocaleTimeString()}] Starting training loop...</div>
              {lossCurve.steps.slice(-5).map((step, i) => (
                <div key={step}>
                  [{new Date().toLocaleTimeString()}] Step {step}: loss={lossCurve.losses[lossCurve.steps.indexOf(step)].toFixed(4)}
                </div>
              ))}
            </>
          )}
          {currentJob.status === 'completed' && (
            <div className="text-blue-400">
              [{new Date().toLocaleTimeString()}] Training completed successfully!
            </div>
          )}
          {currentJob.status === 'failed' && (
            <div className="text-red-400">
              [{new Date().toLocaleTimeString()}] Training failed: {currentJob.error_message || 'Unknown error'}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
