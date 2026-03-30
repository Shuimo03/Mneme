<script setup lang="ts">
import ArticleCard from './ArticleCard.vue'
import type { Article } from '@/types/api'

withDefaults(defineProps<{
  articles?: Article[]
}>(), {
  articles: () => []
})
</script>

<template>
  <div v-if="articles.length === 0" class="empty-state text-muted py-6">
    <p>No articles collected yet.</p>
  </div>
  <div v-else class="article-list grid gap-4">
    <ArticleCard
      v-for="article in articles"
      :key="article.id"
      :article="article"
    />
  </div>
</template>

<style scoped>
.article-list {
  display: grid;
  gap: 18px;
}
</style>
