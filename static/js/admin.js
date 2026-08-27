// Cyber-Cell Analytics & Chart.js Engine
document.addEventListener('DOMContentLoaded', () => {
  if (typeof Chart === 'undefined') return;

  const chartDataElement = document.getElementById('admin-chart-data');
  if (!chartDataElement) return;

  let chartData;
  try {
    chartData = JSON.parse(chartDataElement.textContent);
  } catch (e) {
    console.error('Error parsing chart data:', e);
    return;
  }

  const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';
  const textColor = isDarkMode ? '#94A3B8' : '#64748B';
  const gridColor = isDarkMode ? '#1E293B' : '#E2E8F0';

  Chart.defaults.color = textColor;
  Chart.defaults.font.family = "'Inter', system-ui, sans-serif";

  // 1. Category Bar Chart
  const ctxCat = document.getElementById('chart-category');
  if (ctxCat && chartData.categories) {
    new Chart(ctxCat, {
      type: 'bar',
      data: {
        labels: chartData.categories.labels,
        datasets: [{
          label: 'Complaints',
          data: chartData.categories.data,
          backgroundColor: '#0F4C81',
          hoverBackgroundColor: '#6366F1',
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { padding: 10, cornerRadius: 6 }
        },
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: gridColor }, beginAtZero: true, ticks: { precision: 0 } }
        }
      }
    });
  }

  // 2. Status Doughnut Chart
  const ctxStatus = document.getElementById('chart-status');
  if (ctxStatus && chartData.statuses) {
    new Chart(ctxStatus, {
      type: 'doughnut',
      data: {
        labels: chartData.statuses.labels,
        datasets: [{
          data: chartData.statuses.data,
          backgroundColor: ['#0288D1', '#E65100', '#2E7D32'],
          hoverOffset: 4,
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { padding: 15, usePointStyle: true } }
        },
        cutout: '70%'
      }
    });
  }

  // 3. 7-Day Trend Line Chart
  const ctxTrend = document.getElementById('chart-trend');
  if (ctxTrend && chartData.trends) {
    new Chart(ctxTrend, {
      type: 'line',
      data: {
        labels: chartData.trends.labels,
        datasets: [{
          label: 'Incidents Reported',
          data: chartData.trends.data,
          borderColor: '#6366F1',
          backgroundColor: 'rgba(99, 102, 241, 0.1)',
          fill: true,
          tension: 0.35,
          pointRadius: 4,
          pointBackgroundColor: '#6366F1'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: gridColor }, beginAtZero: true, ticks: { precision: 0 } }
        }
      }
    });
  }

});
