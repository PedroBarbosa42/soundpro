import sys
import os
import time
import threading
import queue
import json
import uuid
import webbrowser
import socket
import subprocess
import urllib.request
import urllib.parse
import logging
from flask import Flask, request, jsonify, render_template, Response, send_file
import flask.cli
from flask_cors import CORS

# --- REDIRECIONAMENTO SEGURO DE FLUXOS ---
# Apenas redireciona se os descritores não existirem (ex: compilado no PyInstaller com console=False)
if getattr(sys, 'frozen', False) and getattr(sys, 'stdout', None) is None:
    try:
        devnull_w = open(os.devnull, 'w', encoding='utf-8')
        devnull_r = open(os.devnull, 'r', encoding='utf-8')
        sys.stdout = devnull_w
        sys.stderr = devnull_w
        sys.stdin = devnull_r
    except Exception:
        pass

# Desativa logs verbosos do Werkzeug
flask.cli.show_server_banner = lambda *args: None
logging.getLogger('werkzeug').setLevel(logging.ERROR)

from logic import listar_musicas, baixar_midia_pro, FFMPEG_DIR

if getattr(sys, 'frozen', False):
    template_folder = os.path.join(getattr(sys, '_MEIPASS', ''), 'templates')
    app = Flask(__name__, template_folder=template_folder)
else:
    app = Flask(__name__, template_folder='templates')

CORS(app)

DEFAULT_DIR = os.path.join(os.path.expanduser('~'), 'Music')
if os.path.exists(DEFAULT_DIR):
    current_download_dir = DEFAULT_DIR
else:
    current_download_dir = os.path.join(os.getcwd(), 'downloads')
    os.makedirs(current_download_dir, exist_ok=True)

sessions = {}
cancel_events = {}
active_downloads_count = 0
active_downloads_lock = threading.Lock()

# Controle do Ciclo de Vida do Aplicativo
first_client_connected = False
last_heartbeat = time.time()
shutdown_timer = None

@app.route('/favicon.ico')
@app.route('/templates/icone.ico')
def favicon():
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    ico_path = os.path.join(base_dir, 'templates', 'icone.ico')
    if os.path.exists(ico_path):
        return send_file(ico_path, mimetype='image/x-icon')
    return ('', 204)

@app.route('/api/heartbeat', methods=['GET'])
def heartbeat():
    global last_heartbeat, first_client_connected
    first_client_connected = True
    last_heartbeat = time.time()
    return '', 200

@app.route('/')
def index():
    global first_client_connected, last_heartbeat
    first_client_connected = True
    last_heartbeat = time.time()
    return render_template('index.html')

USER_HOME = os.path.expanduser('~')
PRESET_DIRS = {
    'music': os.path.join(USER_HOME, 'Music'),
    'downloads': os.path.join(USER_HOME, 'Downloads'),
    'desktop': os.path.join(USER_HOME, 'Desktop'),
}

porta_ativa_global = 5000

def obter_ip_local():
    """Descobre o IP local da máquina na rede Wi-Fi/Ethernet."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(0.5)
            s.connect(('8.8.8.8', 80))
            return s.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return '127.0.0.1'

@app.route('/api/network-info', methods=['GET'])
def network_info():
    ip = obter_ip_local()
    return jsonify({
        'local_ip': ip,
        'port': porta_ativa_global,
        'url': f"http://{ip}:{porta_ativa_global}"
    }), 200

@app.route('/api/download-file', methods=['GET'])
def download_file():
    filename = request.args.get('filename')
    if not filename:
        return jsonify({'error': 'Arquivo não informado.'}), 400
    safe_name = os.path.basename(filename)
    pastas_busca = [
        current_download_dir,
        os.path.join(USER_HOME, 'Music'),
        os.path.join(USER_HOME, 'Downloads'),
        os.path.join(USER_HOME, 'Desktop'),
        os.getcwd()
    ]
    for pasta in pastas_busca:
        if not os.path.exists(pasta):
            continue
        candidato = os.path.join(pasta, safe_name)
        if os.path.exists(candidato):
            return send_file(candidato, as_attachment=True, download_name=safe_name)
    return jsonify({'error': f'Arquivo {safe_name} não encontrado.'}), 404

@app.route('/api/get-directory', methods=['GET'])
def get_directory():
    return jsonify({
        'directory': current_download_dir,
        'presets': {k: v for k, v in PRESET_DIRS.items() if os.path.exists(v)}
    }), 200

@app.route('/api/set-directory', methods=['POST'])
def set_directory():
    global current_download_dir
    data = request.get_json(silent=True) or {}
    preset = data.get('preset')
    custom = data.get('directory')

    if preset and preset in PRESET_DIRS:
        target = PRESET_DIRS[preset]
        if os.path.exists(target):
            current_download_dir = os.path.normpath(target)
            return jsonify({'directory': current_download_dir}), 200

    if custom and os.path.exists(custom):
        current_download_dir = os.path.normpath(custom)
        return jsonify({'directory': current_download_dir}), 200

    return jsonify({'directory': current_download_dir}), 200

def abrir_seletor_pastas_nativo(diretorio_inicial):
    """
    Abre o diálogo nativo do Windows instantaneamente (~0.1s)
    e força a janela a ficar visível em primeiro plano (TopMost).
    """
    # 1. Tkinter com TopMost forçado (ultra rápido: ~100ms)
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes('-topmost', 1)
        root.focus_force()
        escolha = filedialog.askdirectory(
            initialdir=diretorio_inicial,
            title="SoundPro - Selecione a pasta de destino",
            parent=root
        )
        root.destroy()
        if escolha and os.path.exists(escolha):
            return os.path.normpath(escolha)
        if escolha == '':  # Usuário clicou em cancelar
            return diretorio_inicial
    except Exception:
        pass

    # 2. Fallback PowerShell com janela TopMost garantida em primeiro plano
    try:
        ps_code = f"""
        [void][System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms')
        $form = New-Object System.Windows.Forms.Form
        $form.TopMost = $true
        $form.StartPosition = 'CenterScreen'
        $f = New-Object System.Windows.Forms.FolderBrowserDialog
        $f.Description = 'SoundPro - Selecione a pasta de destino'
        $f.SelectedPath = '{diretorio_inicial}'
        $f.ShowNewFolderButton = $true
        if ($f.ShowDialog($form) -eq [System.Windows.Forms.DialogResult]::OK) {{
            Write-Output $f.SelectedPath
        }}
        $form.Dispose()
        """
        res = subprocess.run(
            ['powershell', '-NoProfile', '-Command', ps_code],
            capture_output=True,
            text=True,
            timeout=40
        )
        escolha = res.stdout.strip()
        if escolha and os.path.exists(escolha):
            return os.path.normpath(escolha)
    except Exception:
        pass

    return diretorio_inicial

@app.route('/api/select-directory', methods=['POST'])
def select_directory():
    global current_download_dir
    caminho = abrir_seletor_pastas_nativo(current_download_dir)
    if caminho:
        current_download_dir = os.path.normpath(caminho)
    return jsonify({'directory': current_download_dir}), 200

@app.route('/api/playlist-info', methods=['GET'])
def get_playlist_info():
    pid = request.args.get('id')
    if not pid:
        return jsonify({'error': 'Insira uma URL ou ID válido.'}), 400

    try:
        dados = listar_musicas(pid)
        return jsonify(dados), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-single', methods=['POST'])
def download_single():
    global active_downloads_count
    data = request.get_json(silent=True) or {}
    track = data.get('track')
    custom_dir = data.get('directory') or current_download_dir
    formato = data.get('format', 'mp3')

    if not track:
        return jsonify({'error': 'Dados da faixa não informados.'}), 400

    with active_downloads_lock:
        active_downloads_count += 1

    try:
        caminho_final = baixar_midia_pro(track, custom_dir, formato=formato)
        nome_arquivo = os.path.basename(caminho_final)
        return jsonify({
            'status': 'sucesso',
            'filename': nome_arquivo,
            'download_url': f"/api/download-file?filename={urllib.parse.quote(nome_arquivo)}"
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        with active_downloads_lock:
            active_downloads_count = max(0, active_downloads_count - 1)

@app.route('/api/start-batch', methods=['POST'])
def start_batch():
    global active_downloads_count
    data = request.get_json(silent=True) or {}
    tracks = data.get('tracks', [])
    destino = data.get('directory') or current_download_dir
    formato = data.get('format', 'mp3')

    if not tracks:
        return jsonify({'error': 'Lista de faixas vazia.'}), 400

    task_id = str(uuid.uuid4())
    q = queue.Queue()
    cancel_event = threading.Event()

    sessions[task_id] = q
    cancel_events[task_id] = cancel_event

    def worker():
        global active_downloads_count
        with active_downloads_lock:
            active_downloads_count += 1

        try:
            total = len(tracks)
            for i, track in enumerate(tracks):
                if cancel_event.is_set():
                    q.put({'status': 'cancelled', 'message': 'Download cancelado.'})
                    break
                try:
                    q.put({
                        'status': 'downloading',
                        'current': i + 1,
                        'total': total,
                        'track_title': track.get('title'),
                        'format': formato.upper(),
                        'percent': int(((i) / total) * 100)
                    })
                    caminho_gerado = baixar_midia_pro(track, destino, formato=formato)
                    nome_arquivo = os.path.basename(caminho_gerado)
                    q.put({
                        'status': 'track_finished',
                        'current': i + 1,
                        'total': total,
                        'track_title': track.get('title'),
                        'filename': nome_arquivo,
                        'download_url': f"/api/download-file?filename={urllib.parse.quote(nome_arquivo)}"
                    })
                except Exception:
                    pass

            if not cancel_event.is_set():
                q.put({
                    'status': 'finished',
                    'current': total,
                    'total': total,
                    'percent': 100
                })
        finally:
            with active_downloads_lock:
                active_downloads_count = max(0, active_downloads_count - 1)

    threading.Thread(target=worker, daemon=True).start()
    return jsonify({'task_id': task_id}), 200

@app.route('/api/cancel-batch', methods=['POST'])
def cancel_batch():
    data = request.get_json(silent=True) or {}
    task_id = data.get('task_id')
    if task_id and task_id in cancel_events:
        cancel_events[task_id].set()
        return jsonify({'status': 'cancel_requested'}), 200
    return jsonify({'error': 'Tarefa não encontrada'}), 404

@app.route('/api/stream-progress/<task_id>')
def stream_progress(task_id):
    def event_stream():
        q = sessions.get(task_id)
        if not q:
            yield f"data: {json.dumps({'status': 'error', 'message': 'Sessão não encontrada'})}\n\n"
            return
        while True:
            msg = q.get()
            yield f"data: {json.dumps(msg)}\n\n"
            if msg.get('status') in ['finished', 'cancelled', 'error']:
                sessions.pop(task_id, None)
                cancel_events.pop(task_id, None)
                break
    return Response(event_stream(), mimetype='text/event-stream')

def encontrar_porta_livre(porta_padrao=5000, max_tentativas=100):
    """Encontra uma porta TCP local disponível automaticamente."""
    for porta in range(porta_padrao, porta_padrao + max_tentativas):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', porta))
                return porta
        except OSError:
            continue
    return porta_padrao

def abrir_navegador_quando_pronto(port):
    """
    Sonda ativamente a inicialização do Flask e só abre o navegador
    quando o servidor estiver de fato respondendo com sucesso.
    Evita telas de 'Conexão Recusada' ou travamentos.
    """
    url = f"http://127.0.0.1:{port}"
    for _ in range(60):  # até 30 segundos de sondagem
        time.sleep(0.5)
        try:
            req = urllib.request.Request(f"{url}/api/heartbeat")
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    webbrowser.open_new(url)
                    return
        except Exception:
            pass
    # Caso atinja o limite, tenta abrir de qualquer forma
    webbrowser.open_new(url)

def monitorar_encerramento():
    """
    Monitor de inatividade resiliente:
    - Dá tolerância de inicialização de até 180s antes de qualquer cliente conectar.
    - Após conexão, tolera até 90s sem pulso (resistente a abas em segundo plano).
    - NUNCA encerra o processo se houver downloads em andamento.
    """
    global last_heartbeat, first_client_connected
    while True:
        time.sleep(5)
        with active_downloads_lock:
            em_download = active_downloads_count > 0

        if em_download:
            # Nunca encerra durante um download
            last_heartbeat = time.time()
            continue

        tempo_sem_pulso = time.time() - last_heartbeat
        if not first_client_connected:
            # Espera até 180 segundos antes da primeira conexão
            if tempo_sem_pulso > 180:
                os._exit(0)
        else:
            # Tolerância de 90 segundos após o usuário ter aberto
            if tempo_sem_pulso > 90:
                os._exit(0)

if __name__ == '__main__':
    try:
        porta_ativa_global = encontrar_porta_livre(5000)
        threading.Thread(target=monitorar_encerramento, daemon=True).start()
        threading.Thread(target=abrir_navegador_quando_pronto, args=(porta_ativa_global,), daemon=True).start()
        app.run(host='0.0.0.0', port=porta_ativa_global, debug=False)
    except Exception as e:
        try:
            with open(os.path.join(os.path.expanduser('~'), 'soundpro_crash.log'), 'w', encoding='utf-8') as f:
                import traceback
                f.write(traceback.format_exc())
        except Exception:
            pass