# HidroSed v3.8.6 · Final consolidado de mejoras

Versión aplicada sobre v3.8.5 Hotfix Casos/Lámina.

## Enfoque
- Mantiene el núcleo operativo: secciones v13, perfil longitudinal 3D, hidrología, hidráulica, sedimentos y socavación.
- Ordena la aplicación para separar cuenca topográfica de soporte, subcuenca hidrológica y eje hidráulico.
- Reduce sobrecarga visual mediante expanders cerrados, trazabilidad por etapa y botones de avance.

## Mejoras aplicadas
1. Nombre de proyecto actual en barra lateral y pestaña Proyecto.
2. Nomenclatura automática para archivos KMZ, CSV, XLSX, HTML y lámina PNG.
3. Flujo oficial consolidado de 19 etapas en tabla desplegable.
4. Trazabilidad geométrica por etapa: cuenca topográfica, subcuenca hidrológica, eje hidráulico, curvas simples, curvas interpoladas y curvas externas.
5. Parámetros actualizados de cuenca activa tras validación/corrección.
6. Pestaña de eje/curvas renombrada y reforzada como “Eje del cauce / eje hidráulico”.
7. Análisis estadístico hidrológico con distribuciones: Normal, Log-Normal, Gumbel, Pearson III, Log-Pearson III, Gamma, Weibull y GEV.
8. Ranking por AIC, BIC, KS, RMSE y MAE, con parámetros y valores por período de retorno.
9. Registro de caudales agregados por km del eje con acumulación aguas abajo.
10. Descargas principales con nombre del proyecto.
11. Exportación Excel avanzada con hojas de análisis hidrológico estadístico.
12. Lámina cartográfica con título asociado al proyecto.
13. Paneles de trazabilidad y alertas técnicas cerrados por defecto al final de cada etapa.
14. Se mantienen cuatro casos cuenca–eje y las imágenes referenciales existentes.

## Limitaciones conocidas
- El entorno de sandbox no tiene instalado `streamlit`, por lo que la prueba visual interactiva no pudo ejecutarse aquí.
- Sí se verificaron compilación, pruebas unitarias/funcionales, integridad de módulos, exportaciones principales y enlaces estáticos.
