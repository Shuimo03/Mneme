<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useApi } from './composables/useApi'
import StatusGrid from './components/StatusGrid.vue'
import ArticleList from './components/ArticleList.vue'
import SchedulerForm from './components/SchedulerForm.vue'
import ActionButtons from './components/ActionButtons.vue'
import type { Article, SchedulerUpdatePayload, StatusResponse } from '@/types/api'

const { loading, fetchStatus, fetchArticles, resetArticles, triggerSync, updateScheduler } = useApi()

const status = ref<StatusResponse | null>(null)
const articles = ref<Article[]>([])
const error = ref<string | null>(null)

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Request failed'
}

async function loadData() {
  error.value = null
  try {
    const [statusData, articlesData] = await Promise.all([
      fetchStatus(),
      fetchArticles()
    ])
    status.value = statusData
    articles.value = articlesData
  } catch (error) {
    error.value = getErrorMessage(error)
  }
}

async function handleRun() {
  error.value = null
  try {
    await triggerSync()
    await loadData()
  } catch (error) {
    error.value = getErrorMessage(error)
  }
}

async function handleRefresh() {
  await loadData()
}

async function handleReset() {
  if (!window.confirm('This will delete all collected articles so they can be fetched again. Continue?')) {
    return
  }

  error.value = null
  try {
    const result = await resetArticles()
    await loadData()
    if (result.deleted === 0) {
      error.value = 'No articles were deleted.'
    }
  } catch (error) {
    error.value = getErrorMessage(error)
  }
}

async function handleSchedulerUpdate(config: SchedulerUpdatePayload) {
  error.value = null
  try {
    await updateScheduler(config)
    await loadData()
  } catch (error) {
    error.value = getErrorMessage(error)
  }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="ambient ambient-left"></div>
  <div class="ambient ambient-right"></div>

  <div class="page relative z-10 max-w-6xl mx-auto px-6 py-14">
    <header class="hero flex justify-between items-center gap-8 mb-2">
      <div class="hero-copy max-w-3xl">
        <h1 class="font-serif tracking-tight mb-3" style="font-size: clamp(2.8rem, 4vw, 4.3rem); line-height: 0.98;">
          Mneme
        </h1>
        <p class="subtitle max-w-2xl text-muted text-lg leading-relaxed m-0">
          Automated information summarization from high-quality sources,
          delivered to your preferred channels.
        </p>
        <div class="hero-tags flex flex-wrap gap-2 mt-6">
          <span class="tag">Anthropic</span>
          <span class="tag">Meta Engineering</span>
          <span class="tag">arXiv</span>
          <span class="tag">Hacker News</span>
        </div>
      </div>

      <div class="hero-actions min-w-64 grid justify-items-end gap-4">
        <ActionButtons
          :loading="loading"
          @run="handleRun"
          @refresh="handleRefresh"
          @reset="handleReset"
        />
        <p class="hero-caption max-w-64 text-right text-muted leading-relaxed m-0">
          Trigger a manual sync or refresh the current status
        </p>
      </div>
    </header>

    <section v-if="error" class="mb-6 p-4 rounded-2xl bg-red-50 border border-red-200 text-red-700">
      <p class="m-0 font-semibold">Error: {{ error }}</p>
    </section>

    <div class="grid flex-wrap gap-6 my-6">
      <div class="panel">
        <div class="panel-header mb-5">
          <p class="badge">Configuration</p>
          <h2 class="font-serif text-2xl mt-1 mb-0">Scheduler</h2>
        </div>
        <SchedulerForm
          v-if="status"
          :scheduler="status.scheduler"
          :loading="loading"
          @update="handleSchedulerUpdate"
        />
      </div>
    </div>

    <div v-if="status" class="status-grid grid grid-cols-2 gap-4 my-6">
      <StatusGrid :status="status" />
    </div>

    <section class="article-section mt-8">
      <div class="section-header flex justify-between items-center mb-4">
        <div>
          <p class="badge">Feed</p>
          <h2 class="font-serif text-2xl mt-1 mb-0">Articles</h2>
        </div>
        <span class="text-muted text-sm">{{ articles.length }} articles</span>
      </div>

      <ArticleList :articles="articles" />
    </section>
  </div>
</template>

<style scoped>
.page {
  padding-bottom: 72px;
}

@media (max-width: 720px) {
  .hero {
    flex-direction: column;
  }

  .page {
    padding: 32px 16px 48px;
  }

  .status-grid {
    grid-template-columns: 1fr;
  }
}
</style>
