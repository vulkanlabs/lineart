# Vulkan Agent

AI agent service for the Vulkan platform with LangChain-based LLM abstraction and documentation-in-context assistance.

## Features

- **Multi-provider LLM support**: OpenAI, Anthropic (Claude), Google (Gemini), and other LangChain-compatible providers
- **Documentation-in-Context**: Full documentation loaded directly into LLM context for comprehensive assistance
- **Runtime Documentation Management**: Update documentation via API without service restarts
- **Database-backed Configuration**: Persistent agent configuration with validation
- **Memory Management**: Conversation history and session persistence
- **FastAPI REST API**: HTTP endpoints for agent interaction and configuration
- **Extensible Tool System**: Framework for adding custom tools and capabilities

## Quick Start

### Local Development

```bash
# Install dependencies
make install

# Run tests
make test

# Start the vulkan-agent service (from project root)
cd ..
docker-compose -f docker-compose.dev.yaml up vulkan-agent
```

### Production

```bash
# Run with pre-built images (from project root)
cd ..
docker-compose up vulkan-agent
```

### Available Make Commands

- `make test` - Run unit tests (fast feedback during development)
- `make test-integration` - Run integration tests only
- `make test-all` - Run all tests (unit + integration)
- `make lint` - Run code linting and formatting checks
- `make format` - Format code with ruff
- `make clean` - Clean up cache files and build artifacts
- `make clean-db` - Clean up database files
- `make clean-all` - Clean up everything (cache + database files)
- `make install` - Install dependencies
- `make integration-demo` - Run integration test as standalone demo

## Development

### Project Structure

```
vulkan-agent/
├── vulkan_agent/                    # Main package
│   ├── llm.py                      # LangChain-based LLM abstraction
│   ├── knowledge_base.py           # Documentation loader (replaced RAG system)
│   ├── agent.py                    # Agent creation and tool management
│   ├── config.py                   # Database-backed configuration management
│   ├── database.py                 # SQLite database manager
│   ├── models.py                   # SQLAlchemy database models
│   ├── schemas.py                  # Pydantic request/response schemas
│   ├── app.py                      # FastAPI application
│   └── routers/                    # API route handlers
│       ├── config.py               # Configuration endpoints
│       └── chat.py                 # Chat and documentation endpoints
├── test/                           # Test suite
│   ├── test_llm.py                 # Unit tests for LLM functionality
│   ├── test_documentation_loader.py # Unit tests for documentation system
│   ├── test_config.py              # Unit tests for configuration
│   ├── test_app.py                 # Unit tests for API
│   └── integration/                # Integration tests
│       └── test_langchain_integration.py
├── data/                           # Runtime data (databases, etc.)
└── Makefile                        # Development commands
```

### Testing Strategy

- **Unit Tests** (`test/`): Fast, isolated tests for individual components
- **Integration Tests** (`test/integration/`): End-to-end tests for system integration
- **Test Isolation**: Tests use in-memory databases for clean test environments
- **Automatic Cleanup**: Database files are automatically cleaned after test runs

### Configuration

The agent uses **database-backed configuration** for LLM settings, with minimal environment variables for service configuration.

#### Environment Variables

The agent only uses **3 environment variables**:

```bash
# Service Configuration
HOST=0.0.0.0              # Server host (default: 0.0.0.0)
PORT=8001                 # Server port (default: 8001)

# Documentation Configuration
VULKAN_DOCS_PATH=/app/docs # Path to documentation directory (default: /docs)

# Prompts Configuration
VULKAN_PROMPTS_PATH=/app/prompts # Path to prompts directory (default: /app/prompts)

# Database Configuration
VULKAN_DB_PATH=/app/data/vulkan_agent.db # Path to SQLite database file
```

**Important**: LLM configuration (API keys, models, parameters) is **not** managed via environment variables. All LLM settings are stored in the database and configured through API endpoints for security and runtime flexibility.

**Validation Approach**: The system uses actual API connection testing rather than hard-coded format validation. This ensures compatibility with new models and changing API key formats without requiring code updates.

#### LLM Configuration via API

LLM configuration is handled through API endpoints for security and flexibility:

```bash
# Get current configuration (API keys are hidden)
GET /api/config

# Configure the agent with LLM settings
PUT /api/config
{
  "provider": "openai",
  "api_key": "sk-your-key-here",
  "model": "gpt-4o-mini",
  "max_tokens": 800,
  "temperature": 0.3
}

# Alternative: Anthropic configuration  
PUT /api/config
{
  "provider": "anthropic",
  "api_key": "sk-ant-your-key-here", 
  "model": "claude-3-5-haiku-20241022",
  "max_tokens": 800,
  "temperature": 0.3
}

# Alternative: Google configuration  
PUT /api/config
{
  "provider": "google",
  "api_key": "your-google-api-key-here", 
  "model": "gemini-1.5-pro",
  "max_tokens": 800,
  "temperature": 0.3
}

# Validate configuration and test API connection
POST /api/config/validate

# Check if agent is configured
GET /api/config/status
```

## API Usage

The agent provides REST endpoints for:

### Core Endpoints

- **Health & Status**: `GET /health` - Service health check
- **Root**: `GET /` - Service information and OpenAPI documentation link

### Configuration Management

- `GET /api/config` - Get current configuration (without exposing API keys)
- `PUT /api/config` - Update agent configuration
- `POST /api/config/validate` - Validate configuration and API keys
- `GET /api/config/status` - Check if agent is properly configured

### Chat & Agent Interaction

- `GET /api/chat/status` - Get agent status and available tools
- `POST /api/chat/message` - Send a message to the agent
- `POST /api/chat/clear` - Clear conversation memory

### Documentation Management

The agent supports runtime documentation management via API:

- `GET /api/chat/docs/` - List all documentation files
- `GET /api/chat/docs/{filename}` - Get content of a specific documentation file
- `PUT /api/chat/docs/{filename}` - Update or create a documentation file
- `DELETE /api/chat/docs/{filename}` - Delete a documentation file  
- `POST /api/chat/docs/reload` - Reload all documentation from disk

### API Documentation

Interactive API documentation is available at `/docs` when running the service.

## Architecture

### Documentation-in-Context System

The agent uses a **documentation-in-context** approach that:

- **Direct Loading**: Loads all markdown documentation directly into LLM context
- **No Vector Store**: Eliminates the complexity and overhead of RAG/vector embeddings
- **Runtime Management**: Supports live documentation updates via API endpoints
- **Automatic Discovery**: Recursively finds and loads all `.md` files from the documentation path
- **Caching**: Efficiently caches documentation content with reload capability
- **Full Context**: Provides complete documentation context for comprehensive assistance

#### DocumentationLoader

The `DocumentationLoader` class handles:
- Loading all documentation from `VULKAN_DOCS_PATH`
- Caching documentation content for performance
- Runtime CRUD operations (create, read, update, delete)
- Hot reloading of documentation from disk
- Integration with LLM system prompts

### Database-backed Configuration

- **Persistent Storage**: Agent configuration stored in SQLite database
- **Runtime Updates**: Configuration can be updated via API without restarts
- **Validation**: API key validation and model compatibility checking
- **Migration Support**: Database schema versioning and migrations

### AgentToolsManager

The `AgentToolsManager` class provides a framework for extending the agent with custom tools:

- **Extensible Design**: Easy to add new tools for policy management, data sources, workflows, etc.
- **Tool Caching**: Efficient tool loading and management
- **Capability Reporting**: Automatic detection and reporting of available tools

Future tools will include:
- Policy management (create, update, delete policies)
- Data source management (connect, configure data sources)  
- Workflow orchestration (trigger, monitor workflows)
- File processing (upload, parse, analyze documents)

### Deployment & Configuration

The vulkan-agent follows the standard Vulkan project pattern:

#### Docker Configuration
- **Centralized Dockerfile**: Uses `/images/vulkan-agent.Dockerfile`
- **Environment Files**: Configuration via `config/active/vulkan-agent.env`
- **Documentation Volume**: Documentation mounted at `/app/docs` in container

#### Development vs Production
```bash
# Development (builds from source)
docker-compose -f docker-compose.dev.yaml up vulkan-agent

# Production (uses pre-built image)
docker-compose up vulkan-agent
```

#### Environment Configuration
The agent configuration follows the platform's config management pattern:
- `config/local/vulkan-agent.env` - Local development
- `config/dev/vulkan-agent.env` - Development environment  
- `config/prod/vulkan-agent.env` - Production environment
- `config/active/` - Symlinked to current environment

## Development Workflow

### Getting Started

1. **Clone and Setup**:
   ```bash
   cd vulkan-agent
   make install
   ```

2. **Run Tests**:
   ```bash
   make test-all  # Runs all tests with automatic cleanup
   ```

3. **Start Development**:
   ```bash
   # From project root
   docker-compose -f docker-compose.dev.yaml up vulkan-agent
   ```

4. **API Exploration**:
   Visit `http://localhost:8000/docs` for interactive API documentation

### Code Quality

- **Linting**: `make lint` - Check code quality and formatting
- **Formatting**: `make format` - Auto-format code with ruff
- **Testing**: Comprehensive test suite with unit and integration tests
- **Cleanup**: Automatic database cleanup after tests

### Key Files for Development

- `vulkan_agent/app.py` - FastAPI application setup
- `vulkan_agent/agent.py` - Core agent and tool management
- `vulkan_agent/knowledge_base.py` - Documentation loading system
- `vulkan_agent/config.py` - Configuration management
- `vulkan_agent/llm.py` - LLM abstraction layer

The agent is designed to be easily extensible - add new tools by extending the `AgentToolsManager` or new API endpoints in the `routers/` directory.
