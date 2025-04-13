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
8. **Test Data Generation** - Tools for generating test data in bulk for comprehensive testing
9. **Acceptance Test Scenarios** - End-to-end test workflows covering core business functionality
10. **Security Testing** - Security and penetration testing scenarios

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

## Comprehensive Testing Capabilities

### Test Data Generation

The collection includes utilities for generating test data in bulk:

1. Individual generators for agents, tools, policies, access requests, and credentials
2. A "Generate Multiple Test Entities" request that can be used with the Collection Runner to create multiple entities at once
3. Clean-up tools for removing test data references

Each test data generation request:
- Creates entities with unique names (using timestamps)
- Stores entity IDs in environment variables for later use
- Maintains arrays of IDs for bulk operations

### Acceptance Testing

Ready-to-use acceptance test scenarios cover core business flows:

1. **Agent Registration and Management** - Create, verify, and update agents
2. **Tool Registration Flow** - Register new tools and verify their existence
3. **Policy Creation and Access Control** - Create policies and validate access
4. **Credential Management** - Generate and verify credentials

Each acceptance test includes:
- Pre-request scripts for setup
- Test scripts that validate correct API behavior
- Clear pass/fail criteria
- Environment variable storage for cross-request data sharing

### Security Testing

The collection includes a suite of security tests to identify potential vulnerabilities:

1. **Input Validation Tests** - SQL injection, XSS, and XXE attack attempts
2. **Authorization Tests** - Access control and directory traversal attempts
3. **Data Validation Tests** - Invalid input formats and excessive payloads
4. **Rate Limiting Tests** - API flood protection checks

## Running Test Suites

To run comprehensive test suites:

1. Use the Postman Collection Runner to execute test folders
2. For data generation, set the desired quantity in the "Generate Multiple Test Entities" request
3. For security testing, review the test results to identify potential vulnerabilities
4. Use the environment variables panel to monitor stored test entities

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