"""
Kredit Lab Financial Report Generator
=====================================
Version: 7.7 (Full v7.9 Schema / v7.9 Framework Compatibility)
Description: Streamlit app that renders JSON financial analysis to interactive HTML report
Author: Kredit Lab
Last Updated: February 2026

Changes in v7.7:
- NEW: Excel export — formatted .xlsx with 8 sheets (Summary, P&L, BS, Ratios, WC, DSCR, TNW, Observations)
- NEW: v7.9 framework compatibility (schema detection, version display)
- FIX: PDF AssertionError on Railway — removed Noto Color Emoji, Symbola only
- FIX: PDF error message now shows actual error instead of generic "install weasyprint"
- FIX: 4-column download layout (HTML, PDF, Excel, JSON)

Changes in v7.6:
- FIX: PDF emoji rendering — uses Symbola font for proper emoji display instead of ugly text replacements
- FIX: PDF conversion quality — comprehensive print CSS matching HTML light theme exactly
- UPDATED: Dockerfile requires fonts-symbola for emoji support in PDF output

Changes in v7.5:
- NEW: PDF Download option — users can now download the report as PDF alongside HTML and JSON
- NEW: PDF uses weasyprint for high-fidelity HTML-to-PDF conversion
- NEW: PDF automatically renders in light theme (print-optimized) regardless of toggle state
- NEW: Download tab now shows 3 columns: HTML | PDF | JSON
- UPDATED: PDF strips JavaScript theme toggle and forces light mode for clean print output
- TECHNICAL: Uses weasyprint library; Railway requires: pip install weasyprint

Changes in v7.4:
- NEW: Full v7.7 and v7.8 framework compatibility (schema detection, version gates, rendering)
- NEW: v7.8 support — Phase 0 (MAP) mandatory source mapping, note-reading mandate,
  disclosure note vs direct breakdown distinction. Rendering identical to v7.7.
- NEW: Prior Year Adjustments rendering in Audit Opinion section — displays restatement
  details (description, affected line items, RM amounts) when prior_year_adjustments
  exists in company_info with has_restatement=true
- FIX: WCR validation completely reworked — v7.6/v7.7/v7.8 expects single "values" field only;
  v7.1/v7.2 expects dual values_standard/values_period_adjusted. No more false warnings.
- FIX: WCR rendering label — v7.6+ shows "WC Requirement" (clean), v7.2 shows "WC Requirement (Standard)"
  with optional period-adjusted sub-row. Eliminates confusing "(Standard)" label for single-value schema.
- NEW: Audit opinion type handles "Unqualified (Restated Comparative)" badge display
- UPDATED: All schema version gate lists include "v7.7" (v7.8 maps to v7.7 internally)
- UPDATED: detect_schema_version supports v7.7 and v7.8 explicitly

Changes in v7.3:
- FIX: Period label parser now recognises "(Audited - Restated)" and similar qualified suffixes
- FIX: WCR validation gated to v7.2/v7.3 schema only for dual values check
- NEW: Explicit schema version detection for v7.5 and v7.6

Changes in v7.2:
- NEW: Confidentiality banner at top of report ("This report is confidential...")
- UPDATED: Disclaimer text replaced with full legal disclaimer (hardcoded)
- Both statements are hardcoded in Streamlit (not JSON-driven) as fixed legal language

Changes in v7.1:
- FIX: CCC Days (PRIMARY DRIVER) row in Working Capital section now correctly reads from
  values_standard/values_period_adjusted as fallback when "values" field is empty
- FIX: Facility Guidance section now also reads from suitability_vs_financial_condition
  fields beyond just general_guidance for broader coverage
- BACKWARD COMPATIBLE: All v6.x and v7.x JSON continues to render correctly

Changes in v7.0:
- FULL COMPATIBILITY with JSON Schema v7.2 and Framework v7.2
- NEW: Schema version detection for v7.1 and v7.2
- NEW: Dual efficiency ratio display (standard x365 + period-adjusted)
- NEW: Period-adjusted values shown for YTD debtor/creditor/inventory days and CCC
- NEW: WCR dual values support (values_standard + values_period_adjusted)
- NEW: Period days indicator in efficiency ratios table
- NEW: detect_schema_version updated with v7.1/v7.2 explicit and heuristic detection
- NEW: All schema-version-gated function lists updated to include v7.1/v7.2
- FIX: Period labels no longer show "- XXX days" suffix (clean labels only)
- FIX: Efficiency ratios now read from backward-compatible "values" field
- BACKWARD COMPATIBLE: All v6.19 and earlier JSON continues to render correctly

Changes in v6.7:
- FULL COMPATIBILITY with JSON Schema v6.18 and Custom Instructions v6.18
- NEW: Schema version detection for v6.17 and v6.18
- NEW: Output Optimization support - gracefully handles REMOVED per-period OWC/WCR interpretations
- NEW: OWC vs CCC Conflict Resolution display - CCC shown as PRIMARY driver, OWC as SUPPORTING
- NEW: WC Assessment shows CCC/OWC conflict indicator when signals disagree
- NEW: WC section no longer requires calculation_details for WCR (removed in v6.18)
- NEW: Validation checks for v6.18 specific rules (no interpretation blocks, CCC primary)
- FIX: WC table gracefully renders when calculation_details/interpretation blocks are absent
- FIX: WC section subtitle updated - no longer references "Net WC" as primary metric
- ENHANCED: WC Assessment box shows "PRIMARY" / "SUPPORTING" labels for CCC/OWC
- ENHANCED: Facility Suitability WC Assessment highlights CCC-driven decision
- BACKWARD COMPATIBLE: Still renders OWC/WCR interpretations if present (v6.16 and earlier JSON)

Changes in v6.6:

Changes in v6.5:
- FULL COMPATIBILITY with JSON Schema v6.12 and Custom Instructions v6.13
- NEW: RATIO NAMING UPDATE - supports both old (debt_to_equity) and new (liabilities_to_equity) names
- NEW: FORMULA DISPLAY - All ratios now show formula field in a sub-row for transparency
- NEW: BENCHMARK DISPLAY - Key ratios show benchmark thresholds (e.g., Current Ratio >= 1.25x)
- NEW: detect_schema_version updated for v6.12 detection
- UPDATED: RATIO_DISPLAY_NAMES includes new liabilities_to_equity and liabilities_to_assets
- UPDATED: Leverage ratios list supports both old and new naming conventions
- ENHANCED: Ratios section shows formula below each ratio name
- ENHANCED: Benchmark badges highlight pass/fail status

Changes in v6.4:
- FULL COMPATIBILITY with JSON Schema v6.11 and Custom Instructions v6.12
- NEW: Audit Opinion Section - displays auditor name, opinion type, date signed, going concern notes
- NEW: Period labels now display source type suffix verbatim (Audited/MA/Unaudited)
- NEW: "includes" field tooltip on consolidated expense items
- NEW: Audit Opinion severity badges in header (Qualified/Adverse = warning/danger)
- NEW: detect_schema_version updated for v6.11 detection
- NEW: Navigation bar includes Audit Opinion link
- NEW: Validation checks for audit_opinion section
- ENHANCED: Header shows auditor info for audited periods
- ENHANCED: Notes section shows full audit opinion details
- ENHANCED: Summary section handles audit opinion flags correctly

Changes in v6.3:
- FULLY DYNAMIC OPERATING EXPENSES: Now iterates through ALL keys dynamically (like Balance Sheet)
- Auto-detects nested category structure (any category with line_items/total)
- Handles ANY expense category name: administrative_expenses, other_expenses, selling_expenses, 
  distribution_expenses, or ANY future category - no hardcoded category names
- Calculates TOTAL OPERATING EXPENSES by summing all category totals dynamically
- Three rendering modes supported:
  1. NESTED CATEGORIES: Each with line_items and total (v6.x schema)
  2. FLAT STRUCTURE: Direct line_items under operating_expenses
  3. LEGACY FALLBACK: Known category names for backward compatibility
- Aligned with v6.10 "ADAPTIVE OUTPUT" principle - renders whatever JSON provides
- Prevents "TOTAL OPERATING EXPENSES = 0" issue across all schema variations

Changes in v6.2:
- FULLY DYNAMIC BALANCE SHEET: ALL sections now iterate through JSON keys dynamically
- NON-CURRENT ASSETS: Now renders ALL items (PPE + intangibles + investments + others)
  Previously only rendered PPE, missing items like intangible_assets, investment_in_subsidiaries
- EQUITY: Now iterates through ALL equity items dynamically (not just 3 hardcoded keys)
  Previously hardcoded: share_capital, retained_earnings, other_reserves
- This fully aligns with Custom Instructions v6.10 "ADAPTIVE OUTPUT" principle
- Any balance sheet structure from JSON will now render correctly

Changes in v6.1:
- FIXED: Current Assets now renders ALL items dynamically (same as NCL/CL)
- Previously only 8 hardcoded keys were rendered: trade_receivables, other_receivables, 
  amount_due_from_directors, amount_due_from_related_companies, inventory, tax_prepayment, 
  fixed_deposits, cash_and_bank
- Now iterates through ALL keys in current_assets dict, supporting any JSON structure

Changes in v6.0:
- Updated to support Custom Instructions v6.9 and JSON Schema v6.5
- Added dscr_analysis to required sections
- Updated TNW section to read v6.5 calculation structure (with components fallback)
- Fixed funding mismatch to read both 'non_current_assets' and 'non_current_assets_nca'
- Updated period label handling to be fully adaptive (reads from periods_analyzed)
- Added facility classification display (Term vs Revolving) in DSCR section
- Enhanced DSCR section with facility classification notes
- Updated schema version detection for v6.4, v6.5, v6.9
- Added terminology definitions display in funding mismatch
- Updated Working Capital to show Revenue-based calculation note (v6.8 change)
- Fixed TNW to show both Original TNW and Adjusted TNW per v6.8

Changes in v5.0:
- Added Working Capital Analysis section (3-level analysis)
- Added Funding Mismatch Analysis section (3-layer analysis)
- Added Funding Profile section (facility suitability)
- Added DSCR Analysis detailed breakdown section
- Added Report Footer with mandatory disclaimer and copyright (v6.5)
- Enhanced Analysis Summary with key_observations and facility_suitability_summary
- Updated navigation bar with new sections
- Added severity badges for areas of concern
- Updated validation for v6.3 required sections

Changes in v4.3:
- Added Dual Theme Support (Light Mode & Dark Mode toggle)
- Theme persists via localStorage (browser remembers user preference)
- Updated CSS with comprehensive light/dark theme variables

Usage:
    streamlit run streamlit_financial_report_v7_7.py
"""

import streamlit as st
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Tuple

def convert_html_to_pdf(html_content: str) -> bytes:
    """
    Convert HTML report to PDF using weasyprint.
    Forces light theme, removes interactive elements, expands all sections.
    Uses @font-face unicode-range for emoji rendering without affecting digit spacing.
    """
    import weasyprint
    
    pdf_html = html_content
    
    # 1. Force light theme
    pdf_html = pdf_html.replace('data-theme="dark"', 'data-theme="light"')
    if 'data-theme' not in pdf_html:
        pdf_html = pdf_html.replace('<html', '<html data-theme="light"', 1)
    
    # 2. Remove theme toggle button
    pdf_html = re.sub(r'<button[^>]*class="theme-toggle"[^>]*>.*?</button>', '', pdf_html, flags=re.DOTALL)
    
    # 3. Remove navigation bar entirely
    pdf_html = re.sub(r'<div class="nav-bar">.*?</div>\s*</div>\s*</div>', '', pdf_html, flags=re.DOTALL)
    
    # 4. Force all collapsible sections to be visible
    pdf_html = pdf_html.replace('class="section-content"', 'class="section-content show"')
    
    # 5. Remove all JavaScript
    pdf_html = re.sub(r'<script>[\s\S]*?</script>', '', pdf_html)
    
    # 6. Add print-optimized CSS
    print_css = """
<style>
@page { size: A4; margin: 12mm 10mm 14mm 10mm; }

/* Force light theme variables */
:root, [data-theme="light"], [data-theme="dark"] {
    --bg: #f8fafc !important; --bg-alt: #ffffff !important; --bg-card: #ffffff !important;
    --text-main: #1e293b !important; --text-secondary: #475569 !important;
    --text-soft: #64748b !important; --text-muted: #94a3b8 !important;
    --border-card: rgba(226,232,240,1) !important; --border-subtle: rgba(203,213,225,0.6) !important;
    --row-even: #ffffff !important; --row-odd: #f8fafc !important;
    --section-bg: #ffffff !important; --card-bg: #ffffff !important;
    --header-bg: linear-gradient(135deg,#ffffff,#f8fafc) !important;
    --body-bg: #ffffff !important;
    --table-header-bg: linear-gradient(180deg,#f8fafc 0%,#f1f5f9 100%) !important;
    --accent-text: #047857 !important; --danger-text: #b91c1c !important;
    --warn-text: #b45309 !important; --info-text: #1d4ed8 !important;
    --purple-text: #6d28d9 !important;
    --accent-soft: rgba(5,150,105,0.08) !important; --danger-soft: rgba(220,38,38,0.06) !important;
    --warn-soft: rgba(217,119,6,0.06) !important; --info-soft: rgba(37,99,235,0.06) !important;
    --purple-soft: rgba(124,58,237,0.06) !important;
    --accent-border: rgba(5,150,105,0.3) !important; --danger-border: rgba(220,38,38,0.25) !important;
    --warn-border: rgba(217,119,6,0.3) !important; --info-border: rgba(37,99,235,0.25) !important;
    --section-header-bg: rgba(37,99,235,0.06) !important;
    --total-row-bg: rgba(5,150,105,0.05) !important;
    --grand-total-bg: rgba(37,99,235,0.06) !important;
    --gross-profit-bg: rgba(5,150,105,0.06) !important;
    --expense-total-bg: rgba(220,38,38,0.04) !important;
    --ebitda-bg: rgba(124,58,237,0.05) !important;
    --subsection-bg: rgba(241,245,249,1) !important;
    --highlight: #b45309 !important;
}

body {
    background: #ffffff !important;
    padding: 0 !important;
    margin: 0 !important;
    font-family: system-ui, -apple-system, 'Symbola', sans-serif !important;
}

.page { max-width: 100% !important; margin: 0 !important; padding: 0 !important; }
.theme-toggle, .nav-bar, .toggle-arrow, .nav-controls, .nav-btn { display: none !important; }
.section-content { display: block !important; }
.section-toggle { cursor: default !important; pointer-events: none !important; border-radius: 16px 16px 0 0 !important; border-bottom: none !important; }

/* Tables - force all 3 year columns visible on A4 */
table { width: 100% !important; font-size: 10px !important; }
thead th { font-size: 9px !important; padding: 8px 6px !important; white-space: normal !important; word-wrap: break-word !important; }
tbody td { font-size: 10px !important; padding: 6px !important; white-space: normal !important; word-wrap: break-word !important; }
tbody td.number { white-space: nowrap !important; font-size: 10px !important; }
.table-card { overflow: visible !important; padding: 10px !important; }
.table-wrapper { overflow: visible !important; }

/* Page break controls */
tr { page-break-inside: avoid !important; }
h1, h2, h3, h4 { page-break-after: avoid !important; }
.header-card, .obs-box, .reco-box, .facility-box, .key-obs-item, .audit-opinion-item { page-break-inside: avoid !important; }
.note-box.warning, .note-box.info, .report-footer, footer { page-break-inside: avoid !important; }

/* Grids for A4 */
.key-obs-grid { grid-template-columns: repeat(2, 1fr) !important; gap: 10px !important; }
.obs-grid { grid-template-columns: repeat(2, 1fr) !important; }
.audit-opinion-grid { grid-template-columns: repeat(2, 1fr) !important; }
</style>
"""
    pdf_html = pdf_html.replace('</head>', print_css + '\n</head>')
    
    # Generate PDF
    pdf_bytes = weasyprint.HTML(string=pdf_html).write_pdf()
    return pdf_bytes

st.set_page_config(
    page_title="Kredit Lab Financial Report Generator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# v6.5 required sections (full schema) - Updated to include dscr_analysis
REQUIRED_SECTIONS_V6_5 = [
    "company_info", 
    "statement_of_comprehensive_income", 
    "statement_of_financial_position", 
    "financial_ratios",
    "working_capital_analysis",
    "funding_mismatch_analysis",
    "funding_profile",
    "tnw_analysis",
    "dscr_analysis",  # Added in v6.0
    "integrity_check",
    "analysis_summary",
    "report_footer"
]

# Legacy v6.3 support (without dscr_analysis as required)
REQUIRED_SECTIONS_V6_3 = [
    "company_info", 
    "statement_of_comprehensive_income", 
    "statement_of_financial_position", 
    "financial_ratios",
    "working_capital_analysis",
    "funding_mismatch_analysis",
    "funding_profile",
    "tnw_analysis",
    "integrity_check",
    "analysis_summary",
    "report_footer"
]

# v6.0 uses different section names - support both old and new
REQUIRED_SECTIONS_V6 = [
    "company_info", "statement_of_comprehensive_income", 
    "statement_of_financial_position", "financial_ratios"
]

REQUIRED_SECTIONS_V2 = [
    "metadata", "company", "periods", "income_statement", 
    "balance_sheet", "financial_ratios", "tnw_analysis",
    "integrity_check", "analysis_summary"
]

RATIO_DISPLAY_NAMES = {
    "gross_profit_margin": "Gross Profit Margin",
    "operating_profit_margin": "Operating Profit Margin",
    "pbt_margin": "PBT Margin",
    "net_profit_margin": "Net Profit Margin",
    "ebitda_margin": "EBITDA Margin",
    "roa": "ROA", "roe": "ROE",
    "current_ratio": "Current Ratio",
    "quick_ratio": "Quick Ratio",
    "cash_ratio": "Cash Ratio",
    # v6.12 NEW NAMES (preferred)
    "liabilities_to_equity": "Liabilities-to-Equity",
    "liabilities_to_assets": "Liabilities-to-Assets",
    # v6.11 and earlier (backward compatibility)
    "debt_to_equity": "Debt-to-Equity",
    "debt_to_assets": "Debt-to-Assets",
    "equity_ratio": "Equity Ratio",
    "gearing_ratio": "Gearing Ratio",
    "interest_coverage": "Interest Coverage",
    "dscr": "DSCR",
    "asset_turnover": "Asset Turnover",
    "receivables_turnover": "Receivables Turnover",
    "debtor_days": "Debtor Days",
    "creditor_days": "Creditor Days",
    "inventory_days": "Inventory Turnover Days",
    "inventory_turnover": "Inventory Turnover",
    "cash_conversion_cycle": "Cash Conversion Cycle",
    "working_capital": "Working Capital",
    "working_capital_ratio": "Working Capital Ratio"
}

def detect_schema_version(data: Dict) -> str:
    """Detect JSON schema version - supports v7.9, v7.8, v7.7, v7.6, v7.2, v7.1, v6.19, v6.18, v6.17, v6.16, v6.15, v6.14, v6.13, v6.12, v6.11, v6.5, v6.4, v6.3, v6.0, v2.1"""
    schema_info = data.get("_schema_info", {})
    version = schema_info.get("version", "")
    
    # Explicit version detection
    if version.startswith("v7.9"):
        return "v7.7"  # v7.9 structurally same as v7.7 for rendering
    if version.startswith("v7.8"):
        return "v7.7"  # v7.8 structurally same as v7.7 for rendering
    if version.startswith("v7.7"):
        return "v7.7"
    if version.startswith("v7.6"):
        return "v7.7"  # v7.6 structurally same as v7.7 for rendering
    if version.startswith("v7.5"):
        return "v7.7"  # v7.5 structurally same as v7.7 for rendering
    if version.startswith("v7.3") or version.startswith("v7.4"):
        return "v7.2"  # v7.3/v7.4 structurally same as v7.2 for rendering
    if version.startswith("v7.2"):
        return "v7.2"
    if version.startswith("v7.1"):
        return "v7.1"
    if version.startswith("v6.19"):
        return "v6.19"
    if version.startswith("v6.18"):
        return "v6.18"
    if version.startswith("v6.17"):
        return "v6.17"
    if version.startswith("v6.16"):
        return "v6.16"
    if version.startswith("v6.15"):
        return "v6.15"
    if version.startswith("v6.14"):
        return "v6.14"
    if version.startswith("v6.13"):
        return "v6.13"
    if version.startswith("v6.12"):
        return "v6.12"
    if version.startswith("v6.11") or version.startswith("v6.10") or version.startswith("v6.9"):
        return "v6.11"
    if version.startswith("v6.5") or version.startswith("v6.4"):
        return "v6.5"
    if version.startswith("v6.3"):
        return "v6.3"
    
    # Heuristic detection based on sections present
    if "company_info" in data and "statement_of_comprehensive_income" in data:
        company_info = data.get("company_info", {})
        
        # Check for v7.x specific: efficiency_ratios with values_standard/values_period_adjusted
        eff_ratios = data.get("financial_ratios", {}).get("efficiency_ratios", {})
        debtor_days = eff_ratios.get("debtor_days", {})
        if "values_standard" in debtor_days and "values_period_adjusted" in debtor_days:
            return "v7.2"  # Best guess for v7.x without explicit version
        
        # Check for v6.18 specific: working_capital_analysis WITHOUT interpretation blocks
        wca = data.get("working_capital_analysis", {})
        owc = wca.get("operating_working_capital", {})
        wcr = wca.get("working_capital_requirement", {})
        wc_assess = wca.get("working_capital_assessment", {})
        
        # v6.18 heuristic: has owc_status AND ccc_status in wc_assessment AND no interpretation in OWC
        if (wc_assess.get("ccc_status") and wc_assess.get("owc_status") 
            and "interpretation" not in owc and "calculation_details" not in wcr):
            # Could be v6.17 or v6.18 - check for period labels with month
            periods_analyzed = company_info.get("periods_analyzed", {})
            has_month_labels = False
            for pk, desc in periods_analyzed.items():
                if isinstance(desc, str):
                    import re
                    if re.search(r'FY\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}', desc):
                        has_month_labels = True
                        break
            if has_month_labels:
                return "v6.19"  # Best guess for v6.18+ without explicit version
        
        # Check for v6.15+ specific: dscr_analysis with assessment field
        dscr = data.get("dscr_analysis", {})
        if isinstance(dscr, dict) and "assessment" in dscr:
            # Check for v6.16+ specific: period labels with month in them
            periods_analyzed = company_info.get("periods_analyzed", {})
            for pk, desc in periods_analyzed.items():
                if isinstance(desc, str):
                    import re
                    if re.search(r'FY\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}', desc):
                        return "v6.16"
            return "v6.15"
        
        # Check for v6.14 specific: pbt_margin in profitability_ratios
        ratios = data.get("financial_ratios", {})
        prof_ratios = ratios.get("profitability_ratios", {})
        if "pbt_margin" in prof_ratios:
            return "v6.14"
        
        # Check for v6.12 specific: liabilities_to_equity in financial_ratios
        leverage = ratios.get("leverage_ratios", {})
        if "liabilities_to_equity" in leverage or "liabilities_to_assets" in leverage:
            return "v6.12"
        
        # Check for v6.12 specific: formula field in ratios
        for cat_key, cat_data in ratios.items():
            if isinstance(cat_data, dict):
                for ratio_key, ratio_data in cat_data.items():
                    if isinstance(ratio_data, dict) and "formula" in ratio_data:
                        return "v6.12"
        
        # Check for v6.11 specific: audit_opinion in company_info
        if "audit_opinion" in company_info:
            return "v6.11"
        # Check for v6.11 style periods_analyzed with source type suffix
        periods_analyzed = company_info.get("periods_analyzed", {})
        for pk, desc in periods_analyzed.items():
            if isinstance(desc, str) and ("(Audited" in desc or "(MA)" in desc or "(Unaudited" in desc):
                return "v6.11"
        # Check for v6.5 specific: dscr_analysis with facility_classification or calculation
        if "facility_classification" in dscr or "calculation" in dscr:
            return "v6.5"
        # Check for v6.3/v6.4 specific sections
        if "working_capital_analysis" in data and "funding_mismatch_analysis" in data:
            return "v6.3"
        return "v6.0"
    elif "company" in data and "income_statement" in data:
        return "v2.1"
    else:
        return "unknown"

def get_period_keys(data: Dict) -> List[str]:
    """Extract period keys from data - works with v6.12, v6.11, v6.5, v6.3, v6.0 and v2.1"""
    schema = detect_schema_version(data)
    
    if schema in ["v6.0", "v6.3", "v6.5", "v6.11", "v6.12", "v6.13", "v6.14", "v6.15", "v6.16", "v6.17", "v6.18", "v6.19", "v7.1", "v7.2", "v7.7"]:
        # v6.x: periods are in company_info.periods_analyzed or inferred from values
        company_info = data.get("company_info", {})
        periods_analyzed = company_info.get("periods_analyzed", {})
        if periods_analyzed:
            return list(periods_analyzed.keys())
        # Fallback: extract from first available values dict
        pnl = data.get("statement_of_comprehensive_income", {})
        revenue = pnl.get("revenue", {})
        total = revenue.get("total", {})
        values = total.get("values", {})
        return list(values.keys())
    else:
        # v2.1: periods object
        periods_obj = data.get("periods", {})
        return [k for k in periods_obj.keys() if isinstance(periods_obj[k], dict) and "period_label" in periods_obj[k]]

def get_period_label(data: Dict, pk: str) -> str:
    """Get display label for period - ADAPTIVE to source data (v6.11/v6.12 principle)"""
    schema = detect_schema_version(data)
    
    if schema in ["v6.0", "v6.3", "v6.5", "v6.11", "v6.12", "v6.13", "v6.14", "v6.15", "v6.16", "v6.17", "v6.18", "v6.19", "v7.1", "v7.2", "v7.7"]:
        # First try to get from periods_analyzed description
        company_info = data.get("company_info", {})
        periods_analyzed = company_info.get("periods_analyzed", {})
        period_desc = periods_analyzed.get(pk, "")
        
        # v6.11: If description has source type suffix, use it directly
        if period_desc:
            # v7.2: Strip any "- XXX days" suffix from period labels
            import re
            period_desc = re.sub(r'\s*-\s*\d+\s*days?\s*$', '', period_desc).strip()
            
            # Check for v6.11 style with suffix like "FY2024 (Audited)" or "YTD Jun 2025 (MA)"
            # Also handle qualified suffixes like "(Audited - Restated)"
            if ("(Audited" in period_desc or "(MA)" in period_desc or "(Unaudited" in period_desc):
                return period_desc
            
            import re
            # Check for year ended pattern
            if "Year ended" in period_desc or "FY" in period_desc:
                year_match = re.search(r'20\d{2}', period_desc)
                if year_match:
                    year = year_match.group()
                    if "Audited" in period_desc:
                        return f"FY{year}"
                    elif "Management" in period_desc:
                        return f"FY{year} (MA)"
                    return f"FY{year}"
            # Check for months ended pattern (YTD)
            if "months ended" in period_desc:
                match = re.search(r'(\d+)\s+months\s+ended\s+(\d+\s+\w+\s+\d+)', period_desc, re.IGNORECASE)
                if match:
                    date_str = match.group(2)
                    month_match = re.search(r'(\w+)\s+(\d{4})', date_str)
                    if month_match:
                        month = month_match.group(1)[:3]
                        year = month_match.group(2)
                        return f"YTD {month} {year}"
        
        # Fallback: convert period key to readable format
        pk_lower = pk.lower()
        if pk_lower.startswith("fy"):
            year = pk_lower.replace("fy", "")
            return f"FY{year}"
        elif pk_lower.startswith("ytd_"):
            # ytd_aug2025 -> YTD Aug 2025
            import re
            rest = pk_lower[4:]  # Remove "ytd_"
            match = re.match(r'([a-z]+)(\d+)', rest)
            if match:
                month = match.group(1).capitalize()
                year = match.group(2)
                return f"YTD {month} {year}"
            return pk.upper().replace("_", " ")
        else:
            return pk.upper().replace("_", " ")
    else:
        return data.get("periods", {}).get(pk, {}).get("period_label", pk)

def get_period_type(data: Dict, pk: str) -> str:
    """Get period type (audited/management) - v6.11 compatible"""
    schema = detect_schema_version(data)
    
    if schema in ["v6.0", "v6.3", "v6.5", "v6.11", "v6.12", "v6.13", "v6.14", "v6.15", "v6.16", "v6.17", "v6.18", "v6.19", "v7.1", "v7.2", "v7.7"]:
        company_info = data.get("company_info", {})
        periods_analyzed = company_info.get("periods_analyzed", {})
        period_desc = periods_analyzed.get(pk, "")
        
        # v6.11: Check for suffix format (including qualified suffixes like "Audited - Restated")
        if "(Audited" in period_desc:
            return "audited"
        elif "(MA)" in period_desc or "Management" in period_desc:
            return "management"
        elif "(Unaudited" in period_desc:
            return "unaudited"
        elif "Audited" in period_desc:
            return "audited"
        return "unknown"
    else:
        return data.get("periods", {}).get(pk, {}).get("type", "unknown")

def get_income_statement(data: Dict) -> Dict:
    """Get income statement data - works with all schemas"""
    schema = detect_schema_version(data)
    if schema in ["v6.0", "v6.3", "v6.5", "v6.11", "v6.12", "v6.13", "v6.14", "v6.15", "v6.16", "v6.17", "v6.18", "v6.19", "v7.1", "v7.2", "v7.7"]:
        return data.get("statement_of_comprehensive_income", {})
    else:
        return data.get("income_statement", {})

def get_balance_sheet(data: Dict) -> Dict:
    """Get balance sheet data - works with all schemas"""
    schema = detect_schema_version(data)
    if schema in ["v6.0", "v6.3", "v6.5", "v6.11", "v6.12", "v6.13", "v6.14", "v6.15", "v6.16", "v6.17", "v6.18", "v6.19", "v7.1", "v7.2", "v7.7"]:
        return data.get("statement_of_financial_position", {})
    else:
        return data.get("balance_sheet", {})

def get_company_info(data: Dict) -> Dict:
    """Get company info - works with all schemas"""
    schema = detect_schema_version(data)
    if schema in ["v6.0", "v6.3", "v6.5", "v6.11", "v6.12", "v6.13", "v6.14", "v6.15", "v6.16", "v6.17", "v6.18", "v6.19", "v7.1", "v7.2", "v7.7"]:
        return data.get("company_info", {})
    else:
        return data.get("company", {})

def format_number(value: Any, decimals: int = 0) -> str:
    if value is None: return "-"
    try:
        num = float(value)
        if num == 0: return "0"
        formatted = f"{abs(num):,.{decimals}f}"
        return f"({formatted})" if num < 0 else formatted
    except: return str(value)

def format_number_or_dash(value: Any, decimals: int = 0) -> str:
    """Like format_number but returns dash for None - used for line items where missing period = not applicable"""
    if value is None: return "-"
    return format_number(value, decimals)

def format_percentage(value: Any, decimals: int = 2) -> str:
    if value is None: return "-"
    try: return f"{float(value):.{decimals}f}%"
    except: return str(value)

def snake_to_title(text: str) -> str:
    return ' '.join(word.capitalize() for word in text.split('_'))

def get_display_name(item: Dict, key: str) -> str:
    if isinstance(item, dict):
        return item.get("display_name", item.get("_display_name", snake_to_title(key)))
    return snake_to_title(key)

def get_ratio_display_name(rk: str) -> str:
    return RATIO_DISPLAY_NAMES.get(rk, snake_to_title(rk))

def get_value_from_item(item: Dict, pk: str, default=0):
    """Get value from item - handles both nested 'values' and direct 'amount' structures.
    v7.2: Falls back to values_standard if values is missing (dual efficiency ratios).
    v6.16: For line items, missing period keys return default (callers should pass None for lump sum awareness)."""
    if not isinstance(item, dict): return default
    
    # Try v6.0 style: direct values dict
    values = item.get("values", {})
    if isinstance(values, dict) and values:
        if pk in values:
            return values.get(pk, default)
        else:
            return default
    
    # v7.2 fallback: try values_standard if values is missing/empty
    values_std = item.get("values_standard", {})
    if isinstance(values_std, dict) and values_std:
        if pk in values_std:
            return values_std.get(pk, default)
        else:
            return default
    
    # Try v2.1 style: nested amount/margin_pct
    amount = item.get("amount", {})
    if isinstance(amount, dict):
        amt_values = amount.get("values", {})
        if pk in amt_values:
            return amt_values.get(pk, default)
    
    return default

def get_margin_from_item(item: Dict, pk: str, default=0):
    """Get margin percentage from item - handles both structures"""
    if not isinstance(item, dict): return default
    
    # v2.1 style: nested margin_pct
    margin_pct = item.get("margin_pct", {})
    if isinstance(margin_pct, dict):
        values = margin_pct.get("values", {})
        if pk in values:
            return values.get(pk, default)
    
    # v6.0: margin is a separate key, handled elsewhere
    return default

def get_currency_unit(data: Dict) -> str:
    """
    Get currency unit from JSON _schema_info.
    
    Claude (AI) determines the correct currency unit during analysis by reading
    the source financial statements and sets it in the JSON output.
    
    Streamlit simply reads and displays what Claude provides.
    
    Returns:
    - "RM" for SME companies (actual Ringgit)
    - "RM'000" for large/listed companies (thousands)
    """
    schema_info = data.get("_schema_info", {})
    return schema_info.get("currency_unit", "RM")  # Default to RM if not specified

def validate_json_structure(data: Dict) -> Tuple[bool, List[str], List[str]]:
    errors, warnings = [], []
    schema = detect_schema_version(data)
    
    if schema in ["v6.12", "v6.13", "v6.14", "v6.15", "v6.16", "v6.17", "v6.18", "v6.19", "v7.1", "v7.2", "v7.7"]:
        required = REQUIRED_SECTIONS_V6_5  # v6.12 uses same base requirements as v6.5/v6.11
    elif schema == "v6.11":
        required = REQUIRED_SECTIONS_V6_5  # v6.11 uses same base requirements as v6.5
    elif schema == "v6.5":
        required = REQUIRED_SECTIONS_V6_5
    elif schema == "v6.3":
        required = REQUIRED_SECTIONS_V6_3
    elif schema == "v6.0":
        required = REQUIRED_SECTIONS_V6
    elif schema == "v2.1":
        required = REQUIRED_SECTIONS_V2
    else:
        errors.append("Unknown schema version - cannot validate structure")
        return False, errors, warnings
    
    for section in required:
        if section not in data:
            if schema in ["v6.12", "v6.13", "v6.14", "v6.15", "v6.16", "v6.17", "v6.18", "v6.19", "v7.1", "v7.2", "v7.7", "v6.11", "v6.5", "v6.3"]:
                errors.append(f"Missing required section: '{section}'")
            else:
                warnings.append(f"Missing section (optional in {schema}): '{section}'")
    
    company = get_company_info(data)
    if not (company.get("legal_name") or company.get("name")):
        warnings.append("Missing company name")
    
    if not get_period_keys(data):
        errors.append("No valid periods found")
    
    # v6.5/v6.11/v6.12 specific: Check report_footer
    if "report_footer" not in data:
        warnings.append("Missing report_footer section (required in v6.5+)")
    
    # v6.11/v6.12 specific: Check audit_opinion
    if schema in ["v6.11", "v6.12", "v6.13", "v6.14", "v6.15", "v6.16", "v6.17", "v6.18", "v6.19", "v7.1", "v7.2", "v7.7"]:
        audit_opinion = company.get("audit_opinion", {})
        if not audit_opinion:
            warnings.append("Missing audit_opinion in company_info (recommended in v6.11+)")
        else:
            # Check for non-clean opinions that should be flagged
            for pk, opinion_data in audit_opinion.items():
                if isinstance(opinion_data, dict):
                    opinion_type = opinion_data.get("opinion_type", "")
                    if opinion_type in ["Qualified", "Adverse", "Disclaimer"]:
                        # Check if flagged in areas_of_concern
                        summary = data.get("analysis_summary", {})
                        concerns = summary.get("areas_of_concern", [])
                        flagged = any(
                            opinion_type.lower() in str(c).lower() or "audit" in str(c).lower()
                            for c in concerns
                        )
                        if not flagged:
                            warnings.append(f"{pk}: {opinion_type} opinion should be flagged in areas_of_concern")
    
    # v6.11/v6.12 specific: Check periods_analyzed has source type suffix
    periods_analyzed = company.get("periods_analyzed", {})
    for pk, desc in periods_analyzed.items():
        if isinstance(desc, str):
            if not any(suffix in desc for suffix in ["(Audited", "(MA)", "(Unaudited"]):
                warnings.append(f"Period '{pk}' missing source type suffix (Audited/MA/Unaudited)")
    
    # v7.7/v7.8 specific: Check prior_year_adjustments if any period is labelled Restated
    if schema == "v7.7":
        has_restated_period = any(
            isinstance(desc, str) and "Restated" in desc
            for desc in periods_analyzed.values()
        )
        if has_restated_period:
            pya = company.get("prior_year_adjustments", {})
            if not pya or not pya.get("has_restatement"):
                warnings.append("v7.7: Period labelled 'Restated' but prior_year_adjustments.has_restatement is false or missing")
    
    # v6.15/v6.16 specific validation
    if schema in ["v6.15", "v6.16", "v6.17", "v6.18", "v6.19", "v7.1", "v7.2", "v7.7"]:
        # Check DSCR assessment
        dscr = data.get("dscr_analysis", {})
        if dscr and not dscr.get("assessment"):
            warnings.append("dscr_analysis.assessment is MANDATORY in v6.15+ (missing)")
        
        # Check risk flags when sustainability != Sustainable
        fm = data.get("funding_mismatch_analysis", {})
        fsa = fm.get("funding_structure_assessment", {})
        rating = fsa.get("overall_sustainability_rating", "")
        if rating and rating != "Sustainable":
            flags = fsa.get("risk_flags", [])
            if not flags:
                warnings.append(f"risk_flags empty but sustainability rating is '{rating}' (should be populated)")
        
        # Check all 7 profitability ratios
        ratios = data.get("financial_ratios", {})
        prof = ratios.get("profitability_ratios", {})
        required_prof = ["gross_profit_margin", "operating_profit_margin", "pbt_margin", "net_profit_margin", "ebitda_margin", "roa", "roe"]
        for r in required_prof:
            if r not in prof:
                warnings.append(f"Missing mandatory profitability ratio: {r}")
        
        # Check existing_facility_concerns when appropriate = false
        summary = data.get("analysis_summary", {})
        fss = summary.get("facility_suitability_summary", {})
        if fss.get("existing_facilities_appropriate") == False:
            if not fss.get("existing_facility_concerns"):
                warnings.append("existing_facility_concerns MANDATORY when existing_facilities_appropriate = false")
    
    # v6.16+ specific: Check period labels include month
    if schema in ["v6.16", "v6.17", "v6.18", "v6.19", "v7.1", "v7.2", "v7.7"]:
        import re
        for pk, desc in periods_analyzed.items():
            if isinstance(desc, str) and ("(Audited" in desc or "(MA)" in desc):
                if not re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', desc):
                    warnings.append(f"Period '{pk}' label should include month (v6.16+ rule): '{desc}'")
    
    # v6.18 specific: Check for removed fields (should NOT be present)
    if schema in ["v6.17", "v6.18", "v6.19", "v7.1", "v7.2", "v7.7"]:
        wca = data.get("working_capital_analysis", {})
        owc_data = wca.get("operating_working_capital", {})
        wcr_data = wca.get("working_capital_requirement", {})
        
        if "interpretation" in owc_data:
            warnings.append("v6.18: operating_working_capital.interpretation should be REMOVED (per-period narratives deprecated)")
        if "interpretation" in wcr_data:
            warnings.append("v6.18: working_capital_requirement.interpretation should be REMOVED (per-period narratives deprecated)")
        if "calculation_details" in wcr_data:
            warnings.append("v6.18: working_capital_requirement.calculation_details should be REMOVED (redundant breakdown deprecated)")
        
        # Check WC assessment has ccc_status and owc_status
        wc_assess = wca.get("working_capital_assessment", {})
        if wc_assess:
            if not wc_assess.get("ccc_status"):
                warnings.append("v6.18: working_capital_assessment.ccc_status is recommended (CCC is PRIMARY driver)")
            if not wc_assess.get("owc_status"):
                warnings.append("v6.18: working_capital_assessment.owc_status is recommended (OWC is SUPPORTING indicator)")
            if not wc_assess.get("rationale"):
                warnings.append("v6.18: working_capital_assessment.rationale is MANDATORY")
    
    # v7.x specific: Check efficiency ratios have backward-compatible "values" field
    if schema in ["v7.1", "v7.2", "v7.7"]:
        eff_ratios = data.get("financial_ratios", {}).get("efficiency_ratios", {})
        for rk in ["debtor_days", "creditor_days", "inventory_days", "cash_conversion_cycle"]:
            ratio_item = eff_ratios.get(rk, {})
            if ratio_item:
                if "values" not in ratio_item:
                    warnings.append(f"v7.2: efficiency_ratios.{rk} missing 'values' field (backward compatibility)")
                if "values_standard" not in ratio_item:
                    warnings.append(f"v7.2: efficiency_ratios.{rk} missing 'values_standard' field")
                if "values_period_adjusted" not in ratio_item:
                    warnings.append(f"v7.2: efficiency_ratios.{rk} missing 'values_period_adjusted' field")
                if "period_days" not in ratio_item:
                    warnings.append(f"v7.2: efficiency_ratios.{rk} missing 'period_days' field")
        
        # Check WCR values - v7.6+ uses single "values" field only (CCC adj handles period correction)
        # v7.1/v7.2 used dual values_standard/values_period_adjusted (removed in v7.6)
        # v7.8 maps to v7.7 internally — same single "values" field
        wcr_data = data.get("working_capital_analysis", {}).get("working_capital_requirement", {})
        if wcr_data:
            if schema == "v7.7":
                # v7.6/v7.7/v7.8: Only requires "values" field (single WCR per period)
                if "values" not in wcr_data:
                    warnings.append("v7.7: working_capital_requirement missing 'values' field")
            else:
                # v7.1/v7.2: Expects dual values
                if "values_standard" not in wcr_data:
                    warnings.append("v7.2: working_capital_requirement missing 'values_standard' field")
                if "values_period_adjusted" not in wcr_data:
                    warnings.append("v7.2: working_capital_requirement missing 'values_period_adjusted' field")
    
    return len(errors) == 0, errors, warnings

def check_mathematical_integrity(data: Dict) -> List[str]:
    issues = []
    schema = detect_schema_version(data)
    
    if schema == "v6.0":
        # v6.0 has verification section
        verification = data.get("verification", {})
        bs_check = verification.get("balance_sheet_balances", {})
        for pk in get_period_keys(data):
            if pk in bs_check and not bs_check[pk]:
                issues.append(f"{get_period_label(data, pk)}: Balance Sheet does not balance")
    else:
        integrity = data.get("integrity_check", {})
        bs_check = integrity.get("balance_sheet_verification", {})
        for pk in get_period_keys(data):
            pd = bs_check.get(pk, {})
            if pd.get("variance", 0) != 0:
                issues.append(f"{get_period_label(data, pk)}: Balance Sheet variance")
    return issues

def generate_css() -> str:
    """Generate CSS with dual theme support (Light & Dark Mode)"""
    return '''<style>
/* ============================================
   DUAL THEME CSS - Light & Dark Mode Support
   Version 4.3
   ============================================ */

/* Light Theme (Default) */
:root, [data-theme="light"] {
  --bg:#f8fafc;
  --bg-alt:#ffffff;
  --bg-card:#ffffff;
  --border-card:rgba(226,232,240,1);
  --border-subtle:rgba(203,213,225,0.6);
  
  --accent:#059669;
  --accent-soft:rgba(5,150,105,0.08);
  --accent-border:rgba(5,150,105,0.3);
  --accent-text:#047857;
  
  --danger:#dc2626;
  --danger-soft:rgba(220,38,38,0.06);
  --danger-border:rgba(220,38,38,0.25);
  --danger-text:#b91c1c;
  
  --warn:#d97706;
  --warn-soft:rgba(217,119,6,0.06);
  --warn-border:rgba(217,119,6,0.3);
  --warn-text:#b45309;
  
  --info:#2563eb;
  --info-soft:rgba(37,99,235,0.06);
  --info-border:rgba(37,99,235,0.25);
  --info-text:#1d4ed8;
  
  --text-main:#1e293b;
  --text-secondary:#475569;
  --text-soft:#64748b;
  --text-muted:#94a3b8;
  
  --row-even:#ffffff;
  --row-odd:#f8fafc;
  --row-hover:rgba(37,99,235,0.04);
  
  --purple:#7c3aed;
  --purple-soft:rgba(124,58,237,0.06);
  --purple-text:#6d28d9;
  
  --highlight:#b45309;
  
  --shadow-sm:0 1px 2px rgba(0,0,0,0.04);
  --shadow-md:0 4px 6px -1px rgba(0,0,0,0.05);
  --shadow-lg:0 10px 15px -3px rgba(0,0,0,0.06);
  --shadow-soft:0 10px 15px -3px rgba(0,0,0,0.06);
  
  --header-bg:linear-gradient(135deg,#ffffff,#f8fafc);
  --body-bg:linear-gradient(180deg,#f1f5f9 0%,#f8fafc 100%);
  --card-bg:#ffffff;
  --nav-bg:#ffffff;
  --section-bg:#ffffff;
  --table-header-bg:linear-gradient(180deg,#f8fafc 0%,#f1f5f9 100%);
  
  --section-header-bg:linear-gradient(90deg,rgba(37,99,235,0.08) 0%,rgba(37,99,235,0.03) 100%);
  --total-row-bg:linear-gradient(90deg,rgba(5,150,105,0.06) 0%,rgba(5,150,105,0.02) 100%);
  --grand-total-bg:linear-gradient(90deg,rgba(37,99,235,0.08) 0%,rgba(37,99,235,0.03) 100%);
  --gross-profit-bg:linear-gradient(90deg,rgba(5,150,105,0.08) 0%,rgba(5,150,105,0.02) 100%);
  --expense-total-bg:linear-gradient(90deg,rgba(220,38,38,0.05) 0%,rgba(220,38,38,0.02) 100%);
  --ebitda-bg:linear-gradient(90deg,rgba(124,58,237,0.06) 0%,rgba(124,58,237,0.02) 100%);
  --subsection-bg:rgba(241,245,249,1);
  
  --radius-lg:20px;
  --radius-md:16px;
  --radius-sm:10px;
  --radius-pill:999px;
}

/* Dark Theme */
[data-theme="dark"] {
  --bg:#0f172a;
  --bg-alt:#020617;
  --bg-card:rgba(15,23,42,0.96);
  --border-card:rgba(30,64,175,0.75);
  --border-subtle:rgba(55,65,81,0.7);
  
  --accent:#22c55e;
  --accent-soft:rgba(34,197,94,0.15);
  --accent-border:rgba(34,197,94,0.5);
  --accent-text:#86efac;
  
  --danger:#ef4444;
  --danger-soft:rgba(248,113,113,0.18);
  --danger-border:rgba(248,113,113,0.5);
  --danger-text:#fecaca;
  
  --warn:#f59e0b;
  --warn-soft:rgba(245,158,11,0.16);
  --warn-border:rgba(245,158,11,0.7);
  --warn-text:#fed7aa;
  
  --info:#3b82f6;
  --info-soft:rgba(59,130,246,0.15);
  --info-border:rgba(59,130,246,0.5);
  --info-text:#93c5fd;
  
  --text-main:#e5e7eb;
  --text-secondary:#d1d5db;
  --text-soft:#9ca3af;
  --text-muted:#6b7280;
  
  --row-even:rgba(15,23,42,0.9);
  --row-odd:rgba(15,23,42,0.98);
  --row-hover:rgba(30,64,175,0.15);
  
  --purple:#a78bfa;
  --purple-soft:rgba(167,139,250,0.15);
  --purple-text:#c4b5fd;
  
  --highlight:#facc15;
  
  --shadow-sm:0 1px 2px rgba(0,0,0,0.3);
  --shadow-md:0 4px 6px rgba(0,0,0,0.4);
  --shadow-lg:0 18px 45px rgba(15,23,42,0.8);
  --shadow-soft:0 18px 45px rgba(15,23,42,0.8);
  
  --header-bg:radial-gradient(circle at top left,rgba(56,189,248,0.22),rgba(15,23,42,0.98));
  --body-bg:radial-gradient(circle at top left,#1e293b,#020617 40%,#000);
  --card-bg:linear-gradient(135deg,rgba(15,23,42,0.96),rgba(2,6,23,0.97));
  --nav-bg:linear-gradient(135deg,rgba(15,23,42,0.98),rgba(2,6,23,0.99));
  --section-bg:linear-gradient(135deg,rgba(15,23,42,0.96),rgba(2,6,23,0.97));
  --table-header-bg:radial-gradient(circle at top left,#020617,#020617);
  
  --section-header-bg:linear-gradient(90deg,rgba(59,130,246,0.25),rgba(15,23,42,0.95));
  --total-row-bg:linear-gradient(90deg,rgba(34,197,94,0.12),rgba(15,23,42,0.95));
  --grand-total-bg:linear-gradient(90deg,rgba(250,204,21,0.15),rgba(55,65,81,0.95));
  --gross-profit-bg:linear-gradient(90deg,rgba(34,197,94,0.20),rgba(15,23,42,0.95));
  --expense-total-bg:linear-gradient(90deg,rgba(239,68,68,0.12),rgba(15,23,42,0.95));
  --ebitda-bg:linear-gradient(90deg,rgba(168,85,247,0.15),rgba(15,23,42,0.95));
  --subsection-bg:rgba(51,65,85,0.6);
}

/* Base Styles */
*{box-sizing:border-box}
body{margin:0;padding:32px 16px 40px;font-family:system-ui,-apple-system,sans-serif;background:var(--body-bg);color:var(--text-main);line-height:1.6;transition:background 0.3s ease, color 0.3s ease}
.page{max-width:1200px;margin:0 auto}
h1,h2,h3,h4{margin:0;font-weight:600;color:var(--text-main)}

/* Theme Toggle Button */
.theme-toggle{position:fixed;top:20px;right:20px;z-index:1000;padding:10px 18px;border-radius:var(--radius-pill);border:1px solid var(--border-card);background:var(--card-bg);color:var(--text-main);font-size:13px;font-weight:600;cursor:pointer;display:flex;align-items:center;gap:8px;box-shadow:var(--shadow-md);transition:all 0.3s ease}
.theme-toggle:hover{transform:translateY(-2px);box-shadow:var(--shadow-lg)}

/* Header Card */
.header-card{background:var(--header-bg);border-radius:24px;padding:24px 28px 20px;border:1px solid var(--border-card);box-shadow:var(--shadow-soft);margin-bottom:24px}
.header-top{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;margin-bottom:20px;flex-wrap:wrap}
.pill{display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:var(--radius-pill);border:1px solid var(--border-subtle);background:var(--bg-card);color:var(--text-soft);font-size:11px;text-transform:uppercase;margin-bottom:12px}
.title-block h1{font-size:26px;display:flex;align-items:center;gap:12px;color:var(--text-main)}
.title-icon{width:36px;height:36px;border-radius:12px;display:inline-flex;align-items:center;justify-content:center;background:radial-gradient(circle at 30% 10%,#3b82f6,#1d4ed8);box-shadow:0 0 0 1px rgba(59,130,246,0.8),0 12px 25px rgba(29,78,216,0.7);font-size:18px}
.title-block p{margin:8px 0 0;color:var(--text-soft);font-size:14px}
.header-meta{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px 24px;font-size:13px}
.meta-label{color:var(--text-muted);text-transform:uppercase;font-size:11px;margin-bottom:4px}
.meta-value{color:var(--text-main);font-weight:500}
.header-bottom{display:flex;justify-content:space-between;gap:12px;align-items:center;margin-top:16px;padding-top:16px;border-top:1px solid var(--border-subtle);flex-wrap:wrap}
.badges{display:flex;flex-wrap:wrap;gap:8px}
.badge{font-size:11px;padding:4px 12px;border-radius:var(--radius-pill);display:inline-flex;align-items:center;gap:6px;border:1px solid transparent}
.badge-ok{border-color:var(--accent-border);background:var(--accent-soft);color:var(--accent-text)}
.badge-warn{border-color:var(--warn-border);background:var(--warn-soft);color:var(--warn-text)}
.badge-info{border-color:var(--info-border);background:var(--info-soft);color:var(--info-text)}
.badge-danger{border-color:var(--danger-border);background:var(--danger-soft);color:var(--danger-text)}
.stamp{font-size:11px;color:var(--text-muted);text-align:right}

/* Navigation Bar */
.nav-bar{background:var(--nav-bg);border-radius:var(--radius-lg);border:1px solid var(--border-card);padding:16px 20px;margin-bottom:24px;position:sticky;top:10px;z-index:100;box-shadow:var(--shadow-md)}
.nav-bar-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:10px}
.nav-bar-title{font-size:13px;font-weight:600;color:var(--text-soft);text-transform:uppercase}
.nav-controls{display:flex;gap:8px}
.nav-btn{padding:6px 14px;font-size:11px;font-weight:600;border-radius:var(--radius-pill);border:1px solid var(--info-border);background:var(--info-soft);color:var(--info-text);cursor:pointer;transition:all 0.2s ease}
.nav-btn:hover{background:rgba(59,130,246,0.2)}
.nav-btn.accent{border-color:var(--accent-border);background:var(--accent-soft);color:var(--accent-text)}
.nav-links{display:flex;flex-wrap:wrap;gap:8px}
.nav-link{padding:6px 12px;font-size:11px;border-radius:var(--radius-sm);background:var(--bg-card);color:var(--text-soft);text-decoration:none;border:1px solid transparent;transition:all 0.2s ease}
.nav-link:hover{background:var(--info-soft);color:var(--info-text);border-color:var(--info-border)}

/* Collapsible Sections */
.collapsible-section{margin-bottom:20px}
.section-toggle{width:100%;background:var(--section-bg);border:1px solid var(--border-card);border-radius:var(--radius-lg);padding:18px 24px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;color:var(--text-main);transition:all 0.2s ease}
.section-toggle:hover{background:var(--row-hover)}
.section-toggle.active{border-bottom-left-radius:0;border-bottom-right-radius:0;border-bottom:none}
.toggle-left{display:flex;align-items:center;gap:14px}
.toggle-icon-wrapper{width:40px;height:40px;border-radius:12px;display:flex;align-items:center;justify-content:center;background:radial-gradient(circle at 30% 10%,#3b82f6,#1d4ed8);font-size:18px}
.toggle-text h3{font-size:16px;color:var(--text-main);margin-bottom:4px}
.toggle-text p{font-size:12px;color:var(--text-muted);margin:0}
.toggle-arrow{width:32px;height:32px;border-radius:50%;background:var(--subsection-bg);display:flex;align-items:center;justify-content:center;font-size:14px;color:var(--text-soft);transition:all 0.3s ease}
.section-toggle.active .toggle-arrow{transform:rotate(180deg);background:var(--info-soft);color:var(--info-text)}
.section-content{display:none;background:var(--section-bg);border:1px solid var(--border-card);border-top:none;border-bottom-left-radius:var(--radius-lg);border-bottom-right-radius:var(--radius-lg);padding:20px}
.section-content.show{display:block}

/* Cards */
.card{background:var(--card-bg);border-radius:var(--radius-lg);border:1px solid var(--border-card);padding:20px;margin-bottom:20px}
.card h2{font-size:16px;margin-bottom:16px;display:flex;align-items:center;gap:10px}
.section-content>.card,.section-content>.audit-opinion-card{border:none;padding:0;margin:0;background:transparent;box-shadow:none}

/* Note Boxes */
.note-box{border-radius:var(--radius-md);padding:16px 18px;margin-bottom:20px;font-size:13px;line-height:1.7}
.note-box.info{background:var(--info-soft);border:1px solid var(--info-border)}
.note-box.warning{background:var(--warn-soft);border:1px solid var(--warn-border)}
.note-box strong{color:var(--highlight)}

/* Tables */
.table-card{background:var(--card-bg);border-radius:var(--radius-lg);border:1px solid var(--border-card);padding:16px;overflow:hidden;margin-bottom:20px}
.table-wrapper{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12px}
thead th{text-align:left;padding:12px 10px;background:var(--table-header-bg);color:var(--text-soft);font-weight:600;text-transform:uppercase;border-bottom:1px solid var(--border-subtle);white-space:nowrap}
thead th.number{text-align:right}
tbody td{padding:10px;border-bottom:1px solid var(--border-subtle);white-space:nowrap;color:var(--text-main)}
tbody td.number{text-align:right;font-family:monospace}
tbody tr:nth-child(even){background:var(--row-even)}
tbody tr:nth-child(odd){background:var(--row-odd)}
tbody tr:hover{background:var(--row-hover)}

/* Table Row Types */
.section-header-row td{background:var(--section-header-bg)!important;color:var(--info-text)!important;font-weight:600;font-size:13px;text-transform:uppercase}
.subsection-header-row td{background:var(--subsection-bg)!important;color:var(--text-secondary)!important;font-weight:600}
.total-row td{background:var(--total-row-bg)!important;font-weight:600;border-top:1px solid var(--accent-border)}
.grand-total-row td{background:var(--grand-total-bg)!important;font-weight:700;font-size:13px;border-top:2px solid var(--info-border)}
.gross-profit-row td{background:var(--gross-profit-bg)!important;font-weight:600;border-top:2px solid var(--accent-border)}
.expense-total-row td{background:var(--expense-total-bg)!important;font-weight:600}
.ebitda-row td{background:var(--ebitda-bg)!important;font-weight:600}

/* Text Formatting */
.indent-1{padding-left:30px!important}
.indent-2{padding-left:50px!important}
.positive{color:var(--accent)!important}
.negative{color:var(--danger)!important}
.warning{color:var(--warn)!important}
.muted{color:var(--text-soft)!important;font-style:italic}

/* Observation Grid */
.obs-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-bottom:20px}
.obs-box{border-radius:var(--radius-lg);padding:18px;font-size:13px}
.obs-box.positive{background:var(--accent-soft);border:1px solid var(--accent-border)}
.obs-box.caution{background:var(--warn-soft);border:1px solid var(--warn-border)}
.obs-title{font-size:14px;font-weight:600;margin-bottom:12px;display:flex;align-items:center;gap:8px}
.obs-box.positive .obs-title{color:var(--accent-text)}
.obs-box.caution .obs-title{color:var(--warn-text)}
.obs-list{padding-left:20px;margin:0;line-height:1.8;color:var(--text-main)}
.obs-list li{margin-bottom:6px}
.obs-list li strong{color:var(--text-main)}

/* Recommendations Box */
.reco-box{border-radius:var(--radius-lg);padding:18px 20px;background:var(--purple-soft);border:1px solid var(--purple);font-size:13px}
.reco-box .obs-title{color:var(--purple-text)}
.reco-box ol{margin:10px 0 0;padding-left:20px;line-height:1.8;color:var(--text-main)}
.reco-box li strong{color:var(--purple-text)}

/* Severity Badges */
.severity-badge{font-size:10px;padding:2px 8px;border-radius:var(--radius-pill);font-weight:600;text-transform:uppercase;margin-left:8px}
.severity-critical{background:var(--danger-soft);color:var(--danger-text);border:1px solid var(--danger-border)}
.severity-high{background:rgba(239,68,68,0.15);color:#dc2626;border:1px solid rgba(239,68,68,0.4)}
.severity-medium{background:var(--warn-soft);color:var(--warn-text);border:1px solid var(--warn-border)}
.severity-low{background:var(--info-soft);color:var(--info-text);border:1px solid var(--info-border)}

/* v6.12: Benchmark Badges for Ratios */
.benchmark-badge{font-size:9px;padding:2px 6px;border-radius:var(--radius-pill);font-weight:500;margin-left:6px;background:var(--info-soft);color:var(--info-text);border:1px solid var(--info-border);vertical-align:middle}
.benchmark-pass{background:var(--accent-soft) !important;color:var(--accent-text) !important}
.benchmark-fail{background:var(--danger-soft) !important;color:var(--danger-text) !important}

/* v6.12: Formula Display Row */
.formula-display-row{background:transparent !important}
.formula-display-row td{padding:2px 12px 8px !important;border-bottom:1px solid var(--border-subtle) !important}
.formula-row{font-size:11px;color:var(--text-muted);font-style:italic}

/* Status Pills */
.status-pill{display:inline-flex;align-items:center;padding:4px 12px;border-radius:var(--radius-pill);font-size:11px;font-weight:600}
.status-matched{background:var(--accent-soft);color:var(--accent-text);border:1px solid var(--accent-border)}
.status-minor{background:var(--info-soft);color:var(--info-text);border:1px solid var(--info-border)}
.status-moderate{background:var(--warn-soft);color:var(--warn-text);border:1px solid var(--warn-border)}
.status-severe{background:var(--danger-soft);color:var(--danger-text);border:1px solid var(--danger-border)}

/* Key Observations Grid */
.key-obs-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-bottom:20px}
.key-obs-item{background:var(--bg-card);border:1px solid var(--border-subtle);border-radius:var(--radius-md);padding:14px}
.key-obs-item h4{font-size:11px;color:var(--text-muted);text-transform:uppercase;margin-bottom:8px;letter-spacing:0.5px}
.key-obs-item p{font-size:13px;color:var(--text-main);margin:0;line-height:1.6}

/* Facility Box */
.facility-box{border-radius:var(--radius-lg);padding:18px 20px;background:var(--info-soft);border:1px solid var(--info-border);font-size:13px;margin-top:16px}
.facility-box .obs-title{color:var(--info-text)}
.facility-box ul{margin:10px 0 0;padding-left:20px;line-height:1.8;color:var(--text-main)}
.facility-box p{margin:8px 0}

/* Note Box Variants */
.note-box.success{background:var(--accent-soft);border:1px solid var(--accent-border)}
.note-box.danger{background:var(--danger-soft);border:1px solid var(--danger-border)}

/* Audit Opinion Section (v6.11) */
.audit-opinion-card{background:var(--card-bg);border-radius:var(--radius-lg);border:1px solid var(--border-card);padding:20px;margin-bottom:20px}
.audit-opinion-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
.audit-opinion-item{background:var(--bg-card);border:1px solid var(--border-subtle);border-radius:var(--radius-md);padding:16px}
.audit-opinion-item.clean{border-left:4px solid var(--accent)}
.audit-opinion-item.qualified{border-left:4px solid var(--warn)}
.audit-opinion-item.adverse{border-left:4px solid var(--danger)}
.audit-opinion-item h4{font-size:13px;color:var(--text-main);margin-bottom:12px;display:flex;align-items:center;gap:8px}
.audit-opinion-item .opinion-badge{font-size:10px;padding:3px 10px;border-radius:var(--radius-pill);font-weight:600;text-transform:uppercase}
.opinion-badge.clean{background:var(--accent-soft);color:var(--accent-text);border:1px solid var(--accent-border)}
.opinion-badge.qualified{background:var(--warn-soft);color:var(--warn-text);border:1px solid var(--warn-border)}
.opinion-badge.adverse{background:var(--danger-soft);color:var(--danger-text);border:1px solid var(--danger-border)}
.opinion-badge.disclaimer{background:var(--danger-soft);color:var(--danger-text);border:1px solid var(--danger-border)}
.opinion-badge.emphasis{background:var(--info-soft);color:var(--info-text);border:1px solid var(--info-border)}
.audit-opinion-item .detail{font-size:12px;color:var(--text-soft);margin:6px 0;line-height:1.5}
.audit-opinion-item .detail strong{color:var(--text-secondary)}
.going-concern-alert{background:var(--danger-soft);border:1px solid var(--danger-border);border-radius:var(--radius-sm);padding:8px 12px;margin-top:10px;font-size:11px;color:var(--danger-text)}

/* Expense Includes Tooltip (v6.11) */
.includes-tooltip{position:relative;display:inline-block;cursor:help;border-bottom:1px dotted var(--text-muted)}
.includes-tooltip .tooltip-text{visibility:hidden;width:200px;background-color:var(--bg-card);color:var(--text-main);text-align:left;border-radius:var(--radius-sm);padding:8px 10px;position:absolute;z-index:10;bottom:125%;left:50%;margin-left:-100px;opacity:0;transition:opacity 0.3s;font-size:11px;border:1px solid var(--border-card);box-shadow:var(--shadow-md)}
.includes-tooltip:hover .tooltip-text{visibility:visible;opacity:1}
.includes-tooltip .tooltip-text::after{content:"";position:absolute;top:100%;left:50%;margin-left:-5px;border-width:5px;border-style:solid;border-color:var(--border-card) transparent transparent transparent}

/* Report Footer (v6.5) */
.report-footer{background:#f8fafc;border-top:1px solid #e2e8f0;padding:30px 40px;margin-top:30px;border-radius:0 0 var(--radius-lg) var(--radius-lg)}
[data-theme="dark"] .report-footer{background:rgba(15,23,42,0.95);border-top-color:rgba(55,65,81,0.7)}
.confidential-banner{font-size:11px;color:#64748b;text-align:center;padding:8px 16px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;margin-bottom:20px;letter-spacing:0.3px;font-style:italic}
[data-theme="dark"] .confidential-banner{background:rgba(30,41,59,0.5);color:#9ca3af;border-color:rgba(55,65,81,0.7)}
.disclaimer{font-size:11px;color:#64748b;line-height:1.7;padding:15px 20px;background:#f1f5f9;border-left:3px solid #94a3b8;border-radius:0 4px 4px 0;margin-bottom:20px}
[data-theme="dark"] .disclaimer{background:rgba(51,65,85,0.5);color:#9ca3af;border-left-color:#6b7280}
.disclaimer-title{font-weight:600;color:#475569;margin-bottom:5px;font-size:10px;text-transform:uppercase;letter-spacing:0.5px}
[data-theme="dark"] .disclaimer-title{color:#d1d5db}
.copyright{text-align:center;font-size:11px;color:#94a3b8;padding-top:15px;border-top:1px solid #e2e8f0}
[data-theme="dark"] .copyright{color:#6b7280;border-top-color:rgba(55,65,81,0.7)}
.copyright-main{font-weight:500;color:#64748b;margin-bottom:3px}
[data-theme="dark"] .copyright-main{color:#9ca3af}
.copyright-sub{font-size:10px}

/* Cards for new sections */
.card{background:var(--card-bg);border-radius:var(--radius-lg);border:1px solid var(--border-card);padding:20px;margin-bottom:20px}
.card h2{font-size:16px;margin-bottom:16px;display:flex;align-items:center;gap:10px}
.card h4{font-size:14px;margin:16px 0 8px;color:var(--text-secondary)}
.card ul{margin:8px 0;padding-left:20px;line-height:1.8}
.card p{margin:8px 0;line-height:1.6}
.section-content>.card,.section-content>.audit-opinion-card{border:none;padding:0;margin:0;background:transparent;box-shadow:none}

/* Footer */
footer{margin-top:20px;font-size:11px;color:var(--text-muted);padding-top:16px;text-align:center}
footer p{margin:4px 0}

/* Print Styles */
@media print{
  body{background:white!important;padding:16px}
  .nav-bar,.theme-toggle{display:none}
  .section-toggle{display:none}
  .section-content{display:block!important;border:1px solid #e5e7eb!important;border-radius:12px!important;margin-bottom:16px}
  .collapsible-section{page-break-inside:avoid}
  *{color:#1e293b!important;background:white!important}
  .header-card,.card,.table-card,.obs-box,.note-box,.reco-box,.facility-box{background:white!important;border:1px solid #e5e7eb!important}
  .confidential-banner{background:#f8f8f8!important;border:1px solid #ddd!important}
  thead th{background:#f9fafb!important;color:#374151!important}
  .report-footer{background:#f9fafb!important}
  .disclaimer{background:#f3f4f6!important}
}

/* Responsive */
@media (max-width:768px){
  .obs-grid{grid-template-columns:1fr}
  .key-obs-grid{grid-template-columns:1fr}
  .header-meta{grid-template-columns:1fr}
  .header-top{flex-direction:column}
  .header-bottom{flex-direction:column;align-items:flex-start}
  .nav-links{gap:6px}
  .nav-link{padding:6px 10px;font-size:11px}
  .theme-toggle{top:auto;bottom:20px;right:20px}
  .report-footer{padding:20px}
}

/* --- FORCE LEFT ALIGNMENT FOR SECTION HEADERS --- */
.section-toggle{text-align:left !important}
.toggle-left{justify-content:flex-start !important;width:100% !important}
.toggle-icon-wrapper{min-width:40px;max-width:40px;flex-shrink:0;overflow:hidden}
.toggle-text{text-align:left !important}
.toggle-text h3,.toggle-text p{text-align:left !important;margin-left:0 !important}

</style>'''

def generate_javascript() -> str:
    """Generate JavaScript with theme toggle functionality"""
    return '''<script>
// Theme Toggle Functions
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('financial-report-theme', newTheme);
    
    updateToggleButton(newTheme);
}

function updateToggleButton(theme) {
    const btn = document.getElementById('theme-toggle-btn');
    if (btn) {
        if (theme === 'dark') {
            btn.innerHTML = '☀️ Light Mode';
        } else {
            btn.innerHTML = '🌙 Dark Mode';
        }
    }
}

// Initialize theme from localStorage or system preference
function initTheme() {
    const savedTheme = localStorage.getItem('financial-report-theme');
    
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
        updateToggleButton(savedTheme);
    } else {
        // Check system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.setAttribute('data-theme', 'dark');
            updateToggleButton('dark');
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
            updateToggleButton('light');
        }
    }
}

// Section toggle functions
function toggleSection(button) {
    const content = button.nextElementSibling;
    const isActive = button.classList.contains('active');
    if (isActive) {
        button.classList.remove('active');
        content.classList.remove('show');
    } else {
        button.classList.add('active');
        content.classList.add('show');
    }
}

function expandAll() {
    document.querySelectorAll('.section-toggle').forEach(t => t.classList.add('active'));
    document.querySelectorAll('.section-content').forEach(c => c.classList.add('show'));
}

function collapseAll() {
    document.querySelectorAll('.section-toggle').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.section-content').forEach(c => c.classList.remove('show'));
}

function openSection(sectionId) {
    const section = document.getElementById('section-' + sectionId);
    if (section) {
        section.querySelector('.section-toggle').classList.add('active');
        section.querySelector('.section-content').classList.add('show');
        setTimeout(() => section.scrollIntoView({behavior: 'smooth', block: 'start'}), 100);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initTheme);

// Listen for system theme changes
if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('financial-report-theme')) {
            const newTheme = e.matches ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
            updateToggleButton(newTheme);
        }
    });
}
</script>'''

def generate_theme_toggle_button() -> str:
    """Generate the theme toggle button HTML"""
    return '''<button id="theme-toggle-btn" class="theme-toggle" onclick="toggleTheme()">🌙 Dark Mode</button>'''

def generate_header(data: Dict) -> str:
    company = get_company_info(data)
    schema_info = data.get("_schema_info", {})
    schema = detect_schema_version(data)
    
    company_name = company.get("legal_name") or company.get("name") or "Company Name"
    reg_no = company.get("registration_no", "N/A")
    principal_activities = company.get("principal_activities", "N/A")
    
    period_keys = get_period_keys(data)
    period_labels = [get_period_label(data, pk) for pk in period_keys]
    period_coverage = f"{period_labels[0]} to {period_labels[-1]}" if period_labels else "N/A"
    
    # Get audit opinion data for badge display
    audit_opinion = company.get("audit_opinion", {})
    
    badges_html = ""
    for pk in period_keys:
        ptype = get_period_type(data, pk)
        plabel = get_period_label(data, pk)
        
        # Check for audit opinion status
        opinion_data = audit_opinion.get(pk, {})
        opinion_type = opinion_data.get("opinion_type", "") if isinstance(opinion_data, dict) else ""
        going_concern = opinion_data.get("going_concern_note", False) if isinstance(opinion_data, dict) else False
        
        # Determine badge class based on audit opinion
        if opinion_type.lower() == "adverse" or opinion_type.lower() == "disclaimer" or going_concern:
            badge_class = "badge-danger"
            badge_icon = "⚠️"
        elif opinion_type.lower() == "qualified":
            badge_class = "badge-warn"
            badge_icon = "⚠️"
        elif ptype == "audited":
            badge_class = "badge-info"
            badge_icon = "📋"
        else:
            badge_class = "badge-warn"
            badge_icon = "📋"
        
        badges_html += f'<span class="badge {badge_class}">{badge_icon} {plabel}</span>'
    
    generated_date = schema_info.get("generation_date") or datetime.now().strftime("%Y-%m-%d")
    generated_by = schema_info.get("generated_by") or "Kredit Lab"
    
    # Build auditor info for header if available
    auditor_info = ""
    for pk in period_keys:
        opinion_data = audit_opinion.get(pk, {})
        if isinstance(opinion_data, dict) and opinion_data.get("auditor_name"):
            auditor_name = opinion_data.get("auditor_name")
            auditor_info = f"<div><div class='meta-label'>Auditor</div><div class='meta-value'>{auditor_name}</div></div>"
            break  # Just show first auditor found
    
    return f'''<div class="header-card"><div class="header-top"><div class="title-block"><div class="pill"><span>📊</span><span>Financial Statement Analysis</span></div><h1><span class="title-icon">💼</span><span>{company_name}</span></h1><p>Registration No. {reg_no}</p></div><div class="header-meta"><div><div class="meta-label">Principal Activities</div><div class="meta-value">{principal_activities}</div></div><div><div class="meta-label">Financial Year End</div><div class="meta-value">{company.get("financial_year_end", "31 December")}</div></div><div><div class="meta-label">Analysis Period</div><div class="meta-value">{period_coverage}</div></div>{auditor_info}<div><div class="meta-label">Prepared By</div><div class="meta-value">{generated_by}</div></div></div></div><div class="header-bottom"><div class="badges">{badges_html}</div><div class="stamp">Generated: {generated_date} | Schema: {schema}</div></div></div>'''

def generate_nav_bar() -> str:
    return '''<div class="nav-bar"><div class="nav-bar-header"><span class="nav-bar-title">📑 Quick Navigation</span><div class="nav-controls"><button class="nav-btn accent" onclick="expandAll()">⊕ Expand All</button><button class="nav-btn" onclick="collapseAll()">⊖ Collapse All</button></div></div><div class="nav-links"><a href="#section-notes" class="nav-link" onclick="openSection('notes')">📋 Notes</a><a href="#section-audit" class="nav-link" onclick="openSection('audit')">🔍 Audit</a><a href="#section-pnl" class="nav-link" onclick="openSection('pnl')">📈 P&L</a><a href="#section-bs" class="nav-link" onclick="openSection('bs')">📊 Balance Sheet</a><a href="#section-ratios" class="nav-link" onclick="openSection('ratios')">🧮 Ratios</a><a href="#section-wc" class="nav-link" onclick="openSection('wc')">💰 Working Capital</a><a href="#section-funding" class="nav-link" onclick="openSection('funding')">🏗️ Funding</a><a href="#section-profile" class="nav-link" onclick="openSection('profile')">🎯 Profile</a><a href="#section-dscr" class="nav-link" onclick="openSection('dscr')">📐 DSCR</a><a href="#section-tnw" class="nav-link" onclick="openSection('tnw')">🏦 TNW</a><a href="#section-integrity" class="nav-link" onclick="openSection('integrity')">✅ Integrity</a><a href="#section-summary" class="nav-link" onclick="openSection('summary')">🧭 Summary</a></div></div>'''

def generate_pnl_table(data: Dict) -> str:
    period_keys = get_period_keys(data)
    income_stmt = get_income_statement(data)
    schema = detect_schema_version(data)
    currency_unit = get_currency_unit(data)  # Auto-detect RM or RM'000
    
    if not period_keys: return "<p>No period data available</p>"
    
    header_cells = "<th>Description</th>"
    for pk in period_keys:
        plabel = get_period_label(data, pk)
        # v6.16: If period label already contains source type suffix, don't add redundant type label
        if "(Audited" in plabel or "(MA)" in plabel or "(Unaudited" in plabel:
            header_cells += f'<th class="number">{plabel}<br>{currency_unit}</th>'
        else:
            ptype = "Audited" if get_period_type(data, pk) == "audited" else "Mgmt"
            header_cells += f'<th class="number">{plabel}<br>({ptype})<br>{currency_unit}</th>'
    
    body = ""
    
    # REVENUE
    body += f'<tr class="section-header-row"><td colspan="{len(period_keys)+1}">REVENUE</td></tr>'
    revenue = income_stmt.get("revenue", {})
    for key, item in revenue.get("line_items", {}).items():
        cells = f'<td class="indent-1">{get_display_name(item, key)}</td>'
        for pk in period_keys: 
            val = get_value_from_item(item, pk, None)
            cells += f'<td class="number">{format_number_or_dash(val)}</td>'
        body += f'<tr>{cells}</tr>'
    rev_total = revenue.get("total", {})
    cells = '<td><strong>Total Revenue</strong></td>'
    for pk in period_keys: 
        cells += f'<td class="number"><strong>{format_number(get_value_from_item(rev_total, pk, 0))}</strong></td>'
    body += f'<tr class="total-row">{cells}</tr>'
    
    # COST OF SALES
    body += f'<tr class="section-header-row"><td colspan="{len(period_keys)+1}">COST OF SALES</td></tr>'
    cos = income_stmt.get("cost_of_sales", {})
    for key, item in cos.get("line_items", {}).items():
        cells = f'<td class="indent-1">{get_display_name(item, key)}</td>'
        for pk in period_keys: 
            val = get_value_from_item(item, pk, None); cells += f'<td class="number">{format_number_or_dash(val)}</td>'
        body += f'<tr>{cells}</tr>'
    cos_total = cos.get("total", {})
    cells = '<td><strong>Total Cost of Sales</strong></td>'
    for pk in period_keys: 
        cells += f'<td class="number"><strong>{format_number(get_value_from_item(cos_total, pk, 0))}</strong></td>'
    body += f'<tr class="total-row">{cells}</tr>'
    
    # GROSS PROFIT
    gp = income_stmt.get("gross_profit", {})
    cells = '<td><strong>GROSS PROFIT</strong></td>'
    for pk in period_keys: 
        cells += f'<td class="number"><strong>{format_number(get_value_from_item(gp, pk, 0))}</strong></td>'
    body += f'<tr class="gross-profit-row">{cells}</tr>'
    
    # GP Margin - v6.0 has separate key
    gp_margin = income_stmt.get("gross_profit_margin", {})
    if gp_margin:
        cells = '<td class="indent-1 muted"><em>GP Margin %</em></td>'
        for pk in period_keys: 
            cells += f'<td class="number muted"><em>{format_percentage(get_value_from_item(gp_margin, pk, 0))}</em></td>'
        body += f'<tr>{cells}</tr>'
    
    # OTHER INCOME
    oi = income_stmt.get("other_income", {})
    if oi.get("line_items") or any(get_value_from_item(oi.get("total", {}), pk, 0) != 0 for pk in period_keys):
        body += f'<tr class="section-header-row"><td colspan="{len(period_keys)+1}">OTHER INCOME</td></tr>'
        for key, item in oi.get("line_items", {}).items():
            cells = f'<td class="indent-1">{get_display_name(item, key)}</td>'
            for pk in period_keys: 
                val = get_value_from_item(item, pk, None); cells += f'<td class="number">{format_number_or_dash(val)}</td>'
            body += f'<tr>{cells}</tr>'
        cells = '<td><strong>Total Other Income</strong></td>'
        for pk in period_keys: 
            cells += f'<td class="number"><strong>{format_number(get_value_from_item(oi.get("total", {}), pk, 0))}</strong></td>'
        body += f'<tr class="total-row">{cells}</tr>'
    
    # OPERATING EXPENSES - FULLY DYNAMIC RENDERING (v6.3)
    # Handles ANY structure: nested categories, direct line_items, or legacy style
    # Aligned with v6.10 "ADAPTIVE OUTPUT" principle - renders whatever JSON provides
    body += f'<tr class="section-header-row"><td colspan="{len(period_keys)+1}">OPERATING EXPENSES</td></tr>'
    opex = income_stmt.get("operating_expenses", {})
    
    # Track totals for TOTAL OPERATING EXPENSES calculation
    opex_period_totals = {pk: 0 for pk in period_keys}
    has_nested_categories = False
    rendered_category_keys = []  # Track what we've rendered to avoid duplicates
    
    # DYNAMIC DETECTION: Check if opex has nested category structure
    # A nested category is a dict with "line_items" and/or "total" keys
    def is_expense_category(item):
        """Check if an item is an expense category (has line_items or total structure)"""
        if not isinstance(item, dict):
            return False
        return "line_items" in item or "total" in item
    
    # First pass: detect if we have nested categories
    for key, item in opex.items():
        if key in ["total", "line_items"]:
            continue
        if is_expense_category(item):
            has_nested_categories = True
            break
    
    if has_nested_categories:
        # DYNAMIC NESTED STRUCTURE: Iterate through ALL categories
        # Works with administrative_expenses, other_expenses, selling_expenses, etc.
        for cat_key, cat_data in opex.items():
            # Skip non-category items
            if cat_key in ["total", "line_items"] or not isinstance(cat_data, dict):
                continue
            if not is_expense_category(cat_data):
                continue
            
            rendered_category_keys.append(cat_key)
            cat_line_items = cat_data.get("line_items", {})
            cat_total = cat_data.get("total", {})
            
            # Get display name for category (from total's display_name or convert key)
            cat_display_name = cat_total.get("display_name") if cat_total else None
            if not cat_display_name:
                cat_display_name = snake_to_title(cat_key)
            # Clean up "Total " prefix if present for subsection header
            subsection_name = cat_display_name.replace("Total ", "")
            
            if cat_line_items:
                # Render subsection header
                body += f'<tr class="subsection-header-row"><td colspan="{len(period_keys)+1}">{subsection_name}</td></tr>'
                
                # Render line items (only those with non-zero values)
                for item_key, item in cat_line_items.items():
                    if any(get_value_from_item(item, pk, 0) != 0 for pk in period_keys):
                        display_name = get_display_name(item, item_key)
                        # v6.11: Check for "includes" field for consolidated items
                        includes_text = item.get("includes", "") if isinstance(item, dict) else ""
                        if includes_text:
                            display_name = f'<span class="includes-tooltip">{display_name}<span class="tooltip-text">Includes: {includes_text}</span></span>'
                        cells = f'<td class="indent-2">{display_name}</td>'
                        for pk in period_keys: 
                            val = get_value_from_item(item, pk, None); cells += f'<td class="number">{format_number_or_dash(val)}</td>'
                        body += f'<tr>{cells}</tr>'
                
                # Render subtotal for this category
                if cat_total:
                    cells = f'<td class="indent-1"><em>{cat_display_name}</em></td>'
                    for pk in period_keys:
                        val = get_value_from_item(cat_total, pk, 0)
                        opex_period_totals[pk] += val
                        cells += f'<td class="number"><em>{format_number(val)}</em></td>'
                    body += f'<tr class="total-row">{cells}</tr>'
            
            elif cat_total:
                # No line items but has total - show as single line
                cells = f'<td class="indent-1">{subsection_name}</td>'
                for pk in period_keys:
                    val = get_value_from_item(cat_total, pk, 0)
                    opex_period_totals[pk] += val
                    cells += f'<td class="number">{format_number(val)}</td>'
                body += f'<tr>{cells}</tr>'
        
        # TOTAL OPERATING EXPENSES - calculated from all category totals
        cells = '<td><strong>TOTAL OPERATING EXPENSES</strong></td>'
        for pk in period_keys: 
            cells += f'<td class="number"><strong>{format_number(opex_period_totals[pk])}</strong></td>'
        body += f'<tr class="expense-total-row">{cells}</tr>'
    
    elif "line_items" in opex:
        # FLAT STRUCTURE: direct line_items under operating_expenses
        for key, item in opex.get("line_items", {}).items():
            if any(get_value_from_item(item, pk, 0) != 0 for pk in period_keys):
                display_name = get_display_name(item, key)
                # v6.11: Check for "includes" field for consolidated items
                includes_text = item.get("includes", "") if isinstance(item, dict) else ""
                if includes_text:
                    display_name = f'<span class="includes-tooltip">{display_name}<span class="tooltip-text">Includes: {includes_text}</span></span>'
                cells = f'<td class="indent-1">{display_name}</td>'
                for pk in period_keys: 
                    val = get_value_from_item(item, pk, None); cells += f'<td class="number">{format_number_or_dash(val)}</td>'
                body += f'<tr>{cells}</tr>'
        
        opex_total = opex.get("total", {})
        cells = '<td><strong>TOTAL OPERATING EXPENSES</strong></td>'
        for pk in period_keys: 
            cells += f'<td class="number"><strong>{format_number(get_value_from_item(opex_total, pk, 0))}</strong></td>'
        body += f'<tr class="expense-total-row">{cells}</tr>'
    
    else:
        # LEGACY v2.1 FALLBACK: Try known category names
        legacy_found = False
        for cat_key in ["administrative", "staff_costs", "depreciation", "other", 
                        "administrative_expenses", "other_expenses", "selling_expenses"]:
            cat_data = opex.get(cat_key, {})
            if isinstance(cat_data, dict) and cat_data.get("line_items"):
                legacy_found = True
                body += f'<tr class="subsection-header-row"><td colspan="{len(period_keys)+1}">{snake_to_title(cat_key)}</td></tr>'
                for key, item in cat_data.get("line_items", {}).items():
                    cells = f'<td class="indent-2">{get_display_name(item, key)}</td>'
                    for pk in period_keys: 
                        val = get_value_from_item(item, pk, None); cells += f'<td class="number">{format_number_or_dash(val)}</td>'
                    body += f'<tr>{cells}</tr>'
        
        opex_total = opex.get("total", {})
        cells = '<td><strong>TOTAL OPERATING EXPENSES</strong></td>'
        for pk in period_keys: 
            cells += f'<td class="number"><strong>{format_number(get_value_from_item(opex_total, pk, 0))}</strong></td>'
        body += f'<tr class="expense-total-row">{cells}</tr>'
    
    # SEPARATE OTHER EXPENSES at income statement level (for older schemas)
    # Only render if not already rendered under operating_expenses
    other_exp_top = income_stmt.get("other_expenses", {})
    if other_exp_top and "other_expenses" not in rendered_category_keys:
        if other_exp_top.get("line_items") or any(get_value_from_item(other_exp_top.get("total", {}), pk, 0) != 0 for pk in period_keys):
            body += f'<tr class="section-header-row"><td colspan="{len(period_keys)+1}">OTHER EXPENSES</td></tr>'
            for key, item in other_exp_top.get("line_items", {}).items():
                if any(get_value_from_item(item, pk, 0) != 0 for pk in period_keys):
                    cells = f'<td class="indent-1">{get_display_name(item, key)}</td>'
                    for pk in period_keys: 
                        val = get_value_from_item(item, pk, None); cells += f'<td class="number">{format_number_or_dash(val)}</td>'
                    body += f'<tr>{cells}</tr>'
            cells = '<td><strong>Total Other Expenses</strong></td>'
            for pk in period_keys: 
                cells += f'<td class="number"><strong>{format_number(get_value_from_item(other_exp_top.get("total", {}), pk, 0))}</strong></td>'
            body += f'<tr class="expense-total-row">{cells}</tr>'
    
    # OPERATING PROFIT
    ebit = income_stmt.get("operating_profit", income_stmt.get("profit_from_operations", {}))
    cells = '<td><strong>OPERATING PROFIT (EBIT)</strong></td>'
    for pk in period_keys: 
        cells += f'<td class="number"><strong>{format_number(get_value_from_item(ebit, pk, 0))}</strong></td>'
    body += f'<tr class="gross-profit-row">{cells}</tr>'
    
    # Operating Profit Margin - v6.0 has separate key
    op_margin = income_stmt.get("operating_profit_margin", {})
    if op_margin:
        cells = '<td class="indent-1 muted"><em>Operating Margin %</em></td>'
        for pk in period_keys: 
            cells += f'<td class="number muted"><em>{format_percentage(get_value_from_item(op_margin, pk, 0))}</em></td>'
        body += f'<tr>{cells}</tr>'
    
    # FINANCE COSTS
    fc = income_stmt.get("finance_costs", {})
    if fc.get("line_items") or any(get_value_from_item(fc.get("total", {}), pk, 0) != 0 for pk in period_keys):
        body += f'<tr class="section-header-row"><td colspan="{len(period_keys)+1}">FINANCE COSTS</td></tr>'
        for key, item in fc.get("line_items", {}).items():
            cells = f'<td class="indent-1">{get_display_name(item, key)}</td>'
            for pk in period_keys: 
                val = get_value_from_item(item, pk, None); cells += f'<td class="number">{format_number_or_dash(val)}</td>'
            body += f'<tr>{cells}</tr>'
        cells = '<td><strong>Total Finance Costs</strong></td>'
        for pk in period_keys: 
            cells += f'<td class="number"><strong>{format_number(get_value_from_item(fc.get("total", {}), pk, 0))}</strong></td>'
        body += f'<tr class="total-row">{cells}</tr>'
    
    # PBT
    pbt = income_stmt.get("profit_before_tax", {})
    cells = '<td><strong>PROFIT BEFORE TAX</strong></td>'
    for pk in period_keys: 
        cells += f'<td class="number"><strong>{format_number(get_value_from_item(pbt, pk, 0))}</strong></td>'
    body += f'<tr class="grand-total-row">{cells}</tr>'
    
    # PBT Margin
    pbt_margin = income_stmt.get("pbt_margin", {})
    if pbt_margin:
        cells = '<td class="indent-1 muted"><em>PBT Margin %</em></td>'
        for pk in period_keys: 
            cells += f'<td class="number muted"><em>{format_percentage(get_value_from_item(pbt_margin, pk, 0))}</em></td>'
        body += f'<tr>{cells}</tr>'
    
    # TAXATION - v6.16: Dynamic line items (not hardcoded to 3 keys)
    body += f'<tr class="section-header-row"><td colspan="{len(period_keys)+1}">TAXATION</td></tr>'
    tax = income_stmt.get("taxation", {})
    tax_line_items = tax.get("line_items", {})
    if tax_line_items:
        for key, item in tax_line_items.items():
            if isinstance(item, dict) and any(get_value_from_item(item, pk, None) is not None for pk in period_keys):
                cells = f'<td class="indent-1">{get_display_name(item, key)}</td>'
                for pk in period_keys:
                    val = get_value_from_item(item, pk, None)
                    cells += f'<td class="number">{format_number_or_dash(val)}</td>'
                body += f'<tr>{cells}</tr>'
    else:
        for key, label in [("current_tax", "Current Tax"), ("over_under_provision", "(Over)/Under Provision"), ("deferred_tax", "Deferred Tax")]:
            item = tax.get(key, {})
            if item and any(get_value_from_item(item, pk, 0) != 0 for pk in period_keys):
                cells = f'<td class="indent-1">{label}</td>'
                for pk in period_keys: 
                    val = get_value_from_item(item, pk, None); cells += f'<td class="number">{format_number_or_dash(val)}</td>'
                body += f'<tr>{cells}</tr>'
    cells = '<td><strong>Total Taxation</strong></td>'
    for pk in period_keys: 
        cells += f'<td class="number"><strong>{format_number(get_value_from_item(tax.get("total", {}), pk, 0))}</strong></td>'
    body += f'<tr class="total-row">{cells}</tr>'
    
    # NET PROFIT
    npat = income_stmt.get("net_profit_after_tax", income_stmt.get("profit_after_tax", {}))
    cells = '<td><strong>NET PROFIT</strong></td>'
    for pk in period_keys: 
        cells += f'<td class="number"><strong>{format_number(get_value_from_item(npat, pk, 0))}</strong></td>'
    body += f'<tr class="grand-total-row">{cells}</tr>'
    
    # Net Profit Margin
    np_margin = income_stmt.get("net_profit_margin", {})
    if np_margin:
        cells = '<td class="indent-1 muted"><em>Net Profit Margin %</em></td>'
        for pk in period_keys: 
            cells += f'<td class="number muted"><em>{format_percentage(get_value_from_item(np_margin, pk, 0))}</em></td>'
        body += f'<tr>{cells}</tr>'
    
    # EBITDA
    ebitda = income_stmt.get("ebitda", {})
    if ebitda:
        cells = '<td><strong>EBITDA</strong></td>'
        for pk in period_keys: 
            cells += f'<td class="number"><strong>{format_number(get_value_from_item(ebitda, pk, 0))}</strong></td>'
        body += f'<tr class="ebitda-row">{cells}</tr>'
    
    return f'''<div class="collapsible-section" id="section-pnl"><button class="section-toggle active" onclick="toggleSection(this)"><div class="toggle-left"><div class="toggle-icon-wrapper">📈</div><div class="toggle-text"><h3>Statement of Comprehensive Income / P&L</h3><p>Revenue, Cost of Sales, Operating Expenses, and Net Profit</p></div></div><div class="toggle-arrow">▼</div></button><div class="section-content show"><div class="table-card"><div class="table-wrapper"><table><thead><tr>{header_cells}</tr></thead><tbody>{body}</tbody></table></div></div></div></div>'''

def generate_balance_sheet_table(data: Dict) -> str:
    period_keys = get_period_keys(data)
    bs = get_balance_sheet(data)
    currency_unit = get_currency_unit(data)
    
    if not period_keys: return "<p>No period data available</p>"
    
    header_cells = "<th>Description</th>"
    for pk in period_keys:
        plabel = get_period_label(data, pk)
        # v6.16: If period label already contains source type suffix, don't add redundant type label
        if "(Audited" in plabel or "(MA)" in plabel or "(Unaudited" in plabel:
            header_cells += f'<th class="number">{plabel}<br>{currency_unit}</th>'
        else:
            ptype = "Audited" if get_period_type(data, pk) == "audited" else "Mgmt"
            header_cells += f'<th class="number">{plabel}<br>({ptype})<br>{currency_unit}</th>'
    
    body = ""
    
    # NON-CURRENT ASSETS - Dynamic rendering (v6.2: render ALL NCA items dynamically)
    nca = bs.get("non_current_assets", {})
    if nca:
        body += f'<tr class="section-header-row"><td colspan="{len(period_keys)+1}">NON-CURRENT ASSETS</td></tr>'
        
        # Iterate through ALL NCA items dynamically
        for nca_key, nca_item in nca.items():
            if nca_key == "total" or not isinstance(nca_item, dict):
                continue
            
            # Check if this is PPE (has line_items structure) or a simple item
            if nca_key == "property_plant_equipment" or "line_items" in nca_item:
                # PPE with nested line_items
                ppe_name = nca_item.get("display_name", "Property, Plant & Equipment") if isinstance(nca_item, dict) else "Property, Plant & Equipment"
                body += f'<tr class="subsection-header-row"><td colspan="{len(period_keys)+1}">{ppe_name}</td></tr>'
                for key, item in nca_item.get("line_items", {}).items():
                    if any(get_value_from_item(item, pk, 0) != 0 for pk in period_keys):
                        cells = f'<td class="indent-2">{get_display_name(item, key)}</td>'
                        for pk in period_keys: 
                            val = get_value_from_item(item, pk, None); cells += f'<td class="number">{format_number_or_dash(val)}</td>'
                        body += f'<tr>{cells}</tr>'
                ppe_total = nca_item.get("total", {})
                if ppe_total:
                    cells = f'<td class="indent-1"><strong>{get_display_name(ppe_total, "total_ppe")}</strong></td>'
                    for pk in period_keys: 
                        cells += f'<td class="number"><strong>{format_number(get_value_from_item(ppe_total, pk, 0))}</strong></td>'
                    body += f'<tr class="total-row">{cells}</tr>'
            else:
                # Simple NCA item (intangibles, investments, etc.)
                val_item = nca_item.get("total", nca_item) if "total" in nca_item else nca_item
                if any(get_value_from_item(val_item, pk, 0) != 0 for pk in period_keys):
                    cells = f'<td class="indent-1">{get_display_name(nca_item, nca_key)}</td>'
                    for pk in period_keys: 
                        cells += f'<td class="number">{format_number(get_value_from_item(val_item, pk, 0))}</td>'
                    body += f'<tr>{cells}</tr>'
        
        nca_total = nca.get("total", {})
        cells = '<td><strong>TOTAL NON-CURRENT ASSETS</strong></td>'
        for pk in period_keys: 
            cells += f'<td class="number"><strong>{format_number(get_value_from_item(nca_total, pk, 0))}</strong></td>'
        body += f'<tr class="grand-total-row">{cells}</tr>'
    
    # CURRENT ASSETS - Dynamic rendering (v6.1 fix: render ALL items, not hardcoded list)
    ca = bs.get("current_assets", {})
    if ca:
        body += f'<tr class="section-header-row"><td colspan="{len(period_keys)+1}">CURRENT ASSETS</td></tr>'
        # Iterate through ALL keys dynamically (same approach as NCL and CL)
        for key, item in ca.items():
            if key != "total" and isinstance(item, dict):
                # Check if it has nested total
                if "total" in item:
                    val_item = item.get("total", {})
                else:
                    val_item = item
                
                if any(get_value_from_item(val_item, pk, 0) != 0 for pk in period_keys):
                    cells = f'<td class="indent-1">{get_display_name(item, key)}</td>'
                    for pk in period_keys: 
                        cells += f'<td class="number">{format_number(get_value_from_item(val_item, pk, 0))}</td>'
                    body += f'<tr>{cells}</tr>'
        
        ca_total = ca.get("total", {})
        cells = '<td><strong>TOTAL CURRENT ASSETS</strong></td>'
        for pk in period_keys: 
            cells += f'<td class="number"><strong>{format_number(get_value_from_item(ca_total, pk, 0))}</strong></td>'
        body += f'<tr class="grand-total-row">{cells}</tr>'
    
    # TOTAL ASSETS
    ta = bs.get("total_assets", {})
    if ta:
        cells = '<td><strong>TOTAL ASSETS</strong></td>'
        for pk in period_keys: 
            cells += f'<td class="number"><strong>{format_number(get_value_from_item(ta, pk, 0))}</strong></td>'
        body += f'<tr class="gross-profit-row">{cells}</tr>'
    
    # EQUITY - Dynamic rendering (v6.2: render ALL equity items dynamically)
    eq = bs.get("equity", {})
    if eq:
        body += f'<tr class="section-header-row"><td colspan="{len(period_keys)+1}">EQUITY</td></tr>'
        # Iterate through ALL equity items dynamically (not hardcoded keys)
        for key, item in eq.items():
            if key != "total" and isinstance(item, dict):
                val_item = item.get("total", item) if "total" in item else item
                if any(get_value_from_item(val_item, pk, 0) != 0 for pk in period_keys):
                    cells = f'<td class="indent-1">{get_display_name(item, key)}</td>'
                    for pk in period_keys: 
                        cells += f'<td class="number">{format_number(get_value_from_item(val_item, pk, 0))}</td>'
                    body += f'<tr>{cells}</tr>'
        eq_total = eq.get("total", {})
        cells = '<td><strong>TOTAL EQUITY</strong></td>'
        for pk in period_keys: 
            cells += f'<td class="number"><strong>{format_number(get_value_from_item(eq_total, pk, 0))}</strong></td>'
        body += f'<tr class="grand-total-row">{cells}</tr>'
    
    # NON-CURRENT LIABILITIES
    ncl = bs.get("non_current_liabilities", {})
    if ncl:
        body += f'<tr class="section-header-row"><td colspan="{len(period_keys)+1}">NON-CURRENT LIABILITIES</td></tr>'
        for key, item in ncl.items():
            if key != "total" and isinstance(item, dict):
                val_item = item.get("total", item) if "total" in item else item
                if any(get_value_from_item(val_item, pk, 0) != 0 for pk in period_keys):
                    cells = f'<td class="indent-1">{get_display_name(item, key)}</td>'
                    for pk in period_keys: 
                        cells += f'<td class="number">{format_number(get_value_from_item(val_item, pk, 0))}</td>'
                    body += f'<tr>{cells}</tr>'
        ncl_total = ncl.get("total", {})
        cells = '<td><strong>TOTAL NON-CURRENT LIABILITIES</strong></td>'
        for pk in period_keys: 
            cells += f'<td class="number"><strong>{format_number(get_value_from_item(ncl_total, pk, 0))}</strong></td>'
        body += f'<tr class="total-row">{cells}</tr>'
    
    # CURRENT LIABILITIES
    cl = bs.get("current_liabilities", {})
    if cl:
        body += f'<tr class="section-header-row"><td colspan="{len(period_keys)+1}">CURRENT LIABILITIES</td></tr>'
        for key, item in cl.items():
            if key != "total" and isinstance(item, dict):
                val_item = item.get("total", item) if "total" in item else item
                if any(get_value_from_item(val_item, pk, 0) != 0 for pk in period_keys):
                    cells = f'<td class="indent-1">{get_display_name(item, key)}</td>'
                    for pk in period_keys: 
                        cells += f'<td class="number">{format_number(get_value_from_item(val_item, pk, 0))}</td>'
                    body += f'<tr>{cells}</tr>'
        cl_total = cl.get("total", {})
        cells = '<td><strong>TOTAL CURRENT LIABILITIES</strong></td>'
        for pk in period_keys: 
            cells += f'<td class="number"><strong>{format_number(get_value_from_item(cl_total, pk, 0))}</strong></td>'
        body += f'<tr class="expense-total-row">{cells}</tr>'
    
    # TOTAL LIABILITIES
    tl = bs.get("total_liabilities", {})
    if tl:
        cells = '<td><strong>TOTAL LIABILITIES</strong></td>'
        for pk in period_keys: 
            cells += f'<td class="number"><strong>{format_number(get_value_from_item(tl, pk, 0))}</strong></td>'
        body += f'<tr class="expense-total-row">{cells}</tr>'
    
    # TOTAL EQUITY & LIABILITIES
    tel = bs.get("total_equity_and_liabilities", {})
    if tel:
        cells = '<td><strong>TOTAL EQUITY & LIABILITIES</strong></td>'
        for pk in period_keys: 
            cells += f'<td class="number"><strong>{format_number(get_value_from_item(tel, pk, 0))}</strong></td>'
        body += f'<tr class="gross-profit-row">{cells}</tr>'
    
    return f'''<div class="collapsible-section" id="section-bs"><button class="section-toggle" onclick="toggleSection(this)"><div class="toggle-left"><div class="toggle-icon-wrapper">📊</div><div class="toggle-text"><h3>Statement of Financial Position / Balance Sheet</h3><p>Assets, Liabilities, and Shareholders' Equity</p></div></div><div class="toggle-arrow">▼</div></button><div class="section-content"><div class="table-card"><div class="table-wrapper"><table><thead><tr>{header_cells}</tr></thead><tbody>{body}</tbody></table></div></div></div></div>'''

def generate_ratios_section(data: Dict) -> str:
    """Generate Financial Ratios section - v6.12 compatible with formula display and benchmarks"""
    period_keys = get_period_keys(data)
    ratios = data.get("financial_ratios", {})
    
    if not ratios: return ""
    
    header_cells = "<th>Ratio</th>"
    for pk in period_keys:
        header_cells += f'<th class="number">{get_period_label(data, pk)}</th>'
    
    body = ""
    
    # Define ratio categories and their items
    # v6.12: Support both old names (debt_to_equity) and new names (liabilities_to_equity)
    categories = [
        ("Profitability Ratios", "profitability_ratios", ["gross_profit_margin", "operating_profit_margin", "pbt_margin", "net_profit_margin", "ebitda_margin", "roa", "roe"]),
        ("Liquidity Ratios", "liquidity_ratios", ["current_ratio", "quick_ratio", "cash_ratio"]),
        ("Leverage Ratios", "leverage_ratios", [
            # v6.12 new names first (preferred), then old names for backward compatibility
            "liabilities_to_equity", "debt_to_equity",  # Try new name first, then old
            "liabilities_to_assets", "debt_to_assets",  # Try new name first, then old
            "gearing_ratio", "interest_coverage", "dscr"
        ]),
        ("Efficiency Ratios", "efficiency_ratios", ["asset_turnover", "debtor_days", "creditor_days", "inventory_days", "cash_conversion_cycle"])
    ]
    
    # Track which ratios we've already rendered to avoid duplicates
    rendered_ratios = set()
    
    for cat_name, cat_key, ratio_keys in categories:
        cat_data = ratios.get(cat_key, {})
        if cat_data:
            body += f'<tr class="section-header-row"><td colspan="{len(period_keys)+1}">{cat_name}</td></tr>'
            for rk in ratio_keys:
                # Skip if this is a fallback key and we already rendered the new key
                # e.g., skip debt_to_equity if we already rendered liabilities_to_equity
                if rk == "debt_to_equity" and "liabilities_to_equity" in rendered_ratios:
                    continue
                if rk == "debt_to_assets" and "liabilities_to_assets" in rendered_ratios:
                    continue
                
                item = cat_data.get(rk, {})
                if item and any(get_value_from_item(item, pk, None) is not None for pk in period_keys):
                    rendered_ratios.add(rk)
                    unit = item.get("unit", "")
                    formula = item.get("formula", "")  # v6.12: Get formula field
                    benchmark = item.get("benchmark", "")  # v6.12: Get benchmark field
                    
                    # Get display name - prefer from item, then from lookup
                    display_name = item.get("display_name", "") or get_ratio_display_name(rk)
                    
                    # Build display name with benchmark if available
                    if benchmark:
                        display_name_with_benchmark = f'{display_name} <span class="benchmark-badge">{benchmark}</span>'
                    else:
                        display_name_with_benchmark = display_name
                    
                    # v7.2: Check if this efficiency ratio has dual values
                    has_period_adjusted = "values_period_adjusted" in item and "values_standard" in item
                    
                    # For dual-method efficiency ratios, show standard (x365) as primary row
                    cells = f'<td class="indent-1">{display_name_with_benchmark}</td>'
                    for pk in period_keys:
                        val = get_value_from_item(item, pk, None)
                        if val is not None:
                            # Check benchmark status for styling
                            benchmark_class = ""
                            if benchmark and val is not None:
                                benchmark_class = check_benchmark_status(val, benchmark, unit)
                            
                            if unit == "%":
                                cells += f'<td class="number {benchmark_class}">{format_percentage(val)}</td>'
                            elif unit in ["x", "times"]:
                                cells += f'<td class="number {benchmark_class}">{format_number(val, 2)}x</td>'
                            elif unit == "days":
                                cells += f'<td class="number {benchmark_class}">{format_number(val, 0)} days</td>'
                            else:
                                cells += f'<td class="number {benchmark_class}">{format_number(val, 2)}</td>'
                        else:
                            cells += '<td class="number">-</td>'
                    body += f'<tr>{cells}</tr>'
                    
                    # v7.2: Add period-adjusted row if dual values exist and any YTD period differs
                    if has_period_adjusted:
                        pa_values = item.get("values_period_adjusted", {})
                        std_values = item.get("values_standard", {})
                        period_days = item.get("period_days", {})
                        
                        # Only show period-adjusted row if at least one period differs from standard
                        has_difference = any(
                            pa_values.get(pk) is not None and std_values.get(pk) is not None 
                            and abs(float(pa_values.get(pk, 0)) - float(std_values.get(pk, 0))) > 0.1
                            for pk in period_keys
                        )
                        
                        if has_difference:
                            pa_cells = f'<td class="indent-2 muted"><em>↳ Period-Adjusted</em></td>'
                            for pk in period_keys:
                                pa_val = pa_values.get(pk, None)
                                pd_val = period_days.get(pk, 365)
                                std_val = std_values.get(pk, None)
                                if pa_val is not None and std_val is not None and abs(float(pa_val) - float(std_val)) > 0.1:
                                    pa_cells += f'<td class="number muted"><em>{format_number(pa_val, 0)} days <span style="font-size:0.8em;">({pd_val}d period)</span></em></td>'
                                else:
                                    pa_cells += '<td class="number muted"><em>-</em></td>'
                            body += f'<tr>{pa_cells}</tr>'
                    
                    # v6.12: Add formula row if formula is available
                    if formula:
                        formula_cells = f'<td class="indent-2 formula-row"><em>Formula: {formula}</em></td>'
                        for pk in period_keys:
                            formula_cells += '<td class="formula-row"></td>'
                        body += f'<tr class="formula-display-row">{formula_cells}</tr>'
    
    return f'''<div class="collapsible-section" id="section-ratios"><button class="section-toggle" onclick="toggleSection(this)"><div class="toggle-left"><div class="toggle-icon-wrapper">🧮</div><div class="toggle-text"><h3>Financial Ratios</h3><p>Profitability, Liquidity, Leverage, and Efficiency metrics</p></div></div><div class="toggle-arrow">▼</div></button><div class="section-content"><div class="table-card"><div class="table-wrapper"><table><thead><tr>{header_cells}</tr></thead><tbody>{body}</tbody></table></div></div></div></div>'''

def check_benchmark_status(value: float, benchmark: str, unit: str) -> str:
    """Check if a ratio value meets its benchmark and return appropriate CSS class"""
    try:
        # Parse benchmark string like ">= 1.25x" or "<= 4.0x"
        if ">=" in benchmark:
            threshold = float(benchmark.replace(">=", "").replace("x", "").replace("%", "").strip())
            return "benchmark-pass" if value >= threshold else "benchmark-fail"
        elif "<=" in benchmark:
            threshold = float(benchmark.replace("<=", "").replace("x", "").replace("%", "").strip())
            return "benchmark-pass" if value <= threshold else "benchmark-fail"
        elif ">" in benchmark:
            threshold = float(benchmark.replace(">", "").replace("x", "").replace("%", "").strip())
            return "benchmark-pass" if value > threshold else "benchmark-fail"
        elif "<" in benchmark:
            threshold = float(benchmark.replace("<", "").replace("x", "").replace("%", "").strip())
            return "benchmark-pass" if value < threshold else "benchmark-fail"
    except (ValueError, TypeError):
        pass
    return ""

def generate_working_capital_section(data: Dict) -> str:
    """Generate Working Capital Analysis section - v6.18 compatible
    v6.18: OWC interpretation, WCR interpretation, and WCR calculation_details REMOVED.
    CCC is PRIMARY driver, OWC is SUPPORTING indicator.
    Backward compatible: still renders interpretation blocks if present (v6.16 and earlier)."""
    wc = data.get("working_capital_analysis", {})
    if not wc:
        return ""
    
    period_keys = get_period_keys(data)
    currency_unit = get_currency_unit(data)
    
    header_cells = "<th>Metric</th>"
    for pk in period_keys:
        header_cells += f'<th class="number">{get_period_label(data, pk)}</th>'
    
    body = ""
    
    # Net Working Capital
    nwc = wc.get("net_working_capital", {})
    if nwc:
        body += f'<tr class="section-header-row"><td colspan="{len(period_keys)+1}">NET WORKING CAPITAL</td></tr>'
        cells = '<td class="indent-1">Current Assets - Current Liabilities</td>'
        nwc_values = nwc.get("values", {})
        for pk in period_keys:
            val = nwc_values.get(pk, 0)
            status_class = "positive" if val >= 0 else "negative"
            cells += f'<td class="number {status_class}">{format_number(val)}</td>'
        body += f'<tr class="total-row">{cells}</tr>'
    
    # Operating Working Capital
    owc = wc.get("operating_working_capital", {})
    if owc:
        body += f'<tr class="section-header-row"><td colspan="{len(period_keys)+1}">OPERATING WORKING CAPITAL (SUPPORTING INDICATOR)</td></tr>'
        cells = '<td class="indent-1">Trade Receivables + Inventory - Trade Payables</td>'
        owc_values = owc.get("values", {})
        for pk in period_keys:
            val = owc_values.get(pk, 0)
            status_class = "negative" if val > 0 else "positive"
            cells += f'<td class="number {status_class}">{format_number(val)}</td>'
        body += f'<tr class="total-row">{cells}</tr>'
        
        # v6.18: Show OWC components if available (trade_receivables, inventory, trade_payables)
        owc_components = owc.get("components", {})
        if owc_components:
            # Show components for the latest period that has them
            for pk in reversed(period_keys):
                pk_comp = owc_components.get(pk, {})
                if pk_comp:
                    for comp_key, comp_label in [("trade_receivables", "Trade Receivables"), 
                                                  ("inventory", "Inventory"), 
                                                  ("trade_payables", "Trade Payables")]:
                        comp_val = pk_comp.get(comp_key, 0)
                        if comp_val != 0 or comp_key == "inventory":  # Show inventory even if 0
                            cells = f'<td class="indent-2 muted"><em>  {comp_label}</em></td>'
                            # Show value only for periods that have component data
                            for pk2 in period_keys:
                                pk2_comp = owc_components.get(pk2, {})
                                if pk2_comp:
                                    cells += f'<td class="number muted"><em>{format_number(pk2_comp.get(comp_key, 0))}</em></td>'
                                else:
                                    cells += '<td class="number muted">-</td>'
                            body += f'<tr>{cells}</tr>'
                    break  # Only need to determine structure from one period
        
        # BACKWARD COMPATIBILITY: Render OWC interpretation if present (v6.16 and earlier)
        # v6.18 removes this block, so it simply won't render for v6.18 JSON
        owc_interp = owc.get("interpretation", {})
        if owc_interp:
            for pk in period_keys:
                pk_interp = owc_interp.get(pk, {})
                if isinstance(pk_interp, dict):
                    status = pk_interp.get("status", "")
                    explanation = pk_interp.get("explanation", "")
                    if explanation:
                        status_icon = "🟢" if status == "self_funding" else "🔴"
                        body += f'<tr><td colspan="{len(period_keys)+1}" class="indent-2 muted"><em>{status_icon} {get_period_label(data, pk)}: {explanation}</em></td></tr>'
    
    # Working Capital Requirement
    wcr = wc.get("working_capital_requirement", {})
    if wcr:
        body += f'<tr class="section-header-row"><td colspan="{len(period_keys)+1}">WORKING CAPITAL REQUIREMENT (CCC-BASED)</td></tr>'
        
        # v6.18: calculation_details is REMOVED. Get CCC days from financial_ratios instead.
        # BACKWARD COMPATIBLE: still uses calculation_details if present (v6.16 and earlier)
        calc_details = wcr.get("calculation_details", {})
        wcr_values = wcr.get("values", wcr.get("values_standard", {}))
        
        # v7.2: Also check for values_standard and values_period_adjusted
        wcr_values_standard = wcr.get("values_standard", wcr_values)
        wcr_values_period_adjusted = wcr.get("values_period_adjusted", {})
        
        # Show CCC Days row - try calculation_details first, then fall back to efficiency_ratios.cash_conversion_cycle
        ccc_ratio = data.get("financial_ratios", {}).get("efficiency_ratios", {}).get("cash_conversion_cycle", {})
        # Prefer "values" (backward compat), then "values_standard" for standard x365 display
        ccc_from_ratios = ccc_ratio.get("values", {}) or ccc_ratio.get("values_standard", {})
        has_ccc_data = bool(calc_details) or bool(ccc_from_ratios)
        
        if has_ccc_data:
            cells = '<td class="indent-1">CCC Days (PRIMARY DRIVER)</td>'
            for pk in period_keys:
                # Try calculation_details first (backward compat), then ratios
                ccc = calc_details.get(pk, {}).get("ccc_days", 0) if calc_details else 0
                if not ccc and ccc_from_ratios:
                    ccc = ccc_from_ratios.get(pk, 0)
                ccc_class = "negative" if ccc and float(ccc) > 0 else "positive"
                cells += f'<td class="number {ccc_class}">{format_number(ccc, 0)} days</td>'
            body += f'<tr>{cells}</tr>'
            
            # v7.2: Show period-adjusted CCC if available
            ccc_pa = data.get("financial_ratios", {}).get("efficiency_ratios", {}).get("cash_conversion_cycle", {}).get("values_period_adjusted", {})
            if ccc_pa:
                ccc_std = data.get("financial_ratios", {}).get("efficiency_ratios", {}).get("cash_conversion_cycle", {}).get("values_standard", {})
                has_diff = any(
                    ccc_pa.get(pk) is not None and ccc_std.get(pk) is not None
                    and abs(float(ccc_pa.get(pk, 0)) - float(ccc_std.get(pk, 0))) > 0.1
                    for pk in period_keys
                )
                if has_diff:
                    pa_cells = '<td class="indent-2 muted"><em>↳ Period-Adjusted CCC</em></td>'
                    for pk in period_keys:
                        pa_val = ccc_pa.get(pk, None)
                        std_val = ccc_std.get(pk, None) if ccc_std else None
                        if pa_val is not None and std_val is not None and abs(float(pa_val) - float(std_val)) > 0.1:
                            pa_cells += f'<td class="number muted"><em>{format_number(pa_val, 0)} days</em></td>'
                        else:
                            pa_cells += '<td class="number muted"><em>-</em></td>'
                    body += f'<tr>{pa_cells}</tr>'
        
        # WCR row - v7.7/v7.6: single "WC Requirement"; v7.2: "WC Requirement (Standard)" with optional PA sub-row
        schema = detect_schema_version(data)
        is_single_wcr = schema in ["v7.7"]  # v7.6/v7.7/v7.8 uses single values (no standard/adjusted split)
        
        wcr_label = "WC Requirement" if is_single_wcr else "WC Requirement (Standard)"
        cells = f'<td><strong>{wcr_label}</strong></td>'
        for pk in period_keys:
            req = wcr_values_standard.get(pk, calc_details.get(pk, {}).get("wc_requirement", 0) if calc_details else 0)
            status_class = "negative" if req > 0 else "positive"
            cells += f'<td class="number {status_class}"><strong>{format_number(req)}</strong></td>'
        body += f'<tr class="grand-total-row">{cells}</tr>'
        
        # v7.2: Show period-adjusted WCR row if available and differs
        if wcr_values_period_adjusted:
            has_diff = any(
                wcr_values_period_adjusted.get(pk) is not None and wcr_values_standard.get(pk) is not None
                and abs(float(wcr_values_period_adjusted.get(pk, 0)) - float(wcr_values_standard.get(pk, 0))) > 0.1
                for pk in period_keys
            )
            if has_diff:
                pa_cells = '<td class="indent-1 muted"><em>↳ WCR (Period-Adjusted)</em></td>'
                for pk in period_keys:
                    pa_val = wcr_values_period_adjusted.get(pk, None)
                    std_val = wcr_values_standard.get(pk, None)
                    if pa_val is not None and std_val is not None and abs(float(pa_val) - float(std_val)) > 0.1:
                        pa_cells += f'<td class="number muted"><em>{format_number(pa_val)}</em></td>'
                    else:
                        pa_cells += '<td class="number muted"><em>-</em></td>'
                body += f'<tr>{pa_cells}</tr>'
        
        # BACKWARD COMPATIBILITY: Render WCR interpretation if present (v6.16 and earlier)
        # v6.18 removes this block, so it simply won't render for v6.18 JSON
        wcr_interp = wcr.get("interpretation", {})
        if wcr_interp:
            for pk in period_keys:
                pk_interp = wcr_interp.get(pk, {})
                if isinstance(pk_interp, dict):
                    status = pk_interp.get("status", "")
                    explanation = pk_interp.get("explanation", "")
                    if explanation:
                        status_icon = "🟢" if status == "self_funding" else "🔴"
                        body += f'<tr><td colspan="{len(period_keys)+1}" class="indent-2 muted"><em>{status_icon} {get_period_label(data, pk)}: {explanation}</em></td></tr>'
    
    # v6.15+: WC Assessment Summary (v6.18: CCC is PRIMARY, OWC is SUPPORTING)
    wc_assess = wc.get("working_capital_assessment", {})
    wc_assess_html = ""
    if wc_assess:
        needs_wc = wc_assess.get("needs_wc_facility", None)
        owc_status = wc_assess.get("owc_status", "")
        ccc_status = wc_assess.get("ccc_status", "")
        rec_type = wc_assess.get("recommended_facility_type", "")
        rec_amount = wc_assess.get("recommended_facility_amount", 0)
        wc_rationale = wc_assess.get("rationale", "")
        
        if needs_wc is not None:
            assess_class = "warning" if needs_wc else "success"
            needs_icon = "⚠️ Yes - External WC facility needed" if needs_wc else "✅ No - Self-funding position"
            wc_assess_html = f'<div class="note-box {assess_class}">'
            wc_assess_html += f'<strong>WC Facility Needed:</strong> {needs_icon}<br>'
            
            # v6.18: Show CCC as PRIMARY and OWC as SUPPORTING with conflict detection
            ccc_owc_conflict = (ccc_status and owc_status and 
                                ccc_status.lower() != owc_status.lower())
            
            if ccc_status:
                ccc_icon = "🔴" if ccc_status.lower() == "positive" else "🟢"
                ccc_label = f'{ccc_icon} CCC Status (PRIMARY): <strong>{ccc_status.upper()}</strong>'
                wc_assess_html += f'{ccc_label}'
            if owc_status:
                owc_icon = "🔴" if owc_status.lower() == "positive" else "🟢"
                owc_label = f' | {owc_icon} OWC Status (Supporting): <strong>{owc_status.upper()}</strong>'
                wc_assess_html += f'{owc_label}'
            
            # Show conflict indicator if CCC and OWC disagree
            if ccc_owc_conflict:
                wc_assess_html += '<br><span style="color:var(--warn-text);font-weight:600;">⚡ CCC/OWC signals differ — CCC takes precedence (see rationale)</span>'
            
            wc_assess_html += '<br>'
            if rec_type and rec_type != "None required":
                wc_assess_html += f'<strong>Recommended:</strong> {rec_type}'
                if rec_amount:
                    wc_assess_html += f' ({format_number(rec_amount)})'
                wc_assess_html += '<br>'
            if wc_rationale:
                wc_assess_html += f'<em>{wc_rationale}</em>'
            wc_assess_html += '</div>'
    
    trend = wc.get("working_capital_trend", {})
    trend_html = ""
    if trend:
        direction = trend.get("direction", "")
        obs = trend.get("observations", "")
        trend_class = "success" if direction == "improving" else ("warning" if direction == "deteriorating" else "info")
        trend_html = f'<div class="note-box {trend_class}"><strong>Trend:</strong> {direction.capitalize()} - {obs}</div>'
    
    return f'''<div class="collapsible-section" id="section-wc"><button class="section-toggle" onclick="toggleSection(this)"><div class="toggle-left"><div class="toggle-icon-wrapper">💰</div><div class="toggle-text"><h3>Working Capital Analysis</h3><p>Operating WC (Supporting), CCC (Primary Driver), and WC Requirement</p></div></div><div class="toggle-arrow">▼</div></button><div class="section-content"><div class="table-card"><div class="table-wrapper"><table><thead><tr>{header_cells}</tr></thead><tbody>{body}</tbody></table></div></div>{wc_assess_html}{trend_html}</div></div>'''

def generate_funding_mismatch_section(data: Dict) -> str:
    """Generate Funding Mismatch Analysis section (v6.5 compatible)"""
    fm = data.get("funding_mismatch_analysis", {})
    if not fm:
        return ""
    
    period_keys = get_period_keys(data)
    currency_unit = get_currency_unit(data)
    
    content_html = ""
    
    # Terminology definitions (v6.8 feature)
    terminology = fm.get("terminology", {})
    if terminology:
        content_html += '<div class="card"><h2>📖 Terminology</h2><div class="note-box info">'
        for term, definition in terminology.items():
            if not term.startswith("_"):  # Skip comment fields
                content_html += f'<p><strong>{term}:</strong> {definition}</p>'
        content_html += '</div></div>'
    
    # Layer 1: Gap Identification
    layer1 = fm.get("layer_1_gap_identification", {})
    if layer1:
        content_html += '<div class="card"><h2>📐 Layer 1: Gap Identification</h2>'
        
        header_cells = "<th>Component</th>"
        for pk in period_keys:
            header_cells += f'<th class="number">{get_period_label(data, pk)}</th>'
        
        body = f'<tr class="section-header-row"><td colspan="{len(period_keys)+1}">FUNDING GAP ANALYSIS</td></tr>'
        
        cells = '<td class="indent-1">Non-Current Assets (NCA)</td>'
        for pk in period_keys:
            # Handle both field names: non_current_assets and non_current_assets_nca
            pk_data = layer1.get(pk, {})
            val = pk_data.get("non_current_assets", pk_data.get("non_current_assets_nca", 0))
            cells += f'<td class="number">{format_number(val)}</td>'
        body += f'<tr>{cells}</tr>'
        
        cells = '<td class="indent-1">Long-Term Funding (Equity + NCL)</td>'
        for pk in period_keys:
            lt = layer1.get(pk, {}).get("long_term_funding", {})
            val = lt.get("total", 0) if isinstance(lt, dict) else lt
            cells += f'<td class="number">{format_number(val)}</td>'
        body += f'<tr>{cells}</tr>'
        
        cells = '<td><strong>Funding Gap</strong></td>'
        for pk in period_keys:
            val = layer1.get(pk, {}).get("funding_gap", 0)
            status_class = "negative" if val > 0 else "positive"
            cells += f'<td class="number {status_class}"><strong>{format_number(val)}</strong></td>'
        body += f'<tr class="total-row">{cells}</tr>'
        
        cells = '<td class="indent-1">Gap % of NCA</td>'
        for pk in period_keys:
            val = layer1.get(pk, {}).get("gap_as_percentage_of_nca", 0)
            cells += f'<td class="number">{format_percentage(val)}</td>'
        body += f'<tr>{cells}</tr>'
        
        cells = '<td class="indent-1">Status</td>'
        for pk in period_keys:
            status = layer1.get(pk, {}).get("status", "unknown")
            status_map = {
                "matched": ("status-matched", "✅ Matched"),
                "minor_mismatch": ("status-minor", "⚠️ Minor"),
                "moderate_mismatch": ("status-moderate", "⚠️ Moderate"),
                "severe_mismatch": ("status-severe", "❌ Severe")
            }
            cls, label = status_map.get(status, ("", status))
            cells += f'<td class="number"><span class="status-pill {cls}">{label}</span></td>'
        body += f'<tr>{cells}</tr>'
        
        content_html += f'<div class="table-wrapper"><table><thead><tr>{header_cells}</tr></thead><tbody>{body}</tbody></table></div></div>'
    
    # Overall Assessment
    assessment = fm.get("funding_structure_assessment", {})
    if assessment:
        rating = assessment.get("overall_sustainability_rating", "Unknown")
        rating_map = {"Sustainable": "success", "Adequate": "info", "Fragile": "warning", "Unsustainable": "danger", "Critical": "danger"}
        rating_class = rating_map.get(rating, "info")
        
        content_html += f'<div class="card"><h2>⚖️ Funding Structure Assessment</h2>'
        content_html += f'<div class="note-box {rating_class}"><strong>Sustainability Rating:</strong> {rating}</div>'
        
        flags = assessment.get("risk_flags", [])
        if flags:
            content_html += '<h4>Risk Flags:</h4><ul>'
            for flag in flags:
                if isinstance(flag, dict):
                    sev = flag.get("severity", "medium")
                    content_html += f'<li><strong>{flag.get("flag", "")}</strong> ({sev.upper()}): {flag.get("description", "")}</li>'
                elif isinstance(flag, str):
                    # v6.15/v6.16: Plain string risk flags
                    content_html += f'<li>{flag}</li>'
            content_html += '</ul>'
        content_html += '</div>'
    
    return f'''<div class="collapsible-section" id="section-funding"><button class="section-toggle" onclick="toggleSection(this)"><div class="toggle-left"><div class="toggle-icon-wrapper">🏗️</div><div class="toggle-text"><h3>Funding Mismatch Analysis</h3><p>Gap identification, source decomposition, and funding structure</p></div></div><div class="toggle-arrow">▼</div></button><div class="section-content">{content_html}</div></div>'''

def generate_funding_profile_section(data: Dict) -> str:
    """NEW in v5.0: Generate Funding Profile section (v6.4)"""
    fp = data.get("funding_profile", {})
    if not fp:
        return ""
    
    content_html = ""
    
    # Existing Facilities
    facilities = fp.get("existing_facilities_identified", {})
    if facilities:
        content_html += '<div class="card"><h2>🏦 Existing Facilities</h2>'
        body = '<tr><th>Facility</th><th class="number">Current</th><th class="number">Non-Current</th><th class="number">Total</th></tr>'
        
        for key in ["hire_purchase", "term_loan", "overdraft", "trade_financing", 
                    "revolving_credit", "bankers_guarantee", "invoice_financing",
                    "business_financing_i", "related_party_borrowings"]:
            item = facilities.get(key, {})
            if item:
                current = item.get("current_portion", item.get("amount", 0))
                non_current = item.get("non_current_portion", 0)
                total = item.get("total", current + non_current)
                if total != 0:
                    body += f'<tr><td>{snake_to_title(key)}</td><td class="number">{format_number(current)}</td><td class="number">{format_number(non_current)}</td><td class="number"><strong>{format_number(total)}</strong></td></tr>'
        
        # Also iterate any facility keys NOT in the known list above (catch-all for custom facilities)
        known_keys = {"hire_purchase", "term_loan", "overdraft", "trade_financing", 
                      "revolving_credit", "bankers_guarantee", "invoice_financing",
                      "business_financing_i", "related_party_borrowings", "total_borrowings"}
        for key, item in facilities.items():
            if key in known_keys or not isinstance(item, dict):
                continue
            current = item.get("current_portion", item.get("amount", 0))
            non_current = item.get("non_current_portion", 0)
            total = item.get("total", current + non_current)
            if total != 0:
                body += f'<tr><td>{snake_to_title(key)}</td><td class="number">{format_number(current)}</td><td class="number">{format_number(non_current)}</td><td class="number"><strong>{format_number(total)}</strong></td></tr>'
        
        total_borrowings = facilities.get("total_borrowings", 0)
        body += f'<tr class="grand-total-row"><td><strong>Total Borrowings</strong></td><td></td><td></td><td class="number"><strong>{format_number(total_borrowings)}</strong></td></tr>'
        content_html += f'<div class="table-wrapper"><table><tbody>{body}</tbody></table></div></div>'
    
    # Suitability Assessment
    suit_fin = fp.get("suitability_vs_financial_condition", {})
    if suit_fin:
        guidance = suit_fin.get("general_guidance", [])
        if guidance:
            content_html += '<div class="card"><h2>📋 Facility Guidance</h2><ul>'
            for g in guidance:
                content_html += f'<li>{g}</li>'
            content_html += '</ul></div>'
    
    return f'''<div class="collapsible-section" id="section-profile"><button class="section-toggle" onclick="toggleSection(this)"><div class="toggle-left"><div class="toggle-icon-wrapper">🎯</div><div class="toggle-text"><h3>Funding Profile</h3><p>Existing facilities and suitability assessment</p></div></div><div class="toggle-arrow">▼</div></button><div class="section-content">{content_html}</div></div>'''

def generate_dscr_section(data: Dict) -> str:
    """Generate detailed DSCR Analysis section - v6.5 compatible with facility classification"""
    dscr = data.get("dscr_analysis", {})
    if not dscr:
        return ""
    
    period_keys = get_period_keys(data)
    calc = dscr.get("calculation", {})
    if not calc:
        return ""
    
    content_html = ""
    
    # Facility Classification (v6.8 feature)
    facility_class = dscr.get("facility_classification", {})
    if facility_class:
        content_html += '<div class="card"><h2>🏦 Facility Classification</h2>'
        
        term_fac = facility_class.get("term_facilities", {})
        if term_fac:
            content_html += '<div class="note-box info">'
            content_html += f'<p><strong>Term Facilities</strong> (Principal + Interest in DSCR): {term_fac.get("description", "")}</p>'
            facilities_list = term_fac.get("facilities", [])
            if facilities_list:
                content_html += f'<p>Includes: {", ".join(facilities_list)}</p>'
            current_portions = term_fac.get("current_portions", {})
            if current_portions:
                total = current_portions.get("total", 0)
                content_html += f'<p><strong>Total Term Current Portion:</strong> {format_number(total)}</p>'
            content_html += '</div>'
        
        rev_fac = facility_class.get("revolving_facilities", {})
        if rev_fac:
            content_html += '<div class="note-box warning">'
            content_html += f'<p><strong>Revolving Facilities</strong> (Interest ONLY in DSCR): {rev_fac.get("description", "")}</p>'
            facilities_list = rev_fac.get("facilities", [])
            if facilities_list:
                content_html += f'<p>Includes: {", ".join(facilities_list)}</p>'
            amounts = rev_fac.get("amounts", {})
            if amounts:
                total = amounts.get("total", 0)
                content_html += f'<p><strong>Total Revolving:</strong> {format_number(total)} (excluded from principal)</p>'
            content_html += '</div>'
        
        content_html += '</div>'
    
    # DSCR Calculation Table
    header_cells = "<th>Component</th>"
    for pk in period_keys:
        header_cells += f'<th class="number">{get_period_label(data, pk)}</th>'
    
    body = ""
    
    # EBITDA
    body += f'<tr class="section-header-row"><td colspan="{len(period_keys)+1}">EBITDA</td></tr>'
    cells = '<td class="indent-1">EBITDA</td>'
    for pk in period_keys:
        pk_calc = calc.get(pk, {})
        val = pk_calc.get("ebitda", pk_calc.get("ebitda_annualized", 0))
        cells += f'<td class="number">{format_number(val)}</td>'
    body += f'<tr>{cells}</tr>'
    
    # Check if annualized EBITDA is shown separately
    has_annualized = any(calc.get(pk, {}).get("ebitda_annualized") for pk in period_keys)
    if has_annualized:
        cells = '<td class="indent-1">EBITDA (Annualized)</td>'
        for pk in period_keys:
            val = calc.get(pk, {}).get("ebitda_annualized", 0)
            if val:
                cells += f'<td class="number">{format_number(val)}</td>'
            else:
                cells += '<td class="number">-</td>'
        body += f'<tr>{cells}</tr>'
    
    # Debt Service
    body += f'<tr class="section-header-row"><td colspan="{len(period_keys)+1}">DEBT SERVICE</td></tr>'
    
    # Principal Repayment - show breakdown if available
    cells = '<td class="indent-1">Principal Repayment (Term Facilities)</td>'
    for pk in period_keys:
        ds = calc.get(pk, {}).get("debt_service", {})
        pr = ds.get("principal_repayment", {})
        if isinstance(pr, dict):
            val = pr.get("total_principal", 0)
        else:
            val = pr
        cells += f'<td class="number">{format_number(val)}</td>'
    body += f'<tr>{cells}</tr>'
    
    # Show excluded revolving if available
    has_excluded = any(
        calc.get(pk, {}).get("debt_service", {}).get("principal_repayment", {}).get("excluded_revolving", 0) 
        for pk in period_keys
    )
    if has_excluded:
        cells = '<td class="indent-2 muted">Excluded: Revolving Facilities</td>'
        for pk in period_keys:
            ds = calc.get(pk, {}).get("debt_service", {})
            pr = ds.get("principal_repayment", {})
            val = pr.get("excluded_revolving", 0) if isinstance(pr, dict) else 0
            cells += f'<td class="number muted">{format_number(val)}</td>'
        body += f'<tr>{cells}</tr>'
    
    cells = '<td class="indent-1">Interest Expense</td>'
    for pk in period_keys:
        ds = calc.get(pk, {}).get("debt_service", {})
        val = ds.get("interest_expense", ds.get("interest_expense_annualized", 0))
        cells += f'<td class="number">{format_number(val)}</td>'
    body += f'<tr>{cells}</tr>'
    
    cells = '<td><strong>Total Debt Service</strong></td>'
    for pk in period_keys:
        ds = calc.get(pk, {}).get("debt_service", {})
        val = ds.get("total_debt_service", 0)
        cells += f'<td class="number"><strong>{format_number(val)}</strong></td>'
    body += f'<tr class="total-row">{cells}</tr>'
    
    # DSCR
    body += f'<tr class="section-header-row"><td colspan="{len(period_keys)+1}">DSCR</td></tr>'
    cells = '<td><strong>DSCR</strong></td>'
    for pk in period_keys:
        val = calc.get(pk, {}).get("dscr", 0)
        val_class = "positive" if val >= 1.25 else ("warning" if val >= 1.0 else "negative")
        cells += f'<td class="number {val_class}"><strong>{format_number(val, 2)}x</strong></td>'
    body += f'<tr class="grand-total-row">{cells}</tr>'
    
    notes = dscr.get("notes", "")
    notes_html = f'<div class="note-box info">{notes}</div>' if notes else ""
    benchmark_html = '<div class="note-box warning"><strong>Benchmark:</strong> DSCR ≥ 1.25x (Banking Standard) | Minimum: ≥ 1.00x<br><strong>Note:</strong> DSCR = EBITDA ÷ (Term Facility Principal + All Interest). Revolving facilities contribute to interest but NOT principal.</div>'
    
    # v6.15/v6.16: DSCR Assessment narrative (MANDATORY field)
    assessment_text = dscr.get("assessment", "")
    assessment_html = ""
    if assessment_text:
        assessment_html = f'<div class="card"><h2>📋 DSCR Assessment</h2><div class="note-box info">{assessment_text}</div></div>'
    
    return f'''<div class="collapsible-section" id="section-dscr"><button class="section-toggle" onclick="toggleSection(this)"><div class="toggle-left"><div class="toggle-icon-wrapper">📐</div><div class="toggle-text"><h3>DSCR Analysis</h3><p>Debt service coverage ratio calculation (Banking Standard)</p></div></div><div class="toggle-arrow">▼</div></button><div class="section-content">{content_html}<div class="table-card"><div class="table-wrapper"><table><thead><tr>{header_cells}</tr></thead><tbody>{body}</tbody></table></div></div>{notes_html}{benchmark_html}{assessment_html}</div></div>'''

def generate_tnw_section(data: Dict) -> str:
    """Generate TNW Analysis section - v6.5 compatible with both Original and Adjusted TNW"""
    period_keys = get_period_keys(data)
    tnw = data.get("tnw_analysis", {})
    
    if not tnw: return ""
    
    header_cells = "<th>Component</th>"
    for pk in period_keys:
        header_cells += f'<th class="number">{get_period_label(data, pk)}</th>'
    
    body = ""
    
    # Try v6.5 calculation structure first
    calculation = tnw.get("calculation", {})
    if calculation and any(pk in calculation for pk in period_keys):
        # v6.5 structure: calculation per period
        body += f'<tr class="section-header-row"><td colspan="{len(period_keys)+1}">TNW CALCULATION</td></tr>'
        
        # Original TNW (Total Equity)
        cells = '<td class="indent-1">Total Shareholders\' Equity (Original TNW)</td>'
        for pk in period_keys:
            val = calculation.get(pk, {}).get("original_tnw", 0)
            cells += f'<td class="number">{format_number(val)}</td>'
        body += f'<tr>{cells}</tr>'
        
        # Adjustments
        body += f'<tr class="subsection-header-row"><td colspan="{len(period_keys)+1}">Less: Adjustments</td></tr>'
        
        # Less Intangibles
        cells = '<td class="indent-2">Intangible Assets</td>'
        for pk in period_keys:
            adj = calculation.get(pk, {}).get("adjustments", {})
            val = adj.get("less_intangibles", 0)
            cells += f'<td class="number">{format_number(val)}</td>'
        body += f'<tr>{cells}</tr>'
        
        # Less Due from Directors
        cells = '<td class="indent-2">Due from Directors</td>'
        for pk in period_keys:
            adj = calculation.get(pk, {}).get("adjustments", {})
            val = adj.get("less_due_from_directors", 0)
            cells += f'<td class="number">{format_number(val)}</td>'
        body += f'<tr>{cells}</tr>'
        
        # Less Due from Related Companies
        cells = '<td class="indent-2">Due from Related Companies</td>'
        for pk in period_keys:
            adj = calculation.get(pk, {}).get("adjustments", {})
            val = adj.get("less_due_from_related_companies", 0)
            cells += f'<td class="number">{format_number(val)}</td>'
        body += f'<tr>{cells}</tr>'
        
        # Total Adjustments
        cells = '<td class="indent-1"><strong>Total Adjustments</strong></td>'
        for pk in period_keys:
            adj = calculation.get(pk, {}).get("adjustments", {})
            val = adj.get("total_adjustments", 0)
            cells += f'<td class="number"><strong>{format_number(val)}</strong></td>'
        body += f'<tr class="total-row">{cells}</tr>'
        
        # Adjusted TNW
        cells = '<td><strong>Adjusted TNW</strong></td>'
        for pk in period_keys:
            val = calculation.get(pk, {}).get("adjusted_tnw", 0)
            cells += f'<td class="number"><strong>{format_number(val)}</strong></td>'
        body += f'<tr class="grand-total-row">{cells}</tr>'
    
    else:
        # Fallback to legacy components structure
        components = tnw.get("components", {})
        if components:
            for key, item in components.items():
                if isinstance(item, dict) and any(get_value_from_item(item, pk, 0) != 0 for pk in period_keys):
                    cells = f'<td class="indent-1">{get_display_name(item, key)}</td>'
                    for pk in period_keys: 
                        val = get_value_from_item(item, pk, None); cells += f'<td class="number">{format_number_or_dash(val)}</td>'
                    body += f'<tr>{cells}</tr>'
        
        # Summary (Adjusted TNW)
        summary = tnw.get("summary", {})
        if summary:
            # Try adjusted_tnw first (v6.5), then values (legacy), then direct period keys
            cells = '<td><strong>Adjusted TNW</strong></td>'
            for pk in period_keys:
                adjusted_tnw = summary.get("adjusted_tnw", {})
                if isinstance(adjusted_tnw, dict) and pk in adjusted_tnw:
                    val = adjusted_tnw.get(pk, 0)
                else:
                    val = get_value_from_item(summary, pk, 0)
                cells += f'<td class="number"><strong>{format_number(val)}</strong></td>'
            body += f'<tr class="grand-total-row">{cells}</tr>'
    
    # Assessment notes
    assessment = tnw.get("assessment", {})
    assessment_html = ""
    if assessment:
        notes = assessment.get("notes", "")
        trend = assessment.get("tnw_trend", "")
        if notes or trend:
            assessment_html = f'<div class="note-box info"><strong>Assessment:</strong> {notes} Trend: {trend.capitalize()}</div>'
    
    return f'''<div class="collapsible-section" id="section-tnw"><button class="section-toggle" onclick="toggleSection(this)"><div class="toggle-left"><div class="toggle-icon-wrapper">🏦</div><div class="toggle-text"><h3>Tangible Net Worth (TNW) Analysis</h3><p>Banking perspective: adjusted equity position</p></div></div><div class="toggle-arrow">▼</div></button><div class="section-content"><div class="table-card"><div class="table-wrapper"><table><thead><tr>{header_cells}</tr></thead><tbody>{body}</tbody></table></div></div>{assessment_html}</div></div>'''

def generate_integrity_section(data: Dict) -> str:
    period_keys = get_period_keys(data)
    integrity = data.get("integrity_check", {})
    
    if not integrity: return ""
    
    header_cells = "<th>Check</th>"
    for pk in period_keys:
        header_cells += f'<th class="number">{get_period_label(data, pk)}</th>'
    
    body = ""
    
    bs_verify = integrity.get("balance_sheet_verification", {})
    if bs_verify:
        # Total Assets
        cells = '<td class="indent-1">Total Assets</td>'
        for pk in period_keys:
            val = bs_verify.get(pk, {}).get("total_assets", 0)
            cells += f'<td class="number">{format_number(val)}</td>'
        body += f'<tr>{cells}</tr>'
        
        # Total Equity & Liabilities
        cells = '<td class="indent-1">Total Equity & Liabilities</td>'
        for pk in period_keys:
            val = bs_verify.get(pk, {}).get("total_equity_and_liabilities", 0)
            cells += f'<td class="number">{format_number(val)}</td>'
        body += f'<tr>{cells}</tr>'
        
        # Variance
        cells = '<td class="indent-1"><strong>Variance</strong></td>'
        for pk in period_keys:
            val = bs_verify.get(pk, {}).get("variance", 0)
            balanced = bs_verify.get(pk, {}).get("balanced", False)
            status_class = "positive" if balanced else "negative"
            cells += f'<td class="number {status_class}"><strong>{format_number(val)}</strong></td>'
        body += f'<tr class="total-row">{cells}</tr>'
        
        # Status
        cells = '<td class="indent-1">Status</td>'
        for pk in period_keys:
            balanced = bs_verify.get(pk, {}).get("balanced", False)
            status = "✅ Balanced" if balanced else "❌ Imbalanced"
            status_class = "positive" if balanced else "negative"
            cells += f'<td class="number {status_class}">{status}</td>'
        body += f'<tr>{cells}</tr>'
    
    return f'''<div class="collapsible-section" id="section-integrity"><button class="section-toggle" onclick="toggleSection(this)"><div class="toggle-left"><div class="toggle-icon-wrapper">✅</div><div class="toggle-text"><h3>Integrity Check</h3><p>Balance sheet verification and data quality</p></div></div><div class="toggle-arrow">▼</div></button><div class="section-content"><div class="table-card"><div class="table-wrapper"><table><thead><tr>{header_cells}</tr></thead><tbody>{body}</tbody></table></div></div></div></div>'''

def generate_summary_section(data: Dict) -> str:
    summary = data.get("analysis_summary", {})
    if not summary: return ""
    
    # Key Observations (v6.4 - 9 fields)
    key_obs = summary.get("key_observations", {})
    key_obs_html = ""
    if key_obs:
        key_obs_html = '<div class="card"><h2>📊 Key Observations</h2><div class="key-obs-grid">'
        obs_fields = [
            ("revenue_trend", "Revenue Trend"),
            ("profitability_trend", "Profitability Trend"),
            ("liquidity_position", "Liquidity Position"),
            ("working_capital_cycle", "Working Capital Cycle"),
            ("debt_structure", "Debt Structure"),
            ("funding_position", "Funding Position"),
            ("asset_base", "Asset Base"),
            ("related_party_exposure", "Related Party Exposure"),
            ("dividend_policy", "Dividend Policy")
        ]
        for field_key, field_label in obs_fields:
            val = key_obs.get(field_key, "")
            if val:
                key_obs_html += f'<div class="key-obs-item"><h4>{field_label}</h4><p>{val}</p></div>'
        key_obs_html += '</div></div>'
    
    pos = summary.get("positive_indicators", summary.get("strengths", []))
    pos_html = ""
    for i in pos:
        if isinstance(i, dict): 
            pos_html += f'<li><strong>{i.get("title", "")}:</strong> {i.get("description", "")}</li>'
        else: 
            pos_html += f'<li>{i}</li>'
    if not pos_html: 
        pos_html = "<li>No positive indicators noted</li>"
    
    # Areas of concern with severity badges
    conc = summary.get("areas_of_concern", summary.get("concerns", summary.get("weaknesses", [])))
    conc_html = ""
    for i in conc:
        if isinstance(i, dict):
            severity = i.get("severity", "medium")
            severity_class = f"severity-{severity}"
            conc_html += f'<li><strong>{i.get("title", "")}:</strong> {i.get("description", "")} <span class="severity-badge {severity_class}">{severity.upper()}</span></li>'
        else: 
            conc_html += f'<li>{i}</li>'
    if not conc_html: 
        conc_html = "<li>No significant concerns noted</li>"
    
    reco = summary.get("recommendations", [])
    if isinstance(reco, list):
        # v6.15/v6.16: Priority is a string (HIGH/MEDIUM/LOW), not a number
        priority_order = {"HIGH": 1, "MEDIUM": 2, "LOW": 3, "high": 1, "medium": 2, "low": 3}
        reco = sorted(reco, key=lambda x: priority_order.get(x.get("priority", "LOW"), 99) if isinstance(x, dict) else 99)
    reco_html = ""
    for i in reco:
        if isinstance(i, dict):
            priority = i.get("priority", "")
            area = i.get("area", i.get("title", ""))
            action = i.get("action", i.get("description", ""))
            reco_html += f'<li><strong>[P{priority}] {area}:</strong> {action}</li>'
        else: 
            reco_html += f'<li>{i}</li>'
    if not reco_html: 
        reco_html = "<li>No specific recommendations</li>"
    
    # Facility suitability summary (v6.4, enhanced v6.15/v6.16)
    facility_summary = summary.get("facility_suitability_summary", {})
    facility_html = ""
    if facility_summary:
        facility_html = '<div class="facility-box"><div class="obs-title"><span>🏦</span><span>Facility Suitability Summary</span></div>'
        appropriate = facility_summary.get("existing_facilities_appropriate", None)
        if appropriate is not None:
            if appropriate == True or appropriate == "true":
                status = "✅ Yes"
                status_class = "success"
            else:
                status = "❌ No"
                status_class = "danger"
            facility_html += f'<p><strong>Existing Facilities Appropriate:</strong> {status}</p>'
        
        # v6.15/v6.16: Rationale for facility appropriateness
        rationale = facility_summary.get("rationale", "")
        if rationale:
            facility_html += f'<div class="note-box info" style="margin:10px 0;"><strong>Rationale:</strong> {rationale}</div>'
        
        # v6.15/v6.16: Existing Facility Concerns (MANDATORY when appropriate = false)
        concerns = facility_summary.get("existing_facility_concerns", [])
        if concerns:
            facility_html += '<div class="note-box warning" style="margin:10px 0;"><strong>⚠️ Facility Concerns:</strong><ul style="margin:8px 0 0;padding-left:20px;">'
            for c in concerns:
                facility_html += f'<li>{c}</li>'
            facility_html += '</ul></div>'
        
        # v6.15+: Working Capital Assessment embedded in facility summary
        # v6.18: CCC is PRIMARY driver, OWC is SUPPORTING indicator
        wc_assessment = facility_summary.get("working_capital_assessment", {})
        if wc_assessment:
            owc_status = wc_assessment.get("owc_status", "")
            ccc_status = wc_assessment.get("ccc_status", "")
            wcr_amount = wc_assessment.get("wcr_amount", wc_assessment.get("wcr_amount_standard", 0))
            wcr_amount_pa = wc_assessment.get("wcr_amount_period_adjusted", 0)
            needs_wc = wc_assessment.get("needs_wc_facility", None)
            wc_rationale = wc_assessment.get("rationale", "")
            
            # Detect CCC/OWC conflict
            ccc_owc_conflict = (ccc_status and owc_status and 
                                ccc_status.lower() != owc_status.lower())
            
            facility_html += '<div style="margin:10px 0;padding:12px 16px;border-radius:12px;background:var(--info-soft);border:1px solid var(--info-border);">'
            facility_html += '<strong>📊 Working Capital Assessment:</strong><br>'
            if ccc_status:
                ccc_icon = "🔴" if ccc_status.lower() == "positive" else "🟢"
                facility_html += f'{ccc_icon} CCC Status (PRIMARY): <strong>{ccc_status.upper()}</strong> | '
            if owc_status:
                owc_icon = "🔴" if owc_status.lower() == "positive" else "🟢"
                facility_html += f'{owc_icon} OWC Status (Supporting): <strong>{owc_status.upper()}</strong>'
            if wcr_amount != 0:
                facility_html += f' | WCR: <strong>{format_number(wcr_amount)}</strong>'
                if wcr_amount_pa != 0 and wcr_amount_pa != wcr_amount:
                    facility_html += f' (Period-Adj: {format_number(wcr_amount_pa)})'
                facility_html += '<br>'
            else:
                facility_html += '<br>'
            if ccc_owc_conflict:
                facility_html += '<span style="color:var(--warn-text);font-weight:600;">⚡ CCC/OWC signals differ — CCC takes precedence</span><br>'
            if needs_wc is not None:
                needs_icon = "⚠️ Yes" if needs_wc else "✅ No"
                facility_html += f'Needs WC Facility: <strong>{needs_icon}</strong><br>'
            if wc_rationale:
                facility_html += f'<em>{wc_rationale}</em>'
            facility_html += '</div>'
        
        to_consider = facility_summary.get("potential_facilities_to_consider", [])
        if to_consider:
            facility_html += f'<p><strong>Facilities to Consider:</strong> {", ".join(to_consider)}</p>'
        
        to_avoid = facility_summary.get("facilities_to_avoid", [])
        if to_avoid:
            facility_html += f'<p><strong>Facilities to Avoid:</strong> {", ".join(to_avoid)}</p>'
        
        conditions = facility_summary.get("key_conditions", [])
        if conditions:
            facility_html += '<p><strong>Key Conditions:</strong></p><ul>'
            for c in conditions:
                facility_html += f'<li>{c}</li>'
            facility_html += '</ul>'
        facility_html += '</div>'
    
    return f'''<div class="collapsible-section" id="section-summary"><button class="section-toggle active" onclick="toggleSection(this)"><div class="toggle-left"><div class="toggle-icon-wrapper">🧭</div><div class="toggle-text"><h3>Summary & Key Observations</h3><p>Analysis highlights, concerns, and strategic recommendations</p></div></div><div class="toggle-arrow">▼</div></button><div class="section-content show">{key_obs_html}<div class="obs-grid"><div class="obs-box positive"><div class="obs-title"><span>✅</span><span>Positive Trends</span></div><ul class="obs-list">{pos_html}</ul></div><div class="obs-box caution"><div class="obs-title"><span>⚠️</span><span>Areas Requiring Attention</span></div><ul class="obs-list">{conc_html}</ul></div></div><div class="reco-box"><div class="obs-title"><span>🎯</span><span>Strategic Recommendations</span></div><ol>{reco_html}</ol></div>{facility_html}</div></div>'''

def generate_notes_section(data: Dict) -> str:
    period_keys = get_period_keys(data)
    schema = detect_schema_version(data)
    company = get_company_info(data)
    
    docs_html = ""
    for pk in period_keys:
        plabel = get_period_label(data, pk)
        ptype = get_period_type(data, pk)
        dt = "Audited" if ptype == "audited" else "Management Accounts"
        docs_html += f"• {plabel}: {dt}<br>"
    
    sme_note = ""
    if company.get("sme_qualified"): 
        sme_note = f'<br><strong>SME Status:</strong> Qualified ({company.get("sme_qualification_note", "")})'
    
    return f'''<div class="collapsible-section" id="section-notes"><button class="section-toggle" onclick="toggleSection(this)"><div class="toggle-left"><div class="toggle-icon-wrapper">📋</div><div class="toggle-text"><h3>Notes on Financial Reports</h3><p>Source documents and analysis basis</p></div></div><div class="toggle-arrow">▼</div></button><div class="section-content"><div class="note-box info"><strong>Source Documents:</strong><br>{docs_html}<br><strong>Schema Version:</strong> {schema}{sme_note}</div></div></div>'''

def generate_audit_opinion_section(data: Dict) -> str:
    """Generate Audit Opinion section - v6.11 feature"""
    company = get_company_info(data)
    audit_opinion = company.get("audit_opinion", {})
    
    # If no audit_opinion data, return empty string (backward compatible)
    if not audit_opinion:
        return ""
    
    period_keys = get_period_keys(data)
    
    content_html = '<div class="audit-opinion-grid">'
    
    has_any_opinion = False
    for pk in period_keys:
        opinion_data = audit_opinion.get(pk, {})
        if not isinstance(opinion_data, dict):
            continue
        
        opinion_type = opinion_data.get("opinion_type", "Unknown")
        auditor_name = opinion_data.get("auditor_name", "N/A")
        audit_firm_number = opinion_data.get("audit_firm_number", "")
        date_signed = opinion_data.get("date_signed", "N/A")
        emphasis_of_matter = opinion_data.get("emphasis_of_matter")
        key_audit_matters = opinion_data.get("key_audit_matters", [])
        going_concern_note = opinion_data.get("going_concern_note", False)
        
        has_any_opinion = True
        
        # Determine opinion class and badge
        opinion_lower = opinion_type.lower()
        if "unqualified" in opinion_lower:
            opinion_class = "clean"
            badge_class = "clean"
            if "restated" in opinion_lower:
                badge_text = "✓ UNQUALIFIED (RESTATED)"
            else:
                badge_text = "✓ UNQUALIFIED"
        elif opinion_lower == "qualified":
            opinion_class = "qualified"
            badge_class = "qualified"
            badge_text = "⚠ QUALIFIED"
        elif opinion_type.lower() == "adverse":
            opinion_class = "adverse"
            badge_class = "adverse"
            badge_text = "✗ ADVERSE"
        elif opinion_type.lower() == "disclaimer":
            opinion_class = "adverse"
            badge_class = "disclaimer"
            badge_text = "✗ DISCLAIMER"
        else:
            opinion_class = "clean"
            badge_class = "clean"
            badge_text = opinion_type.upper()
        
        plabel = get_period_label(data, pk)
        
        content_html += f'''<div class="audit-opinion-item {opinion_class}">
            <h4>{plabel} <span class="opinion-badge {badge_class}">{badge_text}</span></h4>
            <div class="detail"><strong>Auditor:</strong> {auditor_name}</div>'''
        
        if audit_firm_number:
            content_html += f'<div class="detail"><strong>Firm No:</strong> {audit_firm_number}</div>'
        
        content_html += f'<div class="detail"><strong>Date Signed:</strong> {date_signed}</div>'
        
        # Emphasis of Matter
        if emphasis_of_matter:
            content_html += f'''<div class="note-box warning" style="margin-top:10px;padding:10px 12px;">
                <strong>Emphasis of Matter:</strong><br>{emphasis_of_matter}
            </div>'''
        
        # Key Audit Matters
        if key_audit_matters and len(key_audit_matters) > 0:
            kam_html = "<br>".join([f"• {kam}" for kam in key_audit_matters])
            content_html += f'''<div class="detail" style="margin-top:8px;">
                <strong>Key Audit Matters:</strong><br>{kam_html}
            </div>'''
        
        # Going Concern Alert
        if going_concern_note:
            content_html += '''<div class="going-concern-alert">
                ⚠️ <strong>Going Concern Note:</strong> Material uncertainty regarding the company's ability to continue as a going concern.
            </div>'''
        
        content_html += '</div>'
    
    content_html += '</div>'
    
    # v7.7: Render Prior Year Adjustments if present
    prior_year_adj = company.get("prior_year_adjustments", {})
    if prior_year_adj and prior_year_adj.get("has_restatement"):
        pya_desc = prior_year_adj.get("description", "")
        adjustments_by_period = prior_year_adj.get("adjustments_by_period", {})
        
        content_html += '<div class="prior-year-adjustments" style="margin-top:20px;">'
        content_html += '<h3 style="margin:0 0 12px;color:var(--warn-text);">📝 Prior Year Adjustments</h3>'
        
        if pya_desc:
            content_html += f'<div class="note-box warning" style="margin-bottom:12px;"><strong>Restatement Description:</strong><br>{pya_desc}</div>'
        
        for adj_pk, adj_data in adjustments_by_period.items():
            if not isinstance(adj_data, dict):
                continue
            adj_label = get_period_label(data, adj_pk) if adj_pk in get_period_keys(data) else adj_pk.upper()
            line_items = adj_data.get("line_items_affected", [])
            summary = adj_data.get("summary", "")
            
            content_html += f'<div style="margin:8px 0;padding:10px 14px;border-radius:8px;background:var(--warn-soft);border:1px solid var(--warn-border);">'
            content_html += f'<strong>{adj_label}:</strong>'
            if summary:
                content_html += f'<br>{summary}'
            if line_items:
                content_html += '<ul style="margin:6px 0 0;padding-left:20px;">'
                for li in line_items:
                    content_html += f'<li>{li}</li>'
                content_html += '</ul>'
            content_html += '</div>'
        
        content_html += '</div>'
    
    if not has_any_opinion:
        return ""
    
    return f'''<div class="collapsible-section" id="section-audit"><button class="section-toggle" onclick="toggleSection(this)"><div class="toggle-left"><div class="toggle-icon-wrapper">🔍</div><div class="toggle-text"><h3>Audit Opinion</h3><p>Independent Auditors' Report summary</p></div></div><div class="toggle-arrow">▼</div></button><div class="section-content"><div class="audit-opinion-card"><h2>🔍 Audit Opinion Summary</h2>{content_html}</div></div></div>'''

def generate_footer(data: Dict) -> str:
    """Generate footer with v6.5 mandatory disclaimer and copyright"""
    schema_info = data.get("_schema_info", {})
    report_footer = data.get("report_footer", {})
    
    generated_by = schema_info.get("generated_by", "Kredit Lab")
    generated_date = schema_info.get("generation_date", datetime.now().strftime("%Y-%m-%d"))
    
    # v7.2 - Disclaimer hardcoded (not JSON-driven)
    disclaimer_text = "This report was prepared by Kredit Lab for the exclusive use of the purchasing party. It does not constitute financial advice, a loan guarantee, or a credit rating. Any recommendations contained herein are provided for informational purposes only — implementation is at the reader's sole discretion. Kredit Lab accepts no responsibility or liability for any decisions, actions, losses, or consequences arising from the use of this report by any party. No duty of care exists between Kredit Lab and any third party who may access this report."
    
    # v6.5 Copyright
    copyright_data = report_footer.get("copyright", {})
    copyright_main = copyright_data.get("main", "© 2026 Kredit Lab. All rights reserved.")
    copyright_sub = copyright_data.get("subsidiary", "Kredit Lab is a division of Capital Island Sdn. Bhd.")
    
    return f'''<div class="report-footer">
    <div class="disclaimer">
        <div class="disclaimer-title">Disclaimer</div>
        {disclaimer_text}
    </div>
    <div class="copyright">
        <div class="copyright-main">{copyright_main}</div>
        <div class="copyright-sub">{copyright_sub}</div>
    </div>
</div>
<footer><p><strong>Prepared by: {generated_by}</strong></p><p>Generated on: {generated_date}</p></footer>'''

def generate_full_html(data: Dict) -> str:
    company = get_company_info(data)
    company_name = company.get("legal_name") or company.get("name") or "Financial Report"
    return f'''<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{company_name} - Financial Statement Analysis</title>
{generate_css()}
</head>
<body>
{generate_theme_toggle_button()}
<div class="page">
{generate_header(data)}
<div class="confidential-banner">This report is confidential and prepared solely for the intended purchaser.</div>
{generate_nav_bar()}
{generate_notes_section(data)}
{generate_audit_opinion_section(data)}
{generate_pnl_table(data)}
{generate_balance_sheet_table(data)}
{generate_ratios_section(data)}
{generate_working_capital_section(data)}
{generate_funding_mismatch_section(data)}
{generate_funding_profile_section(data)}
{generate_dscr_section(data)}
{generate_tnw_section(data)}
{generate_integrity_section(data)}
{generate_summary_section(data)}
{generate_footer(data)}
</div>
{generate_javascript()}
</body>
</html>'''

def main():
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/financial-analytics.png", width=64)
        st.title("Kredit Lab")
        st.markdown("**Financial Report Generator**")
        st.markdown("---")
        st.markdown("**Version:** 7.7")
        st.markdown("**Schema:** Up to v7.9 Framework")
        st.markdown("**Currency:** From JSON")
        st.markdown("**Theme:** Dual (Light/Dark)")
        st.markdown("---")
        st.markdown("**New in v7.4:**")
        st.markdown("- 🏷️ v7.7 framework compatibility")
        st.markdown("- 📝 Prior Year Adjustments display")
        st.markdown("- ✅ WCR validation reworked")
        st.markdown("- 🔍 Restated Comparative badge")
        st.markdown("---")
        st.markdown("**From v7.3:**")
        st.markdown("- 🏷️ (Audited - Restated) label support")
        st.markdown("- ✅ WCR v7.6 single-values compat")
        st.markdown("- 🔍 v7.5/v7.6 schema detection")
        st.markdown("---")
        st.markdown("**From v7.2:**")
        st.markdown("- 🔒 Confidentiality Banner (top of report)")
        st.markdown("- 📜 Updated Legal Disclaimer (bottom of report)")
        st.markdown("---")
        st.markdown("**From v6.8:**")
        st.markdown("- 🔍 v6.19 Schema Detection")
        st.markdown("- ✅ No Breaking Changes from v6.18")
        st.markdown("---")
        st.markdown("**From v6.7:**")
        st.markdown("- 🎯 CCC PRIMARY / OWC SUPPORTING")
        st.markdown("- ⚡ CCC/OWC Conflict Detection")
        st.markdown("- 🔧 Output Optimization Support")
        st.markdown("- 📊 OWC Components Display")
        st.markdown("- 🔍 v6.18 Validation Checks")
        st.markdown("- Schema v6.17-v6.19 Detection")
        st.markdown("---")
        st.markdown("**From v6.6:**")
        st.markdown("- 📋 DSCR Assessment Narrative")
        st.markdown("- ⚠️ Risk Flags (string arrays)")
        st.markdown("- 🏦 Facility Concerns Display")
        st.markdown("- 📊 WC Assessment in Facility")
        st.markdown("- 🏷️ Period Labels with Month")
        st.markdown("- 📦 Lump Sum Line Items (-)")
        st.markdown("- 🔄 Dynamic Taxation/Facilities")
        st.markdown("---")
        st.markdown("**From v6.5:**")
        st.markdown("- 📐 Formula Display in Ratios")
        st.markdown("- 🎯 Benchmark Pass/Fail Badge")
        st.markdown("- 🔄 New Ratio Names Support")
        st.markdown("- 🔍 Audit Opinion Section")
    
    st.title("📊 Financial Report Generator")
    st.markdown("Transform JSON financial analysis into professional HTML reports")
    st.markdown("*Supports Framework v7.7 / JSON Schema v7.7 with Light & Dark mode*")
    st.markdown("---")
    
    uploaded_file = st.file_uploader("Upload JSON Financial Analysis", type=["json"])
    
    if uploaded_file is not None:
        try:
            json_content = uploaded_file.read().decode("utf-8")
            data = json.loads(json_content)
            st.success(f"✅ File loaded: {uploaded_file.name}")
            
            schema = detect_schema_version(data)
            actual_version = data.get('_schema_info', {}).get('version', schema)
            st.info(f"📋 Detected Schema: **{actual_version}**")
            
            tab1, tab2, tab3, tab4 = st.tabs(["📋 Validation", "📊 Data Preview", "🖥️ HTML Preview", "⬇️ Download"])
            
            with tab1:
                st.subheader("JSON Validation Results")
                is_valid, errors, warnings = validate_json_structure(data)
                col1, col2 = st.columns(2)
                with col1: 
                    if is_valid:
                        st.success("✅ Structure Valid")
                    else:
                        st.error("❌ Structure Invalid")
                with col2: 
                    st.metric("Errors", len(errors))
                    st.metric("Warnings", len(warnings))
                if errors:
                    st.markdown("#### ❌ Errors")
                    for err in errors: st.error(err)
                if warnings:
                    st.markdown("#### ⚠️ Warnings")
                    for warn in warnings: st.warning(warn)
                st.markdown("---")
                st.subheader("Mathematical Integrity Check")
                math_issues = check_mathematical_integrity(data)
                if math_issues:
                    for issue in math_issues: st.warning(f"⚠️ {issue}")
                else: 
                    st.success("✅ All calculations verified")
            
            with tab2:
                st.subheader("JSON Data Preview")
                company = get_company_info(data)
                company_name = company.get("legal_name") or company.get("name") or "N/A"
                st.text_input("Company Name", value=company_name, disabled=True)
                period_keys = get_period_keys(data)
                period_labels = [get_period_label(data, pk) for pk in period_keys]
                st.write(f"Periods: {', '.join(period_labels)}")
                with st.expander("📄 View Raw JSON"): 
                    st.json(data)
            
            with tab3:
                st.subheader("HTML Report Preview")
                st.info("💡 The generated HTML includes a theme toggle button (top-right) to switch between Light & Dark mode")
                with st.spinner("Generating HTML report..."): 
                    html_content = generate_full_html(data)
                st.success(f"✅ HTML generated ({len(html_content):,} characters)")
                st.components.v1.html(html_content, height=800, scrolling=True)
            
            with tab4:
                st.subheader("Download Options")
                html_content = generate_full_html(data)
                company_name = company.get("legal_name") or company.get("name") or "Financial_Report"
                safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in company_name).replace(' ', '_')
                date_str = datetime.now().strftime("%Y%m%d")
                
                # Generate PDF
                pdf_ready = False
                pdf_bytes = None
                pdf_error_msg = ""
                try:
                    with st.spinner("Generating PDF report..."):
                        pdf_bytes = convert_html_to_pdf(html_content)
                        pdf_ready = True
                except Exception as e:
                    pdf_error_msg = str(e) if str(e) else type(e).__name__
                    st.warning(f"⚠️ PDF generation encountered an issue: {pdf_error_msg}")
                
                # Generate Excel
                excel_ready = False
                excel_bytes = None
                try:
                    from excel_export import convert_json_to_excel
                    excel_bytes = convert_json_to_excel(data)
                    excel_ready = True
                except Exception as e:
                    pass  # Excel export is optional
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.download_button(
                        label="⬇️ Download HTML Report", 
                        data=html_content, 
                        file_name=f"{safe_name}_Financial_Analysis_{date_str}.html", 
                        mime="text/html", 
                        use_container_width=True
                    )
                    st.caption("Best for: Desktop viewing, interactive features")
                with col2:
                    if pdf_ready and pdf_bytes:
                        st.download_button(
                            label="📑 Download PDF Report", 
                            data=pdf_bytes, 
                            file_name=f"{safe_name}_Financial_Analysis_{date_str}.pdf", 
                            mime="application/pdf", 
                            use_container_width=True
                        )
                        st.caption("Best for: WhatsApp sharing, printing, iPad")
                    else:
                        st.button("📑 Download PDF Report", disabled=True, use_container_width=True)
                        if pdf_error_msg:
                            st.caption(f"⚠️ PDF error: {pdf_error_msg}")
                        else:
                            st.caption("⚠️ PDF generation unavailable")
                with col3:
                    if excel_ready and excel_bytes:
                        st.download_button(
                            label="📊 Download Excel Report",
                            data=excel_bytes,
                            file_name=f"{safe_name}_Financial_Analysis_{date_str}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                        st.caption("Best for: Spreadsheet analysis, data manipulation")
                    else:
                        st.button("📊 Download Excel Report", disabled=True, use_container_width=True)
                        st.caption("⚠️ Excel generation unavailable")
                with col4:
                    st.download_button(
                        label="⬇️ Download JSON", 
                        data=json.dumps(data, indent=2), 
                        file_name=f"{safe_name}_Financial_Analysis_{date_str}.json", 
                        mime="application/json", 
                        use_container_width=True
                    )
                    st.caption("Best for: Re-analysis, data processing")
        except json.JSONDecodeError as e: 
            st.error(f"❌ Invalid JSON file: {e}")
        except Exception as e: 
            st.error(f"❌ Error processing file: {e}")
            st.exception(e)
    else:
        st.info("👆 Please upload a JSON file to get started")
        st.markdown("""
        ### Supported JSON Formats:
        - **v7.9** (Framework v7.9) - Narrative validation, f-string construction rule
        - **v7.8** (Framework v7.8) - Phase 0 MAP, note-reading mandate, disclosure note distinction
        - **v7.7** (Framework v7.7) - Prior year adjustments, restated periods, single WCR values
        - **v7.6** (Framework v7.6) - Single WCR values (CCC adj handles period correction)
        - **v7.2** (Framework v7.2) - Dual efficiency ratios (standard + period-adjusted), dual WCR values, clean period labels
        - **v7.1** (Framework v7.1) - Period days calculation, dual efficiency ratios
        - **v6.19** (Custom Instructions v6.19) - Consolidated single-reference CI, structurally identical to v6.18
        - **v6.18** (Custom Instructions v6.18) - Output Optimization, CCC/OWC conflict resolution, removed per-period WC narratives
        - **v6.17** (Custom Instructions v6.17) - Extraction reconciliation rule
        - **v6.16** (Custom Instructions v6.16) - MA period labeling, lump sum handling, DSCR assessment, risk flags, facility concerns
        - **v6.15** (Custom Instructions v6.15) - Facility appropriateness logic, mandatory DSCR assessment, risk flags, PBT margin
        - **v6.14** (Custom Instructions v6.14) - WC methodology correction, enhanced OWC/CCC interpretation
        - **v6.13** (Custom Instructions v6.13) - Ratio naming update, formula display support
        - **v6.12** (Custom Instructions v6.12) - Full schema with renamed ratios, formula display, benchmarks
        - **v6.11** (Custom Instructions v6.11) - Audit Opinion, Period Labels with source type suffix
        - **v6.5** (Custom Instructions v6.9) - Full schema with TNW, Facility Classification, DSCR Term/Revolving
        - **v6.3** (Custom Instructions v6.3-v6.5) - Working Capital, Funding Mismatch, Funding Profile
        - **v6.0** (Custom Instructions v6.0) - Basic schema with P&L, Balance Sheet, Ratios
        - **v2.1** (Legacy) - Uses `company`, `income_statement`, `balance_sheet`
        
        ### New in v7.7 (Streamlit):
        - 📊 **Excel Export** - Download formatted .xlsx with 8 sheets (Summary, P&L, BS, Ratios, WC, DSCR, TNW, Observations)
        - 🖨️ **PDF Emoji Fix** - Emojis render properly in PDF using Symbola font
        - 📑 **PDF Quality** - Print CSS matches HTML light theme exactly
        - 🏷️ **v7.9 Framework Compatibility** - Full support for latest framework schema
        
        ### From v7.6:
        - 🏷️ **v7.8 Framework Compatibility** - Phase 0 MAP, note-reading mandate
        - 📝 **Prior Year Adjustments** - Renders restatement details in Audit Opinion section
        - ✅ **WCR Validation Reworked** - No false warnings for v7.6/v7.7 single-values schema
        - 🔍 **Restated Comparative Badge** - Handles "Unqualified (Restated Comparative)" opinion type
        
        ### From v7.3:
        - 🏷️ **Restated Period Support** - Handles `(Audited - Restated)` labels correctly
        - ✅ **v7.6 WCR Compatibility** - No false warnings for v7.6 single-values WCR schema
        - 🔍 **v7.5/v7.6 Detection** - Explicit schema version detection for latest framework
        
        ### From v7.0:
        - 🔄 **v7.2 Compatibility** - Full support for Framework v7.2 and JSON Schema v7.2
        - 📊 **Dual Efficiency Ratios** - Shows both standard (x365) and period-adjusted values for YTD periods
        - 📈 **Dual WCR Values** - WCR now shows both standard and period-adjusted amounts
        - 🏷️ **Clean Period Labels** - Strips "- XXX days" suffix from period labels automatically
        - 🔍 **Schema Detection** - Detects v7.1/v7.2 explicitly and via heuristics
        - ✅ **Backward Compatible** - All v6.19 and earlier JSON continues to render correctly
        
        ### From Previous Versions:
        - 📋 **DSCR Assessment** - Mandatory assessment narrative
        - ⚠️ **Risk Flags** - Plain string arrays
        - 🏦 **Facility Concerns** - Shows why facilities are inappropriate
        - 📐 **Formula Display** - All ratios show calculation formula
        - 🎯 **Benchmark Badges** - Pass/fail status on key ratios
        - 🔍 **Audit Opinion** - Auditor details, going concern notes
        - 🌙 **Dual Theme** - Light and Dark mode toggle
        """)

if __name__ == "__main__":
    main()
