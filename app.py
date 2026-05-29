import streamlit as st
import pandas as pd
from datetime import date
import json
import requests
from groq import Groq

# 1. CONFIGURACIÓN DE PÁGINA Y DATOS DEL USUARIO (Perfil 90kg, 1.88m, 45 años)
st.set_page_config(page_title="NutriFit AI Cloud", page_icon="🏋️‍♂️", layout="wide")

PESO = 90.0      # kg
ALTURA = 188.0   # cm
EDAD = 45        # años

# 🚨 CONFIGURA TUS DOS ENLACES DE GOOGLE AQUÍ:
GOOGLE_SHEET_ID = "1iMwrUi9CB8PUbIMC_T_kPw0Gn4xl0Tsou2hcTqFGnnA"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwdUZVWB7cmjp3JFySv0dJ-cE1_tb1G98RM4J6ZgnfS9E-TwgwQNMiSqWb8cQm9ozLT/exec"

CSV_URL = f"https://google.com{GOOGLE_SHEET_ID}/export?format=csv"

# 2. CÁLCULO DE MACRONUTRIENTES OBJETIVO (Mifflin-St. Jeor + Superávit)
tmb = (10 * PESO) + (6.25 * ALTURA) - (5 * EDAD) + 5
get = tmb * 1.45
CALORIAS_OBJETIVO = int(get + 300)  # ~2925 kcal

PROTEINA_OBJETIVO = int(PESO * 2.1)  # ~189g
GRASAS_OBJETIVO = int(PESO * 1.0)    # ~90g
carbohidratos_cal = CALORIAS_OBJETIVO - (PROTEINA_OBJETIVO * 4) - (GRASAS_OBJETIVO * 9)
CARBOHIDRATOS_OBJETIVO = int(carbohidratos_cal / 4)

# 3. LEER LA API KEY DE LOS SECRETOS DE STREAMLIT
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    st.error("❌ Error: No se encontró la API Key en las configuraciones secretas del servidor.")
    st.stop()

# 4. FUNCIÓN PARA ANALIZAR CON LA IA DE GROQ
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

# 5. GESTIÓN AUTOMÁTICA DE ESCRITURA EN GOOGLE SHEETS
def guardar_en_google_sheets(macros):
    payload = {
        "fecha": str(date.today()),
        "calorias": int(macros["calorias"]),
        "proteinas": int(macros["proteinas"]),
        "carbohidratos": int(macros["carbohidratos"]),
        "grasas": int(macros["grasas"])
    }
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            return True
    except Exception as e:
        st.error(f"No se pudo guardar automáticamente en Google Sheets: {e}")
    return False

# 6. LEER HISTORIAL DE GOOGLE SHEETS
def obtener_historial_google():
    try:
        # Forzamos a pandas a descargar la versión más reciente sin usar caché del navegador
        df = pd.read_csv(f"{CSV_URL}&nocache={date.today()}")
        return df
    except Exception:
        return pd.DataFrame(columns=["Fecha", "Calorias", "Proteinas", "Carbohidratos", "Grasas"])

# 7. INTERFAZ GRÁFICA PANEL PRINCIPAL
st.title("🏋️‍♂️ Panel de Hipertrofia Avanzada")
st.subheader("Tu nutrición inteligente en la nube libre de cargas manuales")

st.sidebar.header("🎯 Perfil Calibrado")
st.sidebar.write(f"**Edad:** {EDAD} años | **Peso:** {PESO} kg | **Altura:** {ALTURA/100} m")
st.sidebar.subheader("Metas Diarias:")
st.sidebar.info(f"🔥 **Calorías:** {CALORIAS_OBJETIVO} kcal\n\n"
                f"🍗 **Proteínas:** {PROTEINA_OBJETIVO} g\n\n"
                f"🍞 **Carbohidratos:** {CARBOHIDRATOS_OBJETIVO} g\n\n"
                f"🥑 **Grasas:** {GRASAS_OBJETIVO} g")

st.header("📝 ¿Qué comiste hoy?")
comidas_usuario = st.text_area(
    "Describe tus platos de forma libre:",
    value="Desayuno: un vaso de yogur bebible de vainilla con 4 galletas integrales con chips de chocolate.\nAlmuerzo: 2 porciones de tarta de puerro y cebolla y una banana de postre.",
    height=120
)

if st.button("🚀 Analizar comidas y guardar"):
    with st.spinner("La IA de Groq está procesando tus datos y sincronizando con Google Drive..."):
        macros_estimados = analizar_comidas_con_groq(comidas_usuario, GROQ_API_KEY)
        if macros_estimados:
            st.session_state["macros_cloud"] = macros_estimados
            
            # Guardado automático
            exito = guardar_en_google_sheets(macros_estimados)
            if exito:
                st.success("✅ ¡Comidas analizadas y guardadas automáticamente en tu Google Sheet!")
            else:
                st.warning("⚠️ Los macros se calcularon pero hubo un problema al escribir en Google Sheets.")

# 8. DESPLIEGUE DE RESULTADOS DIARIOS
if "macros_cloud" in st.session_state:
    m = st.session_state["macros_cloud"]
    st.header("📊 Balance Nutricional de Hoy")
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Calorías Consumidas", f"{m['calorias']} kcal", f"{m['calorias'] - CALORIAS_OBJETIVO} kcal vs Meta")
    col2.metric("Proteínas", f"{m['proteinas']} g", f"{m['proteinas'] - PROTEINA_OBJETIVO:.1f} g vs Meta")
    col3.metric("Carbohidratos", f"{m['carbohidratos']} g", f"{m['carbohidratos'] - CARBOHIDRATOS_OBJETIVO:.1f} g vs Meta")
    col4.metric("Grasas", f"{m['grasas']} g", f"{m['grasas'] - GRASAS_OBJETIVO:.1f} g vs Meta")
    
    st.subheader("💡 Recomendación de Ajustes Inmediatos")
    if m["proteinas"] < PROTEINA_OBJETIVO:
        st.error(f"🔴 **Falta Proteína:** Estás {PROTEINA_OBJETIVO - m['proteinas']}g abajo de tu meta. Necesitas más aminoácidos para estimular la hipertrofia a tus 45 años.")
    else:
        st.success("🟢 **Proteína Óptima:** Umbral de síntesis muscular cubierto.")

# 9. INTEGRACIÓN VISUAL DEL HISTORIAL ESTADÍSTICO
st.markdown("---")
st.header("📅 Tu Progreso Histórico")
df_google = obtener_historial_google()

if not df_google.empty and len(df_google) > 0:
    # Mostrar tabla con los últimos 7 días
    st.write("Últimos días registrados:")
    st.dataframe(df_google.tail(7), use_container_width=True)
    
    # Gráficos estadísticos interactivos
    st.subheader("📈 Evolución del Consumo Calórico vs Meta")
    # Línea de consumo real
    df_grafico = df_google.set_index("Fecha")
    st.line_chart(df_grafico["Calorias"])
    
    st.subheader("🍗 Evolución del Consumo de Proteínas")
    st.bar_chart(df_grafico["Proteinas"])
else:
    st.info("📊 Tu Google Sheet está conectado. En cuanto guardes tus primeros días mediante el botón, aquí verás las gráficas automáticas de tu evolución de calorías y proteínas.")
