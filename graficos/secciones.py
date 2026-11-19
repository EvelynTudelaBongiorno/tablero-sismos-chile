import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter

from .api import RANGOS_ZONAS, ZONAS
from .utils import figura_a_imagen, numero, ROJO, GRIS, TEXTO, TENUE

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
MESES_LARGO = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
               "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

UMBRAL_SUPERFICIAL = 70      # km: los sismos más someros que esto se consideran superficiales


def entero(valor):
    return numero(valor, 0)


def mes_en_curso(info):
    """True si el período termina antes de diciembre: el último mes está incompleto."""
    return info["fin"] < pd.Timestamp(info["anio"], 12, 31)


# ---------- los tres KPI, cada uno con su valor de referencia ----------

def indicadores(df, info):
    inicio, fin = info["inicio"], info["fin"]
    dias = (fin - inicio).days + 1
    desde = fin - pd.Timedelta(days=29)                    # los últimos 30 días, hoy incluido
    ultimos = df[df["fecha"] >= desde]

    # 1 · sismos en los últimos 30 días, contra el promedio por cada 30 días del período
    n_ultimos = len(ultimos)
    ref_cantidad = len(df) / dias * 30

    # 2 · mayor magnitud del período, contra el promedio de los máximos de cada mes
    mayor = df.loc[df["mag"].idxmax()]
    max_mensual = df.groupby(df["fecha"].dt.month)["mag"].max().mean()

    # 3 · porcentaje de sismos superficiales, últimos 30 días contra todo el período
    pct_periodo = (df["prof"] < UMBRAL_SUPERFICIAL).mean() * 100
    if len(ultimos):
        pct_ultimos = (ultimos["prof"] < UMBRAL_SUPERFICIAL).mean() * 100
        kpi3 = {"valor": numero(pct_ultimos, 1), "sube": bool(pct_ultimos >= pct_periodo),
                "comparacion": f"Referencia: {numero(pct_periodo, 1)} % en todo el período"}
    else:
        kpi3 = {"valor": "—", "sube": None,
                "comparacion": f"Sin sismos en los últimos 30 días · período: {numero(pct_periodo, 1)} %"}

    return [
        {"etiqueta": "Sismos en los últimos 30 días", "valor": entero(n_ultimos), "unidad": "sismos",
         "comparacion": f"Referencia: {numero(ref_cantidad, 0)} por cada 30 días en el período",
         "detalle": f"{desde:%d/%m} al {fin:%d/%m/%Y}", "sube": bool(n_ultimos >= ref_cantidad)},
        {"etiqueta": "Mayor magnitud del período", "valor": numero(mayor["mag"], 1), "unidad": "magnitud",
         "comparacion": f"Referencia: máximo mensual típico {numero(max_mensual, 1)}",
         "detalle": f"{mayor['fecha']:%d/%m/%Y}", "sube": bool(mayor["mag"] >= max_mensual)},
        {"etiqueta": f"Sismos superficiales (< {UMBRAL_SUPERFICIAL} km)", "unidad": "% de los sismos",
         "detalle": "Últimos 30 días", **kpi3},
    ]


# ---------- vista general · 1 · Barras: sismos por mes ----------

def seccion_mensual(df, info):
    meses = range(1, info["fin"].month + 1)
    cantidad = df.groupby(df["fecha"].dt.month).size().reindex(meses, fill_value=0)
    promedio = cantidad.mean()
    alto = cantidad.idxmax()
    colores = [ROJO if m == alto else GRIS for m in cantidad.index]

    fig, ax = plt.subplots(figsize=(10, 3.9))
    barras = ax.bar([MESES[m - 1] for m in cantidad.index], cantidad.values, color=colores, width=0.7)
    ax.bar_label(barras, labels=[entero(v) if m == alto else "" for m, v in cantidad.items()],
                 padding=4, fontsize=9, color=TEXTO)
    ax.axhline(promedio, color=TENUE, linestyle=(0, (4, 4)), linewidth=1)
    ax.annotate(f"Promedio {numero(promedio, 0)}", xy=(1, promedio),
                xycoords=("axes fraction", "data"), ha="right", va="bottom", fontsize=9, color=TENUE,
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.5, "alpha": 0.85})
    ax.set_ylim(0, cantidad.max() * 1.18)                  # en barras, el eje parte en cero
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: entero(v)))
    ax.set_title(f"{MESES_LARGO[alto - 1]} fue el mes más activo: {entero(cantidad.max())} sismos")
    ax.set_ylabel("Cantidad de sismos")

    lectura = (f"La línea punteada es el promedio mensual ({numero(promedio, 0)} sismos). "
               f"El mes en rojo tuvo {numero((cantidad.max() / promedio - 1) * 100, 0)} % más "
               f"actividad que ese promedio.")
    if mes_en_curso(info):
        lectura += " El último mes está incompleto: el período llega hasta hoy."
    return {"pregunta": "¿Cómo ha estado la actividad mes a mes?",
            "imagen": figura_a_imagen(fig), "lectura": lectura}


# ---------- vista general · 2 · Barras: sismos por clase de magnitud ----------

CLASES = [(4, 5, "4,0 a 4,9"), (5, 6, "5,0 a 5,9"), (6, 7, "6,0 a 6,9"), (7, 11, "7,0 o más")]


def seccion_magnitudes(df, info, mag_min):
    clases = [(a, b, texto) for a, b, texto in CLASES if b > mag_min]
    cantidad = [int(((df["mag"] >= a) & (df["mag"] < b)).sum()) for a, b, _ in clases]
    etiquetas = [texto for _, _, texto in clases]
    total = sum(cantidad)
    mayor = int(np.argmax(cantidad))
    colores = [ROJO if i == mayor else GRIS for i in range(len(cantidad))]

    fig, ax = plt.subplots(figsize=(6, 3.9))
    barras = ax.bar(etiquetas, cantidad, color=colores, width=0.65)
    ax.bar_label(barras, labels=[entero(v) for v in cantidad], padding=4, fontsize=9, color=TEXTO)
    ax.set_ylim(0, max(cantidad) * 1.15)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: entero(v)))
    ax.set_title(f"El {numero(cantidad[mayor] / total * 100, 0)} % es de magnitud {etiquetas[mayor]}")
    ax.set_xlabel("Magnitud")
    ax.set_ylabel("Cantidad de sismos")
    return {"pregunta": "¿Qué tan fuertes son los sismos?",
            "imagen": figura_a_imagen(fig),
            "lectura": "Los sismos fuertes son pocos: cada punto más de magnitud libera cerca de "
                       "32 veces más energía, y por eso cada clase tiene muchos menos eventos que la anterior."}


# ---------- vista de detalle · 1 · Mapa de dispersión: dónde y a qué profundidad ----------

def seccion_mapa(df, info):
    fig, ax = plt.subplots(figsize=(5.8, 7.6))
    tamano = (df["mag"] - 3.0).clip(lower=0.2) ** 2.6 * 7
    orden = df["prof"].sort_values(ascending=False).index   # los más profundos abajo, los someros arriba
    puntos = ax.scatter(df.loc[orden, "lon"], df.loc[orden, "lat"], s=tamano.loc[orden],
                        c=df.loc[orden, "prof"], cmap="viridis", alpha=0.65,
                        edgecolor="white", linewidth=0.3)
    # las líneas punteadas separan las cinco zonas que usa el resto del tablero
    for limite in (-26, -33, -38, -46):
        ax.axhline(limite, color="#D4D4D8", linestyle=(0, (4, 4)), linewidth=0.8, zorder=0)
    ax.set_xlim(-76, -66)
    ax.set_ylim(-56, -17)
    ax.set_aspect(1 / np.cos(np.radians(37)), adjustable="box")  # evita que el mapa se vea estirado
    ax.grid(False)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{abs(v):.0f}° O"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{abs(v):.0f}° S"))
    ax.tick_params(left=True)

    zonas = ax.secondary_yaxis("right")                     # el nombre de cada zona, en el eje derecho
    zonas.set_yticks([-21.5, -29.5, -35.5, -42, -51])
    zonas.set_yticklabels(ZONAS, fontsize=8.5)
    zonas.tick_params(right=False)
    zonas.spines["right"].set_visible(False)

    barra = fig.colorbar(puntos, ax=ax, shrink=0.5, pad=0.28)
    barra.set_label("Profundidad (km)")
    barra.outline.set_visible(False)

    muestras = [Line2D([], [], marker="o", linestyle="", markerfacecolor="#A1A1AA",
                       markeredgecolor="white", alpha=0.8,
                       markersize=float(np.sqrt((m - 3.0) ** 2.6 * 7)), label=f"{m}")
                for m in (4, 5, 6, 7)]
    ax.legend(handles=muestras, title="Magnitud", loc="upper center", bbox_to_anchor=(0.5, -0.05),
              ncol=4, fontsize=9, columnspacing=1.6, handletextpad=0.4, labelspacing=1)

    cerca = (df["prof"] < UMBRAL_SUPERFICIAL).mean() * 100
    profunda = df.groupby("zona", observed=True)["prof"].median().idxmax()
    ax.set_title("Los sismos siguen la costa")
    return {"pregunta": "¿Dónde ocurren y a qué profundidad?",
            "imagen": figura_a_imagen(fig),
            "lectura": f"Cada punto es un sismo: el color indica su profundidad y el tamaño, su magnitud. "
                       f"El {numero(cerca, 0)} % es superficial (menos de {UMBRAL_SUPERFICIAL} km). "
                       f"La zona con la mediana de profundidad más alta es {profunda}."}


# ---------- vista de detalle · 2 · Mapa de calor: zona × mes ----------

def seccion_calor(df, info):
    meses = list(range(1, info["fin"].month + 1))
    tabla = (df.pivot_table(index="zona", columns=df["fecha"].dt.month, values="mag",
                            aggfunc="count", observed=False)
               .reindex(index=ZONAS, columns=meses).fillna(0).astype(int))
    por_zona = tabla.sum(axis=1)
    zona_alta = por_zona.idxmax()
    zona_baja = por_zona.idxmin()

    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    sns.heatmap(tabla, annot=True, fmt="d", cmap="Reds", linewidths=1.5, linecolor="white",
                cbar_kws={"label": "Sismos", "shrink": 0.8}, annot_kws={"size": 8.5}, ax=ax)
    ax.set_xticklabels([MESES[m - 1] for m in meses], rotation=0)
    ax.set_yticklabels(ZONAS, rotation=0)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(left=False, bottom=False)
    ax.grid(False)
    ax.set_title(f"{zona_alta} concentra el {numero(por_zona.max() / por_zona.sum() * 100, 0)} % de los sismos")
    rangos = " · ".join(f"{z}: {RANGOS_ZONAS[z]}" for z in ZONAS)
    return {"pregunta": "¿Qué zona y qué mes concentran más sismos?",
            "imagen": figura_a_imagen(fig),
            "lectura": f"Cuanto más oscuro el cuadro, más sismos. La zona con menos actividad es "
                       f"{zona_baja} ({entero(por_zona.min())} sismos). Zonas por latitud: {rangos}."}


# ---------- vista de detalle · 3 · Cajas: profundidad por zona ----------

def seccion_profundidad(df, info):
    zonas = [z for z in ZONAS if (df["zona"] == z).any()]
    mediana = df.groupby("zona", observed=True)["prof"].median()
    profunda = mediana.idxmax()

    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    colores = [ROJO if z == profunda else GRIS for z in zonas]
    sns.boxplot(data=df, x="zona", y="prof", order=zonas, hue="zona", hue_order=zonas,
                palette=dict(zip(zonas, colores)), legend=False, width=0.55, linewidth=1,
                fliersize=2, flierprops={"alpha": 0.35}, medianprops={"color": TEXTO, "linewidth": 1.6},
                ax=ax)
    ax.invert_yaxis()                                      # la profundidad crece hacia abajo
    ax.axhline(UMBRAL_SUPERFICIAL, color=TENUE, linestyle=(0, (4, 4)), linewidth=1)
    ax.annotate(f"{UMBRAL_SUPERFICIAL} km", xy=(1, UMBRAL_SUPERFICIAL), xycoords=("axes fraction", "data"),
                ha="right", va="top", fontsize=8.5, color=TENUE)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: entero(v)))
    ax.set_xlabel("")
    ax.set_ylabel("Profundidad (km)")
    ax.set_title(f"{profunda} tiene los sismos más profundos")
    return {"pregunta": "¿En qué zonas los sismos son más profundos?",
            "imagen": figura_a_imagen(fig),
            "lectura": f"Cada caja reúne la mitad central de los sismos de la zona y la línea negra "
                       f"marca la mediana; la línea punteada a {UMBRAL_SUPERFICIAL} km separa los sismos superficiales. En {profunda} la mediana es de {numero(mediana.max(), 0)} km; "
                       f"los puntos sueltos son sismos excepcionalmente profundos."}


# ---------- tabla de los sismos más fuertes ----------

def sismos_fuertes(df, cantidad=8):
    datos = df.sort_values("mag", ascending=False).head(cantidad)
    return [{"fecha": f"{fila.fecha:%d/%m/%Y %H:%M}", "mag": numero(fila.mag, 1),
             "prof": numero(fila.prof, 0), "zona": str(fila.zona), "lugar": fila.lugar}
            for fila in datos.itertuples()]
