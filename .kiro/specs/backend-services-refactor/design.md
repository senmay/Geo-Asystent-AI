# Design Document

## Overview

This design document outlines the refactoring approach for backend services in Geo-Asystent AI. The refactoring will transform the current service layer into a more maintainable, production-ready codebase following SOLID principles and best practices for logging, error handling, and code organization.

## Architecture

### Current Architecture Issues

The current backend services suffer from several architectural problems:

1. **Mixed Responsibilities**: Service methods handle validation, business logic, data processing, and response formatting
2. **Code Duplication**: Similar logic for result limiting, message formatting, and error handling is repeated across services
3. **Poor Error Handling**: Generic exception catching and inconsistent error reporting
4. **Logging Issues**: Mix of print() statements and proper logging, inconsistent log levels
5. **Tight Coupling**: Services directly handle response formatting and data transformation

### Target Architecture

The refactored architecture will implement clear separation of concerns:

```
API Layer (Routers)
    ↓
Service Layer (Business Logic)
    ↓
Repository Layer (Data Access)
    ↓
Utility Layer (Shared Functions)
```

## Components and Interfaces

### 1. Logging Infrastructure

#### LoggerMixin
```python
class LoggerMixin:
    """Mixin to provide consistent logging across all services."""
    
    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(f"{self.__module__}.{self.__class__.__name__}")
    
    def log_operation_start(self, operation: str, **kwargs):
        """Log the start of an operation with context."""
        
    def log_operation_success(self, operation: str, duration: float, **kwargs):
        """Log successful completion of an operation."""
        
    def log_operation_error(self, operation: str, error: Exception, **kwargs):
        """Log operation failure with full context."""
```

#### Structured Logging
- All log messages will include structured data for monitoring
- Operation timing will be automatically tracked
- Error context will be preserved and logged

### 2. Error Handling Framework

#### Existing Exception System
The application already has a well-designed exception hierarchy:

- **GeoAsystentException**: Base exception with logging, error codes, and user messages
- **GIS Exceptions**: LayerNotFoundError, InvalidLayerNameError, GISDataProcessingError, DatabaseConnectionError, SpatialQueryError
- **LLM Exceptions**: LLMServiceError, IntentClassificationError, LLMTimeoutError, LLMAPIKeyError

#### Enhanced Error Handling
We'll enhance the existing system by:
- Adding VALIDATION_ERROR to ErrorCode enum
- Creating ValidationError exception class
- Improving context preservation in existing exceptions

#### Error Handler Decorator
```python
def handle_service_errors(operation_name: str):
    """Decorator to standardize error handling across service methods."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Automatic logging, error handling, and context preservation
```

### 3. Shared Utilities

#### Result Processing Utilities
The application already has `limit_results_for_display()` function duplicated in `gis_service.py` and `gis_tools.py`. We'll:

1. **Consolidate existing function**: Move to `utils/result_processor.py`
2. **Enhance with additional utilities**:

```python
class ResultProcessor:
    """Centralized result processing and formatting."""
    
    @staticmethod
    def limit_results_for_display(gdf: gpd.GeoDataFrame, max_display: int = 5, 
                                 item_type: str = "działka") -> Tuple[gpd.GeoDataFrame, Optional[str]]:
        """Existing function - consolidated from duplicated code."""
        
    @staticmethod
    def add_parcel_messages(gdf: gpd.GeoDataFrame, config: LayerConfig) -> gpd.GeoDataFrame:
        """Add descriptive messages to parcel results."""
        
    @staticmethod
    def to_geojson_with_reprojection(gdf: gpd.GeoDataFrame, target_crs: str = "EPSG:4326") -> str:
        """Convert GeoDataFrame to GeoJSON with proper CRS handling."""
```

#### Validation Utilities
The application has some validation scattered across services. We'll consolidate into:

```python
class ValidationUtils:
    """Centralized validation logic."""
    
    @staticmethod
    def validate_positive_number(value: Union[int, float], param_name: str):
        """Validate that a number is positive - raises ValidationError."""
        
    @staticmethod
    def validate_non_empty_string(value: str, param_name: str):
        """Validate that a string is not empty - raises ValidationError."""
        
    @staticmethod
    def validate_parcel_criteria(criteria: ParcelCriteria):
        """Validate parcel search criteria - consolidate existing logic."""
```

#### New ValidationError Exception
```python
class ValidationError(GeoAsystentException):
    """Raised when input validation fails."""
    
    def __init__(self, parameter: str, value: Any, reason: str):
        details = {"parameter": parameter, "value": str(value), "reason": reason}
        super().__init__(
            message=f"Validation failed for parameter '{parameter}': {reason}",
            code=ErrorCode.VALIDATION_ERROR,
            details=details,
            user_message=f"Nieprawidłowa wartość parametru '{parameter}': {reason}"
        )
```

### 4. Refactored Service Classes

#### LLMService Refactoring
```python
class LLMService(LoggerMixin):
    """Refactored LLM service with clear separation of concerns."""
    
    def __init__(self):
        self._llm = None  # Lazy initialization
        self._prompt_loader = PromptLoader()
        
    @handle_service_errors("chat_response_generation")
    def generate_chat_response(self, query: str, context: Optional[str] = None) -> str:
        """Generate chat response - focused only on LLM interaction."""
        # Validation separated
        # Core LLM logic only
        # Error handling standardized
        
    def _validate_query(self, query: str):
        """Separate validation method."""
        
    def _prepare_prompt(self, query: str, context: Optional[str]) -> PromptTemplate:
        """Separate prompt preparation."""
        
    def _execute_llm_request(self, prompt: PromptTemplate, input_data: Dict) -> str:
        """Core LLM execution logic."""
```

#### GISService Refactoring
```python
class GISService(LoggerMixin):
    """Refactored GIS service with clear operation separation."""
    
    def __init__(self, db_engine: Engine):
        self.repository = GISRepository(db_engine)
        self.result_processor = ResultProcessor()
        
    @handle_service_errors("largest_parcel_search")
    def find_largest_parcel(self) -> str:
        """Find largest parcel - simplified and focused."""
        # Input validation
        # Repository call
        # Result processing
        # Response formatting
        
    def _process_parcel_results(self, gdf: gpd.GeoDataFrame, 
                               operation_type: str) -> gpd.GeoDataFrame:
        """Centralized result processing for all parcel operations."""
```

#### IntentService Refactoring
```python
class IntentClassificationService(LoggerMixin):
    """Simplified intent classification focused on core responsibility."""
    
    @handle_service_errors("intent_classification")
    def classify_intent(self, query: str) -> Dict[str, Any]:
        """Classify intent - focused only on classification logic."""
        # Validation
        # LLM classification
        # Result parsing
        # No business logic mixing
```

## Data Models

### Enhanced Domain Models
```python
@dataclass
class OperationContext:
    """Context information for operations."""
    operation_id: str
    user_query: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.now)

@dataclass
class ServiceResult:
    """Standardized service operation result."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    context: Optional[OperationContext] = None
    duration: Optional[float] = None
```

### Configuration Models
```python
@dataclass
class ServiceConfig:
    """Service-specific configuration."""
    max_results_display: int = 5
    default_timeout: int = 30
    enable_caching: bool = True
    log_level: str = "INFO"
```

## Error Handling

### Error Handling Strategy

1. **Specific Exception Catching**: Replace generic `Exception` catches with specific exception types
2. **Context Preservation**: All errors include operation context and parameters
3. **Automatic Logging**: Errors are automatically logged with full context
4. **Graceful Degradation**: Services provide fallback mechanisms where appropriate
5. **User-Friendly Messages**: Technical errors are translated to user-friendly messages

### Error Flow
```
Service Method
    ↓
Validation (ValidationError)
    ↓
Repository Call (DatabaseError, SpatialQueryError)
    ↓
Data Processing (DataProcessingError)
    ↓
Response Formatting (FormattingError)
    ↓
Automatic Error Logging & User Message Generation
```

## Testing Strategy

### Unit Testing Approach
1. **Service Method Testing**: Each refactored method will have comprehensive unit tests
2. **Error Scenario Testing**: All error paths will be tested with specific scenarios
3. **Utility Function Testing**: Shared utilities will have dedicated test suites
4. **Mock Strategy**: External dependencies (database, LLM) will be properly mocked

### Integration Testing
1. **Service Integration**: Test service interactions with repositories
2. **Error Handling Integration**: Test error propagation through layers
3. **Logging Integration**: Verify proper logging behavior

### Test Structure
```python
class TestGISService:
    def test_find_largest_parcel_success(self):
        """Test successful parcel finding."""
        
    def test_find_largest_parcel_no_results(self):
        """Test handling when no parcels found."""
        
    def test_find_largest_parcel_database_error(self):
        """Test database error handling."""
        
    def test_find_largest_parcel_logging(self):
        """Test proper logging behavior."""
```

## Implementation Phases

### Phase 1: Infrastructure Setup
1. Create logging infrastructure and mixins
2. Implement error handling framework
3. Create shared utility classes
4. Set up enhanced testing framework

### Phase 2: Service Refactoring
1. Refactor LLMService with new patterns
2. Refactor GISService with separation of concerns
3. Refactor IntentService for simplicity
4. Update LayerConfigService for consistency

### Phase 3: Integration and Testing
1. Update API routers to use refactored services
2. Implement comprehensive test suites
3. Update error handling middleware
4. Performance testing and optimization

### Phase 4: Documentation and Monitoring
1. Update service documentation
2. Implement monitoring and metrics
3. Create troubleshooting guides
4. Performance benchmarking

## Monitoring and Observability

### Logging Strategy
- **Structured Logging**: All logs include operation context
- **Performance Metrics**: Automatic timing for all operations
- **Error Tracking**: Comprehensive error logging with context
- **Business Metrics**: Track operation success rates and patterns

### Key Metrics to Track
1. Service operation response times
2. Error rates by service and operation type
3. Database query performance
4. LLM request success rates and timing
5. Memory usage patterns
6. Concurrent request handling

This design provides a clear roadmap for transforming the current backend services into a maintainable, production-ready codebase that follows best practices and provides excellent debugging and monitoring capabilities.