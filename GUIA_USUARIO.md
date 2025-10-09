# 🏠 TECHO CHILE - Sistema de Seguimiento de Incidentes

## 📋 Descripción General

El Sistema de Seguimiento de Incidentes de TECHO CHILE es una plataforma web desarrollada en Django que permite gestionar y dar seguimiento a las observaciones reportadas en los proyectos de vivienda. El sistema facilita la comunicación entre beneficiarios, constructoras, TECHO y organismos gubernamentales para resolver incidencias de manera eficiente.

## 🎯 Objetivos del Sistema

- **Centralizar** el reporte y seguimiento de observaciones en viviendas
- **Facilitar** la comunicación entre todos los actores involucrados
- **Mejorar** los tiempos de respuesta y resolución de incidencias
- **Generar** reportes y métricas para la toma de decisiones
- **Transparentar** el proceso de gestión de calidad de las viviendas

---

## 👥 Roles y Permisos

### 🏛️ **ADMINISTRADOR**
**Acceso:** Completo al sistema
- ✅ Gestionar todos los módulos del sistema
- ✅ Crear, editar y eliminar proyectos, viviendas y observaciones
- ✅ Administrar usuarios y roles
- ✅ Cambiar estados de observaciones
- ✅ Generar reportes completos
- ✅ Acceso al panel maestro

**Usuario de ejemplo:**
- **Email:** admin@techo.cl
- **Contraseña:** admin123
- **Nombre:** Administrador Sistema

### 🏢 **TECHO**
**Acceso:** Gestión operativa y supervisión
- ✅ Ver todos los proyectos asignados
- ✅ Crear y gestionar observaciones
- ✅ Cambiar estados de observaciones
- ✅ Asignar constructoras a proyectos
- ✅ Generar reportes de seguimiento
- ❌ No puede eliminar proyectos

**Usuario de ejemplo:**
- **Email:** coordinador@techo.cl
- **Contraseña:** techo123
- **Nombre:** María González Coordinadora

### 🏗️ **CONSTRUCTORA**
**Acceso:** Gestión de observaciones de sus proyectos
- ✅ Ver proyectos asignados a su empresa
- ✅ Responder a observaciones
- ✅ Subir evidencias de reparaciones
- ✅ Cambiar estado a "En proceso" o "Cerrada"
- ❌ No puede crear nuevas observaciones
- ❌ Solo ve sus proyectos asignados

**Usuario de ejemplo:**
- **Email:** supervisor@constructora.cl
- **Contraseña:** const123
- **Nombre:** Carlos Mendoza Supervisor
- **Empresa:** Constructora Ejemplo S.A.

### 🏛️ **SERVIU**
**Acceso:** Solo lectura y reportes
- ✅ Ver todos los proyectos y observaciones
- ✅ Descargar reportes de estado
- ✅ Consultar métricas y estadísticas
- ❌ No puede crear observaciones
- ❌ No puede cambiar estados
- ❌ Solo consulta y descarga de información

**Usuario de ejemplo:**
- **Email:**inspector@serviu.cl 
- **Contraseña:** serviu123
- **Nombre:** Ana Rodríguez Inspector SERVIU

### 👨‍👩‍👧‍👦 **FAMILIA**
**Acceso:** Dashboard personal y reporte de observaciones
- ✅ Ver información de su vivienda
- ✅ Crear nuevas observaciones
- ✅ Ver historial de sus observaciones
- ✅ Subir fotos de problemas detectados
- ❌ No puede cambiar estados de observaciones
- ❌ Solo ve información de su vivienda

**Usuario de ejemplo:**
- **Email:** familia@beneficiario.cl
- **Contraseña:** familia123
- **Nombre:** Juan Pérez Familia
- **RUT:** 12345678-9

---

## 🚀 Funcionalidades Principales

### 📊 **Dashboard Personalizado**
Cada usuario ve un dashboard adaptado a su rol:
- **Métricas relevantes** según su nivel de acceso
- **Gráficos interactivos** de progreso
- **Accesos rápidos** a funciones principales
- **Notificaciones** de observaciones urgentes

### 🏠 **Gestión de Proyectos**
- Registro de proyectos habitacionales
- Asignación de viviendas a beneficiarios
- Control de tipologías y especificaciones
- Seguimiento de avance de construcción

### 🔍 **Sistema de Observaciones**
- **Creación:** Reportar problemas con fotos y descripción detallada
- **Seguimiento:** Estados: Abierta → En Proceso → Cerrada
- **Priorización:** Normal, Alta, Urgente (con tiempos de vencimiento automáticos)
- **Comunicación:** Comentarios y actualizaciones entre actores
- **Evidencias:** Subida de archivos (fotos, documentos, videos)

### 📋 **Flujo de Trabajo**
1. **Familia** reporta observación con fotos
2. **TECHO** valida y asigna a constructora
3. **Constructora** recibe notificación y planifica reparación
4. **Constructora** ejecuta trabajo y sube evidencia
5. **TECHO** verifica calidad y cierra observación
6. **SERVIU** monitorea todo el proceso

### 📈 **Reportes y Métricas**
- Dashboard con KPIs en tiempo real
- Reportes por proyecto, constructora o período
- Métricas de tiempo de resolución
- Indicadores de calidad y satisfacción
- Exportación a Excel/PDF

---

## 💻 **Acceso al Sistema**

### 🌐 **URL del Sistema**
```
http://127.0.0.1:8000/
```

### 🔐 **Proceso de Login**
1. Ingresar email y contraseña
2. El sistema redirige automáticamente según el rol:
   - **Familia** → Dashboard personal "Mi Vivienda"
   - **Otros roles** → Dashboard de gestión con métricas

### 📱 **Características Técnicas**
- **Framework:** Django 4.2.7
- **Base de datos:** SQLite (desarrollo) / PostgreSQL (producción)
- **Frontend:** Bootstrap 5.3 + JavaScript
- **Responsive:** Optimizado para móviles y tablets
- **Archivos:** Soporte para imágenes, PDF, documentos

---

## 🛠️ **Casos de Uso Típicos**

### 📝 **Familia reporta problema de humedad**
1. Login como `familia@beneficiario.cl`
2. Clic en "Nueva Observación"
3. Completar formulario:
   - Recinto: "Dormitorio principal"
   - Elemento: "Muro norte"
   - Descripción: "Mancha de humedad en esquina"
   - Subir fotos del problema
4. Sistema asigna automáticamente fecha de vencimiento
5. Notificación automática a TECHO

### 🔧 **Constructora responde a observación**
1. Login como `supervisor@constructora.cl`
2. Ver observaciones pendientes en dashboard
3. Abrir observación específica
4. Cambiar estado a "En Proceso"
5. Agregar comentario con plan de trabajo
6. Ejecutar reparación
7. Subir evidencia fotográfica de trabajo terminado
8. Cambiar estado a "Cerrada"

### 📊 **SERVIU consulta reportes**
1. Login como `inspector@serviu.cl`
2. Acceder a sección de reportes
3. Filtrar por período, región o proyecto
4. Visualizar métricas de calidad
5. Descargar reporte detallado en Excel

---

## ⚙️ **Configuración y Administración**

### 👤 **Gestión de Usuarios**
- Panel de administración en `/admin/`
- Creación de usuarios por rol
- Asignación de permisos específicos
- Activación/desactivación de cuentas

### 🏗️ **Configuración de Proyectos**
- Registro de constructoras
- Creación de tipologías de vivienda
- Definición de recintos y elementos
- Configuración de tiempos de vencimiento

### 🔧 **Mantenimiento del Sistema**
- Backup automático de base de datos
- Monitoreo de archivos subidos
- Limpieza de archivos temporales
- Actualización de estados automáticos

---

## 📞 **Soporte y Contacto**

### 🆘 **Problemas Técnicos**
- **Email:** soporte@techo.cl
- **Teléfono:** +56 2 2345 6789

### 📚 **Capacitación**
- Videos tutoriales disponibles en el sistema
- Manuales específicos por rol
- Sesiones de capacitación online

### 🔄 **Actualizaciones**
- Nuevas funcionalidades se notifican por email
- Changelog disponible en `/admin/`
- Mantenimientos programados los domingos

---

## 🎯 **Beneficios del Sistema**

### ✅ **Para las Familias**
- Comunicación directa y transparente
- Seguimiento en tiempo real de reparaciones
- Historial completo de su vivienda
- Proceso simplificado para reportar problemas

### ✅ **Para TECHO**
- Centralización de la gestión de calidad
- Métricas para mejorar procesos
- Mejor comunicación con beneficiarios
- Control de tiempos de respuesta

### ✅ **Para Constructoras**
- Organización eficiente de reparaciones
- Evidencia documentada de trabajos
- Comunicación clara de requerimientos
- Seguimiento de performance

### ✅ **Para SERVIU**
- Supervisión completa del proceso
- Reportes detallados para evaluación
- Transparencia en la gestión
- Datos para políticas públicas

---

*Sistema desarrollado para TECHO CHILE - Versión 2025*
*Última actualización: Octubre 2025*