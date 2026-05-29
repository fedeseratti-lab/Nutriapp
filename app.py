import streamlit as st
import pandas as pd
from datetime import date
import json
import requests
from groq import Groq

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="NutriFit AI Cloud", page_icon="🏋️‍♂️", layout="wide")

# 🚨 CONFIGURA TUS DOS ENLACES DE GOOGLE AQUÍ:
GOOGLE_SHEET_ID = "1iMwrUi9CB8PUbIMC_T_kPw0Gn4xl0Tsou2hcTqFGnnA"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwdUZVWB7cmjp3JFySv0dJ-cE1_tb1G98RM4J6ZgnfS9E-TwgwQNMiSqWb8cQm9ozLT/exec"

CSV_URL = f"https://google.com{GOOGLE_SHEET_ID}/export?format=csv"

# 2. INICIALIZACIÓN DE VALORES POR DEFECTO EN LA SESIÓN (Evita reescrituras diarias)
if "peso" not in st.session_state:
    st.session_state.peso = 90.0
if "altura" not in st.session_state:
    st.session_state.altura = 188.0
if "edad" not in st.session_state:
    st.session_state.edad = 45

# Cálculos metabólicos base iniciales
if "calorias_meta" not in st.session_state:
    tmb = (10 * st.session_state.peso) + (6.25 * st.session_state.altura) - (5 * st.session_state.edad) + 5
    st.session_state.calorias_meta = int((tmb * 1.45) + 300)
if "proteinas_meta" not in st.session_state:
    st.session_state.proteinas_meta = int(st.session_state.peso * 2.1)
if "grasas_meta" not in st.session_state:
    st.session_state.grasas_meta = int(st.session_state.peso * 1.0)
if "carbos_meta" not in st.session_state:
    st.session_state.carbos_meta = int((st.session_state.calorias_meta - (st.session_state.proteinas_meta * 4) - (st.session_state.grasas_meta * 9)) / 4)

# Variable para controlar la limpieza del cuadro de texto
if "comidas_input" not in st.session_state:
    st.session_state.comidas_input = ""

# 3. LEER LA API KEY DE LOS SECRETOS DE STREAMLIT
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    st.error("❌ Error: No se encontró la API Key en las configuraciones secretas del servidor.")
    st.stop()

# 4. FUNCIONES DE BASE DE DATOS E IA
def analizar_comidas_con_groq(texto_comidas, key):
    client = Groq(api_key=key)
    prompt = f"""
    Eres un nutricionista deportivo experto en hipertrofia. El usuario te proporcionará un texto con lo que comió en el día de forma genérica.
    Tu tarea es estimar de forma realista el total acumulado de calorías, proteínas (g), carbohidratos (g) y grasas (g) de todo el texto.
    Debes devolver ÚNICAMENTE un objeto JSON con las siguientes claves exactas: "calorias", "proteinas", "carbohidratos", "grasas". No agregues texto adicional ni explicaciones.
    Texto del usuario: "{texto_comidas}"
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        texto_respuesta = response.choices[0].message.content
        return json.loads(texto_respuesta)
    except Exception as e:
        st.error(f"Error al conectar con la API de Groq: {e}")
        return None

def guardar_en_google_sheets(macros, horas_sueno):
    payload = {
        "fecha": str(date.today()),
        "calorias": int(macros["calorias"]),
        "proteinas": int(macros["proteinas"]),
        "carbohidratos": int(macros["carbohidratos"]),
        "grasas": int(macros["grasas"]),
        "sueno": float(horas_sueno)
    }
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            return True
    except Exception as e:
        st.error(f"No se pudo guardar automáticamente en Google Sheets: {e}")
    return False

def obtener_historial_google():
    try:
        df = pd.read_csv(f"{CSV_URL}&nocache={date.today()}")
        return df
    except Exception:
        return pd.DataFrame(columns=["Fecha", "Calorias", "Proteinas", "Carbohidratos", "Grasas", "Sueno"])

# 5. BARRA LATERAL: CONFIGURACIÓN ESPORÁDICA DE DATOS Y METAS
st.sidebar.header("⚙️ Configuración del Perfil")
with st.sidebar.expander("Modificar Datos Físicos"):
    st.session_state.edad = st.number_input("Edad (años):", value=st.session_state.edad, step=1)
    st.session_state.peso = st.number_input("Peso (kg):", value=st.session_state.peso, step=0.5)
    st.session_state.altura = st.number_input("Altura (cm):", value=st.session_state.altura, step=1.0)
    
    # Recalcular automáticamente si el usuario cambia sus datos físicos básicos
    if st.button("Recalcular Metas Teóricas"):
        tmb = (10 * st.session_state.peso) + (6.25 * st.session_state.altura) - (5 * st.session_state.edad) + 5
        st.session_state.calorias_meta = int((tmb * 1.45) + 300)
        st.session_state.proteinas_meta = int(st.session_state.peso * 2.1)
        st.session_state.grasas_meta = int(st.session_state.peso * 1.0)
        st.session_state.carbos_meta = int((st.session_state.calorias_meta - (st.session_state.proteinas_meta * 4) - (st.session_state.grasas_meta * 9)) / 4)
        st.rerun()

with st.sidebar.expander("Editar Objetivos a Mano"):
    st.session_state.calorias_meta = st.number_input("Meta Calorías (kcal):", value=st.session_state.calorias_meta, step=50)
    st.session_state.proteinas_meta = st.number_input("Meta Proteínas (g):", value=st.session_state.proteinas_meta, step=5)
    st.session_state.carbos_meta = st.number_input("Meta Carbohidratos (g):", value=st.session_state.carbos_meta, step=5)
    st.session_state.grasas_meta = st.number_input("Meta Grasas (g):", value=st.session_state.grasas_meta, step=5)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Objetivos Activos Hoy:")
st.sidebar.info(f"🔥 **Calorías:** {st.session_state.calorias_meta} kcal\n\n"
                f"🍗 **Proteínas:** {st.session_state.proteinas_meta} g\n\n"
                f"🍞 **Carbohidratos:** {st.session_state.carbos_meta} g\n\n"
                f"🥑 **Grasas:** {st.session_state.grasas_meta} g")

# 6. PANEL CENTRAL DE REGISTRO
st.title("🏋️‍♂️ Panel de Hipertrofia y Bienestar")
st.subheader("Nutrición inteligente y control de descanso en la nube")

col_text, col_sueno = st.columns([3, 1])

with col_text:
    # Vinculamos el text_area al estado de la sesión para poder limpiarlo
    comidas_usuario = st.text_area(
        "Describe tus platos de forma libre (Desayuno, almuerzo, merienda, cena):",
        value=st.session_state.comidas_input,
        placeholder="Ej: Almorcé 2 porciones de tarta de puerro y una banana. Cené pechuga de pollo con arroz blanco.",
        key="comidas_actuales",
        height=120
    )

with col_sueno:
    horas_sueno = st.number_input("💤 Horas de sueño anoche:", min_value=0.0, max_value=24.0, value=8.0, step=0.5)

# Función intermediaria para procesar, guardar y limpiar la pantalla
def procesar_y_limpiar():
    texto = st.session_state.comidas_actuales
    if not texto.strip():
        st.error("⚠️ Por favor, describe alguna comida antes de guardar.")
        return
        
    with st.spinner("La IA de Groq está procesando tus datos y sincronizando con Google Drive..."):
        macros_estimados = analizar_comidas_con_groq(texto, GROQ_API_KEY)
        if macros_estimados:
            st.session_state["macros_cloud"] = macros_estimados
            
            # Guardado en Google Sheets incluyendo el parámetro de sueño
            exito = guardar_en_google_sheets(macros_estimados, horas_sueno)
            if exito:
                st.success("✅ ¡Datos sincronizados con éxito en tu Google Sheet!")
                # Borramos el cuadro de texto cambiando el valor en la sesión
                st.session_state.comidas_input = ""
                st.rerun()
            else:
                st.warning("⚠️ Los macros se calcularon pero hubo un problema al escribir en Google Sheets. Revisa la URL de tu implementación web.")

st.button("🚀 Analizar comidas y guardar", on_click=procesar_y_limpiar)

# 7. DESPLIEGUE DE RESULTADOS DEL DÍA
if "macros_cloud" in st.session_state:
    m = st.session_state["macros_cloud"]
    st.header("📊 Último Balance Nutricional Calculado")
    c1, c2, c3, c4 = st.columns(4)
    
    c1.metric("Calorías Consumidas", f"{m['calorias']} kcal", f"{m['calorias'] - st.session_state.calorias_meta} kcal vs Meta")
    c2.metric("Proteínas", f"{m['proteinas']} g", f"{m['proteinas'] - st.session_state.proteinas_meta:.1f} g vs Meta")
    c3.metric("Carbohidratos", f"{m['carbohidratos']} g", f"{m['carbohidratos'] - st.session_state.carbos_meta:.1f} g vs Meta")
    c4.metric("Grasas", f"{m['grasas']} g", f"{m['grasas'] - st.session_state.grasas_meta:.1f} g vs Meta")
    
    st.subheader("💡 Recomendación de Ajustes")
    if m["proteinas"] < st.session_state.proteinas_meta:
        st.error(f"🔴 **Falta Proteína:** Estás {st.session_state.proteinas_meta - m['proteinas']}g abajo de tu meta. Sube las porciones de alimentos con alta densidad de aminoácidos.")
    else:
        st.success("🟢 **Proteína Óptima:** Umbral de síntesis muscular cubierto.")

# 8. GRÁFICOS ESTADÍSTICOS DESDE GOOGLE SHEETS
st.markdown("---")
st.header("📅 Tu Progreso Histórico")
df_google = obtener_historial_google()

if not df_google.empty and len(df_google) > 0:
    st.write("Últimos días registrados:")
    st.dataframe(df_google.tail(7), use_container_width=True)
    
    df_grafico = df_google.set_index("Fecha")
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("📈 Evolución de Ingesta Calórica")
        st.line_chart(df_grafico["Calorias"])
    with col_g2:
        st.subheader("🍗 Evolución de Consumo de Proteínas")
        st.bar_chart(df_grafico["Proteinas"])
        
    st.subheader("💤 Registro de Descanso (Horas de Sueño)")
    st.line_chart(df_grafico["Sueno"])
else:
    st.info("📊 Tu Google Sheet está conectado. Los gráficos automáticas de tu evolución calórica, proteica y de sueño aparecerán aquí en cuanto guardes tu primer día.")
