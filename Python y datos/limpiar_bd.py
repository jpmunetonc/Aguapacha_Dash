from sqlalchemy import create_engine, text

url_conexion = "mysql+pymysql://root:ABC123@localhost/aguapacha"

try:
    print("⏳ Conectando a MySQL para limpieza masiva...")
    engine = create_engine(url_conexion)
    
    with engine.begin() as connection:
        print("🧹 Desactivando llaves foráneas y vaciando tablas...")
        connection.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        
        tablas = ['eventos', 'servicios', 'tipos_evento', 'ciudades', 'departamentos']
        for tabla in tablas:
            connection.execute(text(f"TRUNCATE TABLE {tabla};"))
            print(f"   -> Tabla '{tabla}' dejada en cero (IDs reiniciados).")
            
        connection.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        print("\n✨ [ÉXITO] Base de datos 'aguapacha' limpia e intacta para nuevas cargas.")

except Exception as e:
    print(f"\n❌ Error crítico durante la limpieza: {str(e)}")