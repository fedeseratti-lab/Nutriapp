import streamlit as st
import pandas as pd
from datetime import date
import json
from groq import Groq

# 1. CONFIGURACIÓN DE PÁGINA Y DATOS DEL USUARIO (Perfil 90kg, 1.88m, 45 años)
st.set_page_config(page_title="NutriFit AI Cloud", page_icon="🏋️‍♂️", layout="wide")

PESO = 90.0      # kg
ALTURA = 188.0   # cm
EDAD = 45        # años

# 🚨 PEGA AQUÍ EL ID DE TU GOOGLE SHEET (El código largo de tu enlace):
GOOGLE_SHEET_ID = "https://docs.google.com/spreadsheets/d/1iMwrUi9CB8PUbIMC_T_kPw0Gn4xl0Tsou2hcTqFGnnA/edit?usp=sharing"
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
# Esto evita que tengas que escribir la clave en pantalla continuamente
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    st.error("❌ Error: No se encontró la API Key en las configuraciones secretas del servidor.")
    st.stop()

# 4. INTERFAZ GRÁFICA PREMIUM
st.title("🏋️‍♂️ NutriFit AI Cloud")
st.subheader("Tu panel de hipertrofia portable conectado a la nube")

st.sidebar.header("🎯 Tu Perfil Calibrado")
st.sidebar.write(f"**Edad:** {EDAD} años | **Peso:** {PESO} kg | **Altura:** {ALTURA/100} m")
st.sidebar.subheader("Metas Diarias Requeridas:")
st.sidebar.info(f"🔥 **Calorías:** {CALORIAS_OBJETIVO} kcal\n\n"
                f"🍗 **Proteínas:** {PROTEINA_OBJETIVO} g\n\n"
                f"🍞 **Carbohidratos:** {CARBOHIDRATOS_OBJETIVO} g\n\n"
                f"🥑 **Grasas:** {GRASAS_OBJETIVO} g")

# 5. FUNCIÓN PARA ANALIZAR CON LA IA DE GROQ
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

# 6. GESTIÓN DEL ENVIÓ A GOOGLE SHEETS
def guardar_en_google_sheets(cal, prot, carb, gras):
    # Generamos la URL de Google Form o una API de Google requiere credenciales complejas JSON.
    # Para hacerlo 100% simple e inmediato sin configurar credenciales de Google Cloud,
    # el método recomendado por Streamlit es usar st.experimental_connection o gspread.
    # Optamos por indicarte el envío simplificado mediante un Webhook o mostrar el link de carga.
    pass

# NOTA: Para no complicarte con claves complejas de Google Cloud API, la app leerá tu Excel público mediante pandas de forma nativa para los gráficos:
def obtener_historial_google():
    try:
        df = pd.read_csv(CSV_URL)
        return df
    except Exception:
        return pd.DataFrame(columns=["Fecha", "Calorias", "Proteinas", "Carbohidratos", "Grasas"])

# 7. ENTRADA DE DATOS DEL USUARIO
st.header("📝 ¿Qué comiste hoy?")
comidas_usuario = st.text_area(
    "Describe tus platos de forma libre (Desayuno, almuerzo, merienda, cena):",
    value="Desayuno: un vaso de yogur bebible de vainilla con 4 galletas integrales con chips de chocolate.\nAlmuerzo: 2 porciones de tarta de puerro y cebolla y una banana de postre.",
    height=120
)

# Botón para procesar usando un truco simplificado de persistencia
if st.button("🚀 Analizar comidas"):
    with st.spinner("La IA de Groq está procesando tus datos..."):
        macros_estimados = analizar_comidas_con_groq(comidas_usuario, GROQ_API_KEY)
        if macros_estimados:
            st.session_state["macros_cloud"] = macros_estimados
            st.success("✅ ¡Comidas analizadas con éxito!")
            st.info("💡 Consejo: Copia los datos en tu Google Sheet si deseas registrarlos permanentemente.")

# 8. DESPLIEGUE DE RESULTADOS Y DIAGNÓSTICO
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
        st.error(f"🔴 **Falta Proteína:** Estás {PROTEINA_OBJETIVO - m['proteinas']}g abajo de tu meta de hipertrofia. Aumenta la presencia de carnes magras o huevos en tu próxima comida.")
    else:
        st.success("🟢 **Proteína Óptima:** ¡Excelente! Umbral anabólico cubierto para proteger y crear masa muscular.")

# 9. INTEGRACIÓN VISUAL DEL HISTORIAL DESDE GOOGLE SHEETS
st.markdown("---")
st.header("📅 Tu Historial de Progreso en Google Sheets")
df_google = obtener_historial_google()

if not df_google.empty:
    st.dataframe(df_google.tail(7), use_container_width=True)
    st.subheader("Evolución de Ingesta Calórica")
    st.line_chart(df_google.set_index("Fecha")["Calorias"])
else:
    st.info(f"Visualización activa conectada a tu Google Sheet. Para ver tus gráficos aquí, introduce las filas correspondientes en tu documento de Google Drive.")
