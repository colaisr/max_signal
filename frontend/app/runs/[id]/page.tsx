'use client'

import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { useParams, useRouter } from 'next/navigation'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

interface RunStep {
  step_name: string
  input_blob: any
  output_blob: string | null
  llm_model: string | null
  tokens_used: number
  cost_est: number
  created_at: string
}

interface Run {
  id: number
  trigger_type: string
  instrument: string
  timeframe: string
  status: string
  created_at: string
  finished_at: string | null
  cost_est_total: number
  steps: RunStep[]
}

async function fetchRun(id: string) {
  const { data } = await axios.get<Run>(`${API_BASE_URL}/api/runs/${id}`)
  return data
}

export default function RunDetailPage() {
  const params = useParams()
  const router = useRouter()
  const runId = params.id as string

  const { data: run, isLoading, error } = useQuery({
    queryKey: ['run', runId],
    queryFn: () => fetchRun(runId),
    refetchInterval: (data) => {
      // Poll every 2 seconds if still running
      return data?.status === 'running' || data?.status === 'queued' ? 2000 : false
    },
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'succeeded':
        return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20'
      case 'failed':
        return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20'
      case 'running':
        return 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20'
      case 'queued':
        return 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20'
      default:
        return 'text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800'
    }
  }

  if (isLoading) {
    return (
      <main className="min-h-screen p-8 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto">
          <p className="text-gray-600 dark:text-gray-400">Loading run details...</p>
        </div>
      </main>
    )
  }

  if (error || !run) {
    return (
      <main className="min-h-screen p-8 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-700 rounded p-4">
            <p className="text-red-700 dark:text-red-400">
              Error loading run: {error instanceof Error ? error.message : 'Unknown error'}
            </p>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen p-8 bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <button
            onClick={() => router.push('/')}
            className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 mb-4"
          >
            ← Back to Dashboard
          </button>
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
            Run #{run.id}
          </h1>
        </div>

        {/* Run Info */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Instrument</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">{run.instrument}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Timeframe</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">{run.timeframe}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Status</p>
              <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(run.status)}`}>
                {run.status}
              </span>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Created</p>
              <p className="text-sm text-gray-900 dark:text-white">
                {new Date(run.created_at).toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        {/* Steps */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
            Analysis Steps
          </h2>

          {run.steps.length === 0 ? (
            <p className="text-gray-600 dark:text-gray-400">
              No steps yet. Analysis pipeline will be implemented soon.
            </p>
          ) : (
            <div className="space-y-4">
              {run.steps.map((step, index) => (
                <div
                  key={index}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      {step.step_name}
                    </h3>
                    {step.llm_model && (
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {step.llm_model}
                      </span>
                    )}
                  </div>

                  {step.output_blob && (
                    <div className="mt-2">
                      <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Output:</p>
                      <pre className="bg-gray-50 dark:bg-gray-900 p-3 rounded text-sm text-gray-900 dark:text-gray-100 overflow-x-auto">
                        {step.output_blob}
                      </pre>
                    </div>
                  )}

                  <div className="mt-2 flex gap-4 text-xs text-gray-500 dark:text-gray-400">
                    {step.tokens_used > 0 && (
                      <span>Tokens: {step.tokens_used.toLocaleString()}</span>
                    )}
                    {step.cost_est > 0 && (
                      <span>Cost: ${step.cost_est.toFixed(4)}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  )
}

