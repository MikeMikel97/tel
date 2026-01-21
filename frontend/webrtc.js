/**
 * WebRTC Phone Client для подключения к Asterisk через JsSIP
 */

class WebRTCPhone {
    constructor(config) {
        this.config = {
            domain: config.domain || 'localhost',
            server: config.server || 'ws://localhost:8088/asterisk/ws',
            username: config.username || 'operator',
            password: config.password || 'operator123',
            realm: config.realm || 'asterisk',
            ...config
        };
        
        this.phone = null;
        this.session = null;
        this.isConnected = false;
        this.isInCall = false;
        this.remoteAudio = null;
        
        this.onConnected = config.onConnected || (() => {});
        this.onDisconnected = config.onDisconnected || (() => {});
        this.onIncomingCall = config.onIncomingCall || (() => {});
        this.onCallStarted = config.onCallStarted || (() => {});
        this.onCallEnded = config.onCallEnded || (() => {});
        this.onError = config.onError || (() => {});
    }
    
    async connect() {
        try {
            if (!window.JsSIP) {
                throw new Error('JsSIP library not loaded');
            }
            
            console.log('Initializing JsSIP...');
            
            const socket = new JsSIP.WebSocketInterface(this.config.server);
            
            const configuration = {
                sockets: [socket],
                uri: `sip:${this.config.username}@${this.config.domain}`,
                password: this.config.password,
                authorization_user: this.config.username,
                realm: this.config.realm,
                register: true,
                session_timers: false,
                connection_recovery_max_interval: 30,
                connection_recovery_min_interval: 2,
                hack_ip_in_contact: true
            };
            
            this.phone = new JsSIP.UA(configuration);
            
            // События соединения
            this.phone.on('connected', (e) => {
                console.log('WebRTC Phone connected to WebSocket');
            });
            
            this.phone.on('disconnected', (e) => {
                console.log('WebRTC Phone disconnected');
                this.isConnected = false;
                this.onDisconnected();
            });
            
            this.phone.on('registered', (e) => {
                console.log('✅ WebRTC Phone registered successfully!');
                this.isConnected = true;
                this.onConnected();
            });
            
            this.phone.on('registrationFailed', (e) => {
                console.error('❌ Registration failed:', e.cause);
                this.onError(new Error(`Registration failed: ${e.cause}`));
            });
            
            // Входящий звонок
            this.phone.on('newRTCSession', (e) => {
                const session = e.session;
                
                if (session.direction === 'incoming') {
                    console.log('📞 Incoming call:', session);
                    this.handleIncomingCall(session);
                }
            });
            
            this.phone.start();
            
            console.log('WebRTC Phone initialized');
            
        } catch (error) {
            console.error('Failed to connect WebRTC phone:', error);
            this.onError(error);
            throw error;
        }
    }
    
    disconnect() {
        if (this.session) {
            this.hangup();
        }
        
        if (this.phone) {
            this.phone.stop();
        }
        
        this.isConnected = false;
    }
    
    handleIncomingCall(session) {
        this.session = session;
        
        const callerNumber = session.remote_identity.uri.user || 'Unknown';
        
        // События сессии
        session.on('accepted', () => {
            console.log('✅ Call accepted');
            this.isInCall = true;
            this.setupRemoteAudio(session);
            this.onCallStarted();
        });
        
        session.on('ended', () => {
            console.log('📴 Call ended');
            this.handleCallEnd();
        });
        
        session.on('failed', (e) => {
            console.error('❌ Call failed:', e.cause);
            this.handleCallEnd();
        });
        
        this.onIncomingCall({
            callerNumber,
            accept: () => this.acceptCall(),
            reject: () => this.rejectCall()
        });
    }
    
    async acceptCall() {
        if (!this.session) return;
        
        try {
            console.log('Accepting call...');
            
            const options = {
                mediaConstraints: {
                    audio: true,
                    video: false
                },
                pcConfig: {
                    iceServers: [
                        { urls: 'stun:stun.l.google.com:19302' }
                    ]
                }
            };
            
            // Debug ICE connection state
            this.session.on('peerconnection', (data) => {
                console.log('🔗 PeerConnection created:', data.peerconnection);
                
                data.peerconnection.addEventListener('icecandidate', (event) => {
                    if (event.candidate) {
                        console.log('🧊 ICE Candidate:', event.candidate.candidate);
                    } else {
                        console.log('🧊 ICE Gathering complete');
                    }
                });
                
                data.peerconnection.addEventListener('iceconnectionstatechange', () => {
                    console.log('🧊 ICE connection state:', data.peerconnection.iceConnectionState);
                    if (data.peerconnection.iceConnectionState === 'failed') {
                        console.error('❌ ICE connection failed - no connectivity');
                    }
                    if (data.peerconnection.iceConnectionState === 'disconnected') {
                        console.warn('⚠️ ICE connection disconnected');
                    }
                });
                
                data.peerconnection.addEventListener('connectionstatechange', () => {
                    console.log('📡 Connection state:', data.peerconnection.connectionState);
                });
                
                data.peerconnection.addEventListener('icegatheringstatechange', () => {
                    console.log('🌐 ICE gathering state:', data.peerconnection.iceGatheringState);
                });
            });
            
            this.session.answer(options);
            
        } catch (error) {
            console.error('Failed to accept call:', error);
            this.onError(error);
        }
    }
    
    rejectCall() {
        if (this.session) {
            console.log('Rejecting call...');
            this.session.terminate();
            this.session = null;
        }
    }
    
    hangup() {
        if (this.session) {
            try {
                console.log('Hanging up...');
                this.session.terminate();
            } catch (e) {
                console.error('Error hanging up:', e);
            }
            this.handleCallEnd();
        }
    }
    
    setupRemoteAudio(session) {
        const remoteStream = new MediaStream();
        const peerConnection = session.connection;
        
        peerConnection.getReceivers().forEach((receiver) => {
            if (receiver.track) {
                remoteStream.addTrack(receiver.track);
            }
        });
        
        if (!this.remoteAudio) {
            this.remoteAudio = new Audio();
            this.remoteAudio.autoplay = true;
        }
        
        this.remoteAudio.srcObject = remoteStream;
        this.remoteAudio.play().catch(e => {
            console.error('Error playing remote audio:', e);
        });
    }
    
    call(number) {
        if (!this.phone || !this.isConnected) {
            console.error('❌ Phone not connected');
            this.onError(new Error('Phone not connected'));
            return;
        }
        
        if (this.isInCall) {
            console.error('❌ Already in a call');
            this.onError(new Error('Already in a call'));
            return;
        }
        
        const uri = `sip:${number}@${this.config.domain}`;
        console.log(`📞 Making call to ${uri}`);
        
        const options = {
            mediaConstraints: {
                audio: true,
                video: false
            },
            pcConfig: {
                iceServers: [
                    { urls: ['stun:stun.l.google.com:19302'] }
                ]
            }
        };
        
        try {
            this.session = this.phone.call(uri, options);
            
            this.session.on('accepted', () => {
                console.log('✅ Call accepted');
                this.isInCall = true;
                this.setupRemoteAudio(this.session);
                this.onCallStarted();
            });
            
            this.session.on('ended', () => {
                console.log('📴 Call ended');
                this.handleCallEnd();
            });
            
            this.session.on('failed', (e) => {
                console.error('❌ Call failed:', e.cause);
                this.onError(new Error(`Call failed: ${e.cause}`));
                this.handleCallEnd();
            });
            
            this.session.on('peerconnection', (e) => {
                console.log('🔗 Peer connection established');
            });
            
        } catch (error) {
            console.error('❌ Error making call:', error);
            this.onError(error);
        }
    }
    
    handleCallEnd() {
        this.isInCall = false;
        this.session = null;
        
        if (this.remoteAudio) {
            this.remoteAudio.pause();
            this.remoteAudio.srcObject = null;
        }
        
        this.onCallEnded();
    }
}

// Export for use in app.js
window.WebRTCPhone = WebRTCPhone;
