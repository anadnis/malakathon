import json
from datetime import datetime
from pathlib import Path

# === CONFIGURACIÓN ===
INPUT_JSON_FILE = "informe_completo.json"   # puedes poner el JSON directamente en una variable si prefieres
OUTPUT_HTML_FILE = "reporte.html"

# === CARGAR EL JSON ===
with open(INPUT_JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# === PLANTILLA HTML ===
html_template = f"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>📊 Informe de Análisis de Salud Mental</title>
<style>
  body {{
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: #f4f6f8;
    color: #333;
    margin: 0;
    padding: 0;
  }}
  header {{
    background-color: #004e92;
    color: white;
    padding: 20px;
    text-align: center;
  }}
  section {{
    background: white;
    margin: 20px auto;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    width: 90%;
    max-width: 1200px;
  }}
  h2 {{
    border-left: 5px solid #004e92;
    padding-left: 10px;
    color: #004e92;
  }}
  .empirico {{
    border-left: 5px solid {data["datos_empiricos"]["visualizacion"]["color"]};
    background-color: #eaf4fa;
  }}
  .ia {{
    border-left: 5px solid {data["insights_ia"]["visualizacion"]["color"]};
    background-color: #fceaf3;
  }}
  pre {{
    background-color: #f6f6f6;
    border-radius: 5px;
    padding: 10px;
    overflow-x: auto;
  }}
  ul {{
    line-height: 1.6;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
  }}
  table, th, td {{
    border: 1px solid #ccc;
  }}
  th, td {{
    padding: 8px;
    text-align: left;
  }}
  .metadata {{
    background-color: #f1f1f1;
    border-radius: 6px;
    padding: 10px;
  }}
</style>
</head>
<body>
<header>
  <h1>Informe de Análisis de Salud Mental 🧠</h1>
  <p><strong>Modelo IA:</strong> {data["metadata"]["modelo_ia"]} |
     <strong>Fecha:</strong> {data["metadata"]["fecha_analisis"]} |
     <strong>Registros:</strong> {data["metadata"]["total_registros"]}</p>
</header>

<section class="empirico">
  <h2>Datos Empíricos ({data["datos_empiricos"]["tipo"]})</h2>
  <p><strong>Fuente:</strong> {data["datos_empiricos"]["fuente"]}</p>
  <h3>Estadísticas Generales</h3>
  <ul>
    <li>Edad media: {round(data["datos_empiricos"]["estadisticas"]["edad_media"],2)}</li>
    <li>Edad mínima: {data["datos_empiricos"]["estadisticas"]["edad_min"]}</li>
    <li>Edad máxima: {data["datos_empiricos"]["estadisticas"]["edad_max"]}</li>
    <li>Total pacientes: {data["datos_empiricos"]["estadisticas"]["total_pacientes"]}</li>
    <li>Tasa de esquizofrenia: {data["datos_empiricos"]["estadisticas"]["tasa_esquizofrenia"]}%</li>
  </ul>

  <h3>Distribución por edad</h3>
  <table>
    <tr><th>Rango</th><th>Total</th><th>Casos</th><th>Tasa (%)</th></tr>
    {''.join(f"<tr><td>{r}</td><td>{v['total']}</td><td>{v['casos_esquizofrenia']}</td><td>{v['tasa']}</td></tr>" for r, v in data["datos_empiricos"]["estadisticas"]["distribucion_edad"].items())}
  </table>

  <h3>Distribución por sexo</h3>
  <table>
    <tr><th>Sexo</th><th>Total</th><th>Tasa (%)</th><th>Edad media</th></tr>
    {''.join(f"<tr><td>{s}</td><td>{v['total']}</td><td>{v['tasa']}</td><td>{round(v['edad_media'],2)}</td></tr>" for s, v in data["datos_empiricos"]["estadisticas"]["esquizofrenia_por_sexo"].items())}
  </table>

  <p><strong>Categoría diagnóstica:</strong> {data["datos_empiricos"]["estadisticas"]["categoria_diagnostico"]}</p>
</section>

<section class="ia">
  <h2>Insights IA ({data["insights_ia"]["tipo"]})</h2>
  <p><strong>Fuente:</strong> {data["insights_ia"]["fuente"]}</p>

  <h3>Patrones demográficos</h3>
  <ul>{"".join(f"<li>{x}</li>" for x in data["insights_ia"]["contenido"]["patrones_demograficos"])}</ul>

  <h3>Factores asociados</h3>
  <ul>{"".join(f"<li>{x}</li>" for x in data["insights_ia"]["contenido"]["factores_asociados"])}</ul>

  <h3>Análisis comparativo</h3>
  <ul>
    <li><strong>Por edad:</strong> {data["insights_ia"]["contenido"]["analisis_comparativo"]["por_edad"]}</li>
    <li><strong>Por sexo:</strong> {data["insights_ia"]["contenido"]["analisis_comparativo"]["por_sexo"]}</li>
  </ul>

  <h3>Proyección a 6 meses</h3>
  <ul>
    <li>Nuevos casos estimados: {data["insights_ia"]["contenido"]["proyeccion_6_meses"]["nuevos_casos_estimados"]}</li>
    <li>Tasa de crecimiento: {data["insights_ia"]["contenido"]["proyeccion_6_meses"]["tasa_crecimiento"]}</li>
    <li>Nivel de confianza: {data["insights_ia"]["contenido"]["proyeccion_6_meses"]["confianza"]}</li>
    <li>Justificación: {data["insights_ia"]["contenido"]["proyeccion_6_meses"]["justificacion"]}</li>
  </ul>

  <h3>Recomendaciones</h3>
  <ul>{"".join(f"<li>{r}</li>" for r in data["insights_ia"]["contenido"]["recomendaciones"])}</ul>

  <h3>Grupos prioritarios</h3>
  <ul>{"".join(f"<li>{g}</li>" for g in data["insights_ia"]["contenido"]["grupos_prioritarios"])}</ul>

  <h3>Insights adicionales</h3>
  <ul>{"".join(f"<li>{i}</li>" for i in data["insights_ia"]["contenido"]["insights_adicionales"])}</ul>
</section>

<section>
  <h2>Datos para visualización</h2>
  <h3>Distribución por edad</h3>
  <table>
    <tr><th>Rango</th><th>Total</th><th>Casos</th><th>Tasa</th></tr>
    {''.join(f"<tr><td>{d['rango']}</td><td>{d['total']}</td><td>{d['casos']}</td><td>{d['tasa']}</td></tr>" for d in data["datos_visualizacion"]["distribucion_edad"])}
  </table>

  <h3>Distribución por sexo</h3>
  <table>
    <tr><th>Sexo</th><th>Total</th><th>Casos</th><th>Tasa</th></tr>
    {''.join(f"<tr><td>{d['sexo']}</td><td>{d['total']}</td><td>{d['casos']}</td><td>{d['tasa']}</td></tr>" for d in data["datos_visualizacion"]["distribucion_sexo"])}
  </table>

  <p><strong>Tasa actual:</strong> {data["datos_visualizacion"]["tasas_prevalencia"]["actual"]}% |
     <strong>Proyectada:</strong> {data["datos_visualizacion"]["tasas_prevalencia"]["proyectada"]}%</p>
</section>

<footer style="text-align:center; color:#888; margin-bottom:20px;">
  <p>Generado automáticamente el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</footer>
</body>
</html>
"""

# === GUARDAR EL HTML ===
Path(OUTPUT_HTML_FILE).write_text(html_template, encoding="utf-8")
print(f"✅ Reporte generado: {OUTPUT_HTML_FILE}")
