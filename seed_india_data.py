#!/usr/bin/env python3
"""
seed_india_data.py
Adds 4 Indian city-level entries (2 facilities, 2 suppliers) with activity logs and emission data.
"""

import sys
import requests

BASE_URL = "http://127.0.0.1:8000"


def main():
    print(f"Connecting to Drive-pro API at {BASE_URL}...")
    try:
        res = requests.get(f"{BASE_URL}/emissions/summary", timeout=5)
        if res.status_code != 200:
            print(f"Error: API returned status {res.status_code}. Is uvicorn running?")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

    print("\n--- 1. SEEDING INDIAN CITY-LEVEL FACILITIES ---")
    facilities_to_add = [
        {"name": "Delhi Logistics Hub", "country": "Delhi"},
        {"name": "Bengaluru Tech Campus", "country": "Bengaluru"},
    ]

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

    print("\n--- 2. SEEDING ACTIVITY ENTRIES FOR NEW FACILITIES ---")
    activity_entries = [
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

    for act in activity_entries:
        if not act["facility_id"]:
            print(f"  [Skipped] Missing facility_id for activity: {act}")
            continue

        r = requests.post(f"{BASE_URL}/activity-entries", json=act)
        if r.status_code == 201:
            entry = r.json()
            print(f"  [Logged] Activity ID: {entry['id']} | Scope {entry['scope']} {entry['fuel_type']} | Qty: {entry['quantity']} {entry['unit']} | Emissions: {entry['emissions_kg']} kg CO2e")
        else:
            print(f"  [Failed] Activity log -> {r.text}")

    print("\n--- 3. SEEDING INDIAN CITY-LEVEL SUPPLIERS ---")
    suppliers_to_add = [
        {
            "supplier": {
                "name": "Mumbai Precision Components",
                "country": "Mumbai",
                "category": "Manufacturing",
            },
            "emissions": {
                "reporting_period": "2026-Q2",
                "scope1_kg": 9800.0,
                "scope2_kg": 4200.0,
                "scope3_kg": 2100.0,
            },
        },
        {
            "supplier": {
                "name": "Hyderabad Textile Works",
                "country": "Hyderabad",
                "category": "Raw Materials",
            },
            "emissions": {
                "reporting_period": "2026-Q2",
                "scope1_kg": 6500.0,
                "scope2_kg": 2800.0,
                "scope3_kg": 1400.0,
            },
        },
    ]

    existing_supps = {s["name"]: s["supplier_id"] for s in requests.get(f"{BASE_URL}/suppliers/scorecards").json()}

    for item in suppliers_to_add:
        supp_data = item["supplier"]
        name = supp_data["name"]

        if name in existing_supps:
            supp_id = existing_supps[name]
            print(f"  [Exists] Supplier: {name} (ID: {supp_id})")
        else:
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
                print(f"  [Failed] Supplier {supp_data['name']} -> {r.text}")

    print("\n--- 4. VERIFYING UPDATED MAP & SUMMARY DATA ---")
    fac_res = requests.get(f"{BASE_URL}/emissions/by-facility").json()
    print(f"  Total Facilities on Map: {len(fac_res)}")
    for f in fac_res:
        print(f"    - {f['facility_name']:<30} | Loc: {f['country']:<12} | Emissions: {f['total_emissions_kg']:>10.1f} kg CO2e")

    supp_res = requests.get(f"{BASE_URL}/suppliers/scorecards").json()
    print(f"\n  Total Suppliers on Map: {len(supp_res)}")
    for s in supp_res:
        print(f"    - {s['name']:<30} | Loc: {s['country']:<12} | Status: {s['status']:<10} | Total: {s['total_reported_kg']:>10.1f} kg CO2e")

    print("\n=== SUCCESS: Indian city-level demo data seeded successfully! ===")


if __name__ == "__main__":
    main()
