# Sismicidad en Chile · Ficha técnica

**Aplicación desplegada:** https://tablero-sismos-chile.vercel.app

**Repositorio:** https://github.com/EvelynTudelaBongiorno/tablero-sismos-chile

**Integrantes:** Evelyn Tudela Bongiorno  
Asignatura:Visualización de Datos (INACAP) · Evaluación N°3 · Docente: Fernando Aguilera

---

## 1. El tema

**Qué se analiza.** La actividad sísmica de Chile en los últimos tres años: cuántos sismos ocurren, qué tan fuertes son, dónde se concentran y a qué profundidad.

**A quién le sirve.** A quien planifica o comunica la preparación ante sismos: encargados de emergencia municipales y regionales, equipos de prevención de riesgos de empresas, y docentes o estudiantes que necesitan datos reales para entender el fenómeno. No sirve para alertar ni para predecir.

**Preguntas que responde el tablero**

| Vista | Pregunta | Gráfico |
|---|---|---|
| General | ¿Cómo está la actividad ahora, comparada con lo habitual? | 3 KPI |
| General | ¿Cómo ha estado la actividad mes a mes? | Barras por mes |
| General | ¿Qué tan fuertes son los sismos? | Barras por clase de magnitud |
| Detalle | ¿Dónde ocurren y a qué profundidad? | Mapa de dispersión |
| Detalle | ¿Qué zona y qué mes concentran más sismos? | Mapa de calor zona × mes |
| Detalle | ¿En qué zonas los sismos son más profundos? | Diagrama de cajas |

**Filtros.** Año (los últimos tres) y magnitud mínima (4,0 · 4,5 · 5,0 · 5,5). Ambos modifican todos los indicadores y gráficos, y se conservan al cambiar de vista.

**Decisión que permite.** Dónde y cuándo reforzar la preparación: por ejemplo, si el último mes está sobre lo habitual, qué zona del país concentra los eventos y si los sismos de esa zona suelen ser superficiales (más dañinos) o profundos.

---

## 2. La API

**API utilizada:** catálogo de sismos del Servicio Geológico de Estados Unidos (USGS), `https://earthquake.usgs.gov/fdsnws/event/1/query`. Es pública, no requiere registro ni clave, y cualquier persona puede repetir la consulta desde el navegador (la dirección exacta se muestra al final de cada vista del tablero).

**Qué entrega.** Un GeoJSON con un evento por sismo: fecha y hora (UTC, en milisegundos), magnitud, ubicación en texto, longitud, latitud y profundidad en kilómetros.

**Cómo se accede.** Una petición `GET` por año, con estos parámetros:

| Parámetro | Valor | Para qué |
|---|---|---|
| `starttime` / `endtime` | `AAAA-01-01` / `AAAA+1-01-01` | El año elegido |
| `minmagnitude` | `4.0` | Piso de magnitud (ver limitaciones) |
| `minlatitude` / `maxlatitude` | `-56` / `-17` | Caja que rodea a Chile |
| `minlongitude` / `maxlongitude` | `-76` / `-66` | Caja que rodea a Chile |
| `orderby`, `limit` | `time-asc`, `20000` | Orden y máximo de eventos |

**Limitaciones**

- **Cobertura desigual según la magnitud.** La cobertura del USGS es más completa en magnitudes altas: entre 4,0 y 4,5 puede faltar algún evento, y bajo 4,0 el catálogo es claramente incompleto, por eso el tablero no permite bajar de 4,0.
- **No es la fuente oficial en Chile.** El Centro Sismológico Nacional (sismologia.cl) publica magnitudes y ubicaciones que pueden diferir de las del USGS. El pie de página del tablero lo declara.
- **La caja geográfica es un rectángulo** e incluye territorio vecino. Por eso solo se conservan los eventos cuyo texto de ubicación (`place`) menciona Chile (ver sección 4).
- **Máximo de 20.000 eventos por consulta.** Si una consulta lo alcanza, el tablero muestra un aviso de datos posiblemente incompletos.
- **Hora en UTC**, no hora de Chile. Todas las fechas del tablero están en UTC.
- **Sin garantías de disponibilidad.** Si la API no responde, el tablero muestra un mensaje explicando qué pasó (sin conexión, tiempo agotado, error del servidor, formato inválido o sin datos) y mantiene los filtros.

---

## 3. Decisiones de visualización

Cada gráfico responde una pregunta declarada y se eligió el tipo más preciso para ella.

### Vista general · ¿cómo está?

**Barras por mes** · *¿Cómo ha estado la actividad mes a mes?*
Se comparan cantidades entre categorías ordenadas en el tiempo; la longitud de la barra es la codificación más precisa para comparar cantidades. El eje parte en cero. El mes más alto va en rojo y una línea punteada marca el promedio mensual.

**Barras por clase de magnitud** · *¿Qué tan fuertes son los sismos?*
La magnitud se agrupa en clases (4,0–4,9, 5,0–5,9, 6,0–6,9, 7,0 o más) porque la pregunta es por la proporción de sismos fuertes, no por el valor exacto de cada uno. Las clases bajo la magnitud mínima del filtro no se dibujan.

### Vista de detalle · ¿dónde y cuándo?

**Mapa de dispersión (4 variables: longitud, latitud, profundidad y magnitud)** · *¿Dónde ocurren y a qué profundidad?*
Longitud y latitud ubican el sismo; el **color** (escala viridis, secuencial) indica la profundidad y el **tamaño** indica la magnitud. Las líneas punteadas separan las cinco zonas que usan los otros gráficos. Los puntos más profundos se dibujan debajo de los someros para que no los tapen.

**Mapa de calor zona × mes (3 variables: zona, mes y cantidad)** · *¿Qué zona y qué mes concentran más sismos?*
Cruza dos categorías y muestra la cantidad en color y en número. Permite ver al mismo tiempo cuál zona concentra más sismos y si hay meses atípicos dentro de cada una.

**Diagrama de cajas (zona y profundidad)** · *¿En qué zonas los sismos son más profundos?*
La profundidad no se resume bien con un promedio: tiene muchos valores bajos y pocos extremos. La caja muestra la mitad central, la línea la mediana y los puntos sueltos los casos excepcionales. La línea punteada a 70 km marca el límite convencional entre sismo superficial y profundo.

### Gráfico descartado

**Gráfico de torta de sismos por zona.** Se consideró para mostrar cómo se reparten los sismos entre las cinco zonas. Se descartó porque comparar ángulos entre cinco sectores de tamaño parecido es impreciso, no permite agregar el mes como segunda dimensión y los sectores pequeños (Austral) se vuelven ilegibles. El mapa de calor responde la misma pregunta con números visibles y suma el tiempo.

**Líneas con la cantidad diaria de sismos.** También se descartó: la mayoría de los días tiene pocos sismos, la serie sube y baja sin patrón y se leía como ruido. Agrupar por mes muestra la tendencia sin perder información útil.

---

## 4. Preparación de los datos

**Consumo de la API** (`graficos/api.py`). Se piden los sismos de un año completo (con magnitud ≥ 4,0) y el filtro de magnitud mínima se aplica después en pandas, así cambiar de magnitud no obliga a volver a consultar. La respuesta se guarda una hora en la caché de Django.

```python
respuesta = requests.get(url, timeout=20)
if respuesta.status_code == 204:        # la API responde 204 cuando no hay resultados
    raise ErrorAPI("La API no tiene sismos registrados para este período.")
respuesta.raise_for_status()            # 400, 500…: se trata como error
datos = respuesta.json()
```

Todas las fallas (`Timeout`, `HTTPError`, `ValueError`, `RequestException`) se traducen a un único error propio, `ErrorAPI`, con un mensaje para el usuario. La vista lo muestra en vez de caerse.

**Lista blanca de filtros** (`graficos/views.py`). El año y la magnitud que llegan en la dirección se validan contra valores permitidos antes de usarlos; si no coinciden, se usa un valor por defecto.

**Limpieza** (`construir_dataframe` en `graficos/api.py`):

```python
# 1 · solo sismos: se descartan explosiones y otros eventos
if propiedades.get("type") != "earthquake" or len(coordenadas) < 3: continue

# 2 · valores numéricos; se eliminan los registros incompletos
df[columna] = pd.to_numeric(df[columna], errors="coerce")
df = df.dropna(subset=["tiempo", "mag", "lon", "lat", "prof"])

# 3 · la caja geográfica incluye territorio vecino: se dejan los que el USGS ubica en Chile
df = df[df["lugar"].str.contains("Chile", case=False, na=False)]

# 4 · fecha legible (UTC) y profundidades levemente negativas llevadas a cero
df["fecha"] = pd.to_datetime(df["tiempo"], unit="ms", utc=True).dt.tz_localize(None)
df["prof"] = df["prof"].clip(lower=0)

# 5 · zona por latitud, de norte a sur
df["zona"] = pd.cut(df["lat"], bins=LIMITES_ZONAS, labels=list(reversed(ZONAS)), include_lowest=True)

# 6 · sin duplicados y ordenado de lo más antiguo a lo más reciente
df.drop_duplicates(subset=["fecha", "lat", "lon"]).sort_values("fecha")
```

**Zonas.** Se definen por latitud porque el USGS no entrega región administrativa: Norte Grande (17°–26° S), Norte Chico (26°–33° S), Centro (33°–38° S), Sur (38°–46° S) y Austral (46°–56° S). Son una simplificación y no coinciden con los límites regionales oficiales.

**Trazabilidad.** La URL exacta consultada, el período de los datos, la fuente y el aviso de caché o de datos incompletos se muestran en la interfaz.

---

## 5. Los indicadores

Cada KPI muestra su valor, su unidad y un valor de referencia. Los tres se calculan sobre los sismos que cumplen el filtro de año y magnitud mínima.

| KPI | Fórmula | Unidad | Valor de referencia |
|---|---|---|---|
| **Sismos en los últimos 30 días** | Cantidad de sismos entre `fin − 29 días` y `fin` (el año en curso termina hoy) | sismos | **Promedio histórico del período:** `total de sismos ÷ días del período × 30` |
| **Mayor magnitud del período** | `máximo(magnitud)` | magnitud | **Máximo mensual típico:** promedio de la magnitud máxima de cada mes |
| **Sismos superficiales (< 70 km)** | `sismos con profundidad < 70 km ÷ total de sismos × 100`, en los últimos 30 días | % de los sismos | **Promedio histórico del período:** el mismo porcentaje calculado sobre todo el período |

El umbral de 70 km es la convención del USGS para clasificar un sismo como superficial: los más someros suelen causar mayor daño en superficie.

---

## 6. Propuesta de valor y ética

**Qué decisión permite tomar.** Una persona que planifica prevención puede ver de una mirada si la actividad reciente está sobre lo habitual (vista general) y, en el detalle, qué zona concentra los eventos y si son superficiales o profundos. Sirve para priorizar dónde reforzar la comunicación y la preparación, no para anticipar un sismo.

**A quién le sirve y a quiénes afecta.**

- *Le sirve* a encargados de emergencia, prevención de riesgos y comunidades educativas.
- *Afecta* a las personas que viven en las zonas mostradas: una cifra sobre el promedio puede generar alarma, y una cifra bajo el promedio puede dar falsa tranquilidad.
- *Afecta* a la reputación de la fuente oficial: un tablero que se parezca a un sistema de alerta podría competir con ella o ser confundido con una.

**Dilema ético que enfrentó el grupo.** Un indicador como «sismos en los últimos 30 días, sobre el promedio» puede interpretarse como una señal de que «viene uno grande», aunque la sismología no permite predecir sismos. Había que decidir entre mostrar el indicador con una lectura llamativa o priorizar la prudencia.

**Qué se decidió.**

1. Los indicadores se comparan contra una referencia histórica y se describen en lenguaje neutro: no hay etiquetas de alerta ni palabras como «peligro» o «riesgo».
2. Cada vista declara en el pie de página que el tablero **no predice sismos** y que la fuente oficial en Chile es el Centro Sismológico Nacional, con enlace.
3. Se muestra siempre la fuente, el período y la URL consultada, para que un tercero pueda verificar el dato y detectar diferencias con el catálogo oficial.
4. Se fija una magnitud mínima de 4,0 para no mostrar conteos de sismos pequeños, que dependen de la capacidad de detección de las estaciones y no de la actividad real.
5. Las ubicaciones se muestran como zonas amplias y como el texto del USGS, sin precisión que dé a entender un nivel de detalle que los datos no tienen.

---

## Cómo correrlo y publicarlo

```
cd tablero_sismos_chile
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver
```

Abrir http://127.0.0.1:8000/ (requiere conexión a internet).

Para publicar: subir la carpeta a GitHub con `manage.py` en la raíz, importar el repositorio en vercel.com (*Add New → Project*), agregar la variable de entorno `SECRET_KEY` con un valor largo y aleatorio y presionar *Deploy*. Cada `git push` a `main` publica una versión nueva.

**Estructura**

```
graficos/
├── api.py          # consulta al USGS: petición, errores, caché, limpieza y zonas
├── secciones.py    # 3 KPI y 5 gráficos
├── views.py        # valida filtros, pide datos y arma las dos vistas
├── urls.py         # "/" (general) y "/detalle/"
├── utils.py        # estilo de los gráficos, figura_a_imagen, numero
└── templates/graficos/
    ├── base.html   # portada, menú, filtros, trazabilidad
    ├── general.html
    └── detalle.html
```

**Fuente de los datos:** USGS Earthquake Catalog, https://earthquake.usgs.gov/fdsnws/event/1/
