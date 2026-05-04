'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useFinetuneStore, FinetuneJob } from '@/stores/finetuneStore';

export default function JobsPage() {
  const { jobs, jobsLoading, loadJobs, startJob, pauseJob, resumeJob, stopJob, deleteJob } = useFinetuneStore();
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [actionJob, setActionJob] = useState<string | null>(null);

  useEffect(() => {
    loadJobs(statusFilter || undefined);
  }, [statusFilter, loadJobs]);

  const handleAction = async (action: string, jobId: string) => {
    setActionJob(jobId);
    try {
      switch (action) {
        case 'start':
          await startJob(jobId);
          break;
        case 'pause':
          await pauseJob(jobId);
          break;
        case 'resume':
          await resumeJob(jobId);
          break;
        case 'stop':
          await stopJob(jobId);
          break;
        case 'delete':
          await deleteJob(jobId);
          break;
      }
    } catch (error) {
      console.error(`Failed to ${action} job:`, error);
    }
    setActionJob(null);
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      pending: 'bg-gray-100 text-gray-800',
      queued: 'bg-blue-100 text-blue-800',
      running: 'bg-green-100 text-green-800',
      paused: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      cancelled: 'bg-gray-100 text-gray-800',
    };
    
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${styles[status] || styles.pending}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'pending', label: 'Pending' },
    { value: 'queued', label: 'Queued' },
    { value: 'running', label: 'Running' },
    { value: 'paused', label: 'Paused' },
    { value: 'completed', label: 'Completed' },
    { value: 'failed', label: 'Failed' },
    { value: 'cancelled', label: 'Cancelled' },
  ];

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Fine-tuning Jobs</h1>
          <p className="text-gray-600 mt-1">Manage your model fine-tuning jobs</p>
        </div>
        <Link
          href="/finetune/jobs/new"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Create Job
        </Link>
      </div>

      {/* Filters */}
      <div className="mb-6 flex items-center space-x-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          {statusOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      {jobsLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : jobs.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-gray-900">No jobs yet</h3>
          <p className="mt-2 text-gray-500">Create your first fine-tuning job to get started.</p>
          <Link
            href="/finetune/jobs/new"
            className="mt-4 inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Create Job
          </Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {jobs.map((job) => (
            <div key={job.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <h3 className="text-lg font-medium text-gray-900">{job.name}</h3>
                    {getStatusBadge(job.status)}
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    Model: {job.base_model}
                  </p>
                  {job.description && (
                    <p className="text-sm text-gray-600 mt-2">{job.description}</p>
                  )}
                </div>
                
                {/* Progress */}
                <div className="text-right ml-6">
                  <div className="text-2xl font-bold text-gray-900">
                    {job.progress_pct.toFixed(1)}%
                  </div>
                  <div className="text-sm text-gray-500">
                    Step {job.current_step} / {job.total_steps}
                  </div>
                </div>
              </div>
              
              {/* Progress Bar */}
              <div className="mt-4">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all ${
                      job.status === 'running' ? 'bg-green-500' : 'bg-blue-500'
                    }`}
                    style={{ width: `${job.progress_pct}%` }}
                  ></div>
                </div>
              </div>
              
              {/* Metrics */}
              <div className="mt-4 grid grid-cols-4 gap-4">
                <div>
                  <div className="text-xs text-gray-500">Epoch</div>
                  <div className="text-sm font-medium">{job.current_epoch} / {job.total_epochs}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Current Loss</div>
                  <div className="text-sm font-medium">{job.current_loss?.toFixed(4) || '-'}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Best Loss</div>
                  <div className="text-sm font-medium">{job.best_loss?.toFixed(4) || '-'}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Learning Rate</div>
                  <div className="text-sm font-medium">
                    {job.learning_rate ? `${(job.learning_rate * 10000).toFixed(2)}e-4` : '-'}
                  </div>
                </div>
              </div>
              
              {/* Actions */}
              <div className="mt-4 flex justify-end space-x-2">
                <Link
                  href={`/finetune/jobs/${job.id}`}
                  className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  View Details
                </Link>
                
                {job.status === 'pending' && (
                  <button
                    onClick={() => handleAction('start', job.id)}
                    disabled={actionJob === job.id}
                    className="px-3 py-1 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                  >
                    Start
                  </button>
                )}
                
                {job.status === 'running' && (
                  <>
                    <button
                      onClick={() => handleAction('pause', job.id)}
                      disabled={actionJob === job.id}
                      className="px-3 py-1 text-sm border border-yellow-500 text-yellow-600 rounded-lg hover:bg-yellow-50 disabled:opacity-50"
                    >
                      Pause
                    </button>
                    <button
                      onClick={() => handleAction('stop', job.id)}
                      disabled={actionJob === job.id}
                      className="px-3 py-1 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                    >
                      Stop
                    </button>
                  </>
                )}
                
                {job.status === 'paused' && (
                  <button
                    onClick={() => handleAction('resume', job.id)}
                    disabled={actionJob === job.id}
                    className="px-3 py-1 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    Resume
                  </button>
                )}
                
                {job.status !== 'running' && job.status !== 'paused' && (
                  <button
                    onClick={() => handleAction('delete', job.id)}
                    disabled={actionJob === job.id}
                    className="px-3 py-1 text-sm text-red-600 border border-red-300 rounded-lg hover:bg-red-50 disabled:opacity-50"
                  >
                    Delete
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
