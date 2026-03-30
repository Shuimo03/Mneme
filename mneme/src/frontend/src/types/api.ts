export type IsoDatetime = string

export interface Article {
  id: string
  source: string
  source_type: string
  title: string
  published_at: IsoDatetime | null
  url: string
  external_id: string | null
  raw_content: string
  summary: string
  source_summary: string
  chinese_summary: string
  bullets: string[]
  tags: string[]
  reading_recommendation: string
  created_at: IsoDatetime
  notified_at: IsoDatetime | null
}

export interface SchedulerState {
  enabled: boolean
  hour: number
  minute: number
  timezone: string
}

export interface SchedulerUpdatePayload {
  enabled: boolean
  hour: number
  minute: number
}

export interface RunRecord {
  started_at: IsoDatetime
  finished_at: IsoDatetime
  status: string
  trigger: string
  message: string
  processed_count: number
  notified_channels: number
}

export interface StatusCapabilities {
  anthropic_configured: boolean
  telegram_enabled: boolean
  feishu_enabled: boolean
}

export interface StatusResponse {
  scheduler: SchedulerState
  last_run: RunRecord | null
  capabilities: StatusCapabilities
}

export interface SchedulerResponse {
  scheduler: SchedulerState
}

export interface RunResponse {
  run: RunRecord
}

export interface ResetArticlesResponse {
  deleted: number
}
