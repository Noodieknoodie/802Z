# 401k Payment Management System Database Documentation

This document provides a comprehensive guide to the SQLite database schema for the 401k Payment Management System. It details how the database is structured to support both backend and frontend needs.

## Table of Contents
1. [Core Tables](#core-tables)
2. [Junction Tables](#junction-tables)
3. [Summary Tables](#summary-tables)
4. [Frontend Views](#frontend-views)
5. [System Views](#system-views)
6. [Triggers](#triggers)
7. [Indexes](#indexes)
8. [Data Flow Patterns](#data-flow-patterns)
9. [Common Query Patterns](#common-query-patterns)

## Core Tables

### clients
Stores the central client information.

| Column | Type | Description |
|--------|------|-------------|
| client_id | INTEGER | Primary key, auto-increment |
| display_name | TEXT | Name shown in the UI |
| full_name | TEXT | Complete legal name |
| ima_signed_date | TEXT | Date when the IMA was signed (YYYY-MM-DD) |
| onedrive_folder_path | TEXT | Path to client documents in OneDrive |
| valid_from | DATETIME | Record start validity timestamp |
| valid_to | DATETIME | Record end validity timestamp (NULL for active) |

**Notes:**
- Active clients have `valid_to = NULL`
- `ima_signed_date` is used for calculating the "Since" date shown in client details

### contracts
Defines the fee structure and payment schedule for each client.

| Column | Type | Description |
|--------|------|-------------|
| contract_id | INTEGER | Primary key, auto-increment |
| client_id | INTEGER | Foreign key to clients |
| contract_number | TEXT | Provider's contract identifier |
| provider_id | INTEGER | Foreign key to providers |
| provider_name | TEXT | Name of the provider (maintained for backward compatibility) |
| contract_start_date | TEXT | When the contract began (YYYY-MM-DD) |
| fee_type | TEXT | Either 'percentage' or 'flat' |
| percent_rate | REAL | Rate for percentage-based fees (stored as decimal, not percentage) |
| flat_rate | REAL | Amount for flat fee |
| payment_schedule | TEXT | Either 'monthly' or 'quarterly' |
| num_people | INTEGER | Number of participants |
| notes | TEXT | Additional contract information |
| valid_from | DATETIME | Record start validity timestamp |
| valid_to | DATETIME | Record end validity timestamp (NULL for active) |

**Notes:**
- Each client should have one active contract (`valid_to = NULL`)
- For percentage fees, `percent_rate` is stored as a decimal (e.g., 0.0075 for 0.75%)
- `payment_schedule` determines how periods are tracked throughout the system

### providers
Stores information about service providers.

| Column | Type | Description |
|--------|------|-------------|
| provider_id | INTEGER | Primary key, auto-increment |
| name | TEXT | Provider name (unique) |
| valid_from | DATETIME | Record start validity timestamp |
| valid_to | DATETIME | Record end validity timestamp (NULL for active) |

**Notes:**
- Used for grouping clients in the provider view
- Associated with contracts via the `provider_id` foreign key

### payments
Records individual fee payments from clients.

| Column | Type | Description |
|--------|------|-------------|
| payment_id | INTEGER | Primary key, auto-increment |
| contract_id | INTEGER | Foreign key to contracts |
| client_id | INTEGER | Foreign key to clients |
| received_date | TEXT | When payment was received (YYYY-MM-DD) |
| total_assets | INTEGER | Assets under management at time of payment |
| expected_fee | REAL | Calculated expected fee amount |
| actual_fee | REAL | Actual fee amount received |
| variance | REAL | Difference between expected and actual fees (calculated by trigger) |
| variance_percent | REAL | Percentage variance (calculated by trigger) |
| method | TEXT | Payment method: 'Auto - ACH', 'Check', 'Wire', 'Invoice' |
| notes | TEXT | Additional payment information |
| valid_from | DATETIME | Record start validity timestamp |
| valid_to | DATETIME | Record end validity timestamp (NULL for active) |
| applied_start_month | INTEGER | Starting month (1-12) for monthly payments |
| applied_start_month_year | INTEGER | Year for monthly payments |
| applied_end_month | INTEGER | Ending month for multi-month payments |
| applied_end_month_year | INTEGER | Year for ending month |
| applied_start_quarter | INTEGER | Starting quarter (1-4) for quarterly payments |
| applied_start_quarter_year | INTEGER | Year for quarterly payments |
| applied_end_quarter | INTEGER | Ending quarter for multi-quarter payments |
| applied_end_quarter_year | INTEGER | Year for ending quarter |

**Notes:**
- Either the monthly or quarterly fields are used, depending on the client's payment schedule
- For single-period payments, start and end values will be the same
- Multi-period payments span a range (start to end)
- `variance` and `variance_percent` are automatically calculated by triggers

### client_metrics
Stores aggregate metrics and calculated values for each client.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key, auto-increment |
| client_id | INTEGER | Foreign key to clients (unique) |
| last_payment_date | TEXT | Date of most recent payment (YYYY-MM-DD) |
| last_payment_amount | REAL | Amount of most recent payment |
| last_payment_month | INTEGER | Month (1-12) of most recent payment (for monthly clients) |
| last_payment_quarter | INTEGER | Quarter (1-4) of most recent payment (for quarterly clients) |
| last_payment_year | INTEGER | Year of most recent payment |
| total_ytd_payments | REAL | Sum of payments for current year |
| avg_quarterly_payment | REAL | Average payment amount per quarter |
| last_recorded_assets | REAL | Most recent AUM value |
| last_updated | TEXT | When this record was last updated |
| next_payment_due | TEXT | Expected date of next payment |

**Notes:**
- One record per client (enforced by UNIQUE constraint)
- Used for client status calculations and summaries
- Updated by triggers when payments are recorded

### contacts
Stores contact information for each client.

| Column | Type | Description |
|--------|------|-------------|
| contact_id | INTEGER | Primary key, auto-increment |
| client_id | INTEGER | Foreign key to clients |
| contact_type | TEXT | 'Primary', 'Authorized', 'Provider', etc. |
| contact_name | TEXT | Contact's name |
| phone | TEXT | Contact's phone number |
| email | TEXT | Contact's email address |
| fax | TEXT | Contact's fax number |
| physical_address | TEXT | Physical address |
| mailing_address | TEXT | Mailing address (if different) |
| valid_from | DATETIME | Record start validity timestamp |
| valid_to | DATETIME | Record end validity timestamp (NULL for active) |

**Notes:**
- A client can have multiple contacts of different types
- 'Primary' contacts are shown in client summaries

### client_files
Stores metadata about client documents.

| Column | Type | Description |
|--------|------|-------------|
| file_id | INTEGER | Primary key, auto-increment |
| client_id | INTEGER | Foreign key to clients |
| file_name | TEXT | Original file name |
| onedrive_path | TEXT | Path to file in OneDrive |
| uploaded_at | DATETIME | When the file was uploaded |

**Notes:**
- Contains all client documents, not just payment-related ones
- Referenced by payment_files for payment-specific documents

## Junction Tables

### payment_files
Links payments to their associated documents.

| Column | Type | Description |
|--------|------|-------------|
| payment_id | INTEGER | Foreign key to payments |
| file_id | INTEGER | Foreign key to client_files |
| linked_at | DATETIME | When the link was created |

**Notes:**
- Composite primary key (payment_id, file_id)
- One payment can have multiple documents
- One document can be linked to multiple payments

## Summary Tables

### quarterly_summaries
Aggregates payment data by quarter for each client.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key, auto-increment |
| client_id | INTEGER | Foreign key to clients |
| year | INTEGER | Year of the quarter |
| quarter | INTEGER | Quarter number (1-4) |
| total_payments | REAL | Sum of payments for the quarter |
| total_assets | REAL | Average AUM for the quarter |
| payment_count | INTEGER | Number of payments in the quarter |
| avg_payment | REAL | Average payment amount |
| expected_total | REAL | Expected fee total |
| last_updated | TEXT | When this record was last updated |

**Notes:**
- Unique constraint on (client_id, year, quarter)
- Updated automatically by triggers when payments change
- Used for reporting and analytics

### yearly_summaries
Aggregates payment data by year for each client.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key, auto-increment |
| client_id | INTEGER | Foreign key to clients |
| year | INTEGER | Year |
| total_payments | REAL | Sum of payments for the year |
| total_assets | REAL | Average AUM for the year |
| payment_count | INTEGER | Number of payments in the year |
| avg_payment | REAL | Average payment amount |
| yoy_growth | REAL | Year-over-year growth percentage |
| last_updated | TEXT | When this record was last updated |

**Notes:**
- Unique constraint on (client_id, year)
- Updated automatically by triggers when quarterly summaries change
- Used for reporting and analytics

## Frontend Views

These views transform database data into the format expected by the frontend.

### frontend_client_list
Provides client summary data for the sidebar client list.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Client ID |
| name | TEXT | Display name |
| providerId | INTEGER | Provider ID |
| providerName | TEXT | Provider name |
| contact | TEXT | Primary contact name |
| participants | INTEGER | Number of participants |
| clientSince | TEXT | IMA signed date |
| status | TEXT | Payment status ('Paid' or 'Due') |

**Usage:**
- Used by the frontend to populate the client sidebar
- Filtered by `c.valid_to IS NULL` to show only active clients

### frontend_client_details
Provides detailed client information for the client details panel.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Client ID |
| name | TEXT | Display name |
| providerId | INTEGER | Provider ID |
| providerName | TEXT | Provider name |
| participants | INTEGER | Number of participants |
| clientSince | TEXT | IMA signed date |
| feeType | TEXT | 'percentage' or 'flat' |
| rate | REAL | Fee rate (percent or flat amount) |
| paymentSchedule | TEXT | 'monthly' or 'quarterly' |
| percentRateBreakdown | JSON | Monthly/quarterly/annual percentage rates |
| flatRateBreakdown | JSON | Monthly/quarterly/annual flat fees |
| lastPaymentDate | TEXT | Date of last payment |
| lastPaymentAmount | REAL | Amount of last payment |
| lastPaymentPeriod | TEXT | Period of last payment (e.g., "Jan 2024" or "Q1 2024") |
| lastPaymentExpected | REAL | Expected fee for last payment |
| lastPaymentActual | REAL | Actual fee for last payment |
| lastPaymentVariance | REAL | Variance for last payment |
| lastRecordedAUM | REAL | Most recent AUM |
| currentPeriod | TEXT | Current period (e.g., "Feb 2025" or "Q4 2024") |
| currentStatus | TEXT | Current payment status |

**Usage:**
- Used by the frontend to populate the client details panel
- Contains nested JSON objects for rate breakdowns
- Formats periods as user-friendly strings (e.g., "Jan 2024", "Q1 2024")

### frontend_payment_history
Provides payment history data formatted for the frontend.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Payment ID |
| clientId | INTEGER | Client ID |
| receivedDate | TEXT | Payment received date |
| appliedPeriod | TEXT | Applied period (e.g., "Jan 2024" or "Q1 2024") |
| aum | INTEGER | Assets under management |
| expectedFee | REAL | Expected fee amount |
| actualFee | REAL | Actual fee amount |
| variance | REAL | Variance amount |
| variancePercent | REAL | Variance percentage |
| paymentType | TEXT | Payment method |
| notes | TEXT | Payment notes |
| hasAttachment | INTEGER | Whether documents are attached (0/1) |
| attachmentId | INTEGER | File ID of attachment |

**Usage:**
- Used by the frontend to populate the payment history table
- Formats periods as user-friendly strings
- Calculates variance percentage
- Ordered by received date (descending)

## System Views

These views support internal system operations and calculations.

### client_payment_basic
Provides basic data for client payment status calculations.

| Column | Type | Description |
|--------|------|-------------|
| client_id | INTEGER | Client ID |
| display_name | TEXT | Client display name |
| payment_schedule | TEXT | 'monthly' or 'quarterly' |
| fee_type | TEXT | 'percentage' or 'flat' |
| percent_rate | REAL | Percentage rate as decimal |
| flat_rate | REAL | Flat fee amount |
| last_recorded_assets | REAL | Most recent AUM |
| last_payment_date | TEXT | Date of most recent payment |
| last_payment_amount | REAL | Amount of most recent payment |
| applied_end_month | INTEGER | Last payment end month |
| applied_end_month_year | INTEGER | Last payment end month year |
| applied_end_quarter | INTEGER | Last payment end quarter |
| applied_end_quarter_year | INTEGER | Last payment end quarter year |

**Usage:**
- Provides raw data for the backend to calculate payment status
- Used for expected fee calculations
- Backend implements the business logic for status determination



### contract_rate_display
Calculates rate variations based on payment schedule.

| Column | Type | Description |
|--------|------|-------------|
| contract_id | INTEGER | Contract ID |
| client_id | INTEGER | Client ID |
| provider_name | TEXT | Provider name |
| fee_type | TEXT | 'percentage' or 'flat' |
| payment_schedule | TEXT | 'monthly' or 'quarterly' |
| percent_rate | REAL | Base percentage rate |
| flat_rate | REAL | Base flat fee |
| ... | ... | Various derived rate fields |
| monthly_percent_rate | REAL | Monthly equivalent percent rate |
| quarterly_percent_rate | REAL | Quarterly equivalent percent rate |
| annual_percent_rate | REAL | Annual equivalent percent rate |
| monthly_flat_rate | REAL | Monthly equivalent flat fee |
| quarterly_flat_rate | REAL | Quarterly equivalent flat fee |
| annual_flat_rate | REAL | Annual equivalent flat fee |

**Usage:**
- Calculates equivalent rates for different payment frequencies
- Used by frontend_client_details to create rate breakdowns
- Supports fee calculations for different period lengths

### payment_file_view
Simplifies access to payment document information.

| Column | Type | Description |
|--------|------|-------------|
| payment_id | INTEGER | Payment ID |
| client_id | INTEGER | Client ID |
| contract_id | INTEGER | Contract ID |
| received_date | TEXT | Payment received date |
| actual_fee | REAL | Actual fee amount |
| has_file | INTEGER | Whether documents are attached (0/1) |
| file_id | INTEGER | File ID |
| file_name | TEXT | File name |
| onedrive_path | TEXT | Path to file in OneDrive |

**Usage:**
- Simplifies checking for attached documents
- Used by frontend_payment_history view

### payment_with_aum_fallback
Provides AUM values even when not recorded with payment.

| Column | Type | Description |
|--------|------|-------------|
| ... | ... | All columns from payments table |
| final_assets | INTEGER | AUM with fallback to previous payment |

**Usage:**
- If a payment doesn't have an AUM value, uses the most recent previous value
- Ensures fee calculations have AUM data when possible

## Triggers

### payments_update_variance_insert
Calculates variance when a payment is inserted.

**Behavior:**
- Runs AFTER INSERT on payments
- Calculates variance = actual_fee - expected_fee
- Calculates variance_percent = (variance / expected_fee) * 100
- Updates the just-inserted payment record

### payments_update_variance_update
Recalculates variance when a payment is updated.

**Behavior:**
- Runs AFTER UPDATE on payments
- Recalculates variance and variance_percent
- Updates the payment record

### update_quarterly_after_payment
Updates quarterly summary when a payment is added.

**Behavior:**
- Runs AFTER INSERT on payments
- Aggregates data for the payment's quarter
- Inserts or replaces the quarterly summary record

### update_yearly_after_quarterly
Updates yearly summary when a quarterly summary is added.

**Behavior:**
- Runs AFTER INSERT on quarterly_summaries
- Aggregates data for the year
- Inserts or replaces the yearly summary record

## Indexes

The database includes several indexes to optimize query performance:

| Index Name | Table | Columns | Purpose |
|------------|-------|---------|---------|
| idx_client_metrics_lookup | client_metrics | client_id | Speed up client metric lookups |
| idx_contacts_client_id | contacts | client_id | Speed up contact filtering by client |
| idx_contacts_type | contacts | client_id, contact_type | Speed up filtering by contact type |
| idx_contracts_client_id | contracts | client_id | Speed up contract lookups by client |
| idx_contracts_provider | contracts | provider_name | Speed up filtering by provider |
| idx_payments_applied_months | payments | client_id, applied_start_month_year, applied_start_month, applied_end_month_year, applied_end_month | Speed up period-based payment lookups |
| idx_payments_client_id | payments | client_id | Speed up payment filtering by client |
| idx_payments_contract_id | payments | contract_id | Speed up payment filtering by contract |
| idx_payments_date | payments | client_id, received_date DESC | Speed up sorting payments by date |
| idx_quarterly_lookup | quarterly_summaries | client_id, year, quarter | Speed up quarterly summary lookups |
| idx_yearly_lookup | yearly_summaries | client_id, year | Speed up yearly summary lookups |

## Data Flow Patterns

### Handling Payment Periods

The system handles both monthly and quarterly payment schedules:

1. **Monthly Payments:**
   - Stored using `applied_start_month` (1-12) and `applied_start_month_year`
   - May span multiple months using end_ fields
   - Displayed in frontend as "Jan 2024", "Feb 2024", etc.

2. **Quarterly Payments:**
   - Stored using `applied_start_quarter` (1-4) and `applied_start_quarter_year`
   - May span multiple quarters using end_ fields
   - Displayed in frontend as "Q1 2024", "Q2 2024", etc.

3. **Period Transformation:**
   - Database → Frontend: Views convert numeric fields to formatted strings
   - Frontend → Database: Backend parses strings back to numeric values



### Client Status Calculation (MIGRATED OUT OF DB, NOW HANDLED IN PYTHON)

The client payment status is determined as follows:

1. Calculate the current period based on today's date minus one period
2. Compare with the client's last recorded payment period
3. If the last payment period is before the current period, status is "Due"
4. Otherwise, status is "Paid"

This logic is implemented in the Python backend using `client_service.py` functions:
- `determine_payment_status()`: Calculates "Due" or "Paid" status
- `calculate_missing_payments()`: Determines which specific periods are missing

The frontend views still reference a placeholder `client_payment_status` view, but the actual status data is injected by the Python backend before sending to the frontend.

### Fee Calculation

Fees are calculated differently based on fee type:

1. **Percentage Fee:**
   - `expected_fee = total_assets * (percent_rate / 100.0)`
   - Rate is stored as decimal (e.g., 0.0075 for 0.75%)

2. **Flat Fee:**
   - `expected_fee = flat_rate`
   - Rate doesn't depend on assets

The `contract_rate_display` view provides equivalent rates for different periods to support multi-period calculations.

## Common Query Patterns

### Getting Client List for Sidebar

```sql
SELECT * FROM frontend_client_list ORDER BY name;
```

### Getting Client Details

```sql
SELECT * FROM frontend_client_details WHERE id = ?;
```

### Getting Payment History for a Client

```sql
SELECT * FROM frontend_payment_history WHERE clientId = ? ORDER BY receivedDate DESC;
```

### Getting Providers with Client Counts

```sql
SELECT 
    p.provider_id as id,
    p.name,
    COUNT(DISTINCT c.client_id) as clientCount,
    SUM(cm.last_recorded_assets) as totalAssets
FROM 
    providers p
LEFT JOIN 
    contracts ct ON p.provider_id = ct.provider_id AND ct.valid_to IS NULL
LEFT JOIN 
    clients c ON ct.client_id = c.client_id AND c.valid_to IS NULL
LEFT JOIN 
    client_metrics cm ON c.client_id = cm.client_id
WHERE 
    p.valid_to IS NULL
GROUP BY 
    p.provider_id, p.name
ORDER BY 
    p.name;
```

### Creating a New Payment

```sql
INSERT INTO payments (
    contract_id, client_id, received_date, total_assets, 
    expected_fee, actual_fee, method, notes,
    applied_start_month, applied_start_month_year, 
    applied_end_month, applied_end_month_year
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
```

The triggers will automatically:
1. Calculate variance and variance_percent
2. Update quarterly_summaries
3. Update yearly_summaries

### Soft Deleting a Record

For most tables, use this pattern to maintain history:

```sql
UPDATE payments SET valid_to = CURRENT_TIMESTAMP WHERE payment_id = ?;
```