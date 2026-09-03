# Nexgile-DecarbX

Enterprise carbon accounting and environmental intelligence platform — audit-grade Scope 1/2 emissions tracking, product carbon footprinting, and supplier engagement, built as a functional proof-of-concept of a full enterprise carbon platform spec.

## What it does

- **Carbon Accounting**: Log Scope 1 (direct combustion) and Scope 2 (electricity) activity data across facilities. Emissions are calculated automatically against a controlled emission-factor library (14 factors across fuel types and country grids), with geography-aware lookups and fallback to global defaults.
- **AI Reduction Insight**: Automatically identifies the highest-emitting source and facility, and generates a decarbonization recommendation.
- **Product Carbon Footprint (PCF)**: Register products with multi-material bills of materials; computes cradle-to-gate footprint per SKU from component weights and material emission factors.
- **Supplier Engagement**: Register suppliers, collect self-reported Scope 1/2/3 emissions, and view scorecards with data-completeness status (pending / submitted / verified).
- **Compliance Readiness**: Shows how the underlying Scope 1/2/3 activity data maps to the data foundation required for CSRD, TCFD, EU Taxonomy, and CBAM disclosures.
- **Dashboard**: Live emissions totals, scope breakdown chart, emissions-target budget tracker, facility-level aggregation, and CSV export.

## Tech stack

- **Backend**: Python, FastAPI, SQLAlchemy, SQLite
- **Frontend**: Vanilla HTML/JS, Chart.js — no build step
- **No auth/deployment layer** — scoped out for a time-boxed build; the calculation engine and data model are the focus

## Run it

```
cd Drive-pro
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy
uvicorn main:app --reload
```

Visit `http://127.0.0.1:8000` for the app, `http://127.0.0.1:8000/docs` for the API.

## Scope note

This implements the core engine (data ingestion → calculation → audit trail → dashboard) that a full enterprise platform is built on. Modules like multi-language supplier portals, ISO 14067 certification workflows, ERP/PLM integrations, and full CSRD/CBAM XBRL reporting are architecturally compatible extensions of this same data model, out of scope for this build.
