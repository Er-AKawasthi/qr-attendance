document.addEventListener('DOMContentLoaded', () => {
    const statusIndicator = document.getElementById('connection-status');
    const btnStart = document.getElementById('btn-start');
    const btnStop = document.getElementById('btn-stop');
    const qrDisplayArea = document.getElementById('qr-display-area');
    const qrImage = document.getElementById('qr-image');
    const qrOverlay = document.querySelector('.qr-overlay');
    const countdownEl = document.getElementById('countdown');
    const progressCircle = document.querySelector('.progress-ring__circle');
    const countPresent = document.getElementById('count-present');
    const countTotal = document.getElementById('count-total');
    const recentScansList = document.getElementById('recent-scans-list');
    
    let socket = null;
    let reconnectTimer = null;
    let countdownInterval = null;
    let currentExpiresIn = 60;
    let sessionActive = false;
    let seenRolls = new Set();
    
    const circumference = 2 * Math.PI * 34; // r=34

    function init() {
        connectWebSocket();
        setupEventListeners();
    }

    function setupEventListeners() {
        if(btnStart) {
            btnStart.addEventListener('click', () => toggleSession(true));
        }
        if(btnStop) {
            btnStop.addEventListener('click', () => toggleSession(false));
        }
    }

    async function toggleSession(start) {
        try {
            const endpoint = start ? '/api/session/start' : '/api/session/stop';
            btnStart.disabled = true;
            btnStop.disabled = true;
            
            const response = await fetch(endpoint, { method: 'POST' });
            if (!response.ok) throw new Error('Network response was not ok');
            
            updateControlsState(start);
        } catch (error) {
            console.error('Error toggling session:', error);
            alert('Failed to change session state. Please try again.');
            updateControlsState(sessionActive);
        } finally {
            btnStart.disabled = false;
            btnStop.disabled = false;
        }
    }

    function updateControlsState(isActive) {
        sessionActive = isActive;
        if (isActive) {
            btnStart.classList.add('hidden');
            btnStop.classList.remove('hidden');
            qrDisplayArea.classList.remove('hidden');
            qrOverlay.classList.add('hidden');
        } else {
            btnStart.classList.remove('hidden');
            btnStop.classList.add('hidden');
            qrOverlay.classList.remove('hidden');
            stopTimer();
        }
    }

    function updateStats(present, total) {
        if (parseInt(countPresent.textContent) !== present) {
            countPresent.classList.remove('count-up-pulse');
            void countPresent.offsetWidth; // Reflow
            countPresent.classList.add('count-up-pulse');
            countPresent.textContent = present;
        }
        countTotal.textContent = total;
    }

    function updateRecentScans(recentList) {
        const emptyState = recentScansList.querySelector('.empty-state');
        if (emptyState && recentList.length > 0) {
            emptyState.remove();
        }

        recentList.forEach(student => {
            if (!seenRolls.has(student.roll)) {
                seenRolls.add(student.roll);
                
                const li = document.createElement('li');
                li.className = 'scan-item slide-in';
                li.innerHTML = `
                    <div class="scan-student">✅ ${student.roll} - ${student.name}</div>
                    <div class="scan-time">${student.time}</div>
                `;
                
                recentScansList.insertBefore(li, recentScansList.firstChild);
                
                if (recentScansList.children.length > 50) {
                    recentScansList.removeChild(recentScansList.lastChild);
                }
            }
        });
    }

    function startTimer(duration) {
        stopTimer();
        let timeRemaining = duration;
        currentExpiresIn = duration;
        
        updateTimerDisplay(timeRemaining);
        
        countdownInterval = setInterval(() => {
            timeRemaining -= 1;
            if (timeRemaining < 0) {
                timeRemaining = 0;
                stopTimer();
            }
            updateTimerDisplay(timeRemaining);
        }, 1000);
    }

    function stopTimer() {
        if (countdownInterval) {
            clearInterval(countdownInterval);
            countdownInterval = null;
        }
    }

    function updateTimerDisplay(seconds) {
        countdownEl.textContent = seconds;
        const offset = circumference - (seconds / currentExpiresIn) * circumference;
        progressCircle.style.strokeDashoffset = offset;
        
        if (seconds <= 5) {
            progressCircle.style.stroke = '#e74c3c';
            countdownEl.style.color = '#e74c3c';
        } else {
            progressCircle.style.stroke = '#4ecdc4';
            countdownEl.style.color = 'var(--accent-primary)';
        }
    }

    function connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/qr`;
        
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            statusIndicator.textContent = 'Connected';
            statusIndicator.className = 'status-indicator connected';
            console.log('WebSocket connected');
            if(reconnectTimer) clearTimeout(reconnectTimer);
        };

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleWebSocketData(data);
            } catch (e) {
                console.error('Error parsing WS message:', e);
            }
        };

        socket.onclose = () => {
            statusIndicator.textContent = 'Disconnected - Reconnecting...';
            statusIndicator.className = 'status-indicator disconnected';
            stopTimer();
            console.log('WebSocket disconnected. Attempting to reconnect...');
            reconnectTimer = setTimeout(connectWebSocket, 3000);
        };

        socket.onerror = (err) => {
            console.error('WebSocket error:', err);
            socket.close();
        };
    }

    function handleWebSocketData(message) {
        if (message.type === 'attendance') {
            // Live attendance notification
            const student = message.data;
            addRecentScan({
                roll: student.roll_number,
                name: student.name,
                time: student.time || 'Just now'
            });
            return;
        }

        // State update
        const data = message.data || message;
        updateControlsState(data.session_active);

        if (data.session_active) {
            if (data.qr_base64) {
                qrImage.src = `data:image/png;base64,${data.qr_base64}`;
            }
            if (data.expires_in) {
                startTimer(data.expires_in);
            }
        }

        if (data.attendance_count !== undefined && data.total_students !== undefined) {
            updateStats(data.attendance_count, data.total_students);
        }

        if (data.recent && Array.isArray(data.recent)) {
            // Map backend field names to frontend format
            const mapped = data.recent.map(s => ({
                roll: s.roll_number || s.roll,
                name: s.name,
                time: s.marked_at ? new Date(s.marked_at).toLocaleTimeString('en-US', {hour: '2-digit', minute:'2-digit'}) : (s.time || '')
            }));
            updateRecentScans(mapped);
        }
    }

    function addRecentScan(student) {
        if (seenRolls.has(student.roll)) return;
        seenRolls.add(student.roll);
        
        const emptyState = recentScansList.querySelector('.empty-state');
        if (emptyState) emptyState.remove();

        const li = document.createElement('li');
        li.className = 'scan-item slide-in';
        li.innerHTML = `
            <div class="scan-student">✅ ${student.roll} - ${student.name}</div>
            <div class="scan-time">${student.time}</div>
        `;
        recentScansList.insertBefore(li, recentScansList.firstChild);
        
        if (recentScansList.children.length > 50) {
            recentScansList.removeChild(recentScansList.lastChild);
        }

        // Update counter
        const currentCount = parseInt(countPresent.textContent) || 0;
        updateStats(currentCount + 1, parseInt(countTotal.textContent) || 0);
    }

    init();
});
