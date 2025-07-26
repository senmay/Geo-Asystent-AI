"""
Validation utilities for GIS service operations.

This module provides centralized validation functions to separate input validation
from business logic in service methods.
"""

from typing import List
from exceptions import ValidationError


def validate_positive_integer(value: int, param_name: str) -> None:
    """
    Validate that a value is a positive integer.
    
    Args:
        value: Value to validate
        param_name: Name of the parameter for error messages
        
    Raises:
        ValidationError: If value is not positive
    """
    if value <= 0:
        raise ValidationError(param_name, value, "must be positive")


def validate_non_negative_number(value: float, param_name: str) -> None:
    """
    Validate that a value is non-negative.
    
    Args:
        value: Value to validate
        param_name: Name of the parameter for error messages
        
    Raises:
        ValidationError: If value is negative
    """
    if value < 0:
        raise ValidationError(param_name, value, "must be non-negative")


def validate_area_thresholds(thresholds: List[float]) -> None:
    """
    Validate area threshold list.
    
    Args:
        thresholds: List of area thresholds to validate
        
    Raises:
        ValidationError: If thresholds are invalid
    """
    if not thresholds:
        raise ValidationError("area_thresholds", thresholds, "cannot be empty")
    
    for i, threshold in enumerate(thresholds):
        if threshold <= 0:
            raise ValidationError(f"area_thresholds[{i}]", threshold, "must be positive")
    
    # Check if sorted
    if thresholds != sorted(thresholds):
        raise ValidationError("area_thresholds", thresholds, "should be in ascending order")