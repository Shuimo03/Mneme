<script setup lang="ts">
import { computed } from 'vue'
import StatusCard from './StatusCard.vue'
import type { StatusResponse } from '@/types/api'

const props = defineProps<{
  status: StatusResponse
}>()

const scheduler = computed(() => props.status.scheduler)
const lastRun = computed(() => props.status.last_run)
const capabilities = computed(() => props.status.capabilities)

const scheduleCard = computed(() => ({
  label: 'Schedule',
  title: scheduler.value.enabled ? 'Enabled' : 'Disabled',
  description: scheduler.value.enabled
    ? `${String(scheduler.value.hour).padStart(2, '0')}:${String(scheduler.value.minute).padStart(2, '0')} - ${scheduler.value.timezone}`
    : 'Not scheduled'
}))

const lastRunCard = computed(() => ({
  label: 'Last Run',
  title: lastRun.value ? lastRun.value.status : 'No run yet',
  description: lastRun.value ? lastRun.value.message : 'Waiting for the first sync.'
}))

const anthropicCard = computed(() => ({
  label: 'Anthropic',
  title: capabilities.value.anthropic_configured ? 'Configured' : 'Fallback mode',
  description: capabilities.value.anthropic_configured
    ? 'Claude summaries enabled.'
    : 'Local fallback summaries in use.'
}))

const deliveryCard = computed(() => ({
  label: 'Delivery',
  title: capabilities.value.telegram_enabled || capabilities.value.feishu_enabled ? 'Ready' : 'Disabled',
  description: `Telegram: ${capabilities.value.telegram_enabled ? 'on' : 'off'} - Feishu: ${capabilities.value.feishu_enabled ? 'on' : 'off'}`
}))
</script>

<template>
  <StatusCard
    :label="scheduleCard.label"
    :title="scheduleCard.title"
    :description="scheduleCard.description"
  />
  <StatusCard
    :label="lastRunCard.label"
    :title="lastRunCard.title"
    :description="lastRunCard.description"
  />
  <StatusCard
    :label="anthropicCard.label"
    :title="anthropicCard.title"
    :description="anthropicCard.description"
  />
  <StatusCard
    :label="deliveryCard.label"
    :title="deliveryCard.title"
    :description="deliveryCard.description"
  />
</template>
