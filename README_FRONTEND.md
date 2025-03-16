# FRONT END SHIT 

# Add Payment / Edit Payment Section/Form 
Received Date *
-- mm/dd/yyyy
Applied Period *
> Multi-period (untoggled)
>> Select period
-- Dropdown options, in period format. from client's inception period to one prior to today's (areers!), sorted recent first. (ie. Q1 2025, Q4 2024... or Dec 2024 Nov 2024...) 
> Multi-period (toggled)
>> Select periods
-- Two Dropdown options "Start" and "End" in period format. from client's inception period to one prior to today's (areers!), sorted recent first. (ie. Q1 2025, Q4 2024... or Dec 2024 Nov 2024...) End period cant come before first. 
Payment Amount *
-- ($)
Assets Under Management: 
-- ($)
Payment Type:
-- Dropdown: Auto-ACH, Check, Wire, Invoice
Check Number: 
-- number/text
Expected Fee (calculated)
-- ($) (FOR PERCENT FEE TYPES: live calculation as Assets Under Management is entered on this form. AUM x Rate. FOR FIXED FEE TYPES: Always the fixed rate)
Attacchment:
-- Upload Action
Notes:
-- (text field)
** Add Payment-- Button
// TODO: create "clear"  button / action 
// TODO: create "cancle edit" button / action 
# Client Details Section:
-- (Full Name) 
-- xxx participants 
-- Since (month day, year)
## Fee Structure
-- Fee Type (% Percentage or $ Flat)
-- Annual Rate / Fee (%) or ($) *
-- Schedule (monthly / quarterly)
-- (Schedule) (% rate or $ fee) (ie. Monthly 0.5645%)
## Last Payment
-- (Period) 
-- Received (mm/dd/yyyy)
-- Expected ($)
-- Actual ($)
-- Variance (%) and (%)*
## Last AUM 
-- ($) 
-- as of (mm/dd/yyyy)
## Current Period
-- (MON YEAR or QX YEAR)
-- (Paid/Pending)
# Payment History Section:
Received Date
-- mm/dd/yyyy
Period
-- Period format (Month YYYY or QX YYYY)
AUM
-- ($)
Expected Fee
-- ($)
Actual Fee
-- ($)
Variance
-- ($) and (%)
Actions
-- Edit (icon)
-- Delete (icon)
-- View Document (icon, enabled only when document exists)
Pagination
-- "Showing X to Y of Z payments" text
-- Previous button
-- Next button
Empty State
-- "No payment history available" message
# Client Sidebar Section:
View Mode Toggle
-- Clients/Providers switch
Search Field
-- Search clients/providers text input
## Clients View (when toggle is set to "Clients"):
Client List Items (for each client):
-- Client Name
-- Provider Name
-- Participants count
## Providers View (when toggle is set to "Providers"):
Provider List Items (for each provider):
-- Provider Name
-- Client count
-- Total AUM
Provider Expansion (when provider is clicked):
-- Client List under Provider
-- Client Name
-- Participants count
Empty States:
-- "No clients found" (when search returns no clients)
-- "No providers found" (when search returns no providers)
# Top Nav bar 
-- Payments (current)
-- Summary, Manage Clients, Export (all under construction)


////// FRONTEND BUILD REFERENCE ///////
Thought for 2 seconds### 401k Payment Management Dashboard - Build Reference
## Core Data Structures
### Client Data
- `id`: Unique identifier
- `name`: Client name
- `provider`: Provider name
- `providerId`: Provider ID
- `feeType`: "Percentage" or "Fixed"
- `rate`: Annual rate value
- `rateBreakdown`: Monthly/quarterly/annual fee values
- `paymentSchedule`: "Monthly" or "Quarterly"
- `participants`: Number of participants
- `clientSince`: Date client relationship began
- `lastPaymentPeriod`: Most recent payment period
- `lastPaymentReceived`: Date of last payment
- `lastRecordedAUM`: Object with amount and date
- `lastPaymentExpected`: Expected fee amount
- `lastPaymentActual`: Actual fee received
- `lastPaymentVariance`: Difference between expected and actual
- `currentPeriod`: Object with period and status
- `missingPayments`: Array of missing payment periods
### Payment Data
- `id`: Unique identifier
- `receivedDate`: Date payment was received
- `appliedPeriod`: Period payment applies to
- `aum`: Assets under management
- `expectedFee`: Calculated expected fee
- `actualFee`: Actual fee received
- `variance`: Difference between expected and actual
- `variancePercent`: Percentage variance
- `paymentType`: "Auto - ACH", "Check", "Wire", or "Invoice"
- `checkNumber`: Check number if applicable
- `notes`: Additional payment notes
- `hasAttachment`: Boolean for document attachment
- `attachmentId`: ID of attached document
### Provider Data
- `id`: Unique identifier
- `name`: Provider name
- `clientCount`: Number of clients
- `totalAssets`: Total AUM across all clients
- `totalParticipants`: Total participants across all clients
## Core Components
### Layout Components
- `Dashboard`: Main container component
- `Sidebar`: Navigation sidebar with client/provider selection
- `TopBar`: App header with navigation and theme toggle
- `MainPanel`: Primary content area
- `DocumentViewer`: Document preview panel
### Functional Components
- `ClientProvider`: Context provider for client data
- `ThemeProvider`: Context provider for theme management
- `PaymentForm`: Form for adding/editing payments
- `ClientDetails`: Client information display
- `PaymentHistory`: Payment transaction table
## Key Features & Logic
### Client Management
- Display client list in sidebar
- Toggle between clients and providers view
- Group clients by provider in provider view
- Search functionality for clients and providers
- Select client to display details and payment history
### Payment Processing
- Add new payments with validation
- Edit existing payments
- Delete payments
- Calculate expected fee based on AUM and fee structure
- Support for percentage and fixed fee types
- Support for monthly and quarterly payment schedules
- Track payment variances
### Document Management
- Attach documents to payments
- View attached documents in document viewer
- Toggle document viewer visibility
### UI/UX Features
- Responsive layout
- Dark/light theme toggle with persistent preference
- Pagination for payment history
- Status indicators for payments and clients
- Sorting and filtering capabilities
- Form validation
## Visual Elements
### Theme Components
- Color scheme: Emerald primary with slate neutrals
- Dark mode: Dark slate backgrounds with light text
- Light mode: White backgrounds with dark text
- Consistent contrast ratios for accessibility
### UI Components
- Cards with consistent styling
- Data tables with proper spacing
- Form inputs with icons
- Status badges with appropriate colors
- Toggle switches
- Buttons with hover states
- Search inputs
- Pagination controls
## Required Pages/Views
1. Dashboard with payment form and client details
2. Payment history table with pagination
3. Document viewer overlay
4. Client/provider selection sidebar
## Core Functionality Checklist
- Client data management
- Provider data management
- Payment processing
- Fee calculation
- Document attachment
- Theme switching
- Search and filtering
- Responsive layout
This reference covers al
///// FRONTEND GUIDE /////
### 401k Payment Management Dashboard: Integration Guide
## Hello Developer!
Welcome to the 401k Payment Management Dashboard wireframe! This React-based frontend application provides a complete, functional interface for managing 401k plan payments, client information, and payment history. The wireframe includes working components for client selection, payment entry/editing, payment history viewing, and document management - all with a premium look and feel featuring both light and dark modes.
# The frontend tech stack for the 401k Payment Management Dashboard includes:
- **React**: The core library used for building the user interface components
- **Next.js**: The React framework providing the application structure, routing, and server-side capabilities
- **TypeScript**: Used for type safety throughout the application
- **Tailwind CSS**: The utility-first CSS framework used for styling all components
- **Radix UI**: Provides accessible UI primitives that are styled with Tailwind
- **Lucide React**: The icon library used throughout the interface
- **React Context API**: Used for state management (client data and theme)
- **localStorage**: For persisting theme preferences
The application follows modern React patterns including:
- Functional components with hooks
- Context-based state management
- Server and client components (Next.js App Router pattern)
- Responsive design principles
This stack provides a robust, maintainable, and visually polished frontend with excellent developer experience and performance characteristics.
—-
You're already using SQLite as your data source, which is excellent! While this application will eventually expand to include multiple pages, we're currently focusing on the **Payment Management** page, which is the core functionality demonstrated in this wireframe.
## Integration Overview
The wireframe handles all UI rendering, state management, formatting, and user interactions. Your primary integration task is to ensure your backend provides the correct data structure that the frontend expects. The application uses a context-based data provider that expects a specific JSON structure.
Here's a simplified example of the JSON structure the frontend requires:
```json
{
  "clients": {
    "CL001": {
      "id": "CL001",
      "name": "Accelerate Technologies",
      "provider": "PR001",
      "providerId": "PR001",
      "providerName": "Fidelity Investments",
      "paymentSchedule": "Monthly",
      "feeType": "Percentage",
      "rate": 0.0625,
      "participants": 187,
      "clientSince": "05/12/2019",
      "lastAUM": 4783250,
      "lastAUMDate": "02/15/2024",
      "status": "Current"
    },
    "CL002": {
      "id": "CL002",
      "name": "Brightpath Solutions",
      "provider": "PR002",
      "providerId": "PR002",
      "providerName": "Vanguard",
      "paymentSchedule": "Quarterly",
      "feeType": "Percentage",
      "rate": 0.1875,
      "participants": 124,
      "clientSince": "08/23/2020",
      "lastAUM": 6254780,
      "lastAUMDate": "12/31/2023",
      "status": "Current"
    }
  },
  "providers": {
    "PR001": {
      "id": "PR001",
      "name": "Fidelity Investments",
      "clientCount": 5,
      "totalAssets": 78543250,
      "totalParticipants": 934
    },
    "PR002": {
      "id": "PR002",
      "name": "Vanguard",
      "clientCount": 4,
      "totalAssets": 54287600,
      "totalParticipants": 712
    }
  },
  "clientDetails": {
    "CL001": {
      "id": "CL001",
      "name": "Accelerate Technologies",
      "feeType": "Percentage",
      "rate": 0.0625,
      "rateBreakdown": { 
        "monthly": 0.0625, 
        "quarterly": 0.1875, 
        "annual": 0.75 
      }
    }
  },
  "paymentHistory": {
    "CL001": [
      {
        "id": "PMT001_CL001",
        "receivedDate": "03/05/2024",
        "appliedPeriod": "Feb 2024",
        "aum": 4783250
      }
    ]
  }
}

```
## Integration Approach
To successfully integrate your SQLite database with this frontend:
1. **Examine your database schema** to understand how your existing data maps to the required structure
2. **Create transformation functions** in your backend that query your database and shape the results into the expected JSON format
3. **Implement API endpoints** that serve this transformed data to the frontend
4. **Handle data mutations** (create/update/delete operations) from the frontend
The wireframe already handles:
- Client/provider selection and filtering
- Payment form validation and submission
- Payment history display with pagination
- Document viewing
- Theme switching and persistence
- All UI formatting and conditional styling
Your backend needs to focus on:
- Providing correctly structured data
- Calculating derived values (variances, rate breakdowns, etc.)
- Persisting changes to the database
- Serving document content when requested
## Key Database Operations
Beyond the initial data retrieval, your backend will need to handle these write operations:
1. **Adding Payments**: When a user submits the payment form, a new payment record should be created in your database, along with any calculated fields like variance and variance percentage.
2. **Updating Payments**: When a user edits an existing payment and submits the form, the corresponding record in your database should be updated with the new values.
3. **Deleting Payments**: When a user clicks the delete button on a payment record, that record should be removed from your database.
4. **Document Storage**: If a user attaches a document to a payment, your backend should store this document and create a reference to it in the payment record.
5. **Client Status Updates**: After payment operations, you may need to update client status information (like missing payments or last payment details) in your client records.
These operations should trigger appropriate updates to related data (like client totals or provider statistics) following your database's referential integrity rules.
## Using This Guide
The detailed guide below maps out every data-dependent element in the wireframe. For each component, it specifies exactly what JSON data is required and how it's used. Use this as a reference when implementing your backend integration to ensure all frontend features work correctly.
Rather than trying to modify your database schema to match this structure exactly, focus on creating a transformation layer in your backend that maps your existing data to the expected format.
---
### 401k Dashboard: Data Dependency Guide
This guide focuses exclusively on the JSON data dependencies that power the dashboard. It assumes developers have access to the source code and understand basic frontend concepts.
## Client List & Selection
### Client List Items
- **JSON Path**: `clients` array
- **Critical Fields**:
- `id` - Required for selection and lookup
- `name` - Primary display text
- `providerId` - Required for grouping in provider view
- `providerName` - Secondary display text
- **Data Note**: Missing clients will result in empty sidebar
### Provider List & Nested Clients
- **JSON Path**: `providers` array and `clients` filtered by `providerId`
- **Critical Fields**:
- `id` - Required for expansion state
- `name` - Primary display text
- `clientCount` - Displayed in provider summary
- `totalAssets` - Displayed as formatted currency
- **Data Note**: Provider view requires both arrays to function properly
## Client Details Card
### Client Identity & Status
- **JSON Path**: `clientDetails[selectedClient]`
- **Critical Fields**:
- `name` - Header display
- `missingPayments` - Controls status badge (empty array = "Current")
- **Data Note**: Status badge logic depends on `missingPayments` array length
### Fee Structure Section
- **JSON Path**: `clientDetails[selectedClient]`
- **Critical Fields**:
- `feeType` - Controls display format ("Percentage" or "Fixed")
- `rate` - Raw value (displayed as % or $ based on `feeType`)
- `rateBreakdown` - Object with monthly/quarterly/annual values
- `paymentSchedule` - Determines which rate breakdown to emphasize
- **Data Note**: Fee calculations throughout the app depend on these values being correct
### Last Payment Information
- **JSON Path**: `clientDetails[selectedClient]`
- **Critical Fields**:
- `lastPaymentPeriod` - Period label
- `lastPaymentExpected` - Raw number for expected fee
- `lastPaymentActual` - Raw number for actual fee
- `lastPaymentVariance` - Raw number for variance (drives conditional styling)
- **Data Note**: Variance styling depends on positive/negative/zero value
### AUM & Current Period
- **JSON Path**: `clientDetails[selectedClient]`
- **Critical Fields**:
- `lastRecordedAUM.amount` - Raw number for AUM
- `lastRecordedAUM.date` - Date string
- `currentPeriod.period` - Current period string
- `currentPeriod.status` - Status string (drives conditional styling)
- **Data Note**: Missing these fields will break the client details display
## Payment Form
### Form Population (Edit Mode)
- **JSON Path**: `paymentHistory[selectedClient][index]` (when editing)
- **Critical Fields**: All payment fields needed to populate form
- **Data Note**: Form expects complete payment object when in edit mode
### Expected Fee Calculation
- **JSON Path**: Uses `clientDetails[selectedClient].feeType` and `clientDetails[selectedClient].rate`
- **Critical Fields**:
- Client's `feeType` and `rate` - Used in calculation formula
- Form's `aum` value - User input that triggers calculation
- **Data Note**: This calculation happens in real-time as user types in AUM field
### Period Options Generation
- **JSON Path**: Uses `clientDetails[selectedClient].paymentSchedule`
- **Critical Fields**: `paymentSchedule` - Determines format of period options
- **Data Note**:
- "Monthly" schedule generates "Jan 2024", "Feb 2024", etc.
- "Quarterly" schedule generates "Q1 2024", "Q2 2024", etc.
## Payment History Table
### Payment Rows
- **JSON Path**: `paymentHistory[selectedClient]` array
- **Critical Fields**:
- `receivedDate` - Table cell content
- `appliedPeriod` - Table cell content
- `aum` - Table cell content (formatted as currency)
- `expectedFee` - Table cell content (formatted as currency)
- `actualFee` - Table cell content (formatted as currency)
- `variance` - Table cell content with conditional styling
- `variancePercent` - Displayed with variance
- `hasAttachment` - Controls document button state
- `attachmentId` - Used when viewing document
- **Data Note**: Missing or malformed payment data will break table rendering
### Pagination
- **JSON Path**: Length of `paymentHistory[selectedClient]` array
- **Data Note**: Pagination calculation depends on total number of payment records
## Document Viewer
### Document Display
- **JSON Path**: Uses `attachmentId` from selected payment
- **Critical Fields**: `attachmentId` - Used to fetch document content
- **Data Note**: Document viewer expects valid attachment IDs referenced in payment records
## Critical Calculations & Data Dependencies
### Expected Fee (Real-time)
- **Formula**: `feeType === "Percentage" ? aum * (rate / 100) : rate`
- **Data Dependencies**:
- Client's fee type and rate
- User-entered AUM value
- **Impact**: Affects form display and submitted payment data
### Variance & Variance Percentage
- **Formula**:
- Variance: `actualFee - expectedFee`
- Variance Percentage: `((actualFee - expectedFee) / expectedFee) * 100`
- **Data Dependencies**: Expected and actual fee values
- **Impact**: Drives conditional styling in payment history
### Client Status Determination
- **Logic**: Based on presence of items in `missingPayments` array
- **Data Dependencies**: `clientDetails[selectedClient].missingPayments`
- **Impact**: Controls status badge display and styling
### Period Options
- **Logic**: Generated based on client's payment schedule
- **Data Dependencies**: `clientDetails[selectedClient].paymentSchedule`
- **Impact**: Controls available options in period dropdown
This focused guide highlights only the critical data dependencies that would cause functionality issues if the JSON structure was incorrect or missing. Developers can reference the source code for implementation details of UI components and purely frontend functionality.