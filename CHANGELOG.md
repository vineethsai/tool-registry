# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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