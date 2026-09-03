from typing import Optional, Union, Any, List
from datetime import date as dt_date
from pydantic import BaseModel, ConfigDict, Field, field_validator


class FacilityCreate(BaseModel):
    name: str
    country: str


class FacilityOut(BaseModel):
    id: int
    name: str
    country: str

    model_config = ConfigDict(from_attributes=True)


class ActivityEntryCreate(BaseModel):
    facility_id: int
    scope: Union[int, str]
    fuel_type: str
    geography: str
    quantity: float
    unit: str
    date: Optional[Union[str, dt_date]] = Field(default_factory=lambda: dt_date.today().isoformat())

    @field_validator("scope", mode="before")
    @classmethod
    def parse_scope(cls, v: Any) -> int:
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            clean = v.strip().lower().replace("scope", "").strip()
            if clean in ("1", "2"):
                return int(clean)
        raise ValueError("Scope must be 1 or 2")

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v: Any) -> str:
        if not v:
            return dt_date.today().isoformat()
        if isinstance(v, dt_date):
            return v.isoformat()
        return str(v)


class ActivityEntryOut(BaseModel):
    id: int
    facility_id: int
    scope: int
    fuel_type: str
    geography: str
    quantity: float
    unit: str
    date: str
    emissions_kg: float

    model_config = ConfigDict(from_attributes=True)


class EmissionFactorOut(BaseModel):
    id: int
    fuel_type: str
    scope: int
    unit: str
    value: float
    geography: str

    model_config = ConfigDict(from_attributes=True)


class EmissionsSummaryOut(BaseModel):
    scope1_total: float
    scope2_total: float
    total: float


class FacilityEmissionsOut(BaseModel):
    facility_id: int
    facility_name: str
    country: str
    scope1_total: float
    scope2_total: float
    total_emissions_kg: float


# Product LCA (PCF) Schemas
class ProductCreate(BaseModel):
    name: str
    sku: str
    facility_id: int


class ProductOut(BaseModel):
    id: int
    name: str
    sku: str
    facility_id: int

    model_config = ConfigDict(from_attributes=True)


class ProductComponentCreate(BaseModel):
    material_name: str
    weight_kg: float
    material_emission_factor_kgco2e_per_kg: float


class ProductComponentOut(BaseModel):
    id: int
    product_id: int
    material_name: str
    weight_kg: float
    material_emission_factor_kgco2e_per_kg: float

    model_config = ConfigDict(from_attributes=True)


class ComponentFootprintItem(BaseModel):
    material_name: str
    weight_kg: float
    emissions_kg: float


class ProductFootprintOut(BaseModel):
    product_id: int
    product_name: str
    sku: str
    total_pcf_kg: float
    components: List[ComponentFootprintItem]


# Supplier Engagement Schemas
class SupplierCreate(BaseModel):
    name: str
    country: str
    category: str
    status: Optional[str] = "pending"


class SupplierOut(BaseModel):
    id: int
    name: str
    country: str
    category: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class SupplierEmissionDataCreate(BaseModel):
    reporting_period: str
    scope1_kg: float
    scope2_kg: float
    scope3_kg: float
    submitted_date: Optional[Union[str, dt_date]] = Field(default_factory=lambda: dt_date.today().isoformat())

    @field_validator("submitted_date", mode="before")
    @classmethod
    def parse_submitted_date(cls, v: Any) -> str:
        if not v:
            return dt_date.today().isoformat()
        if isinstance(v, dt_date):
            return v.isoformat()
        return str(v)


class SupplierEmissionDataOut(BaseModel):
    id: int
    supplier_id: int
    reporting_period: str
    scope1_kg: float
    scope2_kg: float
    scope3_kg: float
    submitted_date: str

    model_config = ConfigDict(from_attributes=True)


class SupplierScorecardOut(BaseModel):
    supplier_id: int
    name: str
    country: str
    category: str
    status: str
    total_reported_kg: float
    data_completeness: str
