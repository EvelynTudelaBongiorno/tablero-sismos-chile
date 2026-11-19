from urllib.parse import urlencode

import pandas as pd
import requests
from django.core.cache import cache

# API pública del Servicio Geológico de Estados Unidos (USGS): catálogo de sismos en formato GeoJSON.
# No pide registro ni clave. Documentación: https://earthquake.usgs.gov/fdsnws/event/1/
URL_BASE = "https://earthquake.usgs.gov/fdsnws/event/1/query"

# Caja geográfica que rodea a Chile continental (latitud 56° S a 17° S, longitud 76° O a 66° O).
CAJA = {"minlatitude": -56, "maxlatitude": -17, "minlongitude": -76, "maxlongitude": -66}

# Bajo magnitud 4 el catálogo del USGS es claramente incompleto en esta zona, por eso se parte ahí.
MAGNITUD_MINIMA_API = 4.0
LIMITE_API = 20000           # máximo de eventos que entrega una consulta
DURACION_CACHE = 60 * 60     # una hora: el catálogo se actualiza continuamente, pero no es necesario más

# lista blanca de los filtros: solo estos valores se aceptan desde la dirección
MAGNITUDES = [
    {"valor": "4.0", "texto": "4,0"},
    {"valor": "4.5", "texto": "4,5"},
    {"valor": "5.0", "texto": "5,0"},
    {"valor": "5.5", "texto": "5,5"},
]

# zonas por latitud, de norte a sur (límites en grados sur)
ZONAS = ["Norte Grande", "Norte Chico", "Centro", "Sur", "Austral"]
LIMITES_ZONAS = [-56, -46, -38, -33, -26, -17]     # de sur a norte, para pd.cut
RANGOS_ZONAS = {"Norte Grande": "17°–26° S", "Norte Chico": "26°–33° S", "Centro": "33°–38° S",
                "Sur": "38°–46° S", "Austral": "46°–56° S"}


class ErrorAPI(Exception):
    """La API no respondió o respondió algo que no se puede usar."""


def construir_url(anio):
    """La dirección exacta que se consulta: todos los sismos del año dentro de la caja de Chile."""
    parametros = {
        "format": "geojson",
        "starttime": f"{anio}-01-01",
        "endtime": f"{anio + 1}-01-01",
        "minmagnitude": MAGNITUD_MINIMA_API,
        "orderby": "time-asc",
        "limit": LIMITE_API,
        **CAJA,
    }
    return f"{URL_BASE}?{urlencode(parametros)}"


def pedir_a_la_api(url):
    """Hace la petición y devuelve el JSON, o lanza ErrorAPI con un mensaje claro."""
    try:
        respuesta = requests.get(url, timeout=20)
        if respuesta.status_code == 204:             # la API responde 204 cuando no hay resultados
            raise ErrorAPI("La API no tiene sismos registrados para este período.")
        respuesta.raise_for_status()                 # 400, 500…: se trata como error
        return respuesta.json()
    except ErrorAPI:
        raise
    except requests.exceptions.Timeout:
        raise ErrorAPI("La API del USGS tardó demasiado en responder. Intente de nuevo en unos minutos.")
    except requests.exceptions.HTTPError:
        raise ErrorAPI(f"La API del USGS respondió con un error ({respuesta.status_code}).")
    except ValueError:
        raise ErrorAPI("La API del USGS respondió, pero no en formato JSON.")
    except requests.exceptions.RequestException:
        raise ErrorAPI("No fue posible conectarse a earthquake.usgs.gov. Revise la conexión a internet.")


def extraer_registros(datos):
    """Del GeoJSON, deja solo lo que usa el tablero: una lista de diccionarios simples."""
    registros = []
    for evento in datos.get("features", []):
        propiedades = evento.get("properties") or {}
        coordenadas = (evento.get("geometry") or {}).get("coordinates") or []
        if propiedades.get("type") != "earthquake" or len(coordenadas) < 3:
            continue                                  # explosiones, minería, etc. no son sismos
        registros.append({
            "tiempo": propiedades.get("time"),        # milisegundos desde 1970, en UTC
            "mag": propiedades.get("mag"),
            "lugar": propiedades.get("place") or "",
            "lon": coordenadas[0],
            "lat": coordenadas[1],
            "prof": coordenadas[2],                   # profundidad en km
        })
    return registros


def construir_dataframe(registros):
    """Convierte la lista en una tabla limpia y agrega la zona del país."""
    df = pd.DataFrame(registros, columns=["tiempo", "mag", "lugar", "lon", "lat", "prof"])
    for columna in ["tiempo", "mag", "lon", "lat", "prof"]:
        df[columna] = pd.to_numeric(df[columna], errors="coerce")
    df = df.dropna(subset=["tiempo", "mag", "lon", "lat", "prof"])

    # la caja geográfica incluye territorio vecino: se dejan los sismos que el USGS ubica en Chile
    df = df[df["lugar"].str.contains("Chile", case=False, na=False)]

    df["fecha"] = pd.to_datetime(df["tiempo"], unit="ms", utc=True).dt.tz_localize(None)   # hora UTC
    df["prof"] = df["prof"].clip(lower=0)             # algunas profundidades vienen levemente negativas
    zona = pd.cut(df["lat"], bins=LIMITES_ZONAS, labels=list(reversed(ZONAS)), include_lowest=True)
    df["zona"] = zona.cat.reorder_categories(ZONAS, ordered=True)    # de norte a sur

    return (df.drop(columns=["tiempo"])
              .drop_duplicates(subset=["fecha", "lat", "lon"])
              .sort_values("fecha")
              .reset_index(drop=True))


def obtener_sismos(anio):
    """Devuelve los sismos del año como DataFrame y un diccionario con su descripción."""
    url = construir_url(anio)
    clave = f"usgs-sismos-chile-{anio}"

    registros = cache.get(clave)                      # ¿ya se pidió hace poco?
    desde_cache = registros is not None
    truncado = False
    if registros is None:
        datos = pedir_a_la_api(url)
        truncado = len(datos.get("features", [])) >= LIMITE_API
        registros = extraer_registros(datos)
        cache.set(clave, (registros, truncado), DURACION_CACHE)
    else:
        registros, truncado = registros

    df = construir_dataframe(registros)
    if df.empty:
        raise ErrorAPI(f"La API no tiene sismos en Chile para {anio}.")

    hoy = pd.Timestamp.now("UTC").tz_localize(None).normalize()
    info = {
        "anio": anio,
        "url": url,
        "desde_cache": desde_cache,
        "truncado": truncado,
        "inicio": pd.Timestamp(anio, 1, 1),
        "fin": min(hoy, pd.Timestamp(anio, 12, 31)),  # el año en curso llega hasta hoy
    }
    return df, info
