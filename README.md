# Chat API

A scalable Python API for debate-style conversations with deterministic responses.

## Quick Start

### Using Docker (In-Memory, Default)

```bash
# Clone the repository
git clone <repository-url>
cd kopi_challenge

# Install dependencies
make install

# Run API with in-memory storage (default)
make run
```

### With Redis Storage

```bash
# Run API with Redis backend for persistent storage
make run-redis
```

### Local Development

```bash
# Create virtual environment and install dependencies
make install

# Run locally with in-memory storage
make dev

# Run locally with Redis
make dev-redis
```

The API will be available at `http://localhost:8000`.
Interactive API documentation (OpenAPI) is available at `http://localhost:8000/docs`.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Server port |
| `APP_ENV` | `local` | Environment: `local`, `staging`, `prod` |
| `LOG_LEVEL` | `INFO` | Logging level |
| `ENABLE_METRICS` | `0` | Enable Prometheus metrics (1 to enable) |
| `REQUEST_TIMEOUT` | `29` | Request timeout in seconds |
| `REDIS_URL` | _(empty)_ | Redis connection URL. If empty, uses in-memory storage |

### Example with environment variables:
```bash
export REDIS_URL=redis://localhost:6379
export ENABLE_METRICS=1
export LOG_LEVEL=DEBUG
make run
```

## Makefile Usage

| Target | Description |
|--------|-------------|
| `make help` | Show all available targets |
| `make install` | Install dependencies and check for Docker/Compose |
| `make test` | Run tests with pytest |
| `make run` | Build and run with docker compose |
| `make down` | Stop docker compose services |
| `make clean` | Clean up Docker resources completely |

## API Endpoints

### Chat Endpoint
**POST** `/api/v1/chat`

Start or continue a debate conversation.

#### Request
```json
{
  "conversation_id": "string|null",
  "message": "string"
}
```

#### Response
```json
{
  "conversation_id": "uuid-v4",
  "message": [
    {"role": "user", "message": "I think renewable energy is the future"},
    {"role": "bot", "message": "I maintain that renewable energy presents significant concerns that cannot be ignored. Moreover, efficiency improvements. The evidence clearly shows data indicates this viewpoint. First, consider that innovation advancement. This is crucial because research confirms this perspective. Think of it like learning to drive - both share the fundamental principle of continuous improvement. Don't you think progress should be halted due to minor concerns? While you mention 'I think renewable energy is the future', this perspective misses key considerations. These principles ensure the most effective outcomes."}
  ]
}
```

#### cURL Example
```bash
# Start new conversation
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": null,
    "message": "I think climate change is not a serious issue"
  }'

# Continue conversation
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "What evidence supports your position?"
  }'
```

### Health Endpoints

#### Liveness Check
```bash
curl http://localhost:8000/healthz
# Response: {"status": "ok"}
```

#### Readiness Check  
```bash
curl http://localhost:8000/readyz
# Response (in-memory): {"status": "ok"}
# Response (Redis): {"status": "ok", "deps": {"redis": "ok"}}
```

### Metrics (Optional)

When `ENABLE_METRICS=1`:
```bash
curl http://localhost:8000/metrics
# Returns Prometheus-formatted metrics
```

## Language & Topics

### Language Selection
The API automatically detects and locks the conversation language based on the **first user message**:
- **Spanish input** → All bot responses in Spanish for that conversation
- **English input** → All bot responses in English for that conversation

## Stance & Topic Behavior

### Stance Logic
- **The bot always takes the opposite stance** of the first user message for engaging debate
- **Pro-technology user message** → Bot takes contra-technology stance
- **Contra-climate user message** → Bot takes pro-climate stance  
- **Stance remains consistent** throughout the entire conversation

### Topic Handling
- **Topic is fixed** on the first turn of each conversation
- **Supported topics**: technology, climate change, education (with bilingual keyword detection)
- **Generic Comparator Engine**: Handles any "A vs B" or "A better than B" comparison with domain-agnostic arguments
- **Unconventional topics**: Graceful fallback with subjectivity acknowledgment and generic arguments
- **Topic switches**: Bot acknowledges switches (with 2+ keyword threshold) but **stays focused** on the original topic
- **To discuss a new topic**, start a new conversation

### Generic Comparator Engine
The API features a powerful Generic Comparator Engine that can handle any comparison debate:
- **Patterns supported**: "A vs B", "A better than B", "A superior to B", "prefer A to B"
- **Languages**: Full support for English and Spanish comparison patterns
- **Domain-agnostic**: Uses 10 generic axes (simplicity, consistency, accessibility, etc.) instead of topic-specific arguments
- **Deterministic**: Same comparison always produces the same response with variety through rotation
- **Opposite stance**: Always argues for the opposite side to foster debate

### Examples

#### Conventional Topic with Opposite Stance (English)
```bash
# Pro-technology message → Bot takes contra-technology stance
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I believe artificial intelligence will revolutionize society for the better"
  }'

# Continue debate - bot maintains contra stance
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "your-conversation-id", 
    "message": "AI will solve healthcare and education problems"
  }'
```

#### Unconventional Topic with Fallback (English)
```bash
# Unconventional topic → Graceful fallback response
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Pineapple on pizza is delicious and should be the standard"
  }'
# Bot acknowledges subjectivity and uses generic arguments
```

#### Spanish Conversation with Opposite Stance
```bash
# Pro-technology in Spanish → Bot takes contra stance in Spanish
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Creo que la tecnología es excelente y beneficiosa para la humanidad"
  }'
```

#### Generic Comparator Engine Examples

##### English Comparisons
```bash
# Neutral comparison
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "coffee vs tea"
  }'
# Bot chooses a side deterministically and argues using generic axes

# User preference comparison  
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "iPhone is better than Android"
  }'
# Bot argues for Android using axis-based arguments
```

##### Spanish Comparisons
```bash
# Spanish user preference
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Python es mejor que Java"
  }'
# Bot responds: "Tu idea central es que Python supera a Java; sostengo lo contrario por las razones anteriores"

# Neutral Spanish comparison
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "gatos vs perros"
  }'
# Bot uses Spanish axes: "En simplicidad, perros reduce fricción; gatos añade pasos extra"
```

## Testing

```bash
# Run all tests
make test

# Run specific test files
pytest api/tests/test_contract.py -v
pytest api/tests/test_history_trim.py -v
pytest api/tests/test_healthchecks.py -v

# Run with coverage
pytest --cov=api --cov-report=html
```

## Deployment

### EC2 Deployment

1. **Launch EC2 instance** with Docker installed
2. **Security Group**: Open inbound port for your API (default 8000)
3. **Deploy application**:
   ```bash
   # Clone repository
   git clone <repository-url>
   cd kopi_challenge
   
   # Set production environment
   export APP_ENV=prod
   export LOG_LEVEL=INFO
   export REDIS_URL=redis://localhost:6379  # Optional
   
   # Run application
   make run
   ```

4. **Production considerations**:
   - Use a reverse proxy (nginx) for HTTPS and load balancing
   - Set up proper logging aggregation
   - Configure monitoring and alerting
   - Use managed Redis (AWS ElastiCache) for production

### Environment-specific configuration:
```bash
# Production
export APP_ENV=prod
export REDIS_URL=redis://your-redis-host:6379

# Staging  
export APP_ENV=staging
export ENABLE_METRICS=1
```

## Architecture Decisions

### Storage Strategy
- **In-memory by default**: Simple, fast, zero dependencies for development
- **Redis optional**: Production-ready persistence and horizontal scaling
- **TTL management**: Automatic cleanup after 24 hours
- **History trimming**: Maintains last 5 exchanges (10 messages) for performance

### Deterministic Debate Engine
- **Local processing**: No external LLM calls, ensuring speed and reliability
- **Stance detection**: Simple heuristics-based approach for topic/stance extraction
- **Deterministic responses**: Uses message content hash for consistent debate positions
- **Structured argumentation**: 6-part response format (anchor, arguments, analogy, question, refutation, close)

### Error Handling
- **Unified error envelope**: Consistent error format across all endpoints
- **Request tracing**: X-Request-Id for debugging and monitoring
- **Timeout protection**: 29-second request timeout with graceful degradation
- **Validation**: Pydantic models ensure request/response contract compliance

### Observability
- **Structured logging**: JSON format for easy parsing and aggregation
- **Optional metrics**: Prometheus integration when needed
- **Health checks**: Separate liveness and readiness probes
- **Request tracking**: Full request lifecycle monitoring

### Performance Optimizations
- **Message size limits**: 4KB request limit prevents abuse
- **History trimming**: Automatic conversation pruning
- **Response time bounds**: <30s per request guaranteed
- **Minimal dependencies**: Fast startup and low resource usage

## Development

### Code Quality
```bash
# Linting
ruff check api/
ruff format api/

# Type checking (if mypy installed)
mypy api/
```

### Local Redis for testing
```bash
# Start Redis in Docker
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Set Redis URL
export REDIS_URL=redis://localhost:6379

# Run application
python -m api.main
```

## 📖 API Documentation

### Interactive OpenAPI Documentation

The API provides interactive documentation via Swagger UI:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **OpenAPI JSON**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### Endpoints Overview

- `POST /api/v1/chat` - Main chat endpoint with debate functionality
- `GET /healthz` - Liveness probe (always returns 200)
- `GET /readyz` - Readiness probe (checks Redis if configured)
- `GET /metrics` - Prometheus metrics (if `ENABLE_METRICS=1`)

## ⚠️ Limitations

### Language Support

- **Official Languages**: Spanish (ES) and English (EN)
- **Fallback Behavior**: Other languages automatically fall back to English responses
- **Detection**: Uses heuristic-based language detection on first message

### Debate Constraints

- **Topic Fixation**: Topic is locked after the first message in a conversation
- **Stance Opposition**: Bot always takes the opposite stance to foster debate
- **Response Length**: Bot responses are capped at approximately 200-300 words
- **Conversation Memory**: Only the last 5 turns per role (10 total) are retained

## 🔧 Development Notes

### Known-Good Package Versions

The pinned versions in `requirements.txt` have been tested and verified compatible:

| Package | Version | Notes |
|---------|---------|--------|
| FastAPI | 0.104.1 | Core web framework |
| Pydantic | 2.5.2 | Request/response validation |
| Redis | 5.0.1 | Optional storage backend |
| Uvicorn | 0.24.0 | ASGI server |
| Pytest | 7.4.3 | Testing framework |

## License

This project is created for demonstration purposes.
