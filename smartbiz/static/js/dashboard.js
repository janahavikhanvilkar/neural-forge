document.addEventListener('DOMContentLoaded', function () {
    const categoryCanvas = document.getElementById('categoryChart');
    if (!categoryCanvas) return;

    fetch('/api/dashboard/charts')
        .then(res => res.json())
        .then(data => {
            // Chart 1: Tasks by Category
            new Chart(categoryCanvas, {
                type: 'doughnut',
                data: {
                    labels: data.categories.labels,
                    datasets: [{
                        data: data.categories.data,
                        backgroundColor: ['#6366f1', '#ec4899', '#3b82f6', '#f59e0b'],
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } }
                    },
                    cutout: '65%'
                }
            });

            // Chart 2: Human vs Automated Ratio
            const humanVsAutoCanvas = document.getElementById('humanVsAutoChart');
            if (humanVsAutoCanvas) {
                new Chart(humanVsAutoCanvas, {
                    type: 'doughnut',
                    data: {
                        labels: data.human_vs_auto.labels,
                        datasets: [{
                            data: data.human_vs_auto.data,
                            backgroundColor: ['#10b981', '#f59e0b'],
                            borderWidth: 2,
                            borderColor: '#ffffff'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } }
                        },
                        cutout: '65%'
                    }
                });
            }

            // Chart 3: AI Confidence Distribution
            const confidenceCanvas = document.getElementById('confidenceChart');
            if (confidenceCanvas) {
                new Chart(confidenceCanvas, {
                    type: 'bar',
                    data: {
                        labels: ['≥80% High', '60-79% Review', '<60% Low'],
                        datasets: [{
                            label: 'Task Count',
                            data: data.confidence_dist.data,
                            backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                            borderRadius: 6
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
                            x: { grid: { display: false } }
                        }
                    }
                });
            }

            // Chart 4: Lead Score Breakdown
            const leadScoreCanvas = document.getElementById('leadScoreChart');
            if (leadScoreCanvas) {
                new Chart(leadScoreCanvas, {
                    type: 'doughnut',
                    data: {
                        labels: data.lead_scores.labels,
                        datasets: [{
                            data: data.lead_scores.data,
                            backgroundColor: ['#ef4444', '#f59e0b', '#94a3b8'],
                            borderWidth: 2,
                            borderColor: '#ffffff'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } }
                        },
                        cutout: '65%'
                    }
                });
            }

            // Chart 5: Support Tickets by Department
            const ticketDeptCanvas = document.getElementById('ticketDeptChart');
            if (ticketDeptCanvas) {
                new Chart(ticketDeptCanvas, {
                    type: 'bar',
                    data: {
                        labels: data.tickets_by_dept.labels,
                        datasets: [{
                            label: 'Tickets',
                            data: data.tickets_by_dept.data,
                            backgroundColor: '#6366f1',
                            borderRadius: 6
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
                            x: { grid: { display: false } }
                        }
                    }
                });
            }

            // Chart 6: Weekly Automation Trend
            const timelineCanvas = document.getElementById('timelineChart');
            if (timelineCanvas) {
                new Chart(timelineCanvas, {
                    type: 'line',
                    data: {
                        labels: data.timeline.labels,
                        datasets: [
                            {
                                label: 'Automated Straight-Through',
                                data: data.timeline.automated,
                                borderColor: '#4f46e5',
                                backgroundColor: 'rgba(79, 70, 229, 0.1)',
                                fill: true,
                                tension: 0.35
                            },
                            {
                                label: 'Human Verification (HITL)',
                                data: data.timeline.hitl,
                                borderColor: '#f59e0b',
                                backgroundColor: 'transparent',
                                borderDash: [4, 4],
                                tension: 0.35
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } }
                        },
                        scales: {
                            y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
                            x: { grid: { display: false } }
                        }
                    }
                });
            }
        })
        .catch(err => console.error('Dashboard charts error:', err));
});
