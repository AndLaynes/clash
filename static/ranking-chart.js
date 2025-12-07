// Ranking Top 10 Chart
document.addEventListener('DOMContentLoaded', function () {
    const ctx = document.getElementById('rankingChart');
    if (!ctx) return;

    // Data will be injected by Jinja2
    const rankingData = {{ ranking_chart_data | tojson
}};

new Chart(ctx, {
    type: 'bar',
    data: {
        labels: rankingData.labels,
        datasets: [{
            label: 'Troféus',
            data: rankingData.trophies,
            backgroundColor: [
                'rgba(255, 215, 0, 0.8)',    // 1º - Ouro
                'rgba(192, 192, 192, 0.8)',  // 2º - Prata
                'rgba(205, 127, 50, 0.8)',   // 3º - Bronze
                'rgba(233, 69, 96, 0.7)',    // 4º-10º
                'rgba(233, 69, 96, 0.7)',
                'rgba(233, 69, 96, 0.7)',
                'rgba(233, 69, 96, 0.7)',
                'rgba(233, 69, 96, 0.7)',
                'rgba(233, 69, 96, 0.7)',
                'rgba(233, 69, 96, 0.7)'
            ],
            borderColor: [
                '#ffd700',
                '#c0c0c0',
                '#cd7f32',
                '#e94560',
                '#e94560',
                '#e94560',
                '#e94560',
                '#e94560',
                '#e94560',
                '#e94560'
            ],
            borderWidth: 2,
            borderRadius: 8
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                backgroundColor: 'rgba(15, 52, 96, 0.95)',
                titleColor: '#ffd700',
                bodyColor: '#fff',
                borderColor: '#ffd700',
                borderWidth: 2,
                padding: 12,
                displayColors: false,
                callbacks: {
                    label: function (context) {
                        return 'Troféus: ' + context.parsed.y;
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(255, 255, 255, 0.1)'
                },
                ticks: {
                    color: '#94a3b8'
                }
            },
            x: {
                grid: {
                    display: false
                },
                ticks: {
                    color: '#94a3b8',
                    maxRotation: 45,
                    minRotation: 45
                }
            }
        }
    }
});
});
