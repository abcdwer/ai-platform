'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useFinetuneStore, FinetuneModel } from '@/stores/finetuneStore';

export default function ModelsPage() {
  const { models, modelsLoading, loadModels, deployModel, undeployModel, deleteModel } = useFinetuneStore();
  const [actionModel, setActionModel] = useState<string | null>(null);

  useEffect(() => {
    loadModels();
  }, [loadModels]);

  const handleDeploy = async (id: string) => {
    setActionModel(id);
    try {
      await deployModel(id);
    } catch (error) {
      console.error('Failed to deploy model:', error);
    }
    setActionModel(null);
  };

  const handleUndeploy = async (id: string) => {
    setActionModel(id);
    try {
      await undeployModel(id);
    } catch (error) {
      console.error('Failed to undeploy model:', error);
    }
    setActionModel(null);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this model?')) return;
    try {
      await deleteModel(id);
    } catch (error) {
      console.error('Failed to delete model:', error);
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Fine-tuned Models</h1>
        <p className="text-gray-600 mt-1">Manage your fine-tuned models</p>
      </div>

      {modelsLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : models.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-gray-900">No models yet</h3>
          <p className="mt-2 text-gray-500">Complete a fine-tuning job to create your first model.</p>
          <Link
            href="/finetune/jobs"
            className="mt-4 inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            View Jobs
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {models.map((model) => (
            <div key={model.id} className="bg-white rounded-lg shadow overflow-hidden">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center">
                    <div className="bg-purple-100 rounded-lg p-3 mr-4">
                      <svg className="h-6 w-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">{model.name}</h3>
                      <p className="text-sm text-gray-500">{model.base_model}</p>
                    </div>
                  </div>
                  {model.is_deployed ? (
                    <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                      Deployed
                    </span>
                  ) : (
                    <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-600 rounded-full">
                      Not Deployed
                    </span>
                  )}
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Type</span>
                    <span className="font-medium text-gray-900 capitalize">{model.model_type}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Final Loss</span>
                    <span className="font-medium text-gray-900">{model.final_loss?.toFixed(4) || '-'}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Size</span>
                    <span className="font-medium text-gray-900">
                      {model.file_size_mb ? `${model.file_size_mb.toFixed(1)} MB` : '-'}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="mt-6 flex space-x-2">
                  {model.is_deployed ? (
                    <button
                      onClick={() => handleUndeploy(model.id)}
                      disabled={actionModel === model.id}
                      className="flex-1 px-3 py-2 text-sm border border-yellow-500 text-yellow-600 rounded-lg hover:bg-yellow-50 disabled:opacity-50"
                    >
                      Undeploy
                    </button>
                  ) : (
                    <button
                      onClick={() => handleDeploy(model.id)}
                      disabled={actionModel === model.id}
                      className="flex-1 px-3 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                    >
                      Deploy
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(model.id)}
                    className="px-3 py-2 text-sm text-red-600 border border-red-300 rounded-lg hover:bg-red-50"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
