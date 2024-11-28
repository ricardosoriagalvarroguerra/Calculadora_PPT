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

# Cargar los datos
file_path = 'BDD_Ajuste.xlsx'  # Asegúrate de que este archivo está en el mismo directorio o proporciona la ruta completa
df = pd.read_excel(file_path, sheet_name='Original_VPO')

# Asegurarse de que las columnas numéricas estén en el tipo correcto
numeric_columns = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje', 'Alojamiento',
                   'Per-diem y Otros', 'Movilidad']
for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# Calcular la columna 'Total' inicialmente
df['Total'] = df.apply(calculate_total, axis=1)

# Selector de vista
st.sidebar.title("Selector de Vista")
vista = st.sidebar.radio(
    "Elige una vista:",
    ("Vista Resumen Original", "Vista Editable con Actualización")
)

if vista == "Vista Resumen Original":
    st.title("Resumen General con Tablas Expandibles")

    # Resumen por país y categorías
    category_columns = ['Costo de Pasaje', 'Alojamiento', 'Per-diem y Otros', 'Movilidad']
    summary_by_country = df.groupby('País')[category_columns + ['Total']].sum()

    # Mostrar resumen por país con tablas expandibles
    st.write("**Resumen General por País:**")
    for country, data in summary_by_country.iterrows():
        total = data['Total']
        with st.expander(f"{country} - Total: {total:,.2f}"):
            st.write("**Detalles por Categoría**")
            for category in category_columns:
                st.write(f"- **{category}:** {data[category]:,.2f}")

    # Visualizar tabla completa
    st.write("### Tabla Completa:")
    st.dataframe(df)

elif vista == "Vista Editable con Actualización":
    st.title("DPP 2025")

    # Establecer el monto total deseado por defecto en 434,707
    desired_total = st.number_input("Ingresa el monto total deseado:", value=434707.0, step=0.01)

    # Configuración de AgGrid para edición
    st.write("### Tabla Editable")
    st.write("Edita los valores y ajusta los totales hasta alcanzar el monto deseado.")

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True)

    # Configurar la columna 'Total' para que se calcule dinámicamente en el lado del cliente
    gb.configure_column('Total', editable=False, valueGetter=JsCode("""
        function(params) {
            return Number(params.data['Cantidad de Funcionarios']) * Number(params.data['Costo de Pasaje']) +
                   Number(params.data['Cantidad de Funcionarios']) * Number(params.data['Días']) * Number(params.data['Alojamiento']) +
                   Number(params.data['Cantidad de Funcionarios']) * Number(params.data['Días']) * Number(params.data['Per-diem y Otros']) +
                   Number(params.data['Cantidad de Funcionarios']) * Number(params.data['Movilidad']);
        }
    """), type=["numericColumn"], valueFormatter="x.toLocaleString()")

    grid_options = gb.build()

    # Mostrar tabla editable
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode='MODEL_CHANGED',
        fit_columns_on_grid_load=True,
        enable_enterprise_modules=False,
        allow_unsafe_jscode=True,  # Permitir código JavaScript personalizado
    )

    # Datos editados
    edited_df = pd.DataFrame(grid_response['data'])

    # Convertir columnas a numéricas
    numeric_columns = ['Cantidad de Funcionarios', 'Días', 'Costo de Pasaje', 'Alojamiento',
                       'Per-diem y Otros', 'Movilidad']
    for col in numeric_columns:
        edited_df[col] = pd.to_numeric(edited_df[col], errors='coerce').fillna(0)

    # Recalcular la columna 'Total' con los datos editados
    edited_df['Total'] = edited_df.apply(calculate_total, axis=1)

    # Resumen por país y categorías (actualizado)
    category_columns = ['Costo de Pasaje', 'Alojamiento', 'Per-diem y Otros', 'Movilidad']
    summary_by_country_edited = edited_df.groupby('País')[category_columns + ['Total']].sum()

    # Mostrar resumen por país con tablas expandibles
    st.write("**Resumen General por País (Actualizado):**")
    for country, data in summary_by_country_edited.iterrows():
        total = data['Total']
        with st.expander(f"{country} - Total: {total:,.2f}"):
            st.write("**Detalles por Categoría**")
            for category in category_columns:
                st.write(f"- **{category}:** {data[category]:,.2f}")

    # Mostrar el nuevo monto total general
    total_sum = edited_df['Total'].sum()
    st.write(f"### Nuevo Monto Total General: {total_sum:,.2f}")

    # Calcular y mostrar la diferencia respecto al monto deseado
    difference = desired_total - total_sum
    st.write(f"### Diferencia para alcanzar el monto deseado: {difference:,.2f}")

    # Descargar la tabla modificada
    st.write("### Descargar Tabla Modificada")
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button(label="Descargar CSV", data=csv, file_name="tabla_modificada.csv", mime="text/csv")
