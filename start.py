#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path
import time
import json

def is_running_in_virtualenv():
    """Vérifie si nous sommes dans un environnement virtuel"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def print_step(message):
    """Affiche un message d'étape avec un style cool"""
    print("\n" + "="*50)
    print(f"🚀 {message}")
    print("="*50 + "\n")

def print_error(message):
    """Affiche un message d'erreur"""
    print(f"\n❌ ERREUR: {message}\n")

def print_success(message):
    """Affiche un message de succès"""
    print(f"\n✅ {message}\n")

def run_command(command, shell=False):
    """Exécute une commande et retourne son statut"""
    try:
        subprocess.run(
            command if shell else command.split(),
            check=True,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Commande échouée: {command}")
        print(f"Sortie d'erreur: {e.stderr}")
        return False

def check_python_version():
    """Vérifie la version de Python"""
    print_step("Vérification de la version Python")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error("Python 3.8 ou supérieur est requis")
        sys.exit(1)
    print_success(f"Python {version.major}.{version.minor}.{version.micro} détecté")

def setup_virtual_env():
    """Configure l'environnement virtuel"""
    print_step("Configuration de l'environnement virtuel")
    
    # Supprimer l'ancien venv s'il existe
    if os.path.exists("venv"):
        print("Suppression de l'ancien environnement virtuel...")
        try:
            # Désactiver l'environnement virtuel s'il est actif
            if platform.system() == "Windows":
                # Forcer la fermeture de tous les processus Python dans le venv
                try:
                    subprocess.run("taskkill /F /IM python.exe", shell=True, stderr=subprocess.DEVNULL)
                except:
                    pass
                # Utiliser rd au lieu de rmdir pour une suppression forcée
                run_command("rd /s /q venv", shell=True)
            else:
                shutil.rmtree("venv")
            
            # Attendre un peu pour s'assurer que la suppression est terminée
            time.sleep(1)
            
        except Exception as e:
            print_error(f"Erreur lors de la suppression du venv: {e}")
            return False

    # S'assurer que le dossier venv n'existe plus
    if os.path.exists("venv"):
        try:
            shutil.rmtree("venv", ignore_errors=True)
            time.sleep(1)
        except:
            pass

    # Créer un nouveau venv
    print("Création d'un nouvel environnement virtuel...")
    if not run_command(f"{sys.executable} -m venv venv"):
        return False

    # Déterminer les chemins Python
    if platform.system() == "Windows":
        python_path = "venv\\Scripts\\python.exe"
        pip_path = "venv\\Scripts\\pip"
        activate_path = "venv\\Scripts\\activate"
    else:
        python_path = "venv/bin/python"
        pip_path = "venv/bin/pip"
        activate_path = "venv/bin/activate"

    # Attendre que le venv soit prêt
    time.sleep(2)

    # Mettre à jour pip en utilisant la syntaxe recommandée
    print("Mise à jour de pip...")
    if not run_command(f"{python_path} -m pip install --upgrade pip"):
        print("Tentative alternative de mise à jour de pip...")
        if not run_command(f"{pip_path} install --upgrade pip"):
            print_error("Impossible de mettre à jour pip. Continuons tout de même...")
            # On continue malgré l'erreur car ce n'est pas critique
            pass

    print_success("Environnement virtuel configuré")
    return True, activate_path

def install_requirements():
    """Installe les dépendances"""
    print_step("Installation des dépendances")
    
    if platform.system() == "Windows":
        pip_path = "venv\\Scripts\\pip"
    else:
        pip_path = "venv/bin/pip"

    if not run_command(f"{pip_path} install -r requirements.txt"):
        return False
        
    print_success("Dépendances installées")
    return True

def setup_env_file():
    """Configure le fichier .env"""
    print_step("Configuration du fichier .env")
    
    if not os.path.exists(".env"):
        if os.path.exists("env_example.txt"):
            shutil.copy("env_example.txt", ".env")
            print_success("Fichier .env créé à partir de env_example.txt")
            print("\n⚠️  N'oubliez pas de configurer vos variables dans le fichier .env!")
        else:
            print_error("Fichier env_example.txt non trouvé")
            return False
    else:
        print("Le fichier .env existe déjà")
    
    return True

def clean_pycache():
    """Nettoie les fichiers cache Python"""
    print_step("Nettoyage des fichiers cache")
    
    # Supprimer tous les __pycache__ et .pyc
    for root, dirs, files in os.walk("."):
        for dir in dirs:
            if dir == "__pycache__":
                path = os.path.join(root, dir)
                print(f"Suppression de {path}")
                shutil.rmtree(path)
        for file in files:
            if file.endswith(".pyc"):
                path = os.path.join(root, file)
                print(f"Suppression de {file}")
                os.remove(path)

    print_success("Cache nettoyé")

def clean_logs():
    """Nettoie les fichiers de log"""
    print_step("Nettoyage des logs")
    
    if os.path.exists("logs"):
        files = os.listdir("logs")
        for file in files:
            if file.endswith(".log"):
                path = os.path.join("logs", file)
                print(f"Suppression de {file}")
                os.remove(path)
    
    print_success("Logs nettoyés")

def start_app():
    """Démarre l'application"""
    print_step("Démarrage de l'application")
    
    if platform.system() == "Windows":
        python_path = "venv\\Scripts\\python"
    else:
        python_path = "venv/bin/python"

    try:
        subprocess.run([python_path, "app.py"])
    except KeyboardInterrupt:
        print("\n\n👋 Au revoir!")
    except Exception as e:
        print_error(f"Erreur lors du démarrage: {e}")

def main():
    """Fonction principale"""
    # Vérifier qu'on n'est pas dans un venv
    if is_running_in_virtualenv():
        print_error("Ce script doit être exécuté avec Python système, pas depuis un environnement virtuel!")
        print("\nUtilisez la commande:")
        if platform.system() == "Windows":
            print("python start.py")
        else:
            print("python3 start.py")
        sys.exit(1)

    start_time = time.time()
    
    print("\n" + "="*50)
    print("🎯 DÉMARRAGE DU PROJET TIKTOK API")
    print("="*50 + "\n")

    # Vérifier Python
    check_python_version()

    # Nettoyer
    clean_pycache()
    clean_logs()

    # Configurer l'environnement
    venv_result = setup_virtual_env()
    if not venv_result:
        sys.exit(1)

    # Installer les dépendances
    if not install_requirements():
        sys.exit(1)

    # Configurer .env
    if not setup_env_file():
        sys.exit(1)

    # Calculer le temps d'exécution
    setup_time = time.time() - start_time
    print(f"\n⏱️  Configuration terminée en {setup_time:.2f} secondes")

    # Démarrer l'app
    print("\n" + "="*50)
    print("🚀 LANCEMENT DE L'APPLICATION")
    print("="*50 + "\n")
    
    start_app()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Au revoir!")
    except Exception as e:
        print_error(f"Erreur inattendue: {e}")
        sys.exit(1) 