import streamlit as st
import pandas as pd
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

st.image("assets/Donnees_sante6.jpg", caption="Analyse des séjours", use_column_width=True)

st.title("Détection des séjours longs par tranche d’âge")

if "df_dates" not in st.session_state:
    st.warning("Les données ne sont pas encore prêtes. Merci de revenir après l'import.")
    st.stop()

df_dates = st.session_state["df_dates"]



# Seuil par tranche : moyenne + 50%
seuils = df_dates.groupby("tranche_age")["duree_sejour_semaines"].mean() * 1.5

df_dates["sejour_long"] = df_dates.apply(
    lambda row: row["duree_sejour_semaines"] > seuils.get(row["tranche_age"], float('inf')), axis=1
)

tranches = df_dates["tranche_age"].dropna().unique().tolist()
tranche_choisie = st.selectbox("Choisissez une tranche d’âge :", sorted(tranches))

df_filtré = df_dates[(df_dates["tranche_age"] == tranche_choisie) & (df_dates["sejour_long"] == True)]

st.subheader(f"Patients avec séjours longs dans la tranche {tranche_choisie}")
st.dataframe(df_filtré[[
    "identifiant", "date_entree", "date_sortie", "duree_sejour_semaines", "actes_csarr"
]], use_container_width=True)

# Boutons d'export
st.markdown("### Exporter les résultats affichés")
telecharger_dataframe(
    df_filtré[[
        "identifiant", "date_entree", "date_sortie", "duree_sejour_semaines", "actes_csarr"
    ]],
    nom_fichier_base=f"sejours_longs_{tranche_choisie.replace(' ', '_')}"
)
