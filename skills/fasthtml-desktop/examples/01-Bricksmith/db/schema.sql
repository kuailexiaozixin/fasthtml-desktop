-- Bricksmith OLTP schema (SQLite). Idempotent.
--
-- SQLite has no schemas, so the upstream `bricksmith.` qualifier is dropped
-- here. Application code may keep writing `bricksmith.properties`: the shim in
-- db/__init__.py strips the prefix before the statement reaches SQLite.
--
-- Type mapping vs upstream PostgreSQL:
--   BIGSERIAL PRIMARY KEY -> INTEGER PRIMARY KEY AUTOINCREMENT
--   TIMESTAMPTZ           -> TEXT   (ISO-8601, DEFAULT CURRENT_TIMESTAMP)
--   DATE                  -> TEXT   ('YYYY-MM-DD')
--   JSONB / TEXT[]        -> TEXT   (JSON; decoded back to dict/list on read)
--   NUMERIC(p,s)          -> NUMERIC (SQLite keeps this affinity as REAL)

-- ── users + sessions ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT NOT NULL UNIQUE,
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_slug   TEXT,
    title        TEXT,
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS chat_sessions_user_idx ON chat_sessions(user_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS chat_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role        TEXT NOT NULL,   -- user | assistant | tool | system
    content     TEXT NOT NULL,
    tool_calls  TEXT,            -- JSON
    agent_slug  TEXT,
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS chat_messages_session_idx ON chat_messages(session_id, id);

-- ── property + CRE core ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS properties (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    slug           TEXT UNIQUE NOT NULL,
    name           TEXT NOT NULL,
    address        TEXT,
    city           TEXT,
    state          TEXT,
    zip            TEXT,
    metro          TEXT,
    asset_type     TEXT NOT NULL,    -- multifamily | office | industrial | retail
    submarket      TEXT,
    units          INTEGER,
    year_built     INTEGER,
    year_renovated INTEGER,
    sqft           INTEGER,
    land_sqft      INTEGER,
    occupancy_pct  NUMERIC,
    asking_price   NUMERIC,
    description    TEXT,
    listing_status TEXT,             -- on_market | off_market | closed
    seller_intent  TEXT,             -- cold | warm | hot
    deal_stage     TEXT,             -- sourced|screened|loi|psa|diligence|committee|closing|closed|held|exited
    ownership      TEXT,             -- institutional|private|family_office|reit|developer|jv
    noi_annual     NUMERIC,          -- stabilized / in-place annualized NOI
    cap_rate       NUMERIC,          -- implied cap rate on asking_price
    created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- Upstream carried `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` here for clusters
-- seeded before deal_stage/ownership/noi_annual/cap_rate existed. SQLite has no
-- `IF NOT EXISTS` for ADD COLUMN, and this example always creates the table
-- with those columns already present, so the alters are unnecessary.

CREATE INDEX IF NOT EXISTS properties_metro_idx  ON properties(metro);
CREATE INDEX IF NOT EXISTS properties_type_idx   ON properties(asset_type);
CREATE INDEX IF NOT EXISTS properties_status_idx ON properties(listing_status);
CREATE INDEX IF NOT EXISTS properties_stage_idx  ON properties(deal_stage);

CREATE TABLE IF NOT EXISTS rent_rolls (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id  INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    as_of_date   TEXT NOT NULL,
    units        TEXT NOT NULL,   -- JSON [{unit, type, sqft, tenant, rent, lease_start, lease_end, status}]
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (property_id, as_of_date)
);

CREATE TABLE IF NOT EXISTS t12_statements (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id  INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    month        TEXT NOT NULL,   -- first-of-month
    gross_rent   NUMERIC,
    other_income NUMERIC,
    vacancy_loss NUMERIC,
    opex         TEXT,            -- JSON {taxes, insurance, utilities, maintenance, payroll, mgmt, other}
    noi          NUMERIC,
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (property_id, month)
);
CREATE INDEX IF NOT EXISTS t12_property_month_idx ON t12_statements(property_id, month DESC);

CREATE TABLE IF NOT EXISTS leases (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id  INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    unit         TEXT,
    tenant       TEXT,
    unit_type    TEXT,
    sqft         INTEGER,
    start_date   TEXT,
    end_date     TEXT,
    base_rent    NUMERIC,
    escalations  TEXT,         -- JSON [{date, pct | amount}]
    options      TEXT,         -- JSON renewal options
    status       TEXT,         -- active | expired | pending
    doc_path     TEXT,
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS leases_property_idx ON leases(property_id);
CREATE INDEX IF NOT EXISTS leases_tenant_idx   ON leases(tenant);

CREATE TABLE IF NOT EXISTS comps_sales (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id    INTEGER REFERENCES properties(id) ON DELETE SET NULL,
    comp_name      TEXT,
    city           TEXT,
    state          TEXT,
    asset_type     TEXT,
    sqft           INTEGER,
    units          INTEGER,
    sale_date      TEXT,
    sale_price     NUMERIC,
    cap_rate       NUMERIC,
    price_per_unit NUMERIC,
    price_per_sqft NUMERIC,
    source         TEXT
);
CREATE INDEX IF NOT EXISTS comps_sales_property_idx ON comps_sales(property_id);

CREATE TABLE IF NOT EXISTS comps_rents (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id    INTEGER REFERENCES properties(id) ON DELETE SET NULL,
    comp_name      TEXT,
    unit_type      TEXT,
    sqft           INTEGER,
    rent           NUMERIC,
    rent_per_sqft  NUMERIC,
    effective_date TEXT,
    source         TEXT
);
CREATE INDEX IF NOT EXISTS comps_rents_property_idx ON comps_rents(property_id);

CREATE TABLE IF NOT EXISTS pro_formas (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id  INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    name         TEXT,
    assumptions  TEXT NOT NULL,  -- JSON {hold_years, purchase_price, rent_growth, vacancy, expense_growth, exit_cap, ...}
    projections  TEXT NOT NULL,  -- JSON [{year, revenue, opex, noi, capex, cash_flow}]
    returns      TEXT NOT NULL,  -- JSON {irr, coc, moic, dscr, ltv, equity_multiple}
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS debt_stacks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id  INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    name         TEXT,
    tranches     TEXT NOT NULL,  -- JSON [{name, lender, amount, rate, amort_years, term_years, io_years, type}]
    ltv          NUMERIC,
    dscr         NUMERIC,
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS investor_crm (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    firm         TEXT,
    email        TEXT,
    check_size   NUMERIC,
    stage        TEXT,          -- cold | qualified | meeting | committed | closed | passed
    focus        TEXT,          -- multifamily | office | mixed | industrial | retail
    geography    TEXT,
    last_touch   TEXT,
    notes        TEXT,
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS crm_stage_idx ON investor_crm(stage);

CREATE TABLE IF NOT EXISTS market_signals (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    metro        TEXT NOT NULL,
    asset_type   TEXT,
    metric       TEXT NOT NULL,   -- cap_rate | absorption | employment | rent_growth | vacancy
    value        NUMERIC,
    as_of_date   TEXT NOT NULL,
    source       TEXT,
    UNIQUE (metro, asset_type, metric, as_of_date)
);
CREATE INDEX IF NOT EXISTS market_signals_lookup_idx ON market_signals(metro, metric, as_of_date DESC);

CREATE TABLE IF NOT EXISTS dd_findings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id  INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    agent_slug   TEXT NOT NULL,
    category     TEXT NOT NULL,   -- title | zoning | physical | environmental | lease | ops
    severity     TEXT NOT NULL,   -- info | low | medium | high | critical
    summary      TEXT NOT NULL,
    detail       TEXT,
    source_doc   TEXT,
    source_page  INTEGER,
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS dd_property_idx ON dd_findings(property_id, severity);

CREATE TABLE IF NOT EXISTS agent_invocations (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE,
    agent_slug   TEXT NOT NULL,
    input        TEXT,
    tools_used   TEXT,            -- JSON array (upstream: TEXT[])
    duration_ms  INTEGER,
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS agent_invocations_session_idx ON agent_invocations(session_id, created_at DESC);

CREATE TABLE IF NOT EXISTS prompt_versions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slug        TEXT NOT NULL,
    content     TEXT NOT NULL,
    changed_by  TEXT,
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS prompt_versions_slug_idx ON prompt_versions(slug, id DESC);
