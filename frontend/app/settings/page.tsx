'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { useState, useEffect, useRef } from 'react'
import { useRequireAuth, useAuth } from '@/hooks/useAuth'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

interface Model {
  id: number
  name: string
  display_name: string
  provider: string
  description: string | null
  max_tokens: number | null
  cost_per_1k_tokens: string | null
  is_enabled: boolean
}

interface DataSource {
  id: number
  name: string
  display_name: string
  description: string | null
  supports_crypto: boolean
  supports_stocks: boolean
  supports_forex: boolean
  is_enabled: boolean
}

async function fetchModels() {
  const { data } = await axios.get<Model[]>(`${API_BASE_URL}/api/settings/models`)
  return data
}

async function fetchDataSources() {
  const { data } = await axios.get<DataSource[]>(`${API_BASE_URL}/api/settings/data-sources`)
  return data
}

async function fetchTelegramSettings() {
  const { data } = await axios.get(`${API_BASE_URL}/api/settings/telegram`, {
    withCredentials: true
  })
  return data
}

async function fetchOpenRouterSettings() {
  const { data } = await axios.get(`${API_BASE_URL}/api/settings/openrouter`, {
    withCredentials: true
  })
  return data
}

async function updateModel(id: number, is_enabled: boolean) {
  const { data } = await axios.put(
    `${API_BASE_URL}/api/settings/models/${id}`,
    { is_enabled },
    { withCredentials: true }
  )
  return data
}

async function updateDataSource(id: number, is_enabled: boolean) {
  const { data } = await axios.put(
    `${API_BASE_URL}/api/settings/data-sources/${id}`,
    { is_enabled },
    { withCredentials: true }
  )
  return data
}

async function updateTelegramSettings(bot_token: string | null, channel_id: string | null) {
  const { data } = await axios.put(
    `${API_BASE_URL}/api/settings/telegram`,
    { bot_token, channel_id },
    { withCredentials: true }
  )
  return data
}

async function updateOpenRouterSettings(api_key: string | null) {
  const { data } = await axios.put(
    `${API_BASE_URL}/api/settings/openrouter`,
    { api_key },
    { withCredentials: true }
  )
  return data
}

export default function SettingsPage() {
  const { isLoading: authLoading } = useRequireAuth()
  const { isAdmin } = useAuth()
  const queryClient = useQueryClient()
  
  const [telegramBotToken, setTelegramBotToken] = useState('')
  const [telegramChannelId, setTelegramChannelId] = useState('')
  const [openRouterKey, setOpenRouterKey] = useState('')
  const telegramInitialized = useRef(false)
  const openRouterInitialized = useRef(false)

  const { data: models = [], isLoading: modelsLoading } = useQuery({
    queryKey: ['settings', 'models'],
    queryFn: fetchModels,
  })

  const { data: dataSources = [], isLoading: dataSourcesLoading } = useQuery({
    queryKey: ['settings', 'data-sources'],
    queryFn: fetchDataSources,
  })

  const { data: telegramSettings } = useQuery({
    queryKey: ['settings', 'telegram'],
    queryFn: fetchTelegramSettings,
    enabled: !authLoading,
  })

  const { data: openRouterSettings } = useQuery({
    queryKey: ['settings', 'openrouter'],
    queryFn: fetchOpenRouterSettings,
    enabled: !authLoading,
  })

  // Initialize form values from API
  useEffect(() => {
    if (telegramSettings && !telegramInitialized.current) {
      if (telegramSettings.bot_token) {
        setTelegramBotToken(telegramSettings.bot_token)
      }
      if (telegramSettings.channel_id) {
        setTelegramChannelId(telegramSettings.channel_id)
      }
      telegramInitialized.current = true
    }
  }, [telegramSettings])

  useEffect(() => {
    if (openRouterSettings?.api_key && !openRouterInitialized.current) {
      setOpenRouterKey(openRouterSettings.api_key)
      openRouterInitialized.current = true
    }
  }, [openRouterSettings])

  const updateModelMutation = useMutation({
    mutationFn: ({ id, is_enabled }: { id: number; is_enabled: boolean }) =>
      updateModel(id, is_enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'models'] })
    },
  })

  const updateDataSourceMutation = useMutation({
    mutationFn: ({ id, is_enabled }: { id: number; is_enabled: boolean }) =>
      updateDataSource(id, is_enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'data-sources'] })
    },
  })

  const updateTelegramMutation = useMutation({
    mutationFn: () => updateTelegramSettings(telegramBotToken || null, telegramChannelId || null),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'telegram'] })
      alert('Telegram settings saved!')
    },
  })

  const updateOpenRouterMutation = useMutation({
    mutationFn: () => updateOpenRouterSettings(openRouterKey || null),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'openrouter'] })
      alert('OpenRouter settings saved!')
    },
  })

  if (authLoading) {
    return (
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          <p className="text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAdmin) {
    return (
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-700 rounded p-4">
            <p className="text-red-700 dark:text-red-400">
              Admin access required to view settings.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 text-gray-900 dark:text-white">
          Settings
        </h1>

        {/* Available Models Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
            Available Models
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Enable or disable LLM models. Only enabled models will appear in analysis configuration dropdowns.
          </p>

          {modelsLoading ? (
            <p className="text-gray-600 dark:text-gray-400">Loading models...</p>
          ) : (
            <div className="space-y-4">
              {models.map((model) => (
                <div
                  key={model.id}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {model.display_name}
                        </h3>
                        <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-gray-600 dark:text-gray-400">
                          {model.provider}
                        </span>
                        <span className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900/30 rounded text-blue-600 dark:text-blue-400">
                          {model.name}
                        </span>
                      </div>
                      {model.description && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                          {model.description}
                        </p>
                      )}
                      <div className="flex gap-4 text-xs text-gray-500 dark:text-gray-400">
                        {model.max_tokens && (
                          <span>Max tokens: {model.max_tokens.toLocaleString()}</span>
                        )}
                        {model.cost_per_1k_tokens && (
                          <span>Cost: {model.cost_per_1k_tokens}/1k tokens</span>
                        )}
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer ml-4">
                      <input
                        type="checkbox"
                        checked={model.is_enabled}
                        onChange={(e) =>
                          updateModelMutation.mutate({ id: model.id, is_enabled: e.target.checked })
                        }
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Available Data Sources Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
            Available Data Sources
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Enable or disable data sources. Only enabled sources will appear in analysis configuration dropdowns.
          </p>

          {dataSourcesLoading ? (
            <p className="text-gray-600 dark:text-gray-400">Loading data sources...</p>
          ) : (
            <div className="space-y-4">
              {dataSources.map((source) => (
                <div
                  key={source.id}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {source.display_name}
                        </h3>
                        <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-gray-600 dark:text-gray-400">
                          {source.name}
                        </span>
                      </div>
                      {source.description && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                          {source.description}
                        </p>
                      )}
                      <div className="flex gap-2 text-xs">
                        {source.supports_crypto && (
                          <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 rounded text-green-700 dark:text-green-400">
                            Crypto
                          </span>
                        )}
                        {source.supports_stocks && (
                          <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 rounded text-blue-700 dark:text-blue-400">
                            Stocks
                          </span>
                        )}
                        {source.supports_forex && (
                          <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 rounded text-purple-700 dark:text-purple-400">
                            Forex
                          </span>
                        )}
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer ml-4">
                      <input
                        type="checkbox"
                        checked={source.is_enabled}
                        onChange={(e) =>
                          updateDataSourceMutation.mutate({ id: source.id, is_enabled: e.target.checked })
                        }
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Telegram Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
            Telegram Configuration
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Configure Telegram bot token and channel ID for publishing analysis results.
          </p>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                Bot Token
              </label>
              <input
                type="password"
                value={telegramBotToken}
                onChange={(e) => setTelegramBotToken(e.target.value)}
                placeholder="Get from @BotFather"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
              {telegramSettings?.bot_token_masked && (
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  Current: {telegramSettings.bot_token_masked}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                Channel ID
              </label>
              <input
                type="text"
                value={telegramChannelId}
                onChange={(e) => setTelegramChannelId(e.target.value)}
                placeholder="@your_channel or -1001234567890"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            <button
              onClick={() => updateTelegramMutation.mutate()}
              disabled={updateTelegramMutation.isPending}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-md font-medium transition-colors"
            >
              {updateTelegramMutation.isPending ? 'Saving...' : 'Save Telegram Settings'}
            </button>
          </div>
        </div>

        {/* OpenRouter Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-white">
            OpenRouter Configuration
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Configure your OpenRouter API key for LLM model access.
          </p>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
                API Key
              </label>
              <input
                type="password"
                value={openRouterKey}
                onChange={(e) => setOpenRouterKey(e.target.value)}
                placeholder="Get from https://openrouter.ai"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
              {openRouterSettings?.api_key_masked && (
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  Current: {openRouterSettings.api_key_masked}
                </p>
              )}
            </div>

            <button
              onClick={() => updateOpenRouterMutation.mutate()}
              disabled={updateOpenRouterMutation.isPending}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-md font-medium transition-colors"
            >
              {updateOpenRouterMutation.isPending ? 'Saving...' : 'Save OpenRouter Settings'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

