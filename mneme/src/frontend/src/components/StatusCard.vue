<script setup lang="ts">
withDefaults(defineProps<{
  label: string
  title: string
  description?: string
}>(), {
  description: ''
})
</script>

<template>
  <article class="status-card">
    <span class="badge">{{ label }}</span>
    <strong>{{ title }}</strong>
    <p>{{ description }}</p>
  </article>
</template>
