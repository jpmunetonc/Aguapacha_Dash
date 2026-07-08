import pandas as pd
import random
import datetime
import sys
import os
import pymysql

# =====================================================================
# CONFIGURACIÓN GLOBAL DE LA BASE DE DATOS
# =====================================================================
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'ABC123',  # <--- Cambia por tu contraseña real
    'database': 'aguapacha',   # <--- Nombre de tu BD
    'cursorclass': pymysql.cursors.DictCursor
}

def conectar_bd():
    try:
        return pymysql.connect(**DB_CONFIG)
    except Exception as e:
        print(f"❌ Error crítico de conexión a la Base de Datos: {e}")
        sys.exit()

# =====================================================================
# PASO 1: SISTEMA DE LOGIN Y VERIFICACIÓN DE ROLES
# =====================================================================
def iniciar_sesion():
    print("\n=============================================")
    print("  GENERADOR DE DATOS - AGUAPACHÁ EVENTOS     ")
    print("=============================================")
    
    conexion = conectar_bd()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as total FROM usuarios")
            if cursor.fetchone()['total'] == 0:
                print("\n⚠️ ALERTA: No se detectaron usuarios en la base de datos.")
                print("🛠️ Entrando en Modo Configuración Inicial...")
                conexion.close()
                return {'id_usuario': 0, 'usuario': 'Admin_Setup', 'rol': 'admin'}
    except Exception as e:
        print(f"💥 Error al verificar la tabla de usuarios: {e}")
        conexion.close()
        sys.exit()

    while True:
        usuario_input = input("👤 Usuario: ").strip()
        contrasenia_input = input("🔑 Contraseña: ").strip()
        
        try:
            with conexion.cursor() as cursor:
                sql = "SELECT id_usuario, usuario, rol FROM usuarios WHERE usuario = %s AND contrasena = %s"
                cursor.execute(sql, (usuario_input, contrasenia_input))
                resultado = cursor.fetchone()
                
                if resultado:
                    print(f"\n✅ Credenciales correctas. Bienvenido {resultado['usuario']}.")
                    conexion.close()
                    return resultado  
                else:
                    print("\n❌ Usuario o contraseña incorrectos.")
                    opcion = input("❓ ¿Intentar de nuevo? (Yes/No): ").strip().lower()
                    if opcion not in ['yes', 'y', 's', 'si']:
                        sys.exit()
        except Exception as e:
            print(f"💥 Error en el Login: {e}")
            conexion.close()
            sys.exit()

# =====================================================================
# PASO 2: EXTRACCIÓN DE MAESTROS Y EVENTOS EXISTENTES
# =====================================================================
def obtener_datos_maestros():
    conexion = conectar_bd()
    maestros = {}
    
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id_ciudad FROM ciudades")
            maestros['ciudades'] = [row['id_ciudad'] for row in cursor.fetchall()]
            
            cursor.execute("SELECT id_tipo_evento FROM tipos_evento")
            maestros['tipos_evento'] = [row['id_tipo_evento'] for row in cursor.fetchall()]
            
            cursor.execute("SELECT id_servicio FROM servicios")
            maestros['servicios'] = [row['id_servicio'] for row in cursor.fetchall()]
            
            if not maestros['ciudades'] or not maestros['tipos_evento'] or not maestros['servicios']:
                print("\n🛑 PRIMERO TIENES QUE AGREGAR LOS DATOS MAESTROS.")
                print("Faltan registros en las tablas de ciudades, tipos de evento o servicios.")
                sys.exit()
                
            try:
                cursor.execute("SELECT fecha, hora_inicio, id_ciudad FROM eventos")
                eventos_bd = cursor.fetchall()
                maestros['eventos_existentes'] = set()
                
                for row in eventos_bd:
                    f = row['fecha']
                    f_str = f.strftime("%d/%m/%Y") if hasattr(f, 'strftime') else str(f)
                    h_str = str(row['hora_inicio'])
                    maestros['eventos_existentes'].add((f_str, h_str, row['id_ciudad']))
            except Exception:
                maestros['eventos_existentes'] = set()
                
    except Exception as e:
        print(f"\n❌ Error consultando la base de datos: {e}")
        sys.exit()
    finally:
        conexion.close()
        
    return maestros

# =====================================================================
# PASO 3: GENERACIÓN ALEATORIA DE DATOS
# =====================================================================
def generar_excel_aleatorio(maestros, cantidad_registros):
    print(f"\n⏳ Iniciando la generación de {cantidad_registros:,} registros únicos...")
    
    ano_actual = datetime.date.today().year
    fecha_inicio = datetime.date(ano_actual - 2, 1, 1)
    fecha_fin = datetime.date(ano_actual, 12, 31)
    dias_totales = (fecha_fin - fecha_inicio).days
    
    nombres_dummy = ["Andrés", "Carlos", "Juan", "Vanessa", "Diana", "Mateo", "Santiago", "Camila", "Daniela", "Alejandro"]
    direcciones_dummy = [
        "Carrera 59c # 40a - 48",
        "Calle 10 # 43 - 20",
        "Circular 1 # 70 - 01",
        "Cra 48 # 32 - 10, centro",
        "Calle 50 # 51 - 24, parque principal",
        "Diagonal 45 # 12 - 90, Barrio central",
        "Avenida Poblado # 5a - 110, Vereda finca"
    ]
    
    opciones_observaciones = [
        "", 
        "Sin observaciones", 
        "Llegar 1 hora antes para montaje", 
        "Confirmar logística con el encargado", 
        "Llevar equipamiento adicional", 
        "Evento en espacio abierto",
        "Revisar conexiones eléctricas al llegar"
    ]

    registros = []
    generados = 0
    max_intentos = cantidad_registros * 5 
    intentos = 0
    
    while generados < cantidad_registros and intentos < max_intentos:
        intentos += 1
        
        dias_random = random.randint(0, dias_totales)
        fecha_obj = fecha_inicio + datetime.timedelta(days=dias_random)
        fecha_str = fecha_obj.strftime("%d-%m-%Y") 
        
        hora = f"{random.randint(0, 23):02d}:00" 
        id_ciudad = random.choice(maestros['ciudades'])
        
        llave_unica = (fecha_str, hora, id_ciudad)
        if llave_unica in maestros['eventos_existentes']:
            continue 
            
        tel_p = f"3{random.randint(100, 999)}{random.randint(1000, 9999)}"
        tel_s = f"3{random.randint(100, 999)}{random.randint(1000, 9999)}"
        
        fila = {
            'fecha': fecha_str,
            'hora_inicio': hora,
            'duracion': random.randint(1, 8),
            'direccion': random.choice(direcciones_dummy) + f" apto {random.randint(101, 1502)}",
            'id_ciudad': id_ciudad,
            'contacto_ppal': f"{random.choice(nombres_dummy)} {tel_p}",
            'Contacto_Sec': tel_s,
            'id_tipo_evento': random.choice(maestros['tipos_evento']),
            'id_servicio': random.choice(maestros['servicios']),
            'observaciones': random.choice(opciones_observaciones),
            'valor_venta': random.randint(200, 2500) * 1000 
        }
        
        registros.append(fila)
        maestros['eventos_existentes'].add(llave_unica) 
        generados += 1

    if not registros:
        print("⚠️ No se pudo generar ningún registro nuevo debido a restricciones de unicidad.")
        sys.exit()

    if generados < cantidad_registros:
        print(f"⚠️ Nota: Se detuvo la generación en {generados:,} filas porque se agotaron las combinaciones únicas posibles de fecha/hora/ciudad.")

    df = pd.DataFrame(registros)
    
    # =====================================================================
    # CAMBIO AQUÍ: CONTROL DE NOMBRE AUTO-INCREMENTAL
    # =====================================================================
    base_nombre = "datos"
    extension = ".xlsx"
    contador = 1
    
    # Busca dinámicamente un número de archivo que no exista en la carpeta actual
    while os.path.exists(f"{base_nombre}_{contador}{extension}"):
        contador += 1
        
    nombre_archivo = f"{base_nombre}_{contador}{extension}"
    df.to_excel(nombre_archivo, index=False)
    
    print(f"\n🎉 ¡Éxito! Se han generado {generados:,} registros aleatorios.")
    print(f"📁 Archivo guardado como: '{os.path.abspath(nombre_archivo)}'")

# =====================================================================
# FLUJO PRINCIPAL
# =====================================================================
if __name__ == "__main__":
    while True:
        datos_usuario = iniciar_sesion()
        rol_limpio = str(datos_usuario['rol']).strip().lower()
        
        if rol_limpio in ['admin', 'editor']:
            print(f"🔑 Permisos autorizados para {datos_usuario['usuario']}.\n")
            break
            
        print(f"\n🚫 Acceso denegado: El rol '{datos_usuario['rol']}' no tiene permisos.")
        opcion = input("❓ ¿Deseas iniciar sesión con otra cuenta? (Yes/No): ").strip().lower()
        if opcion not in ['yes', 'y', 's', 'si']:
            sys.exit()

    maestros_bd = obtener_datos_maestros()
    
    while True:
        cantidad_input = input("🔢 ¿Cuántos registros deseas generar en el archivo Excel?: ").strip()
        cantidad_limpia = cantidad_input.replace(".", "").replace(",", "")
        
        if cantidad_limpia.isdigit():
            cantidad_final = int(cantidad_limpia)
            if cantidad_final > 0:
                break
        print("❌ Entrada inválida. Por favor ingresa un número entero (ejemplo: 1000 o 1.500).")

    generar_excel_aleatorio(maestros_bd, cantidad_registros=cantidad_final)