import pyshark
import time
import psutil
import logging
import socket
from colorama import init, Fore, Style

# ================= KONFIGURATION =================
INTERFACE = r"\Device\NPF_{23E1B6B0-BE56-4678-BF97-115747AA06BA}"
PROCESS_NAME = "PioneerGame.exe"

# Lag-Erkennung (0.8s ist stabil für Ingame-Tests)
LAG_THRESHOLD_SEC = 0.8 

# Heartbeat-Filter für die Konsole (Größen aus deinem Log)
# Wir loggen sie in die Datei, aber blenden sie in der Konsole aus.
IGNORE_SIZES = [54, 59, 63, 66, 75, 80] 
# =================================================

init(autoreset=True)
LOG_FILE = "arc_complete_analysis.log"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s | %(message)s', datefmt='%H:%M:%S')

class MasterAnalyzer:
    def __init__(self):
        self.last_packet_time = time.time()
        self.local_ip_v4 = self._get_local_ip()

    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 1))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except: return "127.0.0.1"

    def get_game_ips(self):
        print(f"{Fore.CYAN}[SCAN] Suche PioneerGame.exe (TCP + UDP)...")
        target_pid = None
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == PROCESS_NAME:
                target_pid = proc.info['pid']
                break
        
        if not target_pid:
            print(f"{Fore.RED}[FEHLER] Spiel läuft nicht!")
            return None

        server_ips = set()
        try:
            p = psutil.Process(target_pid)
            # Scanne alle aktiven Verbindungen
            for conn in p.net_connections():
                if conn.raddr:
                    ip = conn.raddr.ip
                    if not ip.startswith("127."):
                        server_ips.add(ip)
        except Exception as e:
            print(f"{Fore.RED}Zugriffsfehler: {e} - Bitte als ADMIN starten!")
            return None

        return list(server_ips)

    def process_packet(self, packet):
        try:
            current_time = time.time()
            time_delta = current_time - self.last_packet_time
            # Update Zeit bei JEDEM Paket (verhindert Fehlalarme bei Protokollwechsel)
            self.last_packet_time = current_time

            # 1. LAG ERKENNUNG
            if time_delta > LAG_THRESHOLD_SEC:
                ms = time_delta * 1000
                msg = f"\n>>> ⚠️  STILLE ERKANNT: {ms:.0f}ms (LAG/BLOCK) ⚠️ <<<\n"
                print(f"{Fore.RED}{Style.BRIGHT}{msg}{Style.RESET_ALL}")
                logging.warning(f"LAG | {ms:.0f}ms")

            # 2. PROTOKOLL & IP VERSION
            proto = packet.transport_layer
            length = int(packet.length)
            ip_ver = "IPv6" if hasattr(packet, 'ipv6') else "IPv4"
            src_ip = packet.ipv6.src if ip_ver == "IPv6" else packet.ip.src

            # Richtung bestimmen
            direction = ">> OUT" if src_ip.startswith("2") or src_ip == self.local_ip_v4 else "<< IN "
            
            # 3. FILTER FÜR KONSOLE
            if length in IGNORE_SIZES:
                logging.info(f"HEARTBEAT | {ip_ver} | {proto} | {length} | {src_ip}")
                return

            # Payload (Hex)
            hex_data = ""
            if hasattr(packet[proto], 'payload'):
                hex_data = packet[proto].payload.replace(":", "")[:32]

            # 4. AUSGABE NACH KATEGORIEN
            color = Fore.GREEN if "OUT" in direction else Fore.BLUE
            proto_color = Fore.YELLOW if proto == "TCP" else Fore.MAGENTA
            
            output = f"{color}{direction} {Fore.WHITE}| {ip_ver} | {proto_color}{proto:<3} {Fore.WHITE}| Size: {length:<4} | DATA: {hex_data}"
            
            print(output)
            logging.info(f"{direction} | {ip_ver} | {proto} | {length} | {hex_data} | {src_ip}")

        except Exception: pass

def main():
    print(f"{Fore.YELLOW}{'='*70}")
    print(f"{Fore.YELLOW} ARC RAIDERS MASTER WATCHDOG V3 (TCP + UDP + IPv6)")
    print(f"{Fore.YELLOW}{'='*70}")

    sniffer = MasterAnalyzer()
    ips = sniffer.get_game_ips()
    if not ips: return

    # Filter bauen für alle IPs (TCP und UDP)
    ip_filter = " || ".join([f"{'ipv6' if ':' in ip else 'ip'}.addr == {ip}" for ip in ips])
    final_filter = f"({ip_filter}) && (tcp || udp)"
    
    print(f"{Fore.GREEN}[OK] Überwache {len(ips)} Server-Endpunkte.")
    print(f"{Fore.CYAN}[LOG] Ergebnisse in: {LOG_FILE}")
    print("-" * 70)

    try:
        capture = pyshark.LiveCapture(interface=INTERFACE, display_filter=final_filter)
        for packet in capture.sniff_continuously():
            sniffer.process_packet(packet)
    except KeyboardInterrupt: print(f"\n{Fore.YELLOW}Beendet.")
    except Exception as e: print(f"\n{Fore.RED}Fehler: {e}")

if __name__ == "__main__":
    main()