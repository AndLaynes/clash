// War Progress Chart
document.addEventListener('DOMContentLoaded', function () {
    const ctx = document.getElementById('warProgressChart');
    if (!ctx) return;

    // Data will be injected by Jinja2
    const warData = {{ war_chart_data | tojson
}};

new Chart(ctx, {
    type: 'line',
    data: {
        labels: warData.labels,
        datasets: [{
            label: 'Fama do Clã',
            data: warData.fame,
            borderColor: '#ffd700',
            backgroundColor: 'rgba(255, 215, 0, 0.1)',
            borderWidth: 3,
            tension: 0.4,
            fill: true,
            pointRadius: 5,
            pointBackgroundColor: '#ffd700',
            pointBorderColor: '#fff',
            pointBorderWidth: 2,
            pointHoverRadius: 7
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
                        return 'Fama: ' + context.parsed.y;
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
                    color: 'rgba(255, 255, 255, 0.05)'
                },
                ticks: {
                    color: '#94a3b8'
                }
            }
        },
        interaction: {
            intersect: false,
            mode: 'index'
        }
    }
});
});
