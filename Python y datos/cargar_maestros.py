import pandas as pd
import os
from sqlalchemy import create_engine

archivo_excel = "datos.xlsx"  
url_conexion = "mysql+pymysql://root:ABC123@localhost/aguapacha"

# Solo las tablas maestras o dimensiones
estructuras_maestros = {
    'Departamentos': 'departamentos',      
    'Ciudades': 'ciudades',                
    'Tipos de evento': 'tipos_evento',    
    'Servicios': 'servicios'
}

mapa_columnas_sql = {
    'Departamentos': {'Id_Departamento': 'id_dpto', 'Departamento': 'nombre_departamento'},
    'Ciudades': {'Id_Municipio': 'id_ciudad', 'Municipio': 'nombre_ciudad', 'Id_Departamento': 'id_dpto'},
    'Tipos de evento': {'Id_Tipo': 'id_tipo_evento', 'Tipo_Evento': 'tipo_evento'},
    'Servicios': {'Id_Servicio': 'id_servicio', 'Nombre_Servicio': 'nombre_servicio'}
}

if not os.path.exists(archivo_excel):
    print(f"❌ Error: No se encuentra '{archivo_excel}'")
else:
    try:
        print("⏳ Procesando Tablas Maestras...")
        engine = create_engine(url_conexion)
        reporte = {}
        
        with engine.begin() as connection:
            for hoja, tabla_sql in estructuras_maestros.items():
                df = pd.read_excel(archivo_excel, sheet_name=hoja)
                df.columns = df.columns.str.strip()
                
                # Renombrar y limpiar duplicados internos del Excel
                dic_renombrar = mapa_columnas_sql[hoja]
                df = df.rename(columns=dic_renombrar)
                df_final = df[list(dic_renombrar.values())].copy()
                
                if tabla_sql == 'departamentos':
                    df_final = df_final.drop_duplicates(subset=['nombre_departamento'])
                elif tabla_sql == 'ciudades':
                    df_final = df_final.drop_duplicates(subset=['nombre_ciudad', 'id_dpto'])
                elif tabla_sql == 'tipos_evento':
                    df_final = df_final.drop_duplicates(subset=['tipo_evento'])
                elif tabla_sql == 'servicios':
                    df_final = df_final.drop_duplicates(subset=['nombre_servicio'])
                
                filas_excel = len(df_final)
                
                # Comparar con lo que ya existe en la BD
                try:
                    df_existente = pd.read_sql(f"SELECT * FROM {tabla_sql}", connection)
                except Exception:
                    df_existente = pd.DataFrame()
                
                if not df_existente.empty and not df_final.empty:
                    if tabla_sql == 'departamentos':
                        df_final = df_final[~df_final['nombre_departamento'].isin(df_existente['nombre_departamento'])]
                    elif tabla_sql == 'ciudades':
                        df_final = df_final.merge(df_existente[['nombre_ciudad', 'id_dpto']], on=['nombre_ciudad', 'id_dpto'], how='left', indicator=True)
                        df_final = df_final[df_final['_merge'] == 'left_only'].drop(columns=['_merge'])
                    elif tabla_sql == 'tipos_evento':
                        df_final = df_final[~df_final['tipo_evento'].isin(df_existente['tipo_evento'])]
                    elif tabla_sql == 'servicios':
                        df_final = df_final[~df_final['nombre_servicio'].isin(df_existente['nombre_servicio'])]

                filas_a_subir = len(df_final)
                reporte[hoja] = filas_excel - filas_a_subir
                
                if filas_a_subir > 0:
                    df_final.to_sql(name=tabla_sql, con=connection, if_exists='append', index=False)
                    print(f"   ✅ {filas_a_subir} registros nuevos subidos a '{tabla_sql}'.")
                else:
                    print(f"   ℹ️ Sin datos nuevos para '{tabla_sql}'.")
                    
        print("\n🎉 MAESTROS SINCRONIZADOS Y COMPROMETIDOS EN LA BD.")
    except Exception as e:
        print(f"❌ Error en maestros: {str(e)}")