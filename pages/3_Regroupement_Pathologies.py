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

st.image("assets/Donnees_sante4.jpg", caption="Analyse des séjours", use_column_width=True)

st.title("Regroupement par pathologies (Diagnostics)")

if "rhs_file_text" not in st.session_state:
    st.warning("Veuillez d'abord importer un fichier RHS dans la page d’accueil.")
    st.stop()

lignes = st.session_state["rhs_file_text"].splitlines()

def extraire_diagnostics(ligne):
    return re.findall(r'[A-Z]\d{2}\.?\d*', ligne)

# Extraction des diagnostics par ligne
diagnostics = []
for ligne in lignes:
    diags = extraire_diagnostics(ligne)
    diagnostics.extend(diags)

df_diag = pd.DataFrame(diagnostics, columns=["diagnostic"])
top_diag = df_diag["diagnostic"].value_counts().head(20).reset_index()
top_diag.columns = ["diagnostic", "fréquence"]

st.subheader("Top 20 des diagnostics les plus fréquents")
fig = px.bar(top_diag, x="diagnostic", y="fréquence", color="fréquence", height=500)
st.plotly_chart(fig, use_container_width=True)

# Ajout des boutons d'export
st.markdown("### Exporter les résultats")
telecharger_dataframe(top_diag, nom_fichier_base="top_20_diagnostics")
