# Tool Registry API Postman Collection

This Postman collection provides a comprehensive set of API endpoints for interacting with the Tool Registry API.

> **IMPORTANT NOTES:**
> 1. **AUTHENTICATION IS DISABLED** - Authentication has been disabled to facilitate development and testing. The API is currently accessible without credentials.
> 2. **API STRUCTURE** - The base URL has been updated to `http://localhost:8000` without the `/api/v1` path. You may need to adjust the paths in the requests based on your actual API implementation.

## Contents

The collection includes the following API endpoint groups:

1. **Authentication** - Endpoints for logging in, user registration, and API key management (kept for reference, but not required)
2. **Tools** - Endpoints for managing tools in the registry
3. **Agents** - Endpoints for managing agents that can access tools
4. **Policies** - Endpoints for defining access control policies
5. **Access Control** - Endpoints for requesting and validating access to tools
6. **Credentials** - Endpoints for managing tool access credentials
7. **Monitoring** - Endpoints for system monitoring, health checks, and usage statistics

## Setup Instructions

1. Install [Postman](https://www.postman.com/downloads/)
2. Import the collection file: `tool_registry_api_collection.json`
3. Import the environment file: `tool_registry_environment.json`
4. Select the "Tool Registry API Environment (Auth Disabled)" from the environment dropdown

## Authentication

While the collection includes authentication endpoints, these are kept for reference only. **You do not need to authenticate to use any of the API endpoints.**

The collection has been configured with `noauth` as the authentication type, so no bearer tokens or API keys are required.

## Using Test Variables

The environment includes test variables for easier testing:
- `testToolId` - Sample tool ID for testing endpoints
- `testAgentId` - Sample agent ID for testing endpoints
- `testPolicyId` - Sample policy ID for testing endpoints
- `testCredentialId` - Sample credential ID for testing endpoints
- `testCredentialToken` - Sample credential token for testing

## Base URL Configuration

The default base URL is set to `http://localhost:8000`. To change this:

1. Open the environment variables
2. Update the `baseUrl` variable to your desired endpoint
3. Save changes

## Troubleshooting

If you receive errors like `Method Not Allowed` or `Not Found`:
1. Check that the API server is running
2. Verify that the endpoint paths match your API implementation
3. Confirm that you're using the correct HTTP method (GET, POST, PUT, DELETE)

## Notes

- Pagination is supported in list endpoints using `page` and `page_size` query parameters 