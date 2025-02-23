import os
import pandas as pd  # Pour travailler avec des données tabulaires
import streamlit as st  # Pour créer des applications web
import geopandas as gpd  # Pour travailler avec des données géospatiales
from opencage.geocoder import OpenCageGeocode  # Pour convertir une adresse en coordonnées
from shapely.geometry import Point  # Pour travailler avec la géométrie des points
import folium  # Pour créer des cartes interactives
from folium.plugins import MeasureControl  # Pour ajouter un outil de mesure à la carte
from streamlit_folium import st_folium  # Pour afficher des cartes Folium dans l'application Streamlit
import pandas as pd  # Pour travailler avec des données tabulaires

#-------------------------------------------------------------------------------------------------------------

# Titre de l'application
st.title('Les stations de vélos à Paris')

# Création de la carte centrée sur Paris
m = folium.Map(location=[48.8566, 2.34], zoom_start=12, tiles='CartoDB dark_matter')

# Style CSS personnalisé pour styliser les formulaires dans l'application Streamlit
st.markdown("""
    <style>
    .stForm {
        border: 2px solid red;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

#-------------------------------------------------------------------------------------------------------------

# Chemins vers les fichiers de données
base_dir = os.path.join(os.getcwd(), "data")

chemin_fichier_station = os.path.join(base_dir, "paris_stations_velo.geojson")
chemin_fichier_quartier = os.path.join(base_dir, "paris_quartiers.geojson")
chemin_fichier_rivière = os.path.join(base_dir, "paris_land_use.shp")

# Fonctions de chargement des données : station, quartier, riviere
def charger_donnees_station(chemin):
    gdf = gpd.read_file(chemin)
    return gdf

def charger_donnees_quartier(chemin):
    gdf = gpd.read_file(chemin)
    return gdf

def charger_donnees_rivière(chemin):
    return gpd.read_file(chemin)

donnees_station = charger_donnees_station(chemin_fichier_station)
donnees_quartier = charger_donnees_quartier(chemin_fichier_quartier)
donnees_rivière = charger_donnees_rivière(chemin_fichier_rivière)

plans_eau = donnees_rivière[donnees_rivière['class'] == 'Water bodies'] # Filtrer les plans d'eau



#-------------------------------------------------------------------------------------------------------------
# États pour stocker les résultats de recherche
if 'stations_dans_rayon' not in st.session_state:
    st.session_state['stations_dans_rayon'] = gpd.GeoDataFrame()
if 'stations_dans_quartier' not in st.session_state:
    st.session_state['stations_dans_quartier'] = gpd.GeoDataFrame()
if 'stations_pres_rivière' not in st.session_state:
    st.session_state['stations_pres_rivière'] = gpd.GeoDataFrame()
if 'rayon' not in st.session_state:
    st.session_state['rayon'] = None

#-------------------------------------------------------------------------------------------------------------



#-----------------------Trouver toutes les stations de vélos dans un rayon d'adress---------------------------

# Fonction de géocodage
def geocoder_adresse(adresse):
    cle = '1f548dad679d461c872cc682cbd1fc7b'     # Clé API pour accéder au service OpenCage Geocode opencagedata.com
    geocodeur = OpenCageGeocode(cle)
    resultats = geocodeur.geocode(
        adresse,            # Adresse à géocoder
        no_annotations=1,   # Désactiver les annotations dans les résultats
        language='fr',      # Définir la langue des résultats en français
        abbrv=1,            # Abréger les résultats (par exemple, abréviation des noms de pays)
        limit=1,            # Limiter le nombre de résultats retournés à un seul (le plus pertinent)
        countrycode='fr'    # Limiter la recherche aux résultats en France
    )

    # Vérification des résultats
    if resultats and len(resultats):
        return (resultats[0]['geometry']['lat'], resultats[0]['geometry']['lng'])
    else:
        return None
    
# Formulaire de saisie d'adresse et de rayon
with st.form("formulaire_adresse"):
    adresse = st.text_input("Entrez l'adresse")
    rayon = st.selectbox("Rayon (en mètres)", [500, 1000, 1500, 2000])
    bouton_soumettre_adresse = st.form_submit_button(label='Trouver des stations par adresse')

# Fonction pour trouver les stations dans un rayon
def trouver_stations_dans_rayon(stations, point_central, rayon):
    centre = Point(point_central[1], point_central[0])  # Créer un objet Point pour le point central en utilisant les coordonnées (longitude, latitude)
    stations = stations.to_crs(epsg=3395)  # Projeter dans un système de coordonnées en mètres
    centre = gpd.GeoSeries([centre], crs="EPSG:4326").to_crs(epsg=3395).iloc[0]  # Projeter le point central
    stations['distance'] = stations.geometry.distance(centre)    # Calculer la distance de chaque station au point central
    stations_dans_rayon = stations[stations['distance'] <= rayon]     # Filtrer les stations qui se trouvent à une distance inférieure ou égale au rayon donné
    return stations_dans_rayon.to_crs(epsg=4326)  # Convertir à nouveau en lat/lon pour folium

# Traitement de la recherche par adresse
if bouton_soumettre_adresse:
    emplacement = geocoder_adresse(adresse)
    if emplacement:
        st.write(f"Coordonnées : {emplacement}")
        stations_dans_rayon = trouver_stations_dans_rayon(donnees_station, emplacement, rayon)
        
        st.write(f"{len(stations_dans_rayon)} stations trouvées dans un rayon de {rayon} mètres.")
        
        if not stations_dans_rayon.empty:
            st.session_state['stations_dans_rayon'] = stations_dans_rayon
            st.session_state['stations_dans_quartier'] = gpd.GeoDataFrame()  # Effacer les résultats de recherche par quartier
            st.session_state['stations_pres_rivière'] = gpd.GeoDataFrame()  # Effacer les résultats de recherche près de la rivière
        else:
            st.error("Aucune station trouvée dans le rayon spécifié.")
    else:
        st.error("Adresse non trouvée. Veuillez réessayer.")

#-------------------------------------------------------------------------------------------------------------



#-------------------------------Trouver les stations dans un quartier-----------------------------------------

# Sélection de quartier et liste triée
with st.form("formulaire_quartier"):
    liste_quartiers = [""] + sorted(donnees_quartier['district_name'].tolist())
    quartier_selectionné = st.selectbox("Sélectionner un quartier", liste_quartiers)
    bouton_soumettre_quartier = st.form_submit_button(label='Trouver des stations dans le quartier')

# Fonction pour trouver les stations dans un quartier
def trouver_stations_dans_quartier(stations, quartier, quartiers_gdf):
    polygone_quartier = quartiers_gdf[quartiers_gdf['district_name'] == quartier].geometry.iloc[0]  # Récupérer le polygone correspondant au quartier spécifié
    stations_dans_quartier = stations[stations.geometry.within(polygone_quartier)]     # Filtrer les stations qui se trouvent à l'intérieur du polygone du quartier
    return stations_dans_quartier

# Traitement de la recherche par quartier
if bouton_soumettre_quartier:
    if quartier_selectionné and quartier_selectionné != "":
        stations_dans_quartier = trouver_stations_dans_quartier(donnees_station, quartier_selectionné, donnees_quartier)
        
        st.write(f"{len(stations_dans_quartier)} stations trouvées dans le quartier {quartier_selectionné}.")
        
        if not stations_dans_quartier.empty:
            st.session_state['stations_dans_quartier'] = stations_dans_quartier
            st.session_state['stations_dans_rayon'] = gpd.GeoDataFrame()  # Effacer les résultats de recherche par rayon
            st.session_state['stations_pres_rivière'] = gpd.GeoDataFrame()  # Effacer les résultats de recherche près de la rivière
        else:
            st.error("Aucune station trouvée dans le quartier spécifié.")

# Ce code est conçu pour que seuls les résultats d'une seule requête soient affichés sur la carte.
# Si vous recherchez des stations dans un quartier, les résultats de la recherche par rayon ou à proximité de la rivière sont effacés,
# afin d'éviter tout mélange de données et d'afficher uniquement les résultats actuels de la dernière requête sur la carte.

#----------------------------------------------------------------------------------------------------------------------



#---------------------------------Trouver les stations près  de rivière------------------------------------------------

# Formulaire pour sélectionner le rayon pour la recherche des stations près de la rivière
with st.form("formulaire_rayon"):
    st.write("Sélectionnez le rayon pour la recherche des stations près de la rivière :")
    options = {
        "500 m": 5,
        "1000 m": 10
    }
    display_options = list(options.keys())
    selected_label = st.selectbox("Rayon (m)", display_options)
    option_rayon = options[selected_label]
    bouton_soumettre = st.form_submit_button(label='Trouver des stations')


# Fonction pour trouver les stations près de rivière
def trouver_stations_pres_segments_rivière(stations, segments_rivière, distance):
    resultat = []
    for _, segment in segments_rivière.iterrows():     # Boucle à travers chaque segment de rivière
        buffer = segment.geometry.buffer(distance / 1000)  # Buffer en mètres
        stations_filtrees = stations[stations.geometry.within(buffer)]  # Filtrer les stations qui se trouvent à l'intérieur du buffer
        resultat.append(stations_filtrees)   # Ajouter les stations filtrées à la liste des résultats
    if resultat:
        toutes_stations = gpd.GeoDataFrame(pd.concat(resultat, ignore_index=True))
        return toutes_stations.drop_duplicates(subset='geometry')
    else:
        return gpd.GeoDataFrame(columns=stations.columns)
    
if bouton_soumettre:
    st.session_state['rayon'] = option_rayon
    st.session_state['stations_pres_rivière'] = trouver_stations_pres_segments_rivière(donnees_station, plans_eau, st.session_state['rayon'])
    st.session_state['stations_dans_rayon'] = gpd.GeoDataFrame()  # Effacer les résultats de recherche par rayon
    st.session_state['stations_dans_quartier'] = gpd.GeoDataFrame()  # Effacer les résultats de recherche par quartier


# Affichage des stations trouvées près de la rivière
stations_pres_rivière = st.session_state['stations_pres_rivière']
rayon = st.session_state['rayon']
if rayon is not None:
    st.write(f"{len(stations_pres_rivière)} stations trouvées dans un rayon de {rayon} mètres de la rivière.")

#-------------------------------------------------------------------------------------------------------------




#-------------------------------------------------------------------------------------------------------------

# Ajout des stations de recherche par rayon sur la carte
if not st.session_state['stations_dans_rayon'].empty:
    for _, row in st.session_state['stations_dans_rayon'].iterrows():
        icon_path = os.path.join(base_dir, "velib.png")
        icon = folium.CustomIcon(icon_path, icon_size=(20, 20))
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            tooltip=row['name'],
            popup=row['name'],
            icon=icon
        ).add_to(m)


# Ajout des stations de recherche par quartier sur la carte
if not st.session_state['stations_dans_quartier'].empty:
    for _, row in st.session_state['stations_dans_quartier'].iterrows():
        icon_path = os.path.join(base_dir, "velib.png")
        icon = folium.CustomIcon(icon_path, icon_size=(20, 20))
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            tooltip=row['name'],
            popup=row['name'],
            icon=icon
        ).add_to(m)

# Ajout des stations de recherche près de la rivière sur la carte
if not st.session_state['stations_pres_rivière'].empty:
    for _, row in st.session_state['stations_pres_rivière'].iterrows():
        icon_path = os.path.join(base_dir, "velib.png")
        icon = folium.CustomIcon(icon_path, icon_size=(20, 20))
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            tooltip=row['name'],
            popup=row['name'],
            icon=icon
        ).add_to(m)

st_folium(m, width=800, height=500)
