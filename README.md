# Agentic Insurance Assistant

A production-grade AI-powered insurance chatbot built with FastAPI, LangGraph, and PostgreSQL.

## Features

- **AI-Powered Chat**: Natural language interface powered by LangGraph and OpenAI
- **Database Integration**: Full PostgreSQL backend with proper schema for customers, policies, claims, and documents
- **Tool-Based Agent**: LLM agent with database query tools (no fake if-else logic)
- **Production Ready**: Docker, docker-compose, and Kubernetes manifests included
- **Comprehensive Data**: Synthetic data seeding with 300+ customers, 500+ policies, 1200+ claims, 1500+ documents

## Architecture

```
app/
├── agents/          # LangGraph agent implementation
├── api/             # FastAPI routes
├── config/          # Configuration and logging
├── db/              # Database models and session management
├── models/          # Pydantic schemas
├── tools/           # Database query tools for the agent
└── main.py          # Application entry point

scripts/
├── init_db.py       # Database initialization
└── seed_db.py       # Synthetic data seeding

k8s/
├── staging/         # Kubernetes manifests for staging
└── production/      # Kubernetes manifests for production
```

## API Endpoints

### Health Check
```
GET /health
```
Returns application status, environment, and database connection status.

### Chat
```
POST /chat
Content-Type: application/json

{
    "userId": "user123",
    "message": "What is the status of claim CLM-2024-00001?"
}
```
Returns AI-generated response with supporting data.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key

### Local Development with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd agent-prod
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Start the services**
   ```bash
   docker-compose up -d
   ```

4. **Seed the database** (first time only)
   ```bash
   docker-compose run --rm db-seed
   ```

5. **Access the API**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

### Local Development without Docker

1. **Install Python 3.11+**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start PostgreSQL** (or use Docker)
   ```bash
   docker run -d --name postgres \
     -e POSTGRES_USER=postgres \
     -e POSTGRES_PASSWORD=postgres \
     -e POSTGRES_DB=insurance_db \
     -p 5432:5432 \
     postgres:15-alpine
   ```

4. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize and seed the database**
   ```bash
   python -m scripts.seed_db
   ```

6. **Start the application**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Configuration

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment (local/staging/production) | `local` |
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql+asyncpg://...` |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Example Chat Queries

The agent can answer questions like:

- "What is the status of policy POL-AUTO-10001?"
- "Show me claim CLM-2024-00001"
- "What claims are under review?"
- "Get all documents for policy POL-HOME-10050"
- "What policies does customer with email john@example.com have?"

## Database Schema

### Customers
- Basic info: name, email, phone
- Address details: street, city, state, zip
- Date of birth

### Policies
- Policy number (e.g., POL-AUTO-10001)
- Types: auto, home, life, health, travel
- Status: active, expired, cancelled, pending
- Financial: premium, coverage, deductible
- Dates: start, end

### Claims
- Claim number (e.g., CLM-2024-00001)
- Types: accident, theft, damage, medical, liability, natural_disaster
- Status: submitted, under_review, approved, denied, paid, closed
- Amounts: claimed, approved
- Dates: incident, filed

### Documents
- Metadata for S3/SharePoint style storage
- Types: policy_document, claim_form, evidence, invoice, correspondence, id_proof, medical_report
- Storage providers: s3, sharepoint, local

## Kubernetes Deployment

### Staging
```bash
kubectl apply -f k8s/staging/deployment.yaml
```

### Production
```bash
kubectl apply -f k8s/production/deployment.yaml
```

**Note**: Update the secrets in the manifests with your actual credentials or integrate with your secret management solution.

## Development

### Project Structure
- `app/agents/insurance_agent.py` - LangGraph agent with tools
- `app/tools/db_tools.py` - Database query tools
- `app/api/routes.py` - FastAPI endpoints
- `app/db/models.py` - SQLAlchemy models
- `scripts/seed_db.py` - Data seeding script

### Adding New Tools

1. Add the function in `app/tools/db_tools.py`
2. Register the tool in `app/agents/insurance_agent.py` in the `create_tools()` function
3. The LLM will automatically use the tool based on its description

## License

MIT
