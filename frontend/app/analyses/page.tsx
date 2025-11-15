'use client'

import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { API_BASE_URL } from '@/lib/config'

interface AnalysisType {
  id: number
  name: string
  display_name: string
  description: string | null
  version: string
  config: {
    steps: Array<{
      step_name: string
      step_type: string
      model: string
      system_prompt: string
      user_prompt_template: string
      temperature: number
      max_tokens: number
      data_sources: string[]
    }>
    default_instrument: string
    default_timeframe: string
    estimated_cost: number
    estimated_duration_seconds: number
  }
  is_active: number
  created_at: string
  updated_at: string
}

async function fetchAnalysisTypes() {
  const { data } = await axios.get<AnalysisType[]>(`${API_BASE_URL}/api/analyses`)
  return data
}

export default function AnalysesPage() {
  const router = useRouter()
  const { data: analysisTypes = [], isLoading, error } = useQuery({
    queryKey: ['analysis-types'],
    queryFn: fetchAnalysisTypes,
  })

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          <p className="text-gray-600 dark:text-gray-400">Loading analyses...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-700 rounded p-4">
            <p className="text-red-700 dark:text-red-400">
              Error loading analyses: {error instanceof Error ? error.message : 'Unknown error'}
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
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            Analysis Types
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Browse and configure available analysis pipelines
          </p>
        </div>

        {analysisTypes.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <p className="text-gray-600 dark:text-gray-400">No analysis types available.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {analysisTypes.map((analysis) => (
              <div
                key={analysis.id}
                className="bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-lg transition-shadow p-6 flex flex-col"
              >
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-1">
                      {analysis.display_name}
                    </h3>
                    <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-gray-600 dark:text-gray-400">
                      v{analysis.version}
                    </span>
                  </div>
                </div>

                {analysis.description && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                    {analysis.description}
                  </p>
                )}

                <div className="space-y-2 mb-4 flex-grow">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500 dark:text-gray-400">Steps:</span>
                    <span className="text-gray-900 dark:text-white font-medium">
                      {analysis.config.steps.length}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500 dark:text-gray-400">Estimated Cost:</span>
                    <span className="text-gray-900 dark:text-white font-medium">
                      ${analysis.config.estimated_cost.toFixed(3)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500 dark:text-gray-400">Duration:</span>
                    <span className="text-gray-900 dark:text-white font-medium">
                      ~{Math.round(analysis.config.estimated_duration_seconds / 60)} min
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500 dark:text-gray-400">Default Timeframe:</span>
                    <span className="text-gray-900 dark:text-white font-medium">
                      {analysis.config.default_timeframe}
                    </span>
                  </div>
                </div>

                <div className="flex gap-2 mt-auto">
                  <Link
                    href={`/analyses/${analysis.id}`}
                    className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium text-center transition-colors"
                  >
                    Configure
                  </Link>
                  <button
                    onClick={() => router.push(`/runs?analysis_type_id=${analysis.id}`)}
                    className="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-md text-sm font-medium transition-colors"
                  >
                    View History
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

