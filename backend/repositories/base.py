"""Base repository class with common database operations."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from sqlalchemy.engine import Engine
import logging

from exceptions import DatabaseConnectionError
from backend.utils.db_logger import log_database_operation

logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    """Base repository class providing common database operations."""
    
    def __init__(self, db_engine: Engine):
        """
        Initialize repository with database engine.
        
        Args:
            db_engine: SQLAlchemy database engine
        """
        self.db_engine = db_engine
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def execute_query(self, sql: str, operation_name: str, **context) -> Any:
        """
        Execute a SQL query with proper logging and error handling.
        
        Args:
            sql: SQL query to execute
            operation_name: Name of the operation for logging
            **context: Additional context for logging
            
        Returns:
            Query result
            
        Raises:
            DatabaseConnectionError: If query execution fails
        """
        try:
            with log_database_operation(operation_name, **context):
                with self.db_engine.connect() as connection:
                    result = connection.execute(sql)
                    return result
        except Exception as e:
            self.logger.error(f"Query execution failed: {operation_name}")
            raise DatabaseConnectionError(
                operation=operation_name,
                original_error=e
            )
    
    def check_table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            True if table exists, False otherwise
        """
        try:
            sql = f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = '{table_name}'
                );
            """
            
            with self.db_engine.connect() as connection:
                result = connection.execute(sql)
                return result.scalar()
                
        except Exception as e:
            self.logger.warning(f"Failed to check table existence: {table_name} - {e}")
            return False
    
    def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a table structure.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with table information or None if table doesn't exist
        """
        try:
            sql = f"""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position;
            """
            
            with self.db_engine.connect() as connection:
                result = connection.execute(sql)
                columns = [
                    {
                        "name": row[0],
                        "type": row[1],
                        "nullable": row[2] == "YES",
                        "default": row[3]
                    }
                    for row in result
                ]
                
                if not columns:
                    return None
                
                return {
                    "table_name": table_name,
                    "columns": columns,
                    "column_count": len(columns)
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get table info: {table_name} - {e}")
            return None
    
    @abstractmethod
    def get_available_tables(self) -> List[str]:
        """
        Get list of available tables for this repository.
        
        Returns:
            List of table names
        """
        pass