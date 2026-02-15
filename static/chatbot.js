/**
 * AI Risk Assistant Chatbot - Conversational Interface
 * Real chatbot with natural conversation flow
 */

let chatOpen = false;
let chatHistory = [];
let typingIndicator = false;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initChatbot();
});

function initChatbot() {
    // Create floating button
    const button = document.createElement('div');
    button.id = 'chatbot-button';
    button.innerHTML = '<i class="fas fa-robot"></i>';
    button.onclick = toggleChat;
    document.body.appendChild(button);
    
    // Create chat window
    const window = document.createElement('div');
    window.id = 'chatbot-window';
    window.innerHTML = `
        <div class="chat-header">
            <div class="chat-title">
                <i class="fas fa-robot"></i>
                <span>AI Risk Assistant</span>
            </div>
            <button class="chat-close" onclick="toggleChat()">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="chat-messages" id="chat-messages"></div>
        <div class="chat-input-container">
            <input type="text" id="chat-input" placeholder="Ask me anything about traffic risk..." />
            <button id="chat-send" onclick="sendMessage()">
                <i class="fas fa-paper-plane"></i>
            </button>
        </div>
    `;
    document.body.appendChild(window);
    
    // Enter key support
    document.getElementById('chat-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Welcome message
    setTimeout(() => {
        addBotMessage("Hello! I'm your AI Risk Assistant. I can help you predict traffic risk, get forecasts, and understand risk factors. What would you like to know?");
    }, 500);
}

function toggleChat() {
    chatOpen = !chatOpen;
    const window = document.getElementById('chatbot-window');
    const button = document.getElementById('chatbot-button');
    
    if (chatOpen) {
        window.classList.add('open');
        button.classList.add('active');
        document.getElementById('chat-input').focus();
    } else {
        window.classList.remove('open');
        button.classList.remove('active');
    }
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    addUserMessage(message);
    input.value = '';
    showTypingIndicator();
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: message, user_id: 'default'})
        });
        
        const data = await response.json();
        hideTypingIndicator();
        
        // Format and display bot reply
        addBotMessage(data.reply);
        
        // Handle actions
        if (data.action === 'predict' && data.structured_data) {
            handlePrediction(data.structured_data);
        } else if (data.action === 'forecast') {
            if (typeof loadForecast === 'function') {
                loadForecast();
            }
        } else if (data.action === 'clear_map') {
            if (typeof clearMap === 'function') {
                clearMap();
            }
        } else if (data.action === 'high_risk_areas' && data.structured_data) {
            if (data.structured_data.clusters && typeof map !== 'undefined') {
                const cluster = data.structured_data.clusters[0];
                if (cluster) {
                    map.setView([cluster.latitude, cluster.longitude], 12, {animate: true});
                }
            }
        }
        
    } catch (error) {
        hideTypingIndicator();
        addBotMessage("Sorry, I'm having trouble connecting. Please try again!");
        console.error('Chat error:', error);
    }
}

function handlePrediction(data) {
    const prob = data.probability;
    const severity = data.severity;
    const riskLevel = data.risk_level;
    const entities = data.entities || {};
    
    // Update gauge
    if (typeof updateGauge === 'function') {
        updateGauge(prob);
    }
    
    // Add marker if location provided
    if (entities.latitude && entities.longitude && typeof map !== 'undefined' && typeof markersLayer !== 'undefined') {
        const lat = entities.latitude;
        const lng = entities.longitude;
        const color = prob > 0.7 ? '#ef4444' : prob > 0.4 ? '#fbbf24' : '#22c55e';
        
        const marker = L.circleMarker([lat, lng], {
            color: color,
            fillColor: color,
            fillOpacity: 0.7,
            radius: 8 + (prob * 12),
            weight: 2
        }).addTo(markersLayer);
        
        marker.bindPopup(`
            <strong>Risk: ${(prob * 100).toFixed(1)}%</strong><br>
            Level: ${riskLevel}<br>
            Severity: ${severity}
        `).openPopup();
        
        // Add to heatmap
        if (typeof heatPoints !== 'undefined') {
            heatPoints.push([lat, lng, prob]);
            if (currentLayer === 'heatmap' && typeof updateHeatmap === 'function') {
                updateHeatmap();
            }
        }
        
        map.setView([lat, lng], 13, {animate: true});
    }
    
    // Notification
    if (typeof showNotification === 'function') {
        showNotification(`Risk predicted: ${(prob * 100).toFixed(1)}%`, 'success');
    }
}

function addUserMessage(message) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'message user-message';
    div.innerHTML = `
        <div class="message-content">${escapeHtml(message)}</div>
        <div class="message-time">${getTime()}</div>
    `;
    container.appendChild(div);
    scrollToBottom();
}

function addBotMessage(message) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'message bot-message';
    
    // Format markdown-style
    let formatted = escapeHtml(message);
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\n/g, '<br>');
    
    div.innerHTML = `
        <div class="message-avatar"><i class="fas fa-robot"></i></div>
        <div class="message-content">${formatted}</div>
        <div class="message-time">${getTime()}</div>
    `;
    container.appendChild(div);
    scrollToBottom();
}

function showTypingIndicator() {
    if (typingIndicator) return;
    typingIndicator = true;
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.id = 'typing-indicator';
    div.className = 'message bot-message typing';
    div.innerHTML = `
        <div class="message-avatar"><i class="fas fa-robot"></i></div>
        <div class="message-content">
            <span class="typing-dots"><span>.</span><span>.</span><span>.</span></span>
        </div>
    `;
    container.appendChild(div);
    scrollToBottom();
}

function hideTypingIndicator() {
    typingIndicator = false;
    const indicator = document.getElementById('typing-indicator');
    if (indicator) indicator.remove();
}

function scrollToBottom() {
    const container = document.getElementById('chat-messages');
    container.scrollTop = container.scrollHeight;
}

function getTime() {
    return new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
