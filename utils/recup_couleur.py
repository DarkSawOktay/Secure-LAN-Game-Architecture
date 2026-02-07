import logging
import pickle
import sys
import time
import numpy as np
from utils.config import TeamConfig, GameConfig

# Configuration du logger
logger = logging.getLogger("AnalyseCouleur")

def calcul_pourcentage_nuance(arr, map_couleur, width, height, seuil=2):
    """
    Calcule le pourcentage de chaque couleur présente dans l'image en utilisant NumPy pour une comparaison rapide.
    """
    total_pixels = width * height
    if total_pixels == 0:
        return {team: 0.0 for team in map_couleur}

    # Conversion en tableau numpy (la surface est déjà convertie avec array3d)
    arr = np.array(arr)  # Shape (height, width, 3) pour RGB

    seuil_carre = seuil * seuil  # Calcul du seuil au carré pour comparer les distances
    compteur_couleur = {team: 0 for team in map_couleur}

    for ident, (r_ref, g_ref, b_ref) in map_couleur.items():
        # Calcul de la distance carrée entre chaque pixel et la couleur de référence
        r_diff = arr[:, :, 0] - r_ref
        g_diff = arr[:, :, 1] - g_ref
        b_diff = arr[:, :, 2] - b_ref
        dist_carre = r_diff**2 + g_diff**2 + b_diff**2  # Distance carrée

        # Compter le nombre de pixels dans la tolérance du seuil
        pixels_color = np.sum(dist_carre <= seuil_carre)  # Seulement les pixels dont la distance est en-dessous du seuil
        # print(f"Couleur {ident}: Pixels trouvés : {pixels_color}")  # Log pour vérifier les pixels comptés
        compteur_couleur[ident] = pixels_color

    # Calcul des pourcentages en fonction du nombre total de pixels
    pourcentages = {team: (count / total_pixels) for team, count in compteur_couleur.items()}
    # print(f"Pourcentages: {pourcentages}")  # Log pour vérifier les pourcentages calculés

    return pourcentages



def processus_calcul_couleur(to_queue, from_queue, calc_couleur, paint_surface_queue=None):
    """
    Processus qui calcule, en tâche de fond, les pourcentages de chaque couleur.
    Cette fonction est maintenant optimisée avec NumPy.
    """

    seuil_rgb = 20  # Tolérance (fuzzy)

    last_analysis_time = 0
    analysis_interval = 0.5  # Intervalle d'analyse en secondes

    while calc_couleur.value:
        current_time = time.time()

        if current_time - last_analysis_time < analysis_interval:
            time.sleep(0.1)
            continue

        try:
            if not to_queue.empty():
                data = to_queue.get(block=False)
                if data is None:
                    break
                # Désérialisation et analyse
                arr = pickle.loads(data)  # Convertit l'objet sérialisé
                result = calcul_pourcentage_nuance(arr, TeamConfig.COLOR_MAP, GameConfig.BASE_WIDTH, GameConfig.BASE_HEIGHT)
                from_queue.put(result)  # Envoie les résultats du calcul
                last_analysis_time = current_time
        except Exception as e:
            print(f"Erreur lors du calcul des couleurs: {e}")

        time.sleep(0.1)  # Attente avant la prochaine analyse
