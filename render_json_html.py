import json
from datetime import datetime
from pathlib import Path

# === CONFIGURACIÓN ===
INPUT_JSON_FILE = "informe_completo.json"
OUTPUT_HTML_FILE = "dashboard_profesional.html"

# === CARGAR EL JSON ===
with open(INPUT_JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# === EXTRAER DATOS ===
metadata = data.get("metadata", {})
empiricos = data.get("datos_empiricos", {}).get("estadisticas", {})
insights = data.get("insights_ia", {}).get("contenido", {})
viz_data = data.get("datos_visualizacion", {})

# === CALCULAR ESTADÍSTICAS ADICIONALES ===
total_pacientes = empiricos.get("total_pacientes", 0)
edad_media = empiricos.get("edad_media", 0)
edad_std = empiricos.get("edad_std", 0)
edad_min = empiricos.get("edad_min", 0)
edad_max = empiricos.get("edad_max", 0)

# Coeficiente de variación
cv = (edad_std / edad_media * 100) if edad_media > 0 else 0

# Distribución por sexo
dist_sexo = empiricos.get("distribucion_sexo", {})
sexo_labels = list(dist_sexo.keys())
sexo_values = list(dist_sexo.values())

# Distribución por edad
dist_edad = viz_data.get("distribucion_edad", [])
edad_rangos = [d.get("rango", "") for d in dist_edad]
edad_totales = [d.get("total", 0) for d in dist_edad]

# Proyección
proyeccion = insights.get("proyeccion_6_meses", {})
casos_estimados = proyeccion.get("nuevos_casos_estimados", 0)
tasa_crecimiento = proyeccion.get("tasa_crecimiento", 0)

# === PLANTILLA HTML PROFESIONAL ===
html_template = f"""
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>🏥 Dashboard Clínico Profesional - Análisis IA</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2"></script>
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}

    :root {{
      --color-primary: #2E86AB;
      --color-secondary: #A23B72;
      --color-accent: #F18F01;
      --color-success: #06A77D;
      --color-warning: #F77F00;
      --color-bg: #F0F4F8;
      --color-card: #FFFFFF;
      --color-text: #2D3748;
      --color-text-light: #718096;
      --shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
      --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.1);
    }}

    body {{
      font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: var(--color-bg);
      color: var(--color-text);
      line-height: 1.6;
      padding-bottom: 3rem;
    }}

    /* HEADER */
    header {{
      background: linear-gradient(135deg, var(--color-primary) 0%, #1a5276 100%);
      color: white;
      padding: 2.5rem 2rem;
      box-shadow: var(--shadow-lg);
      position: sticky;
      top: 0;
      z-index: 100;
    }}

    .header-content {{
      max-width: 1400px;
      margin: 0 auto;
    }}

    header h1 {{
      font-size: 2.2rem;
      font-weight: 700;
      margin-bottom: 0.5rem;
      display: flex;
      align-items: center;
      gap: 1rem;
    }}

    .header-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 2rem;
      margin-top: 1rem;
      font-size: 0.95rem;
      opacity: 0.95;
    }}

    .header-meta span {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}

    /* CONTAINER */
    .container {{
      max-width: 1400px;
      margin: 2rem auto;
      padding: 0 2rem;
    }}

    /* GRID LAYOUT */
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 1.5rem;
      margin-bottom: 2rem;
    }}

    .grid-2 {{
      grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
    }}

    /* CARDS */
    .card {{
      background: var(--color-card);
      border-radius: 16px;
      padding: 1.75rem;
      box-shadow: var(--shadow);
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}

    .card:hover {{
      transform: translateY(-4px);
      box-shadow: var(--shadow-lg);
    }}

    .card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.5rem;
      padding-bottom: 1rem;
      border-bottom: 2px solid #E2E8F0;
    }}

    .card-title {{
      font-size: 1.3rem;
      font-weight: 700;
      color: var(--color-primary);
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }}

    .card-icon {{
      width: 40px;
      height: 40px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.4rem;
    }}

    .icon-empirico {{
      background: linear-gradient(135deg, #2E86AB 0%, #45a3c9 100%);
      color: white;
    }}

    .icon-ia {{
      background: linear-gradient(135deg, #A23B72 0%, #c94d8a 100%);
      color: white;
    }}

    .icon-chart {{
      background: linear-gradient(135deg, #F18F01 0%, #ffa726 100%);
      color: white;
    }}

    /* STATS CARDS */
    .stat-card {{
      text-align: center;
      padding: 1.5rem;
    }}

    .stat-value {{
      font-size: 2.5rem;
      font-weight: 800;
      color: var(--color-primary);
      margin-bottom: 0.5rem;
    }}

    .stat-label {{
      font-size: 0.9rem;
      color: var(--color-text-light);
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}

    .stat-sublabel {{
      font-size: 0.85rem;
      color: var(--color-text-light);
      margin-top: 0.25rem;
    }}

    /* BADGES */
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.4rem 0.9rem;
      border-radius: 20px;
      font-size: 0.85rem;
      font-weight: 600;
    }}

    .badge-primary {{
      background: rgba(46, 134, 171, 0.1);
      color: var(--color-primary);
    }}

    .badge-secondary {{
      background: rgba(162, 59, 114, 0.1);
      color: var(--color-secondary);
    }}

    .badge-success {{
      background: rgba(6, 167, 125, 0.1);
      color: var(--color-success);
    }}

    .badge-warning {{
      background: rgba(247, 127, 0, 0.1);
      color: var(--color-warning);
    }}

    /* LISTS */
    .insight-list {{
      list-style: none;
      padding: 0;
    }}

    .insight-list li {{
      padding: 1rem;
      margin-bottom: 0.75rem;
      background: #F7FAFC;
      border-radius: 10px;
      border-left: 4px solid var(--color-primary);
      transition: all 0.2s ease;
    }}

    .insight-list li:hover {{
      background: #EDF2F7;
      transform: translateX(4px);
    }}

    .insight-list.ia li {{
      border-left-color: var(--color-secondary);
    }}

    /* TABLES */
    table {{
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      margin-top: 1rem;
    }}

    thead {{
      background: linear-gradient(135deg, var(--color-primary) 0%, #1a5276 100%);
      color: white;
    }}

    th {{
      padding: 1rem;
      text-align: left;
      font-weight: 600;
      font-size: 0.9rem;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}

    th:first-child {{
      border-top-left-radius: 10px;
    }}

    th:last-child {{
      border-top-right-radius: 10px;
    }}

    td {{
      padding: 1rem;
      border-bottom: 1px solid #E2E8F0;
    }}

    tbody tr:hover {{
      background: #F7FAFC;
    }}

    tbody tr:last-child td {{
      border-bottom: none;
    }}

    /* CHARTS */
    .chart-container {{
      position: relative;
      height: 350px;
      margin-top: 1.5rem;
    }}

    .chart-small {{
      height: 280px;
    }}

    /* PROYECCIÓN CARD */
    .proyeccion-card {{
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 2rem;
      border-radius: 16px;
      box-shadow: var(--shadow-lg);
    }}

    .proyeccion-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 1.5rem;
      margin-top: 1.5rem;
    }}

    .proyeccion-item {{
      text-align: center;
      padding: 1rem;
      background: rgba(255, 255, 255, 0.15);
      border-radius: 12px;
      backdrop-filter: blur(10px);
    }}

    .proyeccion-value {{
      font-size: 2rem;
      font-weight: 800;
      margin-bottom: 0.5rem;
    }}

    .proyeccion-label {{
      font-size: 0.9rem;
      opacity: 0.9;
    }}

    /* RESPONSIVE */
    @media (max-width: 768px) {{
      .container {{
        padding: 0 1rem;
      }}

      .grid, .grid-2 {{
        grid-template-columns: 1fr;
      }}

      header h1 {{
        font-size: 1.5rem;
      }}

      .stat-value {{
        font-size: 2rem;
      }}
    }}

    /* ANIMATIONS */
    @keyframes fadeIn {{
      from {{
        opacity: 0;
        transform: translateY(20px);
      }}
      to {{
        opacity: 1;
        transform: translateY(0);
      }}
    }}

    .card {{
      animation: fadeIn 0.5s ease-out;
    }}

    /* SCROLLBAR */
    ::-webkit-scrollbar {{
      width: 10px;
      height: 10px;
    }}

    ::-webkit-scrollbar-track {{
      background: #E2E8F0;
    }}

    ::-webkit-scrollbar-thumb {{
      background: var(--color-primary);
      border-radius: 5px;
    }}

    ::-webkit-scrollbar-thumb:hover {{
      background: #1a5276;
    }}
  </style>
</head>
<body>

  <!-- HEADER -->
  <header>
    <div class="header-content">
      <h1>
        🏥 Dashboard Clínico de Análisis con IA
      </h1>
      <div class="header-meta">
        <span>📅 <strong>Fecha:</strong> {metadata.get('fecha_analisis', 'N/A')}</span>
        <span>👥 <strong>Pacientes:</strong> {metadata.get('total_registros', 0)}</span>
        <span>🤖 <strong>Modelo:</strong> {metadata.get('modelo_ia', 'N/A')}</span>
        <span>💾 <strong>Fuente:</strong> {metadata.get('fuente_datos', 'Oracle Database')}</span>
      </div>
    </div>
  </header>

  <div class="container">

    <!-- KPIs PRINCIPALES -->
    <h2 style="margin: 2rem 0 1rem; font-size: 1.8rem; color: var(--color-primary);">
      📊 Indicadores Clave
    </h2>
    <div class="grid">
      <div class="card stat-card">
        <div class="stat-value">{total_pacientes}</div>
        <div class="stat-label">Pacientes Total</div>
        <div class="stat-sublabel">Casos diagnosticados</div>
      </div>

      <div class="card stat-card">
        <div class="stat-value">{edad_media:.1f}</div>
        <div class="stat-label">Edad Media</div>
        <div class="stat-sublabel">σ = {edad_std:.2f} años</div>
      </div>

      <div class="card stat-card">
        <div class="stat-value">{edad_min} - {edad_max}</div>
        <div class="stat-label">Rango Edad</div>
        <div class="stat-sublabel">CV = {cv:.1f}%</div>
      </div>

      <div class="card stat-card">
        <div class="stat-value">{empiricos.get('tasa_esquizofrenia', 0):.0f}%</div>
        <div class="stat-label">Tasa Diagnóstico</div>
        <div class="stat-sublabel">Prevalencia en muestra</div>
      </div>
    </div>

    <!-- DATOS EMPÍRICOS -->
    <div class="card">
      <div class="card-header">
        <div class="card-title">
          <div class="card-icon icon-empirico">📊</div>
          Datos Empíricos - Base de Datos Oracle
        </div>
        <span class="badge badge-primary">DATOS REALES</span>
      </div>

      <div class="grid-2" style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
        <div>
          <h3 style="margin-bottom: 1rem; color: var(--color-primary);">📈 Estadísticas Descriptivas</h3>
          <table>
            <thead>
              <tr>
                <th>Métrica</th>
                <th>Valor</th>
              </tr>
            </thead>
            <tbody>
              <tr><td>Media (μ)</td><td><strong>{edad_media:.2f} años</strong></td></tr>
              <tr><td>Desviación Estándar (σ)</td><td><strong>{edad_std:.2f} años</strong></td></tr>
              <tr><td>Mínimo</td><td><strong>{edad_min} años</strong></td></tr>
              <tr><td>Máximo</td><td><strong>{edad_max} años</strong></td></tr>
              <tr><td>Coef. Variación (CV)</td><td><strong>{cv:.2f}%</strong></td></tr>
            </tbody>
          </table>
        </div>

        <div>
          <h3 style="margin-bottom: 1rem; color: var(--color-primary);">👥 Distribución por Sexo</h3>
          <table>
            <thead>
              <tr>
                <th>Sexo</th>
                <th>N</th>
                <th>%</th>
                <th>Edad Media</th>
              </tr>
            </thead>
            <tbody>
              {''.join(f'''
              <tr>
                <td><strong>Sexo {sexo}</strong></td>
                <td>{datos['total']}</td>
                <td>{(datos['total']/total_pacientes*100):.1f}%</td>
                <td>{datos['edad_media']:.1f} años</td>
              </tr>
              ''' for sexo, datos in empiricos.get('esquizofrenia_por_sexo', {}).items())}
            </tbody>
          </table>
        </div>
      </div>

      <div style="margin-top: 2rem;">
        <h3 style="margin-bottom: 1rem; color: var(--color-primary);">📊 Distribución por Grupos de Edad</h3>
        <table>
          <thead>
            <tr>
              <th>Rango Etario</th>
              <th>N Pacientes</th>
              <th>% del Total</th>
              <th>Casos Esquizofrenia</th>
            </tr>
          </thead>
          <tbody>
            {''.join(f'''
            <tr>
              <td><strong>{rango}</strong></td>
              <td>{datos['total']}</td>
              <td>{(datos['total']/total_pacientes*100):.1f}%</td>
              <td>{datos['casos_esquizofrenia']}</td>
            </tr>
            ''' for rango, datos in empiricos.get('distribucion_edad', {}).items())}
          </tbody>
        </table>
      </div>
    </div>

    <!-- GRÁFICAS -->
    <h2 style="margin: 2rem 0 1rem; font-size: 1.8rem; color: var(--color-primary);">
      📈 Visualizaciones Interactivas
    </h2>
    <div class="grid grid-2">
      <div class="card">
        <div class="card-header">
          <div class="card-title">
            <div class="card-icon icon-chart">📊</div>
            Distribución por Grupos de Edad
          </div>
        </div>
        <div class="chart-container">
          <canvas id="chartEdad"></canvas>
        </div>
      </div>

      

      <div class="card">
        <div class="card-header">
          <div class="card-title">
            <div class="card-icon icon-chart">📉</div>
            Distribución por edad Media 
          </div>
        </div>
        <div class="chart-container chart-small">
          <canvas id="chartEdadMedia"></canvas>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <div class="card-title">
            <div class="card-icon icon-chart">📊</div>
            Concentración de Casos
          </div>
        </div>
        <div class="chart-container chart-small">
          <canvas id="chartConcentracion"></canvas>
        </div>
      </div>
    </div>

    <!-- PROYECCIÓN IA -->
    <div class="proyeccion-card">
      <h2 style="font-size: 1.6rem; margin-bottom: 0.5rem;">🔮 Proyección a 6 Meses (IA)</h2>
      <p style="opacity: 0.9; font-size: 0.95rem;">
        Estimación basada en análisis predictivo con {metadata.get('modelo_ia', 'GPT-4o')}
      </p>
      <div class="proyeccion-grid">
        <div class="proyeccion-item">
          <div class="proyeccion-value">{casos_estimados}</div>
          <div class="proyeccion-label">Nuevos Casos</div>
        </div>
        <div class="proyeccion-item">
          <div class="proyeccion-value">{tasa_crecimiento:.2f}%</div>
          <div class="proyeccion-label">Tasa Crecimiento</div>
        </div>
        <div class="proyeccion-item">
          <div class="proyeccion-value">{proyeccion.get('confianza', 'N/A').upper()}</div>
          <div class="proyeccion-label">Confianza</div>
        </div>
        <div class="proyeccion-item">
          <div class="proyeccion-value">{total_pacientes + casos_estimados}</div>
          <div class="proyeccion-label">Total Proyectado</div>
        </div>
      </div>
      <p style="margin-top: 1.5rem; font-size: 0.9rem; opacity: 0.85; font-style: italic;">
        📝 {proyeccion.get('justificacion', 'Sin justificación disponible')}
      </p>
    </div>

    <!-- INSIGHTS IA -->
    <div class="card">
      <div class="card-header">
        <div class="card-title">
          <div class="card-icon icon-ia">🧠</div>
          Insights Generados por Inteligencia Artificial
        </div>
        <span class="badge badge-secondary">GENERADO POR IA</span>
      </div>

      <div class="grid-2" style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
        <div>
          <h3 style="margin-bottom: 1rem; color: var(--color-secondary);">🎯 Patrones Demográficos</h3>
          <ul class="insight-list ia">
            {''.join(f'<li>{patron}</li>' for patron in insights.get('patrones_demograficos', []))}
          </ul>
        </div>

        <div>
          <h3 style="margin-bottom: 1rem; color: var(--color-secondary);">⚠️ Factores Asociados</h3>
          <ul class="insight-list ia">
            {''.join(f'<li>{factor}</li>' for factor in insights.get('factores_asociados', []))}
          </ul>
        </div>
      </div>

      <div style="margin-top: 2rem;">
        <h3 style="margin-bottom: 1rem; color: var(--color-secondary);">🔍 Análisis Comparativo</h3>
        <div style="background: #FFF5F7; padding: 1.5rem; border-radius: 12px; border-left: 4px solid var(--color-secondary);">
          <p style="margin-bottom: 1rem;">
            <strong>Por Edad:</strong> {insights.get('analisis_comparativo', {}).get('por_edad', 'N/A')}
          </p>
          <p>
            <strong>Por Sexo:</strong> {insights.get('analisis_comparativo', {}).get('por_sexo', 'N/A')}
          </p>
        </div>
      </div>

      <div style="margin-top: 2rem;">
        <h3 style="margin-bottom: 1rem; color: var(--color-secondary);">💡 Recomendaciones Clínicas</h3>
        <ul class="insight-list ia">
          {''.join(f'<li><strong>R{i+1}:</strong> {rec}</li>' for i, rec in enumerate(insights.get('recomendaciones', [])))}
        </ul>
      </div>

      <div style="margin-top: 2rem;">
        <h3 style="margin-bottom: 1rem; color: var(--color-secondary);">🎯 Grupos Prioritarios</h3>
        <ul class="insight-list ia">
          {''.join(f'<li>{grupo}</li>' for grupo in insights.get('grupos_prioritarios', []))}
        </ul>
      </div>

      <div style="margin-top: 2rem;">
        <h3 style="margin-bottom: 1rem; color: var(--color-secondary);">✨ Insights Adicionales</h3>
        <ul class="insight-list ia">
          {''.join(f'<li>{insight}</li>' for insight in insights.get('insights_adicionales', []))}
        </ul>
      </div>
    </div>

  </div>

  <!-- SCRIPTS -->
  <script>
    // Configuración global de Chart.js
    Chart.defaults.font.family = "'Inter', 'Segoe UI', sans-serif";
    Chart.defaults.color = '#2D3748';
    Chart.defaults.plugins.legend.display = true;
    Chart.defaults.plugins.legend.position = 'bottom';

    // Datos
    const edadRangos = {json.dumps(edad_rangos)};
    const edadTotales = {json.dumps(edad_totales)};
    const sexoLabels = {json.dumps(['Sexo ' + str(s) for s in sexo_labels])};
    const sexoValues = {json.dumps(sexo_values)};
    
    // Preparar datos para edad media por sexo
    const edadMediaData = {json.dumps([
      {'sexo': 'Sexo ' + str(s), 'edad': datos['edad_media']} 
      for s, datos in empiricos.get('esquizofrenia_por_sexo', {}).items()
    ])};

    // 1. GRÁFICA DE BARRAS - Distribución por Edad
    const ctxEdad = document.getElementById('chartEdad').getContext('2d');
    new Chart(ctxEdad, {{
      type: 'bar',
      data: {{
        labels: edadRangos,
        datasets: [{{
          label: 'Número de Pacientes',
          data: edadTotales,
          backgroundColor: [
            'rgba(46, 134, 171, 0.8)',
            'rgba(162, 59, 114, 0.8)',
            'rgba(241, 143, 1, 0.8)'
          ],
          borderColor: [
            'rgba(46, 134, 171, 1)',
            'rgba(162, 59, 114, 1)',
            'rgba(241, 143, 1, 1)'
          ],
          borderWidth: 2,
          borderRadius: 8
        }}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
          legend: {{
            display: false
          }},
          tooltip: {{
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            padding: 12,
            titleFont: {{ size: 14, weight: 'bold' }},
            bodyFont: {{ size: 13 }},
            callbacks: {{
              label: function(context) {{
                const total = {total_pacientes};
                const value = context.parsed;
                const percent = ((value / total) * 100).toFixed(1);
                return `${{context.label}}: ${{value}} pacientes (${{percent}}%)`;
              }}
            }}
          }}
        }},
        cutout: '65%'
      }}
    }});

    // 3. GRÁFICA DE BARRAS HORIZONTALES - Edad Media por Sexo
    const ctxEdadMedia = document.getElementById('chartEdadMedia').getContext('2d');
    new Chart(ctxEdadMedia, {{
      type: 'bar',
      data: {{
        labels: edadMediaData.map(d => d.sexo),
        datasets: [{{
          label: 'Edad Media (años)',
          data: edadMediaData.map(d => d.edad),
          backgroundColor: [
            'rgba(162, 59, 114, 0.8)',
            'rgba(46, 134, 171, 0.8)'
          ],
          borderColor: [
            'rgba(162, 59, 114, 1)',
            'rgba(46, 134, 171, 1)'
          ],
          borderWidth: 2,
          borderRadius: 8
        }}]
      }},
      options: {{
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
          legend: {{
            display: false
          }},
          tooltip: {{
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            padding: 12,
            callbacks: {{
              label: function(context) {{
                return `Edad media: ${{context.parsed.x.toFixed(2)}} años`;
              }}
            }}
          }}
        }},
        scales: {{
          x: {{
            beginAtZero: false,
            min: 14,
            max: 19,
            ticks: {{
              font: {{ size: 12 }}
            }},
            grid: {{
              color: 'rgba(0, 0, 0, 0.05)'
            }}
          }},
          y: {{
            ticks: {{
              font: {{ size: 13, weight: '500' }}
            }},
            grid: {{
              display: false
            }}
          }}
        }}
      }}
    }});

    // 4. GRÁFICA DE LÍNEA - Concentración de Casos
    const ctxConcentracion = document.getElementById('chartConcentracion').getContext('2d');
    const porcentajes = edadTotales.map(val => ((val / {total_pacientes}) * 100).toFixed(1));
    
    new Chart(ctxConcentracion, {{
      type: 'line',
      data: {{
        labels: edadRangos,
        datasets: [{{
          label: 'Porcentaje de Casos (%)',
          data: porcentajes,
          borderColor: 'rgba(241, 143, 1, 1)',
          backgroundColor: 'rgba(241, 143, 1, 0.1)',
          borderWidth: 3,
          fill: true,
          tension: 0.4,
          pointBackgroundColor: 'rgba(241, 143, 1, 1)',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 6,
          pointHoverRadius: 8
        }}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
          legend: {{
            display: false
          }},
          tooltip: {{
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            padding: 12,
            callbacks: {{
              label: function(context) {{
                return `${{context.parsed.y}}% de los casos`;
              }}
            }}
          }}
        }},
        scales: {{
          y: {{
            beginAtZero: true,
            max: 100,
            ticks: {{
              callback: function(value) {{
                return value + '%';
              }},
              font: {{ size: 12 }}
            }},
            grid: {{
              color: 'rgba(0, 0, 0, 0.05)'
            }}
          }},
          x: {{
            ticks: {{
              font: {{ size: 12, weight: '500' }}
            }},
            grid: {{
              display: false
            }}
          }}
        }}
      }}
    }});

    // Animaciones de entrada
    const observer = new IntersectionObserver((entries) => {{
      entries.forEach(entry => {{
        if (entry.isIntersecting) {{
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateY(0)';
        }}
      }});
    }}, {{ threshold: 0.1 }});

    document.querySelectorAll('.card').forEach(card => {{
      card.style.opacity = '0';
      card.style.transform = 'translateY(20px)';
      card.style.transition = 'all 0.5s ease-out';
      observer.observe(card);
    }});

    // Mensaje en consola
    console.log('%c📊 Dashboard Clínico Profesional', 'font-size: 20px; color: #2E86AB; font-weight: bold;');
    console.log('%c🤖 Análisis generado con IA: {metadata.get("modelo_ia", "GPT-4o")}', 'font-size: 14px; color: #A23B72;');
    console.log('%c📅 Fecha: {metadata.get("fecha_analisis", "N/A")}', 'font-size: 12px; color: #718096;');
    console.log('%c👥 Total pacientes analizados: {total_pacientes}', 'font-size: 12px; color: #718096;');
  </script>

  <!-- FOOTER -->
  <footer style="text-align: center; padding: 2rem; color: var(--color-text-light); margin-top: 3rem;">
    <p style="font-size: 0.9rem;">
      ⚕️ <strong>Dashboard Clínico Profesional</strong> | 
      Generado automáticamente el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </p>
    <p style="font-size: 0.85rem; margin-top: 0.5rem; opacity: 0.8;">
      🏆 Premio Indra al uso y la integración de la Inteligencia Artificial
    </p>
    <p style="font-size: 0.8rem; margin-top: 1rem; opacity: 0.7;">
      Los datos empíricos provienen de {metadata.get('fuente_datos', 'Oracle Database')} | 
      Los insights son generados por {metadata.get('modelo_ia', 'GPT-4o')}
    </p>
  </footer>

</body>
</html>
"""

# === GUARDAR EL HTML ===
Path(OUTPUT_HTML_FILE).write_text(html_template, encoding="utf-8")
print(f"✅ Dashboard profesional generado: {OUTPUT_HTML_FILE}")
print(f"📊 Estadísticas incluidas:")
print(f"   - Total pacientes: {total_pacientes}")
print(f"   - Edad media: {edad_media:.2f} ± {edad_std:.2f} años")
print(f"   - Coeficiente de variación: {cv:.2f}%")
print(f"   - 4 gráficas interactivas generadas")
print(f"   - Proyección IA a 6 meses incluida")
print(f"\n🎨 Características del dashboard:")
print(f"   ✓ Diseño profesional y moderno")
print(f"   ✓ Gráficas interactivas con Chart.js")
print(f"   ✓ Diferenciación clara datos empíricos vs IA")
print(f"   ✓ KPIs destacados")
print(f"   ✓ Responsive design")
print(f"   ✓ Animaciones suaves")
print(f"\n🚀 Abre el archivo '{OUTPUT_HTML_FILE}' en tu navegador")
