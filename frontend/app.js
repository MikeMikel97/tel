/**
 * AI Call Agent - Frontend Application
 */

class AICallAgent {
    constructor() {
        this.ws = null;
        this.calls = new Map();
        this.activeCallId = null;
        this.callTimers = new Map();
        this.phone = null;
        this.isPhoneConnected = false;
        
        // DOM Elements
        this.elements = {
            connectionStatus: document.getElementById('connectionStatus'),
            callsList: document.getElementById('callsList'),
            callCount: document.getElementById('callCount'),
            activeCall: document.getElementById('activeCall'),
            emptyWorkspace: document.getElementById('emptyWorkspace'),
            callerNumber: document.getElementById('callerNumber'),
            callDuration: document.getElementById('callDuration'),
            transcriptContent: document.getElementById('transcriptContent'),
            suggestionsContent: document.getElementById('suggestionsContent'),
            connectPhoneBtn: document.getElementById('connectPhoneBtn'),
            demoBtn: document.getElementById('demoBtn'),
            demoBtn2: document.getElementById('demoBtn2'),
            hangupBtn: document.getElementById('hangupBtn'),
            testCallEchoBtn: document.getElementById('testCallEchoBtn'),
            testCallTimeBtn: document.getElementById('testCallTimeBtn'),
        };
        
        this.init();
    }
    
    init() {
        this.connectWebSocket();
        this.bindEvents();
    }
    
    // === WebSocket Connection ===
    connectWebSocket() {
        const wsUrl = this.getWebSocketUrl();
        console.log('Connecting to WebSocket:', wsUrl);
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.setConnectionStatus('connected', 'Подключено');
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.setConnectionStatus('disconnected', 'Отключено');
            // Reconnect after 3 seconds
            setTimeout(() => this.connectWebSocket(), 3000);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.setConnectionStatus('disconnected', 'Ошибка');
        };
        
        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleEvent(data);
            } catch (e) {
                console.error('Failed to parse message:', e);
            }
        };
    }
    
    getWebSocketUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.hostname || 'localhost';
        const port = 8000; // Backend port
        return `${protocol}//${host}:${port}/ws`;
    }
    
    setConnectionStatus(status, text) {
        this.elements.connectionStatus.className = `connection-status ${status}`;
        this.elements.connectionStatus.querySelector('.status-text').textContent = text;
    }
    
    // === Event Handling ===
    handleEvent(event) {
        console.log('Received event:', event);
        
        switch (event.event_type) {
            case 'call_start':
                this.handleCallStart(event);
                break;
            case 'call_answer':
                this.handleCallAnswer(event);
                break;
            case 'call_end':
                this.handleCallEnd(event);
                break;
            case 'transcript':
                this.handleTranscript(event);
                break;
            case 'suggestion':
                this.handleSuggestion(event);
                break;
        }
    }
    
    handleCallStart(event) {
        const call = {
            id: event.call_id,
            ...event.data,
            transcripts: [],
            suggestions: []
        };
        
        this.calls.set(event.call_id, call);
        this.renderCallsList();
        
        // Auto-select if first call
        if (this.calls.size === 1) {
            this.selectCall(event.call_id);
        }
        
        // Play notification sound (optional)
        this.playNotification();
    }
    
    handleCallAnswer(event) {
        const call = this.calls.get(event.call_id);
        if (call) {
            call.status = 'answered';
            call.answered_at = event.data.answered_at;
            this.startCallTimer(event.call_id);
            this.renderCallsList();
        }
    }
    
    handleCallEnd(event) {
        this.stopCallTimer(event.call_id);
        this.calls.delete(event.call_id);
        this.renderCallsList();
        
        if (this.activeCallId === event.call_id) {
            this.activeCallId = null;
            this.showEmptyWorkspace();
        }
    }
    
    handleTranscript(event) {
        const call = this.calls.get(event.call_id);
        if (call) {
            call.transcripts.push(event.data);
            
            if (this.activeCallId === event.call_id) {
                this.renderTranscript(call);
            }
        }
    }
    
    handleSuggestion(event) {
        const call = this.calls.get(event.call_id);
        if (call) {
            call.suggestions.unshift(event.data); // Add to beginning
            
            if (this.activeCallId === event.call_id) {
                this.renderSuggestions(call);
            }
            
            // Highlight if high priority
            if (event.data.priority === 'high') {
                this.highlightSuggestion();
            }
        }
    }
    
    // === UI Rendering ===
    renderCallsList() {
        const container = this.elements.callsList;
        this.elements.callCount.textContent = this.calls.size;
        
        if (this.calls.size === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                        <circle cx="24" cy="24" r="20" stroke="currentColor" stroke-width="2" stroke-dasharray="4 4"/>
                        <path d="M24 18V24L28 28" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                    <p>Ожидание звонков...</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = '';
        
        this.calls.forEach((call, id) => {
            const card = document.createElement('div');
            card.className = `call-card ${id === this.activeCallId ? 'active' : ''}`;
            card.onclick = () => this.selectCall(id);
            
            const statusClass = call.status === 'answered' ? 'active' : 'ringing';
            const statusText = call.status === 'answered' ? 'В разговоре' : 'Входящий';
            
            card.innerHTML = `
                <div class="call-card-avatar">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                        <path d="M18 14.5V17C18 17.55 17.55 18 17 18C8.72 18 2 11.28 2 3C2 2.45 2.45 2 3 2H5.5C6.05 2 6.5 2.45 6.5 3C6.5 4.25 6.7 5.45 7.07 6.57C7.18 6.92 7.1 7.31 6.82 7.59L4.62 9.79C6.06 12.62 8.38 14.93 11.21 16.38L13.41 14.18C13.69 13.9 14.08 13.82 14.43 13.93C15.55 14.3 16.75 14.5 18 14.5C18.55 14.5 19 14.95 19 15.5V18" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                </div>
                <div class="call-card-info">
                    <div class="call-card-number">${this.formatPhoneNumber(call.caller_number)}</div>
                    <div class="call-card-status ${statusClass}">
                        <span>●</span> ${statusText}
                    </div>
                </div>
                <div class="call-card-duration" data-call-id="${id}">
                    ${call.status === 'answered' ? this.getCallDuration(call) : '--:--'}
                </div>
            `;
            
            container.appendChild(card);
        });
    }
    
    selectCall(callId) {
        this.activeCallId = callId;
        const call = this.calls.get(callId);
        
        if (!call) return;
        
        // Update UI
        this.elements.emptyWorkspace.style.display = 'none';
        this.elements.activeCall.style.display = 'flex';
        
        this.elements.callerNumber.textContent = this.formatPhoneNumber(call.caller_number);
        
        this.renderCallsList();
        this.renderTranscript(call);
        this.renderSuggestions(call);
    }
    
    showEmptyWorkspace() {
        this.elements.activeCall.style.display = 'none';
        this.elements.emptyWorkspace.style.display = 'flex';
    }
    
    renderTranscript(call) {
        const container = this.elements.transcriptContent;
        
        if (call.transcripts.length === 0) {
            container.innerHTML = `
                <div class="empty-state" style="height: 100%;">
                    <p style="color: var(--text-muted);">Ожидание речи...</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = '';
        
        call.transcripts.forEach(transcript => {
            const message = document.createElement('div');
            message.className = `message ${transcript.speaker}`;
            
            const time = new Date(transcript.timestamp * 1000).toLocaleTimeString('ru-RU', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            
            const senderName = transcript.speaker === 'operator' ? 'Оператор' : 'Клиент';
            const avatarText = transcript.speaker === 'operator' ? 'О' : 'К';
            
            message.innerHTML = `
                <div class="message-avatar">${avatarText}</div>
                <div class="message-content">
                    <div class="message-header">
                        <span class="message-sender">${senderName}</span>
                        <span class="message-time">${time}</span>
                    </div>
                    <div class="message-text">${transcript.text}</div>
                </div>
            `;
            
            container.appendChild(message);
        });
        
        // Scroll to bottom
        container.scrollTop = container.scrollHeight;
    }
    
    renderSuggestions(call) {
        const container = this.elements.suggestionsContent;
        
        if (call.suggestions.length === 0) {
            container.innerHTML = `
                <div class="suggestion-placeholder">
                    <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                        <circle cx="20" cy="20" r="16" stroke="currentColor" stroke-width="1.5" stroke-dasharray="4 4"/>
                        <path d="M20 14V20L24 24" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                    <p>AI анализирует разговор...</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = '';
        
        call.suggestions.forEach(suggestion => {
            const card = document.createElement('div');
            card.className = `suggestion-card ${suggestion.type} ${suggestion.priority}`;
            
            const typeLabels = {
                objection: '⚡ Возражение',
                upsell: '💰 Upsell',
                info: 'ℹ️ Инфо',
                warning: '⚠️ Внимание',
                script: '📝 Скрипт'
            };
            
            card.innerHTML = `
                <div class="suggestion-header">
                    <span class="suggestion-type">${typeLabels[suggestion.type] || suggestion.type}</span>
                    <span class="suggestion-priority ${suggestion.priority}">${suggestion.priority}</span>
                </div>
                <div class="suggestion-title">${suggestion.title}</div>
                <div class="suggestion-content">${suggestion.content}</div>
            `;
            
            container.appendChild(card);
        });
    }
    
    // === Timer Management ===
    startCallTimer(callId) {
        const call = this.calls.get(callId);
        if (!call) return;
        
        const updateTimer = () => {
            const duration = this.getCallDuration(call);
            
            // Update in calls list
            const durationEl = document.querySelector(`.call-card-duration[data-call-id="${callId}"]`);
            if (durationEl) {
                durationEl.textContent = duration;
            }
            
            // Update in active call view
            if (this.activeCallId === callId) {
                this.elements.callDuration.textContent = duration;
            }
        };
        
        updateTimer();
        this.callTimers.set(callId, setInterval(updateTimer, 1000));
    }
    
    stopCallTimer(callId) {
        const timer = this.callTimers.get(callId);
        if (timer) {
            clearInterval(timer);
            this.callTimers.delete(callId);
        }
    }
    
    getCallDuration(call) {
        if (!call.answered_at) return '00:00';
        
        const start = new Date(call.answered_at).getTime();
        const now = Date.now();
        const seconds = Math.floor((now - start) / 1000);
        
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    
    // === Utility Functions ===
    formatPhoneNumber(number) {
        if (!number) return 'Неизвестный';
        
        // Remove all non-digits
        const digits = number.replace(/\D/g, '');
        
        if (digits.length === 11 && digits.startsWith('7')) {
            return `+7 (${digits.slice(1, 4)}) ${digits.slice(4, 7)}-${digits.slice(7, 9)}-${digits.slice(9)}`;
        }
        
        return number;
    }
    
    playNotification() {
        // Simple notification sound using Web Audio API
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
        } catch (e) {
            // Audio not supported
        }
    }
    
    highlightSuggestion() {
        // Visual feedback for high priority suggestions
        document.body.style.animation = 'none';
        document.body.offsetHeight; // Trigger reflow
        document.body.style.animation = 'highlightFlash 0.5s ease';
    }
    
    // === Event Bindings ===
    bindEvents() {
        // Connect phone button
        this.elements.connectPhoneBtn?.addEventListener('click', () => this.connectPhone());
        
        // Test call buttons
        this.elements.testCallEchoBtn?.addEventListener('click', () => this.makeTestCall('100'));
        this.elements.testCallTimeBtn?.addEventListener('click', () => this.makeTestCall('101'));
        
        // Demo buttons
        this.elements.demoBtn?.addEventListener('click', () => this.startDemo());
        this.elements.demoBtn2?.addEventListener('click', () => this.startDemo());
        
        // Hangup button
        this.elements.hangupBtn?.addEventListener('click', () => this.hangupCall());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.activeCallId) {
                this.hangupCall();
            }
        });
    }
    
    // === WebRTC Phone Methods ===
    async connectPhone() {
        if (this.isPhoneConnected) {
            this.disconnectPhone();
            return;
        }
        
        try {
            this.elements.connectPhoneBtn.disabled = true;
            this.elements.connectPhoneBtn.textContent = 'Подключение...';
            
            this.phone = new WebRTCPhone({
                server: 'ws://localhost:8088/asterisk/ws',
                domain: 'localhost',
                realm: 'asterisk',
                username: 'operator',
                password: 'operator123',
                
                onConnected: () => {
                    console.log('Phone connected!');
                    this.isPhoneConnected = true;
                    this.elements.connectPhoneBtn.textContent = 'Отключить телефон';
                    this.elements.connectPhoneBtn.disabled = false;
                    this.elements.connectPhoneBtn.classList.add('btn-success');
                    // Показываем кнопки тестовых звонков
                    this.elements.testCallEchoBtn.style.display = 'block';
                    this.elements.testCallTimeBtn.style.display = 'block';
                },
                
                onDisconnected: () => {
                    console.log('Phone disconnected');
                    this.isPhoneConnected = false;
                    this.elements.connectPhoneBtn.textContent = 'Подключить телефон';
                    this.elements.connectPhoneBtn.classList.remove('btn-success');
                    this.elements.connectPhoneBtn.disabled = false;
                    // Скрываем кнопки тестовых звонков
                    this.elements.testCallEchoBtn.style.display = 'none';
                    this.elements.testCallTimeBtn.style.display = 'none';
                },
                
                onIncomingCall: (callInfo) => {
                    console.log('Incoming call from:', callInfo.callerNumber);
                    this.showIncomingCallDialog(callInfo);
                },
                
                onCallStarted: () => {
                    console.log('Call started - audio should be playing');
                },
                
                onCallEnded: () => {
                    console.log('Call ended');
                },
                
                onError: (error) => {
                    console.error('Phone error:', error);
                    alert('Ошибка подключения телефона: ' + error.message);
                    this.elements.connectPhoneBtn.disabled = false;
                    this.elements.connectPhoneBtn.textContent = 'Подключить телефон';
                }
            });
            
            await this.phone.connect();
            
        } catch (error) {
            console.error('Failed to connect phone:', error);
            alert('Не удалось подключить телефон. Проверьте что Asterisk запущен.');
            this.elements.connectPhoneBtn.disabled = false;
            this.elements.connectPhoneBtn.textContent = 'Подключить телефон';
        }
    }
    
    disconnectPhone() {
        if (this.phone) {
            this.phone.disconnect();
            this.phone = null;
        }
        this.isPhoneConnected = false;
    }
    
    makeTestCall(number) {
        if (!this.phone || !this.isPhoneConnected) {
            alert('Сначала подключите телефон!');
            return;
        }
        
        console.log(`Making test call to ${number}`);
        this.phone.call(number);
    }
    
    showIncomingCallDialog(callInfo) {
        // Remove existing dialog if any
        const existingDialog = document.getElementById('incomingCallDialog');
        if (existingDialog) {
            existingDialog.remove();
        }
        
        // Create dialog
        const dialog = document.createElement('div');
        dialog.id = 'incomingCallDialog';
        dialog.innerHTML = `
            <div class="incoming-call-overlay">
                <div class="incoming-call-dialog">
                    <div class="incoming-call-header">
                        <h2>📞 Входящий звонок</h2>
                    </div>
                    <div class="incoming-call-body">
                        <p class="caller-number-large">${callInfo.callerNumber}</p>
                        <p class="call-status">Звонит...</p>
                    </div>
                    <div class="incoming-call-actions">
                        <button class="btn btn-success btn-large" id="acceptCallBtn">
                            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                                <path d="M1.5 8.5C1.5 8.5 4 6 10 6C16 6 18.5 8.5 18.5 8.5V11.5C18.5 12.0523 18.0523 12.5 17.5 12.5H14.5C13.9477 12.5 13.5 12.0523 13.5 11.5V10C13.5 10 12 9 10 9C8 9 6.5 10 6.5 10V11.5C6.5 12.0523 6.05228 12.5 5.5 12.5H2.5C1.94772 12.5 1.5 12.0523 1.5 11.5V8.5Z" stroke="currentColor" stroke-width="1.5"/>
                            </svg>
                            Принять
                        </button>
                        <button class="btn btn-danger btn-large" id="rejectCallBtn">
                            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                                <path d="M1.5 8.5C1.5 8.5 4 6 10 6C16 6 18.5 8.5 18.5 8.5V11.5C18.5 12.0523 18.0523 12.5 17.5 12.5H14.5C13.9477 12.5 13.5 12.0523 13.5 11.5V10C13.5 10 12 9 10 9C8 9 6.5 10 6.5 10V11.5C6.5 12.0523 6.05228 12.5 5.5 12.5H2.5C1.94772 12.5 1.5 12.0523 1.5 11.5V8.5Z" stroke="currentColor" stroke-width="1.5"/>
                            </svg>
                            Отклонить
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(dialog);
        
        // Add event listeners
        document.getElementById('acceptCallBtn').addEventListener('click', () => {
            dialog.remove();
            callInfo.accept();
        });
        
        document.getElementById('rejectCallBtn').addEventListener('click', () => {
            dialog.remove();
            callInfo.reject();
        });
    }
    
    hangupCall() {
        if (this.phone && this.phone.isInCall) {
            this.phone.hangup();
        }
        
        // Also handle demo calls
        this.endCurrentCall();
    }
    
    async startDemo() {
        try {
            const apiUrl = window.location.hostname === 'localhost' ? 'http://localhost:8000' : `http://${window.location.hostname}:8000`;
            const response = await fetch(`${apiUrl}/api/demo/call`, { method: 'POST' });
            const data = await response.json();
            console.log('Demo started:', data);
        } catch (e) {
            console.error('Failed to start demo:', e);
            alert('Не удалось запустить демо. Убедитесь, что backend запущен.');
        }
    }
    
    async endCurrentCall() {
        if (!this.activeCallId) return;
        
        try {
            const apiUrl = window.location.hostname === 'localhost' ? 'http://localhost:8000' : `http://${window.location.hostname}:8000`;
            await fetch(`${apiUrl}/api/demo/end/${this.activeCallId}`, { method: 'POST' });
        } catch (e) {
            console.error('Failed to end call:', e);
        }
    }
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    window.app = new AICallAgent();
});

// Add highlight flash animation
const style = document.createElement('style');
style.textContent = `
    @keyframes highlightFlash {
        0%, 100% { background: var(--bg-primary); }
        50% { background: rgba(239, 68, 68, 0.1); }
    }
`;
document.head.appendChild(style);

    // === User & Auth ===
    async loadUserInfo() {
        if (!auth.user) {
            await auth.checkAuth();
        }
        
        if (auth.user) {
            const userName = document.getElementById('userName');
            if (userName) {
                userName.textContent = auth.user.full_name || auth.user.username;
            }
        }
    }

    // === Call History ===
    async loadCallHistory() {
        try {
            const apiUrl = window.location.hostname === 'localhost' ? 'http://localhost:8000' : `http://${window.location.hostname}:8000`;
            const response = await auth.fetchWithAuth(`${apiUrl}/api/calls/history?limit=50`);
            const calls = await response.json();
            
            const historyContainer = document.getElementById('callsHistory');
            if (!calls || calls.length === 0) {
                historyContainer.innerHTML = '<div class="empty-state"><p>История звонков пуста</p></div>';
                return;
            }

            historyContainer.innerHTML = calls.map(call => `
                <div class="history-item">
                    <div class="history-item-header">
                        <span class="history-item-number">${this.formatPhoneNumber(call.caller_number === auth.user.sip_username ? call.called_number : call.caller_number)}</span>
                        <span class="history-item-direction ${call.direction}">${call.direction === 'inbound' ? '📥 Входящий' : '📤 Исходящий'}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span class="history-item-time">${this.formatDateTime(call.started_at)}</span>
                        ${call.duration ? `<span class="history-item-duration">${this.formatDuration(call.duration)}</span>` : ''}
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load call history:', error);
        }
    }

    formatDateTime(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        
        // Если сегодня
        if (diff < 86400000 && date.getDate() === now.getDate()) {
            return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
        }
        
        // Если вчера
        const yesterday = new Date(now);
        yesterday.setDate(yesterday.getDate() - 1);
        if (date.getDate() === yesterday.getDate()) {
            return 'Вчера, ' + date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
        }
        
        // Иначе полная дата
        return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' }) + ', ' + date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
    }

    formatDuration(seconds) {
        if (!seconds) return '';
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    // === Tabs ===
    setupTabs() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        tabBtns.forEach(btn => {
            btn.addEventListener('click', async () => {
                const tab = btn.dataset.tab;
                
                // Update active tab button
                tabBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // Show corresponding content
                const activeContent = document.querySelector(`[data-tab-content="active"]`);
                const historyContent = document.querySelector(`[data-tab-content="history"]`);
                
                if (tab === 'active') {
                    activeContent.style.display = '';
                    historyContent.style.display = 'none';
                } else {
                    activeContent.style.display = 'none';
                    historyContent.style.display = '';
                    await this.loadCallHistory();
                }
            });
        });
    }

    // === Outbound Calls ===
    setupOutboundCalls() {
        const makeCallBtn = document.getElementById('makeCallBtn');
        const outboundNumber = document.getElementById('outboundNumber');
        
        if (makeCallBtn) {
            makeCallBtn.addEventListener('click', () => {
                const number = outboundNumber.value.trim();
                if (number) {
                    this.makeOutboundCall(number);
                } else {
                    alert('Введите номер телефона');
                }
            });
        }
        
        if (outboundNumber) {
            outboundNumber.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    makeCallBtn.click();
                }
            });
        }
    }

    makeOutboundCall(number) {
        if (!this.isPhoneConnected) {
            alert('Сначала подключите телефон!');
            return;
        }
        
        console.log('Making outbound call to:', number);
        this.phone.call(number);
    }

    // === Logout ===
    setupLogout() {
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                if (confirm('Вы уверены что хотите выйти?')) {
                    auth.logout();
                }
            });
        }
    }
}

// Override init method
AICallAgent.prototype.init = function() {
    this.loadUserInfo();
    this.connectWebSocket();
    this.bindEvents();
    this.setupTabs();
    this.setupOutboundCalls();
    this.setupLogout();
};

// Initialize app after auth check
document.addEventListener('DOMContentLoaded', async () => {
    // Wait for auth check
    await new Promise(resolve => setTimeout(resolve, 100));
    
    if (auth.isAuthenticated()) {
        window.app = new AICallAgent();
    }
});
