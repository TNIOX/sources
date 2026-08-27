#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilisation:
sudo python3 mac_changer.py
"""
"""
MAC Address Changer - Mode interactif
Change l'adresse MAC d'une interface réseau
"""

import subprocess
import re
import os
import sys
import random
import json
import time
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
# Couleurs ANSI
# ═══════════════════════════════════════════════════════════════
class C:
    H = '\033[95m'   # Header
    B = '\033[94m'   # Blue
    CY = '\033[96m'  # Cyan
    G = '\033[92m'   # Green
    Y = '\033[93m'   # Yellow
    R = '\033[91m'   # Red
    BD = '\033[1m'   # Bold
    U = '\033[4m'    # Underline
    E = '\033[0m'    # End
    P = '\033[35m'   # Purple
    D = '\033[90m'   # Dark

# ═══════════════════════════════════════════════════════════════
# Fonctions d'affichage
# ═══════════════════════════════════════════════════════════════
def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def print_banner():
    banner = f"""
{C.CY}{C.BD}
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║   ███╗   ███╗ █████╗ ███████╗ ██████╗                 ║
    ║   ████╗ ████║██╔══██╗╚══███╔╝██╔════╝                 ║
    ║   ██╔████╔██║███████║  ███╔╝ ██║                      ║
    ║   ██║╚██╔╝██║██╔══██║ ███╔╝  ██║                      ║
    ║   ██║ ╚═╝ ██║██║  ██║███████╗╚██████╗                 ║
    ║   ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝   by TNiox      ║
    ║                                                       ║
    ║          {C.Y}⚡ MAC Address Changer v2.0 ⚡{C.CY}               ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
{C.E}"""
    print(banner)

def print_ok(msg):
    print(f"{C.G}[✓]{C.E} {msg}")

def print_err(msg):
    print(f"{C.R}[✗]{C.E} {msg}")

def print_info(msg):
    print(f"{C.CY}[i]{C.E} {msg}")

def print_warn(msg):
    print(f"{C.Y}[!]{C.E} {msg}")

def loading(msg, sec=0.8):
    symbols = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    for i in range(int(sec * 10)):
        sys.stdout.write(f"\r{C.CY}{symbols[i % len(symbols)]}{C.E} {msg}")
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write(f"\r{C.G}[✓]{C.E} {msg}\n")
    sys.stdout.flush()

def wait_key():
    input(f"\n{C.D}Appuyez sur Entrée pour continuer...{C.E}")

def separator():
    print(f"{C.D}{'─' * 55}{C.E}")

# ═══════════════════════════════════════════════════════════════
# Historique
# ═══════════════════════════════════════════════════════════════
HISTORY_FILE = Path.home() / ".mac_changer_history.json"

def load_history():
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {"changes": []}

def save_history(interface, old_mac, new_mac):
    history = load_history()
    history["changes"].append({
        "timestamp": datetime.now().isoformat(),
        "interface": interface,
        "old_mac": old_mac,
        "new_mac": new_mac
    })
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

# ═══════════════════════════════════════════════════════════════
# Fonctions techniques
# ═══════════════════════════════════════════════════════════════
def is_root():
    return os.geteuid() == 0

def validate_mac(mac):
    return bool(re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', mac))

def random_mac():
    mac = [0x00, 0x16, 0x3e,
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff)]
    return ':'.join(f'{x:02x}' for x in mac)

def get_interfaces():
    try:
        result = subprocess.run(['ls', '/sys/class/net/'], 
                              capture_output=True, text=True)
        return [i for i in result.stdout.strip().split('\n') if i and i != 'lo']
    except:
        return []

def get_mac(interface):
    try:
        result = subprocess.check_output(
            ['ip', 'link', 'show', interface], 
            stderr=subprocess.DEVNULL
        ).decode()
        match = re.search(r'link/ether\s+([0-9a-fA-F:]{17})', result)
        if match:
            return match.group(1).lower()
    except:
        pass
    return None

def get_vendor(mac):
    vendors = {
        "00:16:3e": "Xen", "08:00:27": "VirtualBox",
        "00:0c:29": "VMware", "00:50:56": "VMware",
        "00:15:5d": "Hyper-V", "52:54:00": "QEMU/KVM",
        "02:42:ac": "Docker",
    }
    return vendors.get(mac[:8], "Inconnu")

def change_mac(interface, new_mac):
    old_mac = get_mac(interface)
    
    loading(f"Désactivation de {interface}...")
    subprocess.run(['ip', 'link', 'set', interface, 'down'], 
                  capture_output=True)
    
    loading("Configuration de la nouvelle MAC...")
    subprocess.run(['ip', 'link', 'set', interface, 'address', new_mac], 
                  capture_output=True)
    
    loading(f"Activation de {interface}...")
    subprocess.run(['ip', 'link', 'set', interface, 'up'], 
                  capture_output=True)
    
    current = get_mac(interface)
    if current and current.lower() == new_mac.lower():
        save_history(interface, old_mac or "N/A", new_mac)
        return True
    return False

# ═══════════════════════════════════════════════════════════════
# Menus interactifs
# ═══════════════════════════════════════════════════════════════
def menu_interfaces():
    """Affiche la liste des interfaces et retourne le choix"""
    interfaces = get_interfaces()
    if not interfaces:
        print_err("Aucune interface réseau trouvée")
        return None
    
    print(f"\n{C.CY}{C.BD}═══ Interfaces disponibles ═══{C.E}\n")
    print(f"{C.D}{'#':<5} {'Interface':<15} {'Adresse MAC':<20} {'Fabricant'}{C.E}")
    separator()
    
    for i, iface in enumerate(interfaces, 1):
        mac = get_mac(iface)
        if mac:
            vendor = get_vendor(mac)
            print(f"{C.CY}{i:<5} {iface:<15}{C.E} {C.G}{mac:<20}{C.E} {C.Y}{vendor}{C.E}")
        else:
            print(f"{C.CY}{i:<5} {iface:<15}{C.E} {C.R}Non disponible{C.E}")
    
    while True:
        try:
            choice = input(f"\n{C.CY}Choix (1-{len(interfaces)}): {C.E}")
            idx = int(choice) - 1
            if 0 <= idx < len(interfaces):
                return interfaces[idx]
        except (ValueError, EOFError):
            pass
        print_err("Choix invalide")

def menu_mac():
    """Propose le choix de la MAC"""
    print(f"\n{C.CY}{C.BD}═══ Mode de configuration ═══{C.E}\n")
    print(f"  {C.CY}1{C.E} - Générer une MAC aléatoire")
    print(f"  {C.CY}2{C.E} - Saisir une MAC personnalisée")
    print(f"  {C.CY}3{C.E} - Choisir dans l'historique")
    
    while True:
        try:
            choice = input(f"\n{C.CY}Choix (1-3): {C.E}")
            if choice == '1':
                mac = random_mac()
                print_info(f"MAC générée: {C.G}{mac}{C.E}")
                return mac
            elif choice == '2':
                return menu_custom_mac()
            elif choice == '3':
                return menu_history_mac()
        except EOFError:
            pass
        print_err("Choix invalide")

def menu_custom_mac():
    """Saisie manuelle d'une MAC"""
    while True:
        mac = input(f"\n{C.CY}Adresse MAC (XX:XX:XX:XX:XX:XX): {C.E}").strip()
        if validate_mac(mac):
            return mac.lower()
        print_err("Format invalide! Utilisez XX:XX:XX:XX:XX:XX")

def menu_history_mac():
    """Choisir une MAC depuis l'historique"""
    history = load_history()
    if not history["changes"]:
        print_warn("Aucun historique disponible")
        return menu_custom_mac()
    
    print(f"\n{C.CY}{C.BD}═══ Derniers changements ═══{C.E}\n")
    entries = history["changes"][-5:]
    
    for i, entry in enumerate(entries, 1):
        print(f"  {C.CY}{i}{C.E} - {entry['new_mac']} ({entry['interface']})")
    
    print(f"  {C.CY}0{C.E} - Retour")
    
    while True:
        try:
            choice = input(f"\n{C.CY}Choix (0-{len(entries)}): {C.E}")
            idx = int(choice)
            if idx == 0:
                return menu_mac()
            if 1 <= idx <= len(entries):
                return entries[idx - 1]['new_mac']
        except (ValueError, EOFError):
            pass
        print_err("Choix invalide")

def menu_confirm(interface, mac):
    """Demande confirmation avant changement"""
    print(f"\n{C.Y}{C.BD}═══ Résumé ═══{C.E}\n")
    print(f"  Interface:  {C.CY}{interface}{C.E}")
    print(f"  Nouvelle:   {C.G}{mac}{C.E}")
    print(f"  Fabricant:  {C.Y}{get_vendor(mac)}{C.E}")
    
    while True:
        try:
            choice = input(f"\n{C.Y}Confirmer? (O/n): {C.E}").strip().lower()
            if choice in ('', 'o', 'oui', 'y', 'yes'):
                return True
            if choice in ('n', 'non', 'no'):
                return False
        except EOFError:
            pass
        print_err("Répondez par O (oui) ou N (non)")

def menu_history():
    """Affiche l'historique complet"""
    history = load_history()
    if not history["changes"]:
        print_warn("Aucun historique")
        return
    
    print(f"\n{C.CY}{C.BD}═══ Historique ═══{C.E}\n")
    for entry in reversed(history["changes"][-10:]):
        print(f"  {C.D}{entry['timestamp'][:16]}{C.E}")
        print(f"    {entry['interface']}: {C.R}{entry['old_mac']}{C.E} → {C.G}{entry['new_mac']}{C.E}")
        separator()

# ═══════════════════════════════════════════════════════════════
# Menu principal
# ═══════════════════════════════════════════════════════════════
def main_menu():
    while True:
        clear()
        print_banner()
        
        root_status = f"{C.G}✓ Root{C.E}" if is_root() else f"{C.R}✗ Non-root{C.E}"
        print(f"  Statut: {root_status}\n")
        
        print(f"  {C.CY}1{C.E} - Changer l'adresse MAC")
        print(f"  {C.CY}2{C.E} - Voir l'historique")
        print(f"  {C.CY}3{C.E} - Quitter")
        
        try:
            choice = input(f"\n{C.CY}➤ {C.E}")
        except EOFError:
            break
        
        if choice == '1':
            if not is_root():
                clear()
                print_banner()
                print_err("Droits root requis!")
                print_info("Relancez avec: sudo python3 mac_changer.py")
                wait_key()
                continue
            
            clear()
            print_banner()
            
            # Étape 1: Choisir l'interface
            interface = menu_interfaces()
            if not interface:
                wait_key()
                continue
            
            # Étape 2: Choisir la MAC
            clear()
            print_banner()
            new_mac = menu_mac()
            if not new_mac:
                wait_key()
                continue
            
            # Étape 3: Confirmation
            clear()
            print_banner()
            if not menu_confirm(interface, new_mac):
                print_warn("Annulé")
                wait_key()
                continue
            
            # Étape 4: Changement
            clear()
            print_banner()
            if change_mac(interface, new_mac):
                print_ok(f"MAC changée: {C.G}{new_mac}{C.E}")
                vendor = get_vendor(new_mac)
                if vendor != "Inconnu":
                    print_info(f"Fabricant: {C.Y}{vendor}{C.E}")
            else:
                print_err("Échec du changement")
            
            wait_key()
        
        elif choice == '2':
            clear()
            print_banner()
            menu_history()
            wait_key()
        
        elif choice == '3':
            print(f"\n{C.G}Au revoir!{C.E}\n")
            break

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n\n{C.G}Au revoir!{C.E}\n")
