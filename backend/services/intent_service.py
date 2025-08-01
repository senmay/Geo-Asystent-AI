"""Intent classification service for natural language query processing."""

import logging
from typing import Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import Literal, Union

from config import get_settings
from exceptions import (
    IntentClassificationError,
    LLMServiceError,
    LLMTimeoutError,
    LLMAPIKeyError,
    ValidationError
)
from utils import LLMOperationLogger
from templates import PromptLoader

logger = logging.getLogger(__name__)


# --- Pydantic Models for each Intent ---
# Removed GetGisData - no longer supported


class FindLargestParcel(BaseModel):
    """Użytkownik chce znaleźć pojedynczą największą działkę."""
    intent: Literal['find_largest_parcel'] = "find_largest_parcel"


class FindNLargestParcels(BaseModel):
    """Użytkownik chce znaleźć określoną liczbę największych działek."""
    intent: Literal['find_n_largest_parcels'] = "find_n_largest_parcels"
    n: int = Field(description="Liczba największych działek do znalezienia.")


class FindParcelsAboveArea(BaseModel):
    """Użytkownik chce znaleźć wszystkie działki o powierzchni powyżej określonego progu."""
    intent: Literal['find_parcels_above_area'] = "find_parcels_above_area"
    min_area: float = Field(description="Minimalna powierzchnia w metrach kwadratowych.")


class FindParcelsNearGpz(BaseModel):
    """Użytkownik chce znaleźć działki w określonej odległości od GPZ."""
    intent: Literal['find_parcels_near_gpz'] = "find_parcels_near_gpz"
    radius_meters: int = Field(description="Promień w metrach od GPZ.")


class FindParcelsWithoutBuildings(BaseModel):
    """Użytkownik chce znaleźć działki bez budynków."""
    intent: Literal['find_parcels_without_buildings'] = "find_parcels_without_buildings"


class ExportToPdf(BaseModel):
    """Użytkownik chce wyeksportować wyniki do pliku PDF."""
    intent: Literal['export_to_pdf'] = "export_to_pdf"


class Chat(BaseModel):
    """Użytkownik prowadzi luźną rozmowę, zadaje ogólne pytanie lub jego intencja jest niejasna."""
    intent: Literal['chat'] = "chat"


# --- Simplified Route Model ---
class Route(BaseModel):
    intent: str = Field(description="Intent name")
    n: Optional[int] = Field(None, description="Number for n_largest_parcels")
    min_area: Optional[float] = Field(None, description="Min area for parcels_above_area")
    radius_meters: Optional[int] = Field(None, description="Radius for parcels_near_gpz")


class IntentClassificationService:
    """Service for classifying user intents from natural language queries."""
    
    def __init__(self):
        """Initialize the intent classification service."""
        self.settings = get_settings()
        self.llm = None  # Lazy initialization
        self.parser = JsonOutputParser(pydantic_object=Route)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Load prompt template
        self.prompt_template = self._load_prompt_template()
    
    def _get_llm(self) -> ChatGroq:
        """Get configured LLM instance with lazy initialization."""
        if self.llm is None:
            try:
                self.llm = ChatGroq(
                    model_name=self.settings.llm.model,
                    temperature=self.settings.llm.temperature,
                    api_key=self.settings.llm.api_key,
                    timeout=self.settings.llm.timeout
                )
                self.logger.info(f"LLM initialized: {self.settings.llm.model}")
            except ValueError as e:
                if "api_key" in str(e).lower():
                    raise LLMAPIKeyError()
                else:
                    raise LLMServiceError(
                        operation="LLM initialization",
                        original_error=e
                    )
            except Exception as e:
                self.logger.error(f"Unexpected error during LLM initialization: {e}")
                raise LLMServiceError(
                    operation="LLM initialization",
                    original_error=e
                )
        return self.llm
    
    def _load_prompt_template(self) -> PromptTemplate:
        """Load the intent classification prompt template from file."""
        try:
            prompt_loader = PromptLoader()
            return prompt_loader.create_prompt_template(
                template_name="intent_classification",
                input_variables=["query"],
                partial_variables={"format_instructions": self.parser.get_format_instructions()}
            )
        except (FileNotFoundError, KeyError) as e:
            self.logger.error(f"Failed to load intent classification template: {e}")
            # Fallback to basic template if file loading fails
        except Exception as e:
            self.logger.error(f"Unexpected error loading intent classification template: {e}")
            # Fallback to basic template if file loading fails
            fallback_template = """Classify the user query into one of the supported intents and return JSON.
Query: {query}
Schema: {format_instructions}"""
            return PromptTemplate(
                template=fallback_template,
                input_variables=["query"],
                partial_variables={"format_instructions": self.parser.get_format_instructions()}
            )
    
    def classify_intent(self, query: str) -> Dict[str, Any]:
        """
        Classify user intent from natural language query.
        
        Args:
            query: User's natural language query
            
        Returns:
            Dictionary with classified intent and parameters
            
        Raises:
            IntentClassificationError: If classification fails
            LLMTimeoutError: If LLM request times out
            LLMServiceError: If LLM service fails
        """
        if not query or not query.strip():
            raise ValidationError("query", query, "cannot be empty or whitespace only")
        
        self.logger.info(f"Classifying intent for query: '{query}'")
        
        try:
            # Get LLM instance
            llm = self._get_llm()
            
            # Create classification chain
            classification_chain = self.prompt_template | llm | self.parser
            
            # Execute classification with timeout handling
            import time
            start_time = time.time()
            
            try:
                response = classification_chain.invoke({"query": query})
                duration = time.time() - start_time
                
                # Extract route details - now response is directly the route
                route_details = response
                intent = route_details.get("intent")
                
                if not intent:
                    raise IntentClassificationError(
                        query=query,
                        original_error=ValueError("No intent found in response")
                    )
                
                # Log successful classification
                LLMOperationLogger.log_intent_classification(
                    query=query,
                    intent=intent,
                    duration=duration
                )
                
                self.logger.info(f"Intent classified: '{query}' -> {intent} ({duration:.3f}s)")
                
                return route_details
                
            except TimeoutError as e:
                duration = time.time() - start_time
                self.logger.error(f"Intent classification timed out after {duration:.3f}s for query: '{query}'")
                raise LLMTimeoutError(
                    timeout_seconds=self.settings.llm.timeout,
                    operation="intent classification"
                )
            except ValueError as e:
                if "api_key" in str(e).lower():
                    raise LLMAPIKeyError()
                else:
                    raise IntentClassificationError(
                        query=query,
                        original_error=e
                    )
            except Exception as e:
                duration = time.time() - start_time
                self.logger.error(f"Unexpected error during intent classification after {duration:.3f}s: {e}")
                
                # Check for timeout based on duration
                if duration >= self.settings.llm.timeout:
                    raise LLMTimeoutError(
                        timeout_seconds=self.settings.llm.timeout,
                        operation="intent classification"
                    )
                
                # Re-raise as classification error
                raise IntentClassificationError(
                    query=query,
                    original_error=e
                )
                
        except (IntentClassificationError, LLMTimeoutError, LLMAPIKeyError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during intent classification for query '{query}': {e}")
            raise LLMServiceError(
                operation=f"intent classification for query '{query}'",
                original_error=e
            )
    
    def get_supported_intents(self) -> Dict[str, str]:
        """
        Get list of supported intents with descriptions.
        
        Returns:
            Dictionary mapping intent names to descriptions
        """
        return {
            "find_largest_parcel": "Znalezienie największej działki",
            "find_n_largest_parcels": "Znalezienie N największych działek",
            "find_parcels_above_area": "Znalezienie działek powyżej określonej powierzchni",
            "find_parcels_near_gpz": "Znalezienie działek w pobliżu GPZ",
            "find_parcels_without_buildings": "Znalezienie działek bez budynków",
            "export_to_pdf": "Eksport wyników do pliku PDF",
            "chat": "Ogólna rozmowa lub pytania pomocnicze"
        }
    
    def validate_intent_parameters(self, intent: str, parameters: Dict[str, Any]) -> bool:
        """
        Validate parameters for a given intent.
        
        Args:
            intent: Intent name
            parameters: Intent parameters
            
        Returns:
            True if parameters are valid
            
        Raises:
            ValueError: If parameters are invalid
        """
        if intent == "find_n_largest_parcels":
            n = parameters.get("n")
            if not n or n <= 0:
                raise ValidationError("n", n, "must be a positive integer")
        
        elif intent == "find_parcels_above_area":
            min_area = parameters.get("min_area")
            if min_area is None or min_area < 0:
                raise ValidationError("min_area", min_area, "must be non-negative")
        
        elif intent == "find_parcels_near_gpz":
            radius = parameters.get("radius_meters")
            if not radius or radius <= 0:
                raise ValidationError("radius_meters", radius, "must be positive")
        
        # Removed get_gis_data validation - no longer supported
        
        return True