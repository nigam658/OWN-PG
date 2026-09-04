from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.room_router import router as room_router
from app.routers.bed_router import router as bed_router
from app.routers.tenant_router import router as tenant_router
from app.routers.auth_router import router as auth_router
from app.routers.building_router import router as building_router
from app.routers.floor_router import router as floor_router

from app.database import Base, engine
from app.models.owner_model import Owner
from app.models.building_model import Building
from app.models.floor_model import Floor
from app.models.room_model import Room
from app.models.bed_model import Bed
from app.models.tenant_model import Tenant
from app.models.bed_allocation_model import BedAllocation
from app.models.payment_model import Payment
from app.models.monthlyrent_model import MonthlyRent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)
 
# register routers
app.include_router(room_router)
app.include_router(bed_router)
app.include_router(tenant_router)
app.include_router(auth_router)
app.include_router(building_router)
app.include_router(floor_router)