"""
DAO de búsqueda sobre la vista combinada paciente-tarjeta-color.

Ejecuta consultas usando el patrón "Late Join" (Cruce Diferido) para máximo 
rendimiento en HDD y hardware antiguo. Primero aísla, filtra y pagina 
los IDs crudos en la tabla de `pacientes` (junto con `pacientes_fts` o `tarjetas`
si es necesario) y luego extrae los datos relacionales solo para la página actual.

Cambios v4:
    - Paginación "Late Join" que elimina el cuello de botella de ORDER BY/LIMIT
      sobre la vista pesada.
"""

import sqlite3
from models.busqueda import TarjetaSalida
from dao.conexion import ConexionDB
from utils.date_utils import formatear_fecha_para_mostrar, generar_patrones_busqueda_fecha

class BusquedaDAO:
    """DAO de búsqueda optimizada (Late Join)."""

    def __init__(self):
        self.db = ConexionDB()

    def _ejecutar_late_join(self, subquery_from_where: str, params: tuple = (), limit: int = None, offset: int = None) -> tuple[list[TarjetaSalida], int]:
        """Ejecuta una consulta paginada utilizando el patrón Late Join."""
        conn = self.db.obtener_conexion()
        cursor = conn.cursor()
        
        # 1. Contar totales sobre la tabla/filtro base
        count_query = f"SELECT COUNT(*) {subquery_from_where}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]

        # 2. Construir la paginación de IDs base
        base_query = f"""
            SELECT p.id, p.nombre1, p.nombre2, p.apellido1, p.apellido2,
                   p.cedula, p.fecha_nacimiento, p.lugar_nacimiento, p.estado_vital
            {subquery_from_where}
            ORDER BY p.apellido1, p.nombre1
        """
        if limit is not None:
            base_query += f" LIMIT {limit}"
        if offset is not None:
            base_query += f" OFFSET {offset}"

        # 3. Late Join final (se cruza SOLO la página seleccionada)
        late_join_query = f"""
            SELECT 
                base.id AS id_paciente, base.nombre1, base.nombre2, 
                base.apellido1, base.apellido2, COALESCE(base.cedula, 'S/C') AS cedula, 
                base.fecha_nacimiento, base.lugar_nacimiento, base.estado_vital,
                t.num_historia, c.valor AS color
            FROM ({base_query}) AS base
            JOIN tarjetas t ON base.id = t.id_paciente
            JOIN colores c ON c.id = t.id_color
            ORDER BY base.apellido1, base.nombre1
        """

        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(late_join_query, params)
        filas = cursor.fetchall()
        conn.close()

        resultados = []
        for fila in filas:
            datos = dict(fila)
            if datos.get("fecha_nacimiento"):
                datos["fecha_nacimiento"] = formatear_fecha_para_mostrar(datos["fecha_nacimiento"])
            resultados.append(TarjetaSalida(**datos))
            
        return resultados, total

    # ══════════════════════════════════════════════════════════════════
    #  CONSULTAS
    # ══════════════════════════════════════════════════════════════════

    def obtener_todos(self, limit: int = None, offset: int = None) -> tuple[list[TarjetaSalida], int]:
        return self._ejecutar_late_join(
            "FROM pacientes p WHERE p.estado = 1",
            (), limit, offset
        )

    def buscar_por_cedula(self, cedula: str, limit: int = None, offset: int = None) -> tuple[list[TarjetaSalida], int]:
        v = cedula.replace("'", "''").replace('"', '""')
        return self._ejecutar_late_join(
            "FROM pacientes p JOIN pacientes_fts fts ON p.id = fts.id_paciente WHERE p.estado = 1 AND pacientes_fts MATCH ?",
            (f'cedula: "{v}"',), limit, offset
        )

    def buscar_por_nombre(self, nombre: str, limit: int = None, offset: int = None) -> tuple[list[TarjetaSalida], int]:
        v = nombre.replace("'", "''").replace('"', '""')
        return self._ejecutar_late_join(
            "FROM pacientes p JOIN pacientes_fts fts ON p.id = fts.id_paciente WHERE p.estado = 1 AND pacientes_fts MATCH ?",
            (f'nombres: "{v}"',), limit, offset
        )

    def buscar_por_apellido(self, apellido: str, limit: int = None, offset: int = None) -> tuple[list[TarjetaSalida], int]:
        v = apellido.replace("'", "''").replace('"', '""')
        return self._ejecutar_late_join(
            "FROM pacientes p JOIN pacientes_fts fts ON p.id = fts.id_paciente WHERE p.estado = 1 AND pacientes_fts MATCH ?",
            (f'apellidos: "{v}"',), limit, offset
        )

    def buscar_por_nombre_completo(self, texto: str, limit: int = None, offset: int = None) -> tuple[list[TarjetaSalida], int]:
        palabras = texto.strip().split()
        if not palabras:
            return self.obtener_todos(limit, offset)

        match_query = " ".join([f'"{p}"' for p in palabras])
        return self._ejecutar_late_join(
            "FROM pacientes p JOIN pacientes_fts fts ON p.id = fts.id_paciente WHERE p.estado = 1 AND pacientes_fts MATCH ?",
            (match_query,), limit, offset
        )

    def buscar_por_fecha_nacimiento(self, fecha: str, limit: int = None, offset: int = None) -> tuple[list[TarjetaSalida], int]:
        valores = generar_patrones_busqueda_fecha(fecha)
        if not valores:
            return [], 0

        placeholders = " OR ".join(["p.fecha_nacimiento LIKE ?"] * len(valores))
        params = tuple(f"%{valor}%" for valor in valores)
        return self._ejecutar_late_join(
            f"FROM pacientes p WHERE p.estado = 1 AND ({placeholders})",
            params, limit, offset
        )

    def buscar_por_lugar_nacimiento(self, lugar: str, limit: int = None, offset: int = None) -> tuple[list[TarjetaSalida], int]:
        return self._ejecutar_late_join(
            "FROM pacientes p WHERE p.estado = 1 AND p.lugar_nacimiento LIKE ? COLLATE NOCASE",
            (f"%{lugar}%",), limit, offset
        )

    def buscar_por_num_historia(self, num_historia: str, limit: int = None, offset: int = None) -> tuple[list[TarjetaSalida], int]:
        return self._ejecutar_late_join(
            "FROM pacientes p JOIN tarjetas t ON p.id = t.id_paciente WHERE p.estado = 1 AND t.num_historia LIKE ?",
            (f"%{num_historia}%",), limit, offset
        )

    def buscar_multicriterio(self, filtros: dict, limit: int = None, offset: int = None) -> tuple[list[TarjetaSalida], int]:
        if not filtros:
            return self.obtener_todos(limit, offset)

        condiciones = ["p.estado = 1"]
        parametros = []
        
        usar_fts = False
        fts_match_parts = []

        v_cedula = filtros.get("cedula", "")
        if v_cedula and str(v_cedula).strip():
            usar_fts = True
            v = str(v_cedula).strip().replace('"', '""')
            fts_match_parts.append(f'cedula: "{v}"')
            
        v_nombre = filtros.get("nombre", "")
        if v_nombre and str(v_nombre).strip():
            usar_fts = True
            v = str(v_nombre).strip().replace('"', '""')
            fts_match_parts.append(f'nombres: "{v}"')
            
        v_apellido = filtros.get("apellido", "")
        if v_apellido and str(v_apellido).strip():
            usar_fts = True
            v = str(v_apellido).strip().replace('"', '""')
            fts_match_parts.append(f'apellidos: "{v}"')
            
        if usar_fts and fts_match_parts:
            condiciones.append("pacientes_fts MATCH ?")
            parametros.append(" AND ".join(fts_match_parts))

        for clave, valor in filtros.items():
            if valor is None or clave in ["cedula", "nombre", "apellido"]:
                continue

            if clave == "lugar_nacimiento":
                v = str(valor).strip()
                if v:
                    condiciones.append("p.lugar_nacimiento LIKE ? COLLATE NOCASE")
                    parametros.append(f"%{v}%")

            elif clave == "fecha_nacimiento":
                v = str(valor).strip()
                if v:
                    valores = generar_patrones_busqueda_fecha(v)
                    if valores:
                        condiciones.append("(" + " OR ".join(["p.fecha_nacimiento LIKE ?"] * len(valores)) + ")")
                        parametros.extend(f"%{valor_busqueda}%" for valor_busqueda in valores)

            elif clave == "fecha_nacimiento_partes":
                dia, mes, anio = valor
                if dia and str(dia).strip():
                    try:
                        val_dia = f"{int(dia):02d}"
                        condiciones.append("strftime('%d', p.fecha_nacimiento) = ?")
                        parametros.append(val_dia)
                    except ValueError: pass
                if mes and str(mes).strip():
                    try:
                        val_mes = f"{int(mes):02d}"
                        condiciones.append("strftime('%m', p.fecha_nacimiento) = ?")
                        parametros.append(val_mes)
                    except ValueError: pass
                if anio and str(anio).strip():
                    try:
                        val_anio = f"{int(anio):04d}"
                        condiciones.append("strftime('%Y', p.fecha_nacimiento) = ?")
                        parametros.append(val_anio)
                    except ValueError: pass

        # Si a pesar de evaluar los filtros, no quedó ninguna condición extra (más allá de p.estado = 1), entonces usamos obtener_todos()
        if len(condiciones) == 1:
            return self.obtener_todos(limit, offset)

        where = " AND ".join(condiciones)
        
        if usar_fts:
            from_where = f"FROM pacientes p JOIN pacientes_fts fts ON p.id = fts.id_paciente WHERE {where}"
        else:
            from_where = f"FROM pacientes p WHERE {where}"
            
        return self._ejecutar_late_join(from_where, tuple(parametros), limit, offset)
