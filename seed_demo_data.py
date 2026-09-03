#!/usr/bin/env python3
"""
seed_demo_data.py
Populates realistic sample data for the Drive-pro demo:
- 2 additional Facilities (Riverside Distribution Center, Chennai Manufacturing Hub)
- 5 Activity Entries across scopes and fuel types
- 2 Products with multi-component Bills of Materials (PCF)
- 5 Suppliers with self-reported Scope 1/2/3 emissions and status mix
"""

import os
import sys
import time
import requests

# Base URL targeting deployed Render app or localhost:
# e.g. BASE_URL = "https://<paste-your-actual-render-url-here>"
# Can also be set via environment variable: BASE_URL="https://..."
# or command line argument: python seed_demo_data.py https://...
DEFAULT_RENDER_URL = "https://<paste-your-actual-render-url-here>"
ENV_URL = os.environ.get("BASE_URL")
CLI_URL = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].startswith("http") else None

BASE_URL = (ENV_URL or CLI_URL or DEFAULT_RENDER_URL).rstrip("/")
if "<paste-your-actual-render-url-here>" in BASE_URL:
    BASE_URL = "http://127.0.0.1:8000"


def check_connection():
    print(f"Connecting to Drive-pro API at {BASE_URL}...")
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            print(f"  Attempt {attempt}/{max_retries}: Checking {BASE_URL}/emissions/summary...")
            res = requests.get(f"{BASE_URL}/emissions/summary", timeout=30)
            if res.status_code == 200:
                print("  Successfully connected to server.")
                return
            else:
                print(f"  Status {res.status_code}: {res.text}")
        except requests.exceptions.RequestException as e:
            print(f"  Waiting for server response (Render free-tier spin-up takes ~30-50s)...")
            if attempt < max_retries:
                time.sleep(10)
            else:
                print(f"\nConnection failed: {e}")
                print(f"Please ensure {BASE_URL} is running and reachable.")
                sys.exit(1)


def main():
    check_connection()

    print("\n--- 1. SEEDING FACILITIES ---")
    facilities_to_add = [
        {
            "name": "Gigafactory 1",
            "country": "US",
            "address": "4800 Battery Way, Austin, TX",
            "facility_type": "Manufacturing",
            "employee_count": 3200,
            "operational_since": "2019",
        },
        {
            "name": "Riverside Distribution Center",
            "country": "UK",
            "address": "12 Dockside Road, London, UK",
            "facility_type": "Distribution",
            "employee_count": 450,
            "operational_since": "2021",
        },
        {
            "name": "Chennai Manufacturing Hub",
            "country": "IN",
            "address": "Plot 44, SIPCOT Industrial Park, Chennai",
            "facility_type": "Manufacturing",
            "employee_count": 1800,
            "operational_since": "2020",
        },
        {
            "name": "Delhi Logistics Hub",
            "country": "Delhi",
            "address": "Sector 63, Noida, Delhi NCR",
            "facility_type": "Distribution",
            "employee_count": 320,
            "operational_since": "2022",
        },
        {
            "name": "Bengaluru Tech Campus",
            "country": "Bengaluru",
            "address": "Whitefield Tech Park, Bengaluru",
            "facility_type": "Office",
            "employee_count": 900,
            "operational_since": "2018",
        },
    ]

    # Fetch existing facilities to avoid duplicates
    existing_facs = {f["name"]: f["id"] for f in requests.get(f"{BASE_URL}/facilities").json()}
    facility_ids = {}

    for fac in facilities_to_add:
        name = fac["name"]
        if name in existing_facs:
            facility_ids[name] = existing_facs[name]
            print(f"  [Exists] Facility: {name} (ID: {existing_facs[name]})")
        else:
            r = requests.post(f"{BASE_URL}/facilities", json=fac)
            if r.status_code == 201:
                created = r.json()
                facility_ids[name] = created["id"]
                print(f"  [Created] Facility: {name} ({fac['country']}) -> ID: {created['id']}")
            else:
                print(f"  [Failed] Facility: {name} -> {r.text}")

    print("\n--- 2. SEEDING ACTIVITY ENTRIES ---")
    activity_entries = [
        {
            "facility_id": facility_ids.get("Gigafactory 1"),
            "scope": 1,
            "fuel_type": "natural_gas",
            "geography": "US",
            "quantity": 2500.0,
            "unit": "m3",
            "date": "2026-08-28",
        },
        {
            "facility_id": facility_ids.get("Gigafactory 1"),
            "scope": 1,
            "fuel_type": "diesel",
            "geography": "US",
            "quantity": 3500.0,
            "unit": "liters",
            "date": "2026-08-30",
        },
        {
            "facility_id": facility_ids.get("Gigafactory 1"),
            "scope": 2,
            "fuel_type": "electricity",
            "geography": "US",
            "quantity": 18389.6,
            "unit": "kWh",
            "date": "2026-09-01",
        },
        {
            "facility_id": facility_ids.get("Riverside Distribution Center"),
            "scope": 1,
            "fuel_type": "diesel",
            "geography": "UK",
            "quantity": 800.0,
            "unit": "liters",
            "date": "2026-09-01",
        },
        {
            "facility_id": facility_ids.get("Riverside Distribution Center"),
            "scope": 2,
            "fuel_type": "electricity",
            "geography": "UK",
            "quantity": 5000.0,
            "unit": "kWh",
            "date": "2026-09-02",
        },
        {
            "facility_id": facility_ids.get("Chennai Manufacturing Hub"),
            "scope": 1,
            "fuel_type": "natural_gas",
            "geography": "Global",
            "quantity": 1200.0,
            "unit": "m3",
            "date": "2026-09-02",
        },
        {
            "facility_id": facility_ids.get("Chennai Manufacturing Hub"),
            "scope": 2,
            "fuel_type": "electricity",
            "geography": "IN",
            "quantity": 15000.0,
            "unit": "kWh",
            "date": "2026-09-03",
        },
        {
            "facility_id": facility_ids.get("Chennai Manufacturing Hub"),
            "scope": 1,
            "fuel_type": "coal",
            "geography": "Global",
            "quantity": 500.0,
            "unit": "kg",
            "date": "2026-09-03",
        },
        {
            "facility_id": facility_ids.get("Delhi Logistics Hub"),
            "scope": 1,
            "fuel_type": "diesel",
            "geography": "IN",
            "quantity": 600.0,
            "unit": "liters",
            "date": "2026-09-03",
        },
        {
            "facility_id": facility_ids.get("Delhi Logistics Hub"),
            "scope": 2,
            "fuel_type": "electricity",
            "geography": "IN",
            "quantity": 8000.0,
            "unit": "kWh",
            "date": "2026-09-03",
        },
        {
            "facility_id": facility_ids.get("Bengaluru Tech Campus"),
            "scope": 2,
            "fuel_type": "electricity",
            "geography": "IN",
            "quantity": 20000.0,
            "unit": "kWh",
            "date": "2026-09-03",
        },
    ]

    for entry in activity_entries:
        if not entry["facility_id"]:
            print(f"  [Skipped] Entry skipped due to missing facility ID: {entry}")
            continue
        r = requests.post(f"{BASE_URL}/activity-entries", json=entry)
        if r.status_code == 201:
            data = r.json()
            print(f"  [Created] Scope {data['scope']} {data['fuel_type']} ({data['quantity']} {data['unit']}) -> {data['emissions_kg']} kg CO2e")
        else:
            print(f"  [Failed] Entry {entry['fuel_type']} -> {r.text}")

    print("\n--- 3. SEEDING PRODUCTS & MATERIAL COMPONENTS (PCF) ---")
    products_to_add = [
        {
            "product": {
                "name": "EcoDrive Battery Pack",
                "sku": "BAT-2026-A",
                "facility_id": facility_ids.get("Gigafactory 1"),
            },
            "components": [
                {"material_name": "aluminum", "weight_kg": 12.5, "material_emission_factor_kgco2e_per_kg": 11.5},
                {"material_name": "steel", "weight_kg": 8.0, "material_emission_factor_kgco2e_per_kg": 2.0},
                {"material_name": "plastic (PET)", "weight_kg": 3.2, "material_emission_factor_kgco2e_per_kg": 2.15},
            ],
        },
        {
            "product": {
                "name": "Standard Shipping Container",
                "sku": "PKG-2026-B",
                "facility_id": facility_ids.get("Riverside Distribution Center"),
            },
            "components": [
                {"material_name": "cardboard/paper packaging", "weight_kg": 2.0, "material_emission_factor_kgco2e_per_kg": 0.94},
                {"material_name": "plastic (PET)", "weight_kg": 0.8, "material_emission_factor_kgco2e_per_kg": 2.15},
            ],
        },
    ]

    for item in products_to_add:
        prod_data = item["product"]
        if not prod_data["facility_id"]:
            print(f"  [Skipped] Product {prod_data['name']} skipped due to missing facility ID")
            continue

        r = requests.post(f"{BASE_URL}/products", json=prod_data)
        if r.status_code == 201:
            prod = r.json()
            prod_id = prod["id"]
            print(f"  [Created] Product: {prod['name']} (SKU: {prod['sku']}, ID: {prod_id})")

            for comp in item["components"]:
                cr = requests.post(f"{BASE_URL}/products/{prod_id}/components", json=comp)
                if cr.status_code == 201:
                    c = cr.json()
                    print(f"    + Component: {c['material_name']} ({c['weight_kg']} kg @ {c['material_emission_factor_kgco2e_per_kg']} kgCO2e/kg)")
                else:
                    print(f"    ! Component Failed: {cr.text}")

            # Verify footprint calculation
            fp_res = requests.get(f"{BASE_URL}/products/{prod_id}/footprint")
            if fp_res.status_code == 200:
                fp = fp_res.json()
                print(f"    -> Computed Total PCF: {fp['total_pcf_kg']} kg CO2e")
        else:
            print(f"  [Failed] Product {prod_data['name']} -> {r.text}")

    print("\n--- 4. SEEDING SUPPLIERS & EMISSIONS DATA ---")
    suppliers_to_add = [
        {
            "supplier": {"name": "Meridian Steel Co", "country": "China", "category": "Raw Materials"},
            "emissions": {"reporting_period": "2026-Q2", "scope1_kg": 45000.0, "scope2_kg": 12000.0, "scope3_kg": 8000.0},
        },
        {
            "supplier": {"name": "Pacific Logistics Group", "country": "Singapore", "category": "Logistics"},
            "emissions": {"reporting_period": "2026-Q2", "scope1_kg": 22000.0, "scope2_kg": 3000.0, "scope3_kg": 1500.0},
        },
        {
            "supplier": {"name": "GreenPack Materials", "country": "Germany", "category": "Packaging"},
            "emissions": {"reporting_period": "2026-Q2", "scope1_kg": 3200.0, "scope2_kg": 1800.0, "scope3_kg": 900.0},
        },
        {
            "supplier": {"name": "Sunrise Textiles Ltd", "country": "India", "category": "Raw Materials"},
            "emissions": None,  # No emissions logged -> status remains "pending", completeness "No Data"
        },
        {
            "supplier": {"name": "Atlas Component Works", "country": "US", "category": "Manufacturing"},
            "emissions": {"reporting_period": "2026-Q2", "scope1_kg": 18500.0, "scope2_kg": 9200.0, "scope3_kg": 4100.0},
        },
        {
            "supplier": {"name": "Mumbai Precision Components", "country": "Mumbai", "category": "Manufacturing"},
            "emissions": {"reporting_period": "2026-Q2", "scope1_kg": 9800.0, "scope2_kg": 4200.0, "scope3_kg": 2100.0},
        },
        {
            "supplier": {"name": "Hyderabad Textile Works", "country": "Hyderabad", "category": "Raw Materials"},
            "emissions": {"reporting_period": "2026-Q2", "scope1_kg": 6500.0, "scope2_kg": 2800.0, "scope3_kg": 1400.0},
        },
    ]

    for item in suppliers_to_add:
        supp_data = item["supplier"]
        r = requests.post(f"{BASE_URL}/suppliers", json=supp_data)
        if r.status_code == 201:
            supp = r.json()
            supp_id = supp["id"]
            print(f"  [Created] Supplier: {supp['name']} ({supp['country']}, {supp['category']}) -> ID: {supp_id}")

            if item["emissions"]:
                er = requests.post(f"{BASE_URL}/suppliers/{supp_id}/emissions", json=item["emissions"])
                if er.status_code == 201:
                    em = er.json()
                    tot = em['scope1_kg'] + em['scope2_kg'] + em['scope3_kg']
                    print(f"    -> Logged Emissions ({em['reporting_period']}): {tot} kg CO2e (Status: submitted)")
                else:
                    print(f"    ! Emissions Log Failed: {er.text}")
            else:
                print("    -> No emissions logged (Status: pending, Tests 'No Data' badge)")
        else:
            print(f"  [Failed] Supplier {supp_data['name']} -> {r.text}")

    print("\n--- 5. VERIFYING SCORECARDS ---")
    scorecards_res = requests.get(f"{BASE_URL}/suppliers/scorecards")
    if scorecards_res.status_code == 200:
        scorecards = scorecards_res.json()
        print(f"  Retrieved {len(scorecards)} supplier scorecards:")
        for sc in scorecards:
            print(f"    - {sc['name']:<25} | Status: {sc['status']:<10} | Completeness: {sc['data_completeness']:<10} | Total: {sc['total_reported_kg']:>10.1f} kg")

    print("\n=== SUCCESS: All realistic demo data seeded successfully! ===")
    print(f"Refresh your browser at {BASE_URL}/ to explore the updated data.")


if __name__ == "__main__":
    main()
