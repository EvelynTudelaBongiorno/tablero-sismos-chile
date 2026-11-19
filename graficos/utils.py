import io
import os
import base64

# en Vercel solo /tmp se puede escribir: ahí guarda matplotlib su caché de fuentes
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib
matplotlib.use("Agg")      # dibuja sin abrir ventanas: obligatorio en un servidor
import matplotlib.pyplot as plt
import seaborn as sns

ROJO = "#D40202"
GRIS = "#C4C4CC"
TEXTO = "#18181B"
TENUE = "#71717A"

# seaborn pone la base; rcParams ajusta los detalles para todos los gráficos
sns.set_theme(style="white")
plt.rcParams.update({
    "font.family": ["Inter", "Segoe UI", "Arial", "DejaVu Sans"],
    "font.size": 10.5,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",     # el título-conclusión, alineado a la izquierda
    "axes.titlepad": 14,
    "axes.titlecolor": TEXTO,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,        # sin borde izquierdo: la grilla guía la lectura
    "axes.edgecolor": "#D4D4D8",
    "axes.labelcolor": TENUE,
    "axes.grid": True,
    "axes.grid.axis": "y",            # solo líneas horizontales
    "grid.color": "#EEEEF0",
    "xtick.color": TENUE,
    "ytick.color": TENUE,
    "ytick.left": False,
    "legend.frameon": False,
})


def figura_a_imagen(fig):
    """Convierte una figura de matplotlib en texto que el HTML puede mostrar."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buffer.getvalue()).decode()


def numero(valor, decimales=0):
    """Escribe un número al estilo chileno: 1.234,5"""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")
