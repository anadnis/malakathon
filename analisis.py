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
