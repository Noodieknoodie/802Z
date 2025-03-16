# Component Roles and Responsibilities
## Frontend Roles

DO:

Handle UI rendering and user interactions
Perform client-side validation before submission
Manage client-side state with React Context
Format data for display (dates, currency, percentages)
Provide immediate feedback on user actions
Handle document previewing


DON'T:

Calculate values that should be provided by the backend (variance, expected fees)
Store business logic that belongs in the backend
Make direct database queries
Cache large datasets client-side



## SQLite Database Roles

DO:

Store all data with proper relationships and constraints
Maintain data integrity through foreign keys and triggers
Use views for complex queries that combine multiple tables
Calculate derived values through triggers and views
Track historical data with valid_from/valid_to fields
Optimize query performance with indexes


DON'T:

Implement complex business logic that belongs in the backend
Store frontend-specific formatting preferences
Duplicate data unnecessarily
Perform operations that could impact performance



## Backend Python Roles

DO:

Provide RESTful API endpoints for frontend consumption
Transform database data into frontend-expected JSON structure
Handle authentication and authorization
Implement business logic and validation rules
Manage file uploads and document storage
Log operations and errors
Calculate dynamic values not suited for database triggers


DON'T:

Duplicate calculations already handled by database views
Re-implement validation logic that exists in the frontend
Store session state that should be in the database
Process large datasets inefficiently