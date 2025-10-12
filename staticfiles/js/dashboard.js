// Inicializar gráfico circular de Techo Chile
document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('statusChart');
    if (ctx) {
        new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Cerradas', 'Abiertas', 'Vencidas'],
                datasets: [{
                    data: [
                        parseInt(ctx.dataset.cerradas || 142),
                        parseInt(ctx.dataset.abiertas || 15),
                        parseInt(ctx.dataset.vencidas || 6)
                    ],
                    backgroundColor: ['#22c55e', '#fbbf24', '#ef4444'],
                    borderWidth: 0,
                    cutout: '70%'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
});