# Migración de WeasyPrint a xhtml2pdf

## Fecha: 21 de noviembre de 2025

## Resumen
Se ha migrado completamente el sistema de generación de PDFs desde WeasyPrint a xhtml2pdf para eliminar la dependencia de librerías nativas de Windows (GTK, Cairo, etc.) y facilitar el despliegue.

## Archivos Modificados

### 1. core/views_dashboard_pdf.py
- **Cambio**: Reemplazado `weasyprint.HTML()` por `xhtml2pdf.pisa.CreatePDF()`
- **Función afectada**: `dashboard_pdf_report()`
- **Beneficio**: Generación de reportes del dashboard sin dependencias externas

### 2. reportes/views.py
- **Cambio**: Reemplazado WeasyPrint por xhtml2pdf en generación de actas
- **Función afectada**: `descargar_acta_pdf()`
- **Beneficio**: Actas de recepción generadas sin problemas en Windows

### 3. ficha_postventa/views.py
- **Cambio**: Eliminado import de `weasyprint.HTML`, agregado xhtml2pdf
- **Función afectada**: `generar_pdf()`
- **Beneficio**: PDFs de fichas postventa funcionan en cualquier entorno

### 4. requirements.txt
- **Eliminado**: `weasyprint==62.3`
- **Agregado**: `xhtml2pdf==0.2.16`

### 5. WeasyPrint.txt
- Actualizado con documentación sobre xhtml2pdf y sus ventajas

## Ventajas de xhtml2pdf

1. ✅ **100% compatible con Windows** - No requiere GTK, Cairo ni librerías nativas
2. ✅ **Instalación simple** - Solo `pip install xhtml2pdf`
3. ✅ **Mismo formato visual** - Mantiene el diseño de los reportes
4. ✅ **Sin configuración adicional** - Funciona inmediatamente después de instalar
5. ✅ **Portabilidad** - Funciona en Windows, Linux y macOS sin cambios

## Instalación

```bash
# Desinstalar WeasyPrint (si está instalado)
pip uninstall weasyprint -y

# Instalar xhtml2pdf
pip install xhtml2pdf==0.2.16
```

## Pruebas Realizadas

- ✅ Generación de reportes del dashboard
- ✅ Descarga de actas de recepción en PDF
- ✅ Generación de PDFs de fichas postventa
- ✅ Caché de reportes funcionando correctamente

## Notas

- Los PDFs mantienen el mismo formato visual que con WeasyPrint
- xhtml2pdf tiene algunas limitaciones con CSS avanzado (flexbox, grid), pero para nuestros reportes funciona perfectamente
- Si en el futuro se necesitan capacidades CSS más avanzadas, se puede considerar alternativas como reportlab o playwright
- El sistema mantiene el fallback a ReportLab en caso de errores

## Próximos Pasos

- [x] Migración completa de WeasyPrint a xhtml2pdf
- [x] Actualización de documentación
- [x] Pruebas de generación de PDFs
- [ ] Validar en producción
- [ ] Monitorear rendimiento y calidad de PDFs

## Soporte

Si encuentras algún problema con la generación de PDFs, revisa:
1. Que xhtml2pdf esté instalado: `pip list | grep xhtml2pdf`
2. Los logs de errores en la consola
3. El archivo MIGRACION_XHTML2PDF.md para más detalles
