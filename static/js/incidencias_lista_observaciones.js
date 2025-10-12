document.addEventListener('DOMContentLoaded', function() {
    let observacionIdActual = null;
    let modalCambioEstado = document.getElementById('modalCambioEstado');

    // Forzar dark-mode al abrir el modal
    modalCambioEstado.addEventListener('show.bs.modal', function() {
        document.body.classList.add('dark-mode');
    });
    // Remover dark-mode al cerrar el modal
    modalCambioEstado.addEventListener('hidden.bs.modal', function() {
        document.body.classList.remove('dark-mode');
    });

    // Manejar click en botones de cambiar estado
    document.querySelectorAll('.cambiar-estado-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            observacionIdActual = this.dataset.obsId;
        });
    });

    // Manejar click en badges de estado (cambio rápido)
    document.querySelectorAll('.estado-badge').forEach(badge => {
        badge.addEventListener('click', function() {
            observacionIdActual = this.dataset.obsId;
            const modal = new bootstrap.Modal(document.getElementById('modalCambioEstado'));
            modal.show();
        });
    });

    // Confirmar cambio de estado
    document.getElementById('confirmarCambioEstado').addEventListener('click', function() {
        if (!observacionIdActual) return;

        const estado = document.getElementById('nuevoEstado').value;
        const comentario = document.getElementById('comentario').value;

        if (!estado) {
            alert('Debe seleccionar un estado');
            return;
        }

        // Realizar cambio via AJAX
        fetch(`/incidencias/${observacionIdActual}/cambiar-estado/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: new URLSearchParams({
                estado: estado,
                comentario: comentario
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Actualizar badge en la tabla
                const badge = document.getElementById(`estado-badge-${observacionIdActual}`);
                badge.textContent = data.nuevo_estado.nombre;
                badge.className = `badge ${data.nuevo_estado.badge_class} estado-badge`;

                // Cerrar modal y limpiar
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalCambioEstado'));
                modal.hide();
                document.getElementById('formCambioEstado').reset();

                // Mostrar mensaje de éxito
                showAlert('success', data.message);
            } else {
                showAlert('danger', data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('danger', 'Error al cambiar el estado');
        });
    });

    function showAlert(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
        alertDiv.style.zIndex = '9999';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alertDiv);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
});
