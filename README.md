<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=2b2d42&height=180&section=header&text=Secure%20LAN%20Architecture&fontSize=45&fontAlignY=35&animation=fadeIn&fontColor=ffffff"/>
  
  <br>

  ![Python](https://img.shields.io/badge/Language-Python%203-3776AB?style=for-the-badge&logo=python&logoColor=white)
  ![Flask](https://img.shields.io/badge/Framework-Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
  ![Multiprocessing](https://img.shields.io/badge/Architecture-Multiprocessing-orange?style=for-the-badge)
  ![Network](https://img.shields.io/badge/Tech-WebSockets%20%26%20LAN-blue?style=for-the-badge)

</div>

<br>

## 📄 About The Project

Ce projet est une démonstration d'architecture logicielle distribuée en **Python**. Il s'agit d'un système de jeu collaboratif en réseau local (LAN) où les smartphones des utilisateurs servent de contrôleurs (manettes) via une interface Web, interagissant en temps réel avec le moteur de jeu central.

L'objectif technique était de gérer la **haute disponibilité** et la **synchronisation** entre plusieurs processus indépendants.

> *This project was developed as a group assignment. This repository focuses on the **Network Architecture** and **Process Management** layers.*

---

## 👨‍💻 My Contribution (Network & System Security Focus)

Dans une architecture distribuée, la gestion des accès concurrents est critique. Mon travail s'est concentré sur la robustesse du système :

### 📡 1. Network & Input Handling
* **Client-Server Communication:** Mise en place d'un serveur Flask léger pour recevoir les commandes des smartphones (clients) via HTTP/Sockets.
* **Input Sanitization:** Traitement des entrées utilisateurs (commandes de direction) pour éviter les comportements inattendus ou les injections de commandes malformées vers le moteur de jeu.

### 🔄 2. Concurrency & Availability (DoS Prevention)
Pour éviter qu'une surcharge réseau ne bloque le jeu (Déni de Service local), j'ai implémenté une architecture **Multi-Processus** stricte :
* **Isolation des Processus :** Le serveur Web (`server_process`), le moteur de jeu (`game_engine`) et l'affichage sont des processus système distincts gérés par `multiprocessing`.
* **Inter-Process Communication (IPC) :** Utilisation de `Queues` et de `Pipes` sécurisés pour échanger les données sans risque de *Race Conditions* ou de corruption de mémoire.
* **Watchdog :** Le `manager.py` agit comme un superviseur pour lancer et arrêter proprement les processus, assurant la stabilité de l'application.

---

## 🛠️ Tech Stack

* **Core Language:** Python 3.10+
* **System Library:** `multiprocessing` (Process, Queue, Manager)
* **Web Server:** Flask (Micro-framework)
* **Frontend:** HTML5 / CSS3 / JavaScript (Mobile First)

---

## 💻 How to Run

### Prerequisites
* Python 3.x
* A local network (Wi-Fi) to connect smartphones.

### Installation

1. **Clone the repository:**
```bash
git clone [https://github.com/DarkSawOktay/Secure-LAN-Game-Architecture.git](https://github.com/DarkSawOktay/Secure-LAN-Game-Architecture.git)
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```


3. **Run the System:**
The `manager.py` script orchestrates all subsystems (Server, Game, Display).
```bash
python manager.py
```


4. **Connect Players:**
* The console will display the local IP address (e.g., `http://192.168.1.15:5000`).
* Connect smartphones to the same Wi-Fi and open this URL to join the lobby.



---

<div align="center">
<sub>Portfolio Project by Oktay Gencer</sub>
</div>
