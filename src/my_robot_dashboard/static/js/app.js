// Distributed Robot Control & Telemetry Frontend
let scene, camera, renderer, imuMesh;
let radarCanvas, radarCtx;
let evtSource = null;
let reconnectTimer = null;

document.addEventListener('DOMContentLoaded', () => {
    initThreeJS();
    initRadarCanvas();
    initEventStream();
    loadSavedMaps();
});

// ----------------- THREE.JS 3D IMU VISUALIZATION ----------------- //
function initThreeJS() {
    const container = document.getElementById('three-container');
    const width = container.clientWidth;
    const height = container.clientHeight;

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0f1d);

    camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(2.2, 1.8, 2.5);
    camera.lookAt(0, 0, 0);

    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    const loader = document.getElementById('three-loader');
    if (loader) loader.style.display = 'none';

    // Grid Plane
    const grid = new THREE.GridHelper(4, 16, 0x3b82f6, 0x1e293b);
    grid.position.y = -0.5;
    scene.add(grid);

    // Coordinate Axes (RGB = XYZ)
    const axes = new THREE.AxesHelper(1.0);
    scene.add(axes);

    // Virtual BNO086 Sensor PCB Board
    const geometry = new THREE.BoxGeometry(1.2, 0.1, 0.8);
    const materials = [
        new THREE.MeshStandardMaterial({ color: 0x1e293b }), // Right
        new THREE.MeshStandardMaterial({ color: 0x1e293b }), // Left
        new THREE.MeshStandardMaterial({ color: 0x059669 }), // Top (PCB Green)
        new THREE.MeshStandardMaterial({ color: 0x047857 }), // Bottom
        new THREE.MeshStandardMaterial({ color: 0x1e293b }), // Front
        new THREE.MeshStandardMaterial({ color: 0x1e293b })  // Back
    ];
    imuMesh = new THREE.Mesh(geometry, materials);
    scene.add(imuMesh);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight.position.set(3, 5, 4);
    scene.add(dirLight);

    function animate() {
        requestAnimationFrame(animate);
        renderer.render(scene, camera);
    }
    animate();

    window.addEventListener('resize', () => {
        const w = container.clientWidth;
        const h = container.clientHeight;
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
    });
}

// ----------------- 2D POLAR LIDAR RADAR ----------------- //
function initRadarCanvas() {
    radarCanvas = document.getElementById('radar-canvas');
    radarCtx = radarCanvas.getContext('2d');
    drawRadarSweep([]);
}

function drawRadarSweep(points) {
    if (!radarCtx) return;
    const w = radarCanvas.width;
    const h = radarCanvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const maxRange = 6.0; // 6 meters radius

    radarCtx.fillStyle = '#0a0f1d';
    radarCtx.fillRect(0, 0, w, h);

    // Range rings
    radarCtx.strokeStyle = 'rgba(59, 130, 246, 0.2)';
    radarCtx.lineWidth = 1;
    for (let r = 1; r <= 3; r++) {
        radarCtx.beginPath();
        radarCtx.arc(cx, cy, (r / 3.0) * (h / 2 - 10), 0, Math.PI * 2);
        radarCtx.stroke();
    }

    // Crosshairs
    radarCtx.beginPath();
    radarCtx.moveTo(cx, 10);
    radarCtx.lineTo(cx, h - 10);
    radarCtx.moveTo(10, cy);
    radarCtx.lineTo(w - 10, cy);
    radarCtx.stroke();

    // Center origin
    radarCtx.fillStyle = '#ef4444';
    radarCtx.beginPath();
    radarCtx.arc(cx, cy, 3, 0, Math.PI * 2);
    radarCtx.fill();

    // Plot Lidar points
    if (points && points.length > 0) {
        radarCtx.fillStyle = '#10b981';
        for (const pt of points) {
            const angle = pt[0];
            const dist = pt[1];
            const scale = (h / 2 - 10) / maxRange;
            const rPx = Math.min(dist * scale, h / 2 - 10);

            // Polar to Cartesian (ROS frame: angle 0 = forward X)
            const px = cx - rPx * Math.sin(angle);
            const py = cy - rPx * Math.cos(angle);

            radarCtx.beginPath();
            radarCtx.arc(px, py, 2, 0, Math.PI * 2);
            radarCtx.fill();
        }
    }
}

// ----------------- SSE REAL-TIME TELEMETRY STREAM ----------------- //
function initEventStream() {
    if (evtSource) {
        evtSource.close();
    }
    
    evtSource = new EventSource('/api/stream');

    evtSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            updateUI(data);
        } catch (e) {
            console.error("Error parsing telemetry SSE:", e);
        }
    };

    evtSource.onerror = () => {
        evtSource.close();
        if (!reconnectTimer) {
            reconnectTimer = setTimeout(() => {
                reconnectTimer = null;
                initEventStream();
            }, 1500);
        }
    };
}

function updateUI(data) {
    // 1. Hardware Status Badges & Hardware-Aware Gating
    isUnoqConnected = Boolean(data.unoq_online);
    const unoBadge = document.getElementById('unoq-status');
    const btnLidarStart = document.getElementById('btn-lidar-start');

    if (isUnoqConnected) {
        unoBadge.className = "badge bg-emerald-950/80 text-emerald-300 border border-emerald-800";
        unoBadge.innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-500 mr-2 animate-pulse"></span> Uno Q Connected';
        if (btnLidarStart && !btnLidarStart.dataset.originalHtml) {
            btnLidarStart.title = "Start RPLidar scanner stream";
            btnLidarStart.classList.remove('opacity-40', 'cursor-not-allowed');
        }
    } else {
        unoBadge.className = "badge bg-slate-800 text-slate-400 border border-slate-700";
        unoBadge.innerHTML = '<span class="w-2 h-2 rounded-full bg-rose-500 mr-2"></span> Uno Q Offline';
        if (btnLidarStart && !btnLidarStart.dataset.originalHtml) {
            btnLidarStart.title = "Uno Q is offline. Connect board to start scan.";
        }
    }


    // Rates
    const imuBadge = document.getElementById('imu-badge');
    imuBadge.innerHTML = `<span class="w-2 h-2 rounded-full ${data.imu_running ? 'bg-emerald-500' : 'bg-slate-500'} mr-2"></span> IMU: ${data.imu_rate} Hz`;
    document.getElementById('imu-hz-text').innerText = `${data.imu_rate} Hz`;

    const lidarBadge = document.getElementById('lidar-badge');
    lidarBadge.innerHTML = `<span class="w-2 h-2 rounded-full ${data.lidar_running ? 'bg-emerald-500' : 'bg-slate-500'} mr-2"></span> Lidar: ${data.lidar_rate} Hz`;
    document.getElementById('lidar-hz-text').innerText = `${data.lidar_rate} Hz`;

    document.getElementById('imu-state-tag').innerText = data.imu_running ? 'Running' : 'Stopped';
    document.getElementById('lidar-state-tag').innerText = data.lidar_running ? 'Scanning' : 'Stopped';

    // 2. 3D IMU Euler Angles
    document.getElementById('val-roll').innerText = `${data.roll_deg}°`;
    document.getElementById('val-pitch').innerText = `${data.pitch_deg}°`;
    document.getElementById('val-yaw').innerText = `${data.yaw_deg}°`;

    // 3. Accelerometer & Gyro
    document.getElementById('val-ax').innerText = data.acc.x;
    document.getElementById('val-ay').innerText = data.acc.y;
    document.getElementById('val-az').innerText = data.acc.z;

    document.getElementById('val-gx').innerText = data.gyro.x;
    document.getElementById('val-gy').innerText = data.gyro.y;
    document.getElementById('val-gz').innerText = data.gyro.z;

    // 4. Update Three.js Mesh Orientation
    if (imuMesh && data.quat) {
        const q = new THREE.Quaternion(data.quat.x, data.quat.z, -data.quat.y, data.quat.w);
        imuMesh.setRotationFromQuaternion(q);
    }

    // 5. Update 2D Radar Canvas
    drawRadarSweep(data.lidar_points);
}

// ----------------- API ACTION HANDLERS WITH SPINNERS & GATING ----------------- //
let isUnoqConnected = false;

function setButtonLoading(btn, isLoading, loadingText = null) {
    if (!btn) return;
    if (isLoading) {
        btn.dataset.originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin mr-1.5"></i> ${loadingText || 'Processing...'}`;
    } else {
        btn.disabled = false;
        if (btn.dataset.originalHtml) {
            btn.innerHTML = btn.dataset.originalHtml;
        }
    }
}

function apiCall(endpoint, payload = null, btnElement = null) {
    // 1. Hardware-Aware Pre-Flight Check for Sensor Launch
    if (endpoint === '/api/sensors/lidar/start' && !isUnoqConnected) {
        showToast("Cannot Start Scan: Arduino Uno Q is disconnected / offline.", false);
        return;
    }

    if (btnElement) {
        setButtonLoading(btnElement, true);
    }

    const opts = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload || {})
    };

    fetch(endpoint, opts)
        .then(async res => {
            const rawText = await res.text();
            try {
                return JSON.parse(rawText);
            } catch (e) {
                const cleanText = rawText.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
                return {
                    success: res.ok,
                    message: cleanText ? cleanText.substring(0, 120) : `HTTP ${res.status} ${res.statusText}`
                };
            }
        })
        .then(data => {
            showToast(data.message || 'Action executed', data.success !== false);
        })
        .catch(err => {
            showToast(`Network Error: ${err.message || err}`, false);
        })
        .finally(() => {
            if (btnElement) {
                setButtonLoading(btnElement, false);
            }
        });
}

function confirmAction(msg, endpoint, btnElement = null) {
    if (confirm(msg)) {
        if (endpoint === '/api/system/shutdown_all') {
            showToast("System shutting down completely...", true);
            if (evtSource) {
                evtSource.close();
            }
            if (btnElement) {
                setButtonLoading(btnElement, true, 'Shutting down...');
            }
            apiCall(endpoint);
            setTimeout(() => {
                document.body.innerHTML = `
                    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh; background:#0b0f19; color:#94a3b8; font-family:monospace; text-align:center;">
                        <h1 style="color:#ef4444; font-size:24px; margin-bottom:12px;">SYSTEM SHUT DOWN</h1>
                        <p style="font-size:14px; max-width:450px; line-height:1.6;">All ROS 2 nodes, edge sensor streams, and dashboard servers have been safely terminated.</p>
                        <p style="font-size:12px; margin-top:20px; color:#64748b;">To restart, run <code style="color:#38bdf8; background:#1e293b; padding:4px 8px; rounded:4px;">./start_dashboard.sh</code> in your terminal.</p>
                    </div>
                `;
            }, 800);
            return;
        }
        apiCall(endpoint, null, btnElement);
    }
}

function saveCurrentMap(btnElement = null) {
    const mapName = prompt("Enter name for map file (e.g. room_map_1):", `map_${Date.now()}`);
    if (mapName) {
        apiCall('/api/slam/save_map', { name: mapName }, btnElement);
        setTimeout(loadSavedMaps, 2500);
    }
}

function regularizeLatestMap(btnElement = null) {
    showToast("Snapping map to 90° boxy walls...", true);
    apiCall('/api/slam/regularize_map', null, btnElement);
    setTimeout(loadSavedMaps, 2500);
}


function loadSavedMaps() {
    fetch('/api/slam/list_maps')
        .then(res => res.json())
        .then(maps => {
            const list = document.getElementById('saved-maps-list');
            if (!maps || maps.length === 0) {
                list.innerHTML = '<li class="italic text-slate-500">No maps saved yet.</li>';
                return;
            }
            list.innerHTML = maps.map(m => {
                const isReg = m.includes('_regularized');
                const badge = isReg ? '<span class="text-[9px] bg-cyan-950 text-cyan-300 border border-cyan-800 px-1.5 py-0.5 rounded font-bold">Boxy 90°</span>' : '<span class="text-[10px] text-emerald-400">Raw</span>';
                return `
                <li class="flex justify-between items-center bg-slate-900/60 p-1.5 rounded text-slate-300 font-mono text-[11px]">
                    <span class="truncate max-w-[150px]"><i class="fa-solid fa-file-lines ${isReg ? 'text-cyan-400' : 'text-amber-400'} mr-1.5"></i> ${m}</span>
                    ${badge}
                </li>
                `;
            }).join('');
        })
        .catch(err => console.error("Error loading maps:", err));
}

function showToast(msg, isSuccess = true) {
    const toast = document.getElementById('toast');
    const toastMsg = document.getElementById('toast-msg');
    const toastIcon = document.getElementById('toast-icon');

    toastMsg.innerText = msg;
    toastIcon.className = isSuccess ? "fa-solid fa-circle-check text-emerald-400 text-lg" : "fa-solid fa-circle-xmark text-rose-400 text-lg";

    toast.classList.remove('translate-y-20', 'opacity-0');
    toast.classList.add('translate-y-0', 'opacity-100');

    setTimeout(() => {
        toast.classList.remove('translate-y-0', 'opacity-100');
        toast.classList.add('translate-y-20', 'opacity-0');
    }, 4000);
}
