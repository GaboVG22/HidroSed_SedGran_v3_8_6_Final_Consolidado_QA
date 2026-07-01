# HidroSed v3.8.5 · Hotfix casos visibles y lámina cartográfica activa

## Correcciones aplicadas

1. Se restituyó la visibilidad permanente de los cuatro casos cuenca–eje.
   - Selector siempre visible en barra lateral.
   - Resumen del caso activo en encabezado operativo.
   - Tabla de los 4 casos en desplegable superior.
   - Imagen referencial del caso activo en barra lateral.

2. Se corrigió la lámina cartográfica.
   - Ya no se genera una lámina basada solo en la extensión completa del DEM.
   - Requiere cuenca activa para evitar salidas cartográficas engañosas.
   - El DEM se enmascara fuera del polígono de cuenca activa.
   - Las curvas visibles de la lámina se dibujan recortadas al polígono de cuenca activa.
   - La vista se centra en la delimitación de la cuenca, no en todo el DEM.
   - La lámina indica si se usó cuenca activa y si las curvas fueron recortadas al polígono.

3. Se mantiene el orden operativo de v3.8.4.
   - No se alteró el motor v13 de secciones.
   - No se alteraron los módulos de hidrología, hidráulica, sedimentos, socavación ni perfil 3D.

## Archivos modificados

- app.py
- modules/cartographic_output.py
- tests/test_v385_cases_lamina.py
