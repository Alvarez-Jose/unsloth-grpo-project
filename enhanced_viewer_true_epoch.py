#!/usr/bin/env python3
import re
import time
import subprocess
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template_string

app = Flask(__name__)

CHECKPOINT_BASE_EPOCH = 83.33
STEPS_PER_EPOCH = 53.76
public_url = "Detecting..."

def get_tunnel_url():
    global public_url
    while True:
        try:
            result = subprocess.run(
                ['grep', '-a', '6006', '/var/log/portal/tunnel_manager.log'],
                capture_output=True, text=True
            )
            for line in reversed(result.stdout.splitlines()):
                if 'trycloudflare.com' in line:
                    import re as _re
                    m = _re.search(r'https://[\w\-]+\.trycloudflare\.com', line)
                    if m:
                        public_url = m.group(0)
                        break
        except:
            pass
        time.sleep(30)

def make_gpu_stats(gpu_id):
    return {
        'gpu_id': gpu_id,
        'current_step': 0,
        'total_steps': 10000,
        'loss': 0.0,
        'reward': 0.0,
        'best_reward': 0.0,
        'eta': 'Calculating...',
        'speed': '0.0 it/s',
        'speed_its': 0.0,
        'progress_percent': 0,
        'total_tokens': 0,
        'uptime': '0:00:00',
        'start_time': time.time(),
        'session_epoch': 0.0,
        'true_epoch': CHECKPOINT_BASE_EPOCH,
        'true_steps': 4500,
        'true_progress': 45.0,
        'last_task': '',
        'last_command': '',
        'last_score': 0.0,
        'status': 'Starting...',
        'log_lines': [],
    }

gpu_stats = {0: make_gpu_stats(0), 1: make_gpu_stats(1)}
stats_lock = threading.Lock()

def parse_training_output(line, gpu_id):
    with stats_lock:
        s = gpu_stats[gpu_id]
        s['log_lines'].append(line)
        if len(s['log_lines']) > 100:
            s['log_lines'] = s['log_lines'][-100:]
        epoch_match = re.search(r"'epoch': ([\d\.]+)", line)
        if epoch_match:
            session_epoch = float(epoch_match.group(1))
            s['session_epoch'] = session_epoch
            s['true_epoch'] = CHECKPOINT_BASE_EPOCH + session_epoch
            s['true_steps'] = int(s['true_epoch'] * STEPS_PER_EPOCH)
            s['true_progress'] = round((s['true_steps'] / 10000) * 100, 1)
            s['status'] = 'Training'
        step_match = re.search(r'\|\s*(\d+)/(\d+)\s*\[', line)
        if step_match:
            s['current_step'] = int(step_match.group(1))
            s['total_steps'] = int(step_match.group(2))
            s['progress_percent'] = round((s['current_step'] / s['total_steps']) * 100, 1)
        speed_match = re.search(r'([\d\.]+)it/s', line)
        if speed_match:
            its = float(speed_match.group(1))
            s['speed_its'] = its
            s['speed'] = f"{its:.2f} it/s"
            if s['current_step'] > 0 and its > 0:
                remaining = s['total_steps'] - s['current_step']
                s['eta'] = str(timedelta(seconds=int(remaining / its)))
        loss_match = re.search(r"'loss': (-?[\d\.]+)", line)
        if loss_match:
            s['loss'] = float(loss_match.group(1))
        reward_match = re.search(r"'reward': (-?[\d\.]+)", line)
        if reward_match:
            val = float(reward_match.group(1))
            s['reward'] = val
            if val > s['best_reward']:
                s['best_reward'] = val
        tokens_match = re.search(r"'num_tokens': ([\d]+)", line)
        if tokens_match:
            s['total_tokens'] = int(tokens_match.group(1))
        if 'Task:' in line:
            s['last_task'] = line.split('Task:')[-1].strip()
        if 'Command:' in line:
            s['last_command'] = line.split('Command:')[-1].strip()
        score_match = re.search(r'Score: (-?[\d\.]+)', line)
        if score_match:
            s['last_score'] = float(score_match.group(1))
        s['uptime'] = str(timedelta(seconds=int(time.time() - s['start_time'])))

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="3">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>⚡ Dual H100 Training Monitor</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Syne:wght@700;800&display=swap" rel="stylesheet">
<style>
  :root { --bg:#050508;--panel:#0d0d14;--border:#1a1a2e;--gpu0:#00ff88;--gpu1:#00b4ff;--accent:#ff4466;--text:#e0e0f0;--muted:#4a4a6a;--warn:#ffaa00; }
  *{margin:0;padding:0;box-sizing:border-box;}
  body{background:var(--bg);color:var(--text);font-family:'JetBrains Mono',monospace;font-size:13px;min-height:100vh;background-image:radial-gradient(ellipse 80% 50% at 20% 0%,rgba(0,255,136,.04) 0%,transparent 60%),radial-gradient(ellipse 80% 50% at 80% 0%,rgba(0,180,255,.04) 0%,transparent 60%);}
  header{padding:20px 30px 16px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:16px;flex-wrap:wrap;}
  header h1{font-family:'Syne',sans-serif;font-size:22px;font-weight:800;background:linear-gradient(90deg,var(--gpu0),var(--gpu1));-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
  .pulse{width:8px;height:8px;border-radius:50%;background:var(--gpu0);animation:pulse 1.5s ease-in-out infinite;flex-shrink:0;}
  @keyframes pulse{0%,100%{opacity:1;box-shadow:0 0 6px var(--gpu0);}50%{opacity:.3;box-shadow:none;}}
  .timestamp{margin-left:auto;color:var(--muted);font-size:11px;}
  .share-bar{width:100%;background:rgba(0,255,136,0.05);border:1px solid rgba(0,255,136,0.2);border-radius:4px;padding:8px 14px;display:flex;align-items:center;gap:10px;margin-top:8px;}
  .share-label{font-size:10px;color:var(--gpu0);letter-spacing:1px;text-transform:uppercase;white-space:nowrap;}
  .share-url{font-size:11px;color:var(--text);word-break:break-all;flex:1;}
  .copy-btn{background:rgba(0,255,136,0.1);border:1px solid var(--gpu0);color:var(--gpu0);padding:3px 10px;border-radius:3px;cursor:pointer;font-size:10px;font-family:inherit;white-space:nowrap;}
  .copy-btn:hover{background:rgba(0,255,136,0.2);}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border);}
  .gpu-panel{background:var(--panel);padding:24px;}
  .gpu-panel.gpu0{--ac:var(--gpu0);}
  .gpu-panel.gpu1{--ac:var(--gpu1);}
  .gpu-header{display:flex;align-items:center;gap:10px;margin-bottom:20px;padding-bottom:14px;border-bottom:1px solid var(--border);}
  .gpu-badge{font-family:'Syne',sans-serif;font-size:13px;font-weight:800;color:var(--ac);background:rgba(0,0,0,.4);border:1px solid var(--ac);padding:3px 10px;border-radius:3px;letter-spacing:1px;}
  .gpu-title{font-size:12px;color:var(--muted);}
  .gpu-status{margin-left:auto;font-size:11px;color:var(--ac);padding:2px 8px;border-radius:2px;background:rgba(0,0,0,.3);}
  .progress-section{margin-bottom:20px;}
  .progress-label{display:flex;justify-content:space-between;margin-bottom:6px;font-size:11px;color:var(--muted);}
  .progress-label .val{color:var(--ac);font-weight:600;}
  .progress-bar{height:6px;background:rgba(255,255,255,.05);border-radius:3px;overflow:hidden;margin-bottom:4px;}
  .progress-fill{height:100%;background:var(--ac);border-radius:3px;transition:width .5s ease;box-shadow:0 0 8px var(--ac);}
  .progress-sub{display:flex;justify-content:space-between;font-size:10px;color:var(--muted);}
  .metrics{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:18px;}
  .metric{background:rgba(0,0,0,.3);border:1px solid var(--border);border-radius:4px;padding:10px;}
  .metric-label{font-size:9px;color:var(--muted);letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
  .metric-val{font-size:16px;font-weight:600;color:var(--ac);}
  .metric-val.normal{color:var(--text);}
  .metric-val.warn{color:var(--warn);}
  .task-box{background:rgba(0,0,0,.25);border:1px solid var(--border);border-left:3px solid var(--ac);border-radius:4px;padding:10px 12px;margin-bottom:10px;font-size:11px;}
  .task-label{color:var(--muted);font-size:10px;letter-spacing:1px;margin-bottom:4px;}
  .score-badge{display:inline-block;padding:1px 6px;border-radius:2px;font-size:10px;font-weight:700;margin-top:4px;}
  .score-high{background:rgba(0,255,136,.15);color:var(--gpu0);}
  .score-med{background:rgba(255,170,0,.15);color:var(--warn);}
  .score-low{background:rgba(255,68,102,.15);color:var(--accent);}
  .log-title{font-size:10px;color:var(--muted);letter-spacing:1px;margin-bottom:8px;text-transform:uppercase;}
  .log-box{background:rgba(0,0,0,.4);border:1px solid var(--border);border-radius:4px;padding:10px;height:160px;overflow-y:auto;font-size:10px;line-height:1.6;color:var(--muted);}
  .log-task{color:var(--ac);}
  .log-score-hi{color:var(--gpu0);}
  .log-score-lo{color:var(--accent);}
  .log-progress{color:#555588;}
  .bottom-bar{padding:10px 30px;border-top:1px solid var(--border);display:flex;gap:30px;font-size:11px;color:var(--muted);}
  .bottom-bar span{color:var(--text);}
</style>
</head>
<body>
<header>
  <div class="pulse"></div>
  <h1>DUAL H100 TRAINING</h1>
  <div class="timestamp">{{ timestamp }} · refresh 3s</div>
  <div class="share-bar">
    <span class="share-label">🔗 Share</span>
    <span class="share-url" id="shareUrl">{{ public_url }}</span>
    <button class="copy-btn" onclick="navigator.clipboard.writeText(document.getElementById('shareUrl').innerText).then(()=>this.innerText='Copied!').catch(()=>this.innerText='Use Ctrl+C')">Copy</button>
  </div>
</header>
<div class="grid">
{% for gid in [0, 1] %}
{% set s = gpus[gid] %}
<div class="gpu-panel {{ "gpu0" if gid == 0 else "gpu1" }}">
  <div class="gpu-header">
    <div class="gpu-badge">GPU {{ gid }}</div>
    <div class="gpu-title">H100 SXM 80GB · {{ "resume_final_fix.py" if gid == 0 else "resume_gpu1.py" }}</div>
    <div class="gpu-status">{{ s.status }}</div>
  </div>
  <div class="progress-section">
    <div class="progress-label"><span>SESSION PROGRESS</span><span class="val">{{ s.current_step }} / {{ s.total_steps }} ({{ s.progress_percent }}%)</span></div>
    <div class="progress-bar"><div class="progress-fill" style="width:{{ s.progress_percent }}%"></div></div>
    <div class="progress-sub"><span>True epoch: {{ "%.1f"|format(s.true_epoch) }}</span><span>ETA: {{ s.eta }}</span></div>
  </div>
  <div class="progress-section">
    <div class="progress-label"><span>TOTAL PROGRESS (incl. checkpoint)</span><span class="val">{{ s.true_steps }} / 10000 ({{ s.true_progress }}%)</span></div>
    <div class="progress-bar"><div class="progress-fill" style="width:{{ s.true_progress }}%"></div></div>
  </div>
  <div class="metrics">
    <div class="metric"><div class="metric-label">Loss</div><div class="metric-val {{ "warn" if s.loss > 0.5 else "normal" }}">{{ "%.4f"|format(s.loss) }}</div></div>
    <div class="metric"><div class="metric-label">Reward</div><div class="metric-val">{{ "%.2f"|format(s.reward) }}</div></div>
    <div class="metric"><div class="metric-label">Best</div><div class="metric-val">{{ "%.2f"|format(s.best_reward) }}</div></div>
    <div class="metric"><div class="metric-label">Speed</div><div class="metric-val normal">{{ s.speed }}</div></div>
    <div class="metric"><div class="metric-label">Tokens</div><div class="metric-val normal">{{ "{:,}".format(s.total_tokens) }}</div></div>
    <div class="metric"><div class="metric-label">Uptime</div><div class="metric-val normal">{{ s.uptime }}</div></div>
  </div>
  <div class="task-box">
    <div class="task-label">LAST TASK</div>
    <div class="task-content">{{ s.last_task or "Waiting..." }}</div>
    {% if s.last_command %}<div style="color:#888;margin-top:4px;">$ {{ s.last_command }}</div>{% endif %}
    {% if s.last_score %}<div class="score-badge {{ "score-high" if s.last_score >= 5 else ("score-med" if s.last_score >= 0 else "score-low") }}">SCORE {{ s.last_score }}</div>{% endif %}
  </div>
  <div class="log-title">Recent Output</div>
  <div class="log-box">
    {% for line in s.log_lines[-30:] %}
      {% if "Task:" in line %}<span class="log-task">{{ line }}</span>
      {% elif "Score: 5.0" in line or "Score: 8.0" in line %}<span class="log-score-hi">{{ line }}</span>
      {% elif "Score: -" in line %}<span class="log-score-lo">{{ line }}</span>
      {% elif "%|" in line %}<span class="log-progress">{{ line }}</span>
      {% else %}{{ line }}{% endif %}<br>
    {% endfor %}
  </div>
</div>
{% endfor %}
</div>
<div class="bottom-bar">
  <div>GPU 0 Epoch: <span>{{ "%.2f"|format(gpus[0].true_epoch) }}</span></div>
  <div>GPU 1 Epoch: <span>{{ "%.2f"|format(gpus[1].true_epoch) }}</span></div>
  <div>Combined Tokens: <span>{{ "{:,}".format(gpus[0].total_tokens + gpus[1].total_tokens) }}</span></div>
</div>
</body>
</html>
'''

@app.route('/')
def index():
    with stats_lock:
        gpus_copy = {k: dict(v) for k, v in gpu_stats.items()}
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template_string(HTML_TEMPLATE, gpus=gpus_copy, timestamp=timestamp, public_url=public_url)

@app.route('/api/stats')
def api_stats():
    with stats_lock:
        return {str(k): dict(v) for k, v in gpu_stats.items()}

@app.route('/ingest/<int:gpu_id>', methods=['POST'])
def ingest(gpu_id):
    from flask import request
    if gpu_id not in gpu_stats:
        return {'error': 'invalid gpu_id'}, 400
    data = request.get_json(silent=True) or {}
    line = data.get('line', '')
    if line:
        parse_training_output(line, gpu_id)
    return {'ok': True}

def tail_log(log_path, gpu_id):
    import subprocess
    p = subprocess.Popen(['tail', '-F', '-n', '0', log_path],
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    for line in p.stdout:
        parse_training_output(line.rstrip(), gpu_id)

if __name__ == '__main__':
    import sys, os
    threading.Thread(target=get_tunnel_url, daemon=True).start()
    log_files = sys.argv[1:] if len(sys.argv) > 1 else []
    default_logs = ['gpu0_training.log', 'gpu1_training.log']
    for i, log_path in enumerate(log_files or default_logs):
        if os.path.exists(log_path):
            t = threading.Thread(target=tail_log, args=(log_path, i), daemon=True)
            t.start()
            print(f"📡 Tailing {log_path} → GPU {i}")
        else:
            print(f"⚠️  Log not found: {log_path} (POST to /ingest/{i} instead)")
    print("=" * 60)
    print("⚡ DUAL H100 MONITOR → http://0.0.0.0:6006")
    print("=" * 60)
    app.run(host='0.0.0.0', port=6006, debug=False)
