# 🎮 Splatoon-like Multijoueur Local

Un jeu multijoueur local inspiré de Splatoon, conçu pour être joué sur grand écran avec des contrôles via téléphone **sans installation**.

## 📌 Objectif du projet

Créer une expérience multijoueur accessible et fun, où les joueurs s'affrontent en peignant une carte en temps réel, chacun contrôlant un personnage via son smartphone.

## 🔄 Évolution du projet

- **Initialement** prévu comme un jeu coopératif de type *Pico Park*.
- **Pivot** vers un *Splatoon-like* pour mieux exploiter un écran de cinéma (affichage global de la carte).
- **Cible** : Joueurs en local, chaque joueur utilise son téléphone comme manette grâce à une interface web.

## 🚀 Fonctionnalités actuelles

- ✅ Connexion mobile sans installation via navigateur.
- ✅ Rendu temps réel de la map avec zones peintes.
- ✅ Mouvement des joueurs synchronisé à l’écran.
- ✅ Interface de réglage des paramètres avec Pygame.

## ⚙️ Technologies utilisées

- **Python / Pygame** – Moteur principal et interface de test.
- **WebSockets** – Communication temps réel entre clients (téléphones) et serveur.
- **HTML / JS** – Interface web mobile pour les contrôles.
- **(À venir)** Serveur web en Flask ou FastAPI pour héberger l’interface.

## 🧠 Points techniques clés

- Rendu fluide des zones peintes, même en multijoueur.
- Système de contrôle mobile ergonomique sans téléchargement.
- Architecture réseau légère avec buffering des inputs.

## 🧩 Problèmes rencontrés

- Difficulté de synchronisation entre devices.
- Optimisation du rendu peinture sur grand écran.
- Gestion de la latence des entrées mobiles.

## ✅ Solutions mises en place

- Buffer d’input pour lisser les mouvements.
- Algorithme de fusion simplifié pour les zones peintes.
- WebSocket optimisé pour la communication.

## 📅 À venir

- 🎯 Système de scoring par territoire peint.
- 🔫 Intégration de différents types d’armes et équilibrage.
- 🔊 Ajout de sons/musiques dynamiques.
- 🌐 Interface lobby et gestion des joueurs via téléphone.

## 🎓 Projet étudiant

Développé dans le cadre d’un projet universitaire par une équipe d’étudiants passionnés.

---

🕹️ *Préparez vos téléphones… et que le meilleur peintre gagne !*
