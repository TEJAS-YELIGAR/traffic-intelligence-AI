/**
 * Smart City Urban Intelligence Platform - Dashboard JavaScript
 * Advanced features: animations, anomaly detection, auto-centering, tooltips
 */

// Global state
let map, markersLayer, heatmapLayer, anomalyLayer;
let heatPoints = [];
let currentLayer = 'markers';
let forecastChart, featureChart;
let anomalyAlertShown = false;
let riskClusters = [];

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initMap();
    loadForecast();
    loadFeatureImportance();
    checkAnomalies();
    loadRiskClusters();
    updateGauge(0);
    
    // Auto-refresh every 5 minutes
    setInterval(() => {
        checkAnomalies();
        loadRiskClusters();
    }, 300000);
});

// Initialize map with smooth animations
function initMap() {
    map = L.map('map', {
        zoomControl: true,
        fadeAnimation: true,
        zoomAnimation: true
    }).setView([34.0522, -118.2437], 10);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        fadeAnimation: true
    }).addTo(map);
    
    // Initialize layers
    markersLayer = L.layerGroup().addTo(map);
    heatmapLayer = null;
    anomalyLayer = L.layerGroup();
    
    setupMapClickHandler();
}

// Enhanced map click handler with smooth animations
function setupMapClickHandler() {
    map.on('click', function(e) {
        const lat = e.latlng.lat;
        const lng = e.latlng.lng;
        
        // Show loading with animation
        const loadingMarker = L.marker([lat, lng], {
            icon: L.divIcon({
                className: 'loading-marker',
                html: '<div class="spinner"></div>',
                iconSize: [40, 40]
            })
        }).addTo(map);
        
        // Get current time features
        const now = new Date();
        const currentHour = now.getHours();
        const isWeekend = now.getDay() >= 5 ? 1 : 0;
        
        // Make prediction request
        fetch("/predict", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                weather: 1,
                visibility: 10,
                temperature: 70,
                wind_speed: 5,
                hour: currentHour,
                is_weekend: isWeekend,
                traffic_density: 50,
                latitude: lat,
                longitude: lng
            })
        })
        .then(res => res.json())
        .then(data => {
            loadingMarker.remove();
            
            if (data.error) {
                showNotification('Error: ' + data.message, 'error');
                return;
            }
            
            const prob = data.probability;
            const severity = data.severity;
            const riskLevel = data.risk_level || (prob > 0.7 ? 'HIGH' : prob > 0.4 ? 'MEDIUM' : 'LOW');
            const isAnomaly = data.is_anomaly || false;
            
            // Update gauge with animation
            updateGauge(prob);
            
            // Determine color with gradient
            const color = getRiskColor(prob);
            
            // Add marker with smooth animation
            const marker = L.circleMarker([lat, lng], {
                color: color,
                fillColor: color,
                fillOpacity: 0.7,
                radius: 8 + (prob * 12),
                weight: 2
            }).addTo(markersLayer);
            
            // Enhanced tooltip with forecast trend
            const tooltipContent = createTooltipContent(prob, severity, riskLevel, data.geo_features);
            marker.bindPopup(tooltipContent, {
                className: 'risk-popup'
            }).openPopup();
            
            // Add to heatmap data
            heatPoints.push([lat, lng, prob]);
            
            // Update heatmap if active
            if (currentLayer === 'heatmap' && heatmapLayer) {
                updateHeatmap();
            }
            
            // Check for anomaly and show alert
            if (isAnomaly && !anomalyAlertShown) {
                showAnomalyAlert(lat, lng, prob);
                addAnomalyMarker(lat, lng, prob);
            }
            
            // Show notification
            showNotification(`Risk predicted: ${(prob * 100).toFixed(1)}% (${riskLevel})`, 'success');
        })
        .catch(err => {
            loadingMarker.remove();
            console.error('Prediction error:', err);
            showNotification('Failed to get prediction. Please try again.', 'error');
        });
    });
}

// Get risk color with gradient
function getRiskColor(prob) {
    if (prob >= 0.7) return '#ef4444';  // Red
    if (prob >= 0.4) return '#fbbf24';  // Orange
    return '#22c55e';  // Green
}

// Create enhanced tooltip content
function createTooltipContent(prob, severity, riskLevel, geoFeatures) {
    const trend = getForecastTrend();
    return `
        <div class="tooltip-content">
            <div class="tooltip-header">
                <strong>Risk Prediction</strong>
                <span class="risk-badge risk-${riskLevel.toLowerCase()}">${riskLevel}</span>
            </div>
            <div class="tooltip-body">
                <div class="tooltip-stat">
                    <span class="stat-label">Probability:</span>
                    <span class="stat-value">${(prob * 100).toFixed(1)}%</span>
                </div>
                <div class="tooltip-stat">
                    <span class="stat-label">Severity:</span>
                    <span class="stat-value">${severity}</span>
                </div>
                <div class="tooltip-stat">
                    <span class="stat-label">Forecast Trend:</span>
                    <span class="stat-value trend-${trend.direction}">
                        <i class="fas fa-arrow-${trend.direction === 'up' ? 'up' : 'down'}"></i>
                        ${trend.text}
                    </span>
                </div>
                ${geoFeatures ? `
                <div class="tooltip-geo">
                    <small>Distance to Highway: ${geoFeatures.distance_to_highway} km</small><br>
                    <small>Urban Density: ${(geoFeatures.urban_density_score * 100).toFixed(0)}%</small>
                </div>
                ` : ''}
            </div>
        </div>
    `;
}

// Get forecast trend (simplified)
function getForecastTrend() {
    // In production, this would use actual forecast data
    return {
        direction: 'up',
        text: 'Increasing'
    };
}

// Update gauge with smooth animation
function updateGauge(value) {
    const canvas = document.getElementById('gaugeCanvas');
    const valueDisplay = document.getElementById('gaugeValue');
    const riskIndicator = document.getElementById('riskIndicator');
    const riskText = document.getElementById('riskText');
    
    // Animate value change
    animateValue(valueDisplay, parseFloat(valueDisplay.textContent) || 0, value * 100, 500);
    
    // Update gauge drawing
    drawGauge(canvas, value);
    
    // Update risk indicator
    riskIndicator.style.display = 'flex';
    riskIndicator.className = 'risk-indicator';
    if (value < 0.4) {
        riskIndicator.classList.add('risk-low');
        riskText.innerHTML = '<i class="fas fa-check-circle"></i> Low Risk';
    } else if (value < 0.7) {
        riskIndicator.classList.add('risk-medium');
        riskText.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Medium Risk';
    } else {
        riskIndicator.classList.add('risk-high');
        riskText.innerHTML = '<i class="fas fa-exclamation-circle"></i> High Risk';
    }
}

// Animate numeric value
function animateValue(element, start, end, duration) {
    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.round(current) + '%';
    }, 16);
}

// Draw professional gauge (from existing code)
function drawGauge(canvas, value) {
    const ctx = canvas.getContext('2d');
    const centerX = canvas.width / 2;
    const centerY = canvas.height - 20;
    const radius = Math.min(canvas.width, canvas.height) * 0.4;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw arc background
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, Math.PI, 0, false);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.lineWidth = 20;
    ctx.stroke();
    
    // Draw value arc with gradient
    const angle = Math.PI - (value * Math.PI);
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, Math.PI, angle, false);
    
    let gradient;
    if (value < 0.4) {
        gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
        gradient.addColorStop(0, '#22c55e');
        gradient.addColorStop(1, '#16a34a');
    } else if (value < 0.7) {
        gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
        gradient.addColorStop(0, '#fbbf24');
        gradient.addColorStop(1, '#f59e0b');
    } else {
        gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
        gradient.addColorStop(0, '#ef4444');
        gradient.addColorStop(1, '#dc2626');
    }
    
    ctx.strokeStyle = gradient;
    ctx.lineWidth = 20;
    ctx.lineCap = 'round';
    ctx.stroke();
    
    // Draw animated needle
    const needleAngle = Math.PI - (value * Math.PI);
    const needleLength = radius * 0.8;
    const needleX = centerX + Math.cos(needleAngle) * needleLength;
    const needleY = centerY - Math.sin(needleAngle) * needleLength;
    
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.lineTo(needleX, needleY);
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 3;
    ctx.stroke();
    
    // Draw center circle
    ctx.beginPath();
    ctx.arc(centerX, centerY, 8, 0, 2 * Math.PI);
    ctx.fillStyle = '#ffffff';
    ctx.fill();
    
    // Draw scale marks
    for (let i = 0; i <= 10; i++) {
        const markValue = i / 10;
        const markAngle = Math.PI - (markValue * Math.PI);
        const innerRadius = radius - 15;
        const outerRadius = radius + 5;
        
        ctx.beginPath();
        ctx.moveTo(
            centerX + Math.cos(markAngle) * innerRadius,
            centerY - Math.sin(markAngle) * innerRadius
        );
        ctx.lineTo(
            centerX + Math.cos(markAngle) * outerRadius,
            centerY - Math.sin(markAngle) * outerRadius
        );
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.lineWidth = 2;
        ctx.stroke();
    }
}

// Toggle layers
function toggleLayer(layer) {
    currentLayer = layer;
    
    if (layer === 'markers') {
        document.getElementById('markersBtn').classList.add('active');
        document.getElementById('heatmapBtn').classList.remove('active');
        markersLayer.addTo(map);
        if (heatmapLayer) {
            map.removeLayer(heatmapLayer);
        }
    } else if (layer === 'heatmap') {
        document.getElementById('heatmapBtn').classList.add('active');
        document.getElementById('markersBtn').classList.remove('active');
        if (markersLayer) {
            map.removeLayer(markersLayer);
        }
        updateHeatmap();
    }
}

// Update heatmap
function updateHeatmap() {
    if (heatmapLayer) {
        map.removeLayer(heatmapLayer);
    }
    
    if (heatPoints.length > 0) {
        const heatData = heatPoints.map(point => [point[0], point[1], point[2] * 100]);
        heatmapLayer = L.heatLayer(heatData, {
            radius: 25,
            blur: 15,
            maxZoom: 17,
            gradient: {
                0.0: 'blue',
                0.5: 'yellow',
                1.0: 'red'
            }
        }).addTo(map);
    }
}

// Clear map
function clearMap() {
    if (confirm('Clear all markers and heatmap data?')) {
        markersLayer.clearLayers();
        if (heatmapLayer) {
            map.removeLayer(heatmapLayer);
            heatmapLayer = null;
        }
        if (anomalyLayer) {
            map.removeLayer(anomalyLayer);
            anomalyLayer.clearLayers();
        }
        heatPoints = [];
        updateGauge(0);
        document.getElementById('riskIndicator').style.display = 'none';
    }
}

// Load forecast with enhanced data
function loadForecast() {
    fetch("/forecast")
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                console.error('Forecast error:', data.message);
                return;
            }
            
            const ctx = document.getElementById('forecastChart').getContext('2d');
            
            if (forecastChart) {
                forecastChart.destroy();
            }
            
            const hourlyData = data.hourly_forecast || data.risk || [];
            const hours = hourlyData.map((item, idx) => 
                item.hour !== undefined ? item.hour : (item.hour || idx)
            );
            const risks = hourlyData.map(item => 
                item.risk !== undefined ? item.risk : item
            );
            
            forecastChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: hours.map(h => h + ':00'),
                    datasets: [{
                        label: 'Risk Probability',
                        data: risks,
                        borderColor: 'rgb(102, 126, 234)',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            display: true,
                            labels: { color: 'rgba(255, 255, 255, 0.9)' }
                        }
                    },
                    scales: {
                        x: { ticks: { color: 'rgba(255, 255, 255, 0.7)' } },
                        y: { 
                            ticks: { color: 'rgba(255, 255, 255, 0.7)' },
                            min: 0,
                            max: 1
                        }
                    }
                }
            });
            
            // Show peak hour if available
            if (data.peak_hour !== undefined) {
                console.log(`Peak risk hour: ${data.peak_hour}:00`);
            }
        })
        .catch(err => {
            console.error('Forecast fetch error:', err);
        });
}

// Load feature importance
function loadFeatureImportance() {
    fetch("/api/feature-importance")
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                console.error('Feature importance error:', data.message);
                return;
            }
            
            const ctx = document.getElementById('featureChart');
            if (!ctx) return;
            
            const importance = data.feature_importance || {};
            const features = Object.keys(importance);
            const values = Object.values(importance);
            
            if (featureChart) {
                featureChart.destroy();
            }
            
            featureChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: features,
                    datasets: [{
                        label: 'Importance',
                        data: values,
                        backgroundColor: 'rgba(102, 126, 234, 0.6)',
                        borderColor: 'rgb(102, 126, 234)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    indexAxis: 'y',
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: { ticks: { color: 'rgba(255, 255, 255, 0.7)' } },
                        y: { ticks: { color: 'rgba(255, 255, 255, 0.7)' } }
                    }
                }
            });
        })
        .catch(err => {
            console.error('Feature importance fetch error:', err);
        });
}

// Check for anomalies
function checkAnomalies() {
    fetch("/api/anomalies?hours=24")
        .then(res => res.json())
        .then(data => {
            if (data.has_anomalies && data.anomaly_count > 0) {
                showAnomalyAlert(null, null, null, data);
                displayAnomalyMarkers(data.anomalies);
            }
        })
        .catch(err => {
            console.error('Anomaly check error:', err);
        });
}

// Show anomaly alert banner
function showAnomalyAlert(lat, lng, prob, anomalyData) {
    if (anomalyAlertShown) return;
    
    const alertBanner = document.createElement('div');
    alertBanner.className = 'anomaly-alert';
    alertBanner.innerHTML = `
        <div class="alert-content">
            <i class="fas fa-exclamation-triangle"></i>
            <strong>Anomaly Detected!</strong>
            ${anomalyData ? `${anomalyData.anomaly_count} unusual risk patterns detected in the last 24 hours.` : 'Unusual risk pattern detected at this location.'}
            <button onclick="this.parentElement.parentElement.remove(); anomalyAlertShown = false;">×</button>
        </div>
    `;
    
    document.body.insertBefore(alertBanner, document.body.firstChild);
    anomalyAlertShown = true;
    
    // Auto-dismiss after 10 seconds
    setTimeout(() => {
        if (alertBanner.parentElement) {
            alertBanner.remove();
            anomalyAlertShown = false;
        }
    }, 10000);
}

// Display anomaly markers
function displayAnomalyMarkers(anomalies) {
    anomalyLayer.clearLayers();
    
    anomalies.forEach(anomaly => {
        const marker = L.circleMarker([anomaly.latitude, anomaly.longitude], {
            color: '#dc2626',
            fillColor: '#dc2626',
            fillOpacity: 0.8,
            radius: 10,
            weight: 3
        }).bindPopup(`
            <strong>Anomaly Detected</strong><br>
            Risk: ${(anomaly.probability * 100).toFixed(1)}%<br>
            Severity: ${anomaly.severity}
        `);
        
        anomalyLayer.addLayer(marker);
    });
    
    anomalyLayer.addTo(map);
}

// Add anomaly marker
function addAnomalyMarker(lat, lng, prob) {
    const marker = L.circleMarker([lat, lng], {
        color: '#dc2626',
        fillColor: '#dc2626',
        fillOpacity: 0.8,
        radius: 12,
        weight: 3
    }).bindPopup('Anomaly: High risk detected');
    
    anomalyLayer.addLayer(marker);
    if (!map.hasLayer(anomalyLayer)) {
        anomalyLayer.addTo(map);
    }
}

// Load risk clusters and auto-center
function loadRiskClusters() {
    fetch("/api/risk-clusters?n_clusters=5")
        .then(res => res.json())
        .then(data => {
            if (data.clusters && data.clusters.length > 0) {
                riskClusters = data.clusters;
                
                // Auto-center to highest risk cluster
                const highestRisk = riskClusters[0];
                if (highestRisk && highestRisk.average_risk > 0.6) {
                    map.setView([highestRisk.latitude, highestRisk.longitude], 12, {
                        animate: true,
                        duration: 1.0
                    });
                }
                
                // Display cluster markers
                displayRiskClusters(riskClusters);
            }
        })
        .catch(err => {
            console.error('Risk clusters fetch error:', err);
        });
}

// Display risk clusters
function displayRiskClusters(clusters) {
    clusters.forEach((cluster, idx) => {
        const color = cluster.average_risk > 0.7 ? '#ef4444' : 
                     cluster.average_risk > 0.4 ? '#fbbf24' : '#22c55e';
        
        const marker = L.circleMarker([cluster.latitude, cluster.longitude], {
            color: color,
            fillColor: color,
            fillOpacity: 0.6,
            radius: 15 + (cluster.average_risk * 10),
            weight: 2
        }).bindPopup(`
            <strong>Risk Cluster ${idx + 1}</strong><br>
            Average Risk: ${(cluster.average_risk * 100).toFixed(1)}%<br>
            Predictions: ${cluster.count}
        `);
        
        markersLayer.addLayer(marker);
    });
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}
