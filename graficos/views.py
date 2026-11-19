from datetime import date

from django.shortcuts import render

from .api import MAGNITUDES, ErrorAPI, obtener_sismos
from .secciones import (indicadores, seccion_calor, seccion_magnitudes, seccion_mapa,
                        seccion_mensual, seccion_profundidad, sismos_fuertes)


def preparar(request, vista):
    """Lo que comparten las dos vistas: validar los filtros, pedir los datos y filtrarlos."""
    # 1 · los filtros se validan contra una lista blanca antes de usarlos
    hoy = date.today()
    anios = [hoy.year - 2, hoy.year - 1, hoy.year]
    anio = request.GET.get("anio", "")
    anio = int(anio) if anio.isdigit() and int(anio) in anios else hoy.year
    permitidas = [m["valor"] for m in MAGNITUDES]
    mag_txt = request.GET.get("mag", "4.0")
    if mag_txt not in permitidas:
        mag_txt = "4.0"
    mag = float(mag_txt)

    contexto = {"vista": vista, "anios": anios, "anio": anio, "magnitudes": MAGNITUDES,
                "mag_txt": mag_txt, "mag_texto": mag_txt.replace(".", ","),
                "consulta": f"anio={anio}&mag={mag_txt}"}

    # 2 · los datos: se piden a la API; si falla, se muestra un mensaje
    try:
        df, info = obtener_sismos(anio)
    except ErrorAPI as error:
        contexto["error"] = str(error)
        return contexto, None, None

    df = df[df["mag"] >= mag]                               # el filtro de magnitud mínima
    if df.empty:
        contexto["error"] = (f"No hay sismos de magnitud {contexto['mag_texto']} o más en {anio}. "
                             f"Pruebe con una magnitud menor.")
        return contexto, None, None

    contexto.update({
        "info": info,
        "periodo": f"{info['inicio']:%d/%m/%Y} al {info['fin']:%d/%m/%Y}",
        "registros": len(df),
    })
    return contexto, df, info


def general(request):
    """Vista general: ¿cómo está la actividad sísmica? Tres KPI y dos gráficos de síntesis."""
    contexto, df, info = preparar(request, "general")
    if df is not None:
        contexto.update({
            "kpis": indicadores(df, info),
            "secciones": [seccion_mensual(df, info),
                          seccion_magnitudes(df, info, float(contexto["mag_txt"]))],
        })
    return render(request, "graficos/general.html", contexto)


def detalle(request):
    """Vista de detalle: ¿dónde y cuándo ocurren? Mapa, zona × mes y profundidad por zona."""
    contexto, df, info = preparar(request, "detalle")
    if df is not None:
        contexto.update({
            "mapa": seccion_mapa(df, info),
            "calor": seccion_calor(df, info),
            "profundidad": seccion_profundidad(df, info),
            "fuertes": sismos_fuertes(df),
        })
    return render(request, "graficos/detalle.html", contexto)
