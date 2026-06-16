import subprocess
import threading
import time
import os
import sys
import signal
import logging

MITMPROXY_PORT = 8080
MITMPROXY_PATH = "mitmproxy"  # Certifique-se que está no PATH ou forneça o caminho absoluto
FIREFOX_PATH = "firefox-esr"  # Certifique-se que está no PATH ou forneça o caminho absoluto
CAPTURE_FILE = "captured_traffic.mitm"
FIREFOX_PROFILE = os.path.abspath("firefox_capture_profile")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def start_mitmproxy():
    logging.info("Iniciando mitmproxy para captura de tráfego...")
    cmd = [
        MITMPROXY_PATH,
        "-p", str(MITMPROXY_PORT),
        "-w", CAPTURE_FILE
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(5)
    return proc

def create_firefox_profile():
    if not os.path.exists(FIREFOX_PROFILE):
        logging.info("Criando perfil dedicado do Firefox para captura...")
        subprocess.run([FIREFOX_PATH, "-CreateProfile", f"capture_profile {FIREFOX_PROFILE}"])
    # Configurações de proxy no user.js
    user_js = os.path.join(FIREFOX_PROFILE, "user.js")
    with open(user_js, "w") as f:
        f.write(f'''
user_pref("network.proxy.type", 1);
user_pref("network.proxy.http", "127.0.0.1");
user_pref("network.proxy.http_port", {MITMPROXY_PORT});
user_pref("network.proxy.ssl", "127.0.0.1");
user_pref("network.proxy.ssl_port", {MITMPROXY_PORT});
user_pref("network.proxy.no_proxies_on", "");
user_pref("security.enterprise_roots.enabled", true);
user_pref("app.update.enabled", false);
user_pref("browser.shell.checkDefaultBrowser", false);
''')

def start_firefox():
    logging.info("Iniciando Firefox-ESR com proxy configurado...")
    cmd = [
        FIREFOX_PATH,
        "-profile", FIREFOX_PROFILE,
        "-no-remote"
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def run_attack(attack_func, *args, **kwargs):
    logging.info("Iniciando ataque enquanto captura o tráfego...")
    attack_thread = threading.Thread(target=attack_func, args=args, kwargs=kwargs)
    attack_thread.start()
    return attack_thread

def main(attack_func, *args, **kwargs):
    mitm_proc = None
    firefox_proc = None
    try:
        mitm_proc = start_mitmproxy()
        create_firefox_profile()
        firefox_proc = start_firefox()
        attack_thread = run_attack(attack_func, *args, **kwargs)
        attack_thread.join()
        logging.info("Ataque finalizado. Captura de tráfego encerrada.")
    finally:
        if firefox_proc:
            firefox_proc.terminate()
        if mitm_proc:
            mitm_proc.send_signal(signal.SIGINT)
            mitm_proc.wait()
        logging.info(f"Arquivo de captura salvo em: {CAPTURE_FILE}")

# Exemplo de integração: substitua attack_func pelo seu ataque real
def dummy_attack():
    import requests
    for i in range(5):
        try:
            requests.get("http://example.com")
        except Exception:
            pass
        time.sleep(2)

if __name__ == "__main__":
    main(dummy_attack)