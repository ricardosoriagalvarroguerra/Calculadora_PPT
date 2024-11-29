import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, JsCode
import plotly.express as px

# Función para calcular el total dinámicamente
def calculate_total(row):
    return (
        (row['Cantidad de Funcionarios'] * row['Costo de Pasaje']) +
        (row['Cantidad de Funcionarios'] * row['Días'] * row['Alojamiento']) +
        (row['Cantidad de Funcionarios'] * row['Días'] * row['Per-diem y Otros']) +
        (row['Cantidad de Funcionarios'] * row['Movilidad'])
    )

# Definición de columnas numéricas y de categorías
numeric_columns = [
    'Cantidad de Funcionarios', 'Días', 'Costo de Pasaje',
    'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total'
]
category_columns = ['Costo de Pasaje', 'Alojamiento', 'Per-diem y Otros', 'Movilidad']
all_numeric_columns = numeric_columns.copy()  # Evitar duplicados

# Ruta al archivo Excel
file_path = 'BDD_Ajuste.xlsx'  # Asegúrate de que este archivo está en el mismo directorio o proporciona la ruta completa

# Cargar los datos
try:
    df = pd.read_excel(file_path, sheet_name='Original_VPO')
except FileNotFoundError:
    st.error(f"No se encontró el archivo '{file_path}'. Asegúrate de que está en el directorio correcto.")
    st.stop()
except Exception as e:
    st.error(f"Error al leer el archivo Excel: {e}")
    st.stop()

# Limpiar y convertir las columnas numéricas
for col in all_numeric_columns:
    if col in df.columns:
        df[col] = df[col].astype(str).str.replace(',', '').str.strip()
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    else:
        st.error(f"La columna '{col}' no existe en el archivo Excel.")
        st.stop()

# Calcular la columna 'Total' inicialmente
df['Total'] = df.apply(calculate_total, axis=1)

# Monto total deseado (fijo y no editable)
desired_total = 434707.0

# Definir la paleta de colores
color_mapping = {
    'Costo de Pasaje': '#161a1d',
    'Alojamiento': '#ba181b',
    'Per-diem y Otros': '#d3d3d3',
    'Movilidad': '#660708'
}

# Configuración de la página
st.set_page_config(page_title="Calculadora de Presupuesto", layout="wide")

# Estilo personalizado para la aplicación
st.markdown("""
<style>
    .main {
        background-color: #ffffff;
    }
    .stButton>button {
        color: white;
        background-color: #4CAF50;
    }
    .stNumberInput>div>input {
        background-color: #f0f2f6;
    }
    .stDataFrame div, .stDataFrame th, .stDataFrame td {
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# Selector de vista en la barra lateral
st.sidebar.title("Selector de Vista")
vista = st.sidebar.radio(
    "Elige una vista:",
    ("Resumen Original", "Edición y Ajuste")
)

# Vista Resumen Original
if vista == "Resumen Original":
    st.title("Resumen General")

    # Resumen por país y categorías
    summary_by_country = df.groupby('País')[category_columns + ['Total']].sum().reset_index()

    # Convertir las columnas a numéricas en el resumen
    for col in category_columns + ['Total']:
        if col in summary_by_country.columns:
            summary_by_country[col] = pd.to_numeric(summary_by_country[col], errors='coerce').fillna(0)
        else:
            st.error(f"La columna '{col}' no existe en el resumen por país.")
            st.stop()

    # Mostrar resumen por país en gráficos de dona
    st.subheader("Distribución de Costos por País")

    # Determinar el número de columnas por fila (ejemplo: 3)
    num_cols_per_row = 3
    num_countries = summary_by_country.shape[0]
    rows = (num_countries // num_cols_per_row) + (num_countries % num_cols_per_row > 0)

    for i in range(rows):
        cols = st.columns(num_cols_per_row)
        for j in range(num_cols_per_row):
            country_index = i * num_cols_per_row + j
            if country_index < num_countries:
                country_data = summary_by_country.iloc[country_index]
                country_name = country_data['País']
                values = country_data[category_columns].values
                labels = category_columns

                # Crear gráfico de dona
                fig = px.pie(
                    names=labels,
                    values=values,
                    hole=0.4,
                    title=country_name,
                    color=labels,
                    color_discrete_map=color_mapping,
                    showlegend=False
                )

                # Ajustar tamaño del gráfico
                fig.update_layout(
                    margin=dict(t=40, b=20, l=20, r=20),
                    height=250
                )

                cols[j].plotly_chart(fig, use_container_width=True)

    # Visualizar tabla completa con formato
    st.subheader("Tabla Completa")
    st.dataframe(df.style.format("{:,.2f}"), height=400)

# Vista Edición y Ajuste
elif vista == "Edición y Ajuste":
    st.title("Ajuste de Presupuesto")

    # Mostrar el monto total deseado (fijo)
    st.subheader(f"Monto Total Deseado: {desired_total:,.2f} USD")

    st.write("Edita los valores en la tabla para ajustar el presupuesto y alcanzar el monto total deseado.")

    # Configuración de AgGrid para edición
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True, groupable=True)

    # Configurar la columna 'Total' para que se calcule dinámicamente en el lado del cliente
    gb.configure_column('Total', editable=False, valueGetter=JsCode("""
        function(params) {
            return Number(params.data['Cantidad de Funcionarios']) * Number(params.data['Costo de Pasaje']) +
                   Number(params.data['Cantidad de Funcionarios']) * Number(params.data['Días']) * Number(params.data['Alojamiento']) +
                   Number(params.data['Cantidad de Funcionarios']) * Number(params.data['Días']) * Number(params.data['Per-diem y Otros']) +
                   Number(params.data['Cantidad de Funcionarios']) * Number(params.data['Movilidad']);
        }
    """), type=["numericColumn"], valueFormatter="x.toLocaleString()")

    # Personalizar el aspecto de la tabla
    gb.configure_grid_options(domLayout='normal')
    grid_options = gb.build()

    # Mostrar tabla editable
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        data_return_mode=DataReturnMode.FILTERED,
        update_mode='MODEL_CHANGED',
        fit_columns_on_grid_load=False,
        height=400,
        width='100%',
        enable_enterprise_modules=False,
        allow_unsafe_jscode=True,
        theme='alpine'  # Puedes probar otros temas como 'streamlit', 'balham', etc.
    )

    # Datos editados
    edited_df = pd.DataFrame(grid_response['data'])

    # Verificar si 'País' está presente
    if 'País' not in edited_df.columns:
        st.error("La columna 'País' está ausente en los datos editados.")
        st.stop()

    # Limpiar y convertir las columnas numéricas en 'edited_df'
    for col in all_numeric_columns:
        if col in edited_df.columns:
            # Eliminar comas y espacios en blanco
            edited_df[col] = edited_df[col].astype(str).str.replace(',', '').str.strip()
            # Convertir a numérico
            edited_df[col] = pd.to_numeric(edited_df[col], errors='coerce').fillna(0)
        else:
            st.error(f"La columna '{col}' no existe en los datos editados.")
            st.stop()

    # Recalcular la columna 'Total' con los datos editados
    edited_df['Total'] = edited_df.apply(calculate_total, axis=1)

    # Mostrar el nuevo monto total general y la diferencia
    total_sum = edited_df['Total'].sum()
    difference = desired_total - total_sum

    # Mostrar las métricas de manera destacada
    col1, col2 = st.columns(2)
    col1.metric("Nuevo Monto Total General (USD)", f"{total_sum:,.2f}")
    col2.metric("Diferencia con el Monto Deseado (USD)", f"{difference:,.2f}")

    # Resumen por país y categorías (actualizado)
    summary_by_country_edited = edited_df.groupby('País')[category_columns + ['Total']].sum().reset_index()

    # Convertir las columnas a numéricas en el resumen actualizado
    for col in category_columns + ['Total']:
        if col in summary_by_country_edited.columns:
            summary_by_country_edited[col] = pd.to_numeric(summary_by_country_edited[col], errors='coerce').fillna(0)
        else:
            st.error(f"La columna '{col}' no existe en el resumen por país actualizado.")
            st.stop()

    # Mostrar resumen por país actualizado en gráficos de dona
    st.subheader("Distribución de Costos por País Actualizado")

    # Determinar el número de columnas por fila (ejemplo: 3)
    num_cols_per_row = 3
    num_countries = summary_by_country_edited.shape[0]
    rows = (num_countries // num_cols_per_row) + (num_countries % num_cols_per_row > 0)

    for i in range(rows):
        cols = st.columns(num_cols_per_row)
        for j in range(num_cols_per_row):
            country_index = i * num_cols_per_row + j
            if country_index < num_countries:
                country_data = summary_by_country_edited.iloc[country_index]
                country_name = country_data['País']
                values = country_data[category_columns].values
                labels = category_columns

                # Crear gráfico de dona
                fig = px.pie(
                    names=labels,
                    values=values,
                    hole=0.4,
                    title=country_name,
                    color=labels,
                    color_discrete_map=color_mapping,
                    showlegend=False
                )

                # Ajustar tamaño del gráfico
                fig.update_layout(
                    margin=dict(t=40, b=20, l=20, r=20),
                    height=250
                )

                cols[j].plotly_chart(fig, use_container_width=True)

    # Descargar la tabla modificada
    st.subheader("Descargar Tabla Modificada")
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button(label="Descargar CSV", data=csv, file_name="tabla_modificada.csv", mime="text/csv")
