<script setup lang="ts">
import { computed } from 'vue'
import type { Article } from '@/types/api'

const props = defineProps<{
  article: Article
}>()

const sourceSummary = computed(() => props.article.source_summary || props.article.summary)
const chineseSummary = computed(() => props.article.chinese_summary)
</script>

<template>
  <article class="article-card">
    <header class="grid gap-1 mb-3">
      <p class="badge">{{ article.source }}</p>
      <a
        :href="article.url"
        target="_blank"
        rel="noreferrer"
        class="font-serif text-2xl text-text no-underline"
      >
        {{ article.title }}
      </a>
    </header>
    <section v-if="sourceSummary" class="summary-block">
      <p class="summary-label">Original Summary</p>
      <p class="leading-relaxed m-0">
        {{ sourceSummary }}
      </p>
    </section>
    <section v-if="chineseSummary" class="summary-block">
      <p class="summary-label">中文解释</p>
      <p class="leading-relaxed m-0">
        {{ chineseSummary }}
      </p>
    </section>
    <ul v-if="article.bullets && article.bullets.length" class="bullet-list">
      <li v-for="(bullet, index) in article.bullets" :key="index">
        {{ bullet }}
      </li>
    </ul>
    <div v-if="article.tags && article.tags.length" class="tag-row flex flex-wrap gap-2 mt-3">
      <span v-for="tag in article.tags" :key="tag" class="tag">
        {{ tag }}
      </span>
    </div>
  </article>
</template>

<style scoped>
.summary-block + .summary-block {
  margin-top: 14px;
}

.summary-label {
  margin: 0 0 6px;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted);
}
</style>
