import { ref } from 'vue'
import type {
  Article,
  ResetArticlesResponse,
  RunResponse,
  SchedulerResponse,
  SchedulerUpdatePayload,
  StatusResponse
} from '@/types/api'

export function useApi() {
  const loading = ref(false)
  const error = ref<string | null>(null)

  function getErrorMessage(error: unknown): string {
    return error instanceof Error ? error.message : 'Request failed'
  }

  async function fetchJson<T>(url: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      ...options
    })
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`)
    }
    return response.json() as Promise<T>
  }

  async function fetchStatus(): Promise<StatusResponse> {
    return fetchJson<StatusResponse>('/api/status')
  }

  async function fetchArticles(): Promise<Article[]> {
    return fetchJson<Article[]>('/api/articles')
  }

  async function resetArticles(): Promise<ResetArticlesResponse> {
    loading.value = true
    error.value = null
    try {
      return await fetchJson<ResetArticlesResponse>('/api/articles', { method: 'DELETE' })
    } catch (error) {
      error.value = getErrorMessage(error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function triggerSync(): Promise<RunResponse> {
    loading.value = true
    error.value = null
    try {
      return await fetchJson<RunResponse>('/api/runs/sync', { method: 'POST' })
    } catch (error) {
      error.value = getErrorMessage(error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function updateScheduler(config: SchedulerUpdatePayload): Promise<SchedulerResponse> {
    loading.value = true
    error.value = null
    try {
      return await fetchJson<SchedulerResponse>('/api/scheduler', {
        method: 'POST',
        body: JSON.stringify(config)
      })
    } catch (error) {
      error.value = getErrorMessage(error)
      throw error
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    fetchStatus,
    fetchArticles,
    resetArticles,
    triggerSync,
    updateScheduler
  }
}
