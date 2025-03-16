# 401k Payment Management System - Backend Documentation

This documentation serves as a comprehensive guide for implementing the Python backend of the 401k Payment Management System. It outlines how the backend interacts with the SQLite database and provides data to the frontend.

## Table of Contents
1. [System Overview](#system-overview)
2. [Project Structure](#project-structure)
3. [Database Integration](#database-integration)
4. [API Endpoints](#api-endpoints)
5. [Data Transformation Patterns](#data-transformation-patterns)
6. [Implementation Guidelines](#implementation-guidelines)

## System Overview

The 401k Payment Management System backend serves as the bridge between the SQLite database and the Next.js frontend. Its primary responsibilities are:

1. **Data Access**: Query the SQLite database through the recently created frontend views
2. **Data Transformation**: Format data according to frontend requirements
3. **Business Logic**: Handle payment creation, updates, and calculations
4. **File Management**: Store and retrieve payment-related documents

This is a local-only deployment with no internet access, so security features are minimized. The system operates in a trusted environment with a small team.

## Project Structure

The backend follows a modular structure:

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # Application entry point and FastAPI setup
│   ├── database/
│   │   ├── __init__.py
│   │   ├── database.py          # Database connection handling
│   │   └── models.py            # Database interaction functions
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints/
│   │   │   ├── __init__.py
│   │   │   ├── clients.py       # Client-related endpoints
│   │   │   ├── payments.py      # Payment-related endpoints
│   │   │   ├── providers.py     # Provider-related endpoints
│   │   │   └── documents.py     # Document-related endpoints
│   │   └── dependencies.py      # API dependencies (DB connection, pagination)
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py            # Application configuration
│   ├── services/
│   │   ├── __init__.py
│   │   ├── client_service.py    # Client-related business logic
│   │   ├── payment_service.py   # Payment-related business logic
│   │   └── document_service.py  # Document-related business logic
│   └── utils/
│       ├── __init__.py
│       └── format.py            # Formatting utilities
└── requirements.txt             # Python dependencies
```

## Database Integration

### Connection Handling

The backend connects to the SQLite database using the `aiosqlite` library for async operations. The connection pattern is:

```python
async def get_db_connection():
    """Get database connection from the connection pool."""
    conn = await aiosqlite.connect("./data/401k_payments.db")
    conn.row_factory = lambda cursor, row: {
        column[0]: row[idx] for idx, column in enumerate(cursor.description)
    }
    return conn
```

### Key Database Views

The backend primarily interacts with these frontend-specific views:

1. `frontend_client_list`: For sidebar client listing
2. `frontend_client_details`: For client detail panel
3. `frontend_payment_history`: For payment history table

These views already handle most of the complex transformations, so the backend can focus on passing the data through with minimal processing.

### Query Patterns

The backend should use these query patterns:

1. **Read operations**: Use the frontend views directly
   ```python
   async def get_clients():
       conn = await get_db_connection()
       try:
           result = await conn.execute("SELECT * FROM frontend_client_list ORDER BY name")
           clients = await result.fetchall()
           return clients
       finally:
           await conn.close()
   ```

2. **Write operations**: Insert/update core tables directly
   ```python
   async def create_payment(payment_data):
       conn = await get_db_connection()
       try:
           await conn.execute(
               """
               INSERT INTO payments (
                   contract_id, client_id, received_date, total_assets, 
                   expected_fee, actual_fee, method, notes,
                   applied_start_month, applied_start_month_year, 
                   applied_end_month, applied_end_month_year
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               """,
               (
                   payment_data["contract_id"],
                   payment_data["client_id"],
                   # ... other fields
               )
           )
           await conn.commit()
       finally:
           await conn.close()
   ```

## API Endpoints

The backend exposes these RESTful API endpoints:

### Client Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/clients` | GET | Get all clients (for sidebar) |
| `/api/clients/{client_id}` | GET | Get detailed client information |
| `/api/clients/{client_id}/payments` | GET | Get payment history for a client |

### Provider Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/providers` | GET | Get all providers (for sidebar provider view) |
| `/api/providers/{provider_id}/clients` | GET | Get clients for a specific provider |

### Payment Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/clients/{client_id}/payments` | POST | Create a new payment |
| `/api/payments/{payment_id}` | PUT | Update an existing payment |
| `/api/payments/{payment_id}` | DELETE | Delete a payment |

### Document Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/payments/{payment_id}/documents` | POST | Upload a document for a payment |
| `/api/documents/{document_id}` | GET | Get a document |
| `/api/documents/{document_id}` | DELETE | Delete a document |

## Data Transformation Patterns

### Period Handling

The frontend expects periods in formats like "Jan 2024" or "Q1 2024", while the database stores them as numeric fields. When receiving data from the frontend:

```python
def parse_period(period_str, payment_schedule):
    """Parse frontend period format into database fields."""
    if payment_schedule == "monthly":
        # Parse monthly period like "Jan 2024"
        month_map = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
        month_str, year_str = period_str.split()
        return {
            "applied_start_month": month_map[month_str],
            "applied_start_month_year": int(year_str),
            "applied_end_month": month_map[month_str],
            "applied_end_month_year": int(year_str)
        }
    elif payment_schedule == "quarterly":
        # Parse quarterly period like "Q1 2024"
        quarter_str, year_str = period_str.split()
        quarter = int(quarter_str[1])  # Extract the number after 'Q'
        return {
            "applied_start_quarter": quarter,
            "applied_start_quarter_year": int(year_str),
            "applied_end_quarter": quarter,
            "applied_end_quarter_year": int(year_str)
        }
```

### Frontend Data Structure

The frontend expects JSON data in this structure:

```json
{
  "clients": [
    {"id": 1, "name": "AirSea America", "providerId": 1, "providerName": "John Hancock", ...}
  ],
  "providers": [
    {"id": 1, "name": "John Hancock", "clientCount": 5, "totalAssets": 78543250, ...}
  ],
  "clientDetails": {
    "1": {
      "id": 1,
      "name": "AirSea America",
      "feeType": "percentage",
      "rate": 0.0007,
      "rateBreakdown": {"monthly": 0.0007, "quarterly": 0.0021, "annual": 0.0084},
      ...
    }
  },
  "paymentHistory": {
    "1": [
      {"id": 1, "receivedDate": "05/03/2019", "appliedPeriod": "Apr 2019", "aum": 824305, ...}
    ]
  }
}
```

The backend should construct this structure from individual queries:

```python
async def get_frontend_data():
    """Build the complete frontend data structure."""
    clients = await get_all_clients()
    providers = await get_all_providers()
    
    client_details = {}
    payment_history = {}
    
    for client in clients:
        client_id = client["id"]
        client_details[str(client_id)] = await get_client_details(client_id)
        payment_history[str(client_id)] = await get_client_payment_history(client_id)
    
    return {
        "clients": clients,
        "providers": providers,
        "clientDetails": client_details,
        "paymentHistory": payment_history
    }
```

## Implementation Guidelines

### Best Practices

1. **Use the Frontend Views**: The database has views specifically designed for frontend data needs - use them directly when possible.

2. **Leverage Database Calculations**: The database already calculates variance, variance percentages, and status - don't recalculate these in the backend.

3. **Transaction Safety**: Use transactions for operations that modify multiple tables.

4. **Error Handling**: Provide clear error messages that can help diagnose issues.

5. **Connection Management**: Always close database connections in finally blocks.

### Performance Considerations

1. **Connection Pooling**: Use a connection pool to avoid the overhead of creating new connections.

2. **Targeted Queries**: Query only what's needed rather than fetching everything.

3. **Pagination**: Implement pagination for payment history to handle clients with many payments.

4. **Caching**: For low-update-frequency data like providers list, consider basic caching.

### Local File Storage

For document storage:

1. **File Organization**: Store files in a consistent directory structure:
   ```
   /documents/{client_id}/{payment_id}_{filename}
   ```

2. **Metadata in Database**: Keep file metadata in the database, with physical path in `onedrive_path`.

3. **File Reading**: When retrieving documents, read directly from the file system using the path stored in the database.