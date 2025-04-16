
// Tool Types
export interface Tool {
  tool_id: string;
  name: string;
  description: string;
  api_endpoint: string;
  version: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface ToolDetails extends Tool {
  auth_method: string;
  auth_config: Record<string, any>;
  params: Record<string, {
    type: string;
    required: boolean;
    description?: string;
    default?: any;
    allowed_values?: any[];
  }>;
  owner_id: string;
  is_active: boolean;
}

// Policy Types
export interface Policy {
  policy_id: string;
  name: string;
  description: string;
  tool_id: string;
  allowed_scopes: string[];
  conditions: {
    max_requests_per_day?: number;
    allowed_hours?: {
      start: string;
      end: string;
    };
  };
  rules: {
    require_approval: boolean;
    log_usage: boolean;
  };
  priority: number;
  created_at: string;
  updated_at: string;
}

// Agent Types
export interface Agent {
  agent_id: string;
  name: string;
  description: string;
  agent_type: "user" | "service" | "bot";
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

// Access Control Types
export interface AccessRequest {
  request_id: string;
  agent_id: string;
  tool_id: string;
  policy_id: string;
  justification: string;
  status: "pending" | "approved" | "rejected";
  created_at: string;
}

export interface AccessValidation {
  has_access: boolean;
  agent_id: string;
  tool_id: string;
  allowed_scopes: string[];
  policy_id: string;
  policy_name: string;
}

// Credential Types
export interface Credential {
  credential_id: string;
  agent_id: string;
  tool_id: string;
  credential_type: string;
  expires_at: string;
  created_at: string;
}

// Usage Log Types
export interface UsageLog {
  log_id: string;
  agent_id: string;
  tool_id: string;
  timestamp: string;
  duration_ms: number;
  status: "success" | "error";
  error_message?: string;
}

export interface UsageStats {
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  average_duration_ms: number;
  by_period: Array<{
    period: string;
    requests: number;
    success_rate: number;
  }>;
  by_tool: Array<{
    tool_id: string;
    tool_name: string;
    requests: number;
    success_rate: number;
  }>;
}

// Pagination Types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}
