'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

interface User {
  id: number
  email: string
  full_name: string | null
  is_admin: boolean
  created_at: string
}

async function getCurrentUser() {
  try {
    const { data } = await axios.get<User>(`${API_BASE_URL}/api/auth/me`, {
      withCredentials: true
    })
    return data
  } catch (error: any) {
    // If 401, user is not authenticated - this is expected
    if (error.response?.status === 401) {
      return null
    }
    throw error
  }
}

async function logout() {
  await axios.post(`${API_BASE_URL}/api/auth/logout`, {}, {
    withCredentials: true
  })
}

export function useAuth() {
  const router = useRouter()
  const queryClient = useQueryClient()

  const { data: user, isLoading, error } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: getCurrentUser,
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
    refetchOnMount: true,
  })

  const logoutMutation = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.clear()
      router.push('/login')
    },
  })

  const isAuthenticated = !!user && !error
  const isAdmin = user?.is_admin || false

  return {
    user,
    isLoading,
    isAuthenticated,
    isAdmin,
    logout: () => logoutMutation.mutate(),
  }
}

export function useRequireAuth() {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isAuthenticated, isLoading, router])

  return { isAuthenticated, isLoading }
}

