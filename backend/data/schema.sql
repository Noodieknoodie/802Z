----------------
-- TABLE: client_files
----------------
CREATE TABLE "client_files" (
    "file_id" INTEGER NOT NULL,
    "client_id" INTEGER NOT NULL,
    "file_name" TEXT NOT NULL,
    "onedrive_path" TEXT NOT NULL,
    "uploaded_at" DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY("file_id" AUTOINCREMENT),
    FOREIGN KEY("client_id") REFERENCES "clients"("client_id") ON DELETE CASCADE
);
----------------
-- TABLE: client_metrics
----------------
CREATE TABLE "client_metrics" (
	"id"	INTEGER NOT NULL,
	"client_id"	INTEGER NOT NULL,
	"last_payment_date"	TEXT,
	"last_payment_amount"	REAL,
	"last_payment_quarter"	INTEGER,
	"last_payment_year"	INTEGER,
	"total_ytd_payments"	REAL,
	"avg_quarterly_payment"	REAL,
	"last_recorded_assets"	REAL,
	"last_updated"	TEXT,
	"next_payment_due"	TEXT,
	UNIQUE("client_id"),
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("client_id") REFERENCES "clients"("client_id") ON DELETE CASCADE
);
----------------
-- TABLE: clients
----------------
CREATE TABLE "clients" (
	"client_id"	INTEGER NOT NULL,
	"display_name"	TEXT NOT NULL,
	"full_name"	TEXT,
	"ima_signed_date"	TEXT,
	"onedrive_folder_path"	TEXT,
	"valid_from"	DATETIME DEFAULT CURRENT_TIMESTAMP,
	"valid_to"	DATETIME,
	PRIMARY KEY("client_id" AUTOINCREMENT)
);
----------------
-- TABLE: contacts
----------------
CREATE TABLE contacts (
    contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    contact_type TEXT NOT NULL,
    contact_name TEXT,
    phone TEXT,
    email TEXT,
    fax TEXT,
    physical_address TEXT,
    mailing_address TEXT,
    valid_from DATETIME DEFAULT CURRENT_TIMESTAMP,
    valid_to DATETIME,
    FOREIGN KEY(client_id) REFERENCES clients(client_id) ON DELETE CASCADE
);
----------------
-- TABLE: contracts
----------------
CREATE TABLE "contracts" (
	"contract_id"	INTEGER NOT NULL,
	"client_id"	INTEGER NOT NULL,
	"contract_number"	TEXT,
	"provider_name"	TEXT,
	"contract_start_date"	TEXT,
	"fee_type"	TEXT,
	"percent_rate"	REAL,
	"flat_rate"	REAL,
	"payment_schedule"	TEXT,
	"num_people"	INTEGER,
	"notes"	TEXT,
	"valid_from"	DATETIME DEFAULT CURRENT_TIMESTAMP,
	"valid_to"	DATETIME,
	PRIMARY KEY("contract_id" AUTOINCREMENT),
	FOREIGN KEY("client_id") REFERENCES "clients"("client_id") ON DELETE CASCADE
);
----------------
-- TABLE: payment_files
----------------
CREATE TABLE "payment_files" (
    "payment_id" INTEGER NOT NULL,
    "file_id" INTEGER NOT NULL,
    "linked_at" DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY("payment_id", "file_id"),
    FOREIGN KEY("payment_id") REFERENCES "payments"("payment_id") ON DELETE CASCADE,
    FOREIGN KEY("file_id") REFERENCES "client_files"("file_id") ON DELETE CASCADE
);
----------------
-- TABLE: payments
----------------
CREATE TABLE "payments" (
	"payment_id"	INTEGER NOT NULL,
	"contract_id"	INTEGER NOT NULL,
	"client_id"	INTEGER NOT NULL,
	"received_date"	TEXT,
	"total_assets"	INTEGER,
	"expected_fee"	REAL,
	"actual_fee"	REAL,
	"method"	TEXT,
	"notes"	TEXT,
	"valid_from"	DATETIME DEFAULT CURRENT_TIMESTAMP,
	"valid_to"	DATETIME,
	"applied_start_month"	INTEGER,
	"applied_start_month_year"	INTEGER,
	"applied_end_month"	INTEGER,
	"applied_end_month_year"	INTEGER,
	"applied_start_quarter"	INTEGER,
	"applied_start_quarter_year"	INTEGER,
	"applied_end_quarter"	INTEGER,
	"applied_end_quarter_year"	INTEGER,
	PRIMARY KEY("payment_id" AUTOINCREMENT),
	FOREIGN KEY("client_id") REFERENCES "clients"("client_id") ON DELETE CASCADE,
	FOREIGN KEY("contract_id") REFERENCES "contracts"("contract_id") ON DELETE CASCADE
);
----------------
-- TABLE: quarterly_summaries
----------------
CREATE TABLE quarterly_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    total_payments REAL,
    total_assets REAL,
    payment_count INTEGER,
    avg_payment REAL,
    expected_total REAL,
    last_updated TEXT,
    FOREIGN KEY(client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
    UNIQUE(client_id, year, quarter)
);
----------------
-- TABLE: yearly_summaries
----------------
CREATE TABLE yearly_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    total_payments REAL,
    total_assets REAL,
    payment_count INTEGER,
    avg_payment REAL,
    yoy_growth REAL,
    last_updated TEXT,
    FOREIGN KEY(client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
    UNIQUE(client_id, year)
);
----------------
-- VIEW: client_payment_status
----------------
CREATE VIEW client_payment_status AS
SELECT
    c.client_id,
    c.display_name,
    ct.payment_schedule,
    ct.fee_type,
    ct.flat_rate,
    ct.percent_rate,
    -- Last payment information
    cm.last_payment_date,
    cm.last_payment_amount,
    latest.applied_end_month,
    latest.applied_end_month_year,
    latest.applied_end_quarter,
    latest.applied_end_quarter_year,
    -- Calculate current period (based on today's date - 1 period)
    CASE 
        WHEN ct.payment_schedule = 'monthly' THEN 
            CASE 
                WHEN strftime('%m', 'now') = '01' THEN 12 
                ELSE CAST(strftime('%m', 'now') AS INTEGER) - 1 
            END
        ELSE NULL
    END AS current_month,
    CASE 
        WHEN ct.payment_schedule = 'monthly' THEN 
            CASE 
                WHEN strftime('%m', 'now') = '01' THEN CAST(strftime('%Y', 'now') AS INTEGER) - 1
                ELSE CAST(strftime('%Y', 'now') AS INTEGER)
            END
        ELSE NULL
    END AS current_month_year,
    CASE 
        WHEN ct.payment_schedule = 'quarterly' THEN 
            CASE 
                WHEN CAST((strftime('%m', 'now') + 2) / 3 AS INTEGER) = 1 THEN 4
                ELSE CAST((strftime('%m', 'now') + 2) / 3 AS INTEGER) - 1
            END
        ELSE NULL
    END AS current_quarter,
    CASE 
        WHEN ct.payment_schedule = 'quarterly' THEN 
            CASE 
                WHEN CAST((strftime('%m', 'now') + 2) / 3 AS INTEGER) = 1 THEN CAST(strftime('%Y', 'now') AS INTEGER) - 1
                ELSE CAST(strftime('%Y', 'now') AS INTEGER)
            END
        ELSE NULL
    END AS current_quarter_year,
    -- Latest assets for calculating expected fee
    cm.last_recorded_assets,
    -- Calculate expected fee based on fee_type
    CASE
        WHEN ct.fee_type = 'flat' THEN ct.flat_rate
        WHEN ct.fee_type = 'percentage' AND cm.last_recorded_assets IS NOT NULL THEN 
            ROUND(cm.last_recorded_assets * (ct.percent_rate / 100.0), 2)
        ELSE NULL
    END AS expected_fee,
    -- Determine payment status (Due/Paid)
    CASE
        WHEN ct.payment_schedule = 'monthly' AND (
            latest.applied_end_month_year IS NULL OR
            latest.applied_end_month_year < CASE 
                WHEN strftime('%m', 'now') = '01' THEN CAST(strftime('%Y', 'now') AS INTEGER) - 1
                ELSE CAST(strftime('%Y', 'now') AS INTEGER)
            END OR
            (latest.applied_end_month_year = CASE 
                WHEN strftime('%m', 'now') = '01' THEN CAST(strftime('%Y', 'now') AS INTEGER) - 1
                ELSE CAST(strftime('%Y', 'now') AS INTEGER)
            END AND latest.applied_end_month < CASE 
                WHEN strftime('%m', 'now') = '01' THEN 12 
                ELSE CAST(strftime('%m', 'now') AS INTEGER) - 1 
            END)
        ) THEN 'Due'
        WHEN ct.payment_schedule = 'quarterly' AND (
            latest.applied_end_quarter_year IS NULL OR
            latest.applied_end_quarter_year < CASE 
                WHEN CAST((strftime('%m', 'now') + 2) / 3 AS INTEGER) = 1 THEN CAST(strftime('%Y', 'now') AS INTEGER) - 1
                ELSE CAST(strftime('%Y', 'now') AS INTEGER)
            END OR
            (latest.applied_end_quarter_year = CASE 
                WHEN CAST((strftime('%m', 'now') + 2) / 3 AS INTEGER) = 1 THEN CAST(strftime('%Y', 'now') AS INTEGER) - 1
                ELSE CAST(strftime('%Y', 'now') AS INTEGER)
            END AND latest.applied_end_quarter < CASE 
                WHEN CAST((strftime('%m', 'now') + 2) / 3 AS INTEGER) = 1 THEN 4
                ELSE CAST((strftime('%m', 'now') + 2) / 3 AS INTEGER) - 1
            END)
        ) THEN 'Due'
        ELSE 'Paid'
    END AS payment_status
FROM 
    clients c
JOIN 
    contracts ct ON c.client_id = ct.client_id AND ct.valid_to IS NULL
LEFT JOIN 
    client_metrics cm ON c.client_id = cm.client_id
LEFT JOIN (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY client_id ORDER BY received_date DESC) as rn
    FROM payments
    WHERE valid_to IS NULL
) latest ON c.client_id = latest.client_id AND latest.rn = 1
WHERE 
    c.valid_to IS NULL;
----------------
-- VIEW: contract_rate_display
----------------
CREATE VIEW contract_rate_display AS
SELECT
    c.contract_id,
    c.client_id,
    c.provider_name,
    c.fee_type,
    c.payment_schedule,
    c.percent_rate,
    c.flat_rate,
    -----------------------------------------------------------------------
    -- Show frequency-based rate as stored (the "official" one):
    -----------------------------------------------------------------------
    CASE
        WHEN c.fee_type = 'percentage' THEN c.percent_rate
        ELSE NULL
    END AS frequency_percent_rate,
    CASE
        WHEN c.fee_type = 'flat' THEN c.flat_rate
        ELSE NULL
    END AS frequency_flat_rate,
    -----------------------------------------------------------------------
    -- Annual percentage rate (derived from the stored rate):
    -----------------------------------------------------------------------
    CASE
        WHEN c.fee_type = 'percentage' AND c.payment_schedule = 'monthly'
            THEN c.percent_rate * 12
        WHEN c.fee_type = 'percentage' AND c.payment_schedule = 'quarterly'
            THEN c.percent_rate * 4
        WHEN c.fee_type = 'percentage'
            THEN c.percent_rate  -- if actual stored rate was annual
        ELSE NULL
    END AS annual_percent_rate,
    -----------------------------------------------------------------------
    -- Monthly percentage rate (derived):
    -----------------------------------------------------------------------
    CASE
        WHEN c.fee_type = 'percentage' AND c.payment_schedule = 'monthly'
            THEN c.percent_rate
        WHEN c.fee_type = 'percentage' AND c.payment_schedule = 'quarterly'
            THEN c.percent_rate / 3.0
        WHEN c.fee_type = 'percentage'
            THEN c.percent_rate / 12.0
        ELSE NULL
    END AS monthly_percent_rate,
    -----------------------------------------------------------------------
    -- Quarterly percentage rate (derived):
    -----------------------------------------------------------------------
    CASE
        WHEN c.fee_type = 'percentage' AND c.payment_schedule = 'monthly'
            THEN c.percent_rate * 3.0
        WHEN c.fee_type = 'percentage' AND c.payment_schedule = 'quarterly'
            THEN c.percent_rate
        WHEN c.fee_type = 'percentage'
            THEN c.percent_rate / 4.0
        ELSE NULL
    END AS quarterly_percent_rate,
    -----------------------------------------------------------------------
    -- Annual flat rate (derived):
    -----------------------------------------------------------------------
    CASE
        WHEN c.fee_type = 'flat' AND c.payment_schedule = 'monthly'
            THEN c.flat_rate * 12
        WHEN c.fee_type = 'flat' AND c.payment_schedule = 'quarterly'
            THEN c.flat_rate * 4
        WHEN c.fee_type = 'flat'
            THEN c.flat_rate
        ELSE NULL
    END AS annual_flat_rate,
    -----------------------------------------------------------------------
    -- Monthly flat rate (derived):
    -----------------------------------------------------------------------
    CASE
        WHEN c.fee_type = 'flat' AND c.payment_schedule = 'monthly'
            THEN c.flat_rate
        WHEN c.fee_type = 'flat' AND c.payment_schedule = 'quarterly'
            THEN c.flat_rate / 3.0
        WHEN c.fee_type = 'flat'
            THEN c.flat_rate / 12.0
        ELSE NULL
    END AS monthly_flat_rate,
    -----------------------------------------------------------------------
    -- Quarterly flat rate (derived):
    -----------------------------------------------------------------------
    CASE
        WHEN c.fee_type = 'flat' AND c.payment_schedule = 'monthly'
            THEN c.flat_rate * 3.0
        WHEN c.fee_type = 'flat' AND c.payment_schedule = 'quarterly'
            THEN c.flat_rate
        WHEN c.fee_type = 'flat'
            THEN c.flat_rate / 4.0
        ELSE NULL
    END AS quarterly_flat_rate
FROM contracts c;
----------------
-- VIEW: payment_file_view
----------------
CREATE VIEW payment_file_view AS
SELECT 
    p.payment_id,
    p.client_id,
    p.contract_id,
    p.received_date,
    p.actual_fee,
    CASE WHEN cf.file_id IS NOT NULL THEN 1 ELSE 0 END AS has_file,
    cf.file_id,
    cf.file_name,
    cf.onedrive_path
FROM payments p
LEFT JOIN payment_files pf ON p.payment_id = pf.payment_id
LEFT JOIN client_files cf ON pf.file_id = cf.file_id;
----------------
-- VIEW: payment_with_aum_fallback
----------------
CREATE VIEW payment_with_aum_fallback AS
SELECT
    p.*,
    COALESCE(
        p.total_assets,
        (
            SELECT p2.total_assets
            FROM payments p2
            WHERE p2.client_id    = p.client_id
              AND p2.contract_id  = p.contract_id
              AND p2.total_assets IS NOT NULL
              AND p2.received_date < p.received_date
            ORDER BY p2.received_date DESC
            LIMIT 1
        )
    ) AS final_assets
FROM payments p;
----------------
-- TRIGGER: payments_update_variance_insert
----------------
CREATE TRIGGER payments_update_variance_insert
AFTER INSERT ON payments
FOR EACH ROW
BEGIN
    -- We do a second UPDATE to set variance/variance_percent on the same row
    UPDATE payments
    SET 
        variance = (actual_fee - expected_fee),
        variance_percent = CASE
            WHEN expected_fee IS NOT NULL 
                 AND expected_fee <> 0 
                 AND actual_fee IS NOT NULL
            THEN ((actual_fee - expected_fee) / expected_fee) * 100
            ELSE NULL
        END
    WHERE payment_id = NEW.payment_id;
END;
----------------
-- TRIGGER: payments_update_variance_update
----------------
CREATE TRIGGER payments_update_variance_update
AFTER UPDATE ON payments
FOR EACH ROW
BEGIN
    UPDATE payments
    SET 
        variance = (actual_fee - expected_fee),
        variance_percent = CASE
            WHEN expected_fee IS NOT NULL 
                 AND expected_fee <> 0 
                 AND actual_fee IS NOT NULL
            THEN ((actual_fee - expected_fee) / expected_fee) * 100
            ELSE NULL
        END
    WHERE payment_id = NEW.payment_id;
END;
----------------
-- TRIGGER: update_quarterly_after_payment
----------------
CREATE TRIGGER update_quarterly_after_payment
AFTER INSERT ON payments
BEGIN
    INSERT OR REPLACE INTO quarterly_summaries
    (client_id, year, quarter, total_payments, total_assets, payment_count, avg_payment, expected_total, last_updated)
    SELECT
        client_id,
        applied_start_quarter_year,
        applied_start_quarter,
        SUM(actual_fee),
        AVG(total_assets),
        COUNT(*),
        AVG(actual_fee),
        MAX(expected_fee),
        datetime('now')
    FROM payments
    WHERE client_id = NEW.client_id
      AND applied_start_quarter_year = NEW.applied_start_quarter_year
      AND applied_start_quarter = NEW.applied_start_quarter
    GROUP BY client_id, applied_start_quarter_year, applied_start_quarter;
END;
----------------
-- TRIGGER: update_yearly_after_quarterly
----------------
CREATE TRIGGER update_yearly_after_quarterly
AFTER INSERT ON quarterly_summaries
BEGIN
    INSERT OR REPLACE INTO yearly_summaries
    (client_id, year, total_payments, total_assets, payment_count, avg_payment, yoy_growth, last_updated)
    SELECT 
        client_id,
        year,
        SUM(total_payments),
        AVG(total_assets),
        SUM(payment_count),
        AVG(avg_payment),
        NULL,
        datetime('now')
    FROM quarterly_summaries
    WHERE client_id = NEW.client_id
      AND year = NEW.year
    GROUP BY client_id, year;
END;
----------------
-- INDEX: idx_client_metrics_lookup
----------------
CREATE INDEX idx_client_metrics_lookup ON client_metrics(client_id);
----------------
-- INDEX: idx_contacts_client_id
----------------
CREATE INDEX idx_contacts_client_id ON contacts(client_id);
----------------
-- INDEX: idx_contacts_type
----------------
CREATE INDEX idx_contacts_type ON contacts(client_id, contact_type);
----------------
-- INDEX: idx_contracts_client_id
----------------
CREATE INDEX idx_contracts_client_id ON contracts(client_id);
----------------
-- INDEX: idx_contracts_provider
----------------
CREATE INDEX idx_contracts_provider ON contracts(provider_name);
----------------
-- INDEX: idx_payments_applied_months
----------------
CREATE INDEX idx_payments_applied_months ON payments (
    client_id,
    applied_start_month_year,
    applied_start_month,
    applied_end_month_year,
    applied_end_month
);
----------------
-- INDEX: idx_payments_client_id
----------------
CREATE INDEX idx_payments_client_id ON payments(client_id);
----------------
-- INDEX: idx_payments_contract_id
----------------
CREATE INDEX idx_payments_contract_id ON payments(contract_id);
----------------
-- INDEX: idx_payments_date
----------------
CREATE INDEX idx_payments_date ON payments(client_id, received_date DESC);
----------------
-- INDEX: idx_quarterly_lookup
----------------
CREATE INDEX idx_quarterly_lookup ON quarterly_summaries(client_id, year, quarter);
----------------
-- INDEX: idx_yearly_lookup
----------------
CREATE INDEX idx_yearly_lookup ON yearly_summaries(client_id, year);
