'use client'

import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

async function fetchHealth() {
  const { data } = await axios.get(`${API_BASE_URL}/health`)
  return data
}

export default function Home() {
  const { data: health, isLoading } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
  })

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">Max Signal Bot</h1>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <h2 className="text-2xl font-semibold mb-4">System Status</h2>
          {isLoading ? (
            <p>Loading...</p>
          ) : health ? (
            <div>
              <p className="text-green-600 dark:text-green-400">✓ Backend connected</p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                Status: {health.status} | Service: {health.service}
              </p>
            </div>
          ) : (
            <p className="text-red-600 dark:text-red-400">✗ Backend not connected</p>
          )}
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-2xl font-semibold mb-4">Dashboard</h2>
          <p className="text-gray-600 dark:text-gray-400">
            Daystart analysis trigger and run history will be here.
          </p>
        </div>
      </div>
    </main>
  )
}

