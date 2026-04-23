# Test Suite Documentation

This directory contains comprehensive tests for the Voice AI Server.

## Test Files

### 1. `test_auth_complete.py`
Complete authentication test suite that tests:
- Health endpoint
- User registration (multiple users)
- User login
- Token generation
- Session validation
- Concurrent user access
- All endpoints with raw JSON input/output

**Usage:**
```bash
python test/test_auth_complete.py
```

### 2. `test_sse_complete.py`
Complete SSE (Server-Sent Events) test suite that tests:
- SSE connection establishment
- Navigation command endpoint
- Conversation event endpoint
- AI data endpoint
- Concurrent SSE connections
- All SSE event types
- Raw JSON input/output for all events

**Usage:**
```bash
python test/test_sse_complete.py
```

### 3. `run_all_tests.py`
Test runner that executes all test suites in sequence.

**Usage:**
```bash
python test/run_all_tests.py
```

## Test Features

### Raw JSON Output
All tests print complete raw JSON for:
- Request payloads
- Response data
- Headers
- Status codes
- Error messages

### Multiple User Testing
Auth tests create and test multiple users simultaneously:
- `testuser1` / `testpass123`
- `testuser2` / `testpass456`
- `testuser3` / `testpass789`

### Concurrent Testing
Tests simulate real-world scenarios with:
- Multiple simultaneous SSE connections
- Concurrent user logins
- Parallel token generation

### Event Type Coverage
SSE tests cover all event types:
- `connection` - Initial connection
- `keepalive` - Connection maintenance
- `user_speech_text` - User voice input
- `ai_speech_text` - AI voice output
- `ai_intent` - Hash-based intent commands
- `static_data_ready` - Component data loaded
- `navigation_command` - Navigation actions
- `tool_log` - AI tool activity

## Prerequisites

Make sure the server is running:
```bash
python runServer.py
```

## Expected Output

Tests will show:
- ✅ for passed tests
- ❌ for failed tests
- 📋 Raw JSON request/response data
- 📊 Summary statistics
- ⏱️ Timing information

## Log Files

Tests generate detailed log files:
- `test/auth_test.log` - Authentication test logs
- `test/sse_test.log` - SSE test logs

## Troubleshooting

If tests fail:
1. Check server is running on correct port (8004)
2. Verify database connection
3. Check API keys in environment
4. Review log files for detailed errors

## Test Data

Tests use predictable test data for reproducibility:
- Fixed usernames and passwords
- Consistent room names
- Deterministic event sequences