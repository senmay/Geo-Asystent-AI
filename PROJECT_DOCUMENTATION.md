# Geo-Asystent AI - Project Documentation

## Project Overview

Geo-Asystent AI is a GIS (Geographic Information System) chatbot application that allows users to interact with geospatial data through natural language queries. The system combines modern web technologies with AI/LLM capabilities to provide an intuitive interface for GIS operations.

### Core Functionality
- **Natural Language Processing**: Users can ask questions in Polish about GIS data (e.g., "pokaż największą działkę", "znajdź budynki w pobliżu GPZ")
- **Interactive Mapping**: Leaflet-based map interface displaying geospatial data
- **GIS Operations**: Spatial queries, buffering, area calculations using PostGIS
- **AI-Powered Intent Classification**: LLM (Groq/Llama3) interprets user queries and routes them to appropriate GIS operations

### Technology Stack
- **Frontend**: React 19, TypeScript, Leaflet, Vite
- **Backend**: Python 3.12, FastAPI, SQLAlchemy, GeoAlchemy2
- **Database**: PostgreSQL with PostGIS extension
- **AI/LLM**: LangChain with Groq (Llama3-8b-8192)
- **GIS Processing**: GeoPandas, Shapely

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   External      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   Services      │
│                 │    │                 │    │                 │
│ • Map Interface │    │ • API Routes    │    │ • PostgreSQL    │
│ • Chat UI       │    │ • LLM Service   │    │ • PostGIS       │
│ • Layer Control │    │ • GIS Tools     │    │ • Groq LLM      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## File Structure and Specifications

### Backend Structure (`/backend/`)

#### Core Application Files

**`main.py`** - FastAPI Application Entry Point
- **Purpose**: Main application setup, CORS configuration, router registration
- **Key Components**:
  - FastAPI app instance with metadata
  - CORS middleware configuration (currently allows all origins)
  - Router inclusion for chat and layers endpoints
  - Root endpoint returning welcome message
- **Dependencies**: FastAPI, routers (chat, layers)
- **Configuration**: CORS origins set to ["*"] for development

**`database.py`** - Database Configuration and Connection Management
- **Purpose**: SQLAlchemy engine setup, session management, database dependencies
- **Key Components**:
  - Environment variable loading from `.env` file
  - PostgreSQL connection string construction
  - SQLAlchemy engine and session factory creation
  - Dependency functions for FastAPI (get_db, get_db_engine)
- **Environment Variables Required**:
  - `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`
- **Error Handling**: Raises exception if database credentials are incomplete

**`requirements.txt`** - Python Dependencies
- **Core Dependencies**:
  - `fastapi` - Web framework
  - `uvicorn[standard]` - ASGI server
  - `geopandas` - Geospatial data processing
  - `shapely` - Geometric operations
  - `langchain`, `langchain-groq` - LLM integration
  - `sqlalchemy`, `geoalchemy2` - Database ORM
  - `psycopg2-binary` - PostgreSQL adapter
- **Testing**: `pytest`, `pytest-cov`

#### API Layer (`/backend/routers/`)

**`chat.py`** - Chat API Endpoint
- **Purpose**: Handles natural language queries from users
- **Endpoints**:
  - `POST /api/v1/chat` - Processes user queries
- **Request Model**: `ChatRequest` (contains query string)
- **Response**: JSON with type, data, and intent information
- **Business Logic**: Delegates to `agent_service.process_query()`

**`layers.py`** - GIS Layer API Endpoint
- **Purpose**: Direct access to GIS layers without AI processing
- **Endpoints**:
  - `GET /api/v1/layers/{layer_name}` - Returns GeoJSON for specified layer
- **Response**: Raw GeoJSON data with application/json content type
- **Error Handling**: Returns 404 HTTPException for invalid layers
- **Business Logic**: Uses `get_layer_as_geojson` tool function

#### Data Models (`/backend/models/`)

**`schemas.py`** - Pydantic Models for API
- **Purpose**: Request/response validation and serialization
- **Models**:
  - `ChatRequest`: Simple model with query string field
- **Usage**: FastAPI automatic validation and documentation generation

#### Business Logic (`/backend/services/`)

**`agent_service.py`** - Core AI and Query Processing Service
- **Purpose**: Intent classification, query routing, and response generation
- **Key Components**:
  - **LLM Configuration**: ChatGroq with Llama3-8b-8192 model
  - **Intent Models**: Pydantic models for different query types:
    - `GetGisData` - Layer visualization requests
    - `FindLargestParcel` - Single largest parcel queries
    - `FindNLargestParcels` - Multiple largest parcels
    - `FindParcelsAboveArea` - Area-based filtering
    - `FindParcelsNearGpz` - Proximity to GPZ points
    - `Chat` - General conversation
  - **Routing Logic**: LangChain pipeline for intent classification
  - **Query Processing**: Routes classified intents to appropriate GIS tools
- **Language**: Primarily Polish for user interaction
- **Error Handling**: Fallback to helpful error messages in Polish

#### GIS Operations (`/backend/tools/`)

**`gis_tools.py`** - GIS Data Processing Tools
- **Purpose**: Database queries, spatial operations, GeoJSON generation
- **Tools Available**:
  - `get_layer_as_geojson()` - Retrieves complete layers (parcels, buildings, GPZ)
  - `find_largest_parcel()` - Finds single largest parcel by area
  - `find_n_largest_parcels()` - Finds N largest parcels
  - `find_parcels_above_area()` - Filters parcels by minimum area
  - `find_parcels_near_gpz()` - Spatial proximity queries
- **Database Tables**:
  - `parcels_low` / `parcels` - Land parcels with ID_DZIALKI
  - `buildings_low` / `buildings` - Buildings with ID_BUDYNKU  
  - `gpz_110kv` - Electrical substations with id
- **Coordinate Systems**: Reprojects all data to WGS84 (EPSG:4326) for web display
- **Error Handling**: Graceful fallback from low-resolution to full-resolution tables

### Frontend Structure (`/frontend/src/`)

#### Main Application (`/frontend/src/`)

**`App.tsx`** - Main Application Component
- **Purpose**: Root component orchestrating map and chat interfaces
- **Key Features**:
  - State management for base layers and query results
  - Initial layer loading (GPZ, Buildings, Parcels)
  - Layer visibility toggling
  - Integration between map and chat components
- **Layout**: Split-pane design with map on left, chat on right
- **API Integration**: Fetches initial layers from backend on mount

**`main.tsx`** - Application Entry Point
- **Purpose**: React application bootstrap
- **Configuration**: React 19 with StrictMode

#### Map Components

**`GeoJsonLayer.tsx`** - GeoJSON Data Visualization Component
- **Purpose**: Renders GeoJSON data on Leaflet map
- **Key Features**:
  - Separates point and polygon/line geometries
  - Point clustering using MarkerClusterGroup
  - Dynamic styling based on layer type
  - Automatic map bounds fitting
  - Hover effects and tooltips
- **Styling**: Uses mapStyles.ts for consistent appearance
- **Performance**: Efficient rendering of large datasets

**`LayerControl.tsx`** - Map Layer Management Component
- **Purpose**: UI control for toggling layer visibility
- **Features**:
  - Collapsible panel design
  - Checkbox controls for each layer
  - Color swatches showing layer styling
  - Polish language labels
- **State Management**: Communicates with parent App component

**`mapStyles.ts`** - Map Styling Configuration
- **Purpose**: Centralized styling for different layer types
- **Point Styles**:
  - Default: Orange circles for general points
  - GPZ: Red circles with white borders for electrical substations
  - Highlight: Cyan for hover/selection states
- **Path Styles**:
  - Default: Blue lines/fills for general features
  - Parcels: Green outlines with minimal fill
- **Extensibility**: Easy to add new layer-specific styles

#### Chat Interface

**`Chat.tsx`** - Chat Interface Component
- **Purpose**: Natural language query interface
- **Key Features**:
  - Message history display
  - Real-time query processing
  - Intent classification feedback
  - GeoJSON result handling
  - Error message display
- **Language**: Polish UI and interactions
- **Integration**: Updates map through setQueryGeojson callback
- **User Experience**: Shows processing status and tool usage

#### Configuration Files

**`package.json`** - Frontend Dependencies and Scripts
- **Key Dependencies**:
  - React 19 with TypeScript support
  - Leaflet for mapping with React integration
  - Axios for HTTP requests
  - MarkerCluster for point aggregation
- **Development Tools**: Vite, ESLint, TypeScript compiler
- **Scripts**: dev, build, lint, preview

**`vite.config.ts`** - Build Tool Configuration
- **Purpose**: Vite bundler configuration for React
- **Plugins**: React plugin for JSX/TSX support

**`tsconfig.json`** - TypeScript Configuration
- **Purpose**: TypeScript compiler settings
- **Configuration**: Strict type checking, modern ES features

## Database Schema

### Core Tables

**`parcels` / `parcels_low`** - Land Parcels
- **Primary Key**: `ID_DZIALKI` (parcel identifier)
- **Geometry**: `geometry` column (polygon geometries)
- **Usage**: Property boundaries, area calculations
- **Optimization**: `_low` versions for faster queries with reduced precision

**`buildings` / `buildings_low`** - Building Footprints  
- **Primary Key**: `ID_BUDYNKU` (building identifier)
- **Geometry**: `geometry` column (polygon geometries)
- **Usage**: Building visualization and analysis

**`gpz_110kv`** - Electrical Substations
- **Primary Key**: `id`
- **Geometry**: `geom` column (point geometries)
- **Usage**: Infrastructure analysis, proximity queries

### Spatial Operations
- **Coordinate System**: Data stored in projected CRS, converted to WGS84 for web display
- **Spatial Indexing**: PostGIS spatial indexes for efficient queries
- **Area Calculations**: `ST_Area()` for parcel size analysis
- **Proximity Queries**: `ST_DWithin()` for distance-based filtering

## API Endpoints

### Chat API
```
POST /api/v1/chat
Content-Type: application/json

Request:
{
  "query": "pokaż największą działkę"
}

Response:
{
  "type": "geojson",
  "data": "{...geojson...}",
  "intent": "find_largest_parcel"
}
```

### Layer API
```
GET /api/v1/layers/{layer_name}
Accept: application/json

Response: Raw GeoJSON FeatureCollection
```

## Environment Configuration

### Required Environment Variables
```bash
# Database Configuration
DB_USER=your_db_user
DB_PASSWORD=your_db_password  
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_db_name

# LLM Configuration (Groq API)
GROQ_API_KEY=your_groq_api_key
```

### Development Setup
1. **Backend**: `cd backend && pip install -r requirements.txt && uvicorn main:app --reload`
2. **Frontend**: `cd frontend && npm install && npm run dev`
3. **Database**: PostgreSQL with PostGIS extension, sample data loaded

## Current Limitations and Technical Debt

### Architecture Issues
- **Monolithic Services**: `agent_service.py` handles too many responsibilities
- **Configuration**: Scattered configuration, no centralized settings management
- **Error Handling**: Inconsistent error handling patterns
- **Testing**: Limited test coverage

### Code Quality Issues
- **Mixed Languages**: Polish and English mixed in code and comments
- **Hard-coded Values**: API URLs, database table names embedded in code
- **Type Safety**: Missing type hints in several areas
- **Documentation**: Limited inline documentation

### Performance Considerations
- **Database Queries**: Some queries could be optimized
- **Frontend Bundle**: No code splitting or lazy loading
- **Caching**: No caching layer for frequently accessed data

## Development Workflow

### Adding New GIS Operations
1. Create new tool function in `gis_tools.py`
2. Add corresponding Pydantic model in `agent_service.py`
3. Update intent classification prompt
4. Add routing logic in `process_query()`
5. Test with frontend chat interface

### Adding New Layer Types
1. Ensure database table exists with proper geometry column
2. Update `get_layer_as_geojson()` tool with layer recognition
3. Add styling in `mapStyles.ts`
4. Update initial layer loading in `App.tsx`

### Debugging Common Issues
- **Database Connection**: Check environment variables and PostgreSQL service
- **LLM Errors**: Verify Groq API key and model availability
- **CORS Issues**: Check CORS configuration in `main.py`
- **Map Display**: Verify GeoJSON format and coordinate system (should be WGS84)

This documentation provides a comprehensive overview for AI assistants or developers working with the Geo-Asystent AI codebase. The refactoring spec in `.kiro/specs/code-refactoring/` contains detailed plans for improving the architecture and code quality.