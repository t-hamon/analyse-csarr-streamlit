import streamlit as st

st.set_page_config(page_title="Accueil", page_icon="🏠")

st.image("assets/Donnees_sante.jpg", caption="Illustration de l'analyse CSARR", use_column_width=True)

st.title("Analyse des Séjours RHS - CSARR")

st.markdown("""
Bienvenue dans l'outil d'analyse des fichiers RHS contenant des actes **CSARR**.

Cette application vous permet :

- D'importer un fichier texte brut (.TXT) issu d'un RHS.
- D'analyser la distribution des **actes CSARR** par jour, par patient, par mois, etc.
- De visualiser la **durée moyenne de séjour par tranche d'âge**, avec des courbes interactives.
- D'identifier les **patients ayant un seul acte**, les profils atypiques, etc.

---


### Navigation

Utilisez le **menu latéral** (en haut à gauche) pour accéder aux différentes pages d'analyse :


- **Analyse CSARR : Analysez la distribution des actes**
- **Analyse des séjours par tranche d’âge**  
- **Regroupement par pathologies (diagnostics)**  
- **Histogramme des durées selon l’acte principal**  
- **Détection des séjours longs par tranche d’âge**

---

N'oubliez pas de préparer vos fichiers au bon format pour profiter pleinement de toutes les analyses !
""")

uploaded_file = st.file_uploader("Importez un fichier RHS")
if uploaded_file:
    content = uploaded_file.read().decode("utf-8")  # lire une seule fois
    st.session_state["rhs_file_text"] = content     # stocker sous forme texte

    st.success("Fichier chargé avec succès ! Rendez-vous dans une page d'analyse.")

st.info("💡 Astuce : vous pouvez exporter chaque tableau au format Excel/CSV dans les pages d’analyse.")