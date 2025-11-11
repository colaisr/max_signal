'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useRequireAuth } from '@/hooks/useAuth'
import Link from 'next/link'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

interface Instrument {
  symbol: string
  type: string
  exchange: string | null
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
}

async function fetchInstruments() {
  const { data } = await axios.get<Instrument[]>(`${API_BASE_URL}/api/instruments`)
  return data
}

async function fetchRuns() {
  const { data } = await axios.get<Run[]>(`${API_BASE_URL}/api/runs?limit=10`)
  return data
}

async function createRun(instrument: string, timeframe: string) {
  const { data } = await axios.post(`${API_BASE_URL}/api/runs`, {
    instrument,
    timeframe,
  })
  return data
}

export default function DashboardPage() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const { isLoading: authLoading } = useRequireAuth()
  
  const [selectedInstrument, setSelectedInstrument] = useState<string>('')
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>('H1')

  const { data: instruments = [], isLoading: instrumentsLoading, error: instrumentsError } = useQuery({
    queryKey: ['instruments'],
    queryFn: fetchInstruments,
  })

  const { data: runs = [], isLoading: runsLoading } = useQuery({
    queryKey: ['runs'],
    queryFn: fetchRuns,
    refetchInterval: 5000, // Poll every 5 seconds
  })

  const createRunMutation = useMutation({
    mutationFn: ({ instrument, timeframe }: { instrument: string; timeframe: string }) =>
      createRun(instrument, timeframe),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['runs'] })
      router.push(`/runs/${data.id}`)
    },
  })

  const handleRunAnalysis = () => {
    if (!selectedInstrument) {
      alert('Please select an instrument')
      return
    }
    createRunMutation.mutate({
      instrument: selectedInstrument,
      timeframe: selectedTimeframe,
    })
  }

  const timeframes = [
    { value: 'M1', label: '1 Minute' },
    { value: 'M5', label: '5 Minutes' },
    { value: 'M15', label: '15 Minutes' },
    { value: 'H1', label: '1 Hour' },
    { value: 'D1', label: '1 Day' },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'succeeded':
        return 'text-green-600 dark:text-green-400'
      case 'failed':
        return 'text-red-600 dark:text-red-400'
      case 'running':
        return 'text-blue-600 dark:text-blue-400'
      default:
        return 'text-gray-600 dark:text-gray-400'
    }
  }

  if (authLoading) {
    return (
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          <p className="text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 text-gray-900 dark:text-white">
          <span className="text-gray-900 dark:text-white">Max Sig</span><span className="text-5xl text-blue-600 dark:text-blue-400 font-bold">N</span><span className="text-gray-900 dark:text-white">al bot</span>
        </h1>

        {/* Run Analysis Form */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
            Run Analysis
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                Instrument
              </label>
              <select
                value={selectedInstrument}
                onChange={(e) => setSelectedInstrument(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                disabled={instrumentsLoading}
              >
                <option value="">Select instrument...</option>
                {instrumentsLoading ? (
                  <option disabled>Loading instruments...</option>
                ) : (
                  instruments.map((inst) => (
                    <option key={inst.symbol} value={inst.symbol}>
                      {inst.symbol} ({inst.type})
                    </option>
                  ))
                )}
              </select>
              {instrumentsError && (
                <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                  Failed to load instruments
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                Timeframe
              </label>
              <select
                value={selectedTimeframe}
                onChange={(e) => setSelectedTimeframe(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                {timeframes.map((tf) => (
                  <option key={tf.value} value={tf.value}>
                    {tf.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={handleRunAnalysis}
                disabled={!selectedInstrument || createRunMutation.isPending}
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-md font-medium transition-colors"
              >
                {createRunMutation.isPending ? 'Creating...' : 'Run Analysis'}
              </button>
            </div>
          </div>

          <div className="mt-4">
            <Link
              href="/analyses"
              className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 text-sm font-medium"
            >
              → Or choose from available analysis types
            </Link>
          </div>
        </div>

        {/* Recent Runs */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
            Recent Runs
          </h2>

          {runsLoading ? (
            <p className="text-gray-600 dark:text-gray-400">Loading runs...</p>
          ) : runs.length === 0 ? (
            <p className="text-gray-600 dark:text-gray-400">
              No runs yet. Start your first analysis above!
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Instrument
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Timeframe
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Cost
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {runs.map((run) => (
                    <tr key={run.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                        {run.instrument}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {run.timeframe}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`text-sm font-medium ${getStatusColor(run.status)}`}>
                          {run.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {new Date(run.created_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        ${run.cost_est_total.toFixed(3)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <Link
                          href={`/runs/${run.id}`}
                          className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
                        >
                          View →
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

