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
	"next_payment_due"	TEXT, last_payment_month INTEGER,
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
	"valid_to"	DATETIME, provider_id INTEGER REFERENCES providers(provider_id),
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
-- TABLE: providers
----------------
CREATE TABLE "providers" (
    "provider_id" INTEGER NOT NULL,
    "name" TEXT NOT NULL UNIQUE,
    "valid_from" DATETIME DEFAULT CURRENT_TIMESTAMP,
    "valid_to" DATETIME,
    PRIMARY KEY("provider_id" AUTOINCREMENT)
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
-- VIEW: client_payment_basic
----------------
CREATE VIEW client_payment_basic AS
SELECT
    c.client_id,
    c.display_name,
    ct.payment_schedule,
    ct.fee_type,
    ct.percent_rate,
    ct.flat_rate,
    cm.last_recorded_assets,
    cm.last_payment_date,
    cm.last_payment_amount,
    latest.applied_end_month,
    latest.applied_end_month_year,
    latest.applied_end_quarter,
    latest.applied_end_quarter_year
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
-- VIEW: frontend_client_details
----------------
CREATE VIEW frontend_client_details AS
SELECT
    c.client_id AS id,
    c.display_name AS name,
    ct.provider_id AS providerId,
    p.name AS providerName,
    ct.num_people AS participants,
    CASE 
        WHEN c.ima_signed_date IS NOT NULL THEN date(c.ima_signed_date)
        ELSE NULL
    END AS clientSince,
    ct.fee_type AS feeType,
    CASE
        WHEN ct.fee_type = 'percentage' THEN ct.percent_rate
        WHEN ct.fee_type = 'flat' THEN ct.flat_rate
        ELSE NULL
    END AS rate,
    ct.payment_schedule AS paymentSchedule,
    json_object(
        'monthly', crd.monthly_percent_rate,
        'quarterly', crd.quarterly_percent_rate,
        'annual', crd.annual_percent_rate
    ) AS percentRateBreakdown,
    json_object(
        'monthly', crd.monthly_flat_rate,
        'quarterly', crd.quarterly_flat_rate,
        'annual', crd.annual_flat_rate
    ) AS flatRateBreakdown,
    cm.last_payment_date AS lastPaymentDate,
    cm.last_payment_amount AS lastPaymentAmount,
    CASE
        WHEN ct.payment_schedule = 'monthly' AND cm.last_payment_month IS NOT NULL THEN
            CASE 
                WHEN cm.last_payment_month = 1 THEN 'Jan'
                WHEN cm.last_payment_month = 2 THEN 'Feb'
                WHEN cm.last_payment_month = 3 THEN 'Mar'
                WHEN cm.last_payment_month = 4 THEN 'Apr'
                WHEN cm.last_payment_month = 5 THEN 'May'
                WHEN cm.last_payment_month = 6 THEN 'Jun'
                WHEN cm.last_payment_month = 7 THEN 'Jul'
                WHEN cm.last_payment_month = 8 THEN 'Aug'
                WHEN cm.last_payment_month = 9 THEN 'Sep'
                WHEN cm.last_payment_month = 10 THEN 'Oct'
                WHEN cm.last_payment_month = 11 THEN 'Nov'
                WHEN cm.last_payment_month = 12 THEN 'Dec'
            END || ' ' || cm.last_payment_year
        WHEN ct.payment_schedule = 'quarterly' AND cm.last_payment_quarter IS NOT NULL THEN
            'Q' || cm.last_payment_quarter || ' ' || cm.last_payment_year
        ELSE NULL
    END AS lastPaymentPeriod,
    latest_payment.expected_fee AS lastPaymentExpected,
    latest_payment.actual_fee AS lastPaymentActual,
    latest_payment.variance AS lastPaymentVariance,
    cm.last_recorded_assets AS lastRecordedAUM,
    CASE
        WHEN cps.current_month IS NOT NULL THEN
            CASE 
                WHEN cps.current_month = 1 THEN 'Jan'
                WHEN cps.current_month = 2 THEN 'Feb'
                WHEN cps.current_month = 3 THEN 'Mar'
                WHEN cps.current_month = 4 THEN 'Apr'
                WHEN cps.current_month = 5 THEN 'May'
                WHEN cps.current_month = 6 THEN 'Jun'
                WHEN cps.current_month = 7 THEN 'Jul'
                WHEN cps.current_month = 8 THEN 'Aug'
                WHEN cps.current_month = 9 THEN 'Sep'
                WHEN cps.current_month = 10 THEN 'Oct'
                WHEN cps.current_month = 11 THEN 'Nov'
                WHEN cps.current_month = 12 THEN 'Dec'
            END || ' ' || cps.current_month_year
        WHEN cps.current_quarter IS NOT NULL THEN
            'Q' || cps.current_quarter || ' ' || cps.current_quarter_year
        ELSE NULL
    END AS currentPeriod,
    cps.payment_status AS currentStatus
FROM 
    clients c
JOIN 
    contracts ct ON c.client_id = ct.client_id AND ct.valid_to IS NULL
LEFT JOIN
    providers p ON ct.provider_id = p.provider_id
LEFT JOIN
    contract_rate_display crd ON ct.contract_id = crd.contract_id
LEFT JOIN
    client_metrics cm ON c.client_id = cm.client_id
LEFT JOIN
    client_payment_status cps ON c.client_id = cps.client_id
LEFT JOIN (
    SELECT *
    FROM payments
    WHERE payment_id IN (
        SELECT MAX(payment_id)
        FROM payments
        WHERE valid_to IS NULL
        GROUP BY client_id
    )
) latest_payment ON c.client_id = latest_payment.client_id
WHERE 
    c.valid_to IS NULL;
----------------
-- VIEW: frontend_client_list
----------------
CREATE VIEW frontend_client_list AS
SELECT 
    c.client_id AS id,
    c.display_name AS name,
    ct.provider_id AS providerId,
    p.name AS providerName,
    co.contact_name AS contact,
    ct.num_people AS participants,
    CASE 
        WHEN c.ima_signed_date IS NOT NULL THEN date(c.ima_signed_date)
        ELSE NULL
    END AS clientSince,
    cps.payment_status AS status
FROM 
    clients c
JOIN 
    contracts ct ON c.client_id = ct.client_id AND ct.valid_to IS NULL
LEFT JOIN
    providers p ON ct.provider_id = p.provider_id
LEFT JOIN
    contacts co ON c.client_id = co.client_id AND co.contact_type = 'Primary' AND co.valid_to IS NULL
LEFT JOIN
    client_payment_status cps ON c.client_id = cps.client_id
WHERE 
    c.valid_to IS NULL;
----------------
-- VIEW: frontend_payment_history
----------------
CREATE VIEW frontend_payment_history AS
SELECT
    p.payment_id AS id,
    p.client_id AS clientId,
    date(p.received_date) AS receivedDate,
    CASE
        WHEN ct.payment_schedule = 'monthly' AND p.applied_start_month IS NOT NULL THEN
            CASE 
                WHEN p.applied_start_month = 1 THEN 'Jan'
                WHEN p.applied_start_month = 2 THEN 'Feb'
                WHEN p.applied_start_month = 3 THEN 'Mar'
                WHEN p.applied_start_month = 4 THEN 'Apr'
                WHEN p.applied_start_month = 5 THEN 'May'
                WHEN p.applied_start_month = 6 THEN 'Jun'
                WHEN p.applied_start_month = 7 THEN 'Jul'
                WHEN p.applied_start_month = 8 THEN 'Aug'
                WHEN p.applied_start_month = 9 THEN 'Sep'
                WHEN p.applied_start_month = 10 THEN 'Oct'
                WHEN p.applied_start_month = 11 THEN 'Nov'
                WHEN p.applied_start_month = 12 THEN 'Dec'
            END || ' ' || p.applied_start_month_year
        WHEN ct.payment_schedule = 'quarterly' AND p.applied_start_quarter IS NOT NULL THEN
            'Q' || p.applied_start_quarter || ' ' || p.applied_start_quarter_year
        ELSE NULL
    END AS appliedPeriod,
    p.total_assets AS aum,
    p.expected_fee AS expectedFee,
    p.actual_fee AS actualFee,
    p.variance AS variance,
    CASE
        WHEN p.expected_fee IS NOT NULL AND p.expected_fee <> 0 THEN
            (p.variance / p.expected_fee) * 100
        ELSE NULL
    END AS variancePercent,
    p.method AS paymentType,
    p.notes AS notes,
    CASE WHEN pf.has_file = 1 THEN 1 ELSE 0 END AS hasAttachment,
    pf.file_id AS attachmentId
FROM 
    payments p
JOIN 
    contracts ct ON p.contract_id = ct.contract_id
LEFT JOIN
    payment_file_view pf ON p.payment_id = pf.payment_id
WHERE 
    p.valid_to IS NULL
ORDER BY 
    p.received_date DESC;
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
