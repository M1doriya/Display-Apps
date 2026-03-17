# AGENTS.md

## System Architecture

The application flow is:

1. User uploads financial PDFs
2. Tensorlake extracts content
3. API-call stage transforms extraction into KreditLab JSON
4. HTML generator renders report

Rules:
- Tensorlake = extraction only (not authoritative)
- API-call stage = single source of truth (ALL logic lives here)
- HTML generator = rendering only (no logic, no inference)

---

## Canonical Data Rule

There must be exactly ONE canonical case-level JSON object.

All of the following MUST use that object only:
- ratios
- DSCR
- TNW
- funding analysis
- working capital
- integrity checks
- notes / observations / recommendations
- HTML output

No module may:
- read raw Tensorlake output after merge
- use intermediate data
- invent fallback assumptions

---

## Multi-File Handling

- All uploaded files = ONE case
- Never process only 1 file if multiple exist
- Never let one document suppress another

Supported document types:
- audit_report / AFS
- balance_sheet
- bank_statement
- profit_and_loss
- other_supporting_document

---

## Source Authority

- Audit → company info / audited structure
- Balance Sheet → assets, liabilities, equity, borrowings
- P&L → revenue, costs, profit, expenses
- Bank Statement → supporting liquidity only

Never overwrite strong source with weaker source.

---

## Missing vs Zero (CRITICAL)

- Missing ≠ 0
- Never default missing values to zero
- Block calculations if inputs missing
- Use flags instead of fake numbers

---

## Synonym-Aware Mapping

Financial labels vary. Always map by meaning, not exact words.

Examples:
- revenue = sales = turnover
- COGS = cost of sales = project cost
- receivables = debtors
- payables = creditors
- finance cost = interest = bank charges
- restricted cash = pledged deposits = sinking fund

Use:
- section headers
- structure
- subtotal relationships

---

## Unknown Parameter Rule

If a field is not recognized:
- DO NOT DROP IT
- Map to closest valid section
- Preserve original label in metadata

---

## Period Reconciliation

- Extract all dates from all files
- Determine dominant period
- Merge only compatible files
- Flag mismatches

---

## Schema Enforcement

- MUST follow KreditLab_v7_9_updated.txt
- `_schema_info.version = v7.9`
- Reject v7.7 outputs
- Validate structure before render

---

## Narrative Rules

Narrative MUST match data.

DO NOT say:
- “P&L missing” if P&L data exists
- “Balance sheet missing” if BS data exists
- “Finance cost unavailable” if extracted

---

## HTML Rules

HTML must:
- use ONLY canonical JSON
- not re-interpret data
- not generate its own assumptions

---

## Data Quality Flags

Always support:
- missing_required_inputs
- period_mismatch
- synonym_mapped_fields
- unknown_parameters_preserved
- blocked_derived_metrics
- report_consistency_issues
