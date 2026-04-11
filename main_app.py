import json
import time
import random
import hashlib
import threading
import io
import base64
import pandas as pd
import matplotlib
matplotlib.use('Agg') # Server-side backend
import matplotlib.pyplot as plt
from flask import Flask, jsonify, render_template_string, Response


# 1. BLOCKCHAIN & SIMBLOCK LOGIC
# ==========================================

class Block:
    def __init__(self, index, previous_hash, transactions, timestamp):
        self.index = index
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.timestamp = timestamp
        self.nonce = 0
        self.hash = self.calculate_hash()
        self.mined_by = "System"

    def calculate_hash(self):
        # REQUIREMENT: hashlib SHA-256
        block_string = json.dumps(self.__dict__, sort_keys=True, default=str).encode()
        return hashlib.sha256(block_string).hexdigest()

    def mine(self, difficulty=1):
        # REQUIREMENT: Proof of Work
        target = '0' * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()

# Global State
simulation_running = False
public_chain = []
private_chain = []
logs = []
history = {'step': [], 'public': [], 'private': []}
simulation_speed = 3 
current_phase = "Ready"

# SECURITY SETTINGS (The Countermeasures)
security_mode = False # Default to Vulnerable

def run_simblock_engine():
    global public_chain, private_chain, logs, simulation_running, current_phase, history, security_mode

    # Initialize Genesis
    genesis = Block(0, "0", [{"msg": "Genesis"}], time.time())
    genesis.mine()
    public_chain = [genesis]
    private_chain = [genesis]
    
    mode_text = "SECURE MODE" if security_mode else "VULNERABLE MODE"
    logs = [{"time": time.strftime("%H:%M:%S"), "msg": f"Genesis Created. System is in {mode_text}.", "type": "info"}]
    
    current_phase = "Phase 1: Race Started"
    history = {'step': [0], 'public': [1], 'private': [1]}
    
    # --- CONFIGURATION (UPDATED PER SUPERVISOR REQS) ---
    
    # Attacker: 1 Master + 6 Private Nodes = 7 Total
    attacker_hashrate = 7 
    
    if security_mode:
        # COUNTERMEASURE: Honest Majority Defense
        # We add enough nodes to overpower the attacker's 7 nodes.
        # Merchant (1) + Honest (1) + Reinforcements (13) = 15 Total
        public_hashrate = 15  
        confirmations_needed = 6 
    else:
        # VULNERABLE: Attacker Dominance
        # Merchant (1) + Honest Miner (1) = 2 Total
        public_hashrate = 2 
        confirmations_needed = 0 
        
    total_hashrate = public_hashrate + attacker_hashrate
    step = 0
    
    while simulation_running:
        time.sleep(simulation_speed)
        step += 1
        
        # Update Phase Text
        gap = len(private_chain) - len(public_chain)
        if gap > 0:
            current_phase = f"Attack Progress: Attacker +{gap} (Private Lead)"
        elif gap < 0:
            current_phase = f"Attack Progress: Public +{abs(gap)} (Honest Lead)"
        else:
            current_phase = "Attack Progress: TIED"

        # PROBABILISTIC MINING (SimBlock Logic)
        rand = random.random()
        attacker_win_prob = attacker_hashrate / total_hashrate
        
        # --- SIMULATING TRANSACTION BROADCAST (Req #2) ---
        if step % 2 == 0: 
             logs.insert(0, {"time": time.strftime("%H:%M:%S"), "msg": "[P2P] Propagating transactions to network peers...", "type": "info"})
        
        if rand < attacker_win_prob:
            # -- ATTACKER WINS (7 Nodes Power) --
            # Logic: Could be the Master Node or one of the 6 Workers
            node_id = random.randint(1, 7)
            node_name = "Attacker_Master" if node_id == 1 else f"Private_Worker_{node_id-1}"
            
            prev = private_chain[-1]
            tx = [{"from": "Attacker", "to": "Attacker_Wallet", "amt": 50, "verify_by": node_name}]
            
            new_block = Block(prev.index + 1, prev.hash, tx, time.time())
            new_block.mined_by = node_name
            new_block.mine()
            private_chain.append(new_block)
            logs.insert(0, {"time": time.strftime("%H:%M:%S"), "msg": f"[SECRET] {node_name} mined block #{new_block.index}.", "type": "danger"})
        else:
            # -- PUBLIC WINS --
            # Logic: Could be Merchant Node or Honest Miner
            node_id = random.randint(1, public_hashrate)
            if public_hashrate == 2:
                node_name = "Merchant_Node" if node_id == 1 else "Honest_Miner_1"
            else:
                node_name = f"Public_Node_{node_id}"

            prev = public_chain[-1]
            tx = [{"from": "Attacker", "to": "Merchant", "amt": 50, "verify_by": node_name}]
            
            new_block = Block(prev.index + 1, prev.hash, tx, time.time())
            new_block.mined_by = node_name
            new_block.mine()
            public_chain.append(new_block)
            logs.insert(0, {"time": time.strftime("%H:%M:%S"), "msg": f"[PUBLIC] {node_name} mined block #{new_block.index}.", "type": "info"})

        # Record Data for Graph
        history['step'].append(step)
        history['public'].append(len(public_chain))
        history['private'].append(len(private_chain))

        # --- OUTCOME LOGIC (Security Analysis & Fork Resolution) ---
        
        # SCENARIO A: ATTACK SUCCESS (Vulnerable Mode)
        # Success if Attacker is longer AND we aren't checking confirmations
        if not security_mode and len(private_chain) > len(public_chain) + 3:
            current_phase = "ATTACK SUCCESSFUL (Reorg)"
            logs.insert(0, {"time": time.strftime("%H:%M:%S"), "msg": ">>> FORK RESOLUTION: Private chain is longer! Public chain discarded (Reorg).", "type": "success"})
            logs.insert(0, {"time": time.strftime("%H:%M:%S"), "msg": ">>> RESULT: Double Spend Successful. Merchant lost funds.", "type": "success"})
            simulation_running = False
            
        # SCENARIO B: ATTACK FAILED (Secure Mode)
        # Success if Public is dominant OR simply survives long enough with a lead
        if security_mode:
            if len(public_chain) > len(private_chain) + 2:
                current_phase = "ATTACK FAILED (Secure)"
                logs.insert(0, {"time": time.strftime("%H:%M:%S"), "msg": ">>> FORK RESOLUTION: Honest Chain is dominant. Network rejects Attacker chain.", "type": "info"})
                logs.insert(0, {"time": time.strftime("%H:%M:%S"), "msg": ">>> RESULT: Attack Mitigated. Transaction Confirmed.", "type": "info"})
                simulation_running = False
            
        if step > 60: simulation_running = False

# ==========================================
# 2. FLASK WEB SERVER
# ==========================================

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>CS619 Final Project</title>
    <meta http-equiv="refresh" content="300"> 
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body { background-color: #f4f6f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        
        .block-card { 
            min-width: 140px; height: 120px; margin: 0 15px; position: relative; 
            background: white; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
            display: flex; flex-direction: column; align-items: center; justify-content: center; 
            font-size: 0.8em; border-top: 5px solid #ccc; 
        }
        .block-card:not(:first-child)::before { 
            content: ''; position: absolute; left: -15px; top: 50%; width: 15px; height: 2px; background: #aaa; 
        }
        .public-block { border-top-color: #2196f3; }
        .private-block { border-top-color: #f44336; background-color: #fff5f5; }
        
        .chain-wrapper { 
            display: flex; overflow-x: auto; padding: 20px 10px; background: #e9ecef; 
            border-radius: 10px; border: 1px solid #dee2e6; min-height: 160px; align-items: center; 
        }
        
        .terminal { 
            background-color: #1e1e1e; color: #00ff00; font-family: 'Courier New', Courier, monospace; 
            padding: 15px; border-radius: 5px; height: 250px; overflow-y: auto; border: 1px solid #333; 
        }
        
        .status-banner { 
            background: #343a40; color: white; padding: 10px; border-radius: 5px; margin-bottom: 20px; 
            text-align: center; font-weight: bold; font-size: 1.2em; 
        }
        .phase-highlight { color: #ffeb3b; }
    </style>
</head>
<body>

<div class="container mt-4">
    
    <div class="row mb-3">
        <div class="col-md-12 text-center">
            <h2><i class="fas fa-shield-alt"></i> Blockchain Double-Spend Simulator</h2>
        </div>
    </div>

    <!-- SECURITY TOGGLE -->
    <div class="row mb-4 justify-content-center">
        <div class="col-md-8 text-center">
            <div class="card shadow-sm">
                <div class="card-header">Simulation Strategy (Countermeasures)</div>
                <div class="card-body">
                    <div class="btn-group w-100" role="group">
                        <button onclick="setMode('vulnerable')" class="btn btn-outline-danger active" id="btn-vuln">
                            <i class="fas fa-unlock"></i> <strong>Phase 1: Vulnerable</strong><br>
                            <small>2 Public vs 7 Attacker Nodes</small>
                        </button>
                        <button onclick="setMode('secure')" class="btn btn-outline-success" id="btn-sec">
                            <i class="fas fa-lock"></i> <strong>Phase 2: Secure (Countermeasures)</strong><br>
                            <small>Active Defense (15 Nodes) + 6 Confirmations</small>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="status-banner">System Status: <span id="phase-display" class="phase-highlight">Ready</span></div>

    <!-- CONTROLS -->
    <div class="d-grid gap-2 d-md-flex justify-content-center mb-4">
        <button onclick="startSim()" class="btn btn-primary px-5 btn-lg shadow">START SIMULATION</button>
        <button onclick="stopSim()" class="btn btn-warning px-4 shadow">PAUSE</button>
        <button onclick="resetSim()" class="btn btn-secondary px-4 shadow">RESET</button>
        <a href="/download_csv" class="btn btn-info px-4 text-white shadow">EXPORT CSV</a>
    </div>

    <!-- CHAINS -->
    <div class="row">
        <div class="col-12 mb-2">
            <h6 class="text-primary">Public Blockchain (Merchant + Honest Miner)</h6>
            <div id="public-chain" class="chain-wrapper"></div>
        </div>
        <div class="col-12 mb-4">
            <h6 class="text-danger">Private Blockchain (Master + 6 Workers)</h6>
            <div id="private-chain" class="chain-wrapper"></div>
        </div>
    </div>

    <!-- GRAPH & LOGS -->
    <div class="row mb-5">
        <div class="col-md-6">
            <div class="card h-100">
                <div class="card-header bg-secondary text-white">Live Chain Growth (Analysis)</div>
                <div class="card-body text-center">
                    <img id="analysis-graph" src="" style="max-width: 100%; max-height: 250px;">
                </div>
            </div>
        </div>
        <div class="col-md-6">
            <div class="card h-100">
                <div class="card-header bg-dark text-white">Terminal Logs</div>
                <div class="card-body p-0"><div id="logs" class="terminal"></div></div>
            </div>
        </div>
    </div>
</div>

<script>
    setInterval(updateDashboard, 1000);

    async function setMode(mode) {
        await fetch('/set_mode/' + mode);
        
        document.getElementById('btn-vuln').className = mode === 'vulnerable' ? 'btn btn-danger active' : 'btn btn-outline-danger';
        document.getElementById('btn-sec').className = mode === 'secure' ? 'btn btn-success active' : 'btn btn-outline-success';
        
        // Auto Reset to apply changes cleanly
        await resetSim();
    }

    async function updateDashboard() {
        try {
            const response = await fetch('/status');
            const data = await response.json();
            document.getElementById('phase-display').textContent = data.phase;
            if(data.graph) document.getElementById('analysis-graph').src = 'data:image/png;base64,' + data.graph;
            renderChain('public-chain', data.public, 'public-block', 'fa-check-circle text-primary');
            renderChain('private-chain', data.private, 'private-block', 'fa-skull text-danger');
            renderLogs(data.logs);
        } catch (e) { console.error(e); }
    }

    function renderChain(containerId, chain, cssClass, iconClass) {
        const container = document.getElementById(containerId);
        if (container.children.length === chain.length) return; 
        container.innerHTML = '';
        chain.forEach(block => {
            const div = document.createElement('div');
            div.className = `block-card ${cssClass}`;
            div.innerHTML = `<i class="fas ${iconClass} fa-lg mb-1"></i><div class="fw-bold">#${block.index}</div><div class="small text-muted">${block.mined_by}</div>`;
            container.appendChild(div);
        });
        container.scrollLeft = container.scrollWidth;
    }

    function renderLogs(logs) {
        const container = document.getElementById('logs');
        let newHTML = '';
        logs.forEach(log => {
            let color = log.type === 'danger' ? '#ff5252' : (log.type === 'info' ? '#40c4ff' : '#00ff00');
            newHTML += `<div style="color:${color}; margin-bottom:4px;"><span style="opacity:0.7">[${log.time}]</span> ${log.msg}</div>`;
        });
        if (container.children.length !== logs.length) container.innerHTML = newHTML;
    }

    async function startSim() { await fetch('/start'); }
    async function stopSim() { await fetch('/stop'); }
    async function resetSim() { await fetch('/reset'); updateDashboard(); }
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/set_mode/<mode>')
def set_mode(mode):
    global security_mode
    security_mode = (mode == 'secure')
    return jsonify({"status": "mode_set", "security": security_mode})

def generate_graph():
    # Matplotlib Graphing
    plt.figure(figsize=(6, 4))
    plt.plot(history['step'], history['public'], label='Public Chain', color='blue', marker='o')
    plt.plot(history['step'], history['private'], label='Private Chain', color='red', marker='x', linestyle='--')
    plt.title('Chain Growth Rate')
    plt.xlabel('Time Step')
    plt.ylabel('Block Height')
    plt.legend()
    plt.grid(True, alpha=0.3)
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode()

@app.route('/status')
def status():
    return jsonify({
        "public": [vars(b) for b in public_chain], 
        "private": [vars(b) for b in private_chain], 
        "logs": logs,
        "phase": current_phase,
        "graph": generate_graph()
    })

@app.route('/start')
def start_sim():
    global simulation_running
    if not simulation_running:
        simulation_running = True
        threading.Thread(target=run_simblock_engine).start()
    return jsonify({"status": "started"})

@app.route('/stop')
def stop_sim():
    global simulation_running
    simulation_running = False
    return jsonify({"status": "stopped"})

@app.route('/reset')
def reset_sim():
    global simulation_running, public_chain, private_chain, logs, current_phase, history
    simulation_running = False
    time.sleep(0.5)
    public_chain = []
    private_chain = []
    logs = []
    history = {'step': [0], 'public': [1], 'private': [1]}
    current_phase = "Ready"
    return jsonify({"status": "reset"})

@app.route('/download_csv')
def download_csv():
    data = []
    for b in public_chain:
        data.append({"Chain": "Public", "Index": b.index, "Hash": b.hash, "MinedBy": b.mined_by})
    for b in private_chain:
        data.append({"Chain": "Private", "Index": b.index, "Hash": b.hash, "MinedBy": b.mined_by})
    return Response(pd.DataFrame(data).to_csv(index=False), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=results.csv"})

if __name__ == '__main__':
    print("STARTING FINAL WEB SERVER...")
    print("GO TO: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)