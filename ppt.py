import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, JsCode

# Función para calcular el total dinámicamente
def calculate_total(row):
    return (
        (row['Cantidad de Funcionarios'] * row['Costo de Pasaje']) +
        (row['Cantidad de Funcionarios'] * row['Días'] * row['Alojamiento']) +
        (row['Cantidad de Funcionarios'] * row['Días'] * row['Per-diem y Otros']) +
        (row['Cantidad de Funcionarios'] * row['Movilidad'])
    )

# Columnas numéricas y de categorías
numeric_columns = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje', 'Alojamiento',
                   'Per-diem y Otros', 'Movilidad', 'Total']
category_columns = ['Costo de Pasaje', 'Alojamiento', 'Per-diem y Otros', 'Movilidad']
all_numeric_columns = numeric_columns + category_columns

# Cargar los datos asegurando los tipos numéricos
file_path = 'BDD_Ajuste.xlsx'  # Asegúrate de que este archivo está en el mismo directorio o proporciona la ruta completa
df = pd.read_excel(file_path, sheet_name='Original_VPO')

# Eliminar espacios en blanco y convertir a numérico
for col in all_numeric_columns:
    df[col] = df[col].astype(str).str.replace(',', '').str.strip()
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# Calcular la columna 'Total' inicialmente
df['Total'] = df.apply(calculate_total, axis=1)

# Monto total deseado (fijo y no editable)
desired_total = 434707.0

# Estilo de la aplicación
st.set_page_config(page_title="Calculadora de Presupuesto", layout="wide")
st.markdown("""
<style>
    .main {
        background-color: #f0f2f6;
    }
    .stButton>button {
        color: white;
        background-color: #4CAF50;
    }
    .stNumberInput>div>input {
        background-color: #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)

# Selector de vista
st.sidebar.title("Selector de Vista")
vista = st.sidebar.radio(
    "Elige una vista:",
    ("Resumen Original", "Edición y Ajuste")
)

if vista == "Resumen Original":
    st.title("Resumen General")

    # Resumen por país y categorías
    summary_by_country = df.groupby('País')[category_columns + ['Total']].sum().reset_index()

    # Convertir las columnas a numéricas en el resumen
    for col in category_columns + ['Total']:
        summary_by_country[col] = pd.to_numeric(summary_by_country[col], errors='coerce').fillna(0)

    # Mostrar resumen por país en una tabla
    st.subheader("Resumen por País")
    st.dataframe(summary_by_country.style.format("{:,.2f}"), height=400)

    # Visualizar tabla completa
    st.subheader("Tabla Completa")
    st.dataframe(df.style.format("{:,.2f}"), height=400)

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

    # Eliminar espacios en blanco y convertir a numérico en 'edited_df'
    for col in all_numeric_columns:
        edited_df[col] = edited_df[col].astype(str).str.replace(',', '').str.strip()
        edited_df[col] = pd.to_numeric(edited_df[col], errors='coerce').fillna(0)

    # Recalcular la columna 'Total' con los datos editados
    edited_df['Total'] = edited_df.apply(calculate_total, axis=1)

    # Mostrar el nuevo monto total general y la diferencia
    total_sum = edited_df['Total'].sum()
    difference = desired_total - total_sum

    col1, col2 = st.columns(2)
    col1.metric("Nuevo Monto Total General (USD)", f"{total_sum:,.2f}")
    col2.metric("Diferencia con el Monto Deseado (USD)", f"{difference:,.2f}")

    # Resumen por país y categorías (actualizado)
    summary_by_country_edited = edited_df.groupby('País')[category_columns + ['Total']].sum().reset_index()

    # Convertir columnas a numéricas en 'summary_by_country_edited'
    for col in category_columns + ['Total']:
        summary_by_country_edited[col] = pd.to_numeric(summary_by_country_edited[col], errors='coerce').fillna(0)

    # Mostrar resumen por país
    st.subheader("Resumen por País Actualizado")
    st.dataframe(summary_by_country_edited.style.format("{:,.2f}"), height=400)

    # Descargar la tabla modificada
    st.subheader("Descargar Tabla Modificada")
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button(label="Descargar CSV", data=csv, file_name="tabla_modificada.csv", mime="text/csv")
