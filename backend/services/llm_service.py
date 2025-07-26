"""LLM service for chat responses and general language model operations."""

import logging
import time
from typing import Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

from config import get_settings
from exceptions import (
    LLMServiceError,
    LLMTimeoutError,
    LLMAPIKeyError,
    ValidationError
)
from utils.db_logger import LLMOperationLogger
from templates import PromptLoader

logger = logging.getLogger(__name__)


class LLMService:
    """Service for general LLM operations like chat responses."""
    
    def __init__(self):
        """Initialize the LLM service."""
        self.settings = get_settings()
        self.llm = None  # Lazy initialization
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Load chat prompt template
        self.chat_prompt_template = self._load_chat_prompt_template()
    
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
                self.logger.info(f"LLM initialized for chat: {self.settings.llm.model}")
            except ValueError as e:
                if "api_key" in str(e).lower():
                    self.logger.error(
                        f"Invalid API key during LLM initialization - "
                        f"model: {self.settings.llm.model}, timeout: {self.settings.llm.timeout}s"
                    )
                    raise LLMAPIKeyError()
                else:
                    self.logger.error(
                        f"ValueError during LLM initialization - "
                        f"model: {self.settings.llm.model}, temperature: {self.settings.llm.temperature}, "
                        f"timeout: {self.settings.llm.timeout}s - {e}"
                    )
                    raise LLMServiceError(
                        operation=f"LLM initialization (model: {self.settings.llm.model})",
                        original_error=e
                    )
            except Exception as e:
                self.logger.error(
                    f"Unexpected error during LLM initialization - "
                    f"model: {self.settings.llm.model}, temperature: {self.settings.llm.temperature}, "
                    f"timeout: {self.settings.llm.timeout}s - {e}"
                )
                raise LLMServiceError(
                    operation=f"LLM initialization (model: {self.settings.llm.model})",
                    original_error=e
                )
        return self.llm
    
    def _load_chat_prompt_template(self) -> PromptTemplate:
        """Load the chat response prompt template from file."""
        try:
            prompt_loader = PromptLoader()
            return prompt_loader.create_prompt_template(
                template_name="chat_response",
                input_variables=["query"]
            )
        except (FileNotFoundError, KeyError) as e:
            self.logger.error(f"Failed to load chat response template: {e}")
            # Fallback to basic template if file loading fails
        except Exception as e:
            self.logger.error(f"Unexpected error loading chat response template: {e}")
            # Fallback to basic template if file loading fails
            fallback_template = """Jesteś pomocnym asystentem GIS. Odpowiedz na pytanie użytkownika w języku polskim.

Pytanie: {query}

Odpowiedź:"""
            return PromptTemplate(
                template=fallback_template,
                input_variables=["query"]
            )
    
    def _validate_query(self, query: str) -> None:
        """
        Validate chat query input.
        
        Args:
            query: User's query to validate
            
        Raises:
            ValidationError: If query is invalid
        """
        if not query or not query.strip():
            raise ValidationError("query", query, "cannot be empty or whitespace only")
    
    def _prepare_prompt(self, query: str, context: Optional[str] = None) -> tuple[PromptTemplate, dict]:
        """
        Prepare prompt template and input data for LLM execution.
        
        Args:
            query: User's query
            context: Optional context information
            
        Returns:
            Tuple of (prompt_template, input_data)
        """
        prompt_input = {"query": query}
        
        if context:
            # Modify template to include context
            template_with_context = self.chat_prompt_template.template + f"\n\nKontekst: {context}\n\nOdpowiedź:"
            prompt = PromptTemplate(template=template_with_context, input_variables=["query"])
        else:
            prompt = self.chat_prompt_template
            
        return prompt, prompt_input
    
    def _execute_llm_request(self, prompt: PromptTemplate, prompt_input: dict, query: str) -> str:
        """
        Execute LLM request with proper error handling and logging.
        
        Args:
            prompt: Prepared prompt template
            prompt_input: Input data for the prompt
            query: Original user query for error context
            
        Returns:
            Generated response text
            
        Raises:
            LLMTimeoutError: If request times out
            LLMAPIKeyError: If API key is invalid
            LLMServiceError: If other errors occur
        """
        llm = self._get_llm()
        chat_chain = prompt | llm
        start_time = time.time()
        
        try:
            response = chat_chain.invoke(prompt_input)
            duration = time.time() - start_time
            
            # Extract response content
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Log successful response generation
            LLMOperationLogger.log_chat_response(
                query=query,
                response_length=len(response_text),
                duration=duration
            )
            
            self.logger.info(f"Chat response generated: {len(response_text)} chars ({duration:.3f}s)")
            return response_text
            
        except TimeoutError as e:
            duration = time.time() - start_time
            self.logger.error(
                f"LLM request timed out after {duration:.3f}s for query: '{query}' "
                f"(timeout limit: {self.settings.llm.timeout}s)"
            )
            raise LLMTimeoutError(
                timeout_seconds=self.settings.llm.timeout,
                operation=f"chat response generation for query: '{query[:50]}...'"
            )
        except ValueError as e:
            if "api_key" in str(e).lower():
                self.logger.error(f"API key error during chat response for query: '{query}' - {e}")
                raise LLMAPIKeyError()
            else:
                self.logger.error(f"ValueError during chat response for query: '{query}' - {e}")
                raise LLMServiceError(
                    operation=f"chat response generation for query: '{query[:50]}...'",
                    original_error=e
                )
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                f"Unexpected error during chat response generation after {duration:.3f}s "
                f"for query: '{query}' - {e}"
            )
            
            # Check for timeout based on duration
            if duration >= self.settings.llm.timeout:
                raise LLMTimeoutError(
                    timeout_seconds=self.settings.llm.timeout,
                    operation=f"chat response generation for query: '{query[:50]}...'"
                )
            
            raise LLMServiceError(
                operation=f"chat response generation for query: '{query[:50]}...'",
                original_error=e
            )

    def generate_chat_response(self, query: str, context: Optional[str] = None) -> str:
        """
        Generate a chat response for general queries.
        
        Args:
            query: User's query
            context: Optional context information
            
        Returns:
            Generated response text
            
        Raises:
            ValidationError: If query is invalid
            LLMServiceError: If response generation fails
            LLMTimeoutError: If request times out
            LLMAPIKeyError: If API key is invalid
        """
        # Step 1: Validate input
        self._validate_query(query)
        
        self.logger.info(f"Generating chat response for: '{query}'")
        
        try:
            # Step 2: Prepare prompt and input data
            prompt, prompt_input = self._prepare_prompt(query, context)
            
            # Step 3: Execute LLM request
            return self._execute_llm_request(prompt, prompt_input, query)
            
        except (LLMServiceError, LLMTimeoutError, LLMAPIKeyError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during chat response generation for query '{query}': {e}")
            raise LLMServiceError(
                operation=f"chat response generation for query: '{query[:50]}...'",
                original_error=e
            )
    
    def generate_help_response(self) -> str:
        """
        Generate a help response explaining system capabilities.
        
        Returns:
            Help text in Polish
        """
        return """🗺️ **Geo-Asystent AI - Twój asystent GIS**

**Co potrafię:**
• 📍 Wyświetlać warstwy GIS: "pokaż działki", "wczytaj budynki"
• 🏆 Znajdować największe działki: "największa działka", "10 największych działek"
• 📏 Filtrować według powierzchni: "działki większe niż 1000 m²"
• 📍 Wyszukiwać w pobliżu: "działki w pobliżu GPZ"
• ❓ Odpowiadać na pytania o GIS i mapy

**Przykłady zapytań:**
• "pokaż wszystkie działki"
• "znajdź 5 największych działek"
• "działki powyżej 500 metrów kwadratowych"
• "budynki w pobliżu stacji GPZ"

**Dostępne warstwy:**
• Działki (parcels)
• Budynki (buildings) 
• GPZ 110kV (stacje elektroenergetyczne)

Zadaj pytanie, a pomogę Ci z danymi GIS! 🚀"""
    
    def generate_error_fallback_response(self, error_type: str) -> str:
        """
        Generate a fallback response when errors occur.
        
        Args:
            error_type: Type of error that occurred
            
        Returns:
            User-friendly error message
        """
        fallback_responses = {
            "timeout": "Przepraszam, odpowiedź trwa zbyt długo. Spróbuj zadać prostsze pytanie lub spróbuj ponownie za chwilę.",
            "api_key": "Wystąpił problem z usługą AI. Skontaktuj się z administratorem systemu.",
            "classification": "Nie rozumiem tego zapytania. Spróbuj przeformułować lub zadaj pytanie o dane GIS.",
            "general": "Wystąpił nieoczekiwany błąd. Spróbuj ponownie lub zadaj inne pytanie."
        }
        
        base_response = fallback_responses.get(error_type, fallback_responses["general"])
        
        help_text = "\n\nMogę pomóc z:\n• Wyświetlaniem warstw GIS\n• Wyszukiwaniem działek\n• Pytaniami o dane przestrzenne"
        
        return base_response + help_text
    
    def test_llm_connection(self) -> bool:
        """
        Test LLM connection and functionality.
        
        Returns:
            True if LLM is working correctly
        """
        try:
            test_response = self.generate_chat_response("test")
            return len(test_response) > 0
        except (LLMServiceError, LLMTimeoutError, LLMAPIKeyError, ValidationError) as e:
            self.logger.error(f"LLM connection test failed with known error: {e.message}")
            return False
        except Exception as e:
            self.logger.error(f"LLM connection test failed with unexpected error: {e}")
            return False