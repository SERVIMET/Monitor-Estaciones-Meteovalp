from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import json
import os
import re
import ssl
import subprocess
import time
import urllib.request

# ==========================================
# CONFIGURACION GENERAL
# ==========================================
TOLERANCIA_MINUTOS = 12
LIMITE_LECTURAS_REPETIDAS = 10
ZONA_CHILE = ZoneInfo("America/Santiago")
ZONA_PASCUA = ZoneInfo("Pacific/Easter")
ARCHIVO_HISTORIAL = "historial_presion.json"
ARCHIVO_CONGELADAS = "historial_congeladas.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# ==========================================
# ESTACIONES DIRECTEMAR (Clásicas de texto)
# ==========================================
ESTACIONES_DIRECTEMAR = [
    {
        "nombre": "Capitania de Puerto Chanaral",
        "url": "http://web.directemar.cl/met/jturno/estaciones/chanaral/index.htm",
        "lat": -26.347,
        "lon": -70.621,
    },
    {
        "nombre": "Capitania de Puerto Caldera",
        "url": "http://web.directemar.cl/met/jturno/estaciones/caldera/index.htm",
        "lat": -27.068,
        "lon": -70.819,
    },
    {
        "nombre": "Capitania de Puerto Hanga Roa",
        "url": "http://web.directemar.cl/met/jturno/estaciones/pascua/index.htm",
        "lat": -27.150,
        "lon": -109.429,
        "es_insular": True,
    },
    {
        "nombre": "Capitania de Puerto Huasco",
        "url": "http://web.directemar.cl/met/jturno/estaciones/huasco/index.htm",
        "lat": -28.468,
        "lon": -71.226,
    },
    {
        "nombre": "Faro Punta Tortuga Coquimbo",
        "url": "http://web.directemar.cl/met/jturno/estaciones/tortuga/index.htm",
        "lat": -29.939,
        "lon": -71.352,
    },
    {
        "nombre": "Capitania de Puerto Los Vilos",
        "url": "http://web.directemar.cl/met/jturno/estaciones/losvilos/index.htm",
        "lat": -31.916,
        "lon": -71.516,
    },
    {
        "nombre": "Capitania de Puerto Quintero",
        "url": "http://web.directemar.cl/met/jturno/estaciones/quintero/index.htm",
        "lat": -32.778,
        "lon": -71.531,
    },
    {
        "nombre": "Colegio Capellan Pascal (Las Salinas)",
        "url": "http://web.directemar.cl/met/jturno/estaciones/lassalinas/index.htm",
        "lat": -33.015,
        "lon": -71.550,
    },
    {
        "nombre": "Faro Extremo Molo de Abrigo Valparaiso",
        "url": "http://web.directemar.cl/met/jturno/estaciones/valparaiso/index.htm",
        "lat": -33.036,
        "lon": -71.631,
    },
    {
        "nombre": "Faro Punta Panul San Antonio",
        "url": "http://web.directemar.cl/met/jturno/estaciones/panul/index.htm",
        "lat": -33.578,
        "lon": -71.616,
    },
    {
        "nombre": "Capitania de Puerto Juan Fernandez",
        "url": "http://web.directemar.cl/met/jturno/estaciones/cumberland/index.htm",
        "lat": -33.635,
        "lon": -78.841,
    },
    {
        "nombre": "Capitania de Puerto Pichilemu",
        "url": "http://web.directemar.cl/met/jturno/estaciones/pichilemu/index.htm",
        "lat": -34.391,
        "lon": -72.001,
    },
]

# ==========================================
# ESTACIONES WEATHERLINK (Con sus enlaces correctos)
# ==========================================
ESTACIONES_WEATHERLINK = [
    {
        "nombre": "Universidad de Valparaiso (sede Montemar)",
        "url": "https://weatherlink.com/embeddablePage/show/a1debe35d26b4e2dbcf82122501f5fa6/fullscreen",
        "lat": -32.952,
        "lon": -71.553,
    },
    {
        "nombre": "Club de Yates Recreo (Vina del Mar)",
        "url": "https://weatherlink.com/embeddablePage/show/0c66339eed4f47d4a9240ed0b66c992/fullscreen",
        "lat": -33.027,
        "lon": -71.554,
    },
    {
        "nombre": "WL Chilquinta Muelle Baron (Valparaiso)",
        "url": "https://weatherlink.com/embeddablePage/show/6342b5802c854216a359487f335f3718/fullscreen",
        "lat": -33.042,
        "lon": -71.603,
    },
    {
        "nombre": "Dique Flotante Valparaiso III",
        "url": "https://weatherlink.com/embeddablePage/show/1e4869cc59824e6893fc56b963304664/fullscreen",
        "lat": -33.038,
        "lon": -71.621,
    },
    {
        "nombre": "Cofradia Nautica del Pacifico (Algarrobo)",
        "url": "https://weatherlink.com/embeddablePage/show/9fa531d050e648a9a8aa6bb7026c3902/fullscreen",
        "lat": -33.367,
        "lon": -71.666,
    },
]

# Lista para el orden visual en la grilla y mapa
ORDEN_ESTACIONES = [
    "Capitania de Puerto Chanaral",
    "Capitania de Puerto Caldera",
    "Capitania de Puerto Hanga Roa",
    "Capitania de Puerto Huasco",
    "Faro Punta Tortuga Coquimbo",
    "Capitania de Puerto Los Vilos",
    "Capitania de Puerto Quintero",
    "Universidad de Valparaiso (sede Montemar)",
    "Colegio Capellan Pascal (Las Salinas)",
    "Club de Yates Recreo (Vina del Mar)",
    "WL Chilquinta Muelle Baron (Valparaiso)",
    "Dique Flotante Valparaiso III",
    "Faro Extremo Molo de Abrigo Valparaiso",
    "Gobernacion Maritima de Valparaiso",
    "Cofradia Nautica del Pacifico (Algarrobo)",
    "Faro Punta Panul San Antonio",
    "Capitania de Puerto Juan Fernandez",
    "Capitania de Puerto Pichilemu",
]

def obtener_hora_chile():
    return datetime.now(ZONA_CHILE)

def convertir_numero(valor):
    if valor is None:
        return None
    try:
        val_str = str(valor).strip()
        if any(c in val_str.lower() for c in ["color", "purple", "line", "data", "{", "}"]):
            return None
        return float(val_str.replace(",", "."))
    except (ValueError, TypeError):
        return None

def formatear_direccion(dir_str):
    if not dir_str:
        return ""
    d = str(dir_str).upper().strip()
    if any(c in d.lower() for c in ["color", "purple", "line", "data", "{", "}"]):
        return ""
    if len(d) == 3:
        return f"{d[0]}/{d[1:]}"
    return d

def grados_a_cardinal(grados):
    if grados is None:
        return "N/D"
    direcciones = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    indice = int((grados + 11.25) / 22.5) % 16
    return formatear_direccion(direcciones[indice])

def verificar_estacion_congelada(nombre_estacion, temp, viento, racha):
    estaciones_excluidas = []
    if nombre_estacion.lower() in estaciones_excluidas:
        return False

    historial = {}
    if os.path.exists(ARCHIVO_CONGELADAS):
        try:
            with open(ARCHIVO_CONGELADAS, "r", encoding="utf-8") as f:
                historial = json.load(f)
        except Exception:
            historial = {}

    firma_actual = f"{temp}_{viento}_{racha}"
    
    if nombre_estacion not in historial:
        historial[nombre_estacion] = {"firma": firma_actual, "contador": 1}
    else:
        datos_est = historial[nombre_estacion]
        if datos_est.get("firma") == firma_actual:
            datos_est["contador"] = datos_est.get("contador", 1) + 1
        else:
            historial[nombre_estacion] = {"firma": firma_actual, "contador": 1}

    try:
        with open(ARCHIVO_CONGELADAS, "w", encoding="utf-8") as f:
            json.dump(historial, f)
    except Exception:
        pass

    return historial[nombre_estacion]["contador"] >= LIMITE_LECTURAS_REPETIDAS

def gestionar_historial_presion(nombre_estacion, presion_actual):
    ahora = obtener_hora_chile()
    historial = {}
    if os.path.exists(ARCHIVO_HISTORIAL):
        try:
            with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
                historial = json.load(f)
        except Exception:
            historial = {}

    if nombre_estacion not in historial: