# Ajustes de algoritmos y parámetros

Este documento describe los ajustes realizados al procesamiento del aplicativo durante la validación de los resultados. Cada ajuste corresponde a una sección del documento del proyecto de grado (sección 2.2.4).

| N.º | Ajuste | Sección del documento |
|---|---|---|
| 1 | Estabilización numérica en el cálculo de índices | 2.2.4.1 |
| 2 | Corrección de la dirección de normalización de TCARI/OSAVI | 2.2.4.2 |
| 3 | Normalización por percentiles de CIred-edge y LAI | 2.2.4.3 |

---

## 1. Estabilización numérica en el cálculo de índices

**Problema:** en los índices calculados como razones entre bandas, el denominador puede ser cero o muy cercano a cero en píxeles de baja reflectancia (sombras, bordes de la escena). Esto genera valores indefinidos (`NaN`) o infinitos (`Inf`) que afectan las estadísticas y los parámetros derivados.

**Solución:** se agregó una constante de estabilización `ε = 1 × 10⁻⁶` en el denominador. Como la reflectancia está entre 0 y 1, este valor no altera los píxeles válidos. Los valores no finitos que persisten se reemplazan por `NaN` y se aplica la máscara de vegetación, para que las estadísticas se calculen solo con píxeles válidos.

```python
EPS = 1e-6

NDVI = (B8 - B4) / (B8 + B4 + EPS)
NDRE = (B8 - B5) / (B8 + B5 + EPS)
EVI  = 2.5 * (B8 - B4) / (B8 + 6 * B4 - 7.5 * B2 + 1 + EPS)
NDMI = (B8 - B11) / (B8 + B11 + EPS)
RCI  = B8 / (B5 + EPS) - 1          # CIred-edge
TCARI_OSAVI = TCARI / (OSAVI + EPS)

# LAI: no usa EPS; se limita el NDVI para evitar la indeterminación del logaritmo
NDVI_lai = np.clip(NDVI, 0, 0.95)
```

---

## 2. Corrección de la dirección de normalización de TCARI/OSAVI

**Problema:** la normalización asumía que un valor alto del índice indicaba un mejor estado fisiológico. En TCARI/OSAVI ocurre lo contrario: un valor bajo indica mayor contenido de clorofila (Haboudane et al., 2002). Por eso el índice normalizado tenía el signo invertido y reducía los parámetros de clorofila y nitrógeno.

**Solución:** se invirtió la dirección de la normalización y el resultado se limitó al intervalo `[-1, 1]`, ya que algunos píxeles presentaban valores fuera del rango esperado (entre −3,78 y 2,63).

```python
# Antes
TCARI_OSAVI_n = 2 * ((TCARI_OSAVI - 0) / (1 - 0)) - 1

# Después
TCARI_OSAVI_n = 2 * ((1 - TCARI_OSAVI) / (1 - 0)) - 1
```

**Efecto:** el valor medio normalizado pasó de −0,6230 a 0,6228.

---

## 3. Normalización por percentiles de CIred-edge y LAI

**Problema:** CIred-edge y LAI se normalizaban con rangos generales de la literatura (0–15 y 0–5). Estos rangos abarcan cualquier tipo de vegetación, por lo que los valores del cultivo de papa quedaban desplazados hacia el extremo negativo de la escala.

**Solución:** se normalizan con el rango observado en la imagen, entre los percentiles 2 y 98 de los píxeles con vegetación, y el resultado se limita a `[-1, 1]`. Esto reduce la influencia de los valores extremos.

```python
def normalizar_percentil(indice, veg_mask, p_bajo=2, p_alto=98):
    valores_validos = indice[veg_mask & np.isfinite(indice)]
    minimo = np.percentile(valores_validos, p_bajo)
    maximo = np.percentile(valores_validos, p_alto)
    normalizado = 2 * ((indice - minimo) / (maximo - minimo)) - 1
    return np.clip(normalizado, -1, 1)

RCI_n = normalizar_percentil(RCI, veg_mask)
LAI_NDVI_n = normalizar_percentil(LAI_NDVI, veg_mask)
```

**Efecto:** la media de CIred-edge normalizado pasó de −0,7002 a −0,0911, y la de LAI normalizado, de −0,4953 a 0,0942.

**Limitación:** como la normalización depende de los percentiles de cada imagen, los valores normalizados no son directamente comparables entre imágenes de fechas distintas.

---

## Efecto conjunto de los ajustes

Valores medios de los parámetros derivados sobre la zona de estudio:

| Parámetro | Antes | Después |
|---|---|---|
| Clorofila | −0,0706 | 0,3612 |
| Nitrógeno | −0,2303 | 0,2899 |
| Densidad del dosel | 0,1048 | 0,3995 |
| Vigor vegetativo | 0,6474 | 0,6474 |
| Estrés hídrico | 0,2684 | 0,2684 |

Vigor vegetativo y estrés hídrico no cambian porque no incluyen índices normalizados.

---

## Referencias

Haboudane, D., Miller, J. R., Tremblay, N., Zarco-Tejada, P. J. y Dextraze, L. (2002). Integrated narrow-band vegetation indices for prediction of crop chlorophyll content for application to precision agriculture. *Remote Sensing of Environment, 81*(2–3), 416–426. https://doi.org/10.1016/S0034-4257(02)00018-4
