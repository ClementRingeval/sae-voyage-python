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

# Types d'activités disponibles
TYPES_ACTIVITES = {
    "1": "Cinéma",
    "2": "Musée",
    "3": "Théâtre",
    "4": "Parc",
    "5": "Monument historique"
}