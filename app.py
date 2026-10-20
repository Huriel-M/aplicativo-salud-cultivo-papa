# -*- coding: utf-8 -*-
"""
Created on Fri Aug 28 04:19:17 2026

@author: LUIS
"""

# ============================================================
# INTERFAZ DEL PROYECTO DE GRADO
# Análisis de imágenes Sentinel-2 para cultivos de papa
# ============================================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import runpy
import os
import glob

import numpy as np
import rasterio

from PIL import Image, ImageTk
from skimage.transform import resize

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image as RLImage,
    Table,
    TableStyle,
    PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

# CONFIGURACIÓN============================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

CARPETA_PROCESAMIENTO = ( BASE_DIR / "Codigo" / "spyder" / "procesamiento.py")

CARPETA_RESULTADOS = (BASE_DIR / "resultados")

# VENTANA PRINCIPAL========================================

root = tk.Tk()

root.title("Aplicativo para análisis de salud de cultivos de papa")

root.geometry("1100x700")
root.minsize(950, 600)

# ESTILOS================================================

style = ttk.Style()

try:
    style.theme_use("clam")
    
except Exception:
    pass

style.configure("TNotebook.Tab",font=("Arial", 11, "bold"), padding=[15, 8])

style.configure("Titulo.TLabel", font=("Arial", 22, "bold"))

style.configure("Subtitulo.TLabel", font=("Arial", 13))

style.configure("Texto.TLabel", font=("Arial", 11))
 
style.configure("Boton.TButton", font=("Arial", 11, "bold"), padding=8)

# VARIABLES===============================================

carpeta_seleccionada = tk.StringVar(value="")

estado = tk.StringVar(value="Esperando selección de imágenes...")

# VARIABLES PARA EL ÁREA DE INTERÉS (AOI)=================

imagen_rgb_aoi = None
imagen_rgb_tk = None

aoi_inicio_x = None
aoi_inicio_y = None

aoi_rectangulo = None

AOI_BOUNDS = None

factor_x = 1
factor_y = 1

# PESTAÑAS===============================================

notebook = ttk.Notebook(root)

notebook.pack(fill="both", expand=True, padx=10, pady=10)

tab_inicio = ttk.Frame(notebook)
tab_aoi = ttk.Frame(notebook)
tab_procesamiento = ttk.Frame(notebook)
tab_resultados = ttk.Frame(notebook)
tab_ayuda = ttk.Frame(notebook)

notebook.add(tab_inicio, text="Inicio")

notebook.add(tab_aoi, text="Área de interés")

notebook.add(tab_procesamiento, text="Procesamiento")

notebook.add(tab_resultados, text="Resultados")

notebook.add(tab_ayuda, text="Ayuda")

# FUNCIÓN: BUSCAR BANDA==================================

def buscar_banda(carpeta, codigo):

    patrones = [
        os.path.join(carpeta, f"*{codigo}*.jp2"),
        os.path.join(carpeta, f"*{codigo}*.JP2"),
        os.path.join(carpeta, f"*{codigo}*.tif"),
        os.path.join(carpeta, f"*{codigo}*.TIF"),
        os.path.join(carpeta, f"*{codigo}*.tiff"),
        os.path.join(carpeta, f"*{codigo}*.TIFF") ]

    archivos = []

    for patron in patrones:
        archivos.extend(glob.glob(patron))

    if archivos:
        return archivos[0]

    return None

# GENERAR INFORME=========================================

def generar_informe_pdf():
    """Genera el informe PDF del análisis del cultivo."""

    archivo_pdf = filedialog.asksaveasfilename(
        title="Guardar informe PDF",
        defaultextension=".pdf",
        filetypes=[("Archivo PDF", "*.pdf")]  )

    if not archivo_pdf:
        return

    try:
        documento = SimpleDocTemplate(
            archivo_pdf,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50 )

        estilos = getSampleStyleSheet()

        titulo = ParagraphStyle(
            "TituloInforme",
            parent=estilos["Title"],
            alignment=TA_CENTER,
            fontSize=18,
            leading=24,
            spaceAfter=25 )

        subtitulo = ParagraphStyle(
            "SubtituloInforme",
            parent=estilos["Heading2"],
            alignment=TA_CENTER,
            fontSize=13,
            leading=18,
            spaceAfter=20  )

        encabezado = ParagraphStyle(
            "EncabezadoInforme",
            parent=estilos["Heading2"],
            fontSize=14,
            leading=18,
            spaceBefore=15,
            spaceAfter=12   )

        subencabezado = ParagraphStyle(
            "SubencabezadoInforme",
            parent=estilos["Heading3"],
            fontSize=11,
            leading=15,
            spaceBefore=10,
            spaceAfter=8  )

        texto = ParagraphStyle(
            "TextoInforme",
            parent=estilos["BodyText"],
            fontSize=10,
            leading=15,
            spaceAfter=10   )

        contenido = []

        # PORTADA========================================

        contenido.append(
            Paragraph("INFORME DE ANÁLISIS DEL ESTADO DE SALUD DEL CULTIVO DE PAPA", titulo) )

        #contenido.append(Spacer(1, 30))

        #contenido.append(
            #Paragraph(
             #   "Desarrollo de aplicativo para análisis de imágenes "
              #  "hiperespectrales satelitales aplicado a la evaluación "
               # "del estado de salud de cultivos de papa",
                #subtitulo ) )

        contenido.append(Spacer(1, 30))

        datos_portada = [
            ["Aplicativo", "Análisis espectral de cultivos de papa"],
            ["Fuente de información", "Imágenes satelitales Sentinel-2"],
            #["Área de estudio", "Córdoba, Nariño, Colombia"],
            ["Tipo de análisis", "Evaluación del estado de salud del cultivo"]
        ]

        tabla = Table(datos_portada, colWidths=[150, 300] )

        tabla.setStyle(
            TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8)  ])
        )

        contenido.append(tabla)

        contenido.append(Spacer(1, 35))

        contenido.append(
            Paragraph(
                "El presente informe reúne los resultados obtenidos "
                "mediante el procesamiento y análisis de información "
                "espectral del área seleccionada.",  texto ) 
            )

        # RESULTADOS ESTADÍSTICOS DE LOS ÍNDICES=======================

        contenido.append(
            Paragraph(
                "Resultados estadísticos de los índices espectrales",
                encabezado )
        )

        contenido.append(
            Paragraph(
                "La siguiente tabla presenta los valores estadísticos "
                "obtenidos para los índices espectrales calculados "
                "durante el procesamiento de la imagen.", texto  )
        )
        # EXPLICACIÓN DE LOS RESULTADOS ESTADÍSTICOS=================
        
        contenido.append(
           Paragraph(
               "Los índices espectrales se analizan con cuatro estadísticas: "
               "el mínimo y máximo marcan los extremos; "
               "el promedio muestra el comportamiento general; "
               "y la desviación estándar mide la variabilidad espacial "
               "Su interpretación depende de cada índice, pues un valor alto "
               "no siempre significa un mejor cultivo. " , texto)
           )

        archivo_stats = CARPETA_RESULTADOS / "indices_stats.csv"

        if archivo_stats.exists():

            tabla_stats = [
                [
                    "Índice",
                    "Mínimo",
                    "Máximo",
                    "Promedio",
                    "Desv. estándar"  ]
            ]

            with open(archivo_stats, "r", encoding="utf-8-sig") as archivo:

                import csv

                reader = csv.DictReader(archivo)

                for fila in reader:

                    try:

                        tabla_stats.append([
                            fila["indice"],
                            f"{float(fila['minimo']):.4f}",
                            f"{float(fila['maximo']):.4f}",
                            f"{float(fila['promedio']):.4f}",
                            f"{float(fila['desviacion_estandar']):.4f}"
                            ])

                    except (ValueError, KeyError):
                        continue

            if len(tabla_stats) > 1:

                tabla_indices = Table(
                    tabla_stats,
                    colWidths=[110, 85, 85, 95, 95],
                    repeatRows=1
                )

                tabla_indices.setStyle(
                    TableStyle([
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6) ])
                )

                contenido.append(tabla_indices)

            else:

                contenido.append(
                    Paragraph(
                        "No se encontraron estadísticas válidas "
                        "para los índices espectrales.", texto )
                )

        else:

            contenido.append(
                Paragraph(
                    "No se encontró el archivo de estadísticas "
                    "de los índices espectrales.", texto )
            )

        # MAPAS DE LOS ÍNDICES ESPECTRALES=========================
        contenido.append(
            Paragraph(
                "Mapas de los índices espectrales",  encabezado )
        )

        contenido.append(
            Paragraph(
                "A continuación se presentan los mapas correspondientes "
                "a los índices espectrales obtenidos durante el análisis "
                "de la zona de estudio.", texto )
        )

        mapas_indices = [
            ("NDVI", "NDVI_n.png"),
            ("NDRE", "NDRE_n.png"),
            ("EVI", "EVI_n.png"),
            ("NDMI", "NDMI_n.png"),
            ("CIred-edge", "CIre_n.png"),
            ("TCARI/OSAVI", "TCARI_OSAVI_n.png"),
            ("LAI NDVI", "LAI_NDVI_n.png"),
        ]
        # FIRMA ESPECTRAL ==========================================

        ruta_firma = CARPETA_RESULTADOS / "Firma_Espectral.png"

        if ruta_firma.exists():

            contenido.append(Paragraph("Firma espectral", estilos["Heading1"] ) )

            contenido.append(Spacer(1, 12) )

            contenido.append(
                Paragraph(
                    "La firma espectral representa el comportamiento "
                    "promedio de la reflectancia de las bandas Sentinel-2 "
                    "utilizadas en el análisis.",
                    estilos["Normal"]  )
            )

            contenido.append(Spacer(1, 12) )

            imagen_firma = RLImage(str(ruta_firma), width=450, height=250)

            imagen_firma.hAlign = "CENTER"

            contenido.append(imagen_firma)

            contenido.append(Spacer(1, 12) )
            
            
        # CARGAR ESTADÍSTICAS PARA LAS INTERPRETACIONES DEL PDF

        estadisticas_indices = {}
        archivo_stats = CARPETA_RESULTADOS / "indices_stats.csv"

        if archivo_stats.exists():
            import csv

            with open(archivo_stats, "r", encoding="utf-8-sig") as archivo:
                reader = csv.DictReader(archivo)

                for fila in reader:
                    try:
                        estadisticas_indices[fila["indice"]] = {
                            "minimo": float(fila["minimo"]),
                            "maximo": float(fila["maximo"]),
                            "promedio": float(fila["promedio"]),
                            "desviacion_estandar": float(
                                fila["desviacion_estandar"]
                            )
                        }
                    except (ValueError, KeyError):
                        continue

        # MAPAS DE ÍNDICES ==========================================

        for nombre_indice, nombre_archivo in mapas_indices:

            ruta_mapa = CARPETA_RESULTADOS / nombre_archivo

            if ruta_mapa.exists():

                contenido.append(Paragraph(nombre_indice, subencabezado) )

                try:

                    imagen = RLImage(str(ruta_mapa), width=340, height=280) #

                    imagen.hAlign = "CENTER"

                    contenido.append(imagen)

                    contenido.append(Spacer(1, 8) )

                    definiciones_indices = {
                        "NDVI": (
                            "<b>Definición:</b> Índice de vegetación utilizado "
                            "para representar el vigor y la actividad de la "
                            "vegetación. Valores mayores indican una mayor "
                            "respuesta asociada a vegetación activa."
                        ),

                        "NDRE": (
                            "<b>Definición:</b> Índice sensible al estado "
                            "fisiológico de la vegetación y a variaciones "
                            "relacionadas con el contenido de clorofila, "
                            "utilizando información del borde rojo."
                        ),

                        "EVI": (
                            "<b>Definición:</b> Índice de vegetación utilizado "
                            "para representar el vigor de la cobertura vegetal "
                            "y reducir la influencia del suelo y de otras "
                            "fuentes de variación."
                        ),

                        "NDMI": (
                            "<b>Definición:</b> Índice relacionado con el "
                            "contenido de humedad de la vegetación y utilizado "
                            "para evaluar las condiciones hídricas del cultivo."
                        ),

                        "CIred-edge": (
                            "<b>Definición:</b> Índice relacionado con el "
                            "contenido relativo de clorofila de la vegetación "
                            "mediante información espectral del borde rojo."
                        ),

                        "TCARI/OSAVI": (
                            "<b>Definición:</b> Indicador relacionado con la "
                            "respuesta espectral asociada a la clorofila, "
                            "considerando también la influencia del fondo del "
                            "suelo."
                        ),

                        "LAI NDVI": (
                            "<b>Definición:</b> Estimación del índice de área "
                            "foliar a partir del NDVI, relacionada con la "
                            "cantidad de superficie foliar presente en la "
                            "cobertura vegetal."
                        )
                    }


                    definicion = definiciones_indices.get(
                        nombre_indice,
                        "Definición no disponible."
                    )

                    contenido.append(
                        Paragraph(definicion, estilos["Normal"])
                    )

                    # ESTADÍSTICAS E INTERPRETACIÓN DEL ÍNDICE

                    datos_indice = estadisticas_indices.get(nombre_indice)

                    if datos_indice is not None:
                        promedio = datos_indice["promedio"]

                        tabla_estadisticas_indice = Table(
                            [
                                ["Mínimo", "Máximo", "Promedio", "Desv. estándar"],
                                [
                                    f"{datos_indice['minimo']:.4f}",
                                    f"{datos_indice['maximo']:.4f}",
                                    f"{promedio:.4f}",
                                    f"{datos_indice['desviacion_estandar']:.4f}"
                                ]
                            ],
                            colWidths=[112, 112, 112, 112]
                        )

                        tabla_estadisticas_indice.setStyle(
                            TableStyle([
                                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                                ("FONTSIZE", (0, 0), (-1, -1), 8),
                                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                ("TOPPADDING", (0, 0), (-1, -1), 6),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
                            ])
                        )

                        contenido.append(Spacer(1, 8))
                        contenido.append(tabla_estadisticas_indice)
                        contenido.append(Spacer(1, 8))

                        clasificacion = interpretar_indice(
                            nombre_indice,
                            promedio
                        )

                        contenido.append(
                            Paragraph(
                                f"<b>Interpretación del resultado:</b> "
                                f"Promedio obtenido: {promedio:.4f}. "
                                f"{clasificacion}",
                                estilos["Normal"]
                            )
                        )

                    else:
                        contenido.append(
                            Paragraph(
                                "No hay estadísticas disponibles para "
                                "interpretar este índice.",
                                estilos["Normal"]
                            )
                        )

                    contenido.append(Spacer(1, 15))


                except Exception as e:

                    contenido.append(
                        Paragraph(
                            f"No fue posible cargar el mapa de "
                            f"{nombre_indice}: {e}", texto )
                    )

            else:

                contenido.append(
                    Paragraph(
                        f"No se encontró el mapa correspondiente "
                        f"al índice {nombre_indice}.", texto )
                )

        # DIAGNÓSTICO DEL CULTIVO=====================================

        #contenido.append(PageBreak())

        contenido.append(
            Paragraph(
                "Diagnóstico del estado de salud del cultivo",  encabezado )
        )

        contenido.append(
            Paragraph(
                "Los siguientes resultados corresponden a los "
                "diagnósticos obtenidos mediante los indicadores "
                "espectrales procesados.", texto )
        )

        archivo_diagnostico = (CARPETA_RESULTADOS / "diagnostico_stats.csv")

        diagnosticos = {}

        if archivo_diagnostico.exists():

            with open(archivo_diagnostico, "r", encoding="utf-8-sig") as archivo:

                import csv

                reader = csv.DictReader(archivo)

                for fila in reader:

                    try:

                        diagnosticos[fila["diagnostico"]] = {
                            "promedio": float(fila["promedio"]),
                            "desviacion_estandar": float(
                                fila["desviacion_estandar"]
                            ),
                            "minimo": float(fila["minimo"]),
                            "maximo": float(fila["maximo"])
                        }

                    except (ValueError, KeyError):
                        continue

        orden_diagnosticos = [
            "Vigor vegetativo",
            "Clorofila",
            "Nitrógeno",
            "Estrés hídrico",
            "Densidad del dosel"
        ]

        # DEFINICIONES DE LOS DIAGNÓSTICOS ==========================

        definiciones_diagnosticos = {

            "Vigor vegetativo": (
                "<b>Definición:</b> Indicador que representa el nivel "
                "general de actividad y desarrollo de la vegetación "
                "en el área analizada, obtenido a partir de la "
                "combinación de NDVI, EVI y NDRE."
            ),

            "Clorofila": (
                "<b>Definición:</b> Indicador que representa una "
                "estimación relativa de la respuesta asociada al "
                "contenido de clorofila en la vegetación del área "
                "analizada."
            ),

            "Nitrógeno": (
                "<b>Definición:</b> Indicador que representa una "
                "estimación relativa de la condición de nitrógeno "
                "en la vegetación del área analizada, a partir de "
                "la información espectral utilizada por el aplicativo."
            ),

            "Estrés hídrico": (
                "<b>Definición:</b> Indicador relacionado con la "
                "condición hídrica de la vegetación, obtenido a "
                "partir del NDMI para identificar diferentes niveles "
                "de disponibilidad de humedad en el cultivo."
            ),

            "Densidad del dosel": (
                "<b>Definición:</b> Indicador que representa la "
                "densidad de la cobertura vegetal a partir de la "
                "combinación del LAI estimado mediante NDVI, el "
                "NDVI y el EVI. Valores más altos representan una "
                "mayor densidad del dosel vegetativo."
            )
        }


        for nombre_diagnostico in orden_diagnosticos:

            datos = diagnosticos.get(nombre_diagnostico)

            if datos is None:
                continue

            contenido.append(Paragraph(nombre_diagnostico, subencabezado))

            tabla_diagnostico = Table(
                [
                    [
                        "Mínimo",
                        "Máximo",
                        "Promedio",
                        "Desv. estándar"
                    ],
                    [
                        f"{datos['minimo']:.4f}",
                        f"{datos['maximo']:.4f}",
                        f"{datos['promedio']:.4f}",
                        f"{datos['desviacion_estandar']:.4f}"
                    ]
                ],
                colWidths=[112, 112, 112, 112]
            )

            tabla_diagnostico.setStyle(
                TableStyle([
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
                ])
            )

            contenido.append(tabla_diagnostico)

            # INTERPRETACIÓN AUTOMÁTICA ==============================

            promedio = datos["promedio"]

            if nombre_diagnostico == "Clorofila":

                interpretacion = (
                    f"El valor promedio obtenido es de {promedio:.4f}. "
                    "Este valor corresponde a una estimación relativa "
                    "del contenido de clorofila en la vegetación del "
                    "área analizada. Un valor relativamente mayor "
                    "representa una mayor respuesta asociada a la "
                    "clorofila dentro del área evaluada, mientras que "
                    "un valor relativamente menor representa una "
                    "menor respuesta."
                )

            elif nombre_diagnostico == "Nitrógeno":

                interpretacion = (
                    f"El valor promedio obtenido es de {promedio:.4f}. "
                    "Este valor corresponde a una estimación relativa "
                    "de la condición de nitrógeno en la vegetación del "
                    "área analizada. Un valor relativamente mayor "
                    "representa una mayor respuesta asociada a la "
                    "disponibilidad de nitrógeno dentro del área "
                    "evaluada, mientras que un valor relativamente "
                    "menor representa una menor respuesta."
                )

            elif nombre_diagnostico == "Estrés hídrico":

                if promedio > 0.3:

                    nivel = "Sin estrés hídrico"

                    interpretacion = (
                        "El valor promedio del NDMI indica condiciones "
                        "sin evidencia de estrés hídrico en el área analizada." )

                elif promedio > 0.1:

                    nivel = "Estrés hídrico moderado"

                    interpretacion = (
                        "El valor promedio del NDMI indica condiciones "
                        "de estrés hídrico moderado en el área analizada." )

                else:

                    nivel = "Estrés hídrico alto"

                    interpretacion = (
                        "El valor promedio del NDMI indica condiciones "
                        "de estrés hídrico alto en el área analizada." )

                interpretacion = (
                    f"Nivel: {nivel}. {interpretacion}"  )

            elif nombre_diagnostico == "Vigor vegetativo":

                if promedio < 0.3:

                    nivel = "Bajo"

                    interpretacion = (
                        f"El valor promedio obtenido es de "
                        f"{promedio:.4f}, correspondiente a un "
                        "nivel bajo de vigor vegetativo. Esto "
                        "indica una menor actividad y desarrollo "
                        "de la vegetación en el área analizada."  )

                elif promedio < 0.6:

                    nivel = "Medio"

                    interpretacion = (
                        f"El valor promedio obtenido es de "
                        f"{promedio:.4f}, correspondiente a un "
                        "nivel medio de vigor vegetativo. Esto "
                        "indica una condición intermedia de "
                        "desarrollo de la vegetación en el "
                        "área analizada."  )

                else:

                    nivel = "Alto"

                    interpretacion = (
                        f"El valor promedio obtenido es de "
                        f"{promedio:.4f}, correspondiente a un "
                        "nivel alto de vigor vegetativo. Esto "
                        "indica una condición favorable de "
                        "desarrollo de la vegetación en el "
                        "área analizada."  )

                interpretacion = (
                    f"Nivel: {nivel}. {interpretacion}"   )

            elif nombre_diagnostico == "Densidad del dosel":

                if promedio < 0:

                    nivel = "Muy baja"

                    interpretacion = (
                        "El resultado indica una densidad muy baja "
                        "del dosel vegetal en el área analizada."   )

                elif promedio < 0.33:

                    nivel = "Baja"

                    interpretacion = (
                        "El resultado indica una densidad baja "
                        "del dosel vegetal en el área analizada."   )

                elif promedio < 0.66:

                    nivel = "Media"

                    interpretacion = (
                        "El resultado indica una densidad media "
                        "del dosel vegetal en el área analizada."   )

                else:

                    nivel = "Alta"

                    interpretacion = (
                        "El resultado indica una densidad alta "
                        "del dosel vegetal en el área analizada."   )

                interpretacion = ( f"Nivel: {nivel}. {interpretacion}"   )

            # AGREGAR INTERPRETACIÓN AL PDF ===========================

            contenido.append(Spacer(1, 8))

            contenido.append(Paragraph(f"<b>Interpretación:</b> {interpretacion}", estilos["Normal"] ) )

            contenido.append(Spacer(1, 15) )

        # MAPAS DEL DIAGNÓSTICO =====================================

        #contenido.append(PageBreak())

        contenido.append(Paragraph("Mapas de diagnóstico del estado de salud", encabezado) )

        contenido.append( Paragraph(
                "A continuación se presentan los mapas correspondientes "
                "a los diagnósticos obtenidos para el área de estudio.", texto ) 
                )

        # DEFINICIONES DE LOS DIAGNÓSTICOS ==========================

        definiciones_diagnosticos = {

            "Vigor vegetativo": (
                "<b>Definición:</b> Indicador que representa el nivel "
                "general de actividad y desarrollo de la vegetación "
                "en el área analizada, obtenido a partir de la "
                "combinación de NDVI, EVI y NDRE."
            ),

            "Clorofila": (
                "<b>Definición:</b> Indicador que representa una "
                "estimación relativa de la respuesta asociada al "
                "contenido de clorofila en la vegetación del área "
                "analizada."
            ),

            "Nitrógeno": (
                "<b>Definición:</b> Indicador que representa una "
                "estimación relativa de la condición de nitrógeno "
                "en la vegetación del área analizada, a partir de "
                "la información espectral utilizada por el aplicativo."
            ),

            "Estrés hídrico": (
                "<b>Definición:</b> Indicador relacionado con la "
                "condición hídrica de la vegetación, obtenido a "
                "partir del NDMI para identificar diferentes niveles "
                "de disponibilidad de humedad en el cultivo."
            ),

            "Densidad del dosel": (
                "<b>Definición:</b> Indicador que representa la "
                "densidad de la cobertura vegetal a partir de la "
                "combinación del LAI estimado mediante NDVI, el "
                "NDVI y el EVI. Valores más altos representan una "
                "mayor densidad del dosel vegetativo."
            )
        }

        # MAPAS =====================================================

        mapas_diagnostico = [
            ("Vigor vegetativo", "Vigor.png"),
            ("Clorofila", "Clorofila.png"),
            ("Nitrógeno", "Nitrogeno.png"),
            ("Estrés hídrico", "Estres_Hidrico.png"),
            ("Densidad del dosel", "Densidad_Dosel.png")
        ]

        for nombre_diagnostico, nombre_archivo in mapas_diagnostico:

            ruta_mapa = CARPETA_RESULTADOS / nombre_archivo

            if ruta_mapa.exists():

                contenido.append(Paragraph(nombre_diagnostico, subencabezado))

                try:

                    imagen = RLImage(str(ruta_mapa), width=340, height=280) #

                    imagen.hAlign = "CENTER"

                    contenido.append(imagen)

                    contenido.append(Spacer(1, 8) )

                    # DEFINICIÓN DEBAJO DEL MAPA ====================

                    definicion = definiciones_diagnosticos.get(
                        nombre_diagnostico,"Definición no disponible." )

                    contenido.append(
                        Paragraph( definicion,  estilos["Normal"] ) )

                    contenido.append(Spacer(1, 15) )

                except Exception as e:

                    contenido.append(
                        Paragraph(
                            f"No fue posible cargar el mapa de "
                            f"{nombre_diagnostico}: {e}",  texto )
                    )

            else:

                contenido.append(
                    Paragraph(
                        f"No se encontró el mapa correspondiente "
                        f"al diagnóstico {nombre_diagnostico}.", texto )
                )

        # GENERAR DOCUMENTO=========================================

        documento.build(contenido)

        messagebox.showinfo("Informe PDF", "El informe PDF se generó correctamente.")

    except Exception as e:

        messagebox.showerror("Error al generar PDF", f"No fue posible generar el informe PDF.\n\n{e}")

# FUNCIÓN: NORMALIZAR IMAGEN RGB=====================================

def normalizar_rgb(banda):

    banda = banda.astype(np.float32)

    p2 = np.percentile(banda, 2)
    p98 = np.percentile(banda, 98)

    if p98 <= p2:
        return np.zeros_like(banda, dtype=np.uint8)

    banda = np.clip((banda - p2) / (p98 - p2), 0, 1)

    return (banda * 255).astype(np.uint8)

# FUNCIÓN: CARGAR IMAGEN RGB PARA AOI================================

def cargar_imagen_rgb():

    global imagen_rgb_aoi
    global imagen_rgb_tk
    global factor_x
    global factor_y
    global AOI_BOUNDS

    carpeta = carpeta_seleccionada.get()

    if not carpeta:
        return

    try:

        ruta_b02 = buscar_banda(carpeta, "B02")
        ruta_b03 = buscar_banda(carpeta, "B03")
        ruta_b04 = buscar_banda(carpeta, "B04")

        if not ruta_b02 or not ruta_b03 or not ruta_b04:

            messagebox.showerror("Bandas no encontradas",
                "No se encontraron las bandas B02, B03 y B04 "
                "necesarias para mostrar la imagen RGB.")

            return

        # Cargar B04 como referencia=========================
       
        with rasterio.open(ruta_b04) as src:

            b04 = src.read(1).astype(np.float32)

            alto = src.height
            ancho = src.width

        # Cargar B03=========================================

        with rasterio.open(ruta_b03) as src:

            b03_original = src.read(1).astype(np.float32)

        b03 = resize(b03_original, (alto, ancho), preserve_range=True, anti_aliasing=True)

        # Cargar B02=========================================

        with rasterio.open(ruta_b02) as src:

            b02_original = src.read(1).astype(np.float32)

        b02 = resize(b02_original, (alto, ancho), preserve_range=True, anti_aliasing=True)

        # Crear RGB===========================================

        rojo = normalizar_rgb(b04)
        verde = normalizar_rgb(b03)
        azul = normalizar_rgb(b02)

        rgb = np.dstack((rojo, verde, azul))

        imagen_rgb_aoi = Image.fromarray(rgb)
        
        # Mostrar imagen en el Canvas==========================

        canvas_ancho = 800
        canvas_alto = 430

        imagen_mostrada = imagen_rgb_aoi.copy()

        imagen_mostrada.thumbnail((canvas_ancho, canvas_alto), Image.Resampling.LANCZOS)

        imagen_rgb_tk = ImageTk.PhotoImage(imagen_mostrada)

        canvas_aoi.delete("all")

        canvas_aoi.config(width=imagen_mostrada.width, height=imagen_mostrada.height)

        canvas_aoi.create_image(0, 0, anchor="nw", image=imagen_rgb_tk)

        # ----------------------------------------------------
        # Factores para convertir coordenadas del Canvas
        # a coordenadas reales de la imagen
        # ----------------------------------------------------

        factor_x = (imagen_rgb_aoi.width / imagen_mostrada.width)

        factor_y = (imagen_rgb_aoi.height / imagen_mostrada.height)

        # Reiniciar AOI=======================================

        AOI_BOUNDS = None

        limpiar_aoi_visual()

        etiqueta_aoi.config(
            text=(
                "Imagen RGB cargada.\n\n"
                "Haz clic y arrastra sobre la imagen "
                "para seleccionar el área de interés." )
        )

        estado.set("Imagen RGB cargada. Selecciona el área de interés.")

    except Exception as e:

        messagebox.showerror("Error al cargar imagen", "No fue posible cargar la imagen RGB:\n\n" + str(e))

# FUNCIÓN: LIMPIAR AOI VISUAL=================================

def limpiar_aoi_visual():

    global aoi_rectangulo

    if aoi_rectangulo is not None:

        canvas_aoi.delete(aoi_rectangulo)

        aoi_rectangulo = None

# FUNCIÓN: INICIO DE SELECCIÓN AOI===========================

def iniciar_seleccion(event):

    global aoi_inicio_x
    global aoi_inicio_y
    global aoi_rectangulo

    aoi_inicio_x = event.x
    aoi_inicio_y = event.y

    limpiar_aoi_visual()

    aoi_rectangulo = canvas_aoi.create_rectangle(
        aoi_inicio_x,
        aoi_inicio_y,
        aoi_inicio_x,
        aoi_inicio_y,
        outline="red",
        width=3
    )

# FUNCIÓN: MOVIMIENTO DEL MOUSE==============================

def mover_seleccion(event):

    global aoi_rectangulo

    if (
        aoi_rectangulo is not None
        and aoi_inicio_x is not None
        and aoi_inicio_y is not None
    ):

        canvas_aoi.coords(
            aoi_rectangulo,
            aoi_inicio_x,
            aoi_inicio_y,
            event.x,
            event.y
        )

# FUNCIÓN: FINALIZAR SELECCIÓN AOI=============================

def finalizar_seleccion(event):

    global AOI_BOUNDS

    if (aoi_inicio_x is None or aoi_inicio_y is None):
        
        return

    x1_canvas = min(aoi_inicio_x, event.x)

    y1_canvas = min(aoi_inicio_y, event.y)

    x2_canvas = max(aoi_inicio_x, event.x)

    y2_canvas = max(aoi_inicio_y, event.y)

    # Convertir coordenadas del Canvas a píxeles reales==============

    x1 = int(x1_canvas * factor_x)

    y1 = int(y1_canvas * factor_y)

    x2 = int(x2_canvas * factor_x)

    y2 = int(y2_canvas * factor_y)

    # Verificar que exista un área válida============================

    if (x2 - x1 < 10 or y2 - y1 < 10):

        AOI_BOUNDS = None

        etiqueta_aoi.config(text=("La selección es demasiado pequeña.\n"
                "Selecciona un área mayor.") )

        return

    AOI_BOUNDS = (x1, y1, x2, y2)

    etiqueta_aoi.config(
        text=(
            "Área de interés seleccionada.\n\n"
            f"Coordenadas: X = {x1}:{x2} | "
            f"Y = {y1}:{y2}\n\n"
            "Pulsa 'Confirmar AOI' para utilizar esta zona." )
    )

    estado.set("AOI seleccionada correctamente.")

# FUNCIÓN: LIMPIAR SELECCIÓN AOI=================================

def limpiar_seleccion_aoi():

    global AOI_BOUNDS
    global aoi_inicio_x
    global aoi_inicio_y

    AOI_BOUNDS = None

    aoi_inicio_x = None
    aoi_inicio_y = None

    limpiar_aoi_visual()

    etiqueta_aoi.config(text=(
            "No hay un área de interés seleccionada.\n\n"
            "Haz clic y arrastra sobre la imagen.")
    )

    estado.set("Selección AOI eliminada.")

# FUNCIÓN: CONFIRMAR AOI==========================================

def confirmar_aoi():

    if AOI_BOUNDS is None:

        messagebox.showwarning(
            "AOI",
            "Primero debes seleccionar un área "
            "sobre la imagen RGB."
        )

        return

    x1, y1, x2, y2 = AOI_BOUNDS

    messagebox.showinfo("Área de interés confirmada", (
            "El área de interés ha sido confirmada.\n\n"
            f"X: {x1} - {x2}\n"
            f"Y: {y1} - {y2}\n\n"
            "El procesamiento utilizará únicamente "
            "esta zona." )
    )

    estado.set("AOI confirmada. Puedes iniciar el procesamiento.")

    notebook.select(tab_procesamiento)

# FUNCIÓN: SELECCIONAR CARPETA====================================

def seleccionar_carpeta():

    carpeta = filedialog.askdirectory(title="Seleccionar carpeta de imágenes Sentinel-2")

    if carpeta:

        carpeta_seleccionada.set(carpeta)

        etiqueta_carpeta.config(text=("Carpeta seleccionada:\n\n" + carpeta) )

        estado.set("Carpeta seleccionada correctamente.")

        # Cargar automáticamente RGB
        cargar_imagen_rgb()

# FUNCIÓN: EJECUTAR PROCESAMIENTO===============================

def ejecutar_procesamiento():

    carpeta = carpeta_seleccionada.get()

    if not carpeta:

        messagebox.showwarning(
            "Carpeta no seleccionada",
            "Primero debes seleccionar la carpeta "
            "de imágenes Sentinel-2."
        )

        notebook.select(tab_aoi)

        return

    if not os.path.exists(carpeta):

        messagebox.showerror("Error", "La carpeta seleccionada no existe.")

        return

    if not CARPETA_PROCESAMIENTO.exists():

        messagebox.showerror("Error", "No se encontró el archivo:\n\n" + str(CARPETA_PROCESAMIENTO))

        return

    try:

        estado.set("Procesando imágenes... espera un momento.")

        root.update()

        # Procesamiento con o sin AOI=============================

        runpy.run_path(
            str(CARPETA_PROCESAMIENTO),
            init_globals={
                "CARPETA_IMAGENES": carpeta,
                "AOI_BOUNDS": AOI_BOUNDS }
        )

        estado.set("Procesamiento terminado correctamente.")

        cargar_resultados()

        messagebox.showinfo(
            "Procesamiento finalizado",
            "El procesamiento de las imágenes "
            "terminó correctamente.\n\n"
            "Ahora puedes consultar los resultados."
        )

        notebook.select(tab_resultados)

    except Exception as e:

        estado.set("Se presentó un error durante el procesamiento.")

        messagebox.showerror("Error durante el procesamiento", "Ocurrió un error:\n\n" + str(e))

# FUNCIÓN: CARGAR RESULTADOS===================================

def cargar_resultados():

    if not CARPETA_RESULTADOS.exists():

        return

    nombres_resultados = {

        # ÍNDICES===============================================

        "NDVI":
            "NDVI_n.png",

        "NDRE":
            "NDRE_n.png",

        "EVI":
            "EVI_n.png",

        "NDMI":
            "NDMI_n.png",

        "CIred-edge":
            "CIre_n.png",

        "TCARI/OSAVI":
            "TCARI_OSAVI_n.png",

        "LAI NDVI":
            "LAI_NDVI_n.png"
    }

    resultados_disponibles = []

    for nombre, archivo in nombres_resultados.items():

        ruta = (CARPETA_RESULTADOS / archivo)

        if ruta.exists():

            resultados_disponibles.append(nombre)

    combo_resultados["values"] = resultados_disponibles

    if resultados_disponibles:

        combo_resultados.current(0)

        titulo_resultado.config(text=("Selecciona un resultado y pulsa "
                "'Mostrar resultado'") )

    else:

        titulo_resultado.config(text="No hay resultados disponibles")
        
# FUNCIÓN: CARGAR ESTADÍSTICAS================================

def cargar_estadisticas():

    csv_path = (CARPETA_RESULTADOS / "indices_stats.csv")

    if not csv_path.exists():

        return {}

    estadisticas = {}

    try:

        with open(csv_path, "r", encoding="utf-8") as f:

            import csv

            reader = csv.DictReader(f)

            for fila in reader:

                nombre = fila["indice"]

                estadisticas[nombre] = {

                    "minimo": float(fila["minimo"]),

                    "maximo": float(fila["maximo"]),

                    "promedio": float(fila["promedio"]),

                    "desviacion_estandar": float(fila["desviacion_estandar"]),

                    "percentil_2": float(fila["percentil_2"]),

                    "percentil_98": float(fila["percentil_98"])
                }

    except Exception as e:

        print("Error al cargar estadísticas:", e)

        return {}

    return estadisticas

# FUNCIÓN: CARGAR ESTADÍSTICAS DEL DIAGNÓSTICO==============================

def cargar_diagnostico():

    csv_path = (CARPETA_RESULTADOS / "diagnostico_stats.csv")

    if not csv_path.exists():
        return {}

    diagnostico = {}

    try:

        with open(csv_path, "r", encoding="utf-8") as f:

            import csv

            reader = csv.DictReader(f)

            for fila in reader:

                nombre = fila["diagnostico"]

                diagnostico[nombre] = {

                    "promedio": float(fila["promedio"]),

                    "desviacion_estandar": float(fila["desviacion_estandar"]),

                    "minimo": float(fila["minimo"]),

                    "maximo": float(fila["maximo"])
                }

    except Exception as e:

        print("Error al cargar diagnóstico:", e)

        return {}

    return diagnostico

# INTERPRETACIONES DEL DIAGNÓSTICO=============================

interpretaciones_diagnostico = {

    "Vigor vegetativo": (
        "El vigor vegetativo representa el estado general "
        "de desarrollo y actividad de la vegetación. "
        "Valores más altos indican una vegetación "
        "con mayor vigor."
    ),

    "Clorofila": (
        "La clorofila estimada representa un indicador "
        "relativo asociado al contenido de clorofila "
        "de la vegetación. Valores mayores representan "
        "una mayor respuesta relativa del indicador."
    ),

    "Nitrógeno": (
        "El nitrógeno estimado corresponde a un indicador "
        "relativo basado en índices espectrales asociados "
        "con características nutricionales de la vegetación."
    ),

    "Estrés hídrico": (
        "El estrés hídrico se determina a partir del NDMI. "
        "El resultado permite identificar zonas sin estrés, "
        "con estrés moderado o con estrés alto."
    ),

    "Densidad del dosel": (
    "Este indicador representa la densidad de la cobertura vegetal "
    "a partir de la combinación del LAI estimado mediante NDVI, "
    "el NDVI y el EVI. Valores más altos representan una mayor "
    "densidad del dosel vegetativo."
),
}

def actualizar_opciones_resultado(event=None):

    tipo = combo_tipo_resultado.get()

    if tipo == "Índices":

        opciones = ["NDVI", "NDRE", "EVI", "NDMI", "CIred-edge", "TCARI/OSAVI", "LAI NDVI",]

    else:

        opciones = ["Vigor vegetativo", "Clorofila", "Nitrógeno", "Estrés hídrico", "Densidad del dosel"]

    combo_resultados["values"] = opciones

    if opciones:
        combo_resultados.current(0)

# INTERPRETACIÓN DE LOS ÍNDICES==================================

interpretaciones = {

    "NDVI": (
        "El NDVI permite evaluar el vigor y la "
        "cantidad de vegetación presente en el cultivo. "
        "Valores más altos generalmente indican una "
        "vegetación más vigorosa y desarrollada."
    ),

    "NDRE": (
        "El NDRE permite analizar características "
        "relacionadas con el estado de la vegetación "
        "y el contenido de clorofila. Es especialmente "
        "útil en cultivos con vegetación densa."
    ),

    "EVI": (
        "El EVI permite analizar el vigor de la vegetación "
        "y reducir algunos efectos producidos por el suelo "
        "y la atmósfera. Se utiliza como complemento del NDVI."
    ),

    "NDMI": (
        "El NDMI permite analizar el contenido relativo "
        "de humedad de la vegetación. En este proyecto "
        "también se utiliza para evaluar el estrés hídrico."
    ),

    "CIred-edge": (
        "El CIred-edge relaciona la respuesta espectral "
        "del infrarrojo cercano y del borde rojo. "
        "Se utiliza como indicador relacionado con "
        "el contenido de clorofila."
    ),

    "TCARI/OSAVI": (
        "El TCARI/OSAVI permite analizar características "
        "relacionadas con la clorofila y reducir la "
        "influencia del suelo."
    ),

        "LAI NDVI": (
        "El LAI estimado mediante NDVI representa "
        "la cantidad de superficie foliar respecto "
        "al área de suelo y permite analizar la "
        "densidad y desarrollo de la vegetación."
    ),

}

#============================================================

def interpretar_indice(resultado, promedio):
    """Interpreta el promedio según las categorías del procesamiento."""

    import numpy as np

    if not np.isfinite(promedio):
        return "Sin datos válidos para interpretar."

    # NDVI
    if resultado == "NDVI":
        if promedio < 0:
            return "Superficies sin vegetación verde."
        elif promedio < 0.2:
            return "Suelo expuesto o cobertura vegetal muy escasa."
        elif promedio < 0.5:
            return "Vegetación dispersa o dosel aún abierto."
        elif promedio < 0.8:
            return "Vegetación verde de moderada a densa."
        elif promedio <= 1:
            return "Dosel verde muy denso; el NDVI puede perder sensibilidad."
        return "Valor fuera del rango de referencia."

    # NDRE
    elif resultado == "NDRE":
        if promedio < 0:
            return "Suelo o ausencia de vegetación."
        elif promedio < 0.3:
            return "Vegetación escasa; posible etapa temprana del cultivo."
        elif promedio < 0.6:
            return "Densidad media de vegetación."
        elif promedio <= 1:
            return "Alta densidad de vegetación."
        return "Valor fuera del rango de referencia."

    # NDMI
    elif resultado == "NDMI":
        if promedio < -0.4:
            return "Cobertura vegetal muy baja; predominan superficies secas o suelo expuesto."
        elif promedio < -0.1:
            return "Cobertura vegetal baja y humedad reducida."
        elif promedio < 0.1:
            return "Humedad baja; puede indicar estrés hídrico."
        elif promedio < 0.3:
            return "Humedad media; sin evidencia clara de estrés hídrico significativo."
        elif promedio < 0.5:
            return "Humedad alta; verificar posibles condiciones de exceso."
        elif promedio <= 1:
            return "Humedad muy alta; verificar posible agua libre o encharcamiento."
        return "Valor fuera del rango de referencia."

    # CIred-edge
    elif resultado == "CIred-edge":
        if promedio < 0:
            return "Valor fuera del rango de referencia."
        elif promedio <= 1:
            return "Puede indicar ausencia o muy baja respuesta de clorofila."
        elif promedio <= 3:
            return "Posible estrés alto o etapa de emergencia."
        elif promedio <= 6:
            return "Desarrollo medio y contenido relativo de clorofila aceptable."
        elif promedio <= 10:
            return "Vigor óptimo según las categorías del procesamiento."
        elif promedio <= 15:
            return "Respuesta muy elevada; verificar la densidad vegetal."
        return "Valor superior al rango de referencia."

    # LAI NDVI
    elif resultado == "LAI NDVI":
        if promedio < 0:
            return "Valor fuera del rango de referencia."
        elif promedio == 0:
            return "Sin área foliar estimada."
        elif promedio < 1:
            return "Baja densidad del dosel."
        elif promedio < 3.5:
            return "Densidad intermedia del dosel."
        elif promedio <= 5:
            return "Densidad alta del dosel."
        return "Valor superior al rango de referencia."

    
    # EVI
    elif resultado == "EVI":
        if promedio < 0:
            return "Agua, nieve, nubes u otras superficies sin vegetación."
        elif promedio < 0.2:
            return ("Vegetación escasa, suelo expuesto, crecimiento muy temprano "
                    "o vegetación senescente.")
        
        elif promedio < 0.4:
            return ("Vegetación moderada o en desarrollo; crecimiento temprano a medio.")
        
        elif promedio < 0.6:
            return ("Vegetación sana y moderadamente densa; cultivo bien desarrollado.")
        
        elif promedio < 0.9:
            return ("Vegetación muy densa y vigorosa; cobertura vegetal elevada.")
        
        elif promedio <= 1:
            return ("Vegetación extremadamente densa; valores próximos a la "
                    "saturación del índice.")
        else:
            return "Valor fuera del rango de referencia."

    # TCARI/OSAVI
    elif resultado == "TCARI/OSAVI":
        if promedio < 0:
            return ("Valor inferior al rango de referencia; puede corresponder "
                    "a un valor extremo o a condiciones no contempladas "
                    "en la clasificación.")
        
        elif promedio <= 0.2:
            return ("Vigor máximo; vegetación muy densa y con alto contenido "
                    "relativo de clorofila.")
        
        elif promedio <= 0.5:
            return ("Vegetación saludable; cultivo en condiciones normales "
                    "y con desarrollo favorable.")
        
        elif promedio <= 0.7:
            return ("Estrés leve o moderado; puede indicar el inicio de clorosis "
                    "y requiere evaluar las condiciones nutricionales.")
        
        elif promedio <= 1.0:
            return ("Estrés severo; puede estar asociado con clorosis avanzada, "
                    "plagas, enfermedades o deficiencias nutricionales importantes.")
        
        else:
            return ("Sin vegetación útil o valor anómalo; puede corresponder "
                    "a suelo expuesto, vegetación seca o posibles problemas "
                    "de procesamiento.")

    return "No hay una interpretación disponible para este índice."

# FUNCIÓN: MOSTRAR RESULTADO=================================

def mostrar_resultado():

    resultado = combo_resultados.get()
    tipo = combo_tipo_resultado.get()

    if not resultado:
        messagebox.showwarning("Resultado", "Selecciona un resultado.")
        return

    # RESULTADOS: ÍNDICES====================================

    if tipo == "Índices":

        archivos = {
            "NDVI": "NDVI_n.png",
            "NDRE": "NDRE_n.png",
            "EVI": "EVI_n.png",
            "NDMI": "NDMI_n.png",
            "CIred-edge": "CIre_n.png",
            "TCARI/OSAVI": "TCARI_OSAVI_n.png",
            "LAI NDVI": "LAI_NDVI_n.png",
        }

        archivo = archivos.get(resultado)

        if archivo is None:
            messagebox.showerror("Error", "No se encontró el archivo correspondiente al índice.")
            return

        ruta_imagen = CARPETA_RESULTADOS / archivo

        if not ruta_imagen.exists():
            messagebox.showerror("Error", f"No se encontró el resultado:\n{ruta_imagen}")
            
            return

        # MOSTRAR MAPA DEL ÍNDICE=================================

        try:

            imagen = Image.open(ruta_imagen)

            imagen.thumbnail((650, 480) )

            imagen_tk = ImageTk.PhotoImage(imagen)

            etiqueta_imagen.configure(image=imagen_tk, text="")

            etiqueta_imagen.image = imagen_tk

            titulo_resultado.configure(text=f"Mapa de {resultado}")

        except Exception as e:

            messagebox.showerror("Error", f"No fue posible cargar el mapa:\n{e}")

            return

        # CARGAR ESTADÍSTICAS DEL ÍNDICE=================================
        estadisticas = cargar_estadisticas()

        datos = estadisticas.get(resultado)

        if datos is None:

            etiqueta_estadisticas.configure(text="No hay estadísticas disponibles para este índice.")

        else:

            texto_estadisticas = (
                f"Mínimo:                 "
                f"{datos['minimo']:.4f}\n\n"

                f"Máximo:                 "
                f"{datos['maximo']:.4f}\n\n"

                f"Promedio:               "
                f"{datos['promedio']:.4f}\n\n"

                f"Desviación estándar:    "
                f"{datos['desviacion_estandar']:.4f}\n\n"
            )

            etiqueta_estadisticas.configure(text=texto_estadisticas)

        # INTERPRETACIÓN DEL ÍNDICE ================================

        texto_interpretacion = ("No hay estadísticas disponibles para interpretar este índice.")

        if datos is not None:
            promedio = datos["promedio"]

            definicion = interpretaciones.get(resultado,"No hay una descripción disponible para este índice.")

            clasificacion = interpretar_indice(resultado, promedio)
            
            texto_interpretacion = (
                f"{definicion}\n\n"
                f"Interpretación del resultado:\n"
                f"Promedio obtenido: {promedio:.4f}\n"
                f"{clasificacion}"
            )

        etiqueta_interpretacion.configure(text=texto_interpretacion)

    # RESULTADOS: DIAGNÓSTICO ======================================

    else:

        diagnostico = cargar_diagnostico()

        datos = diagnostico.get(resultado)

        if datos is None:
            messagebox.showwarning("Diagnóstico", "No hay información disponible para este diagnóstico.")
            return

        # ESTADÍSTICAS DEL DIAGNÓSTICO=============================

        texto_estadisticas = (
            f"Mínimo:                 "
            f"{datos['minimo']:.4f}\n\n"

            f"Máximo:                 "
            f"{datos['maximo']:.4f}\n\n"

            f"Promedio:               "
            f"{datos['promedio']:.4f}\n\n"

            f"Desviación estándar:    "
            f"{datos['desviacion_estandar']:.4f}"
        )

        etiqueta_estadisticas.configure(text=texto_estadisticas)

        # INTERPRETACIÓN DEL DIAGNÓSTICO==============================

        texto_interpretacion = interpretaciones_diagnostico.get(resultado, "No hay una interpretación disponible para este diagnóstico.")

        # INTERPRETACIÓN AUTOMÁTICA DE CLOROFILA=======================

        if resultado == "Clorofila":

            promedio = datos["promedio"]

            texto_interpretacion = (
                f"{texto_interpretacion}\n\n"
                f"Interpretación del resultado:\n"
                f"El valor promedio obtenido es de {promedio:.4f}. "
                "Este valor corresponde a una estimación relativa "
                "del contenido de clorofila en la vegetación del "
                "área analizada. Un valor relativamente mayor "
                "representa una mayor respuesta asociada a la "
                "clorofila dentro del área evaluada, mientras que "
                "un valor relativamente menor representa una "
                "menor respuesta."
            )

        # INTERPRETACIÓN AUTOMÁTICA DE NITRÓGENO=======================

        if resultado == "Nitrógeno":

            promedio = datos["promedio"]

            texto_interpretacion = (
                f"{texto_interpretacion}\n\n"
                f"Interpretación del resultado:\n"
                f"El valor promedio obtenido es de {promedio:.4f}. "
                "Este valor corresponde a una estimación relativa "
                "de la condición de nitrógeno en la vegetación del "
                "área analizada. Un valor relativamente mayor "
                "representa una mayor respuesta asociada a la "
                "disponibilidad de nitrógeno dentro del área "
                "evaluada, mientras que un valor relativamente "
                "menor representa una menor respuesta."
            )

        # INTERPRETACIÓN AUTOMÁTICA DE ESTRÉS HÍDRICO=================

        if resultado == "Estrés hídrico":

            promedio = datos["promedio"]

            if promedio > 0.3:

                nivel_estres = "Sin estrés hídrico"

                interpretacion_estres = ("El valor promedio del NDMI indica condiciones "
                                         "sin evidencia de estrés hídrico en el área analizada.")

            elif promedio > 0.1:

                nivel_estres = "Estrés hídrico moderado"

                interpretacion_estres = ("El valor promedio del NDMI indica condiciones "
                                         "de estrés hídrico moderado en el área analizada.")

            else:

                nivel_estres = "Estrés hídrico alto"

                interpretacion_estres = ("El valor promedio del NDMI indica condiciones "
                                         "de estrés hídrico alto en el área analizada.")

            texto_interpretacion = (
                f"{texto_interpretacion}\n\n"
                f"Interpretación del resultado:\n"
                f"Nivel: {nivel_estres}\n"
                f"{interpretacion_estres}"
            )

        # INTERPRETACIÓN AUTOMÁTICA DEL VIGOR===========================

        if resultado == "Vigor vegetativo":

            promedio = datos["promedio"]

            if promedio < 0.3:

                nivel = "Bajo"

                interpretacion_resultado = (f"El valor promedio obtenido es de {promedio:.4f}, "
                                            "correspondiente a un nivel bajo de vigor vegetativo. "
                                            "Esto indica una menor actividad y desarrollo de la "
                                            "vegetación en el área analizada." )

            elif promedio < 0.6:

                nivel = "Medio"

                interpretacion_resultado = (f"El valor promedio obtenido es de {promedio:.4f}, "
                                            "correspondiente a un nivel medio de vigor vegetativo. "
                                            "Esto indica una condición intermedia de desarrollo "
                                            "de la vegetación en el área analizada." )

            else:

                nivel = "Alto"

                interpretacion_resultado = (f"El valor promedio obtenido es de {promedio:.4f}, "
                                            "correspondiente a un nivel alto de vigor vegetativo. "
                                            "Esto indica una condición favorable de desarrollo "
                                            "de la vegetación en el área analizada." )

            texto_interpretacion = (f"{texto_interpretacion}\n\n"
                                    f"Interpretación del resultado:\n"
                                    f"Nivel: {nivel}\n"
                                    f"{interpretacion_resultado}" )

        # INTERPRETACIÓN AUTOMÁTICA DE DENSIDAD DEL DOSEL=============

        if resultado == "Densidad del dosel":

            promedio = datos["promedio"]

            if promedio < 1:

                nivel_densidad = "Densidad baja"

                interpretacion_resultado = ("El valor promedio indica una baja densidad del dosel "
                                            "vegetativo en el área analizada." )

            elif promedio < 3:

                nivel_densidad = "Densidad media"

                interpretacion_resultado = ("El valor promedio indica una densidad intermedia del "
                                            "dosel vegetativo. Se recomienda revisar la distribución "
                                            "espacial de los valores para identificar posibles zonas "
                                            "con menor cobertura." )

            else:

                nivel_densidad = "Densidad alta"

                interpretacion_resultado = ("El valor promedio indica una alta densidad del dosel "
                                            "vegetativo en el área analizada." )

            texto_interpretacion = (f"{texto_interpretacion}\n\n"
                                    f"Interpretación del resultado:\n"
                                    f"Nivel: {nivel_densidad}\n"
                                    f"{interpretacion_resultado}" )

        # MOSTRAR INTERPRETACIÓN EN LA INTERFAZ ======================

        etiqueta_interpretacion.configure(text=texto_interpretacion)

        # MOSTRAR MAPA DEL DIAGNÓSTICO=============================

        archivos_diagnostico = {"Vigor vegetativo": "Vigor.png",
                                "Clorofila": "Clorofila.png",
                                "Nitrógeno": "Nitrogeno.png",
                                "Estrés hídrico": "Estres_Hidrico.png",
                                "Densidad del dosel": "Densidad_Dosel.png" }

        archivo = archivos_diagnostico.get(resultado)

        if archivo is None:
            messagebox.showerror("Error", "No se encontró el archivo correspondiente al diagnóstico.")
            return

        ruta_imagen = CARPETA_RESULTADOS / archivo

        if not ruta_imagen.exists():
            messagebox.showerror("Error", f"No se encontró el resultado:\n{ruta_imagen}")
            return

        try:

            imagen = Image.open(ruta_imagen)

            imagen.thumbnail((650, 480))

            imagen_tk = ImageTk.PhotoImage(imagen)

            etiqueta_imagen.configure(image=imagen_tk, text="")

            etiqueta_imagen.image = imagen_tk

            titulo_resultado.configure(text=f"Diagnóstico: {resultado}")

        except Exception as e:

            messagebox.showerror("Error", f"No fue posible cargar el mapa:\n{e}")

            return

# PESTAÑA INICIO=========================================

frame_inicio = ttk.Frame(tab_inicio)

frame_inicio.pack(expand=True)

ttk.Label( frame_inicio,
    text="Análisis de salud de cultivos de papa",
    style="Titulo.TLabel").pack( pady=(80, 20))

ttk.Label(frame_inicio,
    text=("Procesamiento y análisis de imágenes "
        "satelitales Sentinel-2"), 
    style="Subtitulo.TLabel").pack(pady=10)

ttk.Label(frame_inicio,
    text=("Aplicativo para la evaluación del estado "
        "de salud de cultivos de papa mediante "
        "índices de vegetación."),
    style="Texto.TLabel", 
    justify="center").pack(pady=20)

ttk.Button(frame_inicio,
    text="Comenzar análisis",
    style="Boton.TButton", command=lambda: notebook.select(tab_aoi)).pack(pady=30)

# PESTAÑA ÁREA DE INTERÉS========================================

ttk.Label(tab_aoi,
    text="Área de interés",
    style="Titulo.TLabel").pack(pady=15)

ttk.Label(tab_aoi,
    text=("Selecciona una carpeta de imágenes Sentinel-2 "
        "y posteriormente selecciona con el mouse "
        "la zona del cultivo que deseas analizar."),
    style="Texto.TLabel",
    justify="center").pack(pady=5)

# Botón seleccionar carpeta====================================

ttk.Button(tab_aoi,
    text="Seleccionar carpeta de imágenes",
    style="Boton.TButton",command=seleccionar_carpeta).pack(pady=10)

etiqueta_carpeta = ttk.Label(tab_aoi,
    text=("No se ha seleccionado ninguna carpeta."),
    style="Texto.TLabel", 
    justify="center")

etiqueta_carpeta.pack(pady=5)

# CONTENEDOR PRINCIPAL DEL ÁREA DE INTERÉS =======================

frame_contenido_aoi = ttk.Frame(tab_aoi)

frame_contenido_aoi.pack(pady=5, padx=10)


# MARCO PARA IMAGEN RGB ==========================================

frame_canvas = ttk.Frame(frame_contenido_aoi)

frame_canvas.pack(side="left", padx=(0, 10), pady=5)

canvas_aoi = tk.Canvas(
    frame_canvas,
    width=800,
    height=430,
    bg="lightgray",
    highlightthickness=1,
    highlightbackground="gray"
)

canvas_aoi.pack()

# EVENTOS DEL MOUSE ==============================================

canvas_aoi.bind("<ButtonPress-1>", iniciar_seleccion)

canvas_aoi.bind("<B1-Motion>", mover_seleccion)

canvas_aoi.bind("<ButtonRelease-1>", finalizar_seleccion)

# INFORMACIÓN AOI ================================================

etiqueta_aoi = ttk.Label(tab_aoi, text=("Selecciona una carpeta para cargar "
                                        "la imagen RGB."),
    style="Texto.TLabel",
    justify="center")

etiqueta_aoi.pack(pady=2)

# PANEL LATERAL DE BOTONES AOI ===================================

frame_botones_aoi_derecha = ttk.Frame(
    frame_contenido_aoi
)

frame_botones_aoi_derecha.pack(
    side="right",
    padx=(10, 10),
    pady=10
)

# BOTÓN: LIMPIAR SELECCIÓN =======================================

ttk.Button(
    frame_botones_aoi_derecha,
    text="Limpiar selección",
    style="Boton.TButton",
    command=limpiar_seleccion_aoi
).pack(
    pady=(20, 10),
    ipadx=5
)

# BOTÓN: CONFIRMAR AOI ===========================================

ttk.Button(
    frame_botones_aoi_derecha,
    text="Confirmar AOI",
    style="Boton.TButton",
    command=confirmar_aoi
).pack(
    pady=10,
    ipadx=5
)

# PESTAÑA PROCESAMIENTO==================================

ttk.Label(
    tab_procesamiento,
    text="Procesamiento de imágenes",
    style="Titulo.TLabel"
).pack(
    pady=30
)

ttk.Label(
    tab_procesamiento,
    text=("Ejecuta el procesamiento para calcular "
          "los índices y generar los mapas de resultados." ),
    style="Texto.TLabel",
    justify="center"
).pack(pady=15)

ttk.Button(
    tab_procesamiento,
    text="Ejecutar procesamiento",
    style="Boton.TButton",
    command=ejecutar_procesamiento
).pack(pady=30)

ttk.Label(
    tab_procesamiento,
    textvariable=estado,
    style="Texto.TLabel",
    justify="center"
).pack(pady=20)

# PESTAÑA RESULTADOS===========================================

ttk.Label(
    tab_resultados,
    text="Resultados del análisis",
    style="Titulo.TLabel"
).pack(pady=15)

# SELECTOR DE RESULTADOS======================================

frame_selector = ttk.Frame(tab_resultados)
frame_selector.pack(pady=5)

ttk.Label(
    frame_selector,
    text="Tipo de resultado:"
).pack(side="left", padx=5)

combo_tipo_resultado = ttk.Combobox(
    frame_selector,
    state="readonly",
    width=15,
    values=["Índices", "Diagnóstico"]
)
combo_tipo_resultado.set("Índices")
combo_tipo_resultado.pack(side="left", padx=5)

combo_tipo_resultado.bind(
    "<<ComboboxSelected>>",
    actualizar_opciones_resultado
)

ttk.Label(
    frame_selector,
    text="Seleccionar:"
).pack(side="left", padx=5)

combo_resultados = ttk.Combobox(
    frame_selector,
    state="readonly",
    width=25
)
combo_resultados.pack(side="left", padx=5)

ttk.Button(
    frame_selector,
    text="Mostrar resultado",
    command=mostrar_resultado
).pack(side="left", padx=10)

ttk.Button(
    frame_selector,
    text="Generar informe PDF",
    command=generar_informe_pdf
).pack(side="left", padx=10)

# CONTENEDOR PRINCIPAL===========================================

frame_contenido = ttk.Frame(tab_resultados)

frame_contenido.pack(
    fill="both",
    expand=True,
    padx=15,
    pady=10
)

frame_contenido.columnconfigure(0,weight=3)

frame_contenido.columnconfigure(1,weight=2)

frame_contenido.rowconfigure(0,weight=1)

# PANEL IZQUIERDO: MAPA============================================

frame_mapa = ttk.LabelFrame(frame_contenido,text="Mapa del resultado")

frame_mapa.grid(
    row=0,
    column=0,
    sticky="nsew",
    padx=(0, 10)
)

titulo_resultado = ttk.Label(
    frame_mapa,
    text="Selecciona un resultado",
    font=("Arial", 14, "bold")
)

titulo_resultado.pack(pady=10)

etiqueta_imagen = ttk.Label(
    frame_mapa,
    text="Aquí aparecerá el mapa del índice seleccionado.",
    anchor="center",
    justify="center"
)

etiqueta_imagen.pack(
    expand=True,
    fill="both",
    padx=10,
    pady=10
)

# PANEL DERECHO: INFORMACIÓN========================================

frame_informacion = ttk.LabelFrame(frame_contenido, text="Información del resultado")

frame_informacion.grid(
    row=0,
    column=1,
    sticky="nsew"
)

# ESTADÍSTICAS=======================================================

ttk.Label(
    frame_informacion,
    text="Estadísticas",
    font=("Arial", 13, "bold")
).pack(
    anchor="w",
    padx=15,
    pady=(15, 10)
)

etiqueta_estadisticas = ttk.Label(
    frame_informacion,
    text="Selecciona un índice para visualizar sus estadísticas.",
    justify="left",
    anchor="nw",
    font=("Arial", 10)
)

etiqueta_estadisticas.pack(
    fill="x",
    padx=15,
    pady=5
)

ttk.Separator(
    frame_informacion,
    orient="horizontal"
).pack(
    fill="x",
    padx=15,
    pady=15
)

# INTERPRETACIÓN=============================================

ttk.Label(
    frame_informacion,
    text="Interpretación",
    font=("Arial", 13, "bold")
).pack(
    anchor="w",
    padx=15,
    pady=(5, 10)
)

etiqueta_interpretacion = ttk.Label(
    frame_informacion,
    text="Aquí aparecerá la interpretación del índice seleccionado.",
    justify="left",
    anchor="nw",
    wraplength=300,
    font=("Arial", 10)
)

etiqueta_interpretacion.pack(
    fill="both",
    expand=True,
    padx=15,
    pady=5
)

# PESTAÑA AYUDA==================================================

ttk.Label(
    tab_ayuda,
    text="Ayuda",
    style="Titulo.TLabel"
).pack(
    pady=20
)

frame_ayuda = ttk.Frame(tab_ayuda)

frame_ayuda.pack(
    fill="both",
    expand=True,
    padx=30,
    pady=10
)

texto_ayuda = tk.Text(
    frame_ayuda,
    wrap="word",
    font=("Arial", 11),
    padx=15,
    pady=15
)

texto_ayuda.pack(
    side="left",
    fill="both",
    expand=True
)

scroll_ayuda = ttk.Scrollbar(
    frame_ayuda,
    orient="vertical",
    command=texto_ayuda.yview
)

scroll_ayuda.pack(
    side="right",
    fill="y"
)

texto_ayuda.configure(yscrollcommand=scroll_ayuda.set)

# CONTENIDO DE AYUDA====================================================

texto_ayuda.insert(
    "1.0",
    """
GUÍA DE LOS ÍNDICES EVALUADOS
========================================


NDVI
Índice de Vegetación de Diferencia Normalizada

Permite evaluar el vigor y la cantidad de vegetación
presente en el cultivo.

Un valor alto generalmente representa una vegetación
más vigorosa y desarrollada.

Un valor bajo puede indicar menor desarrollo de la
vegetación, suelo expuesto o algún tipo de estrés.


NDRE
Índice de Diferencia Normalizada de Borde Rojo

Permite analizar características relacionadas con
el estado de la vegetación y el contenido de clorofila.

Es especialmente útil en cultivos con vegetación densa.


EVI
Índice de Vegetación Mejorado

Permite analizar el vigor de la vegetación y reducir
algunos efectos producidos por el suelo y la atmósfera.

Se utiliza como complemento del NDVI.


NDMI
Índice de Humedad de Diferencia Normalizada

Permite analizar el contenido relativo de humedad
de la vegetación.

En este proyecto también se utiliza para realizar
la clasificación del estrés hídrico.


CIred-edge
Índice de Clorofila de Borde Rojo

Relaciona la respuesta espectral del infrarrojo cercano
y del borde rojo.

Se utiliza como indicador relacionado con el contenido
de clorofila.


TCARI/OSAVI

Es una combinación de índices utilizada para analizar
características relacionadas con la clorofila y reducir
la influencia del suelo.

Es útil para el análisis de cultivos.


LAI
Índice de Área Foliar

Representa la cantidad de superficie foliar existente
respecto al área de suelo.

Permite analizar la densidad y desarrollo de la vegetación.


CLOROFILA ESTIMADA

El procesamiento genera una estimación relativa
asociada al contenido de clorofila.

Debe interpretarse como un indicador relativo dentro
del análisis si no existe una calibración con mediciones
de campo.


NITRÓGENO RELATIVO

El procesamiento genera una estimación relativa
relacionada con el estado nutricional del cultivo.

Su interpretación debe realizarse como un indicador
relativo.


ESTRÉS HÍDRICO

La clasificación utilizada en el proyecto considera
tres categorías:

• Sin estrés
• Estrés moderado
• Estrés alto

Estas categorías se determinan mediante los valores
de NDMI y los umbrales definidos en el procesamiento.


VIGOR VEGETATIVO

El vigor vegetativo combina información de NDVI y EVI
para obtener un indicador general del comportamiento
de la vegetación.


ÁREA DE INTERÉS (AOI)

El área de interés permite seleccionar únicamente
una zona específica de la imagen para realizar
el análisis.

Para seleccionar el área:

1. Selecciona la carpeta de imágenes Sentinel-2.

2. Espera a que aparezca la imagen RGB.

3. Haz clic sobre la imagen y arrastra el mouse.

4. Se mostrará un rectángulo sobre la zona seleccionada.

5. Pulsa "Confirmar AOI".

6. Ejecuta el procesamiento.

Si no se selecciona un área de interés, se procesará
la imagen completa.

"""
)

texto_ayuda.configure(state="disabled")

# BARRA INFERIOR==============================================

barra_inferior = ttk.Frame(root)

barra_inferior.pack(
    fill="x",
    padx=10,
    pady=(0, 10)
)

ttk.Label(barra_inferior,text=("Proyecto de grado | Análisis de cultivos de papa"), font=("Arial", 9)) .pack( side="left")

ttk.Label(barra_inferior, textvariable=estado, font=("Arial", 9)).pack(side="right")

# INICIO=================================================

cargar_resultados()

actualizar_opciones_resultado()

root.mainloop()