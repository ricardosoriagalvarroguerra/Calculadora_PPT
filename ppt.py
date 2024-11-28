import streamlit as st
import pandas as pd

# Configuración de contraseña
PASSWORD = "mi_contraseña_secreta"

# Título de la app
st.title("Resumen y Visualización de Presupuesto - VPO")

# Solicitar contraseña
password = st.text_input("Introduce la contraseña para acceder", type="password")

if password == PASSWORD:
    # Cargar los datos
    file_path = 'BDD_Ajuste.xlsx'
    try:
        df = pd.read_excel(file_path, sheet_name='Original_VPO')
    except ValueError:
        st.error("La hoja 'VPO' no existe en el archivo. Por favor, verifica el archivo.")
    else:
        # Calcular los totales por país y categoría
        summary_by_country = df.groupby('País').sum()
        summary_by_category = df[['Costo de Pasaje', 'Alojamiento', 'Per-diem y Otros', 'Movilidad']].sum()

        # Mostrar resumen general
        st.write("**Resumen General:**")

        # Totales por categoría
        st.write("### Totales por Categoría:")
        st.table(summary_by_category)

        # Totales por país con detalle desplegable
        st.write("### Totales por País:")
        for country, group in df.groupby('País'):
            with st.expander(f"{country} (Total: {group['Total'].sum()})"):
                st.write(group[['Operación', 'Cantidad de Funcionarios', 'Días', 'Costo de Pasaje', 
                                'Alojamiento', 'Per-diem y Otros', 'Movilidad', 'Total']])

        # Visualizar toda la tabla
        st.write("### Tabla Completa:")
        st.dataframe(df)
else:
    st.warning("Por favor, introduce la contraseña correcta para acceder.")
