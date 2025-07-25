"""
Simula una base de datos en memoria para el almacenamiento de datos de la aplicación.
Incluye datos de usuarios y un catálogo de electrodomésticos.
"""
from datetime import datetime

# BASE DE DATOS SIMULADA
db_usuarios = {
    "usuario1@example.com": {
        "id": "user-abc123def456",
        "username": "usuario1@example.com",
        "password": "password123",
        "nombre": "Ana García",
        "ubicacion": "Resistencia, Chaco",
        "nivel_subsidio": "medio",
        "facturas": [],
        "electrodomesticos": [],
        "puntos_sostenibilidad": 0,
        "consejos_cumplidos": [],
        "progreso_sostenibilidad": [{"fecha": "2024-01-01", "puntos": 0}]
    }
}

BASE_ELECTRODOMESTICOS = [
    {"id": "cat-001", "nombre": "Heladera c/freezer (moderno)", "potencia_base": 150, "eficiencia_estandar": "Alta", "horas_dia_estandar": 8, "dias_mes_estandar": 30},
    {"id": "cat-002", "nombre": "Freezer independiente", "potencia_base": 250, "eficiencia_estandar": "Baja", "horas_dia_estandar": 7.2, "dias_mes_estandar": 30},
    {"id": "cat-003", "nombre": "Heladera sin freezer", "potencia_base": 150, "eficiencia_estandar": "Baja", "horas_dia_estandar": 7.2, "dias_mes_estandar": 30},
    {"id": "cat-004", "nombre": "Aire Acond. Split 2200 fg Inv", "potencia_base": 877.5, "eficiencia_estandar": "Alta", "horas_dia_estandar": 1.5, "dias_mes_estandar": 30},
    {"id": "cat-005", "nombre": "Aire Acond. Split 2200 fg On/Off", "potencia_base": 1350, "eficiencia_estandar": "Baja", "horas_dia_estandar": 1.5, "dias_mes_estandar": 30},
    {"id": "cat-006", "nombre": "Lavadora Automática (sin agua)", "potencia_base": 500, "eficiencia_estandar": "Alta", "horas_dia_estandar": 0.5, "dias_mes_estandar": 10},
    {"id": "cat-007", "nombre": "Lavadora c/calefacción", "potencia_base": 2500, "eficiencia_estandar": "Baja", "horas_dia_estandar": 0.5, "dias_mes_estandar": 10},
    {"id": "cat-008", "nombre": "Horno eléctrico 30L", "potencia_base": 1500, "eficiencia_estandar": "Alta", "horas_dia_estandar": 0.75, "dias_mes_estandar": 15},
    {"id": "cat-009", "nombre": "Horno eléctrico empotrado", "potencia_base": 2450, "eficiencia_estandar": "Baja", "horas_dia_estandar": 0.75, "dias_mes_estandar": 15},
    {"id": "cat-010", "nombre": "Termotanque eléctrico", "potencia_base": 1500, "eficiencia_estandar": "Baja", "horas_dia_estandar": 1.3, "dias_mes_estandar": 30},
    {"id": "cat-011", "nombre": "Calefón eléctrico", "potencia_base": 1800, "eficiencia_estandar": "Baja", "horas_dia_estandar": 0.7, "dias_mes_estandar": 30},
    {"id": "cat-012", "nombre": "Lámpara LED 11W", "potencia_base": 11, "eficiencia_estandar": "Alta", "horas_dia_estandar": 6.0, "dias_mes_estandar": 30},
    {"id": "cat-013", "nombre": "Tubo fluorescente 58W", "potencia_base": 58, "eficiencia_estandar": "Baja", "horas_dia_estandar": 6.0, "dias_mes_estandar": 30},
    {"id": "cat-014", "nombre": "Lámpara bajo consumo 20W", "potencia_base": 20, "eficiencia_estandar": "Baja", "horas_dia_estandar": 6.0, "dias_mes_estandar": 30},
    {"id": "cat-015", "nombre": "CPU de escritorio", "potencia_base": 200, "eficiencia_estandar": "Media", "horas_dia_estandar": 4.0, "dias_mes_estandar": 30},
    {"id": "cat-016", "nombre": "Monitor LED 19\"", "potencia_base": 22, "eficiencia_estandar": "Alta", "horas_dia_estandar": 4.0, "dias_mes_estandar": 30},
    {"id": "cat-017", "nombre": "Laptop/Notebook", "potencia_base": 60, "eficiencia_estandar": "Alta", "horas_dia_estandar": 4.0, "dias_mes_estandar": 30},
    {"id": "cat-018", "nombre": "Pava eléctrica", "potencia_base": 2000, "eficiencia_estandar": "Alta", "horas_dia_estandar": 0.1, "dias_mes_estandar": 30},
    {"id": "cat-019", "nombre": "Plancha", "potencia_base": 1500, "eficiencia_estandar": "Media", "horas_dia_estandar": 0.5, "dias_mes_estandar": 10},
    {"id": "cat-020", "nombre": "Secarropas térmico", "potencia_base": 950, "eficiencia_estandar": "Media", "horas_dia_estandar": 1.0, "dias_mes_estandar": 10},
    {"id": "cat-021", "nombre": "Secarropas centrífugo", "potencia_base": 380, "eficiencia_estandar": "Media", "horas_dia_estandar": 1.0, "dias_mes_estandar": 10},
    {"id": "cat-022", "nombre": "Lavavajillas 12 cubiertos", "potencia_base": 1500, "eficiencia_estandar": "Baja", "horas_dia_estandar": 1.5, "dias_mes_estandar": 15},
    {"id": "cat-023", "nombre": "Bomba de agua 1/2 HP", "potencia_base": 380, "eficiencia_estandar": "Media", "horas_dia_estandar": 1.0, "dias_mes_estandar": 30},
    {"id": "cat-024", "nombre": "Bomba de agua 3/4 HP", "potencia_base": 570, "eficiencia_estandar": "Media", "horas_dia_estandar": 1.0, "dias_mes_estandar": 30},
    {"id": "cat-025", "nombre": "Anafe vitrocerámico", "potencia_base": 2350, "eficiencia_estandar": "Alta", "horas_dia_estandar": 0.5, "dias_mes_estandar": 30},
    {"id": "cat-026", "nombre": "Anafe resistivo", "potencia_base": 2000, "eficiencia_estandar": "Baja", "horas_dia_estandar": 0.5, "dias_mes_estandar": 30},
    {"id": "cat-027", "nombre": "Cafetera eléctrica filtro", "potencia_base": 900, "eficiencia_estandar": "Alta", "horas_dia_estandar": 0.25, "dias_mes_estandar": 10},
    {"id": "cat-028", "nombre": "Secador de cabello", "potencia_base": 2000, "eficiencia_estandar": "Media", "horas_dia_estandar": 0.2, "dias_mes_estandar": 6},
    {"id": "cat-029", "nombre": "Tostadora", "potencia_base": 950, "eficiencia_estandar": "Alta", "horas_dia_estandar": 0.1, "dias_mes_estandar": 30},
    {"id": "cat-030", "nombre": "Cargador de celular", "potencia_base": 5, "eficiencia_estandar": "Alta", "horas_dia_estandar": 6.0, "dias_mes_estandar": 30},
    {"id": "cat-031", "nombre": "Consola en standby", "potencia_base": 100, "eficiencia_estandar": "Baja", "horas_dia_estandar": 2.0, "dias_mes_estandar": 30},
    {"id": "cat-032", "nombre": "Router WiFi", "potencia_base": 10, "eficiencia_estandar": "Alta", "horas_dia_estandar": 24.0, "dias_mes_estandar": 30},
]