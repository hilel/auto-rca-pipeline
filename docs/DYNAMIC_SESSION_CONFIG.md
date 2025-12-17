# Dynamic Session Identifier Configuration

## Overview

The Auto-RCA Pipeline now supports dynamic configuration of the session identifier field. Instead of hardcoding `session_id`, you can configure which field (e.g., `token`, `order_id`, `transaction_id`) should be used to identify and group log entries into sessions.

## Features

- **Dynamic Configuration**: Change the session identifier field via REST API
- **Persistent Storage**: Configuration is stored in SQLite database (`data/config.db`)
- **Fallback Logic**: If the configured field is missing in a log entry, the system falls back to standard fields
- **Zero Downtime**: Changes take effect immediately for new processing operations

## Architecture

### Components

1. **Database Layer** (`src/auto_rca/database.py`)
   - SQLite connection management
   - Database initialization with default values
   - Table: `config` (key-value store)

2. **Repository Layer** (`src/auto_rca/repositories/config_repository.py`)
   - `get_session_field()`: Retrieve current session field
   - `set_session_field(field_name)`: Update session field

3. **API Layer** (`src/auto_rca/api/routes/configuration.py`)
   - `GET /config/session-field`: Get current configuration
   - `POST /config/session-field`: Update configuration

4. **Business Logic** (`src/auto_rca/sessionization/session_grouper.py`)
   - Uses dynamic field for session grouping
   - Priority: configured_field → session_id → request_id → user_id → ip_address

## API Usage

### Get Current Session Field

```bash
curl http://localhost:8000/config/session-field
```

Response:
```json
{
  "success": true,
  "message": "Configuration retrieved successfully",
  "data": {
    "session_field": "session_id"
  }
}
```

### Update Session Field

```bash
curl -X POST http://localhost:8000/config/session-field \
  -H "Content-Type: application/json" \
  -d '{"session_field": "token"}'
```

Response:
```json
{
  "success": true,
  "message": "Session field updated to 'token'",
  "data": {
    "session_field": "token"
  }
}
```

## Python SDK Usage

```python
from auto_rca.repositories import get_session_field, set_session_field

# Get current configuration
current_field = get_session_field()
print(f"Current session field: {current_field}")

# Update configuration
set_session_field("order_id")
print("Updated session field to 'order_id'")
```

## Use Cases

### E-commerce Transaction Tracking
```python
# Configure to use order_id
set_session_field("order_id")
# Now logs will be grouped by order_id
```

### Token-based Authentication
```python
# Configure to use token
set_session_field("token")
# Now logs will be grouped by authentication token
```

### Banking/Payment Systems
```python
# Configure to use transaction_id
set_session_field("transaction_id")
# Now logs will be grouped by transaction
```

### Distributed Tracing
```python
# Configure to use correlation_id
set_session_field("correlation_id")
# Now logs will be grouped by distributed trace
```

## Fallback Behavior

When processing logs, the system checks fields in this order:

1. **Configured Field** (e.g., `token`)
2. **session_id** (default fallback)
3. **request_id**
4. **user_id**
5. **ip_address**
6. **"unknown"** (if none found)

### Example

If configured field is `order_id`:

```python
# Log with order_id - uses order_id
{"timestamp": "...", "order_id": "12345", "message": "..."}
# Grouped by: "12345"

# Log without order_id but with session_id - uses session_id
{"timestamp": "...", "session_id": "sess_1", "message": "..."}
# Grouped by: "sess_1"

# Log without order_id or session_id - uses request_id
{"timestamp": "...", "request_id": "req_1", "message": "..."}
# Grouped by: "req_1"
```

## Testing

### Unit Tests

Run the test suite:
```bash
pytest tests/unit/test_configuration.py -v
pytest tests/unit/test_sessionization.py::TestSessionGrouper::test_group_by_custom_field -v
```

### Integration Demo

Run the demonstration script:
```bash
# Start the API server
python -m uvicorn auto_rca.api.main:app --host 127.0.0.1 --port 8000

# In another terminal, run the demo
python examples/config_demo.py
```

## Database Schema

The configuration is stored in `data/config.db`:

```sql
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Example data
INSERT INTO config (key, value) VALUES ('session_field', 'session_id');
```

## Configuration Persistence

- Configuration persists across API restarts
- Default value: `session_id`
- Database location: `data/config.db` (automatically created)
- Database is excluded from version control (`.gitignore`)

## Error Handling

### Database Access Failures
If the database cannot be accessed, the system falls back to `session_id`:

```python
try:
    configured_field = get_session_field()
except Exception:
    configured_field = 'session_id'  # Safe fallback
```

### Invalid Field Names
The API accepts any string as a field name. If the field doesn't exist in logs, the fallback logic takes over.

## Best Practices

1. **Choose Meaningful Fields**: Use fields that uniquely identify user sessions or transactions
2. **Document Your Choice**: Keep track of which field you're using in your deployment
3. **Test Fallback**: Ensure your logs contain fallback fields (session_id, request_id, etc.)
4. **Monitor Changes**: Log configuration changes for audit purposes

## OpenAPI Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Look for the "Configuration" section in the API documentation.

## Security Considerations

- ✅ No SQL injection vulnerabilities (parameterized queries)
- ✅ Input validation via Pydantic models
- ✅ Database access properly isolated in repository layer
- ✅ Graceful error handling with fallbacks
- ✅ CodeQL security scan passed with 0 alerts

## Limitations

- Only one session field can be active at a time
- Field name changes don't retroactively affect already-processed sessions
- Empty string values in the configured field trigger fallback to next identifier

## Future Enhancements

Potential future improvements:
- Multiple session field support (composite keys)
- Field validation against log schemas
- Configuration versioning and history
- Per-pipeline configuration (multiple pipelines with different settings)
