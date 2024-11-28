import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode

# Función para calcular el total dinámicamente
def calculate_total(row):
    return (row['Cantidad de Funcionarios'] * row['Costo de Pasaje']) + \
           (row['Cantidad de Funcionarios'] * row['Días'] * row['Alojamiento']) + \
           (row['Cantidad de Funcionarios'] * row['Días'] * row['Per-diem y Otros']) + \
           (row['Cantidad de Funcionarios'] * row['Movilidad'])

# Cargar los datos
file_path = 'BDD_Ajuste.xlsx'
df = pd.read_excel(file_path, sheet_name='Original_VPO')
df['Total'] = df.apply(calculate_total, axis=1)

# Selector de vista
st.sidebar.title("Selector de Vista")
vista = st.sidebar.radio(
    "Elige una vista:",
    ("Vista Resumen Original", "Vista Editable con Actualización")
)

if vista == "Vista Resumen Original":
    st.title("Resumen General con Tablas Extendibles")

    # Resumen por país y categorías
    category_columns = ['Costo de Pasaje', 'Alojamiento', 'Per-diem y Otros', 'Movilidad']
    summary_by_country = df.groupby('País')[category_columns + ['Total']].sum()

    # Mostrar resumen por país con tablas extendibles
    st.write("**Resumen General por País:**")
    for country, data in summary_by_country.iterrows():
        total = data['Total']
        with st.expander(f"{country} - Total: {total:,.2f}"):
            st.write("**Detalles por Categoría**")
            for category in category_columns:
                st.write(f"- **{category.lower()}:** {data[category]:,.2f}")

    # Visualizar tabla completa
    st.write("### Tabla Completa:")
    st.dataframe(df)

elif vista == "Vista Editable con Actualización":
    st.title("Edición de Tabla Interactiva con Recalculo Dinámico")

    # Configuración de AgGrid para edición
    st.write("### Tabla Editable")
    st.write("Edita los valores y ajusta los totales hasta alcanzar el monto deseado.")
    
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=True)  # Permitir edición
    gb.configure_column('Total', editable=False)  # Bloquear la columna Total
    grid_options = gb.build()

    # Mostrar tabla editable
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        data_return_mode=DataReturnMode.AS_INPUT,
        update_mode='MODEL_CHANGED',
        fit_columns_on_grid_load=True,
        enable_enterprise_modules=False,
    )

    # Datos editados
    edited_df = grid_response['data']
    edited_df = pd.DataFrame(edited_df)

    # Recalcular la columna Total
    edited_df['Total'] = edited_df.apply(calculate_total, axis=1)

    # Resumen por país y categorías (actualizado)
    category_columns = ['Costo de Pasaje', 'Alojamiento', 'Per-diem y Otros', 'Movilidad']
    summary_by_country_edited = edited_df.groupby('País')[category_columns + ['Total']].sum()

    # Mostrar resumen por país con tablas extendibles
    st.write("**Resumen General por País (Actualizado):**")
    for country, data in summary_by_country_edited.iterrows():
        total = data['Total']
        with st.expander(f"{country} - Total: {total:,.2f}"):
            st.write("**Detalles por Categoría**")
            for category in category_columns:
                st.write(f"- **{category.lower()}:** {data[category]:,.2f}")

    # Mostrar el nuevo monto total general
    total_sum = edited_df['Total'].sum()
    st.write(f"### Nuevo Monto Total General: {total_sum:,.2f}")

    # Descargar la tabla modificada
    st.write("### Descargar Tabla Modificada")
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button(label="Descargar CSV", data=csv, file_name="tabla_modificada.csv", mime="text/csv")
