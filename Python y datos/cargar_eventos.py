import os
import sys
import tkinter as tk
from tkinter import filedialog
import pandas as pd
import pymysql

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

def conectar_bd():
    try:
        return pymysql.connect(**DB_CONFIG)
    except Exception as e:
        print(f"❌ Error crítico de conexión a la Base de Datos: {e}")
        sys.exit()

# Detector de celdas totalmente vacías (Blanks)
def es_vacio_absoluto(val):
    if val is None or pd.isna(val):
        return True
    if isinstance(val, str):
        return val.strip() == ''
    return False

# Detector de la convención "NA"
def es_texto_na(val):
    if isinstance(val, str):
        return val.strip().lower() in ['na', 'n/a', 'nan', 'null', 'none']
    return False

# =====================================================================
# PASO 1: SISTEMA DE LOGIN (Modificado para traer id_usuario)
# =====================================================================
def iniciar_sesion():
    print("\n=============================================")
    print("      CONTROL DE ACCESO - AGUAPACHÁ EVENTOS   ")
    print("=============================================")
    
    conexion = conectar_bd()
    while True:
        usuario_input = input("👤 Usuario: ").strip()
        contrasenia_input = input("🔑 Contraseña: ").strip()
        
        try:
            with conexion.cursor() as cursor:
                sql = "SELECT id_usuario, usuario, rol FROM usuarios WHERE usuario = %s AND contrasena = %s"
                cursor.execute(sql, (usuario_input, contrasenia_input))
                resultado = cursor.fetchone()
                
                if resultado:
                    print(f"\n✅ Credenciales correctas. Usuario verificado: {resultado['usuario']} (ID: {resultado['id_usuario']})")
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
        title="Aguapachá - Selecciona el archivo de Carga Masiva",
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
# MOTOR CENTRAL DE PROCESAMIENTO (Modificado para recibir id_usuario)
# =====================================================================
def procesar_archivo_masivo(ruta_excel, id_usuario, usuario, rol):
    conexion = conectar_bd()
    
    try:
        print("\n🔍 Sincronizando datos con la BD para control de duplicados...")
        with conexion.cursor() as cursor:
            # CORRECCIÓN: Forzamos a MySQL a entregar la fecha y la hora en un formato estandarizado
            sql_duplicados = """
                SELECT CONCAT(
                    DATE_FORMAT(fecha, '%Y-%m-%d'), '|', 
                    TIME_FORMAT(hora_inicio, '%H:%i:%s'), '|', 
                    contacto_ppal, '|', 
                    direccion, '|', 
                    id_tipo_evento, '|', 
                    id_servicio
                ) AS llave 
                FROM eventos
            """
            cursor.execute(sql_duplicados)
            eventos_existentes = set([row['llave'] for row in cursor.fetchall()])

        df = pd.read_excel(ruta_excel, keep_default_na=False)
        df.columns = df.columns.str.strip().str.lower()
        
        registros_correctos = []
        filas_con_error = [] 
        
        print("\n📋 Analizando filas con validación estricta de FKs y Valores...")
        
        for index, fila in df.iterrows():
            num_fila = index + 2  
            campos_faltantes = []
            
            # 1. fecha (Obligatorio - No permite NA)
            val_fecha = fila.get('fecha')
            if es_vacio_absoluto(val_fecha) or es_texto_na(val_fecha):
                campos_faltantes.append('fecha')
                fecha_limpia = None
            else:
                try:
                    # Primero intenta leer priorizando el día al inicio (dd-mm-yyyy o dd/mm/yyyy)
                    fecha_dt = pd.to_datetime(val_fecha, dayfirst=True, errors='coerce')
                    
                    # Si no coincide o da NaT, intenta con el formato mixto (por ejemplo, si viene yyyy-mm-dd)
                    if pd.isna(fecha_dt):
                        fecha_dt = pd.to_datetime(val_fecha, format='mixed', errors='coerce')
                    
                    if pd.isna(fecha_dt):
                        raise ValueError()
                        
                    fecha_limpia = fecha_dt.date().strftime('%Y-%m-%d')
                except Exception:
                    error_msg = f"Rechazado: El formato de fecha '{val_fecha}' es inválido."
                    filas_con_error.append({**fila.to_dict(), 'Fila_Excel': num_fila, 'Motivo_Rechazo': error_msg})
                    continue

            # 2. hora_inicio (Opcional - Normalizado con segundos)
            val_hora = fila.get('hora_inicio')
            if es_vacio_absoluto(val_hora) or es_texto_na(val_hora):
                hora_limpia = "00:00:00"
            else:
                try:
                    h_str = str(val_hora).strip()
                    if '.' in h_str:
                        h_str = h_str.split('.')[0]
                    
                    partes = h_str.split(':')
                    if len(partes) == 2:  # HH:MM -> HH:MM:00
                        hora_limpia = f"{partes[0].zfill(2)}:{partes[1].zfill(2)}:00"
                    elif len(partes) >= 3:  # HH:MM:SS
                        hora_limpia = f"{partes[0].zfill(2)}:{partes[1].zfill(2)}:{partes[2][:2].zfill(2)}"
                    else:
                        t_dt = pd.to_datetime(h_str, errors='coerce')
                        if not pd.isna(t_dt):
                            hora_limpia = t_dt.strftime('%H:%M:%S')
                        else:
                            hora_limpia = h_str
                except Exception:
                    hora_limpia = str(val_hora).strip()

            # 3. duracion (Opcional)
            val_duracion = fila.get('duracion')
            if es_vacio_absoluto(val_duracion) or es_texto_na(val_duracion):
                duracion = 0.0
            else:
                try:
                    duracion = float(val_duracion)
                except (ValueError, TypeError):
                    duracion = 0.0

            # 4. direccion (Obligatorio de texto - Acepta "NA" corporativo)
            val_direccion = fila.get('direccion')
            if es_vacio_absoluto(val_direccion):
                campos_faltantes.append('direccion')
                direccion = ""
            else:
                direccion = str(val_direccion).strip()

            # 5. id_ciudad (FK Obligatoria - No permite NA)
            val_ciudad = fila.get('id_ciudad')
            if es_vacio_absoluto(val_ciudad) or es_texto_na(val_ciudad):
                campos_faltantes.append('id_ciudad')
                id_ciudad = None
            else:
                try:
                    id_ciudad = int(float(val_ciudad))
                except (ValueError, TypeError):
                    campos_faltantes.append('id_ciudad')
                    id_ciudad = None

            # 6. contacto_ppal (Obligatorio de texto - Acepta "NA" corporativo)
            val_contacto = fila.get('contacto_ppal')
            if es_vacio_absoluto(val_contacto):
                campos_faltantes.append('contacto_ppal')
                contacto_ppal = ""
            else:
                contacto_ppal = str(val_contacto).strip()

            # 7. contacto_sec (Opcional)
            val_contacto_sec = fila.get('contacto_sec')
            contacto_sec_limpio = None if (es_vacio_absoluto(val_contacto_sec) or es_texto_na(val_contacto_sec)) else str(val_contacto_sec).strip()

            # 8. id_tipo_evento (FK Obligatoria - No permite NA)
            val_tipo = fila.get('id_tipo_evento')
            if es_vacio_absoluto(val_tipo) or es_texto_na(val_tipo):
                campos_faltantes.append('id_tipo_evento')
                id_tipo_evento = None
            else:
                try:
                    id_tipo_evento = int(float(val_tipo))
                except (ValueError, TypeError):
                    campos_faltantes.append('id_tipo_evento')
                    id_tipo_evento = None

            # 9. id_servicio (FK Obligatoria - No permite NA)
            val_servicio = fila.get('id_servicio')
            if es_vacio_absoluto(val_servicio) or es_texto_na(val_servicio):
                campos_faltantes.append('id_servicio')
                id_servicio = None
            else:
                try:
                    id_servicio = int(float(val_servicio))
                except (ValueError, TypeError):
                    campos_faltantes.append('id_servicio')
                    id_servicio = None

            # 10. observaciones (Opcional)
            val_obs = fila.get('observaciones')
            observaciones_limpias = None if (es_vacio_absoluto(val_obs) or es_texto_na(val_obs)) else str(val_obs).strip()

            # 11. valor_venta (Valor Obligatorio - No permite NA, permite >= 0)
            val_venta = fila.get('valor_venta')
            if es_vacio_absoluto(val_venta) or es_texto_na(val_venta):
                campos_faltantes.append('valor_venta')
                valor_numerico = None
            else:
                try:
                    valor_numerico = int(float(val_venta))
                    if valor_numerico < 0:
                        error_msg = f"Rechazado: El valor de venta '{val_venta}' no puede ser menor a cero."
                        filas_con_error.append({**fila.to_dict(), 'Fila_Excel': num_fila, 'Motivo_Rechazo': error_msg})
                        continue
                except (ValueError, TypeError):
                    error_msg = f"Rechazado: El valor de venta '{val_venta}' debe ser un número entero válido."
                    filas_con_error.append({**fila.to_dict(), 'Fila_Excel': num_fila, 'Motivo_Rechazo': error_msg})
                    continue

            # Si se detectó vacío en campos críticos obligatorios, se rechaza la fila entera
            if campos_faltantes:
                error_msg = f"Rechazado: Campos obligatorios/FKs vacíos o con 'NA': {campos_faltantes}."
                filas_con_error.append({**fila.to_dict(), 'Fila_Excel': num_fila, 'Motivo_Rechazo': error_msg})
                continue

            # CORRECCIÓN: Armamos la llave con fecha_limpia y hora_limpia para el control estricto de duplicados
            llave_fila = f"{fecha_limpia}|{hora_limpia}|{contacto_ppal}|{direccion}|{id_tipo_evento}|{id_servicio}"
            if llave_fila in eventos_existentes:
                error_msg = "Omitido: Ya existe un registro idéntico en la BD."
                filas_con_error.append({**fila.to_dict(), 'Fila_Excel': num_fila, 'Motivo_Rechazo': error_msg})
                continue

            registros_correctos.append((
                fecha_limpia, hora_limpia, float(duracion), direccion, id_ciudad,
                contacto_ppal, contacto_sec_limpio, id_tipo_evento, id_servicio,
                observaciones_limpias, valor_numerico
            ))

        # Diagnóstico y Reporte en Pantalla
        total_ok = len(registros_correctos)
        total_errores = len(filas_con_error)
        
        print("\n=============================================")
        print("          REPORTE DE PRE-VALIDACIÓN          ")
        print("=============================================")
        print(f"✅ Filas óptimas para subir a la BD: {total_ok}")
        print(f"⚠️ Filas rechazadas / duplicadas   : {total_errores}")
        print("=============================================")
        
        if total_ok == 0:
            print("\nℹ️ Operación terminada: No hay datos válidos para inyectar.")
            generar_excel_errores(filas_con_error, ruta_excel)
            return

        print(f"\nSe procederá a realizar la carga de los {total_ok} registros correctos.")
        confirmacion = input("❓ ¿Desea continuar con la inyección a la Base de Datos? (Yes/No): ").strip().lower()
        
        if confirmacion not in ['yes', 'y', 's', 'si']:
            print("\n❌ Operación cancelada por el usuario.")
            generar_excel_errores(filas_con_error, ruta_excel)
            return

        # Persistencia masiva transaccional atómica
        with conexion.cursor() as cursor:
            cursor.execute("SET @carga_masiva = 1;")
            
            sql_insert = """
                INSERT INTO eventos (
                    fecha, hora_inicio, duracion, direccion, id_ciudad, 
                    contacto_ppal, contacto_sec, id_tipo_evento, id_servicio, 
                    observaciones, valor_venta
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.executemany(sql_insert, registros_correctos)
            
            cursor.execute("SET @carga_masiva = 0;")
            
            sql_log = """
                INSERT INTO log_auditoria (id_usuario, accion)
                VALUES (%s, %s)
            """
            detalle_accion = f"Carga masiva: {total_ok} Registros"[:100]
            cursor.execute(sql_log, (id_usuario, detalle_accion))
            
            conexion.commit()
            
        print(f"\n🎉 ¡ÉXITO TOTAL! Inyectados {total_ok} registros limpios en la tabla 'eventos'.")
        generar_excel_errores(filas_con_error, ruta_excel)

    except Exception as e:
        conexion.rollback()
        print(f"\n💥 Error crítico detectado en MySQL. Se aplicó ROLLBACK absoluto: {e}")
    finally:
        conexion.close()

# =====================================================================
# AUXILIAR: GENERACIÓN DEL EXCEL DE ERRORES
# =====================================================================
def generar_excel_errores(lista_errores, ruta_excel_origen):
    if not lista_errores:
        print("\n✨ ¡Excelente! El origen de datos fue compatible.")
        return
        
    nombre_base = os.path.splitext(os.path.basename(ruta_excel_origen))[0]
    contador = 1
    while True:
        nombre_archivo = f"{nombre_base}_error{contador}.xlsx"
        if not os.path.exists(nombre_archivo):
            break
        contador += 1
        
    df_errores = pd.DataFrame(lista_errores)
    columnas_ordenadas = ['Fila_Excel', 'Motivo_Rechazo'] + [col for col in df_errores.columns if col not in ['Fila_Excel', 'Motivo_Rechazo']]
    df_errores = df_errores[columnas_ordenadas]
    
    try:
        df_errores.to_excel(nombre_archivo, index=False)
        print(f"\n💾 Archivo de novedades generado con éxito: '{nombre_archivo}'")
    except Exception as e:
        print(f"⚠️ No se pudo guardar el archivo de errores debido a: {e}")

if __name__ == "__main__":
    sesion = None
    while True:
        datos_usuario = iniciar_sesion()
        rol_limpio = str(datos_usuario['rol']).strip().lower()
        if rol_limpio in ['admin', 'editor']:
            sesion = datos_usuario
            print(f"🔑 Rol verificado con éxito. Permisos autorizados para {sesion['usuario']}.\n")
            break
        print(f"\n🚫 Acceso denegado: El rol '{datos_usuario['rol']}' no tiene permisos.")
        opcion = input("\n❓ ¿Deseas iniciar sesión con otra cuenta? (Yes/No): ").strip().lower()
        if opcion not in ['yes', 'y', 's', 'si']:
            sys.exit()

    archivo_a_procesar = seleccionar_archivo_visual()
    procesar_archivo_masivo(archivo_a_procesar, sesion['id_usuario'], sesion['usuario'], sesion['rol'])
