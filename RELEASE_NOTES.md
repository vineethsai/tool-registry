# Release Notes

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