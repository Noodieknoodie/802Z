# backend/app/database/database.py
"""
Database connection and session management.

This module handles SQLite database connection, providing:
- Database initialization
- Connection management
- Session management
- Query execution utilities
"""
import aiosqlite
from contextlib import asynccontextmanager
from typing import Any, Optional
from app.core.config import PATHS

# Global connection variable (will be initialized on startup)
_db_connection = None

def dict_factory(cursor, row):
    """Convert row results to dictionary with column names as keys."""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

async def init_db_pool():
    """Initialize the database connection."""
    global _db_connection
    
    # Create a single connection instead of a pool
    # aiosqlite doesn't have a create_pool method
    _db_connection = await aiosqlite.connect(str(PATHS["DB_PATH"]))
    _db_connection.row_factory = dict_factory
    
    return _db_connection

async def close_db_pool():
    """Close the database connection."""
    global _db_connection
    if _db_connection:
        await _db_connection.close()
        _db_connection = None

@asynccontextmanager
async def get_db_connection():
    """Get a database connection from the pool."""
    if _db_connection is None:
        raise RuntimeError("Database connection not initialized")
    
    # Return the existing connection
    yield _db_connection

async def execute_query(
    query: str, 
    params: Optional[tuple] = None
) -> list[dict[str, Any]]:
    """
    Execute a query and return all results.
    
    Args:
        query: SQL query to execute
        params: Query parameters
        
    Returns: Query results as a list of dictionaries
    """
    async with get_db_connection() as conn:
        cursor = await conn.execute(query, params or ())
        
        # For SELECT queries, fetch results
        if query.strip().upper().startswith("SELECT"):
            rows = await cursor.fetchall()
            return rows
        # For other queries, commit and return empty list
        else:
            await conn.commit()
            return []

async def execute_transaction(queries: list[tuple[str, tuple]]) -> bool:
    """
    Execute multiple queries as a single transaction.
    
    Args:
        queries: List of (query, params) tuples
        
    Returns: Boolean indicating transaction success/failure
    """
    async with get_db_connection() as conn:
        async with conn.execute("BEGIN") as _:
            try:
                for query, params in queries:
                    await conn.execute(query, params or ())
                await conn.commit()
                return True
            except Exception as e:
                await conn.rollback()
                print(f"Transaction failed: {str(e)}")
                return False

async def execute_write_query(
    query: str, 
    params: Optional[tuple] = None
) -> int:
    """
    Execute a write query (INSERT, UPDATE, DELETE) and return affected rows.
    
    Args:
        query: SQL query to execute
        params: Query parameters
        
    Returns: Number of rows affected or last row ID for INSERT
    """
    async with get_db_connection() as conn:
        cursor = await conn.execute(query, params or ())
        await conn.commit()
        
        # For INSERT, return last row id
        if query.strip().upper().startswith("INSERT"):
            return cursor.lastrowid
        # For others, return rows affected
        else:
            return cursor.rowcount