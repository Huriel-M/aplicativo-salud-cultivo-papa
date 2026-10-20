# -*- coding: utf-8 -*-
"""
Created on Wed Aug 26 21:53:46 2026

@author: LUIS
"""

# ============================================================
# PROCESAMIENTO DE IMÁGENES SENTINEL-2
# Proyecto de grado
# Análisis del estado de salud de cultivos de papa
# ============================================================

import os
import glob
import csv
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt
import rasterio
from skimage.transform import resize

# 1. CONFIGURACIÓN DE CARPETAS============================

# Carpeta principal del proyecto
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent

# Carpeta donde se encuentran las bandas Sentinel-2
BAND_FOLDER = Path(
    globals().get("CARPETA_IMAGENES",
        r"D:\Proyecto de Grado\Proyecto_Grado\datos\Imagenes_13"))

# Carpeta donde se guardarán los resultados
OUTDIR = PROJECT_DIR / "resultados"

OUTDIR.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("PROCESAMIENTO DE IMÁGENES SENTINEL-2")
print("=" * 60)

print("Carpeta de bandas:")
print(BAND_FOLDER)

print("\nCarpeta de resultados:")
print(OUTDIR)

# 2. LONGITUDES DE ONDA DE SENTINEL-2=======================

BAND_WAVELENGTHS = {
    "B01": 443,
    "B02": 490,
    "B03": 560,
    "B04": 665,
    "B05": 705,
    "B06": 740,
    "B07": 783,
    "B08": 842,
    "B8A": 865,
    "B09": 945,
    "B11": 1610,
    "B12": 2190
}
# 3. BUSCAR ARCHIVOS DE BANDAS=============================

def find_band_files(folder):

    files = glob.glob(os.path.join(str(folder), "*"))

    band_files = {}

    for f in files:

        name = os.path.basename(f).upper()

        for b in BAND_WAVELENGTHS.keys():

            if b in name:
                band_files[b] = f

    return band_files

# 4. CARGAR BANDA===================================

def load_band(path):
    with rasterio.open(path) as src:
        arr = src.read(1).astype(np.float32)

    return arr

# 5. BUSCAR Y CARGAR BANDAS=======================

band_files = find_band_files(BAND_FOLDER)

print("\nBandas encontradas:")
print(sorted(band_files.keys()))

if len(band_files) == 0:

    raise FileNotFoundError("\nNo se encontraron imágenes de bandas Sentinel-2.\n"
        "Verifica que estén dentro de:\n"
        f"{BAND_FOLDER}")

bands = {}

for b, p in band_files.items():

    bands[b] = load_band(p)

    print(f"Cargada {b}: "
        f"shape={bands[b].shape}, "
        f"min={bands[b].min():.3f}, "
        f"max={bands[b].max():.3f}")
    
# 6. CONTROL DE COMPATIBILIDAD ESPACIAL

print("\n" + "=" * 60)
print("CONTROL DE COMPATIBILIDAD ESPACIAL")
print("=" * 60)

formas = set()
resoluciones = set()
sistemas_referencia = set()

for b, p in band_files.items():

    with rasterio.open(p) as src:

        formas.add(src.shape)
        resoluciones.add(src.res)
        sistemas_referencia.add(str(src.crs))

if (len(formas) == 1 and len(resoluciones) == 1 and len(sistemas_referencia) == 1):

    print("✓ Todas las bandas tienen dimensiones, "
          "resolución y CRS compatibles.")

else:

    print("ERROR: Las bandas no son espacialmente compatibles.")

    print("Revise las bandas descargadas y vuelva a cargarlas.")

    raise ValueError("Procesamiento detenido: las bandas tienen "
                     "diferencias de dimensiones, resolución o CRS.")

# 6.1 APLICACIÓN DEL ÁREA DE INTERÉS (AOI)======================

AOI_BOUNDS = globals().get("AOI_BOUNDS", None)

if AOI_BOUNDS is not None:

    print("\n" + "=" * 60)
    print("APLICANDO ÁREA DE INTERÉS (AOI)")
    print("=" * 60)

    x1, y1, x2, y2 = AOI_BOUNDS

    # Dimensiones actuales de la imagen de referencia
    shape_ref = bands["B04"].shape

    # Asegurar límites válidos
    x1 = max(0, int(x1))
    y1 = max(0, int(y1))
    x2 = min(shape_ref[1], int(x2))
    y2 = min(shape_ref[0], int(y2))

    if x2 <= x1 or y2 <= y1:
        raise ValueError("El área de interés seleccionada no es válida.")

    print(f"AOI seleccionada: x={x1}:{x2}, y={y1}:{y2}")

    for b in bands:
        bands[b] = bands[b][y1:y2, x1:x2]

    print("Nueva dimensión de las bandas:", bands["B04"].shape)

else:
    print("\nNo se seleccionó AOI.")
    print("Se procesará la imagen completa.")
      
# 7. IMAGEN RGB====================================

print("\nGenerando imagen RGB...")

rgb = np.dstack(
       (bands["B04"],
        bands["B03"],
        bands["B02"] ) )

rgb_max = np.percentile(rgb, 98)

if rgb_max > 0:

    rgb = rgb / rgb_max

rgb = np.clip(rgb, 0, 1)

plt.figure(figsize=(6, 6))

plt.imshow(rgb)

plt.title("Imagen RGB Sentinel-2")

plt.axis("off")

plt.show()

# 8. DEFINICIÓN DE BANDAS==================================

NIR = bands["B08"]

RED = bands["B04"]

GREEN = bands["B03"]

BLUE = bands["B02"]

REDEDGE = bands["B05"]

SWIR = bands["B11"]

epsilon = 1e-6

# 9. NDVI======================================

print("\nCalculando NDVI...")

NDVI = ((NIR - RED)/(NIR + RED + epsilon))

NDVI = np.where(np.isfinite(NDVI),NDVI,np.nan)

NDVI = np.clip(NDVI, -1, 1)

vmin = np.nanpercentile(NDVI, 2)

vmax = np.nanpercentile(NDVI, 98)

plt.figure(figsize=(6, 6))

plt.imshow(NDVI, cmap="RdYlGn", vmin=vmin, vmax=vmax)

plt.title("NDVI")

plt.colorbar()

plt.axis("off")

plt.show()

# Máscara de vegetación=======================
veg_mask = NDVI > 0.3
NDVI[~veg_mask] = np.nan

print("NDVI promedio =", np.nanmean(NDVI))

print("NDVI std =", np.nanstd(NDVI))

# 10. NDRE=========================================

print("\nCalculando NDRE...")#=======================

NDRE = ((NIR - REDEDGE)/(NIR + REDEDGE + epsilon))

NDRE = np.where(np.isfinite(NDRE),NDRE,np.nan)

NDRE = np.clip(NDRE, -1, 1)

NDRE[~veg_mask] = np.nan

print("NDRE después de aplicar veg_mask:")
print("  Mínimo =", np.nanmin(NDRE))
print("  Máximo =", np.nanmax(NDRE))

vmin = np.nanpercentile(NDRE, 2)

vmax = np.nanpercentile(NDRE, 98)

plt.figure(figsize=(6, 6))

plt.imshow(NDRE, cmap="RdYlGn", vmin=vmin, vmax=vmax )

plt.title("NDRE")

plt.colorbar()

plt.axis("off")

plt.show()

print("NDRE promedio =", np.nanmean(NDRE))

print("NDRE std =", np.nanstd(NDRE))

# 11. EVI=============================================

print("\nCalculando EVI...")

EVI = (2.5*(NIR - RED)/(NIR + 6 * RED - 7.5 * BLUE + 1 + epsilon))

EVI = np.where(np.isfinite(EVI),EVI,np.nan )

EVI = np.clip(EVI, -1, 1)

EVI[~veg_mask] = np.nan

print("EVI después de aplicar veg_mask:")
print("  Mínimo =", np.nanmin(EVI))
print("  Máximo =", np.nanmax(EVI))

vmin = np.nanpercentile(EVI, 2)
vmax = np.nanpercentile(EVI, 98)

plt.figure(figsize=(6, 6))

plt.imshow(EVI, cmap="RdYlGn", vmin=vmin, vmax=vmax )

plt.title("EVI")

plt.colorbar()

plt.axis("off")

plt.show()

print("EVI promedio =", np.nanmean(EVI))
print("EVI std =", np.nanstd(EVI))

# 12. NDMI===========================================

print("\nCalculando NDMI...")

NDMI = ((NIR - SWIR)/(NIR + SWIR + epsilon))

NDMI = np.where(np.isfinite(NDMI),NDMI,np.nan )

NDMI = np.clip(NDMI, -1, 1)

NDMI[~veg_mask] = np.nan

print("NDMI después de aplicar veg_mask:")
print("  Mínimo =", np.nanmin(NDMI))
print("  Máximo =", np.nanmax(NDMI))

vmin = np.nanpercentile(NDMI, 2)

vmax = np.nanpercentile(NDMI, 98)

plt.figure(figsize=(6, 6))

plt.imshow(NDMI, cmap="BrBG", vmin=vmin, vmax=vmax)

plt.title("NDMI")

plt.colorbar()

plt.axis("off")

plt.show()

print("NDMI promedio =", np.nanmean(NDMI))

print("NDMI std =", np.nanstd(NDMI))

# 13. CIRED-EDGE / RCI====================================

print("\nCalculando CIred-edge (RCI)...")

RCI = (NIR/(REDEDGE + epsilon)) - 1

RCI = np.where(np.isfinite(RCI),RCI,np.nan)

RCI[~veg_mask] = np.nan

vmin = np.nanpercentile(RCI, 2)

vmax = np.nanpercentile(RCI, 98)

plt.figure(figsize=(6, 6))

plt.imshow(RCI, cmap="YlGn", vmin=vmin, vmax=vmax )

plt.title("CIred-edge (RCI)")

plt.colorbar(label="RCI")

plt.axis("off")

plt.show()

print("RCI promedio =", np.nanmean(RCI))

print("RCI std =", np.nanstd(RCI))

print("RCI mínimo =", np.nanmin(RCI))

print("RCI máximo =", np.nanmax(RCI))

# 14. TCARI / OSAVI=====================================

print("\nCalculando TCARI/OSAVI...")

red_valid = (RED > 0)

TCARI = 3 * ((REDEDGE - RED)- 0.2 * (REDEDGE - GREEN)* (REDEDGE / (RED + epsilon)))

OSAVI = (1.16 * (NIR - RED) / (NIR + RED + 0.16 + epsilon))

TCARI_OSAVI = TCARI / OSAVI

TCARI_OSAVI = np.where(np.isfinite(TCARI_OSAVI) & red_valid & veg_mask,TCARI_OSAVI,np.nan)

vmin = np.nanpercentile(TCARI_OSAVI, 2)
vmax = np.nanpercentile(TCARI_OSAVI, 98)

plt.figure(figsize=(6, 6))

plt.imshow(TCARI_OSAVI, cmap="RdYlGn_r", vmin=vmin, vmax=vmax)

plt.title("TCARI/OSAVI")

plt.colorbar(label="TCARI/OSAVI")

plt.axis("off")

plt.show()

print("TCARI/OSAVI promedio =" ,np.nanmean(TCARI_OSAVI))

print("TCARI/OSAVI std =" ,np.nanstd(TCARI_OSAVI))

print("TCARI/OSAVI mínimo =" ,np.nanmin(TCARI_OSAVI))

print("TCARI/OSAVI máximo =" ,np.nanmax(TCARI_OSAVI))

# 15. LAI=========================================

print("\nCalculando LAI...")

NDVI_safe = np.clip(NDVI,0,0.95)

LAI_NDVI = (-np.log((1 - NDVI_safe)/0.69))

LAI_NDVI = np.where(np.isfinite(LAI_NDVI),LAI_NDVI,np.nan)

LAI_NDVI[~veg_mask] = np.nan

def plot_lai(data, title):

    valid = data[~np.isnan(data)]

    if valid.size > 0:

        vmin = np.percentile(valid,2)

        vmax = np.percentile(valid,98)

    else:

        vmin = 0
        vmax = 1

    plt.figure(figsize=(6, 6))

    plt.imshow(data, cmap="YlGn", vmin=vmin, vmax=vmax)

    plt.title(title)

    plt.colorbar()

    plt.axis("off")

    plt.show()

plot_lai(LAI_NDVI,"LAI (NDVI)")

print("LAI promedio (NDVI) =",np.nanmean(LAI_NDVI))

print("LAI std (NDVI) =",np.nanstd(LAI_NDVI))

# 16. FIRMA ESPECTRAL===================================

print("\nGenerando firma espectral...")

available_bands = sorted([(BAND_WAVELENGTHS[b],b)for b in bands.keys()if b in BAND_WAVELENGTHS])

wavelengths = []
medios = []

for wl, b in available_bands:

    wavelengths.append(wl)
    medios.append(np.nanmean(bands[b]))

wavelengths = np.array(wavelengths)

medios = np.array(medios)

xx = np.linspace(wavelengths.min(), wavelengths.max(), 400)

yy = np.interp(xx,wavelengths,medios)

plt.figure(figsize=(9, 5))

plt.plot(xx,yy, linewidth=2)

plt.scatter(wavelengths,medios, s=80)

for x, y in zip(wavelengths, medios):

    plt.annotate(f"{y:.3f}",(x, y), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)

plt.xlabel("Longitud de onda (nm)")
plt.ylabel("Reflectancia (0–1)")
plt.title("Firma espectral Sentinel-2 (medias por banda)")
plt.grid(True)

# Guardar firma espectral para el informe PDF============================
ruta_firma = OUTDIR / "Firma_Espectral.png"
plt.savefig(ruta_firma, dpi=300, bbox_inches="tight")
print("Firma espectral guardada:", ruta_firma)

plt.show()
plt.close()

# 17. NORMALIZACIÓN DE ÍNDICES===============================

print("\nNormalizando índices...")

# NDVI, NDMI, NDRE y EVI ya están en [-1, 1]==================

NDVI_n = np.clip(NDVI,-1, 1)

NDMI_n = np.clip(NDMI,-1, 1)

NDRE_n = np.clip(NDRE,-1, 1)

EVI_n = np.clip(EVI,-1, 1)

# RCI: rango de referencia [0, 15]============================

RCI_n = (2 *((RCI - 0)/(15 - 0))- 1)

RCI_n = np.clip(RCI_n,-1, 1)

CIre_n = RCI_n.copy()

# TCARI/OSAVI: rango de referencia [0, 1]=====================

TCARI_OSAVI_n = (2 *((TCARI_OSAVI - 0)/(1 - 0))- 1)

TCARI_OSAVI_n = np.clip(TCARI_OSAVI_n,-1, 1)

# LAI-NDVI: rango de referencia [0, 5]=======================

LAI_NDVI_n = (2 *((LAI_NDVI - 0)/(5 - 0))- 1)

LAI_NDVI_n = np.clip(LAI_NDVI_n,-1, 1)

# Aplicar máscara de vegetación===============================

NDVI_n[~veg_mask] = np.nan
NDMI_n[~veg_mask] = np.nan
NDRE_n[~veg_mask] = np.nan
EVI_n[~veg_mask] = np.nan
RCI_n[~veg_mask] = np.nan
CIre_n[~veg_mask] = np.nan
TCARI_OSAVI_n[~veg_mask] = np.nan
LAI_NDVI_n[~veg_mask] = np.nan

print("Normalización completada.")

# 18. ESTIMACIÓN DE CLOROFILA=================================

print("\nEstimando clorofila...")

Clorofila = (0.40 * NDRE + 0.30 * RCI_n + 0.20 * TCARI_OSAVI_n + 0.10 * EVI)

Clorofila = np.where(np.isfinite(Clorofila), Clorofila, np.nan)

Clorofila[~veg_mask] = np.nan

vmin = np.nanpercentile(Clorofila, 2)

vmax = np.nanpercentile(Clorofila, 98)

plt.figure(figsize=(6, 6))

plt.imshow(Clorofila,cmap="YlGn",vmin=vmin,vmax=vmax)

plt.title("Clorofila estimada")

plt.colorbar()

plt.axis("off")

plt.show()

print("Clorofila promedio =", np.nanmean(Clorofila))

print("Clorofila std =", np.nanstd(Clorofila))

# 19. ESTIMACIÓN DE NITRÓGENO====================================

print("\nEstimando nitrógeno...")

Nitrogeno = (0.35 * NDRE + 0.30 * RCI_n + 0.20 * TCARI_OSAVI_n + 0.15 * LAI_NDVI_n)

Nitrogeno[~veg_mask] = np.nan

vmin = np.nanpercentile(Nitrogeno, 2)

vmax = np.nanpercentile(Nitrogeno, 98)

plt.figure(figsize=(6, 6))

plt.imshow(Nitrogeno, cmap="viridis", vmin=vmin, vmax=vmax)

plt.title("Nitrógeno estimado (relativo)")

plt.colorbar()

plt.axis("off")

plt.show()

print("Nitrógeno promedio =", np.nanmean(Nitrogeno))

print("Nitrógeno std =", np.nanstd(Nitrogeno))

# 20. ESTRÉS HÍDRICO======================================

print("\nCalculando estrés hídrico...")

estres_hidrico = np.asarray(NDMI, dtype=np.float32)

estres_hidrico = np.where(np.isfinite(estres_hidrico), estres_hidrico, np.nan)

estres_hidrico[~veg_mask] = np.nan

vmin = np.nanpercentile(estres_hidrico, 2)

vmax = np.nanpercentile(estres_hidrico, 98)

plt.figure(figsize=(6, 6))

plt.imshow(estres_hidrico, cmap="RdYlGn_r", vmin=vmin, vmax=vmax)

plt.title("Estrés hídrico")

plt.colorbar(label="NDMI")

plt.axis("off")

plt.show()

print("Estrés hídrico promedio =", np.nanmean(estres_hidrico))

print("Estrés hídrico std =", np.nanstd(estres_hidrico))

# 21. DENSIDAD DEL DOSEL===========================================

print("\nCalculando densidad del dosel...")

Densidad = (0.50 * LAI_NDVI_n + 0.30 * NDVI + 0.20 * EVI)

Densidad = np.where(np.isfinite(Densidad), Densidad, np.nan)

Densidad[~veg_mask] = np.nan

vmin = np.nanpercentile(Densidad, 2)

vmax = np.nanpercentile(Densidad, 98)

plt.figure(figsize=(6,6))

plt.imshow(Densidad,cmap="YlGn", vmin=vmin, vmax=vmax)

plt.title("Densidad del dosel")

plt.colorbar()

plt.axis("off")

plt.show()

print("Densidad promedio =", np.nanmean(Densidad))

print("Densidad std =", np.nanstd(Densidad))

# 22. VIGOR VEGETATIVO==========================================

print("\n--- DATOS USADOS PARA VIGOR ---")
print("NDVI promedio =", np.nanmean(NDVI))
print("EVI promedio =", np.nanmean(EVI))
print("NDRE promedio =", np.nanmean(NDRE))
print("\nCalculando vigor vegetativo...")

Vigor = (0.40 * NDVI + 0.35 * EVI + 0.25 * NDRE)

Vigor = np.where(np.isfinite(Vigor),Vigor,np.nan)

Vigor[~veg_mask] = np.nan

vmin = np.nanpercentile(Vigor,2)

vmax = np.nanpercentile(Vigor,98)

plt.figure(figsize=(6, 6))

plt.imshow(Vigor, cmap="RdYlGn", vmin=vmin, vmax=vmax)

plt.title("Vigor vegetativo")

plt.colorbar()

plt.axis("off")

plt.show()

print("Vigor promedio =",np.nanmean(Vigor))

print("Vigor std =",np.nanstd(Vigor))

# Clasificación=============================

Vigor_class = np.full_like(Vigor,np.nan)

Vigor_class[Vigor < 0.3] = 0

Vigor_class[(Vigor >= 0.3) & (Vigor < 0.6)] = 1

Vigor_class[Vigor >= 0.6] = 2

# 23. VALIDACIÓN DEL MODELO====================================

print("\n")
print("=" * 60)
print("VALIDACIÓN DEL MODELO")
print("=" * 60)

def safe_mask(*arrays):

    m = np.ones_like(arrays[0], dtype=bool)

    for a in arrays:

        m &= ~np.isnan(a)

    return m

def safe_corr(a, b):

    m = safe_mask(a, b)

    if np.sum(m) < 100:

        return np.nan

    return np.corrcoef(a[m], b[m])[0, 1]

def summary_stats(arr):

    v = arr[~np.isnan(arr)]

    if v.size == 0:

        return None

    return {"mean": np.mean(v),
            "std": np.std(v),
            "min": np.min(v),
            "max": np.max(v),
            "p2": np.percentile(v, 2),
            "p98": np.percentile(v, 98) }

# 23.1 COHERENCIA FISIOLÓGICA================================

print("\n=== 1. COHERENCIA FISIOLÓGICA ===")

corr_matrix = {

    "Clorofila–N":
        safe_corr(Clorofila, Nitrogeno),

    "Clorofila–NDRE":
        safe_corr(Clorofila, NDRE),

    "N–NDRE":
        safe_corr(Nitrogeno, NDRE),

    "NDMI–Vigor":
        safe_corr(NDMI, Vigor),

    "LAI–Vigor":
    safe_corr(LAI_NDVI, Vigor) }

for k, v in corr_matrix.items():

    print(f"{k}: {v:.3f}")

# 23.2 VALIDACIÓN ESTADÍSTICA=====================================

print("\n=== 2. VALIDACIÓN ESTADÍSTICA ===")

variables = {

    "NDVI": NDVI,

    "EVI": EVI,

    "NDMI": NDMI,

    "LAI": LAI_NDVI,

    "Clorofila": Clorofila,

    "Nitrógeno": Nitrogeno,

    "Vigor": Vigor }

for name, arr in variables.items():

    stats = summary_stats(arr)

    if stats:

        print(f"\n{name}:")

        for k, v in stats.items():

            print(f"  {k}: {v:.3f}")

# 23.3 ESTABILIDAD ESPACIAL======================================

print("\n=== 3. ESTABILIDAD ESPACIAL ===")

h, w = NDVI.shape

zones = [(slice(0, h // 2), slice(0, w // 2)), (slice(0, h // 2),slice(w // 2, w)),
    (slice(h // 2, h), slice(0, w // 2)), (slice(h // 2, h), slice(w // 2, w))]

def zone_variability(arr):

    means = []

    for r, c in zones:

        sub = arr[r, c]

        if np.all(np.isnan(sub)):

            means.append(np.nan)

        else:

            means.append(np.nanmean(sub))

    return np.nanstd(means)

for name, arr in variables.items():

    zv = zone_variability(arr)

    print(f"{name} variabilidad espacial: "
          f"{zv:.4f}")
    
# 23.4 ROBUSTEZ A UMBRALES=========================================

print("\n=== 4. ROBUSTEZ A UMBRALES ===")

def stress_map(ndmi, t1, t2):

    out = np.full_like(ndmi, np.nan)
    
    ndmi_v = np.where(veg_mask, ndmi, np.nan)

    out[ndmi_v > t1] = 0

    out[(ndmi_v <= t1) & (ndmi_v > t2)] = 1

    out[ndmi_v <= t2] = 2

    return out

base = stress_map(NDMI,0.3, 0.1)

alt = stress_map(NDMI, 0.35, 0.15)

def class_distribution(x):

    m = ~np.isnan(x)

    total = np.sum(m)

    if total == 0:

        return (np.nan, np.nan, np.nan)

    return (np.sum(x == 0) / total, np.sum(x == 1) / total, np.sum(x == 2) / total)

p_base = class_distribution(base)

p_alt = class_distribution(alt)


print("Base:", p_base)

print("Alternativo:", p_alt)

print("\n--- INTERPRETACIÓN ---")

print(f"Sin estrés: "
     f"{p_base[0] * 100:.1f}% "
     f"→ "
     f"{p_alt[0] * 100:.1f}%")

print(f"Moderado:   "
    f"{p_base[1] * 100:.1f}% "
    f"→ "
    f"{p_alt[1] * 100:.1f}%")

print(f"Alto:       "
    f"{p_base[2] * 100:.1f}% "
    f"→ "
    f"{p_alt[2] * 100:.1f}%")

# 23.5 CONSISTENCIA MULTIVARIABLE======================================

print("\n=== 5. CONSISTENCIA MULTIVARIABLE ===")

variables_mv = {"NDRE (clorofila/nitrógeno)":NDRE,

    "Clorofila":
        Clorofila,

    "Nitrógeno":
        Nitrogeno,

    "Vigor":
        Vigor,

    "NDMI (estrés hídrico)":
        NDMI }

data = []

names = []

for name, arr in variables_mv.items():

    data.append(arr.flatten())

    names.append(name)

X = np.vstack(data).T

# Eliminar NaN======================================

X = X[~np.isnan(X).any(axis=1)]

if X.shape[0] > 100:

    cov_matrix = np.cov(X, rowvar=False)

    eigvals, eigvecs = np.linalg.eig(cov_matrix)

    idx = np.argsort(eigvals)[::-1]

    eigvals = eigvals[idx]

    eigvecs = eigvecs[:, idx]

    print("\nAutovalores "
          "(varianza explicada):")

    for i, val in enumerate(eigvals):

        print(f"Componente {i + 1}: "
            f"{val:.6f}")
        
    var_exp = (eigvals / np.sum(eigvals))

    print("\nVarianza explicada (%):")

    for i, v in enumerate(var_exp):

        print(f"Componente {i + 1}: "
            f"{v * 100:.2f}%")

    print("\nContribución de variables "
          "a la Componente 1:")

    for i, name in enumerate(names):

        contrib = eigvecs[i, 0]

        print(f"{name}: "
            f"{contrib:.4f}")

else:

    print("No hay suficientes datos "
        "para realizar el análisis "
        "multivariable")

# 24. GUARDAR MAPAS DE LOS ÍNDICES ==============================

print("\nGuardando mapas de los índices...")

def guardar_mapa_indice(arr, nombre_archivo, cmap):
    
    # Obtener únicamente los valores válidos
    valores = arr[np.isfinite(arr)]
    
    if valores.size == 0:
        print(f"No hay valores válidos para {nombre_archivo}")
        
        return
    
    # Mismos límites de visualización utilizados en Colab
    vmin = np.percentile(valores, 2)
    vmax = np.percentile(valores, 98)
    
    # Crear figura
    fig, ax = plt.subplots(figsize=(6, 6))
    
    # Mostrar mapa
    im = ax.imshow(arr, cmap=cmap, vmin=vmin, vmax=vmax)
    
    # Barra de color
    fig.colorbar(im, ax=ax, label="Valor")
    
    # Ocultar ejes
    ax.axis("off")
    
    # Guardar mapa
    plt.savefig(OUTDIR / nombre_archivo, dpi=300, bbox_inches="tight", pad_inches=0)
    
    plt.close(fig)
    
    print("Mapa guardado:", OUTDIR / nombre_archivo)

# NDVI==========================================================

guardar_mapa_indice(NDVI, "NDVI_n.png", cmap="RdYlGn")

# NDRE===========================================================

guardar_mapa_indice(NDRE, "NDRE_n.png", cmap="RdYlGn")

# EVI============================================================

guardar_mapa_indice(EVI, "EVI_n.png", cmap="RdYlGn")

# NDMI===========================================================

guardar_mapa_indice(NDMI, "NDMI_n.png", cmap="Blues")

# CIred-edge======================================================

guardar_mapa_indice(RCI, "CIre_n.png", cmap="YlGn")

# TCARI/OSAVI=====================================================

guardar_mapa_indice(TCARI_OSAVI, "TCARI_OSAVI_n.png", cmap="RdYlGn_r")

# LAI NDVI=========================================================

guardar_mapa_indice(LAI_NDVI,"LAI_NDVI_n.png",cmap="YlGn")

print("Mapas de los índices guardados correctamente.")

# 25. GUARDAR ESTADÍSTICAS EN CSV===============================

print("\nGuardando estadísticas de los índices...")

csv_path = (OUTDIR / "indices_stats.csv")
# Variables que se mostrarán en la interfaz

variables_estadisticas = {

    "NDVI": NDVI,

    "NDRE": NDRE,

    "EVI": EVI,

    "NDMI": NDMI,

    "CIred-edge": RCI,

    "TCARI/OSAVI": TCARI_OSAVI,

    "LAI NDVI": LAI_NDVI }

with open(csv_path, "w", newline="", encoding="utf-8") as f:

    writer = csv.writer(f)

    writer.writerow([
            "indice",
            "minimo",
            "maximo",
            "promedio",
            "desviacion_estandar",
            "percentil_2",
            "percentil_98" ])

    for nombre, arr in variables_estadisticas.items():

        valores = arr[np.isfinite(arr)]

        if valores.size > 0:

            writer.writerow([nombre,
                    np.nanmin(arr),
                    np.nanmax(arr),
                    np.nanmean(arr),
                    np.nanstd(arr),
                    np.percentile(valores, 2),
                    np.percentile(valores, 98) ])

        else:

            writer.writerow([nombre,
                    np.nan,
                    np.nan,
                    np.nan,
                    np.nan,
                    np.nan,
                    np.nan ])

print("\nCSV de estadísticas guardado en:")

print(csv_path)

# 26. GUARDAR RESULTADOS DEL DIAGNÓSTICO================================

print("\nGuardando resultados del diagnóstico...")

diagnostico_path = (OUTDIR / "diagnostico_stats.csv")

with open(diagnostico_path, "w", newline="", encoding="utf-8") as f:

    writer = csv.writer(f)

    writer.writerow(["diagnostico","promedio","desviacion_estandar","minimo","maximo"])

    variables_diagnostico = {

        "Vigor vegetativo": Vigor,

        "Clorofila": Clorofila,

        "Nitrógeno": Nitrogeno,

        "Densidad del dosel": Densidad }

    for nombre, arr in variables_diagnostico.items():

        valores = arr[np.isfinite(arr)]

        if valores.size > 0:

            writer.writerow([nombre,
                    np.mean(valores),
                    np.std(valores),
                    np.min(valores),
                    np.max(valores) ])

        else:

            writer.writerow([nombre,
                    np.nan,
                    np.nan,
                    np.nan,
                    np.nan ])

    # ESTRÉS HÍDRICO===============================================
 
    valores_estres = estres_hidrico[
        np.isfinite(estres_hidrico) ]

    if valores_estres.size > 0:

        writer.writerow(["Estrés hídrico",
                np.mean(valores_estres),
                np.std(valores_estres),
                np.min(valores_estres),
                np.max(valores_estres) ])

    else:

        writer.writerow(["Estrés hídrico",
                np.nan,
                np.nan,
                np.nan,
                np.nan ])

print("\nCSV de diagnóstico guardado en:")

print(diagnostico_path)

# 27. GUARDAR MAPAS DEL DIAGNÓSTICO======================================

print("\nGuardando mapas del diagnóstico...")

def guardar_mapa_diagnostico(arr, nombre_archivo, cmap="viridis"):

    # Obtener únicamente los valores válidos
    valores = arr[np.isfinite(arr)]

    if valores.size == 0:
        print(f"No hay valores válidos para {nombre_archivo}")
        return

    # Mismos límites utilizados en Colab
    vmin = np.percentile(valores, 2)
    vmax = np.percentile(valores, 98)

    # Evitar problemas si ambos límites son iguales
    if vmin == vmax:
        vmin = np.min(valores)
        vmax = np.max(valores)

    # Crear figura con el mismo tamaño de Colab
    fig, ax = plt.subplots(figsize=(7, 6))

    # Mostrar mapa
    im = ax.imshow(arr, cmap=cmap, vmin=vmin, vmax=vmax)

    # Título
    #ax.set_title(nombre_archivo.replace(".png", ""))

    # Barra de color
    fig.colorbar(im, ax=ax, label="Valor")

    # Ocultar ejes
    ax.axis("off")

    # Guardar
    plt.savefig(OUTDIR / nombre_archivo, dpi=300,bbox_inches="tight", pad_inches=0)

    plt.close(fig)

# Vigor vegetativo===========================================
guardar_mapa_diagnostico(Vigor, "Vigor.png", cmap="RdYlGn")

# Clorofila=============================================
guardar_mapa_diagnostico(Clorofila, "Clorofila.png", cmap="YlGn")

# Nitrógeno=============================================
guardar_mapa_diagnostico(Nitrogeno, "Nitrogeno.png", cmap="viridis")

# Estrés hídrico========================================
guardar_mapa_diagnostico(estres_hidrico, "Estres_Hidrico.png", cmap="Blues")

# Densidad del dosel====================================
guardar_mapa_diagnostico(Densidad, "Densidad_Dosel.png", cmap="Greens")

print("Mapas del diagnóstico guardados correctamente.")

print("\n=== ARCHIVOS GENERADOS ===")
 
for archivo in OUTDIR.iterdir():
    print(archivo.name)
#==========================================  
print("\n=== COMPARACIÓN DE RANGOS ===")

variables = {
    "NDVI": NDVI,
    "NDRE": NDRE,
    "EVI": EVI,
    "NDMI": NDMI,
    "LAI NDVI": LAI_NDVI }

for nombre, arr in variables.items():

    valores = arr[np.isfinite(arr)]

    print(f"\n{nombre}")
    print(f"  Mínimo = {np.min(valores):.6f}")
    print(f"  Máximo = {np.max(valores):.6f}")  