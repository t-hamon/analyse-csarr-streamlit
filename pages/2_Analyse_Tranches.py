import streamlit as st
import pandas as pd
import plotly.express as px
import re
from datetime import datetime
import io

def telecharger_dataframe(df, nom_fichier_base="export"):
    # Export en CSV
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="Télécharger en CSV",
        data=csv_buffer.getvalue(),
        file_name=f"{nom_fichier_base}.csv",
        mime="text/csv"
    )

    # Export en Excel
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Feuille1")
    st.download_button(
        label="Télécharger en Excel",
        data=excel_buffer.getvalue(),
        file_name=f"{nom_fichier_base}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.image("assets/Donnees_sante3.jpg", caption="Analyse des séjours", use_column_width=True)


st.title("Analyse des séjours par tranche d’âge")

# Vérification de l'import du fichier
if "rhs_file_text" not in st.session_state:
    st.warning("Veuillez d'abord importer un fichier RHS dans la page d’accueil.")
    st.stop()



# Traitement du fichier
with st.spinner("Traitement des données en cours..."):
    lignes = st.session_state["rhs_file_text"].splitlines()

    def extraire_dates_depuis_ligne(ligne):
        # Cherche un bloc de 24 chiffres consécutifs correspondant aux 3 dates
        match = re.search(r'(\d{8})(\d{8}| {8})(\d{8})', ligne)
        if match:
            entree = match.group(1)
            sortie = match.group(2).strip() or None  # Peut être vide si hospitalisation en cours
            naissance = match.group(3)
            return entree, sortie, naissance
        return None, None, None


    # donnees = []
    # for ligne in lignes:
    #     dentree, dsortie, dnaissance = extraire_dates_depuis_ligne(ligne)
    #     if dentree and dsortie and dnaissance:
    #         donnees.append([dentree, dsortie, dnaissance])

    # df_dates = pd.DataFrame(donnees, columns=["date_entree", "date_sortie", "date_naissance"])

    def extraire_actes_csarr(ligne):
        return " - ".join(re.findall(r'[A-Z]{3}(?:\+\d{3}|\d{3})', ligne))

    donnees = []
    for ligne in lignes:
        dentree, dsortie, dnaissance = extraire_dates_depuis_ligne(ligne)
        actes = extraire_actes_csarr(ligne)
        identifiant_match = re.search(r'\b(\d{8})\b', ligne)
        identifiant = identifiant_match.group(1) if identifiant_match else None
        donnees.append([dentree, dsortie, dnaissance, actes, identifiant])

    df_dates = pd.DataFrame(donnees, columns=[
        "date_entree", "date_sortie", "date_naissance", "actes_csarr", "identifiant"
    ])


    # Conversion des dates
    df_dates["date_entree"] = pd.to_datetime(df_dates["date_entree"], format="%d%m%Y", errors="coerce")
    df_dates["date_sortie"] = pd.to_datetime(df_dates["date_sortie"], format="%d%m%Y", errors="coerce")
    df_dates["date_naissance"] = pd.to_datetime(df_dates["date_naissance"], format="%d%m%Y", errors="coerce")

    df_dates["date_entree"] = pd.to_datetime(df_dates["date_entree"], format="%d%m%Y", errors="coerce")
    df_dates["date_sortie"] = pd.to_datetime(df_dates["date_sortie"], format="%d%m%Y", errors="coerce")
    df_dates["date_naissance"] = pd.to_datetime(df_dates["date_naissance"], format="%d%m%Y", errors="coerce")

    df_dates["age_entree"] = df_dates.apply(
        lambda row: (row["date_entree"] - row["date_naissance"]).days // 365
        if pd.notnull(row["date_entree"]) and pd.notnull(row["date_naissance"]) else None, axis=1)

    df_dates["duree_sejour_semaines"] = df_dates.apply(
        lambda row: (row["date_sortie"] - row["date_entree"]).days / 7
        if pd.notnull(row["date_sortie"]) and pd.notnull(row["date_entree"]) else None, axis=1)
    
    # Supprimer les heures inutiles dans les dates
    df_dates["date_entree_affichee"] = df_dates["date_entree"].dt.strftime("%Y-%m-%d")
    df_dates["date_naissance_affichee"] = df_dates["date_naissance"].dt.strftime("%Y-%m-%d")
    df_dates["date_sortie_affichee"] = df_dates["date_sortie"].apply(
        lambda x: "Hospitalisation en cours" if pd.isna(x) else x.strftime("%Y-%m-%d")
    )

    def classer_age(age):
        if age is None or pd.isna(age):
            return None
        elif age < 13:
            return "Moins de 13 ans"
        elif age <= 17:
            return "13-17 ans"
        elif age <= 29:
            return "18-29 ans"
        elif age <= 39:
            return "30-39 ans"
        elif age <= 49:
            return "40-49 ans"
        elif age <= 59:
            return "50-59 ans"
        elif age <= 69:
            return "60-69 ans"
        elif age <= 79:
            return "70-79 ans"
        elif age <= 84:
            return "80-84 ans"
        elif age <= 89:
            return "85-89 ans"
        elif age <= 94:
            return "90-94 ans"
        else:
            return "95 ans et plus"

    df_dates["tranche_age"] = df_dates["age_entree"].apply(classer_age)

    ordre_tranches = [
        "Moins de 13 ans", "13-17 ans", "18-29 ans", "30-39 ans", "40-49 ans",
        "50-59 ans", "60-69 ans", "70-79 ans", "80-84 ans", "85-89 ans",
        "90-94 ans", "95 ans et plus"
    ]

    agg_df = df_dates[df_dates["tranche_age"].notnull()].groupby("tranche_age", sort=False).agg(
        nb_sejours=("duree_sejour_semaines", "count"),
        duree_moyenne=("duree_sejour_semaines", lambda x: round(x.mean(), 2))
    ).reset_index()

    df_final = pd.DataFrame({"tranche_age": ordre_tranches})
    df_final = df_final.merge(agg_df, on="tranche_age", how="left")
    df_final["nb_sejours"] = df_final["nb_sejours"].fillna(0).astype(int)
    df_final["duree_moyenne"] = df_final.apply(
        lambda row: 0 if row["nb_sejours"] == 0 else row["duree_moyenne"], axis=1)
    
st.session_state["df_dates"] = df_dates


# Affichage tableau
st.subheader("Tableau synthétique")
st.dataframe(df_final, use_container_width=True)
st.markdown("### Exporter les données")
telecharger_dataframe(df_final, nom_fichier_base="tranches_age_synthese")


# Affichage graphique
st.subheader("Durée moyenne de séjour par tranche d’âge")
fig = px.bar(
    df_final,
    x="tranche_age",
    y="duree_moyenne",
    color="duree_moyenne",
    hover_data=["nb_sejours"],
    labels={"tranche_age": "Tranche d'âge", "duree_moyenne": "Durée moyenne (semaines)"},
    title="Durée moyenne de séjour par tranche d’âge",
)
fig.update_layout(
    xaxis_title="Tranche d'âge",
    yaxis_title="Durée moyenne de séjour (semaines)",
    height=500,
    width=900,
    showlegend=False
)
st.plotly_chart(fig)

# Affichage dynamique par tranche avec un menu déroulant
st.subheader("Afficher les patients par tranche d’âge")


# Choix de la tranche
tranches_disponibles = [t for t in ordre_tranches if t in df_dates["tranche_age"].unique()]
tranche_selectionnee = st.selectbox("Sélectionnez une tranche d'âge :", tranches_disponibles)

# Affichage du tableau filtré
df_tranche = df_dates[df_dates["tranche_age"] == tranche_selectionnee]
df_affichage = df_tranche[[
    "identifiant",
    "date_entree_affichee",
    "date_sortie_affichee",
    "date_naissance_affichee",
    "age_entree",
    "duree_sejour_semaines",
    "actes_csarr"
]].rename(columns={
    "identifiant": "Identifiant patient",
    "date_entree_affichee": "Date d'entrée",
    "date_sortie_affichee": "Date de sortie",
    "date_naissance_affichee": "Date de naissance",
    "age_entree": "Âge à l'entrée",
    "duree_sejour_semaines": "Durée (semaines)",
    "actes_csarr": "Actes CSARR"
})

def surligner_hosp_en_cours(row):
    color = 'background-color: #ffe599' if row["Date de sortie"] == "Hospitalisation en cours" else ''
    return [color] * len(row)

st.write(
    df_affichage.style.apply(surligner_hosp_en_cours, axis=1)
)

# Légende
st.markdown('<div style="margin-top: 10px;"><span style="background-color:#ffe599;padding:3px 8px;border-radius:4px;">&nbsp;</span> : Hospitalisation en cours</div>', unsafe_allow_html=True)

st.markdown("### Exporter la liste des patients de cette tranche")
telecharger_dataframe(df_tranche[[
    "date_entree", "date_sortie_affichee", "date_naissance",
    "age_entree", "duree_sejour_semaines", "actes_csarr", "identifiant"
]], nom_fichier_base=f"patients_tranche_{tranche_selectionnee.replace(' ', '_')}")

# Export global combiné
st.markdown("### Export global de l’analyse des séjours par tranche d’âge")

def telecharger_export_global(dfs: dict, nom_fichier="export_global_tranches_age.xlsx"):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        for nom_feuille, df in dfs.items():
            df.to_excel(writer, index=False, sheet_name=nom_feuille[:31])
    st.download_button(
        label="⬇️ Télécharger toutes les données (Excel)",
        data=buffer.getvalue(),
        file_name=nom_fichier,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Tableaux à exporter
dfs_export = {
    "Synthèse_par_tranche": df_final,
    f"Patients_{tranche_selectionnee.replace(' ', '_')}": df_affichage.reset_index(drop=True)
}
telecharger_export_global(dfs_export)

