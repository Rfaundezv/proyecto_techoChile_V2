document.addEventListener('DOMContentLoaded', function() {
    const rolField = document.getElementById('id_rol');
    const constructoraRow = document.querySelector('.form-row.field-constructora, .field-constructora').closest('.form-row, .field-constructora');
    
    function toggleConstructoraField() {
        if (rolField && constructoraRow) {
            const selectedOption = rolField.options[rolField.selectedIndex];
            const selectedText = selectedOption ? selectedOption.text : '';
            
            if (selectedText.includes('Constructora') || selectedText.includes('CONSTRUCTORA')) {
                constructoraRow.style.display = '';
            } else {
                constructoraRow.style.display = 'none';
                // Limpiar el campo si no es constructora
                const constructoraField = document.getElementById('id_constructora');
                if (constructoraField) {
                    constructoraField.value = '';
                }
            }
        }
    }
    
    // Ejecutar al cargar la página
    toggleConstructoraField();
    
    // Ejecutar cuando cambie el rol
    if (rolField) {
        rolField.addEventListener('change', toggleConstructoraField);
    }
});