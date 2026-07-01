# CHANGELOG v3.8.4

## Cambios de interfaz

- Se cambió el encabezado a **HidroSed Core Ordenado · v3.8.4**.
- Se agregaron modos de trabajo: Operativo simple, Corrección / edición y Experto / auditoría.
- Se reorganizaron pestañas con nombres más claros y centrados en el flujo real de trabajo.
- Se ocultaron paneles avanzados en modo operativo simple.
- Diagnósticos y tablas técnicas quedan en `st.expander` cerrado por defecto.

## Cambios funcionales

- Nuevo constructor interno de KML para secciones v13 usando eje y curvas activos.
- El KML interno excluye polígonos y metadatos para evitar que se descarguen o interpreten como eje del cauce.
- El motor v13 ya no depende exclusivamente de una carga manual externa para generar secciones.
- La selección de eje prioriza automáticamente nombres tipo `EJE_CAUCE_HIDROSED`, `EJE` o `CAUCE`.
- Se preservan hidrología, caudales, hidráulica, sedimentos y socavación.
- Se agregaron claves únicas a descargas relevantes de secciones v13.

## Pruebas agregadas

- `tests/test_v384_core_ordered_sections3d.py`
  - Smoke test de motor v13 con eje + curvas y perfil 3D.
  - Smoke test de hidráulica/sedimentos con secciones sintéticas.

