# Implementation Plan

- [x] 1. Fix logging issues - replace print() with logger





  - Replace all print() statements in backend/tools/gis_tools.py with logger.info()
  - Replace print() statements in backend/config/validation.py with logger calls
  - Add proper logging context (operation name, parameters) to existing log calls
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Eliminate code duplication in result processing





  - Move limit_results_for_display function from gis_service.py and gis_tools.py to utils/result_helpers.py
  - Update all imports to use the shared function
  - Remove duplicate message formatting code by creating simple helper functions
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 3. Simplify GISService methods - one method, one job




  - Break down complex methods like find_n_largest_parcels into smaller focused functions
  - Separate input validation from business logic in each GIS method
  - Move repeated GeoJSON conversion logic to simple helper function
  - _Requirements: 4.1, 4.2, 4.3, 5.1_

- [x] 4. Improve error handling - catch specific exceptions





  - Replace generic Exception catches with specific exception types in all services
  - Add ValidationError to exceptions module for input validation failures
  - Ensure all errors include proper context in log messages
  - _Requirements: 2.1, 2.2, 2.3, 2.6_

- [x] 5. Clean up LLMService - separate concerns





  - Split generate_chat_response method into validation, prompt prep, and execution
  - Move query validation to separate simple function
  - Improve error context in LLM timeout and API key error scenarios
  - _Requirements: 4.1, 4.2, 5.1, 5.2_

- [ ] 6. Test the refactored code
  - Update existing tests to work with refactored method signatures
  - Add basic tests for new helper functions
  - Test error scenarios with specific exception types
  - _Requirements: 7.1, 7.2, 7.3_