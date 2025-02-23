<h1 align="center"> Application interactive pour la visualisation <br>de la répartition des stations Vélib à Paris</h1>

Ce projet utilise **Python**, **Streamlit** et **GeoPandas** pour analyser et visualiser les stations Vélib à Paris à partir de données géospatiales. Il permet d'explorer les stations disponibles en fonction de leur proximité avec une adresse donnée, un quartier ou une rivière. 

Grâce à l'intégration de **Folium** pour la cartographie interactive et de l'API OpenCage pour le géocodage, l'application propose une approche automatisée et interactive pour l'exploration des données Vélib.

*Mots clés : Webmapping, Python, Streamlit, Folium, GeoPandas, OpenCage API*


Points clés :
- Automatisation du traitement des données : Utilisation de **GeoPandas** et **Streamlit** pour charger, filtrer et analyser les fichiers GeoJSON et SHP contenant les stations Vélib et les quartiers de Paris.  
- Analyse géospatiale avancée : Possibilité d'afficher les stations dans un **rayon défini autour d'une adresse**, dans un **quartier spécifique** ou à proximité d’une **rivière** en utilisant des buffers géométriques.  
- Résultats visuels et interactifs : Création d'une **carte interactive Folium**, affichant les stations en fonction des critères de sélection, avec des marqueurs personnalisés et des filtres dynamiques.

Vous pouvez exécuter le script sur GitHub via Codespaces :
- Pour charger les bibliothèques : **pip install -r requirements.txt**
- Pour lancer le code : **python3 -m streamlit run Velib.py**

Exemple de recherche de stations pour un quartier spécifique :
<div align="center">
    <img src="https://github.com/DariaPodlovchenko/Velib-Paris/raw/main/ex.jpg" width="600">
</div>

