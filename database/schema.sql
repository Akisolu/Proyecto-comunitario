BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "colores" (
	"id"	INTEGER,
	"valor"	TEXT NOT NULL,
	"estado"	INTEGER NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "pacientes" (
	"id"	INTEGER,
	"nombre1"	TEXT NOT NULL,
	"nombre2"	TEXT,
	"apellido1"	TEXT NOT NULL,
	"apellido2"	TEXT,
	"cedula"	TEXT,
	"lugar_nacimiento"	TEXT NOT NULL,
	"fecha_nacimiento"	TEXT NOT NULL,
	"estado_vital"	INTEGER NOT NULL,
	"estado"	INTEGER NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "tarjetas" (
	"id"	INTEGER,
	"num_historia"	TEXT NOT NULL UNIQUE,
	"id_paciente"	INTEGER NOT NULL,
	"id_color"	INTEGER NOT NULL,
	"estado"	INTEGER NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("id_color") REFERENCES "colores"("id"),
	FOREIGN KEY("id_paciente") REFERENCES "pacientes"("id")
);
CREATE TABLE IF NOT EXISTS "usuarios" (
	"id"	INTEGER,
	"nombre"	TEXT NOT NULL,
	"apellido"	TEXT NOT NULL,
	"cedula"	INTEGER NOT NULL UNIQUE,
	"usuario"	TEXT NOT NULL UNIQUE,
	"clave"	TEXT NOT NULL,
	"estado"	INTEGER,
	"pregunta1" TEXT,
	"respuesta1" TEXT,
	"pregunta2" TEXT,
	"respuesta2" TEXT,
	"pregunta3" TEXT,
	"respuesta3" TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE VIEW IF NOT EXISTS vista_paciente_tarjeta AS
SELECT
    pacientes.id AS id_paciente,
    pacientes.nombre1,
    pacientes.nombre2,
    pacientes.apellido1,
    pacientes.apellido2,
    COALESCE(pacientes.cedula, 'S/C') AS cedula,
    pacientes.fecha_nacimiento,
    pacientes.lugar_nacimiento,
    pacientes.estado_vital,
    tarjetas.num_historia,
    colores.valor AS color
FROM pacientes
JOIN tarjetas ON pacientes.id = tarjetas.id_paciente
JOIN colores ON colores.id = tarjetas.id_color
WHERE pacientes.estado = 1;
CREATE INDEX IF NOT EXISTS "idx_historias_id_paciente" ON "tarjetas" (
	"id_paciente"
);
CREATE VIRTUAL TABLE IF NOT EXISTS pacientes_fts USING fts5(
    id_paciente UNINDEXED, 
    nombres, 
    apellidos, 
    cedula,
    tokenize="trigram"
);
CREATE TRIGGER IF NOT EXISTS pacientes_ai AFTER INSERT ON pacientes
BEGIN
  INSERT INTO pacientes_fts(rowid, id_paciente, nombres, apellidos, cedula) 
  VALUES (new.id, new.id, new.nombre1 || ' ' || COALESCE(new.nombre2, ''), new.apellido1 || ' ' || COALESCE(new.apellido2, ''), new.cedula);
END;

CREATE TRIGGER IF NOT EXISTS pacientes_ad AFTER DELETE ON pacientes
BEGIN
  DELETE FROM pacientes_fts WHERE rowid = old.id;
END;

CREATE TRIGGER IF NOT EXISTS pacientes_au AFTER UPDATE ON pacientes
BEGIN
  DELETE FROM pacientes_fts WHERE rowid = old.id;
  INSERT INTO pacientes_fts(rowid, id_paciente, nombres, apellidos, cedula)
  VALUES (new.id, new.id, new.nombre1 || ' ' || COALESCE(new.nombre2, ''), new.apellido1 || ' ' || COALESCE(new.apellido2, ''), new.cedula);
END;
CREATE UNIQUE INDEX IF NOT EXISTS "idx_pacientes_numero_cedula" ON "pacientes" (
	"cedula"
);
CREATE INDEX IF NOT EXISTS "idx_pacientes_primer_apellido" ON "pacientes" (
	"apellido1"
);
CREATE INDEX IF NOT EXISTS "idx_pacientes_primer_nombre" ON "pacientes" (
	"nombre1"
);
CREATE INDEX IF NOT EXISTS "idx_usuarios_primer_apellido" ON "usuarios" (
	"apellido"
);
CREATE INDEX IF NOT EXISTS "idx_usuarios_primer_nombre" ON "usuarios" (
	"nombre"
);
CREATE TABLE IF NOT EXISTS "servicios" (
	"id"	INTEGER,
	"nombre"	TEXT NOT NULL UNIQUE,
	"total_camas"	INTEGER NOT NULL,
	"estado"	INTEGER NOT NULL DEFAULT 1,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "ingresos" (
	"id"	INTEGER,
	"id_paciente"	INTEGER NOT NULL UNIQUE,
	"id_servicio"	INTEGER NOT NULL,
	"fecha_ingreso"	TEXT NOT NULL,
	"estado"	INTEGER NOT NULL DEFAULT 1,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("id_paciente") REFERENCES "pacientes"("id"),
	FOREIGN KEY("id_servicio") REFERENCES "servicios"("id")
);
CREATE INDEX IF NOT EXISTS "idx_ingresos_servicio" ON "ingresos" (
	"id_servicio"
);
CREATE INDEX IF NOT EXISTS "idx_ingresos_paciente" ON "ingresos" (
	"id_paciente"
);
CREATE INDEX IF NOT EXISTS "idx_pacientes_estado" ON "pacientes" (
	"estado"
);
CREATE INDEX IF NOT EXISTS "idx_pacientes_apellidos_nombres" ON "pacientes" (
	"apellido1", "nombre1", "estado"
);
COMMIT;
