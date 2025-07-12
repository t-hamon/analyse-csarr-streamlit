import streamlit as st
import pandas as pd
import plotly.express as px
import re
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

st.image("assets/Donnees_sante5.jpg", caption="Analyse des séjours", use_column_width=True)

st.title("Histogramme des durées selon l’acte principal (CSARR)")

if "rhs_file_text" not in st.session_state:
    st.warning("Veuillez d'abord importer un fichier RHS dans la page d’accueil.")
    st.stop()

lignes = st.session_state["rhs_file_text"].splitlines()

def extraire_dates(ligne):
    match = re.search(r'(\d{8})(\d{8}| {8})(\d{8})', ligne)
    if match:
        entree = match.group(1)
        sortie = match.group(2).strip() or None
        return entree, sortie
    return None, None

def extraire_acte_principal(ligne):
    actes = re.findall(r'[A-Z]{3}(?:\+\d{3}|\d{3})', ligne)
    return actes[0] if actes else None

donnees = []
for ligne in lignes:
    entree, sortie = extraire_dates(ligne)
    acte = extraire_acte_principal(ligne)
    if entree and sortie and acte:
        donnees.append([entree, sortie, acte])

df = pd.DataFrame(donnees, columns=["entree", "sortie", "acte"])
df["entree"] = pd.to_datetime(df["entree"], format="%d%m%Y", errors="coerce")
df["sortie"] = pd.to_datetime(df["sortie"], format="%d%m%Y", errors="coerce")
df["duree"] = (df["sortie"] - df["entree"]).dt.days / 7

actes_uniques = df["acte"].dropna().unique().tolist()
acte_choisi = st.selectbox("Choisissez un acte principal :", sorted(actes_uniques))

df_filtré = df[df["acte"] == acte_choisi]

st.subheader(f"Histogramme des durées pour l’acte {acte_choisi}")
fig = px.box(df_filtré, y="duree", labels={"duree": "Durée de séjour (semaines)"}, points="all")
st.plotly_chart(fig, use_container_width=True)

# Export des données filtrées
st.markdown("### Exporter les données de cette sélection")
telecharger_dataframe(df_filtré, nom_fichier_base=f"histogramme_acte_{acte_choisi}")
