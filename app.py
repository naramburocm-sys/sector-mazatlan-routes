import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from shapely.geometry import Point, Polygon

st.set_page_config(page_title="Gestor y Filtro de Territorios - Sector 1-5", layout="wide")

st.title("📍 Rediseño y Filtrado de Rutas - Sector 1-5 (Mazatlán)")
st.markdown("Herramienta integral para delimitar el sector y cruzar tu base de datos de clientes/entregas.")

# 1. Definición de coordenadas del polígono (Sector 1-5)
# Nota: Shapely usa orden (longitud, latitud), por eso invertimos el orden tradicional [lat, lon]
polygon_coords_latlon = [
    [23.1950, -106.4230], # Playa Sur / Extremo Sur
    [23.2050, -106.4080], # Parque Bonfil (Este)
    [23.2350, -106.4150], # Sube por Av. del Mar
    [23.2500, -106.4250], # Intersección Av. Rafael Buelna
    [23.2650, -106.4350], # Conexión hacia Av. Arnoldo Rigodanza
    [23.2750, -106.4200]  # Intersección Av. Santa Rosa (Norte)
]

# Convertir a formato Shapely (Longitud, Latitud)
polygon_coords_shapely = [(lon, lat) for lat, lon in polygon_coords_latlon]
sector_polygon = Polygon(polygon_coords_shapely)

# 2. Panel lateral para carga de datos
st.sidebar.header("📁 Cargar Base de Clientes / Tiendas")
uploaded_file = st.sidebar.file_uploader("Sube tu archivo Excel (.xlsx) o CSV", type=["xlsx", "csv"])

# Crear mapa centrado en Mazatlán
m = folium.Map(location=[23.2494, -106.4111], zoom_start=13, tiles="CartoDB positron")

# Añadir el polígono del Sector 1-5 al mapa
folium.Polygon(
    locations=polygon_coords_latlon,
    color="#FF4B4B",
    weight=3,
    fill=True,
    fill_color="#FF4B4B",
    fill_opacity=0.25,
    popup="<b>Sector 1-5</b><br>Playa Sur ➔ Bonfil ➔ Santa Rosa"
).add_to(m)

# 3. Procesar datos si el usuario sube un archivo
clientes_dentro = pd.DataFrame()

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.sidebar.success(f"¡Archivo cargado con éxito! Total registros: {len(df)}")
        
        # Selectores para que elijas las columnas de latitud y longitud de tu archivo
        st.sidebar.subheader("Configurar Columnas")
        col_lat = st.sidebar.selectbox("Columna de Latitud", df.columns)
        col_lon = st.sidebar.selectbox("Columna de Longitud", df.columns)
        col_name = st.sidebar.selectbox("Columna de Nombre / Tienda", df.columns)
        
        # Filtrar puntos dentro del polígono
        resultados = []
        for index, row in df.iterrows():
            try:
                lat = float(row[col_lat])
                lon = float(row[col_lon])
                punto = Point(lon, lat)
                esta_dentro = sector_polygon.contains(punto)
                
                resultados.append({
                    "Nombre": row[col_name],
                    "Lat": lat,
                    "Lon": lon,
                    "En_Sector_1_5": esta_dentro
                })
                
                # Pintar en el mapa (Verde si está dentro, Gris si está fuera)
                color_pin = "green" if esta_dentro else "gray"
                icon_type = "ok-sign" if esta_dentro else "info-sign"
                
                if esta_dentro:
                    folium.Marker(
                        location=[lat, lon],
                        popup=f"<b>{row[col_name]}</b><br>Sector 1-5",
                        icon=folium.Icon(color=color_pin, icon=icon_type, prefix="glyphicon")
                    ).add_to(m)
                    
            except Exception:
                continue
                
        df_res = pd.DataFrame(resultados)
        clientes_dentro = df_res[df_res["En_Sector_1_5"] == True]
        
    except Exception as e:
        st.sidebar.error(f"Error al procesar el archivo: {e}")

# Mostrar mapa interactivo
st.subheader("Visualización del Territorio y Puntos")
st_folium(m, width="100%", height=550)

# 4. Sección de Resultados y Exportación
if not clientes_dentro.empty:
    st.markdown("---")
    st.subheader(f"📊 Resumen de Rutas: {len(clientes_dentro)} clientes ubicados en el Sector 1-5")
    st.dataframe(clientes_dentro[["Nombre", "Lat", "Lon"]])
    
    # Botón de descarga
    csv_export = clientes_dentro.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Clientes del Sector 1-5 (CSV)",
        data=csv_export,
        file_name="clientes_sector_1_5.csv",
        mime="text/csv",
    )
elif uploaded_file is not None:
    st.info("Sube un archivo con columnas de latitud y longitud válidas para ver el desglose automático de este sector.")
else:
    st.info("💡 **Tip:** Carga un archivo Excel con las coordenadas de tus puntos de entrega para visualizar de inmediato cuáles pertenecen a este polígono.")