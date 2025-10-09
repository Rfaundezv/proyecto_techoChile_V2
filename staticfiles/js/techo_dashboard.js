// Dashboard JavaScript mejorado para Techo Chile
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar funcionalidades
    initializeThemeToggle();
    initializeTooltips();
    setupDynamicForms();
    initializeAnimations();

    // Auto-hide alerts
    setTimeout(hideAlerts, 5000);
});

// Toggle de modo oscuro/claro
function initializeThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    const currentTheme = localStorage.getItem('theme') || 'light';

    // Aplicar tema guardado
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateToggleIcon(currentTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateToggleIcon(newTheme);

            // Animar transición
            document.body.style.transition = 'all 0.3s ease';
            setTimeout(() => {
                document.body.style.transition = '';
            }, 300);
        });
    }
}

function updateToggleIcon(theme) {
    const toggle = document.getElementById('theme-toggle');
    if (toggle) {
        toggle.innerHTML = theme === 'dark' ? '☀️' : '🌙';
        toggle.title = theme === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro';
    }
}

// Inicializar tooltips de Bootstrap
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Formularios dinámicos mejorados
function setupDynamicForms() {
    // Región -> Comuna
    const regionSelect = document.getElementById('id_region');
    const comunaSelect = document.getElementById('id_comuna');

    if (regionSelect && comunaSelect) {
        regionSelect.addEventListener('change', function() {
            const regionId = this.value;
            updateSelect(comunaSelect, 'Cargando comunas...');

            if (regionId) {
                fetch(`/ajax/comunas/?region_id=${regionId}`)
                    .then(response => response.json())
                    .then(data => {
                        populateSelect(comunaSelect, data.comunas, 'Seleccionar comuna');
                    })
                    .catch(() => {
                        populateSelect(comunaSelect, [], 'Error al cargar comunas');
                    });
            } else {
                populateSelect(comunaSelect, [], 'Seleccionar comuna');
            }
        });
    }

    // Proyecto -> Viviendas y Recintos
    const proyectoSelect = document.getElementById('id_proyecto');
    const viviendaSelect = document.getElementById('id_vivienda');
    const recintoSelect = document.getElementById('id_recinto');

    if (proyectoSelect) {
        proyectoSelect.addEventListener('change', function() {
            const proyectoId = this.value;

            // Actualizar viviendas
            if (viviendaSelect) {
                updateSelect(viviendaSelect, 'Cargando viviendas...');

                if (proyectoId) {
                    fetch(`/incidencias/ajax/viviendas/?proyecto_id=${proyectoId}`)
                        .then(response => response.json())
                        .then(data => {
                            const viviendas = data.viviendas.map(v => ({
                                id: v.id,
                                nombre: `Vivienda ${v.codigo}`
                            }));
                            populateSelect(viviendaSelect, viviendas, 'Seleccionar vivienda');
                        })
                        .catch(() => {
                            populateSelect(viviendaSelect, [], 'Error al cargar viviendas');
                        });
                } else {
                    populateSelect(viviendaSelect, [], 'Seleccionar vivienda');
                }
            }

            // Actualizar recintos
            if (recintoSelect) {
                updateSelect(recintoSelect, 'Cargando recintos...');

                if (proyectoId) {
                    fetch(`/incidencias/ajax/recintos/?proyecto_id=${proyectoId}`)
                        .then(response => response.json())
                        .then(data => {
                            populateSelect(recintoSelect, data.recintos, 'Seleccionar recinto');
                        })
                        .catch(() => {
                            populateSelect(recintoSelect, [], 'Error al cargar recintos');
                        });
                } else {
                    populateSelect(recintoSelect, [], 'Seleccionar recinto');
                }
            }
        });
    }
}

// Funciones auxiliares para selects dinámicos
function updateSelect(selectElement, loadingText) {
    selectElement.innerHTML = `<option value="">${loadingText}</option>`;
    selectElement.disabled = true;
}

function populateSelect(selectElement, options, emptyText) {
    selectElement.innerHTML = `<option value="">${emptyText}</option>`;
    options.forEach(function(option) {
        const optionElement = document.createElement('option');
        optionElement.value = option.id;
        optionElement.textContent = option.nombre;
        selectElement.appendChild(optionElement);
    });
    selectElement.disabled = false;
}

// Inicializar animaciones
function initializeAnimations() {
    // Observer para animaciones al hacer scroll
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = 'fadeInUp 0.6s ease-out';
            }
        });
    });

    // Observar elementos que se animan
    document.querySelectorAll('.chart-container, .form-techo').forEach(el => {
        observer.observe(el);
    });

    // Efectos hover para tarjetas métricas
    document.querySelectorAll('.metric-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px) scale(1.02)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
}

// Ocultar alertas automáticamente
function hideAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        if (bootstrap && bootstrap.Alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    });
}

// Función para confirmar eliminación
function confirmarEliminacion(mensaje) {
    return confirm(mensaje || '¿Estás seguro de que quieres eliminar este elemento?');
}

// Función para mostrar/ocultar elementos
function toggleElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = element.style.display === 'none' ? 'block' : 'none';
    }
}

// Función para actualizar métricas en tiempo real (para futuro uso con WebSockets)
function updateMetrics(data) {
    Object.keys(data).forEach(key => {
        const element = document.querySelector(`[data-metric="${key}"]`);
        if (element) {
            const currentValue = parseInt(element.textContent);
            const newValue = data[key];
            animateNumber(element, currentValue, newValue);
        }
    });
}

// Animar números en las métricas
function animateNumber(element, start, end, duration = 1000) {
    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current);
    }, 16);
}

// Exportar funciones para uso global
window.TechoApp = {
    updateMetrics,
    confirmarEliminacion,
    toggleElement
};
