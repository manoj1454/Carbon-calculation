import os
from contextlib import asynccontextmanager
from typing import List
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Depends, HTTPException, status
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from fastapi.staticfiles import StaticFiles
# pyrefly: ignore [missing-import]
from fastapi.responses import FileResponse
# pyrefly: ignore [missing-import]
from fastapi.security import OAuth2PasswordRequestForm
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy import func

from datetime import date
from database import engine, SessionLocal, Base, get_db
import models
import schemas
from seed import seed_emission_factors
import auth


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_emission_factors(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Drive-pro API", lifespan=lifespan)

# CORS middleware allowing all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static directory exists and mount static files
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Drive-pro API is running"}


# ==========================================
# Auth Endpoints
# ==========================================
@app.post("/auth/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth.create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": token, "token_type": "bearer", "role": user.role, "username": user.username}


@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
@app.post("/auth/signup", status_code=status.HTTP_201_CREATED)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == user_in.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{user_in.username}' is already taken. Please choose another.",
        )
    user = models.User(
        username=user_in.username,
        hashed_password=auth.hash_password(user_in.password),
        role=user_in.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = auth.create_access_token(data={"sub": user.username, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "username": user.username,
        "message": f"Account '{user.username}' created successfully.",
    }


@app.get("/auth/me")

def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return {"username": current_user.username, "role": current_user.role}


@app.post("/auth/seed-user", status_code=status.HTTP_201_CREATED, include_in_schema=False)
def seed_user(payload: dict, db: Session = Depends(get_db)):
    """Internal seeding endpoint — creates a user if username doesn't exist yet."""
    from fastapi import Response
    username = payload.get("username")
    password = payload.get("password")
    role = payload.get("role")
    if not username or not password or not role:
        raise HTTPException(status_code=400, detail="username, password, and role required")
    existing = db.query(models.User).filter(models.User.username == username).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"User '{username}' already exists")
    user = models.User(
        username=username,
        hashed_password=auth.hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "role": user.role}



# Facility Endpoints
@app.post("/facilities", response_model=schemas.FacilityOut, status_code=status.HTTP_201_CREATED)
def create_facility(
    facility: schemas.FacilityCreate,
    db: Session = Depends(get_db),
    _current_user: models.User = Depends(auth.require_manager),
):
    db_facility = models.Facility(
        name=facility.name,
        country=facility.country,
        address=facility.address,
        facility_type=facility.facility_type,
        employee_count=facility.employee_count,
        operational_since=facility.operational_since,
    )
    db.add(db_facility)
    db.commit()
    db.refresh(db_facility)
    return db_facility


@app.get("/facilities", response_model=List[schemas.FacilityOut])
def list_facilities(db: Session = Depends(get_db)):
    return db.query(models.Facility).all()


# Activity Entry Endpoints
@app.post(
    "/activity-entries",
    response_model=schemas.ActivityEntryOut,
    status_code=status.HTTP_201_CREATED,
)
def create_activity_entry(
    entry: schemas.ActivityEntryCreate,
    db: Session = Depends(get_db),
    _current_user: models.User = Depends(auth.require_manager),
):
    # 1. Verify facility exists
    facility = db.query(models.Facility).filter(models.Facility.id == entry.facility_id).first()
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Facility with id {entry.facility_id} not found.",
        )

    # 2. Look up matching EmissionFactor by fuel_type + scope + geography
    fuel_norm = entry.fuel_type.strip().lower()
    geo_norm = entry.geography.strip().lower()

    factor = (
        db.query(models.EmissionFactor)
        .filter(
            func.lower(models.EmissionFactor.fuel_type) == fuel_norm,
            models.EmissionFactor.scope == entry.scope,
            func.lower(models.EmissionFactor.geography) == geo_norm,
        )
        .first()
    )

    # Fallback to "Global" geography if regional factor is not found
    if not factor and geo_norm != "global":
        factor = (
            db.query(models.EmissionFactor)
            .filter(
                func.lower(models.EmissionFactor.fuel_type) == fuel_norm,
                models.EmissionFactor.scope == entry.scope,
                func.lower(models.EmissionFactor.geography) == "global",
            )
            .first()
        )

    if not factor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Emission factor not found for fuel_type='{entry.fuel_type}', "
                f"scope={entry.scope}, geography='{entry.geography}'."
            ),
        )

    # 3. Compute emissions_kg = quantity * factor.value
    emissions_kg = round(float(entry.quantity * factor.value), 4)

    # 4. Store and return computed ActivityEntry
    db_entry = models.ActivityEntry(
        facility_id=entry.facility_id,
        scope=entry.scope,
        fuel_type=entry.fuel_type,
        geography=entry.geography,
        quantity=entry.quantity,
        unit=entry.unit,
        date=str(entry.date) if entry.date and str(entry.date) != "None" else date.today().isoformat(),
        emissions_kg=emissions_kg,
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry


@app.get("/activity-entries", response_model=List[schemas.ActivityEntryOut])
def list_activity_entries(db: Session = Depends(get_db)):
    return (
        db.query(models.ActivityEntry)
        .order_by(models.ActivityEntry.id.desc())
        .limit(50)
        .all()
    )



# Emission Factors Listing Endpoint
@app.get("/emission-factors", response_model=List[schemas.EmissionFactorOut])
def list_emission_factors(db: Session = Depends(get_db)):
    return db.query(models.EmissionFactor).all()


# Emissions Aggregation Endpoints
@app.get("/emissions/summary", response_model=schemas.EmissionsSummaryOut)
def get_emissions_summary(db: Session = Depends(get_db)):
    scope1_sum = (
        db.query(func.coalesce(func.sum(models.ActivityEntry.emissions_kg), 0.0))
        .filter(models.ActivityEntry.scope == 1)
        .scalar()
    )
    scope2_sum = (
        db.query(func.coalesce(func.sum(models.ActivityEntry.emissions_kg), 0.0))
        .filter(models.ActivityEntry.scope == 2)
        .scalar()
    )
    scope1_total = round(float(scope1_sum), 2)
    scope2_total = round(float(scope2_sum), 2)
    total = round(scope1_total + scope2_total, 2)

    return {
        "scope1_total": scope1_total,
        "scope2_total": scope2_total,
        "total": total,
    }


@app.get("/emissions/by-facility", response_model=List[schemas.FacilityEmissionsOut])
def get_emissions_by_facility(db: Session = Depends(get_db)):
    facilities = db.query(models.Facility).all()
    results = []
    for fac in facilities:
        s1 = (
            db.query(func.coalesce(func.sum(models.ActivityEntry.emissions_kg), 0.0))
            .filter(
                models.ActivityEntry.facility_id == fac.id,
                models.ActivityEntry.scope == 1,
            )
            .scalar()
        )
        s2 = (
            db.query(func.coalesce(func.sum(models.ActivityEntry.emissions_kg), 0.0))
            .filter(
                models.ActivityEntry.facility_id == fac.id,
                models.ActivityEntry.scope == 2,
            )
            .scalar()
        )
        scope1_val = round(float(s1), 2)
        scope2_val = round(float(s2), 2)
        total_val = round(scope1_val + scope2_val, 2)
        results.append({
            "facility_id": fac.id,
            "facility_name": fac.name,
            "country": fac.country,
            "address": fac.address,
            "facility_type": fac.facility_type,
            "employee_count": fac.employee_count,
            "operational_since": fac.operational_since,
            "scope1_total": scope1_val,
            "scope2_total": scope2_val,
            "total_emissions_kg": total_val,
        })
    return results


# AI Carbon Reduction Insights Endpoint
@app.get("/insights")
def get_insights(db: Session = Depends(get_db)):
    # 1. Query highest emissions_kg entry
    top_entry = (
        db.query(models.ActivityEntry)
        .order_by(models.ActivityEntry.emissions_kg.desc())
        .first()
    )

    if not top_entry:
        return {
            "top_source": None,
            "top_facility": None,
            "recommendation": "No activity data recorded yet. Add activity entries to generate carbon reduction insights.",
        }

    # Fetch facility name for top entry
    top_fac = db.query(models.Facility).filter(models.Facility.id == top_entry.facility_id).first()
    top_source_fac_name = top_fac.name if top_fac else f"Facility #{top_entry.facility_id}"

    top_source = {
        "id": top_entry.id,
        "facility_id": top_entry.facility_id,
        "facility_name": top_source_fac_name,
        "scope": top_entry.scope,
        "fuel_type": top_entry.fuel_type,
        "geography": top_entry.geography,
        "quantity": top_entry.quantity,
        "unit": top_entry.unit,
        "date": top_entry.date,
        "emissions_kg": top_entry.emissions_kg,
    }

    # 2. Find facility with highest total emissions
    facility_totals = (
        db.query(
            models.ActivityEntry.facility_id,
            func.sum(models.ActivityEntry.emissions_kg).label("total_emissions"),
        )
        .group_by(models.ActivityEntry.facility_id)
        .order_by(func.sum(models.ActivityEntry.emissions_kg).desc())
        .first()
    )

    top_facility = None
    if facility_totals:
        fac = db.query(models.Facility).filter(models.Facility.id == facility_totals[0]).first()
        if fac:
            top_facility = {
                "facility_id": fac.id,
                "facility_name": fac.name,
                "country": fac.country,
                "total_emissions_kg": round(float(facility_totals[1]), 2),
            }

    # 3. Simple recommendation logic
    fuel = top_entry.fuel_type.strip().lower()
    geo = top_entry.geography.strip().lower()

    if fuel in ["diesel", "petrol", "coal"]:
        recommendation = (
            f"Switching {top_source_fac_name}'s {top_entry.fuel_type} usage to a lower-carbon alternative "
            f"could reduce emissions by up to 85% — switch to electricity in a low-carbon grid country like France (0.041 kgCO2e/kWh)."
        )
    elif fuel == "electricity":
        recommendation = (
            f"Switching {top_source_fac_name}'s {top_entry.fuel_type} sourcing in {top_entry.geography} "
            f"could reduce emissions by up to 60% — switch grid sourcing to a lower-carbon geography or renewable PPAs."
        )
    else:
        recommendation = (
            f"Switching {top_source_fac_name}'s {top_entry.fuel_type} usage to a lower-carbon alternative "
            f"could reduce emissions by up to 50% through process electrification and efficiency improvements."
        )

    return {
        "top_source": top_source,
        "top_facility": top_facility,
        "recommendation": recommendation,
    }


# ==========================================
# Product LCA (PCF) Endpoints
# ==========================================
@app.post("/products", response_model=schemas.ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
    _current_user: models.User = Depends(auth.require_manager),
):
    fac = db.query(models.Facility).filter(models.Facility.id == product.facility_id).first()
    if not fac:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Facility with id {product.facility_id} not found.",
        )
    db_product = models.Product(
        name=product.name,
        sku=product.sku,
        facility_id=product.facility_id,
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.get("/products", response_model=List[schemas.ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(models.Product).order_by(models.Product.id.desc()).all()


@app.post(
    "/products/{product_id}/components",
    response_model=schemas.ProductComponentOut,
    status_code=status.HTTP_201_CREATED,
)
def add_product_component(
    product_id: int,
    comp: schemas.ProductComponentCreate,
    db: Session = Depends(get_db),
    _current_user: models.User = Depends(auth.require_manager),
):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found.",
        )
    db_comp = models.ProductComponent(
        product_id=product_id,
        material_name=comp.material_name,
        weight_kg=comp.weight_kg,
        material_emission_factor_kgco2e_per_kg=comp.material_emission_factor_kgco2e_per_kg,
    )
    db.add(db_comp)
    db.commit()
    db.refresh(db_comp)
    return db_comp


@app.get("/products/{product_id}/footprint", response_model=schemas.ProductFootprintOut)
def get_product_footprint(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found.",
        )

    components_out = []
    total_pcf = 0.0
    for comp in product.components:
        emissions = round(float(comp.weight_kg) * float(comp.material_emission_factor_kgco2e_per_kg), 4)
        total_pcf += emissions
        components_out.append({
            "material_name": comp.material_name,
            "weight_kg": float(comp.weight_kg),
            "emissions_kg": emissions,
        })

    return {
        "product_id": product.id,
        "product_name": product.name,
        "sku": product.sku,
        "total_pcf_kg": round(total_pcf, 4),
        "components": components_out,
    }


# ==========================================
# Supplier Engagement Endpoints
# ==========================================
@app.post("/suppliers", response_model=schemas.SupplierOut, status_code=status.HTTP_201_CREATED)
def create_supplier(
    supplier: schemas.SupplierCreate,
    db: Session = Depends(get_db),
    _current_user: models.User = Depends(auth.require_manager),
):
    db_supplier = models.Supplier(
        name=supplier.name,
        country=supplier.country,
        category=supplier.category,
        status=supplier.status or "pending",
    )
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier


@app.get("/suppliers", response_model=List[schemas.SupplierScorecardOut])
def list_suppliers(db: Session = Depends(get_db)):
    suppliers = db.query(models.Supplier).order_by(models.Supplier.id.desc()).all()
    scorecards = []
    for s in suppliers:
        latest_emission = (
            db.query(models.SupplierEmissionData)
            .filter(models.SupplierEmissionData.supplier_id == s.id)
            .order_by(models.SupplierEmissionData.id.desc())
            .first()
        )
        if latest_emission:
            s1 = float(latest_emission.scope1_kg or 0.0)
            s2 = float(latest_emission.scope2_kg or 0.0)
            s3 = float(latest_emission.scope3_kg or 0.0)
            total = round(s1 + s2 + s3, 2)
            if s1 > 0 and s2 > 0 and s3 > 0:
                completeness = "Complete"
            elif s1 > 0 or s2 > 0 or s3 > 0:
                completeness = "Partial"
            else:
                completeness = "No Data"
        else:
            total = 0.0
            completeness = "No Data"

        scorecards.append({
            "supplier_id": s.id,
            "name": s.name,
            "country": s.country,
            "category": s.category,
            "status": s.status,
            "total_reported_kg": total,
            "data_completeness": completeness,
        })
    return scorecards


@app.post(
    "/suppliers/{supplier_id}/emissions",
    response_model=schemas.SupplierEmissionDataOut,
    status_code=status.HTTP_201_CREATED,
)
def log_supplier_emissions(
    supplier_id: int,
    data: schemas.SupplierEmissionDataCreate,
    db: Session = Depends(get_db),
    _current_user: models.User = Depends(auth.require_manager),
):
    supplier = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with id {supplier_id} not found.",
        )

    # Set supplier status to submitted
    supplier.status = "submitted"

    db_emission = models.SupplierEmissionData(
        supplier_id=supplier_id,
        reporting_period=data.reporting_period,
        scope1_kg=data.scope1_kg,
        scope2_kg=data.scope2_kg,
        scope3_kg=data.scope3_kg,
        submitted_date=data.submitted_date or date.today().isoformat(),
    )
    db.add(db_emission)
    db.commit()
    db.refresh(db_emission)
    return db_emission


@app.get("/suppliers/scorecards", response_model=List[schemas.SupplierScorecardOut])
def get_supplier_scorecards(db: Session = Depends(get_db)):
    scorecards = list_suppliers(db)
    scorecards.sort(key=lambda x: x["total_reported_kg"], reverse=True)
    return scorecards


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)



