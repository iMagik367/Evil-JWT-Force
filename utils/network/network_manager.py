import os
import subprocess

class NetworkManager:
    def __init__(self):
        self.vpn_proc = None
        self.tor_proc = None

    def start_vpn(self, config_path):
        """Start OpenVPN with the given .ovpn config file."""
        if self.vpn_proc and self.vpn_proc.poll() is None:
            return self.vpn_proc
        self.vpn_proc = subprocess.Popen(
            ['openvpn', '--config', config_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return self.vpn_proc

    def stop_vpn(self):
        """Stop the running OpenVPN process."""
        if self.vpn_proc:
            self.vpn_proc.terminate()
            self.vpn_proc.wait()
            self.vpn_proc = None

    def start_tor(self, tor_path='tor', torrc_path=None):
        """Start Tor process using the given executable and optional torrc file."""
        if self.tor_proc and self.tor_proc.poll() is None:
            return self.tor_proc
        cmd = [tor_path]
        if torrc_path:
            cmd.extend(['-f', torrc_path])
        self.tor_proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return self.tor_proc

    def stop_tor(self):
        """Stop the running Tor process."""
        if self.tor_proc:
            self.tor_proc.terminate()
            self.tor_proc.wait()
            self.tor_proc = None

    def set_tor_proxy_env(self, enable=True):
        """Enable or disable HTTP/S proxy environment variables for Tor."""
        if enable:
            os.environ['HTTP_PROXY'] = 'socks5h://127.0.0.1:9050'
            os.environ['HTTPS_PROXY'] = 'socks5h://127.0.0.1:9050'
        else:
            os.environ.pop('HTTP_PROXY', None)
            os.environ.pop('HTTPS_PROXY', None)

# Singleton instance for application-wide use
network_manager = NetworkManager() 