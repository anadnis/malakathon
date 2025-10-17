# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path

# --- Configuración de salida bonita ---
pd.set_option("display.max_rows", 200)
pd.set_option("display.max_columns", 200)
pd.set_option("display.width", 160)

# --- Cargar XLS (requiere xlrd instalado) ---
# pip install xlrd
df = pd.read_excel("SaludMental.xls", engine="xlrd")

print("\n=== INFO GENERAL ===")
print(df.info())
print("\n=== PRIMERAS FILAS ===")
print(df.head())

# --- Intento de detección/parseo de fechas (por nombre de columna) ---
posibles_fechas = [c for c in df.columns if any(k in c.lower() for k in ["fecha", "fec", "ingres", "alta", "nac", "interv"])]
for c in posibles_fechas:
    try:
        df[c] = pd.to_datetime(df[c], errors="coerce", dayfirst=True)
    except Exception:
        pass

# Recontar tipos tras convertir fechas
print("\n=== TIPOS DE DATO (tras parseo de fechas) ===")
print(df.dtypes.value_counts())

# --- Clasificación por tipo de dato ---
categoricas = df.select_dtypes(include="object").columns.tolist()
numericas   = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
fechas      = df.select_dtypes(include="datetime64[ns]").columns.tolist()

print(f"\nVariables categóricas: {len(categoricas)}")
print(f"Variables numéricas:   {len(numericas)}")
print(f"Variables de fecha:    {len(fechas)}")

print("\nEjemplos de variables por tipo:")
print(" - Categóricas:", categoricas[:10])
print(" - Numéricas:  ", numericas[:10])
print(" - Fechas:     ", fechas[:10])

# --- Estadísticos descriptivos ---
print("\n=== DESCRIPTIVOS NUMÉRICOS ===")
desc_num = df[numericas].describe().T
print(desc_num)

print("\n=== DESCRIPTIVOS CATEGÓRICOS (conteo top 10) ===")
for col in categoricas[:5]:  # muestra 5 como ejemplo (puedes ampliar)
    vc = df[col].value_counts(dropna=False).head(10)
    print(f"\n-- {col} --")
    print(vc)

# --- Nulos y unicidad ---
summary = pd.DataFrame({
    "Tipo de dato": df.dtypes.astype(str),
    "Valores únicos": df.nunique(dropna=True),
    "Nulos": df.isna().sum(),
})
summary["% Nulos"] = (summary["Nulos"] / len(df) * 100).round(2)
summary = summary.sort_values(["% Nulos", "Nulos"], ascending=[False, False])

print("\n=== RESUMEN POR VARIABLE (primeras 30 por % de nulos) ===")
print(summary.head(30))

# --- Guardar outputs para tu informe ---
outdir = Path("eda_outputs")
outdir.mkdir(exist_ok=True)

desc_num.to_csv(outdir / "descriptivos_numericos.csv", encoding="utf-8", index=True)
summary.to_csv(outdir / "resumen_variables.csv", encoding="utf-8", index=True)

# También útil: lista de categorías por columna (limitado para no explotar)
cat_preview = {}
for col in categoricas:
    vals = df[col].dropna().unique()
    cat_preview[col] = vals[:20]  # primeras 20 categorías
pd.Series(cat_preview).to_json(outdir / "categorias_preview.json", force_ascii=False)

print(f"\nArchivos generados en: {outdir.resolve()}")
print(" - descriptivos_numericos.csv")
print(" - resumen_variables.csv")
print(" - categorias_preview.json")
# ===============================
# (3) VALORES NULOS / DATOS COMPLETOS
# ===============================

# 3.1 Ranking de nulos y % (ya lo tienes como 'summary'); guardamos extra un top 50 por comodidad
summary_top50 = summary.head(50).copy()
summary_top50.to_csv(outdir / "resumen_variables_top50.csv", encoding="utf-8", index=True)

# 3.2 Eliminar columnas 100% nulas (datos completos)
cols_all_null = summary.index[summary["% Nulos"] == 100.0].tolist()
pd.Series(cols_all_null, name="columnas_100pct_nulas").to_csv(outdir / "columnas_100pct_nulas.csv", index=False, encoding="utf-8")

print(f"\nColumnas 100% nulas detectadas ({len(cols_all_null)}):")
print(cols_all_null[:20], "..." if len(cols_all_null) > 20 else "")

df = df.drop(columns=cols_all_null)
print(f"DataFrame tras eliminar columnas 100% nulas: {df.shape[0]} filas x {df.shape[1]} columnas")
df.to_csv(outdir / "df_post_drop_100pct_nulls_preview.csv", index=False, encoding="utf-8")

# Recalcular lista de tipos tras el drop (útil para lo siguiente)
categoricas = df.select_dtypes(include="object").columns.tolist()
numericas   = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
fechas      = df.select_dtypes(include="datetime64[ns]").columns.tolist()


# ===============================
# COHERENCIA TEMPORAL Y VARIABLES DERIVADAS
# ===============================

from datetime import datetime

# 1) Coherencia: Fecha de Ingreso < Fecha de Fin Contacto
flag_cols = []
if {"Fecha de Ingreso", "Fecha de Fin Contacto"}.issubset(df.columns):
    incoh_mask = (df["Fecha de Ingreso"].notna() & df["Fecha de Fin Contacto"].notna() &
                  (df["Fecha de Ingreso"] >= df["Fecha de Fin Contacto"]))
    df["flag_fecha_incoherente"] = incoh_mask
    flag_cols.append("flag_fecha_incoherente")
    print("Registros con incoherencia temporal (Ingreso >= Fin):", int(incoh_mask.sum()))

    # 2) Derivada: Estancia_calc = (Fin - Ingreso).days, evitando negativos
    df["Estancia_calc"] = (df["Fecha de Fin Contacto"] - df["Fecha de Ingreso"]).dt.days
    df.loc[df["Estancia_calc"] < 0, "Estancia_calc"] = None  # si hay negativos, set a NaN

    # 3) Comparación con 'Estancia Días' si existe
    if "Estancia Días" in df.columns:
        # Diferencia absoluta (cuando ambos existen)
        both_ok = df["Estancia_calc"].notna() & df["Estancia Días"].notna()
        df.loc[both_ok, "Estancia_diff"] = (df.loc[both_ok, "Estancia_calc"] - df.loc[both_ok, "Estancia Días"]).abs()
        df["flag_estancia_mismatch"] = df["Estancia_diff"].fillna(0).gt(1)  # tolerancia ±1 día
        flag_cols.append("flag_estancia_mismatch")
        print("Registros con mismatch Estancia_calc vs 'Estancia Días' (>1 día):", int(df["flag_estancia_mismatch"].sum()))
else:
    print("Aviso: no se pudieron verificar coherencias temporales (faltan columnas de fecha).")


# ===============================
# RANGOS PLAUSIBLES (no se corrige, se marca)
# ===============================

# Edad ∈ [0, 115]
if "Edad" in df.columns:
    df["flag_edad_out_of_range"] = ~df["Edad"].between(0, 115, inclusive="both")
    flag_cols.append("flag_edad_out_of_range")
    print("Edades fuera de rango [0,115]:", int(df["flag_edad_out_of_range"].sum()))

# Días UCI ≥ 0
if "Días UCI" in df.columns:
    # Hay columnas con pocos datos; convertimos a numérico seguro para marcar
    dias_uci = pd.to_numeric(df["Días UCI"], errors="coerce")
    df["flag_diasuci_negativo"] = dias_uci.lt(0)
    flag_cols.append("flag_diasuci_negativo")
    print("Registros con Días UCI negativos:", int(df["flag_diasuci_negativo"].sum()))


# ===============================
# OUTLIERS (PRELIMINAR: IQR y z-score) — no se eliminan
# ===============================

import numpy as np

def iqr_flags(series):
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return pd.Series(False, index=series.index)
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return (pd.to_numeric(series, errors="coerce") < lo) | (pd.to_numeric(series, errors="coerce") > hi)

def zscore_flags(series, z=3.0):
    s = pd.to_numeric(series, errors="coerce")
    mu, sd = s.mean(), s.std()
    if pd.isna(sd) or sd == 0:
        return pd.Series(False, index=series.index)
    return ((s - mu).abs() / sd) > z

cols_outliers = [c for c in ["Estancia Días", "Coste APR", "Edad", "Días UCI"] if c in df.columns]
for c in cols_outliers:
    df[f"flag_{c.replace(' ','_').lower()}_outlier_iqr"] = iqr_flags(df[c])
    df[f"flag_{c.replace(' ','_').lower()}_outlier_z3"]  = zscore_flags(df[c], z=3.0)
    flag_cols += [f"flag_{c.replace(' ','_').lower()}_outlier_iqr", f"flag_{c.replace(' ','_').lower()}_outlier_z3"]

# Resumen de cuántos outliers por variable (IQR y z-score)
outlier_counts = {}
for c in cols_outliers:
    outlier_counts[c] = {
        "iqr": int(df[f"flag_{c.replace(' ','_').lower()}_outlier_iqr"].sum()),
        "z3":  int(df[f"flag_{c.replace(' ','_').lower()}_outlier_z3"].sum())
    }
pd.DataFrame(outlier_counts).to_csv(outdir / "outliers_resumen.csv")


# ===============================
# (4) NORMALIZACIÓN / CORRECCIÓN DE CATEGORÍAS (datos optimizados)
# ===============================

# 4.1 Limpieza de texto: strip() universal en object
for c in df.select_dtypes(include="object").columns:
    df[c] = df[c].astype(str).str.strip()

# 4.2 Upper solo en columnas claramente de códigos (evitar nombres propios)
cols_upper = [c for c in df.columns if any(kw in c.lower() for kw in ["diagnóstico", "procedimiento", "servicio", "categoría", "cie", "poa"])]
for c in cols_upper:
    if c in df.columns:
        df[c] = df[c].astype(str).str.upper()

# 4.3 SEXO: mapeo defensivo a {1,2,3,9} según RAE-CMBD (1 Varón, 2 Mujer, 3 Indeterm., 9 No especificado)
if "Sexo" in df.columns:
    # convertir a texto y normalizar variantes comunes
    sexo_map_texto = {"M":"1", "F":"2", "V":"1", "H":"1"}  # añade variantes si aparecieran
    df["Sexo"] = df["Sexo"].astype(str).str.strip().str.upper().replace(sexo_map_texto)
    df["Sexo"] = pd.to_numeric(df["Sexo"], errors="coerce").fillna(9).astype("int64")
    df.loc[~df["Sexo"].isin([1,2,3,9]), "Sexo"] = 9

# 4.4 (Opcional) Conservar versiones categóricas optimizadas para análisis
for c in ["Comunidad Autónoma", "Servicio", "Tipo Alta", "Procedencia", "Categoría"]:
    if c in df.columns:
        df[c] = df[c].astype("category")

# ===============================
# EXPORTS DE CONTROL DE CALIDAD
# ===============================

# 1) Guardar conteos de banderas de calidad (coherencia, rangos, outliers)
qc_cols = [c for c in df.columns if str(c).startswith("flag_")]
qc_counts = df[qc_cols].sum(numeric_only=True).sort_values(ascending=False)
qc_counts.to_csv(outdir / "qc_flags_counts.csv", header=["casos"], encoding="utf-8")

# 2) Vista de ejemplos problemáticos (muestras para el informe)
ejemplos = pd.DataFrame()
for c in qc_cols:
    bad = df.loc[df[c] == True].head(5)  # primeras 5 filas con problema
    if not bad.empty:
        tmp = bad.copy()
        tmp["_flag"] = c
        ejemplos = pd.concat([ejemplos, tmp], axis=0)
if not ejemplos.empty:
    ejemplos.to_csv(outdir / "qc_flags_ejemplos.csv", index=False, encoding="utf-8")

# 3) Guardar dataset con columnas añadidas (preview)
df.to_csv(outdir / "df_preprocesado_con_flags.csv", index=False, encoding="utf-8")

print("\n=== PREPROCESAMIENTO COMPLETADO ===")
print(f"- Columnas 100% nulas eliminadas: {len(cols_all_null)}")
print(f"- Banderas de calidad generadas: {len(qc_cols)}  -> ver 'qc_flags_counts.csv'")
print(f"- Resumen de outliers: 'outliers_resumen.csv'")
print(f"- Dataset con flags: 'df_preprocesado_con_flags.csv'")
