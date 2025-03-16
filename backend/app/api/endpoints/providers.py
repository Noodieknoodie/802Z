# backend/app/api/endpoints/providers.py
"""
Provider API endpoints.

Provides routes for:
- Listing all providers
- Getting clients by provider
"""

def get_all_providers():
    """
    GET /api/providers
    
    Algorithm:
    1. Query database for all active providers (valid_to IS NULL)
    2. For each provider, aggregate:
       - Total client count
       - Total assets under management
       - Total participant count
    3. Format response according to frontend expectations
    
    Why aggregation matters:
    - Provider sidebar view shows summary metrics
    - Reduces need for multiple client-side calculations
    - Provides consistent provider data
    
    Returns: JSON response with array of provider objects including aggregated stats
    """
    pass

def get_provider_clients(provider_id):
    """
    GET /api/providers/{provider_id}/clients
    
    Algorithm:
    1. Validate provider_id parameter
    2. Query frontend_client_list view with providerId filter
    3. Sort clients by name for consistent display
    4. Format response to match frontend expectations
    
    This endpoint is called when:
    - User expands a provider in the sidebar
    - User clicks on a provider to see all its clients
    
    Returns: JSON response with array of client objects belonging to the provider
    """
    pass