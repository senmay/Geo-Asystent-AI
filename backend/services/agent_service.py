"""Main agent service orchestrating intent classification and GIS operations."""

import logging
from typing import Dict, Any

from config.database import engine
from exceptions import GeoAsystentException
from .intent_service import IntentClassificationService
from .llm_service import LLMService
from .gis_service import GISService

logger = logging.getLogger(__name__)

# Initialize services (lazy initialization)
_intent_service = None
_llm_service = None
_gis_service = None


def get_intent_service() -> IntentClassificationService:
    """Get intent classification service instance."""
    global _intent_service
    if _intent_service is None:
        _intent_service = IntentClassificationService()
    return _intent_service


def get_llm_service() -> LLMService:
    """Get LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def get_gis_service() -> GISService:
    """Get GIS service instance."""
    global _gis_service
    if _gis_service is None:
        _gis_service = GISService(engine)
    return _gis_service


# PDF export is now handled on the frontend

def process_query(query: str) -> dict:
    """
    Processes the user query by first routing it to the correct logic.
    """
    logger.info(f"Processing query: '{query}'")
    
    try:
        # Intent classification using separated service
        try:
            intent_service = get_intent_service()
            route_details = intent_service.classify_intent(query)
            intent = route_details.get("intent")
            logger.info(f"Routed to intent: '{intent}' with details: {route_details}")
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            raise

        # Handle different intents using separated services
        try:
            gis_service = get_gis_service()
            geojson_data = None
            
            if intent == 'find_largest_parcel':
                geojson_data = gis_service.find_largest_parcel()

            elif intent == 'find_n_largest_parcels':
                geojson_data = gis_service.find_n_largest_parcels(route_details['n'])

            elif intent == 'find_parcels_above_area':
                geojson_data = gis_service.find_parcels_above_area(route_details['min_area'])

            elif intent == 'find_parcels_near_gpz':
                geojson_data = gis_service.find_parcels_near_gpz(route_details['radius_meters'])

            elif intent == 'find_parcels_without_buildings':
                logger.info("Executing find_parcels_without_buildings function")
                try:
                    geojson_data = gis_service.find_parcels_without_buildings()
                    logger.info(f"Successfully got GeoJSON data: {len(geojson_data) if geojson_data else 0} characters")
                except Exception as e:
                    logger.error(f"Error in find_parcels_without_buildings: {e}", exc_info=True)
                    raise

            elif intent == 'export_to_pdf':
                # For PDF export, we need to handle it differently as it doesn't return GeoJSON
                try:
                    # This would typically use the last query result stored in session/context
                    # For now, return a message indicating PDF export functionality
                    return {
                        "type": "text", 
                        "data": "Funkcja eksportu do PDF została wywołana. W pełnej implementacji wyeksportowałaby ostatnie wyniki zapytania do pliku PDF.",
                        "intent": intent
                    }
                except Exception as e:
                    logger.error(f"PDF export failed: {e}")
                    return {
                        "type": "text",
                        "data": "Wystąpił błąd podczas eksportu do PDF. Spróbuj ponownie później.",
                        "intent": intent
                    }

            else: # Intent is 'chat' or fallback
                try:
                    llm_service = get_llm_service()
                    response_text = llm_service.generate_chat_response(query)
                    return {"type": "text", "data": response_text}
                except Exception as e:
                    logger.error(f"Chat response generation failed: {e}")
                    # Use fallback response
                    llm_service = get_llm_service()
                    fallback_response = llm_service.generate_error_fallback_response("general")
                    return {"type": "text", "data": fallback_response}

            # Return successful GIS operation result
            return {"type": "geojson", "data": geojson_data, "intent": intent}
            
        except GeoAsystentException:
            # Re-raise our custom exceptions to be handled by FastAPI exception handlers
            raise
        except Exception as e:
            logger.error(f"Service execution failed: {e}")
            raise

    except GeoAsystentException:
        # Re-raise our custom exceptions to be handled by FastAPI exception handlers
        raise
    except Exception as e:
        logger.error(f"Unexpected error during query processing: {e}")
        raise
