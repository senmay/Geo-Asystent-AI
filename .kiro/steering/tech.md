# Technology Stack

## Backend
- **Framework**: FastAPI with Python 3.12
- **Database**: PostgreSQL with PostGIS extension
- **ORM**: SQLAlchemy with GeoAlchemy2 for spatial data
- **GIS Processing**: GeoPandas, Shapely
- **AI/LLM**: LangChain with Groq (Llama3-8b-8192 model)
- **Configuration**: Pydantic Settings with environment variables
- **Testing**: pytest with coverage reporting

## Frontend
- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite
- **Mapping**: Leaflet with React-Leaflet
- **HTTP Client**: Axios
- **Clustering**: Leaflet MarkerCluster
- **Linting**: ESLint with TypeScript support

## Development Environment
- **Language**: Mixed Polish/English (Polish for user-facing content, English for code)
- **Environment**: Windows with cmd shell
- **Package Management**: pip (backend), npm (frontend)

## Common Commands

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Testing
```bash
# Backend tests with coverage
cd backend
pytest --cov=backend --cov-report=html

# Frontend linting
cd frontend
npm run lint
```

### Database Setup
Requires PostgreSQL with PostGIS extension and sample GIS data loaded into tables:
- `parcels` / `parcels_low` (land parcels)
- `buildings` / `buildings_low` (building footprints)
- `gpz_110kv` (electrical substations)

## Environment Variables Required
```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# LLM Service
GROQ_API_KEY=your_groq_api_key
```
## Code writing method
- use KISS and DRY and YAGNI principles
- try to keep structure simple