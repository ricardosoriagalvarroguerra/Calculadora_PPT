import streamlit as st
import pandas as pd

# Configuración de la contraseña
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
        category_columns = ['Costo de Pasaje', 'Alojamiento', 'Per-diem y Otros', 'Movilidad']
        df['Total'] = df[category_columns].sum(axis=1)
        
        summary_by_country = df.groupby('País')[category_columns + ['Total']].sum()

        # Mostrar resumen general
        st.write("**Resumen General por País:**")
        for country, data in summary_by_country.iterrows():
            total = data['Total']
            with st.expander(f"{country} - Total: {total:,.2f}"):
                st.write("**Misiones**")
                for category in category_columns:
                    st.write(f"- **{category.lower()}:** {data[category]:,.2f}")
        
        # Visualizar toda la tabla original
        st.write("### Tabla Completa:")
        st.dataframe(df)
else:
    st.warning("Por favor, introduce la contraseña correcta para acceder.")
