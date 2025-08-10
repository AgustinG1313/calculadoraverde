"""
Archivo principal de la aplicación FastAPI.
Inicializa la app, configura CORS y agrega todos los routers modulares.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, users, invoices, appliances, calculations, advice, metrics

# INICIALIZACIÓN DE LA APP
app = FastAPI(
    title="BioTrack API",
    description="API para gestionar datos de consumo energético y sostenibilidad.",
    version="1.0.0"
)

# MIDDLEWARE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# INCLUSIÓN DE ROUTERS
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(invoices.router)
app.include_router(appliances.router)
app.include_router(calculations.router)
app.include_router(advice.router)
app.include_router(metrics.router)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Bienvenido a la API de BioTrack"}