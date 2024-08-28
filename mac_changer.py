#!/usr/bin/env python
# coding: UTF8
import subprocess
import optparse
import re


def get_arguments():
    parser = optparse.OptionParser()
    parser.add_option("-i", "--interface", dest="interface", help="Interface de l'adresse MAC à modifier")
    parser.add_option("-m", "--mac", dest="new_mac", help="Nouvelle adresse MAC")
    (Options, arguments) = parser.parse_args()
    if not Options.interface:
        parser.error("[-] Merci de renseigner une interface valide, --help pour plus d'infos")
    elif not Options.new_mac:
        parser.error("[-] Merci de renseigner une adresse MAC valide, --help pour plus d'infos")
    return Options


def change_mac(interface, new_mac):
    subprocess.call(["ifconfig", interface, "down"])
    subprocess.call(["ifconfig", interface, "hw", "ether", new_mac])
    subprocess.call(["ifconfig", interface, "up"])
    print("[+] Nouvelle adresse Mac demandée pour " + interface + " : " + new_mac)

def get_current_mac(interface):
    ifconfig_result = subprocess.check_output(["ifconfig", interface])
    mac_address_search_result = re.search(r"\w\w:\w\w:\w\w:\w\w:\w\w:\w\w", str(ifconfig_result))
    if mac_address_search_result:
        #print(mac_address_search_result)
        return mac_address_search_result.group(0)
    else:
        print("[-] Impossible de lire l'adresse MAC.")


options = get_arguments()
change_mac(options.interface, options.new_mac)
current_MAC = get_current_mac(options.interface)
if current_MAC == options.new_mac:
    print("[+] L'adresse MAC a été modifiée avec succés!")
else:
    print("[-] L'adresse MAC n'a pas été modifiée")
