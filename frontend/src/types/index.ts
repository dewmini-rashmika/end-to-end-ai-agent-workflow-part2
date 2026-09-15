// ── Auth ──────────────────────────────────────────────────────────────────────
export interface User {
  id: string
  email: string
  username: string
  full_name: string | null
  avatar_url: string | null
  is_verified: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  username: string
  password: string
  full_name?: string
}

// ── Thread / History ──────────────────────────────────────────────────────────
export interface ThreadSummary {
  id: string
  title: string | null
  status: ThreadStatus
  hitl_status: HitlStatus | null
  created_at: string
  updated_at: string
  destination: string | null
  departure_date: string | null
}

export interface Message {
  id: string
  role: MessageRole
  content: string
  agent_name: string | null
  created_at: string
  metadata: Record<string, unknown> | null
  model_used: string | null
}

export interface ThreadDetail {
  id: string
  title: string | null
  status: ThreadStatus
  hitl_status: HitlStatus | null
  hitl_feedback: string | null
  travel_state: TravelState | null
  messages: Message[]
  created_at: string
  updated_at: string
}

export interface ThreadListResponse {
  threads: ThreadSummary[]
  total: number
  page: number
  page_size: number
}

export type ThreadStatus =
  | 'active'
  | 'awaiting_hitl'
  | 'completed'
  | 'rejected'
  | 'error'

export type HitlStatus =
  | 'pending'
  | 'approved'
  | 'changes_requested'
  | 'rejected'

export type MessageRole =
  | 'user'
  | 'assistant'
  | 'system'
  | 'tool'
  | 'agent'
  | 'hitl'

// ── Trip Planning ─────────────────────────────────────────────────────────────
export interface PlanTripRequest {
  user_input: string
}

export interface TripConstraints {
  origin: string | null
  destination: string | null
  departure_date: string | null
  return_date: string | null
  duration_days: number | null
  travelers: number
  budget_usd: number | null
  budget_level: 'budget' | 'mid' | 'luxury'
  interests: string[]
  accommodation_type: string
}

export interface AgentResult {
  agent_name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  error: string | null
  prompt_tokens: number
  completion_tokens: number
  model_used: string | null
}

export interface TravelState {
  thread_id: string
  user_input: string
  selected_agents: string[]
  trip_constraints: TripConstraints
  supervisor_reasoning: string | null
  flight_results: FlightResults | null
  hotel_results: HotelResults | null
  weather_results: WeatherResults | null
  budget_analysis: BudgetAnalysis | null
  itinerary_plan: ItineraryPlan | null
  rag_context: string | null
  agent_results: AgentResult[]
  hitl_status: HitlStatus | null
  hitl_feedback: string | null
  final_response: string | null
  is_complete: boolean
}

export interface PlanResponse {
  status: 'awaiting_review' | 'blocked' | 'completed' | 'error' | 'rejected'
  thread_id: string | null
  reason: string | null
  risk_level: string | null
  hitl_payload: HitlPayload | null
  final_response: string | null
  message: string | null
}

// ── Agent Results ─────────────────────────────────────────────────────────────
export interface FlightOption {
  flight_number: string
  airline: string
  origin: string
  destination: string
  departure_time: string
  arrival_time: string
  duration_minutes: number
  stops: number
  price_per_person_usd: number
  total_price_usd: number
  cabin_class: string
  value_score: number
}

export interface FlightResults {
  flights: FlightOption[]
  total_found: number
  origin: string
  destination: string
}

export interface HotelOption {
  name: string
  url: string | null
  star_rating: number
  price_per_night_usd: number
  total_price_usd: number
  check_in: string
  check_out: string
  nights: number
  free_cancellation: boolean
  description: string
}

export interface HotelResults {
  hotels: HotelOption[]
  destination: string
  nights: number
}

export interface DayForecast {
  date: string
  condition: string
  description: string
  temp_min_c: number
  temp_max_c: number
  humidity_pct: number
  precipitation_chance_pct: number
  uv_index: number
}

export interface WeatherResults {
  daily_forecast: DayForecast[]
  packing_suggestions: string[]
  activity_warnings: string[]
  destination: string
}

export interface BudgetAnalysis {
  total_estimated_usd: number
  breakdown: Record<string, number>
  budget_status: 'within_budget' | 'over_budget' | 'under_budget' | 'no_budget_set'
  budget_gap_usd: number | null
  savings_tips: string[]
  cost_per_person_usd: number
  local_currency: string
  total_estimated_local: number
}

export interface ItineraryDay {
  date: string
  morning: string
  afternoon: string
  evening: string
  meals: string
  transport: string
  estimated_day_cost_usd: number
}

export interface ItineraryPlan {
  summary: string
  days: ItineraryDay[]
  total_trip_cost_usd: number
}

// ── HITL ──────────────────────────────────────────────────────────────────────
export interface HitlPayload {
  thread_id: string
  hitl_status: HitlStatus
  itinerary_plan: ItineraryPlan | null
  flight_results: FlightResults | null
  hotel_results: HotelResults | null
  weather_results: WeatherResults | null
  budget_analysis: BudgetAnalysis | null
  trip_constraints: TripConstraints
  supervisor_reasoning: string | null
  agent_results: AgentResult[]
  selected_agents?: string[]
}

export interface HITLDecisionRequest {
  thread_id: string
  decision: 'approve' | 'request_changes' | 'reject'
  feedback: string
  change_agents: string[]
}

// ── SSE Events ────────────────────────────────────────────────────────────────
export type SSEEvent =
  | { type: 'status'; status: ThreadStatus; thread_id: string }
  | { type: 'message'; role: MessageRole; content: string; agent_name: string | null; created_at: string }
  | { type: 'hitl_required'; thread_id: string; hitl_status: HitlStatus }
  | { type: 'complete'; final_response: string }
  | { type: 'end'; status: ThreadStatus }
  | { type: 'timeout' }
