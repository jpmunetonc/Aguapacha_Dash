/*1. Creación de Vista Comercial - Simplificada:
 - Contiene información detallada de la tabla EVENTOS y sus relaciones (Mostrando nombres en vez de códigos).
 - Se unifica Municipio con su Departamento, para darle mejor uso en informes.*/
 
CREATE VIEW eventos_vista_comercial AS
SELECT 
	e.id_evento,
    e.fecha,
    e.hora_inicio,
    e.duracion,
    e.direccion,
    e.id_ciudad,
    CONCAT(c.nombre_ciudad,", ",d.nombre_departamento) AS ciudad,
    e.contacto_ppal,
    e.contacto_sec,
    e.id_tipo_evento,
    t.tipo_evento,
    e.id_servicio,
    s.nombre_servicio,
    e.observaciones,
    e.valor_venta
FROM eventos e
JOIN ciudades c ON c.id_ciudad = e.id_ciudad
JOIN departamentos d ON d.id_dpto = c.id_dpto
JOIN tipos_evento t ON t.id_tipo_evento = e.id_tipo_evento
JOIN servicios s ON s.id_servicio = e.id_servicio;

-- Se trae la vista con la información
SELECT * FROM eventos_vista_comercial;


/*2. Creación de Vista Ocupación:
 - Muestra el total de eventos agrupados por fecha y ciudad.
 - Sabemos como se manejó operativamente cada día y cuáles fueron los picos*/

CREATE VIEW eventos_ocupacion_fechas AS
SELECT 
	fecha, 
	ciudad, 
	COUNT(*) AS total_eventos 
FROM eventos_vista_comercial
GROUP BY fecha, ciudad;

-- Se trae la vista con la información
SELECT * FROM eventos_ocupacion_fechas;


/*3. Procedimiento almacenado RESUMEN COMERCIAL POR FECHAS
- Muestra la CANTIDAD, TOTAL VENTAS y PROMEDIO DE VENTAS, acorde a un rango de fechas
*/

DELIMITER $$
CREATE PROCEDURE sp_resumen_comercial_fechas(fecha_inicio date, fecha_fin date)
BEGIN
	SELECT 
		COUNT(*) AS total_eventos,
		IFNULL(SUM(valor_venta), 0) AS total_ventas,
		IFNULL(AVG(valor_venta), 0) as promedio_ventas
	FROM eventos
	WHERE fecha >= fecha_inicio AND fecha <= fecha_fin;
END $$
DELIMITER ;

-- Se ejecuta el Procedimiento
CALL sp_resumen_comercial_fechas("2017-01-01","2017-12-31"); -- 2017
CALL sp_resumen_comercial_fechas("2022-01-01","2022-12-31"); -- 2022
CALL sp_resumen_comercial_fechas("2026-01-01","2026-12-31"); -- 2026
CALL sp_resumen_comercial_fechas("2027-01-01","2027-12-31"); -- 2027 debe arrojar 0 en todo


/*4. TRIGGER y FUNCTION: Para tener registro de auditoría cada vez que se haga un insert en la tabla EVENTOS*/

-- Se crea una función para validar si es una carga masiva o individual
DELIMITER $$
CREATE FUNCTION fn_eventos_carga_masiva() 
RETURNS TINYINT(1)
DETERMINISTIC
BEGIN
    IF (@carga_masiva IS NOT NULL AND @carga_masiva = 1) THEN
        RETURN 1;
    ELSE
        RETURN 0;
    END IF;
END $$
DELIMITER ;

/*Se crea el Trigger que se prende cada vez que se inserta, 
revisa si es carga masiva o no con la function creada 
luego inserta el registro correspondiente en log_auditoria*/

DELIMITER $$
CREATE TRIGGER trg_auditoria_eventos_insert
AFTER INSERT ON eventos
FOR EACH ROW
BEGIN
    -- Si la función retorna 0, significa que NO es masivo (es una acción manual)
    IF (fn_eventos_carga_masiva() = 0) THEN
        INSERT INTO log_auditoria (fecha_accion, usuario, accion)
        VALUES (NOW(), CURRENT_USER(), CONCAT('Inserción manual de evento. Fecha: ', NEW.fecha));
    END IF;
END $$
DELIMITER ;


