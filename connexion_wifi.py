import subprocess
import re
import time


class WifiManager:

    @staticmethod
    def activer_wifi(interface="Wi-Fi"):
        """Active l'interface Wi-Fi."""
        resultat = subprocess.run(
            ["netsh", "interface", "set", "interface", interface, "enable"],
            capture_output=True,
            text=True
        )

        return resultat.returncode == 0

    @staticmethod
    def scanner_reseaux():
        """Retourne la liste des SSID disponibles."""
        resultat = subprocess.run(
            ["netsh", "wlan", "show", "networks"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        ssids = []

        for ligne in resultat.stdout.splitlines():
            if "SSID" in ligne and "BSSID" not in ligne:
                match = re.search(r"SSID\s+\d+\s*:\s*(.*)", ligne)
                if match:
                    nom = match.group(1).strip()
                    if nom:
                        ssids.append(nom)

        return ssids

    @staticmethod
    def connecter(ssid):
        """Se connecte à un réseau déjà enregistré."""
        resultat = subprocess.run(
            ["netsh", "wlan", "connect", f"name={ssid}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        return resultat.returncode == 0

    @staticmethod
    def est_connecte(ssid=None):
        """Vérifie si le PC est connecté."""

        resultat = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        texte = resultat.stdout

        if "State" not in texte and "État" not in texte:
            return False

        if "connected" not in texte.lower() and "connecté" not in texte.lower():
            return False

        if ssid:
            return ssid.lower() in texte.lower()

        return True


if __name__ == "__main__":

    print("Activation du Wi-Fi...")

    if WifiManager.activer_wifi():
        print("✓ Wi-Fi activé")
    else:
        print("Impossible d'activer le Wi-Fi")

    time.sleep(2)

    print("\nRecherche des réseaux...\n")

    reseaux = WifiManager.scanner_reseaux()

    for r in reseaux:
        print("-", r)

    wifi = "NomDuWifi"

    print(f"\nConnexion à {wifi}...")

    if WifiManager.connecter(wifi):
        print("Commande envoyée.")
    else:
        print("Erreur de connexion.")

    time.sleep(5)

    if WifiManager.est_connecte(wifi):
        print(f"✓ Connecté à {wifi}")
    else:
        print("✗ La connexion a échoué.")