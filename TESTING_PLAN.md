# Testing Plan for SleepBot

## Overview
Target: >= 90% code coverage with meaningful tests

## Test Structure

### Branches Created
- `tests/mock` - Mock tests with fake database
- `tests/unit` - Unit tests for isolated functions
- `tests/smoke` - Critical functionality tests
- `tests/integration` - Component interaction tests

## Mock Tests (`tests/mock/`)

### ✅ Completed
1. **test_sleep_service_validation.py** - Time window validation
   - Fresh session (<24h) - allow first update
   - Fresh session with data - ask confirmation
   - Old session (>=24h) - show warning
   - Rating validation (1.0-10.0)
   - Note validation (empty, whitespace)
   - Active session protection

2. **test_sql_injection_protection.py** - Security tests
   - SQL injection payloads in notes
   - SQL injection in usernames
   - XSS attempts
   - Special characters handling
   - Unicode support
   - Long input handling

3. **test_repositories.py** - Database layer
   - CRUD operations
   - Query methods
   - Concurrent modifications

### 🚧 TODO for >= 90% Coverage

4. **test_handlers.py** - Bot handlers
   - `/sleep` command
   - `/wake` command
   - `/quality` command with FSM states
   - `/note` command with FSM states
   - `/stats` command
   - Callback query handlers
   - Language switching

5. **test_statistics_service.py**
   - Statistics calculation
   - Export to CSV/JSON
   - Date range filtering

6. **test_localization.py**
   - Message formatting
   - Language switching
   - Placeholder replacement

7. **test_exporters.py**
   - CSV export
   - JSON export
   - Data formatting

## Unit Tests (`tests/unit/`)

### TODO
1. **test_formatters.py**
   - Time formatting
   - Duration formatting
   - Percentage calculation

2. **test_validators.py**
   - Input validation
   - Range validation
   - Type validation

3. **test_utils.py**
   - Logger functionality
   - Helper functions

## Smoke Tests (`tests/smoke/`)

### TODO - Critical Path Testing
1. **test_critical_flow.py**
   - User registration
   - Sleep tracking (start -> end)
   - Quality rating
   - Note adding
   - Stats export

## Integration Tests (`tests/integration/`)

### TODO
1. **test_bot_flow.py**
   - Full user journey
   - FSM state transitions
   - Database persistence

2. **test_database_integration.py**
   - Migrations
   - Data integrity
   - Transaction handling

## Test Cases to Cover

### Security Tests ✅
- [x] SQL injection protection
- [x] XSS protection
- [x] Long input handling
- [x] Unicode support
- [ ] Rate limiting
- [ ] Input sanitization

### Validation Tests ✅
- [x] Time window validation (<24h, >=24h)
- [x] Quality rating range (1.0-10.0)
- [x] Empty note detection
- [x] Active session protection
- [ ] Timezone validation
- [ ] Date range validation

### Business Logic Tests
- [x] Session lifecycle
- [x] Data overwriting with confirmation
- [ ] Statistics calculation
- [ ] Export formatting
- [ ] Localization

### Edge Cases
- [x] No sessions for user
- [x] Multiple sessions
- [x] Concurrent modifications
- [ ] Database errors
- [ ] Network timeouts
- [ ] Invalid FSM states

## Coverage Goals

| Module | Target | Status |
|--------|--------|--------|
| services/ | >= 90% | 🚧 In Progress |
| repositories/ | >= 90% | ✅ ~85% |
| bot/handlers/ | >= 90% | 📝 TODO |
| utils/ | >= 90% | 📝 TODO |
| localization/ | >= 90% | 📝 TODO |

## Running Tests

```bash
# Run all mock tests
pytest tests/mock/ -v

# Run with coverage
pytest tests/mock/ --cov=services --cov=repositories --cov-report=html

# Run specific test file
pytest tests/mock/test_sql_injection_protection.py -v

# Run with detailed output
pytest tests/mock/ -vv -s
```

## Next Steps

1. ✅ Create test fixtures and base setup
2. ✅ Implement SQL injection protection tests
3. ✅ Implement time window validation tests
4. ✅ Implement repository tests
5. 🚧 Add handler tests (bot commands)
6. 📝 Add service tests (statistics, user service)
7. 📝 Add utility tests (exporters, formatters)
8. 📝 Add smoke tests (critical paths)
9. 📝 Add integration tests
10. 📝 Achieve >= 90% coverage
11. 📝 Document test results

## Notes

- All tests use in-memory SQLite database
- Faker library generates realistic test data
- Tests are isolated and can run in parallel
- Each test file focuses on one module/concern
- Mocked external dependencies (Telegram API)
