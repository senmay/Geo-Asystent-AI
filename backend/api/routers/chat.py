"""Chat API router for natural language queries."""

import logging
from fastapi import APIRouter, Depends, HTTPException

from models.schemas import ChatRequest, ChatResponse
from services import IntentClassificationService, LLMService, GISService
from api.dependencies import get_intent_service, get_llm_service, get_gis_service
from exceptions import GeoAsystentException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def process_chat(
    request: ChatRequest,
    intent_service: IntentClassificationService = Depends(get_intent_service),
    llm_service: LLMService = Depends(get_llm_service),
    gis_service: GISService = Depends(get_gis_service)
):
    """
    Process a natural language query and return the appropriate response.
    
    The query is first classified to determine the user's intent, then routed
    to the appropriate service for processing.
    """
    query = request.query
    logger.info(f"Processing chat request: '{query}'")
    
    try:
        # Classify intent
        route_details = intent_service.classify_intent(query)
        intent = route_details.get("intent")
        logger.info(f"Classified intent: '{intent}' with details: {route_details}")
        
        # Process based on intent
        if intent == 'find_largest_parcel':
            geojson_data = gis_service.find_largest_parcel()
            return ChatResponse(type="geojson", data=geojson_data, intent=intent)
        
        elif intent == 'find_n_largest_parcels':
            geojson_data = gis_service.find_n_largest_parcels(route_details['n'])
            return ChatResponse(type="geojson", data=geojson_data, intent=intent)
        
        elif intent == 'find_parcels_above_area':
            geojson_data = gis_service.find_parcels_above_area(route_details['min_area'])
            return ChatResponse(type="geojson", data=geojson_data, intent=intent)

        elif intent == 'find_parcels_without_buildings':
            geojson_data = gis_service.find_parcels_without_buildings()
            return ChatResponse(type="geojson", data=geojson_data, intent=intent)            
        
        elif intent == 'find_parcels_near_gpz':
            geojson_data = gis_service.find_parcels_near_gpz(route_details['radius_meters'])
            return ChatResponse(type="geojson", data=geojson_data, intent=intent)
        
        else:  # Intent is 'chat' or fallback
            response_text = llm_service.generate_chat_response(query)
            return ChatResponse(type="text", data=response_text, intent=intent)
    
    except GeoAsystentException as e:
        # Custom exceptions are handled by middleware
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))