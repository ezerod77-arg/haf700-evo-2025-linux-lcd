# Política transversal de changelog
Decisión del usuario: 27/10/2026. Zona horaria de nuevos hechos: America/Argentina/Buenos_Aires.
## Obligación
Todo proyecto propio debe tener CHANGELOG.md en la raíz. Si ya hay un changelog
canónico en docs/ u otra ubicación, la raíz lo enlaza explícitamente: no mantener dos
historias paralelas. Las bitácoras técnicas y registros de decisiones se conservan.
Antes de dar por cerrado un bloque de trabajo, actualizar el changelog del proyecto;
aplica a código, ingesta, contenido, infraestructura, configuración y documentación.
## Campos de cada entrada nueva
- ID estable, título y proyecto/componente.
- Inicio, última actualización y cierre cuando se conozcan, con hora y zona; si no
  constan: 'no documentado'. No sustituirlos por la hora del commit o del archivo.
- Objetivo y qué cambió concretamente; archivos, capacidades o entregables afectados.
- Estado explícito: planificado, implementado, probado técnicamente, aceptado por el
  usuario, bloqueado, pausado, descartado o sustituido. Pueden coexistir dimensiones.
- Validación: qué se ejecutó, cuándo, resultado, evidencia y límites. Si no se ejecutó,
  decirlo; terminar un script o una ingesta no certifica el producto completo.
- Fuentes: commits, bitácora, manifiesto, informe o ruta verificable sin secretos.
- Pendientes, impedimento, siguiente acción y condición de cierre.
## Reconstrucción del pasado
Indicar 'reconstruido' y la fecha de reconstrucción además de la fecha documentada
del hecho. Si solo se sabe el día, no inventar hora. Un commit registra una modificación,
no prueba su ejecución ni aceptación. Preservar procedencia de código importado.
No inventar fechas o porcentajes, convertir planes en hechos ni dar pendientes viejos
por actuales sin contrastar entradas posteriores. Las correcciones son entradas nuevas
que referencian y sustituyen a las anteriores; no borrar la historia.
## Conservación y publicación
No incluir credenciales, datos de clientes, historias clínicas ni datos personales
innecesarios. Registrar capacidades y evidencia operativa; las fuentes originales
permanecen donde corresponde. Mantener las bitácoras existentes y enlazarlas.
Versionar y subir solo rutas propias verificadas, conservar cambios ajenos y no forzar
push ni reescribir historial. Esta es una regla documental para agentes que la lean:
no se afirma que exista un bloqueo automático de commits.
## Plantilla
### [AAAA-MM-DD HH:MM -03:00] ID — título
- Inicio: no documentado. Última actualización: fecha conocida. Cierre: no documentado.
- Objetivo / cambio:
- Alcance / archivos:
- Estado de implementación:
- Validación y aceptación:
- Evidencia / fuentes:
- Pendientes / próximo paso / criterio de cierre:
