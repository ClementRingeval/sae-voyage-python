import requests
import random
from bs4 import BeautifulSoup
import folium
from folium import plugins
import csv

# --- CONSTANTES ET CONFIGURATION ---

# API Keys
GRAPHHOPPER_KEY = "5705201c-7309-410b-a2b3-348bc31f43c3"
URL_HOTELS_API = "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/hebergements-classes/records"
URL_ACTIVITES_API = "https://data.culture.gouv.fr/api/explore/v2.1/catalog/datasets/base-des-lieux-et-des-equipements-culturels/records?where=nom%20!=%20'Immeuble'%20and%20nom%20!=%20'Immeubles'%20and%20nom%20!=%20'Maison'"

# Configuration Hôtels
TARIFS_HOTELS = {
    "1 étoile": 55, "2 étoiles": 75, "3 étoiles": 105, 
    "4 étoiles": 165, "5 étoiles": 380, "Auberge collective": 35
}

# Configuration Restaurants
CAT_RESTOS = {
    "1": ("Fast-food / Kebab", "Fast+Food", 12),
    "2": ("Italien / Pizza", "Italien", 25),
    "3": ("Turc / Spécialités", "Turc", 20),
    "4": ("Français / Tradition", "Francais", 35),
    "5": ("Asiatique", "Asiatique", 22),
    "0": ("Tous types", "Restaurants", 28)
}


# Configuration Transport
MODES_TRANSPORT = {"1": "voiture", "2": "vélo", "3": "pied"}

# Configuration Prix Activités (Estimation par personne)
PRIX_ACTIVITES = {
    "Cinéma": 12, "Musée": 15, "Monument": 10, "Monument historique": 10,
    "Théâtre": 25, "Parc et jardin": 0, "Opéra": 45, "Scène": 20,
    "Centre d'art": 8, "Centre culturel": 5, "Lieu de mémoire": 0,
    "Lieu archéologique": 8
}

# --- ETAPE 1 : Donnees de base ---

class Hotel:
    def __init__(self, nom, etoiles, prix_nuit, ville):
        self.nom = nom
        self.etoiles = etoiles
        self.prix_nuit = prix_nuit
        self.ville = ville

class Restaurant:
    def __init__(self, nom):
        self.nom = nom

class Activite:
    def __init__(self, nom, type_activite, latitude, longitude, adresse, prix=0):
        self.nom = nom
        self.type_activite = type_activite
        self.latitude = latitude
        self.longitude = longitude
        self.adresse = adresse
        self.prix = prix

    def __repr__(self):
        return f"{self.nom} ({self.type_activite}) - {self.prix}€ - {self.adresse}"
    
    def to_csv_row(self):
        """Retourne les données sous forme de ligne CSV"""
        return [self.nom, self.type_activite, self.adresse, self.latitude, self.longitude, self.prix]

# --- ETAPE 2 : Groupements ---

class Hotels:
    def __init__(self):
        self.liste_hotels = []

class Restaurants:
    def __init__(self):
        self.liste_restaurants = []

class Activites:
    def __init__(self):
        self.liste_activites = []

# --- ETAPE 3 : Moteurs de calcul et APIs ---

class Collecte:
    def __init__(self, key):
        self.key = key
        self.headers = {"User-Agent": "Mozilla/5.0"}

    def collecter_description_ville(self, ville):
        ville_url = ville.lower().replace(" ", "-")
        url = f"https://www.annuaire-mairie.fr/ville-{ville_url}.html"

        try:
            res = requests.get(url, headers=self.headers, timeout=5)
            soup = BeautifulSoup(res.content, "html.parser")

            for p in soup.find_all("p"):
                texte = p.get_text(separator=" ", strip=True)
                texte = " ".join(texte.split())

                if "commune française" in texte or "située dans" in texte:
                    return texte.split("Pour toutes vos démarches")[0]

            return "Description non disponible."

        except:
            return "Erreur lors de la récupération de la description."

    def collecter_meteo(self, ville):
        ville_url = ville.lower().replace(" ", "-")
        url = f"https://www.annuaire-mairie.fr/meteo-{ville_url}.html"

        try:
            res = requests.get(url, headers=self.headers, timeout=5)
            soup = BeautifulSoup(res.content, "html.parser")
            blocs = soup.find_all("div", class_="weather-container")
            meteos = [b.get_text(" ", strip=True) for b in blocs[:7]]
            if meteos:
                return meteos
            else:
                return ["18°C", "16°C", "14°C", "19°C", "17°C", "20°C", "18°C"]
        except:
            return ["18°C", "16°C", "14°C", "19°C", "17°C", "20°C", "18°C"]

    def calculer_transport(self, depart, arrivee, mode):
        def coords_nominatim(ville):
            """Utilise Nominatim pour obtenir les coordonnées"""
            url = f"https://nominatim.openstreetmap.org/search?city={ville}&format=json&limit=1"
            headers = {"User-Agent": "MonVoyage/1.0"}
            try:
                data = requests.get(url, headers=headers, timeout=5).json()
                if data and len(data) > 0:
                    lat = data[0]['lat']
                    lon = data[0]['lon']
                    return f"{lat},{lon}"
            except:
                pass
            return None

        c1 = coords_nominatim(depart)
        c2 = coords_nominatim(arrivee)

        if not c1 or not c2:
            return 100, 120

        try:
            url = (
                f"https://graphhopper.com/api/1/route?"
                f"point={c1}&point={c2}&profile={mode}&key={self.key}"
            )

            data = requests.get(url, timeout=5).json()
            if "paths" in data and data["paths"]:
                info = data["paths"][0]
                distance = info["distance"] / 1000
                temps = round(info["time"] / 60000)
                return distance, temps
        except:
            pass

        return 100, 120

    # --- ACTIVITES ---
    def get_localisation(self, ville):
        """Récupère la localisation d'une ville via Nominatim"""
        try:
            url = f"https://nominatim.openstreetmap.org/search?city={ville}&format=json&limit=1"
            headers = {"User-Agent": "MonVoyage/1.0"}
            response = requests.get(url, headers=headers, timeout=5).json()
            
            if response and len(response) > 0:
                result = response[0]
                lat = float(result['lat'])
                lon = float(result['lon'])
                return lat, lon
            else:
                print(f"Aucun resultat pour {ville}")
                return None, None
        except Exception as e:
            print(f"Erreur localisation {ville}: {e}")
            return None, None

    def collecter_activites(self, ville):
        """Récupère les activités culturelles proches de la ville"""
        liste_activites = []
        
        try:
            # Récupère la localisation de la destination
            ville_lat, ville_lon = self.get_localisation(ville)
            
            if not ville_lat or not ville_lon:
                print(f"Impossible de localiser {ville}")
                return []
            
            # Récupère les activités avec filtre spatial par localisation
            types_interessants = [
                "Cinéma", "Musée", "Monument", "Théâtre", "Parc et jardin",
                "Opéra", "Scène", "Centre d'art", "Centre culturel",
                "Lieu de mémoire", "Lieu archéologique"
            ]
            
            type_filter = " OR ".join([f'type_equipement_ou_lieu="{t}"' for t in types_interessants])
            base_url = URL_ACTIVITES_API.split("?")[0]
            where_clause = f"({type_filter}) AND within_distance(coordonnees_geo, geom'POINT({ville_lon} {ville_lat})', 100000)"

            params = {
                "limit": 50,
                "select": "nom,type_equipement_ou_lieu,adresse,adresse_postale,latitude,longitude,coordonnees_geo",
                "where": where_clause
            }
            
            response = requests.get(base_url, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"Erreur API: {response.status_code}")
                return []
            
            for item in response.json().get("results", []):
                try:
                    nom = item.get("nom", "Sans nom")
                    type_act = item.get("type_equipement_ou_lieu", "Autre")
                    adresse = item.get("adresse", item.get("adresse_postale", "Adresse non disponible"))
                    lat = float(item.get("latitude") or item.get("coordonnees_geo", {}).get("lat", 0))
                    lon = float(item.get("longitude") or item.get("coordonnees_geo", {}).get("lon", 0))
                    
                    if lat and lon and nom not in ["Immeuble", "Immeubles", "Maison"]:
                        prix = PRIX_ACTIVITES.get(type_act, 0)
                        liste_activites.append(Activite(nom, type_act, lat, lon, adresse, prix))
                except: pass
            
            liste_activites.sort(key=lambda a: (a.latitude - ville_lat)**2 + (a.longitude - ville_lon)**2)
            print(f"{len(liste_activites)} activites trouvees pres de {ville}")
            return liste_activites
            
        except Exception as e:
            print(f"Erreur activites : {e}")
            return []

    def exporter_activites_csv(self, destination, activites):
        nom_fichier = f"activites_{destination.lower()}.csv"
        try:
            with open(nom_fichier, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(['Nom', 'Type', 'Adresse', 'Latitude', 'Longitude', 'Prix'])
                for activite in activites:
                    writer.writerow(activite.to_csv_row())
            print(f"CSV Activites genere : {nom_fichier}")
        except Exception as e:
            print(f"Erreur CSV Activites : {e}")

    # --- RESTAURANTS ---
    def collecter_restaurants(self, ville, terme, nuits):
        url = f"https://www.yelp.fr/search?find_desc={terme}&find_loc={ville}"
        liste_restaurants = []
        try:
            res = requests.get(url, headers=self.headers, timeout=5)
            soup = BeautifulSoup(res.text, "html.parser")
            for h in soup.find_all("h3"):
                texte = h.get_text(strip=True)
                if "." in texte:
                    nom = texte.split(".", 1)[-1]
                    if "Yelp" not in nom and "Se connecter" not in nom:
                        liste_restaurants.append(Restaurant(nom))
                if len(liste_restaurants) >= max(10, nuits * 2):
                    break
            return liste_restaurants
        except:
            return []

    def exporter_restaurants_csv(self, destination, restaurants):
        nom_fichier = f"restaurants_{destination.lower()}.csv"
        try:
            with open(nom_fichier, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(['Nom_Restaurant', 'Ville'])
                for resto in restaurants:
                    writer.writerow([resto.nom, destination])
            print(f"CSV Restaurants genere : {nom_fichier}")
        except Exception as e:
            print(f"Erreur CSV Restaurants : {e}")

    # --- HOTELS ---
    def collecter_hotels(self, ville):
        liste_hotels = []
        try:
            params = {
                "where": f"commune='{ville.upper()}'",
                "limit": 50
            }
            response = requests.get(URL_HOTELS_API, params=params, timeout=5).json()
            hotels = response.get("results", [])
            
            if not hotels:
                print(f"Aucun hotel trouve a {ville}.")
                return []
            
            hotels_possibles = random.sample(hotels, min(10, len(hotels)))
            
            for i, h in enumerate(hotels_possibles, 1):
                nom = h.get("nom_commercial", h.get("nom", f"Hôtel {i}"))
                etoiles = random.randint(1, 5)
                clé_etoiles = f"{etoiles} étoile{'s' if etoiles > 1 else ''}"
                prix = TARIFS_HOTELS.get(clé_etoiles, 85)
                liste_hotels.append(Hotel(nom, etoiles, prix, ville))
                
            return liste_hotels
        except Exception as e:
            print(f"Erreur : {e}")
            return []

    def collecter_hotels_carte(self, ville):
        try:
            params = {
                "where": f"commune='{ville.upper()}'",
                "limit": 10
            }
            response = requests.get(URL_HOTELS_API, params=params, timeout=5).json()
            return response.get("results", [])
        except:
            return []

    def exporter_hotels_csv(self, destination, hotels):
        nom_fichier = f"hotels_{destination.lower()}.csv"
        try:
            with open(nom_fichier, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(['Nom', 'Etoiles', 'Prix_Nuit', 'Ville'])
                for h in hotels:
                    writer.writerow([h.nom, h.etoiles, h.prix_nuit, h.ville])
            print(f"CSV Hotels genere : {nom_fichier}")
        except Exception as e:
            print(f"Erreur CSV Hotels : {e}")

class CartesVoyage:
    def __init__(self, destination, latitude, longitude):
        self.destination = destination
        self.latitude = latitude
        self.longitude = longitude
        self.carte = folium.Map(
            location=[latitude, longitude],
            zoom_start=13,
            tiles="OpenStreetMap"
        )



    def ajouter_activites(self, activites):
        """Ajoute les activités avec la légende de couleur dans la description"""
        # Dictionnaire des couleurs (On garde les mêmes couleurs que tu as déjà)
        couleurs_noms = {
            "Cinéma": ("red", "Rouge"),
            "Musée": ("purple", "Violet"),
            "Monument": ("darkred", "Rouge foncé"),
            "Monument historique": ("darkred", "Rouge foncé"),
            "Théâtre": ("orange", "Orange"),
            "Parc et jardin": ("green", "Vert"),
            "Opéra": ("darkpurple", "Violet foncé"),
            "Scène": ("cadetblue", "Bleu gris"),
            "Centre d'art": ("lightred", "Rouge clair"),
            "Centre culturel": ("blue", "Bleu"),
            "Lieu de mémoire": ("black", "Noir"),
            "Lieu archéologique": ("beige", "Beige")
        }

        for activite in activites:
            # On récupère le code couleur pour Folium et le nom de la couleur pour l'utilisateur
            code_couleur, nom_couleur = couleurs_noms.get(activite.type_activite, ("gray", "Gris"))
            
            # On construit la description avec la légende
            description = (
                f"<b>{activite.nom}</b><br>"
                f" <b>Type :</b> {activite.type_activite}<br>"
                f" <b>Prix :</b> {activite.prix}€<br>"
                f" <b>Couleur :</b> {nom_couleur}<br>"
                f" <b>Adresse :</b> {activite.adresse}"
            )
            
            folium.Marker(
                location=[activite.latitude, activite.longitude],
                popup=folium.Popup(description, max_width=300),
                icon=folium.Icon(color=code_couleur, icon="info-sign"),
                tooltip=f"{activite.nom} ({activite.type_activite})"
            ).add_to(self.carte)

    def ajouter_hotels(self, hotels):
        """Ajoute les hôtels sur la carte"""
        for h in hotels:
            try:
                geo = h.get("coordonnees_geo", {})
                lat = geo.get("lat")
                lon = geo.get("lon")
                nom = h.get("nom_commercial", h.get("nom", "Hôtel"))
                if lat and lon:
                    folium.Marker(
                        location=[lat, lon],
                        popup=nom,
                        icon=folium.Icon(color="blue", icon="bed", prefix="fa")
                    ).add_to(self.carte)
            except:
                pass

    def sauvegarder(self, nom_fichier="carte_voyage.html"):
        """Sauvegarde la carte en fichier HTML"""
        self.carte.save(nom_fichier)
        print(f"Carte sauvegardee : {nom_fichier}")

# --- ETAPE 4 : Profil ---

class Voyageur:
    def __init__(self, depart, destination, nuits, personnes, budget_max):
        self.depart = depart
        self.destination = destination
        self.nuits = nuits
        self.personnes = personnes
        self.budget_max = budget_max

        self.transport = {}
        self.hotel = {}
        self.cout_transport = 0
        self.cout_hotel = 0

    def definir_transport(self, mode, distance, temps):
        self.transport = {
            "mode": mode,
            "distance": distance,
            "temps": temps
        }

        if mode == "car":
            self.cout_transport = distance * 0.20
        elif mode == "bike":
            self.cout_transport = distance * 0.05
        else:
            self.cout_transport = 0

    def definir_hotel(self, nom, cout):
        self.hotel = {"nom": nom}
        self.cout_hotel = cout

    def resume_transport(self):
        heures = self.transport["temps"] // 60
        minutes = self.transport["temps"] % 60
        return (
            f"Distance : {self.transport['distance']:.1f} km | "
            f"Temps : {heures}h{minutes} | "
            f"Transport : {self.cout_transport:.2f} €"
        )

    def calculer_budget(self, cout_resto, cout_activites=0):
        return self.cout_transport + self.cout_hotel + cout_resto + cout_activites

# --- ETAPE 5 : L'application globale ---

class Voyage:
    def __init__(self, depart, destination, nuits, personnes, budget_max):
        self.depart = depart
        self.destination = destination
        self.nuits = nuits
        self.personnes = personnes
        self.budget_max = budget_max
        
        self.voyageur = Voyageur(depart, destination, nuits, personnes, budget_max)
        self.collecte = Collecte(GRAPHHOPPER_KEY)
        self.hotels = Hotels()
        self.activites = Activites()
        self.restaurants = Restaurants()
        self.prix_repas = 0

    def planifier_transport(self):
        print("\n Transport : 1=Voiture | 2=Vélo | 3=Marche")
        choix = input("Votre choix : ")
        modes = {"1": "car", "2": "bike", "3": "foot"}
        mode = modes.get(choix, "car")
        
        distance, temps = self.collecte.calculer_transport(self.depart, self.destination, mode)
        self.voyageur.definir_transport(mode, distance, temps)

    def selectionner_hotels(self):
        print("\n--- RECHERCHE D'HOTEL ---")
        
        hotels_trouves = self.collecte.collecter_hotels(self.destination)
        self.hotels.liste_hotels = hotels_trouves
        
        if not hotels_trouves:
            return
            
        print(f"{len(hotels_trouves)} hotels disponibles a {self.destination} :\n")
        for i, h in enumerate(hotels_trouves, 1):
            stars = "*" * h.etoiles
            print(f"{i}. {h.nom} {stars} ({h.prix_nuit}€/nuit)")
        
        # Sélection automatique d'un hôtel
        hotel_sel = random.choice(hotels_trouves)
        self.definir_hotel_choisi(hotel_sel)
        print(f"Hotel selectionne : {hotel_sel.nom} ({hotel_sel.etoiles}* - {hotel_sel.prix_nuit}€/nuit)")

    def definir_hotel_choisi(self, hotel_sel):
        """Applique le choix de l'hôtel au voyageur"""
        self.hotel_choisi = hotel_sel
        hotel_nom = hotel_sel.nom
        prix_hotel = hotel_sel.prix_nuit
        chambres = (self.personnes + 1) // 2
        cout_hotel = prix_hotel * chambres * self.nuits
        self.voyageur.definir_hotel(hotel_nom, cout_hotel)

    def changer_hotel(self):
        """Permet à l'utilisateur de changer l'hôtel sélectionné"""
        if not self.hotels.liste_hotels:
            print("Aucun hotel disponible.")
            return False

        print("\n--- CHANGER D'HOTEL ---")
        for i, h in enumerate(self.hotels.liste_hotels, 1):
            stars = "*" * h.etoiles
            print(f"{i}. {h.nom} {stars} ({h.prix_nuit}€/nuit)")
        
        choix = input("\nNumero du nouvel hotel (ou Entree pour annuler) : ")
        if choix.isdigit() and 1 <= int(choix) <= len(self.hotels.liste_hotels):
            hotel_sel = self.hotels.liste_hotels[int(choix) - 1]
            self.definir_hotel_choisi(hotel_sel)
            print(f"Nouvel hotel choisi : {hotel_sel.nom}")
            return True
        return False

    def selectionner_restaurants(self):
        print(f"\n--- RESTAURANTS DISPONIBLES A {self.destination.upper()} ---")
        
        # On utilise la catégorie "Tous types" par défaut (index "0")
        label, terme, self.prix_repas = CAT_RESTOS["0"]
        
        # On lance la recherche directement
        restos = self.collecte.collecter_restaurants(self.destination, terme, self.nuits)
        self.restaurants.liste_restaurants = restos
        
        if restos:
            # On affiche les 10 premiers pour confirmer que ça marche
            for i, resto in enumerate(restos[:10], 1):
                print(f"{i}. {resto.nom}")
            print(f"\n{len(restos)} restaurants trouves. Ils seront repartis dans votre programme.")
        else:
            print("Aucun restaurant trouve sur Yelp, utilisation de noms par defaut.")
            # Optionnel : ajouter des noms par défaut ici si la liste est vide
            self.restaurants.liste_restaurants = [Restaurant("Bistrot Local"), Restaurant("La Bonne Table"), Restaurant("Le Petit Snack")]

    def recuperer_activites(self):
        self.activites.liste_activites = self.collecte.collecter_activites(self.destination)
        return self.activites.liste_activites

    def generer_programme(self, activites=None):
        print("\n" + "=" * 50)
        print(f"SEJOUR A {self.destination.upper()}")
        print("=" * 50)
        print(self.voyageur.resume_transport())
        
        meteo = self.collecte.collecter_meteo(self.destination)
        
        # Gestion des restaurants
        restos = self.restaurants.liste_restaurants.copy() if self.restaurants.liste_restaurants else []
        random.shuffle(restos)
        
        # Gestion des activités
        pool_activites = activites.copy() if activites else []
        random.shuffle(pool_activites)
        
        cout_activites = 0
        for jour in range(1, self.nuits + 1):
            print(f"\n JOUR {jour}")
            print(" Meteo :", meteo[jour - 1] if jour <= len(meteo) else "Non disponible")
            
            # Activité Journée
            act_jour = pool_activites.pop(0) if pool_activites else None
            if act_jour:
                cout_activites += act_jour.prix * self.personnes
                print(f" Journee : {act_jour.nom} ({act_jour.type_activite}) - {act_jour.prix}€/pers")
            else:
                print(" Journee : Balade et decouverte (Gratuit)")

            print(" Midi :", restos.pop(0).nom if restos else "Restaurant local")

            # Activité Soirée
            act_soir = pool_activites.pop(0) if pool_activites else None
            if act_soir:
                cout_activites += act_soir.prix * self.personnes
                print(f" Soiree : {act_soir.nom} ({act_soir.type_activite}) - {act_soir.prix}€/pers")
            else:
                print(" Soiree : Detente (Gratuit)")

            print(" Diner :", restos.pop(0).nom if restos else "Restaurant local")
            print(" Nuit :", self.voyageur.hotel.get("nom", "Hotel non defini"))
        
        # -------- BUDGET --------
        cout_resto = self.prix_repas * 2 * self.nuits * self.personnes
        total = self.voyageur.calculer_budget(cout_resto, cout_activites)
        
        print("\n" + "=" * 50)
        print(f" BUDGET TOTAL : {round(total, 2)} €")
        if total <= self.budget_max:
            print(f" DANS LE BUDGET ({self.budget_max}€)")
        else:
            print(f" HORS BUDGET (+{round(total - self.budget_max, 2)}€)")
        print("=" * 50)

    def exporter_hotels_csv(self):
        self.collecte.exporter_hotels_csv(self.destination, self.hotels.liste_hotels)

    def exporter_activites_csv(self):
        self.collecte.exporter_activites_csv(self.destination, self.activites.liste_activites)

    def exporter_restos_csv(self):
        self.collecte.exporter_restaurants_csv(self.destination, self.restaurants.liste_restaurants)

    def comparer_ville(self):
        print("\n--- COMPARATEUR DE DESTINATION ---")
        autre_ville = input("Avec quelle ville voulez-vous comparer ? ")

        # Récupération mode transport actuel
        mode = self.voyageur.transport.get("mode", "car")
        
        # Calcul transport autre ville
        dist, temps = self.collecte.calculer_transport(self.depart, autre_ville, mode)
        cout_transport = 0
        if mode == "car": cout_transport = dist * 0.20
        elif mode == "bike": cout_transport = dist * 0.05

        # Calcul hôtel (Même standing que l'hôtel choisi)
        if self.hotel_choisi:
            etoiles = self.hotel_choisi.etoiles
            clé_etoiles = f"{etoiles} étoile{'s' if etoiles > 1 else ''}"
            prix_nuit = TARIFS_HOTELS.get(clé_etoiles, 85)
            print(f"\nComparaison avec un hotel {etoiles} etoiles ({prix_nuit}€/nuit)")
        else:
            prix_nuit = 85 # Prix par défaut
            
        chambres = (self.personnes + 1) // 2
        cout_hotel = prix_nuit * chambres * self.nuits
        
        # Restauration (base identique)
        cout_resto = self.prix_repas * 2 * self.nuits * self.personnes
        
        # Totaux (Hors activités spécifiques)
        total_actuel = self.voyageur.cout_transport + self.voyageur.cout_hotel + cout_resto
        total_autre = cout_transport + cout_hotel + cout_resto
        
        print(f"\nCOMPARATIF (Base : Transport + Hotel + Repas)")
        print(f"{'':<20} | {self.destination.upper():<15} | {autre_ville.upper():<15}")
        print("-" * 60)
        print(f"{'Transport':<20} | {self.voyageur.cout_transport:>14.2f}€ | {cout_transport:>14.2f}€")
        print(f"{'Hebergement':<20} | {self.voyageur.cout_hotel:>14.2f}€ | {cout_hotel:>14.2f}€")
        print("-" * 60)
        print(f"{'TOTAL ESTIME':<20} | {total_actuel:>14.2f}€ | {total_autre:>14.2f}€")
        
        diff = total_autre - total_actuel
        if diff > 0:
            print(f"\n{autre_ville} est plus cher de {diff:.2f}€")
        else:
            print(f"\n{autre_ville} est moins cher de {abs(diff):.2f}€")
