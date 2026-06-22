import sqlite3
import random
import faker
from datetime import datetime

fake = faker.Faker()
DB_NAME = r'database\database.db' # Coloca la ruta real de tu archivo .db

def poblar_sistema_medico():
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    # Optimizaciones de velocidad para SQLite
    cursor.execute("PRAGMA journal_mode = MEMORY;")
    cursor.execute("PRAGMA synchronous = OFF;")
    cursor.execute("PRAGMA cache_size = -100000;")
    cursor.execute("PRAGMA foreign_keys = OFF;") # Desactivar temporalmente para máxima velocidad
    
    # Los 10 colores oficiales del hospital (decena del último par de num_historia)
    colores_oficiales = [
        "Marron",        # 00-09
        "Azul Marino",   # 10-19
        "Verde",         # 20-29
        "Naranja",       # 30-39
        "Morado",        # 40-49
        "Rosa",          # 50-59
        "Turquesa",      # 60-69
        "Amarillo",      # 70-79
        "Rojo",          # 80-89
        "Azul Celeste",  # 90-99
    ]
    
    # Asegurar que existan los colores oficiales en la base de datos
    for idx, color_name in enumerate(colores_oficiales, start=1):
        cursor.execute(
            "INSERT OR IGNORE INTO colores (id, valor, estado) VALUES (?, ?, 1);",
            (idx, color_name)
        )
    conexion.commit()
    
    # Mapear nombres de color a sus IDs en la base de datos
    cursor.execute("SELECT id, valor FROM colores;")
    color_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    # Cargar cédulas e historias existentes para garantizar unicidad absoluta
    cursor.execute("SELECT cedula FROM pacientes WHERE cedula IS NOT NULL;")
    cedulas_existentes = {row[0] for row in cursor.fetchall()}
    
    cursor.execute("SELECT num_historia FROM tarjetas;")
    historias_existentes = {row[0] for row in cursor.fetchall()}
    
    # Averiguar en qué ID comenzar por si ya tienes datos previos
    cursor.execute("SELECT MAX(id) FROM pacientes;")
    ultimo_id = cursor.fetchone()[0]
    id_actual = (ultimo_id if ultimo_id is not None else 0) + 1
    
    total_registros = 2000
    tamano_lote = 100 # Reducimos un poco el lote porque insertaremos en dos tablas a la vez
    
    print(f"Iniciando inyección de {total_registros} pacientes con sus respectivas tarjetas...")
    inicio_total = datetime.now()
    
    for lote_idx in range(0, total_registros, tamano_lote):
        cursor.execute("BEGIN TRANSACTION;")
        
        lista_pacientes = []
        lista_tarjetas = []
        
        for _ in range(tamano_lote):
            # Generar cédula única y realista (rango 10,000,000 - 39,999,999, sin ceros a la izquierda)
            while True:
                num_cedula = random.randint(10000000, 39999999)
                cedula = f"{random.choice(['V', 'E'])}-{num_cedula}"
                if cedula not in cedulas_existentes:
                    cedulas_existentes.add(cedula)
                    break
            
            # Generar número de historia único en formato XX-XX-XX
            while True:
                p1 = random.randint(10, 99)
                p2 = random.randint(10, 99)
                p3 = random.randint(0, 99)
                num_historia = f"{p1:02d}-{p2:02d}-{p3:02d}"
                if num_historia not in historias_existentes:
                    historias_existentes.add(num_historia)
                    break
            
            # Determinar el color correcto según el último par de dígitos
            decena = p3 // 10
            color_nombre = colores_oficiales[decena]
            id_color = color_map.get(color_nombre, 1)
            
            # Datos alineados estrictamente a tus columnas de 'pacientes'
            # (id, nombre1, nombre2, apellido1, apellido2, cedula, lugar_nacimiento, fecha_nacimiento, estado_vital, estado)
            paciente = (
                id_actual,
                fake.first_name(),
                fake.first_name(),
                fake.last_name(),
                fake.last_name(),
                cedula,
                fake.city(),
                fake.date_of_birth(minimum_age=11, maximum_age=100).strftime("%d-%m-%Y"),
                random.choice([0, 1]),
                1 # Estado activo
            )
            lista_pacientes.append(paciente)
            
            # Datos alineados estrictamente a tus columnas de 'tarjetas'
            # (num_historia, id_paciente, id_color, estado)
            tarjeta = (
                num_historia,
                id_actual,
                id_color,
                1  # Estado activa
            )
            lista_tarjetas.append(tarjeta)
            
            id_actual += 1
            
        # Inserción masiva en tabla Pacientes (forzando el ID manual para sincronizar)
        cursor.executemany("""
            INSERT INTO pacientes (id, nombre1, nombre2, apellido1, apellido2, cedula, lugar_nacimiento, fecha_nacimiento, estado_vital, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, lista_pacientes)
        
        # Inserción masiva correspondiente en tabla Tarjetas
        cursor.executemany("""
            INSERT INTO tarjetas (num_historia, id_paciente, id_color, estado)
            VALUES (?, ?, ?, ?);
        """, lista_tarjetas)
        
        conexion.commit()
        print(f"-> Procesados {id_actual - 1} registros totales...")
        
    # Reactivar llaves foráneas y cerrar
    cursor.execute("PRAGMA foreign_keys = ON;")
    conexion.close()
    print(f"¡Éxito absoluto! Sistema poblado en: {datetime.now() - inicio_total}")

def sincronizar_fts():
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    print("Sincronizando pacientes existentes hacia FTS5...")
    # Limpiamos e insertamos todo de nuevo
    cursor.execute("DELETE FROM pacientes_fts;")
    cursor.execute("""
        INSERT INTO pacientes_fts(rowid, id_paciente, nombres, apellidos, cedula)
        SELECT id, id, nombre1 || ' ' || COALESCE(nombre2, ''), apellido1 || ' ' || COALESCE(apellido2, ''), cedula
        FROM pacientes;
    """)
    conexion.commit()
    conexion.close()
    print("¡Sincronización FTS5 completa!")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "sync":
        sincronizar_fts()
    else:
        poblar_sistema_medico()
        # Sincronizamos por si acaso, aunque los triggers deberían hacerlo
        sincronizar_fts()
