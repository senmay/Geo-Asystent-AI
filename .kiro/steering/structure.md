# Project Structure

## Root Level Organization
```
/
├── backend/           # FastAPI Python backend
├── frontend/          # React TypeScript frontend
├── sample_data/       # GIS sample data files (.shp, .dbf, etc.)
├── .kiro/            # Kiro AI assistant configuration
├── .env              # Environment variables
└── README.md         # Project documentation
```

## Backend Structure (`/backend/`)

### Core Application
- `main.py` - FastAPI app entry point with CORS and router setup
- `database.py` - SQLAlchemy configuration and session management
- `requirements.txt` - Python dependencies

### Modular Architecture
- `config/` - Centralized Pydantic settings management
- `api/routers/` - FastAPI route handlers (chat, layers)
- `services/` - Business logic (agent_service, llm_service, etc.)
- `models/` - Pydantic schemas and domain models
- `repositories/` - Database access layer
- `tools/` - GIS operations and utility functions
- `middleware/` - Custom middleware (logging, monitoring, error handling)
- `exceptions/` - Custom exception classes
- `utils/` - Shared utility functions
- `tests/` - Test suite with pytest

### Key Patterns
- **Dependency Injection**: FastAPI dependencies for database sessions
- **Settings Management**: Centralized configuration with environment variables
- **Layered Architecture**: Clear separation between API, business logic, and data layers
- **Error Handling**: Centralized exception handling middleware

## Frontend Structure (`/frontend/src/`)

### Core Components
- `App.tsx` - Main application orchestrating map and chat
- `main.tsx` - React application bootstrap

### Feature Modules
- **Map Components**:
  - `GeoJsonLayer.tsx` - GeoJSON data visualization
  - `LayerControl.tsx` - Layer visibility management
  - `mapStyles.ts` - Centralized styling configuration
- **Chat Interface**:
  - `Chat.tsx` - Natural language query interface

### Configuration
- `package.json` - Dependencies and build scripts
- `vite.config.ts` - Vite bundler configuration
- `tsconfig.json` - TypeScript compiler settings
- `eslint.config.js` - Code linting rules

## Database Schema Conventions

### Table Naming
- Primary tables: `parcels`, `buildings`, `gpz_110kv`
- Low-resolution variants: `parcels_low`, `buildings_low`
- Geometry columns: `geometry` or `geom`
- Primary keys: `ID_DZIALKI`, `ID_BUDYNKU`, `id`

### Coordinate Systems
- Storage: Projected CRS (varies by data source)
- Web display: WGS84 (EPSG:4326)
- Automatic reprojection in GIS tools

## API Conventions

### Endpoints
- Base URL: `/api/v1/`
- Chat endpoint: `POST /api/v1/chat`
- Layer endpoint: `GET /api/v1/layers/{layer_name}`
- Documentation: `/api/docs` (Swagger UI)

### Response Formats
- GeoJSON for spatial data
- Consistent error response structure
- Polish language for user-facing messages

## File Naming Conventions
- Python: `snake_case` for files and functions
- TypeScript: `PascalCase` for components, `camelCase` for functions
- Configuration files: `lowercase` with extensions
- Test files: `test_*.py` pattern