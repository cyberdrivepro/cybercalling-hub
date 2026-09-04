import os, sys, time, shutil, socket, subprocess, threading, requests

TOR_DATA_DIR = os.getenv('TOR_DATA_DIR', '/tmp/tor_data' if os.name != 'nt' else os.path.join(os.getenv('TEMP', '.'), 'tor_data'))
TOR_RC_PATH = os.path.join(TOR_DATA_DIR, 'torrc')
TOR_SOCKS_PORT = 9050

class TorDaemonManager:
    _instance = None
    _lock = threading.Lock()
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TorDaemonManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized: return
        self._initialized = True
        self.is_running = False
        self.process = None
        self.exit_ip = None
        self.bootstrap_percent = 0

    def find_tor_binary(self):
        for c in [shutil.which('tor'), '/usr/bin/tor', '/usr/local/bin/tor']:
            if c and os.path.exists(c): return c
        return None

    def is_tor_installed(self):
        return self.find_tor_binary() is not None

    def is_port_open(self, host='127.0.0.1', port=TOR_SOCKS_PORT):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        try:
            s.connect((host, port))
            s.close()
            return True
        except Exception:
            return False

    def start(self):
        threading.Thread(target=self._run_worker, daemon=True).start()

    def _run_worker(self):
        if self.is_port_open():
            self.is_running = True
            self.bootstrap_percent = 100
            print(f'Tor detected on 127.0.0.1:{TOR_SOCKS_PORT}')
            return

        tor_bin = self.find_tor_binary()
        if not tor_bin:
            print('Tor binary not found on local path.')
            return

        os.makedirs(TOR_DATA_DIR, exist_ok=True)
        torrc = (
            f"SocksPort 127.0.0.1:{TOR_SOCKS_PORT}\n"
            f"DataDirectory {TOR_DATA_DIR}\n"
            "ClientOnly 1\n"
            "ExitRelay 0\n"
            "Log notice stdout\n"
        )
        with open(TOR_RC_PATH, 'w', encoding='utf-8') as f:
            f.write(torrc)

        cmd = [tor_bin, '-f', TOR_RC_PATH]
        print(f'Starting Tor daemon: {cmd}')
        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in self.process.stdout:
                l = line.strip()
                if 'Bootstrapped' in l:
                    print(f'[Tor] {l}')
                    if '100%' in l:
                        self.is_running = True
                        self.bootstrap_percent = 100
                elif 'Opening Socks listener' in l:
                    self.is_running = True
        except Exception as e:
            print(f'Tor start error: {e}')

    def get_status(self):
        return {
            'installed': self.is_tor_installed(),
            'active': self.is_running or self.is_port_open(),
            'socks_port': TOR_SOCKS_PORT,
            'socks_proxy_url': f'socks5h://127.0.0.1:{TOR_SOCKS_PORT}'
        }

tor_service = TorDaemonManager()