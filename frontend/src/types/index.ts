export interface User {
  id: number;
  full_name: string;
  username: string;
  email: string;
}

export interface ParsedStep {
  order: number;
  description: string;
}

export interface ParsedTestCase {
  name: string;
  module?: string;
  priority?: string;
  environment?: string;
  browser?: string;
  total_steps: number;
  steps: ParsedStep[];
}

export interface FileUploadResponse {
  filename: string;
  file_content: string;
  test_cases_count: number;
  total_steps: number;
  test_cases: ParsedTestCase[];
}

export interface ExecutionCreateResponse {
  id: string;
  filename: string;
  status: string;
  total_test_cases: number;
  created_at: string;
}

export interface ScreenshotInfo {
  id: string;
  filename: string;
  execution_id: string;
}

export interface StepResponse {
  id: string;
  order_index: number;
  description: string;
  intent?: string;
  target?: string;
  value?: string;
  status: string;
  error_message?: string;
  duration_ms?: number;
  screenshots: ScreenshotInfo[];
}

export interface TestCaseResponse {
  id: string;
  name: string;
  module?: string;
  priority?: string;
  order_index: number;
  status: string;
  total_steps: number;
  passed_steps: number;
  failed_steps: number;
  steps: StepResponse[];
}

export interface ExecutionResponse {
  id: string;
  filename: string;
  status: string;
  total_test_cases: number;
  passed: number;
  failed: number;
  blocked: number;
  duration_seconds?: number;
  started_at?: string;
  completed_at?: string;
  created_at?: string;
  test_cases: TestCaseResponse[];
}

export interface ExecutionListItem {
  id: string;
  filename: string;
  status: string;
  total_test_cases: number;
  passed: number;
  failed: number;
  duration_seconds?: number;
  created_at?: string;
}

export interface DashboardStats {
  total_executions: number;
  total_test_cases: number;
  passed: number;
  failed: number;
  running: number;
  blocked: number;
  pass_percentage: number;
  fail_percentage: number;
}

export interface ModuleStat {
  module: string;
  total: number;
  passed: number;
  failed: number;
}

export interface DailyTrend {
  date: string;
  executed: number;
  passed: number;
  failed: number;
}

export interface AiConfigResponse {
  configured: boolean;
  provider: string | null;
  model: string | null;
  key_preview: string | null;
}

export interface ExecutionListResponse {
  items: ExecutionListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ExecutionDashboardStats {
  execution_id: string;
  filename: string;
  status: string;
  created_at: string;
  total_test_cases: number;
  executed: number;
  passed: number;
  failed: number;
  blocked: number;
  skipped: number;
  pending: number;
  executed_percentage: number;
  pass_percentage: number;
  fail_percentage: number;
  blocked_percentage: number;
  skipped_percentage: number;
  pending_percentage: number;
  pass_rate_of_executed: number;
  started_at: string | null;
  completed_at: string | null;
  duration: string | null;
  duration_seconds: number | null;
  test_cases: ExecutionDashboardTestCase[];
  module_breakdown: ExecutionModuleBreakdown[];
}

export interface ExecutionDashboardTestCase {
  id: string;
  name: string;
  module?: string;
  priority?: string;
  status: string;
  total_steps: number;
  passed_steps: number;
  failed_steps: number;
  error_message?: string;
}

export interface ExecutionModuleBreakdown {
  module: string;
  total: number;
  passed: number;
  failed: number;
  pending: number;
  blocked: number;
  pass_pct: number;
}

export interface SSEEvent {
  type: string;
  execution_id?: string;
  test_case_index?: number;
  test_case_name?: string;
  step_order?: number;
  step_description?: string;
  intent?: string;
  status?: string;
  error?: string;
  screenshot_id?: string;
  screenshot_filename?: string;
  duration_ms?: number;
  passed?: number;
  failed?: number;
  blocked?: number;
  total_test_cases?: number;
  total_steps?: number;
}
