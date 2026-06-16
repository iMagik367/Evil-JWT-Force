import subprocess
import threading
import logging
import time
import sys
import os
from typing import Optional

try:
    import requests
except ImportError:
    requests = None

class VPNError(Exception):
    pass

class VPNIPMasker:
    _instance = None
    _lock = threading.Lock()
    _vpn_process: Optional[subprocess.Popen] = None
    _vpn_active: bool = False
    _vpn_path: Optional[str] = None
    _last_ip: Optional[str] = None

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(VPNIPMasker, cls).__new__(cls)
        return cls._instance

    def __init__(self, vpn_path: Optional[str] = None, wait_time: int = 12):
        self._vpn_path = vpn_path or self._find_riseup_vpn()
        self._wait_time = wait_time
        self.logger = logging.getLogger("VPNIPMasker")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def _find_riseup_vpn(self) -> str:
        # Busca caminhos comuns do RiseupVPN no Linux/Windows
        if sys.platform.startswith("win"):
            possible = [
                os.path.expandvars(r"%ProgramFiles%\RiseupVPN\riseup-vpn.exe"),
                os.path.expandvars(r"%ProgramFiles(x86)%\RiseupVPN\riseup-vpn.exe")
            ]
        else:
            possible = [
                "/usr/bin/riseup-vpn",
                "/snap/bin/riseup-vpn.launcher",
                "/usr/local/bin/riseup-vpn"
            ]
        for path in possible:
            if os.path.exists(path):
                return path
        raise VPNError("RiseupVPN não encontrado no sistema. Instale conforme https://riseup.net/pt/linux")

    def _get_external_ip(self) -> Optional[str]:
        if not requests:
            self.logger.warning("requests não instalado, não é possível obter IP externo.")
            return None
        try:
            return requests.get("https://api.ipify.org", timeout=8).text
        except Exception as e:
            self.logger.warning(f"Falha ao obter IP externo: {e}")
            return None

    def activate_vpn(self):
        with self._lock:
            if self._vpn_active:
                self.logger.info("VPN já está ativa.")
                return
            self.logger.info("Ativando VPN Riseup...")
            try:
                if sys.platform.startswith("win"):
                    self._vpn_process = subprocess.Popen([self._vpn_path], shell=True)
                else:
                    self._vpn_process = subprocess.Popen([self._vpn_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                time.sleep(self._wait_time)
                self._vpn_active = True
                self._last_ip = self._get_external_ip()
                self.logger.info(f"VPN ativada. IP atual: {self._last_ip}")
            except Exception as e:
                self.logger.error(f"Erro ao ativar VPN: {e}")
                raise VPNError(f"Erro ao ativar VPN: {e}")

    def deactivate_vpn(self):
        with self._lock:
            if not self._vpn_active or not self._vpn_process:
                self.logger.info("VPN já está desativada.")
                return
            self.logger.info("Desativando VPN Riseup...")
            try:
                if sys.platform.startswith("win"):
                    self._vpn_process.terminate()
                else:
                    self._vpn_process.terminate()
                self._vpn_process.wait(timeout=10)
                self._vpn_active = False
                time.sleep(5)
                ip = self._get_external_ip()
                self.logger.info(f"VPN desativada. IP atual: {ip}")
            except Exception as e:
                self.logger.error(f"Erro ao desativar VPN: {e}")

    def is_vpn_active(self) -> bool:
        return self._vpn_active

    def get_current_ip(self) -> Optional[str]:
        return self._get_external_ip()

    def run_with_vpn(self, func, *args, **kwargs):
        self.activate_vpn()
        try:
            result = func(*args, **kwargs)
        finally:
            self.deactivate_vpn()
        return result

    def __enter__(self):
        self.activate_vpn()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deactivate_vpn()

# Uso programático:
# with VPNIPMasker() as vpn:
#     ... código sensível ...

# CLI para integração direta
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Automação avançada de VPN Riseup e mascaramento de IP")
    parser.add_argument("--on", action="store_true", help="Ativar VPN")
    parser.add_argument("--off", action="store_true", help="Desativar VPN")
    parser.add_argument("--ip", action="store_true", help="Mostrar IP atual")
    parser.add_argument("--run", metavar="SCRIPT", help="Executar script Python com VPN ativa")
    args = parser.parse_args()

    vpn = VPNIPMasker()
    if args.on:
        vpn.activate_vpn()
    if args.off:
        vpn.deactivate_vpn()
    if args.ip:
        print("IP atual:", vpn.get_current_ip())
    if args.run:
        vpn.activate_vpn()
        try:
            subprocess.run([sys.executable, args.run])
        finally:
            vpn.deactivate_vpn()