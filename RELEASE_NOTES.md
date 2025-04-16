# Release Notes

## Tool Registry v1.0.7 (2025-04-17)

### Overview

This release focuses on enhancing the tool registration process to properly handle duplicate tool names, improving error handling, and providing clearer feedback when conflicts occur.

### What's New

1. **Improved Tool Registration**
   - Enhanced the tool registration endpoint to properly handle duplicate tool names
   - Added proper HTTP status code (409 Conflict) when attempting to register a tool with an existing name
   - Improved error handling in the tool registration process

2. **Enhanced Validation and Error Handling**
   - Added more robust validation of tool names during registration
   - Enhanced error responses with descriptive messages for better debugging
   - Improved integration between API endpoints and core registry layer

3. **Bug Fixes**
   - Fixed duplicate tool name detection using the tool registry's search functionality
   - Improved error handling in the tool registration process

### Docker Updates

The Docker container has been updated with version 1.0.7 and includes:
- Updated version labeling in Dockerfile
- Updated build and test scripts for easier releases

### Installation and Upgrade

#### Docker Installation

```bash
# Pull and run the latest version
docker pull ghcr.io/yourusername/tool-registry:1.0.7
docker-compose up -d
```

#### Upgrading from v1.0.5

```bash
# Pull the latest changes
git pull

# Build and start the updated containers
./build_release.sh
```

### Testing the New Features

1. **Testing Duplicate Tool Handling**
   - Attempt to register a tool with an existing name to verify the 409 conflict response:
   ```bash
   # First, register a tool
   curl -X POST "http://localhost:8000/tools" -H "Content-Type: application/json" -d '{"name":"Test Tool","description":"Test tool for API testing"}'
   
   # Then try to register another tool with the same name
   curl -X POST "http://localhost:8000/tools" -H "Content-Type: application/json" -d '{"name":"Test Tool","description":"Another test tool"}'
   
   # Should return a 409 Conflict response
   ```

### Known Issues

- When running with Redis disabled, rate limiting falls back to in-memory storage with a warning

### Contributors

- Vineeth Sai Narajala

## Tool Registry v1.0.3 (2025-04-15)

### Overview

This release focuses on improving the stability and reliability of the test suite, particularly for end-to-end tests, and ensuring that the mock implementations accurately reflect the actual API behavior.

### What's New

1. **End-to-End Test Improvements**
   - Fixed the `test_tool_registration_and_discovery_flow` test to properly handle Tool objects
   - Resolved issues with tool metadata handling in tests
   - Improved mock implementations for better alignment with API behavior

2. **Bug Fixes**
   - Fixed datetime import inconsistencies in test modules
   - Added missing required fields (is_active, created_at, updated_at) in mock responses
   - Resolved issues with mock tool list handling
   - Fixed parameter definitions in mock functions

3. **Standardization Improvements**
   - Enhanced test data consistency by properly tracking test tools
   - Standardized UUID handling with consistent string conversion
   - Improved tool object mock implementation

### Docker Updates

The Docker container has been updated with version 1.0.3 and includes:
- Updated version labeling in Dockerfile
- Updated build and test scripts for easier releases

### Installation and Upgrade

#### Docker Installation

```bash
# Pull and run the latest version
docker pull ghcr.io/yourusername/tool-registry:1.0.3
docker-compose up -d
```

#### Upgrading from v1.0.2

```bash
# Pull the latest changes
git pull

# Build and start the updated containers
./build_release.sh
```

### Testing Improvements

1. **Testing with the Updated Mocks**
   - Run the tool registration and discovery flow test:
   ```
   python -m pytest tests/test_end_to_end_flows.py::TestEndToEndFlows::test_tool_registration_and_discovery_flow -v
   ```

2. **Running All End-to-End Tests**
   ```
   python -m pytest tests/test_end_to_end_flows.py -v
   ```

### Known Issues

- Some end-to-end tests still fail and will be addressed in future releases:
  - The tool access flow test (`test_tool_access_flow`) fails with a 404 status code
  - The policy management flow test (`test_policy_management_flow`) fails with validation errors
  - The monitoring and analytics flow test (`test_monitoring_and_analytics_flow`) fails with a missing required timestamp

### Contributors

- Vineeth Sai Narajala

## Tool Registry v1.0.1 (2023-06-20)

### Overview

This release focuses on enhancing the logging capabilities within the Tool Registry to improve troubleshooting and debugging. The primary areas of improvement are in the credential management system and rate limiting functionality.

### What's New

1. **Enhanced Credential Vendor Logging**
   - Added comprehensive logs throughout the credential lifecycle
   - Improved error tracking for credential validation
   - Added detailed logs for test token handling
   - Enhanced debug information for credential operations

2. **Improved Rate Limiter Logging**
   - Added detailed request tracking with timestamps
   - Improved Redis interaction logging
   - Enhanced debugging for rate limit decisions
   - Added detailed logging in middleware for request/response cycle

3. **Bug Fixes**
   - Fixed credential validation issues with test tokens
   - Corrected credential ID handling in the credential vendor
   - Fixed usage history tracking
   - Improved error handling for Redis failures

4. **Documentation Updates**
   - Updated README.md with information about the enhanced logging
   - Added a new section in developer_guide.md about the logging system
   - Enhanced troubleshooting.md with information about using logs for debugging
   - Added CHANGELOG.md to track version changes

### Docker Updates

The Docker container has been updated with version 1.0.1 and includes:
- Added version labeling in Dockerfile
- Updated docker-compose.yml with logging configuration
- Created a build script (build_release.sh) for easier releases

### Installation and Upgrade

#### Docker Installation

```bash
# Pull and run the latest version
docker-compose up -d
```

#### Upgrading from v1.0.0

```bash
# Pull the latest changes
git pull

# Build and start the updated containers
./build_release.sh
```

### Tips for Using the Enhanced Logging

1. **Enable Debug Logging**
   ```
   export LOG_LEVEL=DEBUG
   ```

2. **Filter Logs by Component**
   ```
   grep "credential_vendor" app.log
   grep "rate_limit" app.log
   ```

3. **Watch for Key Warning Patterns**
   - Credential expiration: `Credential expired`
   - Rate limiting: `Rate limit exceeded`
   - Token mapping issues: `Token not found in mapping`

### Known Issues

- The authorization service tests have failures that have not been addressed in this release
- There are some deprecation warnings related to SQLAlchemy and Pydantic that will be addressed in a future release

### Contributors

- Vineeth Sai Narajala 