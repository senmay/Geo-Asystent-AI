"""Prompt template loader for LLM services."""

import logging
from pathlib import Path
from typing import Dict, Optional
from langchain_core.prompts import PromptTemplate

logger = logging.getLogger(__name__)


class PromptLoader:
    """Utility class for loading prompt templates from files."""
    
    def __init__(self):
        """Initialize the prompt loader."""
        self.templates_dir = Path(__file__).parent / "prompts"
        self._cache: Dict[str, str] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def load_template(self, template_name: str, use_cache: bool = True) -> str:
        """
        Load a prompt template from file.
        
        Args:
            template_name: Name of the template file (without .txt extension)
            use_cache: Whether to use cached version if available
            
        Returns:
            Template content as string
            
        Raises:
            FileNotFoundError: If template file doesn't exist
            IOError: If file cannot be read
        """
        if use_cache and template_name in self._cache:
            return self._cache[template_name]
        
        template_path = self.templates_dir / f"{template_name}.txt"
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if use_cache:
                self._cache[template_name] = content
            
            self.logger.debug(f"Loaded template: {template_name}")
            return content
            
        except Exception as e:
            self.logger.error(f"Failed to load template {template_name}: {e}")
            raise IOError(f"Cannot read template file {template_path}: {e}")
    
    def create_prompt_template(self, template_name: str, input_variables: list, 
                             partial_variables: Optional[Dict[str, str]] = None) -> PromptTemplate:
        """
        Create a LangChain PromptTemplate from a template file.
        
        Args:
            template_name: Name of the template file
            input_variables: List of input variable names
            partial_variables: Optional partial variables
            
        Returns:
            Configured PromptTemplate
        """
        template_content = self.load_template(template_name)
        
        return PromptTemplate(
            template=template_content,
            input_variables=input_variables,
            partial_variables=partial_variables or {}
        )
    
    def get_available_templates(self) -> list:
        """
        Get list of available template files.
        
        Returns:
            List of template names (without .txt extension)
        """
        if not self.templates_dir.exists():
            return []
        
        return [
            f.stem for f in self.templates_dir.glob("*.txt")
            if f.is_file()
        ]
    
    def clear_cache(self):
        """Clear the template cache."""
        self._cache.clear()
        self.logger.debug("Template cache cleared")
    
    def reload_template(self, template_name: str) -> str:
        """
        Reload a template from file, bypassing cache.
        
        Args:
            template_name: Name of the template to reload
            
        Returns:
            Reloaded template content
        """
        return self.load_template(template_name, use_cache=False)