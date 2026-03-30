<script setup lang="ts">
import { ref, watch } from 'vue'
import type { SchedulerState, SchedulerUpdatePayload } from '@/types/api'

const props = withDefaults(defineProps<{
  scheduler: SchedulerState
  loading?: boolean
}>(), {
  loading: false
})

const emit = defineEmits<{
  (event: 'update', payload: SchedulerUpdatePayload): void
}>()

const enabled = ref(props.scheduler.enabled)
const hour = ref(props.scheduler.hour)
const minute = ref(props.scheduler.minute)

watch(() => props.scheduler, (newScheduler) => {
  enabled.value = newScheduler.enabled
  hour.value = newScheduler.hour
  minute.value = newScheduler.minute
}, { deep: true })

async function handleSubmit() {
  emit('update', {
    enabled: enabled.value,
    hour: Number(hour.value),
    minute: Number(minute.value)
  })
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="stack grid gap-4">
    <div class="checkbox-row flex items-center gap-4">
      <label class="flex items-center gap-3 cursor-pointer">
        <input
          v-model="enabled"
          type="checkbox"
          class="accent-accent w-5 h-5"
        />
        <span class="font-semibold text-accent">Enable scheduled sync</span>
      </label>
    </div>

    <div class="time-grid flex flex-wrap gap-4">
      <div class="flex-1 min-w-24">
        <label class="block text-sm text-muted mb-2">Hour</label>
        <input
          v-model.number="hour"
          type="number"
          min="0"
          max="23"
          class="w-full p-3 rounded-xl border border-border bg-panel-strong text-base"
        />
      </div>
      <div class="flex-1 min-w-24">
        <label class="block text-sm text-muted mb-2">Minute</label>
        <input
          v-model.number="minute"
          type="number"
          min="0"
          max="59"
          class="w-full p-3 rounded-xl border border-border bg-panel-strong text-base"
        />
      </div>
    </div>

    <button
      type="submit"
      class="secondary-button w-full"
      :disabled="loading"
    >
      {{ loading ? 'Saving...' : 'Save schedule' }}
    </button>
  </form>
</template>

<style scoped>
.stack {
  display: grid;
  gap: 16px;
}

.time-grid {
  flex-wrap: wrap;
}

input[type="number"] {
  width: 100%;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: var(--panel-strong);
  font-size: 1rem;
}

input[type="checkbox"] {
  accent-color: var(--accent);
}
</style>
