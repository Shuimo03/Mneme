<script setup lang="ts">
withDefaults(defineProps<{
  loading?: boolean
}>(), {
  loading: false
})

const emit = defineEmits<{
  (event: 'run'): void
  (event: 'refresh'): void
  (event: 'reset'): void
}>()
</script>

<template>
  <div class="action-buttons flex gap-3 flex-wrap">
    <button
      class="primary-button"
      :disabled="loading"
      @click="emit('run')"
    >
      {{ loading ? 'Running...' : 'Run now' }}
    </button>
    <button
      class="secondary-button"
      :disabled="loading"
      @click="emit('refresh')"
    >
      Refresh
    </button>
    <button
      class="danger-button"
      :disabled="loading"
      @click="emit('reset')"
    >
      Reset
    </button>
  </div>
</template>
