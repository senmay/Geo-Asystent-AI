# Design Document

## Overview

This design document outlines the architectural improvements for refactoring the Geo-Asystent AI application. The refactoring will transform the current structure into a maintainable, scalable, and well-organized codebase following modern software engineering practices.

## Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Frontend (React + TypeScript)"
        UI[UI Components]
        Hooks[Custom Hooks]
        Services[API Services]
        Types[Type Definitions]
    end
    
    subgraph "Backend (FastAPI + Python)"
        API[API Layer]
        Services_BE[Service Layer]
        Repositories[Repository Layer]
        Models[Domain Models]
        Config[Configuration]
    end
    
    subgraph "External Services"
        DB[(PostgreSQL + PostGIS)]
        LLM[LLM Service (Groq)]
    end
    
    UI --> Hooks
    Hooks --> Services
    Services --> API
    API --> Services_BE
    Services_BE --> Repositories
    Repositories --> DB
    Services_BE --> LLM
```

### Backend Architecture Layers

1. **API Layer** - FastAPI routers handling HTTP requests/responses
2. **Service Layer** - Business logic and orchestration
3. **Repository Layer** - Data access abstraction
4. **Domain Models** - Core business entities and value objects
5. **Configuration Layer** - Centralized settings management

### Frontend Architecture Layers

1. **UI Components** - React components for presentation
2. **Custom Hooks** - Business logic and state management
3. **API Services** - HTTP client abstraction
4. **Type Definitions** - TypeScript interfaces and types

## Components and Interfaces

### Backend Components

#### Configuration Module
```python
# backend/config/settings.py
class DatabaseSettings(BaseSettings):
    host: str
    port: int
    name: str
    user: str
    password: str

class LLMSettings(BaseSettings):
    model: str
    temperature: float
    api_key: str

class APISettings(BaseSettings):
    host: str
    port: int
    cors_origins: List[str]

class Settings(BaseSettings):
    database: DatabaseSettings
    llm: LLMSettings
    api: APISettings
```

#### Repository Layer
```python
# backend/repositories/base.py
class BaseRepository(ABC):
    def __init__(self, db_engine: Engine):
        self.db_engine = db_engine

# backend/repositories/gis_repository.py
class GISRepository(BaseRepository):
    def get_layer_data(self, layer_config: LayerConfig) -> GeoDataFrame
    def find_parcels_by_criteria(self, criteria: ParcelCriteria) -> GeoDataFrame
    def find_parcels_near_point(self, point: Point, radius: float) -> GeoDataFrame
```

#### Service Layer
```python
# backend/services/intent_service.py
class IntentClassificationService:
    def classify_intent(self, query: str) -> IntentResult

# backend/services/gis_service.py
class GISService:
    def __init__(self, repository: GISRepository, intent_service: IntentClassificationService)
    def process_query(self, query: str) -> QueryResult

# backend/services/llm_service.py
class LLMService:
    def classify_intent(self, query: str, prompt_template: str) -> Dict
    def generate_response(self, query: str, context: str) -> str
```

#### Domain Models
```python
# backend/models/domain.py
@dataclass
class LayerConfig:
    name: str
    table_name: str
    geometry_column: str
    id_column: str

@dataclass
class ParcelCriteria:
    min_area: Optional[float] = None
    max_area: Optional[float] = None
    limit: Optional[int] = None

@dataclass
class QueryResult:
    type: Literal['geojson', 'text']
    data: Union[str, Dict]
    intent: str
    metadata: Dict[str, Any]
```

### Frontend Components

#### API Service Layer
```typescript
// frontend/src/services/api/client.ts
class APIClient {
    private baseURL: string;
    private httpClient: AxiosInstance;
    
    constructor(config: APIConfig);
    async request<T>(config: RequestConfig): Promise<T>;
}

// frontend/src/services/api/gis-api.ts
class GISAPIService {
    constructor(private client: APIClient);
    async sendChatMessage(query: string): Promise<ChatResponse>;
    async getLayer(layerName: string): Promise<GeoJSONData>;
}
```

#### Custom Hooks
```typescript
// frontend/src/hooks/useChat.ts
interface UseChatReturn {
    messages: Message[];
    sendMessage: (query: string) => Promise<void>;
    isLoading: boolean;
    error: string | null;
}

// frontend/src/hooks/useMapLayers.ts
interface UseMapLayersReturn {
    layers: LayerState[];
    toggleLayer: (id: number) => void;
    queryResult: GeoJSONData | null;
    setQueryResult: (data: GeoJSONData | null) => void;
}
```

#### Type Definitions
```typescript
// frontend/src/types/api.ts
interface ChatResponse {
    type: 'geojson' | 'text';
    data: string;
    intent: string;
    metadata?: Record<string, any>;
}

// frontend/src/types/map.ts
interface LayerState {
    id: number;
    name: string;
    data: GeoJSONData;
    visible: boolean;
    style: LayerStyle;
}
```

## Data Models

### Database Layer Models
```python
# backend/models/database.py
class LayerMetadata(BaseModel):
    name: str
    table_name: str
    geometry_column: str
    id_column: str
    display_name: str
    description: Optional[str]
    default_style: Dict[str, Any]
```

### API Models
```python
# backend/models/api.py
class ChatRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    type: Literal['geojson', 'text']
    data: str
    intent: str
    metadata: Optional[Dict[str, Any]] = None

class LayerResponse(BaseModel):
    name: str
    data: Dict[str, Any]  # GeoJSON
    feature_count: int
    bounds: List[float]
```

## Error Handling

### Backend Error Handling
```python
# backend/exceptions/base.py
class GeoAsystentException(Exception):
    def __init__(self, message: str, code: str, details: Optional[Dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}

# backend/exceptions/gis.py
class LayerNotFoundError(GeoAsystentException):
    def __init__(self, layer_name: str):
        super().__init__(
            message=f"Layer '{layer_name}' not found",
            code="LAYER_NOT_FOUND",
            details={"layer_name": layer_name}
        )

# backend/middleware/error_handler.py
@app.exception_handler(GeoAsystentException)
async def handle_geoasystent_exception(request: Request, exc: GeoAsystentException):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "message": exc.message,
                "code": exc.code,
                "details": exc.details
            }
        }
    )
```

### Frontend Error Handling
```typescript
// frontend/src/utils/error-handler.ts
class ErrorHandler {
    static handleAPIError(error: AxiosError): UserFriendlyError {
        // Convert API errors to user-friendly messages
    }
    
    static logError(error: Error, context: string): void {
        // Log errors for debugging
    }
}

// frontend/src/hooks/useErrorHandler.ts
interface UseErrorHandlerReturn {
    error: string | null;
    setError: (error: string | null) => void;
    handleError: (error: Error) => void;
    clearError: () => void;
}
```

## Testing Strategy

### Backend Testing
1. **Unit Tests** - Test individual functions and classes
2. **Integration Tests** - Test API endpoints and database operations
3. **Repository Tests** - Test data access layer
4. **Service Tests** - Test business logic

### Frontend Testing
1. **Component Tests** - Test React components in isolation
2. **Hook Tests** - Test custom hooks
3. **Integration Tests** - Test component interactions
4. **API Service Tests** - Test API communication

### Test Structure
```
backend/tests/
├── unit/
│   ├── services/
│   ├── repositories/
│   └── models/
├── integration/
│   ├── api/
│   └── database/
└── fixtures/

frontend/src/tests/
├── components/
├── hooks/
├── services/
└── utils/
```

## File Organization

### Backend Structure
```
backend/
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── database.py
├── models/
│   ├── __init__.py
│   ├── domain.py
│   ├── database.py
│   └── api.py
├── repositories/
│   ├── __init__.py
│   ├── base.py
│   └── gis_repository.py
├── services/
│   ├── __init__.py
│   ├── intent_service.py
│   ├── gis_service.py
│   └── llm_service.py
├── api/
│   ├── __init__.py
│   ├── dependencies.py
│   └── routers/
│       ├── __init__.py
│       ├── chat.py
│       └── layers.py
├── exceptions/
│   ├── __init__.py
│   ├── base.py
│   └── gis.py
├── middleware/
│   ├── __init__.py
│   ├── error_handler.py
│   └── logging.py
├── templates/
│   └── prompts/
│       ├── intent_classification.txt
│       └── chat_response.txt
└── main.py
```

### Frontend Structure
```
frontend/src/
├── components/
│   ├── common/
│   ├── map/
│   └── chat/
├── hooks/
│   ├── useChat.ts
│   ├── useMapLayers.ts
│   └── useErrorHandler.ts
├── services/
│   ├── api/
│   │   ├── client.ts
│   │   └── gis-api.ts
│   └── storage/
├── types/
│   ├── api.ts
│   ├── map.ts
│   └── common.ts
├── utils/
│   ├── error-handler.ts
│   ├── formatters.ts
│   └── constants.ts
├── styles/
│   ├── globals.css
│   ├── components/
│   └── themes/
└── App.tsx
```

## Migration Strategy

The refactoring will be implemented in phases to minimize disruption:

### Phase 1: Backend Foundation
1. Create configuration module
2. Implement error handling infrastructure
3. Set up logging and monitoring

### Phase 2: Backend Service Layer
1. Extract repository layer
2. Separate service classes
3. Refactor API routers

### Phase 3: Frontend Infrastructure
1. Create API service layer
2. Implement custom hooks
3. Add type definitions

### Phase 4: Integration and Testing
1. Update tests for new structure
2. Integration testing
3. Performance validation

### Phase 5: Documentation and Cleanup
1. Update documentation
2. Remove deprecated code
3. Final code review