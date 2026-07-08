-- Se crea la BD y sus tablas

CREATE DATABASE aguapacha;

-- ---------- CREACIÓN DE TABLAS --------------

-- Tabla Servicios
CREATE TABLE servicios(
  id_servicio INT NOT NULL AUTO_INCREMENT,
  nombre_servicio VARCHAR(45) NOT NULL,
  PRIMARY KEY (id_servicio)
);

-- Tabla Departamentos
CREATE TABLE departamentos (
  id_dpto INT NOT NULL AUTO_INCREMENT,
  nombre_departamento VARCHAR(45) NOT NULL,
  PRIMARY KEY (id_dpto)
);

-- Tabla ciudades
CREATE TABLE ciudades(
	id_ciudad INT NOT NULL AUTO_INCREMENT,
	nombre_ciudad VARCHAR(45) NOT NULL,
	id_dpto INT NOT NULL,
	PRIMARY KEY (id_ciudad),
	FOREIGN KEY (id_dpto) REFERENCES departamentos(id_dpto)
);

-- Tipo de eventos
CREATE TABLE tipos_evento(
	id_tipo_evento INT NOT NULL AUTO_INCREMENT,
	tipo_evento VARCHAR(45) NOT NULL,
	PRIMARY KEY (id_tipo_evento)
);

-- Se crea la tabla de hechos AGENDA
CREATE TABLE eventos(
	id_evento INT NOT NULL AUTO_INCREMENT,
    fecha DATE NOT NULL,
    hora_inicio TIME NOT NULL DEFAULT '00:00',
    duracion DECIMAL(3,1) NOT NULL DEFAULT 0,
    direccion TEXT NOT NULL,
    id_ciudad INT NOT NULL,
    contacto_ppal VARCHAR(200) NOT NULL,
    contacto_sec VARCHAR(200) DEFAULT NULL,
    id_tipo_evento INT NOT NULL,
    id_servicio INT NOT NULL,
    observaciones TEXT,
    valor_venta INT NOT NULL,
	PRIMARY KEY (id_evento),
	FOREIGN KEY (id_ciudad) REFERENCES ciudades(id_ciudad),
    FOREIGN KEY (id_tipo_evento) REFERENCES tipos_evento(id_tipo_evento),
    FOREIGN KEY (id_servicio) REFERENCES servicios(id_servicio)
);

-- Se crea la tabla USUARIOS
CREATE TABLE usuarios(
	id_usuario INT NOT NULL AUTO_INCREMENT,
	usuario VARCHAR(100) NOT NULL,
    contrasena VARCHAR(100) NOT NULL,
    rol VARCHAR(45),
	PRIMARY KEY (id_usuario)
);

-- Se crea la tabla AUDITORIA
CREATE TABLE log_auditoria(
	id_log INT NOT NULL AUTO_INCREMENT,
    fecha_accion DATETIME DEFAULT CURRENT_TIMESTAMP,
	id_usuario INT NOT NULL,
    accion VARCHAR(100),
	PRIMARY KEY (id_log),
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
    );

