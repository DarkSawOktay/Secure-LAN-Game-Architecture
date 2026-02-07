import multiprocessing as mp
import sys
import time

from network.server_process import webapp_main, get_local_ip
from network.admin_process import admin_main
from utils.display_process import display_main
from game_core.lobby_logic import lobby_logic
from game_core.real_game import real_game_logic
from utils.recup_couleur import processus_calcul_couleur

def main():
    mp.set_start_method("spawn")

    manager = mp.Manager()
    connected_players = manager.dict()
    admin_queue = mp.Queue()
    manager_queue = mp.Queue()
    display_queue = mp.Queue()
    lobby_state_queue = mp.Queue()
    paint_surface_queue = mp.Queue()

    game_started = manager.Value("b", False)
    prepare_phase = manager.Value("b", False)
    prepare_start_time = manager.Value("d", 0.0)
    game_start_time = manager.Value("d", 0.0)  # Nouveau timer réel lancé après préparation

    game_duration = manager.Value("i", 60)
    friendly_collisions = manager.Value("b", True)
    calc_couleur = manager.Value("b", True)

    to_couleur_queue = mp.Queue()
    from_couleur_queue = mp.Queue()

    speed_config = manager.dict({
        "neutre": 8,
        "allie": 12,
        "ennemi": 4
    })

    processes = {
        "webapp": mp.Process(
            target=webapp_main,
            args=(connected_players, game_started),
            name="WebApp"
        ),
        "admin": mp.Process(
            target=admin_main,
            args=(admin_queue, manager_queue, connected_players, game_started, friendly_collisions, calc_couleur, speed_config, game_duration),
            name="Admin"
        ),
        "display": mp.Process(
            target=display_main,
            args=(
                display_queue, lobby_state_queue,
                game_started, get_local_ip(),
                calc_couleur,
                to_couleur_queue,
                from_couleur_queue,
                paint_surface_queue,
                prepare_phase,
                prepare_start_time
            ),
            name="Display"
        ),
        "lobby": mp.Process(
            target=lobby_logic,
            args=(connected_players, lobby_state_queue, game_started),
            name="Lobby"
        ),
        "couleurs": mp.Process(
            target=processus_calcul_couleur,
            args=(to_couleur_queue, from_couleur_queue, calc_couleur, paint_surface_queue),
            name="ProcessCouleur"
        )
    }

    for proc in processes.values():
        proc.start()

    real_game_proc = None
    print("[Manager] Tous les processus sont lancés. Ctrl+C pour quitter.")

    try:
        while True:
            # Phase préparation
            if prepare_phase.value:
                if time.time() - prepare_start_time.value >= 6:
                    print("[Manager] Fin de la phase de préparation.")
                    prepare_phase.value = False
                    game_start_time.value = time.time()  # Démarrage officiel de la partie ici

            # Redémarrage lobby si crash après partie
            if not game_started.value and real_game_proc and not real_game_proc.is_alive():
                if not processes["lobby"].is_alive():
                    print("[Manager] Redémarrage du lobby après fin de partie.")
                    processes["lobby"] = mp.Process(
                        target=lobby_logic,
                        args=(connected_players, lobby_state_queue, game_started),
                        name="Lobby"
                    )
                    processes["lobby"].start()
                    real_game_proc = None

            # Admin triggers
            if not admin_queue.empty():
                msg = admin_queue.get()
                if msg == "START_GAME":
                    print("[Manager] Passage immédiat en mode jeu avec phase préparation.")
                    game_started.value = True
                    prepare_phase.value = True
                    prepare_start_time.value = time.time()

                    if processes["lobby"].is_alive():
                        processes["lobby"].terminate()
                        processes["lobby"].join()

                    real_game_proc = mp.Process(
                        target=real_game_logic,
                        args=(connected_players, lobby_state_queue,
                              game_started, friendly_collisions, paint_surface_queue, to_couleur_queue, from_couleur_queue, game_duration, speed_config, prepare_phase,game_start_time),
                        name="RealGame"
                    )
                    real_game_proc.start()

            manager_queue.put(("UPDATE_PLAYERS", len(connected_players)))
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("[Manager] Arrêt demandé. Fermeture...")

        for name, proc in processes.items():
            if proc.is_alive():
                proc.terminate()
                proc.join()

        if real_game_proc and real_game_proc.is_alive():
            real_game_proc.terminate()
            real_game_proc.join()

        print("[Manager] Fermeture propre.")
        sys.exit(0)

if __name__ == "__main__":
    main()
