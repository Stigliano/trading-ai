#!/usr/bin/env python3
"""
vpn_utils.py - Utilities per la gestione della rotazione IP tramite VPN.
"""

import os
import time
import random
import logging
import subprocess
import socket
import requests
import json
from datetime import datetime

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('vpn_utils')

# Path configurazioni
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config')
VPN_CONFIG_PATH = os.path.join(CONFIG_DIR, 'vpn_config.json')

# Crea la directory di configurazione se non esiste
os.makedirs(CONFIG_DIR, exist_ok=True)

# Configurazione predefinita VPN
DEFAULT_VPN_CONFIG = {
    "vpn_provider": "openvpn",
    "available_locations": ["us", "uk", "de", "fr", "nl", "sg"],
    "connection_command": "sudo openvpn --config {config_file} --daemon",
    "disconnect_command": "sudo pkill -f openvpn",
    "config_dir": "/etc/openvpn/client",
    "rotation_interval": 30,  # minuti
    "last_rotation": None
}

def load_vpn_config():
    """Carica la configurazione VPN."""
    if not os.path.exists(VPN_CONFIG_PATH):
        # Crea file di configurazione predefinito
        with open(VPN_CONFIG_PATH, 'w') as f:
            json.dump(DEFAULT_VPN_CONFIG, f, indent=4)
        logger.info(f"✅ Creato file di configurazione VPN in {VPN_CONFIG_PATH}")
        return DEFAULT_VPN_CONFIG
    
    try:
        with open(VPN_CONFIG_PATH, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"❌ Errore caricamento configurazione VPN: {str(e)}")
        return DEFAULT_VPN_CONFIG

def save_vpn_config(config):
    """Salva la configurazione VPN."""
    try:
        with open(VPN_CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=4)
        logger.info("✅ Configurazione VPN aggiornata")
    except Exception as e:
        logger.error(f"❌ Errore salvataggio configurazione VPN: {str(e)}")

def get_current_ip():
    """Ottiene l'indirizzo IP pubblico attuale."""
    try:
        ip = requests.get('https://api.ipify.org').text
        logger.info(f"IP pubblico attuale: {ip}")
        return ip
    except Exception as e:
        logger.error(f"❌ Errore ottenimento IP: {str(e)}")
        return None

def connect_vpn(location=None):
    """
    Connette a una VPN in una location specifica.
    
    Args:
        location (str, optional): Codice location (es. "us", "uk")
    
    Returns:
        bool: True se connessione riuscita, altrimenti False
    """
    config = load_vpn_config()
    
    # Disconnetti da eventuali VPN attive
    disconnect_vpn()
    
    # Se location non specificata, scegline una casuale
    if not location:
        location = random.choice(config['available_locations'])
    
    logger.info(f"🔄 Tentativo connessione VPN: {location}")
    
    try:
        # Trova il file di configurazione per la location
        config_pattern = f"{location}"
        config_dir = config.get('config_dir', '/etc/openvpn/client')
        
        # Cerca file di configurazione compatibile
        config_files = []
        if os.path.exists(config_dir):
            config_files = [f for f in os.listdir(config_dir) if config_pattern in f.lower() and f.endswith('.ovpn')]
        
        if not config_files:
            logger.error(f"❌ Nessun file di configurazione VPN trovato per {location}")
            return False
        
        # Scegli file casuale
        config_file = os.path.join(config_dir, random.choice(config_files))
        
        # Applica comando di connessione
        cmd = config['connection_command'].format(config_file=config_file)
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        # Verifica l'esito
        if process.returncode != 0:
            logger.error(f"❌ Errore connessione VPN: {stderr.decode('utf-8')}")
            return False
        
        # Attendi che la connessione sia stabilita
        time.sleep(5)
        
        # Verifica cambio IP
        new_ip = get_current_ip()
        if new_ip:
            logger.info(f"✅ Connessione VPN stabilita: {location}")
            
            # Aggiorna configurazione
            config['last_rotation'] = datetime.now().isoformat()
            save_vpn_config(config)
            
            return True
        else:
            logger.warning("⚠️ Impossibile verificare il cambio IP")
            return False
            
    except Exception as e:
        logger.error(f"❌ Errore durante connessione VPN: {str(e)}")
        return False

def disconnect_vpn():
    """
    Disconnette dalla VPN attuale.
    
    Returns:
        bool: True se disconnessione riuscita, altrimenti False
    """
    config = load_vpn_config()
    
    try:
        logger.info("🔄 Disconnessione VPN...")
        process = subprocess.Popen(config['disconnect_command'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        # Attendi disconnessione
        time.sleep(3)
        
        logger.info("✅ Disconnessione VPN completata")
        return True
    except Exception as e:
        logger.error(f"❌ Errore durante disconnessione VPN: {str(e)}")
        return False

def should_rotate_vpn():
    """
    Determina se è necessario ruotare la connessione VPN.
    
    Returns:
        bool: True se è necessario ruotare, altrimenti False
    """
    config = load_vpn_config()
    
    last_rotation = config.get('last_rotation')
    interval_minutes = config.get('rotation_interval', 30)
    
    if not last_rotation:
        return True
    
    try:
        last_time = datetime.fromisoformat(last_rotation)
        elapsed = (datetime.now() - last_time).total_seconds() / 60
        return elapsed >= interval_minutes
    except Exception:
        return True

def rotate_vpn_if_needed():
    """
    Ruota la connessione VPN se necessario in base all'intervallo impostato.
    
    Returns:
        bool: True se rotazione avvenuta, False altrimenti
    """
    if should_rotate_vpn():
        logger.info("🔄 Rotazione VPN necessaria")
        return connect_vpn()
    else:
        logger.info("✅ Rotazione VPN non necessaria")
        return False

def setup_vpn_config(interval_minutes=30, available_locations=None):
    """
    Configura i parametri di rotazione VPN.
    
    Args:
        interval_minutes (int): Minuti tra le rotazioni
        available_locations (list): Lista di location disponibili
    """
    config = load_vpn_config()
    
    # Aggiorna parametri
    config['rotation_interval'] = interval_minutes
    
    if available_locations:
        config['available_locations'] = available_locations
    
    save_vpn_config(config)
    logger.info(f"✅ Configurazione rotazione VPN aggiornata: intervallo {interval_minutes} minuti")

if __name__ == "__main__":
    print("== Utility Rotazione VPN ==")
    print(f"IP attuale: {get_current_ip()}")
    
    while True:
        print("\nMenu:")
        print("1. Connetti VPN (location casuale)")
        print("2. Disconnetti VPN")
        print("3. Imposta intervallo rotazione")
        print("4. Visualizza IP attuale")
        print("5. Esci")
        
        choice = input("\nScelta: ")
        
        if choice == "1":
            connect_vpn()
        elif choice == "2":
            disconnect_vpn()
        elif choice == "3":
            try:
                interval = int(input("Intervallo in minuti: "))
                setup_vpn_config(interval_minutes=interval)
            except ValueError:
                print("❌ Inserisci un numero valido")
        elif choice == "4":
            print(f"IP attuale: {get_current_ip()}")
        elif choice == "5":
            break
        else:
            print("❌ Scelta non valida")
