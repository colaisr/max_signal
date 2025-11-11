'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { useParams, useRouter } from 'next/navigation'
import { useState } from 'react'

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
  const { data } = await axios.get<Run>(`${API_BASE_URL}/api/runs/${id}`, {
    withCredentials: true
  })
  return data
}

async function publishRun(id: string) {
  const { data } = await axios.post(`${API_BASE_URL}/api/runs/${id}/publish`, {}, {
    withCredentials: true
  })
  return data
}

export default function RunDetailPage() {
  const params = useParams()
  const router = useRouter()
  const queryClient = useQueryClient()
  const runId = params.id as string
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set())
  const [copied, setCopied] = useState(false)
  const [publishStatus, setPublishStatus] = useState<{ success?: boolean; message?: string; error?: string } | null>(null)

  const { data: run, isLoading, error } = useQuery({
    queryKey: ['run', runId],
    queryFn: () => fetchRun(runId),
    refetchInterval: (query) => {
      const data = query.state.data as Run | undefined
      // Poll every 2 seconds if still running/queued, otherwise stop polling
      if (data?.status === 'running' || data?.status === 'queued') {
        return 2000
      }
      return false
    },
    // Force refetch on mount and window focus
    refetchOnMount: 'always',
    refetchOnWindowFocus: true,
    // Don't cache stale data when polling - always fetch fresh
    staleTime: 0,
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

  const toggleStep = (stepName: string) => {
    const newExpanded = new Set(expandedSteps)
    if (newExpanded.has(stepName)) {
      newExpanded.delete(stepName)
    } else {
      newExpanded.add(stepName)
    }
    setExpandedSteps(newExpanded)
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const getFinalPost = () => {
    const mergeStep = run?.steps.find(s => s.step_name === 'merge')
    return mergeStep?.output_blob || null
  }

  const publishMutation = useMutation({
    mutationFn: () => publishRun(runId),
    onSuccess: (data) => {
      setPublishStatus({ success: data.success, message: data.message })
      queryClient.invalidateQueries({ queryKey: ['run', runId] })
      setTimeout(() => setPublishStatus(null), 5000)
    },
    onError: (error: any) => {
      setPublishStatus({ success: false, error: error.response?.data?.detail || error.message })
      setTimeout(() => setPublishStatus(null), 5000)
    },
  })

  const handlePublish = () => {
    if (window.confirm('Publish this analysis to Telegram channel?')) {
      publishMutation.mutate()
    }
  }

  const finalPost = getFinalPost()

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          <p className="text-gray-600 dark:text-gray-400">Loading run details...</p>
        </div>
      </div>
    )
  }

  if (error || !run) {
    return (
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-700 rounded p-4">
            <p className="text-red-700 dark:text-red-400">
              Error loading run: {error instanceof Error ? error.message : 'Unknown error'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
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

        {/* Final Telegram Post Preview */}
        {finalPost && run.status === 'succeeded' && (
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-lg shadow-lg p-6 mb-6 border-2 border-blue-200 dark:border-blue-800">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
                📱 Final Telegram Post
              </h2>
              <div className="flex gap-2">
                <button
                  onClick={() => copyToClipboard(finalPost)}
                  className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-md text-sm font-medium transition-colors"
                >
                  {copied ? '✓ Copied!' : 'Copy to Clipboard'}
                </button>
                <button
                  onClick={handlePublish}
                  disabled={publishMutation.isPending}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-md text-sm font-medium transition-colors"
                >
                  {publishMutation.isPending ? 'Publishing...' : '📤 Publish to Telegram'}
                </button>
              </div>
            </div>
            
            {publishStatus && (
              <div className={`mb-4 p-3 rounded ${
                publishStatus.success 
                  ? 'bg-green-100 dark:bg-green-900/30 border border-green-400 dark:border-green-700 text-green-700 dark:text-green-400'
                  : 'bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-400'
              }`}>
                {publishStatus.success ? (
                  <p>✅ {publishStatus.message}</p>
                ) : (
                  <p>❌ Error: {publishStatus.error}</p>
                )}
              </div>
            )}
            
            <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
              <pre className="whitespace-pre-wrap text-sm text-gray-900 dark:text-gray-100 font-mono">
                {finalPost}
              </pre>
            </div>
            <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              Ready to publish to Telegram channel
            </p>
          </div>
        )}

        {/* Analysis Steps Timeline */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
            Analysis Steps Timeline
          </h2>

          {run.steps.length === 0 ? (
            <p className="text-gray-600 dark:text-gray-400">
              {run.status === 'running' || run.status === 'queued' 
                ? 'Pipeline is running... Steps will appear here as they complete.'
                : 'No steps yet. Analysis pipeline will be implemented soon.'}
            </p>
          ) : (
            <div className="space-y-3">
              {run.steps.map((step, index) => {
                const isExpanded = expandedSteps.has(step.step_name)
                const stepNames: Record<string, string> = {
                  wyckoff: '1️⃣ Wyckoff Analysis',
                  smc: '2️⃣ Smart Money Concepts (SMC)',
                  vsa: '3️⃣ Volume Spread Analysis (VSA)',
                  delta: '4️⃣ Delta Analysis',
                  ict: '5️⃣ ICT Analysis',
                  merge: '6️⃣ Merge & Telegram Post',
                }
                const stepLabel = stepNames[step.step_name] || step.step_name

                return (
                  <div
                    key={index}
                    className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
                  >
                    {/* Step Header */}
                    <button
                      onClick={() => toggleStep(step.step_name)}
                      className="w-full px-4 py-3 flex justify-between items-center hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-lg font-semibold text-gray-900 dark:text-white">
                          {stepLabel}
                        </span>
                        {step.llm_model && (
                          <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-gray-600 dark:text-gray-400">
                            {step.llm_model}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-4">
                        {step.tokens_used > 0 && (
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {step.tokens_used.toLocaleString()} tokens
                          </span>
                        )}
                        {step.cost_est > 0 && (
                          <span className="text-xs font-medium text-gray-600 dark:text-gray-300">
                            ${step.cost_est.toFixed(4)}
                          </span>
                        )}
                        <span className="text-gray-400 dark:text-gray-500">
                          {isExpanded ? '▼' : '▶'}
                        </span>
                      </div>
                    </button>

                    {/* Step Content (Expandable) */}
                    {isExpanded && (
                      <div className="px-4 pb-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
                        {step.input_blob && (
                          <div className="mt-3">
                            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wide">
                              Input Prompt
                            </p>
                            <div className="bg-white dark:bg-gray-800 rounded p-3 text-xs text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700">
                              <p className="font-semibold mb-1">System:</p>
                              <p className="mb-3">{step.input_blob.system_prompt || 'N/A'}</p>
                              <p className="font-semibold mb-1">User:</p>
                              <pre className="whitespace-pre-wrap text-xs">{step.input_blob.user_prompt || 'N/A'}</pre>
                            </div>
                          </div>
                        )}

                        {step.output_blob && (
                          <div className="mt-4">
                            <div className="flex justify-between items-center mb-2">
                              <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                                Output
                              </p>
                              <button
                                onClick={() => copyToClipboard(step.output_blob || '')}
                                className="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                              >
                                {copied ? 'Copied!' : 'Copy'}
                              </button>
                            </div>
                            <div className="bg-white dark:bg-gray-800 rounded p-4 border border-gray-200 dark:border-gray-700">
                              <pre className="whitespace-pre-wrap text-sm text-gray-900 dark:text-gray-100">
                                {step.output_blob}
                              </pre>
                            </div>
                          </div>
                        )}

                        <div className="mt-3 text-xs text-gray-500 dark:text-gray-400">
                          Completed: {new Date(step.created_at).toLocaleString()}
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
