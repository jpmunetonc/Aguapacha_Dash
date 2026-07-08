import pandas as pd
import os
import sys
import tkinter as tk
from tkinter import filedialog
import pymysql
from sqlalchemy import create_engine

# =====================================================================
# CONFIGURACIÓN GLOBAL DE LA BASE DE DATOS
# =====================================================================
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'ABC123',  
    'database': 'aguapacha',  
    'cursorclass': pymysql.cursors.DictCursor
}

# Construimos la URL de SQLAlchemy automáticamente a partir de DB_CONFIG
URL_CONEXION_SA = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"

def conectar_bd():
    try:
        return pymysql.connect(**DB_CONFIG)
    except Exception as e:
        print(f"❌ Error crítico de conexión a la Base de Datos: {e}")
        sys.exit()

# =====================================================================
# PASO 1: SISTEMA DE LOGIN (Con Bypass de Primer Uso)
# =====================================================================
def iniciar_sesion():
    print("\n=============================================")
    print("     CONTROL DE ACCESO - AGUAPACHÁ EVENTOS   ")
    print("=============================================")
    
    conexion = conectar_bd()
    
    # Validar si la tabla usuarios está vacía (Modo Configuración Inicial)
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as total FROM usuarios")
            resultado = cursor.fetchone()
            
            if resultado['total'] == 0:
                print("\n⚠️ ALERTA: No se detectaron usuarios en la base de datos.")
                print("🛠️ Entrando en 'Modo Configuración Inicial' para permitir la primera carga de maestros.")
                conexion.close()
                # Retornamos un usuario temporal con permisos de admin para saltar el login
                return {'id_usuario': 0, 'usuario': 'Admin_Setup', 'rol': 'admin'}
    except Exception as e:
        print(f"💥 Error al verificar la tabla de usuarios: {e}")
        conexion.close()
        sys.exit()

    # Flujo normal si ya existen usuarios
    while True:
        usuario_input = input("👤 Usuario: ").strip()
        contrasenia_input = input("🔑 Contraseña: ").strip()
        
        try:
            with conexion.cursor() as cursor:
                sql = "SELECT id_usuario, usuario, rol FROM usuarios WHERE usuario = %s AND contrasena = %s"
                cursor.execute(sql, (usuario_input, contrasenia_input))
                resultado = cursor.fetchone()
                
                if resultado:
                    print(f"\n✅ Credenciales correctas. Usuario verificado: {resultado['usuario']}")
                    conexion.close()
                    return resultado  
                else:
                    print("\n❌ Usuario o contraseña incorrectos.")
                    opcion = input("❓ ¿Desea volver a intentar el ingreso? (Yes/No): ").strip().lower()
                    if opcion not in ['yes', 'y', 's', 'si']:
                        print("\n👋 Saliendo de la ejecución. ¡Hasta luego!")
                        conexion.close()
                        sys.exit()
        except Exception as e:
            print(f"💥 Error inesperado durante el Login: {e}")
            conexion.close()
            sys.exit()

# =====================================================================
# PASO 2: EXPLORADOR DE ARCHIVOS
# =====================================================================
def seleccionar_archivo_visual():
    print("\n📂 Abriendo el explorador de archivos...")
    root = tk.Tk()
    root.withdraw() 
    root.attributes('-topmost', True) 
    
    ruta_seleccionada = filedialog.askopenfilename(
        title="Aguapachá - Selecciona el archivo de Maestros",
        filetypes=[("Archivos de Excel", "*.xlsx *.xls")]
    )
    
    if not ruta_seleccionada:
        print("\n⚠️ No seleccionaste ningún archivo de Excel.")
        opcion = input("❓ ¿Deseas intentar seleccionar el archivo otra vez? (Yes/No): ").strip().lower()
        if opcion in ['yes', 'y', 's', 'si']:
            return seleccionar_archivo_visual()
        else:
            print("👋 Saliendo de la ejecución. ¡Hasta luego!")
            sys.exit()
            
    print(f"🎯 Archivo seleccionado con éxito: '{os.path.basename(ruta_seleccionada)}'")
    return ruta_seleccionada

# =====================================================================
# PASO 3: MOTOR DE PROCESAMIENTO DE MAESTROS
# =====================================================================
def procesar_maestros(archivo_excel):
    estructuras_maestros = {
        'Departamentos': 'departamentos',      
        'Ciudades': 'ciudades',                
        'Tipos de evento': 'tipos_evento',    
        'Servicios': 'servicios',
        'Usuarios': 'usuarios' 
    }

    mapa_columnas_sql = {
        'Departamentos': {'Id_Departamento': 'id_dpto', 'Departamento': 'nombre_departamento'},
        'Ciudades': {'Id_Municipio': 'id_ciudad', 'Municipio': 'nombre_ciudad', 'Id_Departamento': 'id_dpto'},
        'Tipos de evento': {'Id_Tipo': 'id_tipo_evento', 'Tipo_Evento': 'tipo_evento'},
        'Servicios': {'Id_Servicio': 'id_servicio', 'Nombre_Servicio': 'nombre_servicio'},
        'Usuarios': {'Usuario': 'usuario', 'Contrasena': 'contrasena', 'Rol': 'rol'} 
    }

    try:
        print("\n⏳ Procesando Tablas Maestras...")
        engine = create_engine(URL_CONEXION_SA)
        
        with engine.begin() as connection:
            for hoja, tabla_sql in estructuras_maestros.items():
                try:
                    df = pd.read_excel(archivo_excel, sheet_name=hoja)
                except ValueError:
                    print(f"  ⚠️ Advertencia: No se encontró la hoja '{hoja}' en el archivo. Se omitirá.")
                    continue

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
                elif tabla_sql == 'usuarios':
                    df_final = df_final.drop_duplicates(subset=['usuario'])
                
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
                    elif tabla_sql == 'usuarios':
                        df_final = df_final[~df_final['usuario'].isin(df_existente['usuario'])]
                        
                filas_a_subir = len(df_final)
                
                if filas_a_subir > 0:
                    df_final.to_sql(name=tabla_sql, con=connection, if_exists='append', index=False)
                    print(f"   ✅ {filas_a_subir} registros nuevos subidos a '{tabla_sql}'.")
                else:
                    print(f"   ℹ️ Sin datos nuevos para '{tabla_sql}'.")
                    
        print("\n🎉 MAESTROS SINCRONIZADOS Y COMPROMETIDOS EN LA BD.")

    except Exception as e:
        print(f"\n❌ Error en maestros: {str(e)}")

# =====================================================================
# FLUJO PRINCIPAL
# =====================================================================
if __name__ == "__main__":
    sesion = None
    while True:
        datos_usuario = iniciar_sesion()
        rol_limpio = str(datos_usuario['rol']).strip().lower()
        
        if rol_limpio in ['admin', 'editor']:
            sesion = datos_usuario
            print(f"🔑 Rol verificado con éxito. Permisos autorizados para {sesion['usuario']}.\n")
            break
            
        print(f"\n🚫 Acceso denegado: El rol '{datos_usuario['rol']}' no tiene permisos para actualizar maestros.")
        opcion = input("\n❓ ¿Deseas iniciar sesión con otra cuenta? (Yes/No): ").strip().lower()
        if opcion not in ['yes', 'y', 's', 'si']:
            sys.exit()

    archivo_a_procesar = seleccionar_archivo_visual()
    procesar_maestros(archivo_a_procesar)
