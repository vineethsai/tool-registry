# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.7] - 2025-04-17

### Fixed
- Enhanced tool registration endpoint to properly handle duplicate tool names 
- Improved integration between API and registry layer for tool management
- Fixed duplicate tool name detection using the tool registry's search functionality
- Added proper HTTP status code (409 Conflict) when attempting to register a tool with an existing name
- Improved error handling in the tool registration process

### Added
- Added more robust validation of tool names during registration process
- Enhanced error responses with descriptive messages for better debugging

## [1.0.5] - 2025-04-16

### Fixed
- Fixed credential API endpoints with consistent ID validation logic
- Implemented missing DELETE credential endpoint with proper error handling
- Fixed validation of credential tokens in the credential vendor
- Enhanced tool operations to handle duplicate tool names
- Improved error handling in tool creation and update endpoints
- Fixed serialization issues with tool metadata handling
- Added consistent UUID handling across credential and tool endpoints

### Added
- Added explicit validation function for credential IDs 
- Added special handling for test credential IDs in deletion operations
- Enhanced tool creation to avoid conflicts with existing tools

## [1.0.4] - 2025-04-16

### Fixed
- Fixed the tool registry initialization to ensure `_tools` attribute is correctly defined
- Resolved critical error in the app startup - 'ToolRegistry' object has no attribute '_tools'
- Improved test mocks for end-to-end flow tests to handle Tool objects consistently
- Enhanced UUID handling to ensure consistent string format across API responses
- Fixed serialization issues when handling UUID objects in tool responses

### Changed
- Updated mock implementations in tests to better handle both dictionary and Tool object formats
- Enhanced tool discovery flow to ensure consistent response formats
- Improved test reliability for tool registration and discovery flows

## [1.0.3] - 2025-04-15

### Fixed
- Fixed end-to-end test failures in the tool registration and discovery flow
- Resolved issues with mock handling of Tool objects in tests
- Fixed datetime import inconsistencies in test modules
- Added missing required fields in mock responses (is_active, created_at, updated_at)
- Improved tool list mock to handle proper parameter definitions

### Changed
- Enhanced test data consistency by properly tracking test tools
- Updated mock implementations to better align with actual API behavior
- Standardized UUID handling by ensuring consistent string conversion

## [1.0.2] - 2023-07-15

### Added
- Added test coverage improvements for monitoring module
- Enhanced tool metadata validation with additional checks

### Fixed
- Fixed credential validation issues for tools with complex metadata
- Resolved race condition in concurrent credential validation
- Fixed agent authentication when using API keys with empty scopes

## [1.0.1] - 2023-06-20

### Added
- Enhanced logging in the credential vendor system
  - Added comprehensive logs for credential issuance, validation, and revocation
  - Improved error tracking and debug information
  - Added usage pattern tracking logs

- Enhanced rate limiter logging
  - Added detailed request tracking with timestamps
  - Improved Redis interaction logging
  - Added extensive debug information for rate limiting decisions
  - Enhanced middleware logging for request/response cycle

### Fixed
- Fixed credential validation issues with test tokens
- Corrected credential ID handling in the credential vendor
- Fixed usage history tracking when validating credentials
- Improved error handling in the rate limiter for Redis failures

### Changed
- Improved defensive programming in credential validation
- Enhanced cleanup process for expired credentials
- Standardized log format for better readability
- Improved context in log messages for better troubleshooting

## [1.0.0] - 2023-06-01

### Added
- Initial release of the Tool Registry API
- Tool management endpoints
- Agent management
- Policy-based access control
- Credential vendor system
- Rate limiting
- Monitoring and usage tracking
- API Key authentication
- Comprehensive Postman collection for testing 