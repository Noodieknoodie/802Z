# backend/app/database/database.py
"""
Database connection and session management.

This module handles SQLite database connection, providing:
- Database initialization
- Connection pooling
- Session management
- Query execution utilities
"""
import aiosqlite
from contextlib import asynccontextmanager
from typing import Any, Optional
from app.core.config import PATHS

# Connection pool (will be initialized on startup)
_connection_pool = None

def dict_factory(cursor, row):
    """Convert row results to dictionary with column names as keys."""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

async def init_db_pool():
    """Initialize the database connection pool."""
    global _connection_pool
    _connection_pool = await aiosqlite.create_pool(
        str(PATHS["DB_PATH"]), 
        minsize=1, 
        maxsize=10,
        timeout=30.0
    )
    return _connection_pool

async def close_db_pool():
    """Close the database connection pool."""
    global _connection_pool
    if _connection_pool:
        _connection_pool.close()
        await _connection_pool.wait_closed()
        _connection_pool = None

@asynccontextmanager
async def db_connection():
    """Async context manager for database connections."""
    global _connection_pool
    
    if _connection_pool is None:
        await init_db_pool()
    
    # Get connection from pool
    async with _connection_pool.acquire() as conn:
        # Setup connection
        conn.row_factory = dict_factory
        await conn.execute("PRAGMA foreign_keys = ON")
        await conn.execute("PRAGMA journal_mode = WAL")
        yield conn

async def execute_query(
    query: str, 
    params: Optional[tuple] = None, 
    fetch_all: bool = True
) -> list[dict[str, Any]]:
    """
    Execute a query with optional parameters.
    
    Args:
        query: SQL query string with parameter placeholders
        params: Tuple of parameters to substitute
        fetch_all: Whether to fetch all results or just one row
    
    Returns: Query results as a list of dictionaries
    """
    async with db_connection() as conn:
        cursor = await conn.execute(query, params or ())
        
        if fetch_all:
            results = await cursor.fetchall()
        else:
            result = await cursor.fetchone()
            results = [result] if result else []
            
        await cursor.close()
        return results

async def execute_transaction(queries: list[dict[str, Any]]) -> bool:
    """
    Execute multiple queries in a transaction.
    
    Args:
        queries: List of dicts, each with 'query' and optional 'params' keys
    
    Returns: Boolean indicating transaction success/failure
    """
    async with db_connection() as conn:
        async with conn.execute("BEGIN") as _:
            try:
                for item in queries:
                    query = item['query']
                    params = item.get('params', ())
                    await conn.execute(query, params)
                
                await conn.commit()
                return True
            except Exception as e:
                await conn.rollback()
                print(f"Transaction error: {str(e)}")
                return False

async def execute_write_query(
    query: str,
    params: Optional[tuple] = None
) -> int:
    """
    Execute a write query (INSERT, UPDATE, DELETE) and return affected rows.
    
    Args:
        query: SQL query string with parameter placeholders
        params: Tuple of parameters to substitute
    
    Returns: Number of rows affected or last row ID for INSERT
    """
    async with db_connection() as conn:
        cursor = await conn.execute(query, params or ())
        await conn.commit()
        
        # For INSERT statements, return last row ID
        if query.strip().upper().startswith("INSERT"):
            return cursor.lastrowid
        # For UPDATE/DELETE, return modified rows
        else:
            return cursor.rowcount