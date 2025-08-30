class ChatBot {
    constructor() {
        this.wsUrl = this.getWebSocketUrl();
        this.ws = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 1000;
        
        // DOM elements
        this.messagesContainer = document.getElementById('messagesContainer');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.statusDot = document.getElementById('statusDot');
        this.statusText = document.getElementById('statusText');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.connectionAlert = document.getElementById('connectionAlert');
        this.escalationBanner = document.getElementById('escalationBanner');
        this.charCounter = document.getElementById('charCounter');
        this.clearChatBtn = document.getElementById('clearChat');
        this.themeToggle = document.getElementById('themeToggle');
        
        // Theme state
        this.isDarkMode = localStorage.getItem('darkMode') === 'true';
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.initializeTheme();
        this.connect();
        this.updateCharCounter();
    }

    // Fetch WebSocket URL from config.js or fallback
    getWebSocketUrl() {
        if (window.CONFIG && window.CONFIG.WEBSOCKET_URL) {
            return window.CONFIG.WEBSOCKET_URL;
        } else {
            console.error('WebSocket URL not found in config.js. Please set CONFIG.WEBSOCKET_URL.');
            return 'wss://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/dev'; // Fallback URL
        }
    }
    
    setupEventListeners() {
        // Send message events
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Input events
        this.messageInput.addEventListener('input', () => {
            this.updateCharCounter();
            this.autoResize();
            this.updateSendButton();
        });
        
        // Clear chat
        this.clearChatBtn.addEventListener('click', () => this.clearChat());
        
        // Theme toggle
        this.themeToggle.addEventListener('click', () => this.toggleTheme());
        
        // Handle page visibility for reconnection
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && !this.isConnected) {
                this.connect();
            }
        });
    }
    
    connect() {
        try {
            this.updateStatus('connecting', 'Connecting...');
            this.ws = new WebSocket(this.wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateStatus('connected', 'Connected');
                this.hideConnectionAlert();
            };
            
            this.ws.onmessage = (event) => {
                this.handleMessage(event.data);
            };
            
            this.ws.onclose = (event) => {
                console.log('WebSocket closed:', event.code, event.reason);
                this.isConnected = false;
                this.updateStatus('disconnected', 'Disconnected');
                this.hideTypingIndicator();
                
                if (event.code !== 1000) { // Not a normal closure
                    this.handleReconnect();
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.showConnectionAlert();
            };
            
        } catch (error) {
            console.error('Failed to connect:', error);
            this.updateStatus('disconnected', 'Connection failed');
            this.handleReconnect();
        }
    }
    
    handleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.showConnectionAlert();
            
            setTimeout(() => {
                console.log(`Reconnection attempt ${this.reconnectAttempts}`);
                this.connect();
            }, this.reconnectInterval * this.reconnectAttempts);
        } else {
            this.updateStatus('disconnected', 'Connection failed');
            this.showConnectionAlert();
        }
    }
    
    sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || !this.isConnected) return;
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Clear input
        this.messageInput.value = '';
        this.updateCharCounter();
        this.autoResize();
        this.updateSendButton();
        
        // Show typing indicator
        this.showTypingIndicator();
        
        // Send to WebSocket
        const payload = {
            action: 'sendMessage',
            body: message
        };
        
        try {
            this.ws.send(JSON.stringify(payload));
        } catch (error) {
            console.error('Failed to send message:', error);
            this.hideTypingIndicator();
            this.addMessage('Failed to send message. Please try again.', 'bot', true);
        }
    }
    
    handleMessage(data) {
        this.hideTypingIndicator();
        
        try {
            // Try to parse as JSON first (new structured format)
            const response = JSON.parse(data);
            
            if (response.chatbotResponse && response.fullResponse) {
                // New structured format
                const message = response.chatbotResponse;
                const fullResponse = response.fullResponse;
                
                console.log('📋 Full response metadata:', fullResponse);
                
                // Use the escalation flag from the structured response
                const isEscalation = fullResponse.escalation === true;
                
                this.addMessage(message, 'bot');
                
                if (isEscalation) {
                    console.log('🚨 Escalation detected:', fullResponse.tags);
                    this.showEscalationBanner();
                }
                
                return;
            }
        } catch (error) {
            // If JSON parsing fails, fall back to plain text handling
            console.log('📝 Received plain text response, parsing as text');
        }
        
        // Fallback: handle as plain text (legacy format)
        const message = typeof data === 'string' ? data : data.toString();
        
        // Check if this looks like an escalation response (text-based detection)
        const isEscalation = message.toLowerCase().includes('human support') || 
                           message.toLowerCase().includes('escalat') ||
                           message.toLowerCase().includes('forwarded to');
        
        this.addMessage(message, 'bot');
        
        if (isEscalation) {
            this.showEscalationBanner();
        }
    }
    
    addMessage(content, sender, isError = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const timestamp = new Date().toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        messageDiv.innerHTML = `
            <div class="avatar">
                <i class="fas fa-${sender === 'user' ? 'user' : 'robot'}"></i>
            </div>
            <div class="message-content ${isError ? 'error' : ''}">
                ${this.formatMessage(content)}
                <div class="message-time">${timestamp}</div>
            </div>
        `;
        
        // Remove welcome message if it exists
        const welcomeMessage = this.messagesContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    formatMessage(content) {
        // Preserve line breaks and format the message
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }
    
    showTypingIndicator() {
        this.typingIndicator.style.display = 'block';
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
    }
    
    showConnectionAlert() {
        this.connectionAlert.style.display = 'flex';
    }
    
    hideConnectionAlert() {
        this.connectionAlert.style.display = 'none';
    }
    
    showEscalationBanner() {
        this.escalationBanner.style.display = 'flex';
        setTimeout(() => {
            this.escalationBanner.style.display = 'none';
        }, 10000); // Hide after 10 seconds
    }
    
    updateStatus(status, text) {
        this.statusDot.className = `status-dot ${status}`;
        this.statusText.textContent = text;
    }
    
    updateCharCounter() {
        const length = this.messageInput.value.length;
        this.charCounter.textContent = `${length}/2000`;
        
        if (length > 1800) {
            this.charCounter.style.color = '#ef4444';
        } else if (length > 1500) {
            this.charCounter.style.color = '#f59e0b';
        } else {
            this.charCounter.style.color = '#64748b';
        }
    }
    
    updateSendButton() {
        const hasText = this.messageInput.value.trim().length > 0;
        this.sendButton.disabled = !hasText || !this.isConnected;
    }
    
    autoResize() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }, 100);
    }
    
    clearChat() {
        if (confirm('Are you sure you want to clear the conversation?')) {
            // Remove all messages and any existing welcome message
            const messages = this.messagesContainer.querySelectorAll('.message');
            messages.forEach(msg => msg.remove());
            
            const existingWelcome = this.messagesContainer.querySelector('.welcome-message');
            if (existingWelcome) {
                existingWelcome.remove();
            }
            
            // Add welcome message back
            const welcomeDiv = document.createElement('div');
            welcomeDiv.className = 'welcome-message';
            welcomeDiv.innerHTML = `
                <div class="bot-avatar-large">
                    <i class="fas fa-robot"></i>
                </div>
                <h2>Welcome to TechAssist</h2>
                <p>I'm here to help you with technical support, account issues, and product guidance. How can I assist you today?</p>
            `;
            
            this.messagesContainer.appendChild(welcomeDiv);
            this.hideEscalationBanner();
        }
    }
    
    hideEscalationBanner() {
        this.escalationBanner.style.display = 'none';
    }
    
    initializeTheme() {
        if (this.isDarkMode) {
            document.documentElement.setAttribute('data-theme', 'dark');
            this.themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
            this.themeToggle.title = 'Switch to light mode';
        } else {
            document.documentElement.removeAttribute('data-theme');
            this.themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
            this.themeToggle.title = 'Switch to dark mode';
        }
    }
    
    toggleTheme() {
        this.isDarkMode = !this.isDarkMode;
        localStorage.setItem('darkMode', this.isDarkMode.toString());
        
        if (this.isDarkMode) {
            document.documentElement.setAttribute('data-theme', 'dark');
            this.themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
            this.themeToggle.title = 'Switch to light mode';
        } else {
            document.documentElement.removeAttribute('data-theme');
            this.themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
            this.themeToggle.title = 'Switch to dark mode';
        }
    }
}

// Initialize the chatbot when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.chatbot = new ChatBot();
});

// Handle WebSocket URL configuration
// You can override the WebSocket URL by setting it in localStorage or via environment variable
if (localStorage.getItem('wsUrl')) {
    document.addEventListener('DOMContentLoaded', () => {
        if (window.chatbot) {
            window.chatbot.wsUrl = localStorage.getItem('wsUrl');
        }
    });
}

// Development helper - allows setting WebSocket URL via console
window.setWebSocketUrl = (url) => {
    localStorage.setItem('wsUrl', url);
    if (window.chatbot) {
        window.chatbot.wsUrl = url;
        window.chatbot.connect();
    }
    console.log('WebSocket URL updated to:', url);
};