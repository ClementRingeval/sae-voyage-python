from classes import Voyage, CartesVoyage, Activite, GRAPHHOPPER_KEY

def lancer_mon_voyage():
    print("=" * 45)
    print("BIENVENUE SUR MONVOYAGE")
    print("=" * 45)

    try:
        # -------- INFOS UTILISATEUR --------
        depart = input("Ville de depart : ")
        destination = input("Destination : ")
        nuits = int(input("Nombre de nuits : "))
        personnes = int(input("Nombre de personnes : "))
        budget_max = float(input("Budget max (€) : "))

        # Instanciation de la classe Voyage
        mon_voyage = Voyage(depart, destination, nuits, personnes, budget_max)

        print("\nA PROPOS DE LA VILLE :")
        description = mon_voyage.collecte.collecter_description_ville(destination)
        print(f"{description}\n")

        # Exécution du déroulement du voyage
        mon_voyage.planifier_transport()
        mon_voyage.selectionner_hotels()
        mon_voyage.selectionner_restaurants()

        # -------- ACTIVITÉS --------
        print("\n--- ACTIVITES ---")
        print("Recuperation des activites...")
        
        activites = mon_voyage.recuperer_activites()
        
        if activites:
            print(f"{len(activites)} activites trouvees :\n")
            for i, act in enumerate(activites[:10], 1):
                print(f"{i}. {act.nom} ({act.type_activite}) - {act.prix}€")
        else:
            print("Aucune activite trouvee.")
            activites = []

        # Génère le programme
        mon_voyage.generer_programme(activites)

        # Proposition de changement d'hôtel
        print("\n" + "-" * 30)
        if input("Voulez-vous changer d'hotel ? (o/n) : ").lower() == 'o':
            if mon_voyage.changer_hotel():
                print("\nMise a jour du programme...")
                mon_voyage.generer_programme(activites)

        # Export des données en CSV
        mon_voyage.exporter_hotels_csv()
        mon_voyage.exporter_restos_csv()
        mon_voyage.exporter_activites_csv()

        # -------- GÉNÉRATION DE LA CARTE --------
        print("\n--- GENERATION DE LA CARTE ---")
        
        # Récupère les coordonnées de la destination
        lat, lon = mon_voyage.collecte.get_localisation(destination)
        if not lat:
            lat, lon = 48.8566, 2.3522  # Paris par défaut
        
        # Crée la carte
        carte = CartesVoyage(destination, lat, lon)
        
        # Récupère les hôtels pour la carte
        hotels_carte = mon_voyage.collecte.collecter_hotels_carte(destination)
        if hotels_carte:
            carte.ajouter_hotels(hotels_carte)
        
        # Ajoute les activités
        if activites:
            carte.ajouter_activites(activites)
        
        # Sauvegarde la carte
        carte.sauvegarder(f"carte_{destination.lower()}.html")
        print(f"Ouvrez le fichier 'carte_{destination.lower()}.html' dans votre navigateur")

        # Comparateur
        if input("\nVoulez-vous comparer avec une autre ville ? (o/n) : ").lower() == 'o':
            mon_voyage.comparer_ville()

    except ValueError:
        print("Erreur : Veuillez entrer des nombres valides.")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")

if __name__ == "__main__":
    lancer_mon_voyage()
