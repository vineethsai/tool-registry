import { 
  Tool, 
  ToolDetails, 
  PaginatedResponse, 
  Policy, 
  Agent, 
  AccessRequest, 
  AccessValidation,
  Credential,
  UsageLog,
  UsageStats
} from "./types";

// Updated API URL to point to the local backend server
const API_URL = "http://localhost:8000"; 

// Tool API
export async function getTools(page = 1, pageSize = 20, tags?: string[]): Promise<PaginatedResponse<Tool>> {
  const tagsParam = tags?.length ? `&tags=${tags.join(',')}` : '';
  const response = await fetch(`${API_URL}/tools?page=${page}&page_size=${pageSize}${tagsParam}`);
  
  if (!response.ok) {
    throw new Error(`Error fetching tools: ${response.statusText}`);
  }
  
  // Get the response directly, not wrapped in a data field
  const items = await response.json();
  
  // Create a paginated response object
  return {
    items,
    total: items.length,
    page,
    page_size: pageSize,
    pages: Math.ceil(items.length / pageSize)
  };
}

export async function searchTools(query: string, page = 1, pageSize = 20): Promise<PaginatedResponse<Tool>> {
  const response = await fetch(`${API_URL}/tools/search?query=${encodeURIComponent(query)}&page=${page}&page_size=${pageSize}`);
  
  if (!response.ok) {
    throw new Error(`Error searching tools: ${response.statusText}`);
  }
  
  // Get the response directly, not wrapped in a data field
  const items = await response.json();
  
  // Create a paginated response object
  return {
    items,
    total: items.length,
    page,
    page_size: pageSize,
    pages: Math.ceil(items.length / pageSize)
  };
}

export async function getTool(toolId: string): Promise<ToolDetails> {
  const response = await fetch(`${API_URL}/tools/${toolId}`);
  
  if (!response.ok) {
    throw new Error(`Error fetching tool: ${response.statusText}`);
  }
  
  // Get the response directly
  return await response.json();
}

export async function createTool(toolData: Omit<ToolDetails, 'tool_id' | 'created_at' | 'updated_at' | 'owner_id' | 'is_active'>): Promise<ToolDetails> {
  // Use the existing admin agent ID
  const adminAgentId = "00000000-0000-0000-0000-000000000003";

  // Format the request data to match what the backend API expects
  const formattedData = {
    name: toolData.name,
    description: toolData.description,
    version: toolData.version || "1.0.0",
    owner_id: adminAgentId, // Use the known admin agent ID
    tool_metadata: {
      api_endpoint: toolData.api_endpoint,
      auth_method: toolData.auth_method,
      auth_config: toolData.auth_config || {},
      params: toolData.params || {},
      tags: toolData.tags || [],
      allowed_scopes: toolData.allowed_scopes || ["read"]
    }
  };

  console.log("Sending tool creation request:", formattedData);

  const response = await fetch(`${API_URL}/tools`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(formattedData)
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Error creating tool: ${errorText}`);
  }
  
  // Get the response directly
  return await response.json();
}

export async function updateTool(toolId: string, toolData: Partial<ToolDetails>): Promise<ToolDetails> {
  const response = await fetch(`${API_URL}/tools/${toolId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(toolData)
  });
  
  if (!response.ok) {
    throw new Error(`Error updating tool: ${response.statusText}`);
  }
  
  // Get the response directly
  return await response.json();
}

export async function deleteTool(toolId: string): Promise<void> {
  const response = await fetch(`${API_URL}/tools/${toolId}`, {
    method: 'DELETE'
  });
  
  if (!response.ok) {
    throw new Error(`Error deleting tool: ${response.statusText}`);
  }
}

// Policy API
export async function getPolicies(page = 1, pageSize = 20, toolId?: string): Promise<PaginatedResponse<Policy>> {
  const toolParam = toolId ? `&tool_id=${toolId}` : '';
  const response = await fetch(`${API_URL}/policies?page=${page}&page_size=${pageSize}${toolParam}`);
  
  if (!response.ok) {
    throw new Error(`Error fetching policies: ${response.statusText}`);
  }
  
  // Get the response directly, not wrapped in a data field
  const items = await response.json();
  
  // Create a paginated response object
  return {
    items,
    total: items.length,
    page,
    page_size: pageSize,
    pages: Math.ceil(items.length / pageSize)
  };
}

export async function getPolicy(policyId: string): Promise<Policy> {
  const response = await fetch(`${API_URL}/policies/${policyId}`);
  
  if (!response.ok) {
    throw new Error(`Error fetching policy: ${response.statusText}`);
  }
  
  // Get the response directly
  return await response.json();
}

export async function createPolicy(policyData: Omit<Policy, 'policy_id' | 'created_at' | 'updated_at'>): Promise<Policy> {
  const response = await fetch(`${API_URL}/policies`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(policyData)
  });
  
  if (!response.ok) {
    throw new Error(`Error creating policy: ${response.statusText}`);
  }
  
  // Get the response directly
  return await response.json();
}

export async function updatePolicy(policyId: string, policyData: Partial<Policy>): Promise<Policy> {
  const response = await fetch(`${API_URL}/policies/${policyId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(policyData)
  });
  
  if (!response.ok) {
    throw new Error(`Error updating policy: ${response.statusText}`);
  }
  
  // Get the response directly
  return await response.json();
}

export async function deletePolicy(policyId: string): Promise<void> {
  const response = await fetch(`${API_URL}/policies/${policyId}`, {
    method: 'DELETE'
  });
  
  if (!response.ok) {
    throw new Error(`Error deleting policy: ${response.statusText}`);
  }
}

// Agent API
export async function getAgents(page = 1, pageSize = 20, agentType?: string): Promise<PaginatedResponse<Agent>> {
  const typeParam = agentType ? `&agent_type=${agentType}` : '';
  const response = await fetch(`${API_URL}/agents?page=${page}&page_size=${pageSize}${typeParam}`);
  
  if (!response.ok) {
    throw new Error(`Error fetching agents: ${response.statusText}`);
  }
  
  // Get the response directly, not wrapped in a data field
  const items = await response.json();
  
  // Create a paginated response object
  return {
    items,
    total: items.length,
    page,
    page_size: pageSize,
    pages: Math.ceil(items.length / pageSize)
  };
}

export async function getAgent(agentId: string): Promise<Agent> {
  const response = await fetch(`${API_URL}/agents/${agentId}`);
  
  if (!response.ok) {
    throw new Error(`Error fetching agent: ${response.statusText}`);
  }
  
  // Get the response directly
  return await response.json();
}

export async function createAgent(agentData: Omit<Agent, 'agent_id' | 'created_at' | 'updated_at'>): Promise<Agent> {
  const response = await fetch(`${API_URL}/agents`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(agentData)
  });
  
  if (!response.ok) {
    throw new Error(`Error creating agent: ${response.statusText}`);
  }
  
  // Get the response directly
  return await response.json();
}

export async function updateAgent(agentId: string, agentData: Partial<Agent>): Promise<Agent> {
  const response = await fetch(`${API_URL}/agents/${agentId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(agentData)
  });
  
  if (!response.ok) {
    throw new Error(`Error updating agent: ${response.statusText}`);
  }
  
  const responseData = await response.json();
  return responseData.data;
}

export async function deleteAgent(agentId: string): Promise<void> {
  const response = await fetch(`${API_URL}/agents/${agentId}`, {
    method: 'DELETE'
  });
  
  if (!response.ok) {
    throw new Error(`Error deleting agent: ${response.statusText}`);
  }
}

// Access Control API
export async function requestAccess(requestData: {
  agent_id: string;
  tool_id: string;
  policy_id: string;
  justification: string;
}): Promise<AccessRequest> {
  const response = await fetch(`${API_URL}/access/request`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(requestData)
  });
  
  if (!response.ok) {
    throw new Error(`Error requesting access: ${response.statusText}`);
  }
  
  const responseData = await response.json();
  return responseData.data;
}

export async function validateAccess(agentId: string, toolId: string): Promise<AccessValidation> {
  const response = await fetch(`${API_URL}/access/validate?agent_id=${agentId}&tool_id=${toolId}`);
  
  if (!response.ok) {
    throw new Error(`Error validating access: ${response.statusText}`);
  }
  
  const responseData = await response.json();
  return responseData.data;
}

export async function getAccessRequests(
  page = 1, 
  pageSize = 20, 
  filters?: {
    agent_id?: string;
    tool_id?: string;
    status?: "pending" | "approved" | "rejected";
  }
): Promise<PaginatedResponse<AccessRequest>> {
  let url = `${API_URL}/access/requests?page=${page}&page_size=${pageSize}`;
  
  if (filters) {
    if (filters.agent_id) url += `&agent_id=${filters.agent_id}`;
    if (filters.tool_id) url += `&tool_id=${filters.tool_id}`;
    if (filters.status) url += `&status=${filters.status}`;
  }
  
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`Error fetching access requests: ${response.statusText}`);
  }
  
  // Get the response directly, not wrapped in a data field
  const items = await response.json();
  
  // Create a paginated response object
  return {
    items,
    total: items.length,
    page,
    page_size: pageSize,
    pages: Math.ceil(items.length / pageSize)
  };
}

// Credentials API
export async function createCredential(credentialData: {
  agent_id: string;
  tool_id: string;
  credential_type: string;
  credential_value: Record<string, any>;
  expires_at?: string;
}): Promise<Credential> {
  const response = await fetch(`${API_URL}/credentials`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(credentialData)
  });
  
  if (!response.ok) {
    throw new Error(`Error creating credential: ${response.statusText}`);
  }
  
  // Get the response directly
  return await response.json();
}

export async function getCredentials(
  page = 1, 
  pageSize = 20, 
  filters?: {
    agent_id?: string;
    tool_id?: string;
  }
): Promise<PaginatedResponse<Credential>> {
  let url = `${API_URL}/credentials?page=${page}&page_size=${pageSize}`;
  
  if (filters) {
    if (filters.agent_id) url += `&agent_id=${filters.agent_id}`;
    if (filters.tool_id) url += `&tool_id=${filters.tool_id}`;
  }
  
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`Error fetching credentials: ${response.statusText}`);
  }
  
  // Get the response directly, not wrapped in a data field
  const items = await response.json();
  
  // Create a paginated response object
  return {
    items,
    total: items.length,
    page,
    page_size: pageSize,
    pages: Math.ceil(items.length / pageSize)
  };
}

export async function deleteCredential(credentialId: string): Promise<void> {
  const response = await fetch(`${API_URL}/credentials/${credentialId}`, {
    method: 'DELETE'
  });
  
  if (!response.ok) {
    throw new Error(`Error deleting credential: ${response.statusText}`);
  }
}

// Usage Logs API
export async function getUsageLogs(
  page = 1, 
  pageSize = 20, 
  filters?: {
    agent_id?: string;
    tool_id?: string;
    start_date?: string;
    end_date?: string;
    status?: "success" | "error";
  }
): Promise<PaginatedResponse<UsageLog>> {
  let url = `${API_URL}/logs?page=${page}&page_size=${pageSize}`;
  
  if (filters) {
    if (filters.agent_id) url += `&agent_id=${filters.agent_id}`;
    if (filters.tool_id) url += `&tool_id=${filters.tool_id}`;
    if (filters.start_date) url += `&start_date=${filters.start_date}`;
    if (filters.end_date) url += `&end_date=${filters.end_date}`;
    if (filters.status) url += `&status=${filters.status}`;
  }
  
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`Error fetching usage logs: ${response.statusText}`);
  }
  
  // Get the response directly, not wrapped in a data field
  const items = await response.json();
  
  // Create a paginated response object
  return {
    items,
    total: items.length,
    page,
    page_size: pageSize,
    pages: Math.ceil(items.length / pageSize)
  };
}

export async function getUsageStats(
  filters?: {
    tool_id?: string;
    period?: "day" | "week" | "month";
    start_date?: string;
    end_date?: string;
  }
): Promise<UsageStats> {
  let url = `${API_URL}/stats/usage`;
  const queryParams: string[] = [];
  
  if (filters) {
    if (filters.tool_id) queryParams.push(`tool_id=${filters.tool_id}`);
    if (filters.period) queryParams.push(`period=${filters.period}`);
    if (filters.start_date) queryParams.push(`start_date=${filters.start_date}`);
    if (filters.end_date) queryParams.push(`end_date=${filters.end_date}`);
  }
  
  if (queryParams.length) {
    url += `?${queryParams.join('&')}`;
  }
  
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error(`Error fetching usage statistics: ${response.statusText}`);
  }
  
  // Get the response directly
  return await response.json();
}

// Health check API
export async function getSystemHealth(): Promise<{
  status: string;
  version: string;
  uptime: number;
  db_connection: string;
  components: Record<string, any>;
}> {
  const response = await fetch(`${API_URL}/health`);
  
  if (!response.ok) {
    throw new Error(`Error fetching system health: ${response.statusText}`);
  }
  
  // Get the response directly
  return await response.json();
}
