document.addEventListener('DOMContentLoaded', function() {
    const rolField = document.getElementById('id_rol');
    const constructoraField = document.getElementById('id_constructora');
    const constructoraGroup = constructoraField ? constructoraField.closest('.mb-3, .form-group, .col-md-6') : null;

    function toggleConstructoraField() {
        if (rolField && constructoraGroup) {
            const selectedOption = rolField.options[rolField.selectedIndex];
            const selectedText = selectedOption ? selectedOption.text : '';
            if (selectedText.includes('Constructora') || selectedText.includes('CONSTRUCTORA')) {
                constructoraGroup.style.display = '';
            } else {
                constructoraGroup.style.display = 'none';
                constructoraField.value = '';
            }
        }
    }

    toggleConstructoraField();
    if (rolField) {
        rolField.addEventListener('change', toggleConstructoraField);
    }
});