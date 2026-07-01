# HidroSed SedGran v3.8.4 · Core Ordenado Secciones 3D QA

## Objetivo

Esta versión ordena la aplicación para recuperar un flujo operativo claro y proteger el motor de secciones, el perfil longitudinal 3D, la hidrología, la hidráulica, los sedimentos y la socavación.

## Modos de trabajo

La barra lateral incorpora tres modos:

1. **Operativo simple**: modo por defecto. Muestra el flujo principal y oculta herramientas avanzadas.
2. **Corrección / edición**: habilita edición de secciones, HEC-RAS Excel, sección compuesta rectangular/trapecial y herramientas de corrección.
3. **Experto / auditoría**: habilita diagnóstico técnico y auditorías avanzadas.

## Flujo principal protegido

1. Proyecto
2. DEM / Cuenca
3. Cuenca validada
4. Eje / Curvas
5. Secciones + Perfil 3D
6. Hidrología
7. Caudales
8. Hidráulica + Sedimentos
9. Exportación final

## Correcciones principales

- El motor v13 de secciones puede usar directamente el eje y las curvas activas de HidroSed, sin exigir carga manual de un KMZ externo.
- Se construye internamente un KML `hidrosed_eje_curvas_activos.kml` que contiene solo `LineString` de eje y curvas, evitando que un polígono sea tratado como eje.
- Las tablas técnicas de secciones quedan cerradas por defecto en listas desplegables.
- La herramienta de sección compuesta rectangular/trapecial queda disponible solo en modo Corrección / edición.
- Las auditorías avanzadas quedan ocultas en modo operativo simple.
- Se mantienen los módulos de hidrología, caudales, hidráulica conectada, sedimentos, socavación y exportación final.

## Uso recomendado

Para un flujo normal:

1. Cargar punto y/o geometría del proyecto.
2. Descargar o cargar DEM.
3. Delimitar y validar cuenca activa.
4. Generar o cargar eje y curvas.
5. Ir a **Secciones + Perfil 3D**.
6. Mantener motor v13 y fuente **Usar eje y curvas activos de HidroSed**.
7. Generar secciones v13 + QA.
8. Generar perfil previo 3D.
9. Calcular hidrología, caudales e hidráulica/sedimentos.

