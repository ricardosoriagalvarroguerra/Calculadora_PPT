import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode

# Título de la app
st.title("Edición de Tabla Interactiva - Presupuesto VPO")

# Cargar los datos
file_path = 'BDD_Ajuste.xlsx'
df = pd.read_excel(file_path, sheet_name='VPO')

# Agregar columna calculada Total basada en la fórmula proporcionada
def calculate_total(row):
    return (row['Cantidad de Funcionarios'] * row['Costo de Pasaje']) + \
           (row['Cantidad de Funcionarios'] * row['Días'] * row['Alojamiento']) + \
           (row['Cantidad de Funcionarios'] * row['Días'] * row['Per-diem y Otros']) + \
           (row['Cantidad de Funcionarios'] * row['Movilidad'])

df['Total'] = df.apply(calculate_total, axis=1)

# Mostrar tabla editable
st.write("### Tabla Editable")
st.write("Edita los valores y ajusta los totales hasta alcanzar el monto deseado.")

# Configuración de AgGrid para edición interactiva
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(editable=True)  # Permitir edición
gb.configure_column('Total', editable=False)  # Bloquear la columna Total
grid_options = gb.build()

# Mostrar tabla editable
grid_response = AgGrid(
    df,
    gridOptions=grid_options,
    data_return_mode=DataReturnMode.AS_INPUT,
    update_mode='MANUAL',
    fit_columns_on_grid_load=True,
    enable_enterprise_modules=False,
)

# Datos editados
edited_df = grid_response['data']
edited_df = pd.DataFrame(edited_df)

# Recalcular la columna Total
edited_df['Total'] = edited_df.apply(calculate_total, axis=1)

# Mostrar el nuevo monto total general
total_sum = edited_df['Total'].sum()
st.write(f"### Nuevo Monto Total General: {total_sum:,.2f}")

# Descargar la tabla editada
st.write("### Descargar Tabla Modificada")
csv = edited_df.to_csv(index=False).encode('utf-8')
st.download_button(label="Descargar CSV", data=csv, file_name="tabla_modificada.csv", mime="text/csv")
