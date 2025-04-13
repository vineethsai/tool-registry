# Tool Registry API Postman Collection

This Postman collection provides a comprehensive set of API endpoints for interacting with the Tool Registry API.

## Contents

The collection includes the following API endpoint groups:

1. **Authentication** - Endpoints for logging in, user registration, and API key management
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
4. Select the "Tool Registry API Environment" from the environment dropdown

## Authentication

Before using most endpoints, you need to authenticate:

1. Use the **Login** endpoint with your username and password
2. The authentication token will be automatically stored in the environment variables
3. Subsequent requests will use this token for authentication

## Using Test Variables

The environment includes test variables for easier testing:
- `testToolId` - Sample tool ID for testing endpoints
- `testAgentId` - Sample agent ID for testing endpoints
- `testPolicyId` - Sample policy ID for testing endpoints
- `testCredentialId` - Sample credential ID for testing endpoints
- `testCredentialToken` - Sample credential token for testing

## Base URL Configuration

The default base URL is set to `http://localhost:8000/api/v1`. To change this:

1. Open the environment variables
2. Update the `baseUrl` variable to your desired endpoint
3. Save changes

## Notes

- All authenticated requests require a valid bearer token, which is automatically handled by the collection
- Pagination is supported in list endpoints using `page` and `page_size` query parameters 