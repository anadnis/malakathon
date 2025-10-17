import pandas as pd
import numpy as np
import oracledb
import openai
import subprocess
import json
import json
from typing import Dict, Any
import warnings
warnings.filterwarnings('ignore')

class AnalizadorSaludMentalIA:
    """
    Sistema de análisis de datos de salud mental con integración de IA.
    Premio Indra - Hackathon
    Versión Oracle Database
    """
    
    def __init__(self, api_key: str, connection=None, db_config: Dict[str, str] = None):
        """
        Inicializa el analizador.
        
        Args:
            api_key: API key de OpenAI
            connection: (Opcional) Conexión de Oracle ya establecida
            db_config: (Opcional) Diccionario con configuración de Oracle DB
                {
                    'user': 'usuario',
                    'password': 'contraseña',
                    'dsn': 'dsn_connection',
                    'config_dir': 'ruta/wallet',
                    'wallet_location': 'ruta/wallet',
                    'wallet_password': 'password_wallet'
                }
        """
        openai.api_key = api_key
        self.db_config = db_config
        self.connection = connection  # Puede ser None o una conexión existente
        self.df = None
        self.datos_empiricos = {}
        self.insights_ia = {}
    
    def conectar_bd(self):
        """Establece conexión con Oracle Database."""
        
        # Si ya hay una conexión, usarla
        if self.connection is not None:
            print("✅ Usando conexión existente")
            return self.connection
        
        # Si no hay configuración, error
        if self.db_config is None:
            raise ValueError("Se requiere db_config o una conexión existente")
        
        print("🔌 Conectando a Oracle Database...")
        
        try:
            self.connection = oracledb.connect(
                user=self.db_config['user'],
                password=self.db_config['password'],
                dsn=self.db_config['dsn'],
                config_dir=self.db_config['config_dir'],
                wallet_location=self.db_config['wallet_location'],
                wallet_password=self.db_config['wallet_password']
            )
            print("✅ Conexión establecida correctamente")
            return self.connection
            
        except Exception as e:
            print(f"❌ Error al conectar con Oracle: {e}")
            raise
    
    def cargar_datos(self, filtro_edad: int = 20, tabla: str = "SALUDMENTAL"):
        """
        Carga y filtra los datos desde Oracle DB.
        
        Args:
            filtro_edad: Edad máxima para filtrar (default: 20)
            tabla: Nombre de la tabla (default: SALUDMENTAL)
        """
        print("📊 Cargando datos desde Oracle Database...")
        
        # Asegurar conexión
        if self.connection is None:
            self.conectar_bd()
        elif not hasattr(self.connection, 'cursor'):
            raise ValueError("La conexión proporcionada no es válida")
        
        # Construir query SQL
        query = f"""
        SELECT 
            EDAD, 
            SEXO, 
            "Categoría"
        FROM {tabla}
        WHERE EDAD < {filtro_edad}
          AND "Categoría" LIKE '%Esquizofrenia, trastornos esquizotípicos y trastornos delirantes%'
          AND SEXO IS NOT NULL
        """
        
        print("🔍 Ejecutando consulta SQL...")
        print(f"   Filtro edad: < {filtro_edad} años")
        print(f"   Filtro categoría: Esquizofrenia")
        
        try:
            # Ejecutar query y cargar en DataFrame
            self.df = pd.read_sql(query, self.connection)
            
            # Crear columna binaria de Esquizofrenia
            self.df['Esquizofrenia'] = 1
            
            print(f"✅ Datos cargados: {len(self.df)} registros")
            print(f"📋 Columnas: {list(self.df.columns)}")
            
            # Mostrar muestra de datos
            if len(self.df) > 0:
                print("\n📄 Primeras filas:")
                print(self.df.head())
            else:
                print("⚠️ No se encontraron registros con los filtros aplicados")
            
            return self.df
            
        except Exception as e:
            print(f"❌ Error al ejecutar query: {e}")
            raise
    
    def calcular_estadisticas(self):
        """
        Calcula estadísticas descriptivas y correlaciones.
        Genera DATOS EMPÍRICOS para el análisis.
        """
        print("\n📈 Calculando estadísticas empíricas...")
        
        self.datos_empiricos = {
            # Estadísticas generales
            'total_pacientes': int(len(self.df)),
            'edad_media': float(self.df['EDAD'].mean()),
            'edad_min': int(self.df['EDAD'].min()),
            'edad_max': int(self.df['EDAD'].max()),
            'edad_std': float(self.df['EDAD'].std()),
            
            # Distribución por sexo
            'distribucion_sexo': self.df['SEXO'].value_counts().to_dict(),
            
            # Prevalencia de esquizofrenia (todos son casos en este dataset filtrado)
            'casos_esquizofrenia': int(len(self.df)),
            'tasa_esquizofrenia': 100.0,  # 100% porque están todos filtrados
            
            # Análisis por grupos de edad
            'distribucion_edad': self._agrupar_por_edad(),
            
            # Análisis por sexo y esquizofrenia
            'esquizofrenia_por_sexo': self._analizar_por_sexo(),
            
            # Correlaciones (si hay más columnas numéricas)
            'correlaciones': self._calcular_correlaciones(),
            
            # Información de la categoría
            'categoria_diagnostico': 'Esquizofrenia, trastornos esquizotípicos y trastornos delirantes'
        }
        
        print("✅ Estadísticas calculadas")
        return self.datos_empiricos
    
    def _agrupar_por_edad(self):
        """Agrupa pacientes por rangos de edad."""
        bins = [0, 10, 15, 20]
        labels = ['0-10 años', '11-15 años', '16-19 años']
        
        self.df['Rango_Edad'] = pd.cut(
            self.df['EDAD'], 
            bins=bins, 
            labels=labels, 
            include_lowest=True
        )
        
        resultado = {}
        for rango in labels:
            datos_rango = self.df[self.df['Rango_Edad'] == rango]
            if len(datos_rango) > 0:
                # Todos son casos de esquizofrenia (filtrados previamente)
                resultado[rango] = {
                    'total': int(len(datos_rango)),
                    'casos_esquizofrenia': int(len(datos_rango)),
                    'tasa': 100.0
                }
        
        return resultado
    
    def _analizar_por_sexo(self):
        """Analiza la relación entre sexo y esquizofrenia."""
        resultado = {}
        
        for sexo in self.df['SEXO'].unique():
            datos_sexo = self.df[self.df['SEXO'] == sexo]
            # Todos son casos de esquizofrenia
            resultado[str(sexo)] = {
                'total': int(len(datos_sexo)),
                'casos_esquizofrenia': int(len(datos_sexo)),
                'tasa': 100.0,
                'edad_media': float(datos_sexo['EDAD'].mean())
            }
        
        return resultado
    
    def _calcular_correlaciones(self):
        """Calcula correlaciones entre variables numéricas."""
        # Seleccionar solo columnas numéricas
        columnas_numericas = self.df.select_dtypes(
            include=[np.number]
        ).columns.tolist()
        
        if len(columnas_numericas) >= 2:
            corr_matrix = self.df[columnas_numericas].corr()
            
            # Extraer correlación edad-esquizofrenia si existe
            if 'EDAD' in columnas_numericas and 'Esquizofrenia' in columnas_numericas:
                return {
                    'edad_esquizofrenia': float(
                        corr_matrix.loc['EDAD', 'Esquizofrenia']
                    )
                }
        
        return {}
    
    def construir_prompt(self):
        """
        Construye un prompt estructurado y contextualizado para la IA.
        Este es el PUNTO CLAVE del reto.
        """
        print("\n🤖 Construyendo prompt para IA...")
        
        prompt = f"""Eres un experto en análisis de datos de salud mental pediátrica y juvenil. 
        Analiza los siguientes datos REALES de pacientes menores de 20 años DIAGNOSTICADOS con esquizofrenia, trastornos esquizotípicos y trastornos delirantes.

        ## DATOS EMPÍRICOS EXTRAÍDOS DE LA BASE DE DATOS ORACLE:

        ### Información General:
        - Diagnóstico: {self.datos_empiricos['categoria_diagnostico']}
        - Total de casos diagnosticados: {self.datos_empiricos['total_pacientes']}
        - Edad promedio: {self.datos_empiricos['edad_media']:.2f} años (σ = {self.datos_empiricos['edad_std']:.2f})
        - Rango de edad: {self.datos_empiricos['edad_min']} a {self.datos_empiricos['edad_max']} años

        ### Distribución por Sexo:
        {self._formatear_distribucion_sexo()}

        ### Distribución por Grupos de Edad:
        {self._formatear_grupos_edad()}

        ### Análisis Detallado por Sexo:
        {self._formatear_analisis_sexo()}

        {self._formatear_correlaciones()}

        ## CONTEXTO IMPORTANTE:
        - Estos son TODOS casos diagnosticados (no población general)
        - La muestra representa menores de 20 años con el diagnóstico confirmado
        - Los datos permiten analizar patrones demográficos en casos confirmados

        ## TAREA DE ANÁLISIS:

        Basándote EXCLUSIVAMENTE en estos datos empíricos, proporciona un análisis profesional que incluya:

        1. **Patrones demográficos**: Identifica tendencias en edad, sexo y distribución
        2. **Factores de riesgo observados**: Basándote en los datos demográficos disponibles
        3. **Análisis comparativo**: Diferencias entre grupos de edad y sexo
        4. **Proyección a 6 meses**: Estimación prudente de nuevos casos esperados en esta población
        5. **Recomendaciones clínicas**: Acciones específicas para el seguimiento de estos pacientes
        6. **Áreas de atención prioritaria**: Grupos demográficos que requieren mayor seguimiento

        IMPORTANTE: 
        - Base tus conclusiones únicamente en los datos proporcionados
        - Reconoce que estos son casos diagnosticados, no prevalencia poblacional
        - Sé específico y cita números cuando sea relevante
        - Las proyecciones deben considerar el contexto clínico
        - Las recomendaciones deben ser accionables para profesionales de salud

        ## FORMATO DE RESPUESTA REQUERIDO:

        Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:

        {{
            "patrones_demograficos": [
                "patrón 1 con datos específicos",
                "patrón 2 con datos específicos",
                "patrón 3 con datos específicos"
            ],
            "factores_asociados": [
                "factor de riesgo 1 observado",
                "factor de riesgo 2 observado"
            ],
            "analisis_comparativo": {{
                "por_edad": "análisis de diferencias etarias",
                "por_sexo": "análisis de diferencias por sexo"
            }},
            "proyeccion_6_meses": {{
                "nuevos_casos_estimados": número_entero,
                "tasa_crecimiento": número_decimal,
                "confianza": "alta|media|baja",
                "justificacion": "explicación basada en datos demográficos"
            }},
            "recomendaciones": [
                "recomendación clínica específica 1",
                "recomendación clínica específica 2",
                "recomendación clínica específica 3"
            ],
            "grupos_prioritarios": [
                "grupo demográfico 1 con justificación y datos",
                "grupo demográfico 2 con justificación y datos"
            ],
            "insights_adicionales": [
                "insight relevante 1 sobre la población estudiada",
                "insight relevante 2 sobre tendencias observadas"
            ]
        }}

        Responde SOLO con el JSON, sin texto adicional antes o después."""

        return prompt
    
    def _formatear_distribucion_sexo(self):
        """Formatea la distribución por sexo para el prompt."""
        texto = ""
        for sexo, cantidad in self.datos_empiricos['distribucion_sexo'].items():
            porcentaje = (cantidad / self.datos_empiricos['total_pacientes']) * 100
            texto += f"- {sexo}: {cantidad} pacientes ({porcentaje:.1f}%)\n"
        return texto
    
    def _formatear_grupos_edad(self):
        """Formatea los grupos de edad para el prompt."""
        texto = ""
        for rango, datos in self.datos_empiricos['distribucion_edad'].items():
            texto += f"- {rango}: {datos['total']} pacientes, "
            texto += f"{datos['casos_esquizofrenia']} casos ({datos['tasa']:.1f}%)\n"
        return texto
    
    def _formatear_analisis_sexo(self):
        """Formatea el análisis por sexo para el prompt."""
        texto = ""
        for sexo, datos in self.datos_empiricos['esquizofrenia_por_sexo'].items():
            texto += f"- {sexo}: {datos['total']} pacientes, "
            texto += f"{datos['casos_esquizofrenia']} casos ({datos['tasa']:.1f}%), "
            texto += f"edad media {datos['edad_media']:.1f} años\n"
        return texto
    
    def _formatear_correlaciones(self):
        """Formatea las correlaciones para el prompt."""
        if self.datos_empiricos['correlaciones']:
            texto = "### Correlaciones Detectadas:\n"
            for clave, valor in self.datos_empiricos['correlaciones'].items():
                texto += f"- {clave.replace('_', ' ').title()}: {valor:.3f}\n"
            return texto
        return ""
    
    def consultar_ia(self, prompt: str, modelo: str = "gpt-4o"):
        """
        Envía el prompt a OpenAI y obtiene la respuesta.
        
        Args:
            prompt: El prompt construido
            modelo: Modelo de OpenAI a usar (default: gpt-4o)
        """
        print(f"\n🚀 Consultando a OpenAI ({modelo})...")
        
        try:
            response = openai.ChatCompletion.create(
                model=modelo,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en análisis de datos de salud mental. "
                                   "Respondes SOLO con JSON válido, sin texto adicional."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Baja temperatura para respuestas más precisas
                max_tokens=2000
            )
            
            respuesta_texto = response['choices'][0]['message']['content']
            print("✅ Respuesta recibida de OpenAI")
            
            return respuesta_texto
            
        except Exception as e:
            print(f"❌ Error al consultar OpenAI: {e}")
            raise
    
    def procesar_respuesta_ia(self, respuesta_texto: str):
        """
        Procesa y valida la respuesta JSON de la IA.
        
        Args:
            respuesta_texto: Respuesta de OpenAI en texto
        """
        print("\n🔍 Procesando respuesta de la IA...")
        
        try:
            # Limpiar la respuesta (por si hay texto antes/después del JSON)
            respuesta_limpia = respuesta_texto.strip()
            
            # Buscar el JSON dentro del texto
            inicio = respuesta_limpia.find('{')
            fin = respuesta_limpia.rfind('}') + 1
            
            if inicio != -1 and fin > inicio:
                json_texto = respuesta_limpia[inicio:fin]
                self.insights_ia = json.loads(json_texto)
            else:
                self.insights_ia = json.loads(respuesta_limpia)
            
            # Validar estructura
            campos_requeridos = [
                'patrones_demograficos',
                'factores_asociados',
                'analisis_comparativo',
                'proyeccion_6_meses',
                'recomendaciones',
                'grupos_prioritarios'
            ]
            
            campos_faltantes = [
                campo for campo in campos_requeridos 
                if campo not in self.insights_ia
            ]
            
            if campos_faltantes:
                print(f"⚠️ Advertencia: Campos faltantes: {campos_faltantes}")
            else:
                print("✅ JSON válido con todos los campos requeridos")
            
            return self.insights_ia
            
        except json.JSONDecodeError as e:
            print(f"❌ Error al parsear JSON: {e}")
            print(f"Respuesta recibida: {respuesta_texto[:500]}...")
            raise
    
    def generar_informe_completo(self):
        """
        Genera un informe completo diferenciando datos empíricos de insights de IA.
        Formato listo para dashboard.
        """
        print("\n📋 Generando informe completo...")
        
        informe = {
            'metadata': {
                'fecha_analisis': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_registros': self.datos_empiricos['total_pacientes'],
                'modelo_ia': 'gpt-4o',
                'fuente_datos': 'Oracle Database'
            },
            
            # DATOS EMPÍRICOS (de la base de datos)
            'datos_empiricos': {
                'tipo': 'DATOS_REALES',
                'fuente': 'Base de datos Oracle - Tabla SALUDMENTAL',
                'estadisticas': self.datos_empiricos,
                'visualizacion': {
                    'color': '#2E86AB',  # Azul para datos reales
                    'icono': 'database'
                }
            },
            
            # INSIGHTS GENERADOS POR IA
            'insights_ia': {
                'tipo': 'GENERADO_POR_IA',
                'fuente': 'Análisis OpenAI GPT-4o',
                'contenido': self.insights_ia,
                'visualizacion': {
                    'color': '#A23B72',  # Morado para IA
                    'icono': 'brain'
                }
            },
            
            # DATOS PARA GRÁFICOS
            'datos_visualizacion': {
                'distribucion_edad': self._preparar_datos_edad(),
                'distribucion_sexo': self._preparar_datos_sexo(),
                'tasas_prevalencia': self._preparar_tasas_prevalencia()
            }
        }
        
        print("✅ Informe generado correctamente")
        return informe
    
    def _preparar_datos_edad(self):
        """Prepara datos de edad para gráficos."""
        datos = []
        for rango, info in self.datos_empiricos['distribucion_edad'].items():
            datos.append({
                'rango': rango,
                'total': info['total'],
                'casos': info['casos_esquizofrenia'],
                'tasa': info['tasa']
            })
        return datos
    
    def _preparar_datos_sexo(self):
        """Prepara datos de sexo para gráficos."""
        datos = []
        for sexo, info in self.datos_empiricos['esquizofrenia_por_sexo'].items():
            datos.append({
                'sexo': sexo,
                'total': info['total'],
                'casos': info['casos_esquizofrenia'],
                'tasa': info['tasa']
            })
        return datos
    
    def _preparar_tasas_prevalencia(self):
        """Prepara datos de tasas de prevalencia."""
        return {
            'actual': self.datos_empiricos['tasa_esquizofrenia'],
            'proyectada': self.insights_ia.get('proyeccion_6_meses', {}).get(
                'tasa_crecimiento', 
                0.0
            )
        }
    
    def guardar_informe(self, nombre_archivo: str = 'informe_completo.json'):
        """Guarda el informe en un archivo JSON."""
        informe = self.generar_informe_completo()
        
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            json.dump(informe, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Informe guardado en: {nombre_archivo}")
    
    def cerrar_conexion(self):
        """Cierra la conexión con Oracle DB."""
        if self.connection:
            self.connection.close()
            print("\n🔌 Conexión a Oracle cerrada")
    
    def ejecutar_analisis_completo(self):
        """
        Ejecuta el pipeline completo de análisis.
        Método principal para usar en la hackathon.
        """
        print("=" * 70)
        print("🏆 ANÁLISIS DE SALUD MENTAL CON IA - PREMIO INDRA")
        print("=" * 70)
        
        try:
            # 1. Cargar datos desde Oracle
            self.cargar_datos(filtro_edad=20)
            
            # 2. Calcular estadísticas
            self.calcular_estadisticas()
            
            # 3. Construir prompt
            prompt = self.construir_prompt()
            
            # 4. Consultar IA
            respuesta = self.consultar_ia(prompt)
            
            # 5. Procesar respuesta
            self.procesar_respuesta_ia(respuesta)
            
            # 6. Generar informe
            informe = self.generar_informe_completo()
            
            # 7. Guardar informe
            self.guardar_informe()
            
            # 8. Cerrar conexión
            self.cerrar_conexion()
            
            print("\n" + "=" * 70)
            print("✅ ANÁLISIS COMPLETADO CON ÉXITO")
            print("=" * 70)
            
            return informe
            
        except Exception as e:
            print(f"\n❌ Error en el análisis: {e}")
            # Cerrar conexión en caso de error
            self.cerrar_conexion()
            raise


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    
    # Configuración de OpenAI
    API_KEY = "sk-proj-x-x"  # ⚠️ CAMBIAR
    
    # ====================================================================
    # OPCIÓN 1: Pasar la configuración y que el script se conecte
    # ====================================================================
    DB_CONFIG = {
        'user': "malackathon",
        'password': "Oci.x",  # ⚠️ CAMBIAR
        'dsn': "x",  # ⚠️ CAMBIAR
        'config_dir': r"C:\Users\x\Wallet_APROBADOSDB",  # ⚠️ CAMBIAR
        'wallet_location': r"C:\Users\x\Wallet_APROBADOSDB",  # ⚠️ CAMBIAR
        'wallet_password': "x"  # ⚠️ CAMBIAR
    }
    
    # Crear analizador con configuración
    analizador = AnalizadorSaludMentalIA(
        api_key=API_KEY,
        db_config=DB_CONFIG
    )
    
    # ====================================================================
    # OPCIÓN 2: Pasar una conexión ya establecida
    # ====================================================================
    # import oracledb
    # 
    # # Crear tu propia conexión
    # connection = oracledb.connect(
    #     user="malackathon",
    #     password="xxx",
    #     dsn="xxx",
    #     config_dir=r"C:\xxx\Wallet_APROBADOSDB",
    #     wallet_location=r"C:\xxx\HACKTHON\Wallet_APROBADOSDB",
    #     wallet_password="xxx"
    # )
    # 
    # # Crear analizador con conexión existente
    # analizador = AnalizadorSaludMentalIA(
    #     api_key=API_KEY,
    #     connection=connection
    # )
    # ====================================================================
    
    # Ejecutar análisis completo
    informe = analizador.ejecutar_analisis_completo()
    
    # Mostrar resumen
    print("\n📊 RESUMEN DE RESULTADOS:")
    print(f"- Pacientes analizados: {informe['metadata']['total_registros']}")
    print(f"- Patrones demográficos: {len(informe['insights_ia']['contenido']['patrones_demograficos'])}")
    print(f"- Factores asociados: {len(informe['insights_ia']['contenido']['factores_asociados'])}")
    print(f"- Recomendaciones: {len(informe['insights_ia']['contenido']['recomendaciones'])}")
    
    print("\n🎯 PATRONES DEMOGRÁFICOS (IA):")
    for i, patron in enumerate(informe['insights_ia']['contenido']['patrones_demograficos'], 1):
        print(f"{i}. {patron}")
    
    print("\n💡 RECOMENDACIONES (IA):")
    for i, rec in enumerate(informe['insights_ia']['contenido']['recomendaciones'], 1):
        print(f"{i}. {rec}")
    
    print("\n📈 PROYECCIÓN 6 MESES:")
    proyeccion = informe['insights_ia']['contenido']['proyeccion_6_meses']
    print(f"- Nuevos casos estimados: {proyeccion['nuevos_casos_estimados']}")
    print(f"- Tasa crecimiento: {proyeccion['tasa_crecimiento']}%")
    print(f"- Confianza: {proyeccion['confianza']}")

    