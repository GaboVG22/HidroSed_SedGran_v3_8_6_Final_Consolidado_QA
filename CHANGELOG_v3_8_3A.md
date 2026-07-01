# HidroSed v3.8.3A · Hotfix descarga KMZ Streamlit

## Corrección aplicada

- Se corrigió `StreamlitDuplicateElementId` en los botones de descarga `eje_cauce_cuenca.kmz`.
- Se asignaron claves explícitas y únicas a las descargas oficiales y de compatibilidad.
- Se mantiene la exportación ordenada recomendada en dos salidas principales:
  - `eje_cauce_cuenca.kmz`
  - `cuenca_eje_curvas_unificado.kmz`
- La descarga avanzada queda como respaldo de compatibilidad, sin interferir con la descarga oficial.

## Nota técnica

El error se producía porque Streamlit encontraba dos `download_button` con la misma etiqueta y el mismo nombre de archivo durante la misma renderización. Aunque las descargas pertenecían a paneles distintos, Streamlit calculaba el mismo identificador interno. La solución fue asignar `key` único a cada botón.
