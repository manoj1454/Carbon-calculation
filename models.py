from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)

    activities = relationship("ActivityEntry", back_populates="facility", cascade="all, delete-orphan")


class ActivityEntry(Base):
    __tablename__ = "activity_entries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False)
    scope = Column(Integer, nullable=False)
    fuel_type = Column(String, nullable=False)
    geography = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    date = Column(String, nullable=False)
    emissions_kg = Column(Float, nullable=False)

    facility = relationship("Facility", back_populates="activities")


class EmissionFactor(Base):
    __tablename__ = "emission_factors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fuel_type = Column(String, nullable=False)
    scope = Column(Integer, nullable=False)
    unit = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    geography = Column(String, nullable=False)


# Product LCA (PCF) Models
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    sku = Column(String, nullable=False, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False)

    facility = relationship("Facility")
    components = relationship("ProductComponent", back_populates="product", cascade="all, delete-orphan")


class ProductComponent(Base):
    __tablename__ = "product_components"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    material_name = Column(String, nullable=False)
    weight_kg = Column(Float, nullable=False)
    material_emission_factor_kgco2e_per_kg = Column(Float, nullable=False)

    product = relationship("Product", back_populates="components")


# Supplier Engagement Models
class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    category = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, submitted, verified

    emissions_data = relationship("SupplierEmissionData", back_populates="supplier", cascade="all, delete-orphan")


class SupplierEmissionData(Base):
    __tablename__ = "supplier_emission_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    reporting_period = Column(String, nullable=False)
    scope1_kg = Column(Float, nullable=False, default=0.0)
    scope2_kg = Column(Float, nullable=False, default=0.0)
    scope3_kg = Column(Float, nullable=False, default=0.0)
    submitted_date = Column(String, nullable=False)

    supplier = relationship("Supplier", back_populates="emissions_data")
