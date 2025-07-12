import streamlit as st
import re
from datetime import datetime
from collections import defaultdict
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
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

st.image("assets/Donnees_sante2.jpg", caption="Analyse des séjours", use_column_width=True)


st.title("Analyse des actes CSARR à partir d'un fichier RHS (.TXT)")

# Upload du fichier .txt
if "rhs_file_text" not in st.session_state:
    st.warning("Veuillez d'abord importer un fichier RHS dans la page d'accueil.")
    st.stop()

from io import StringIO
contenu_rhs = st.session_state["rhs_file_text"]
if not contenu_rhs:
    st.error("⚠️ Le fichier RHS est vide ou mal chargé.")
    st.stop()

with st.spinner("Analyse du fichier en cours..."):
    lignes = contenu_rhs.splitlines()


        # Regex
    pattern_acte_date = re.compile(r"([A-Z]{3}\+\d{3})\s+(?:[A-Z0-9]+\s+)?(\d{14})")

        # Extraction
    compteur_actes = defaultdict(int)
    patients_uniques = set()
    total_actes = 0
    dernier_patient = None

    for ligne in lignes:
        match_patient = re.search(r"\b(\d{8})\b", ligne)
        if match_patient:
            dernier_patient = match_patient.group(1)


        if not dernier_patient:
            continue

        for match in pattern_acte_date.finditer(ligne):
            code_csarr = match.group(1)
            bloc_date = match.group(2)
            try:
                date_str = bloc_date[2:10]  # JJMMYYYY
                date_acte = datetime.strptime(date_str, "%d%m%Y").date()
            except ValueError:
                continue

            key = (dernier_patient, date_acte)
            compteur_actes[key] += 1
            total_actes += 1
            patients_uniques.add(dernier_patient)

    # DataFrame
    df_summary = pd.DataFrame([
        {"patient_id": pid, "date_acte": date, "nb_actes": nb}
        for (pid, date), nb in compteur_actes.items()
    ])

    df_summary["mois"] = df_summary["date_acte"].apply(lambda x: x.strftime("%Y-%m"))
    df_summary["jour_semaine"] = df_summary["date_acte"].apply(lambda x: x.strftime("%A"))

    st.markdown("### Exporter les données agrégées par date")
    telecharger_dataframe(df_summary, nom_fichier_base="actes_par_jour_patient")


        # Option de filtrage par plage de dates
        # st.subheader("Filtrer les résultats par période (facultatif)")
        # min_date = df_summary["date_acte"].min()
        # max_date = df_summary["date_acte"].max()
        # date_debut = st.date_input("Date de début", value=min_date, min_value=min_date, max_value=max_date)
        # date_fin = st.date_input("Date de fin", value=max_date, min_value=min_date, max_value=max_date)

        # if date_debut > date_fin:
        #     st.warning("La date de début ne peut pas être postérieure à la date de fin.")
        #     st.stop()
        # else:
        #    df_summary = df_summary[(df_summary["date_acte"] >= date_debut) & (df_summary["date_acte"] <= date_fin)]
        #    if df_summary.empty:
        #        st.warning("Aucune donnée pour la période sélectionnée.")
        #        st.stop()
        # La partie au-dessus crée un système de filtrage pour une date de début et une date de fin. Mais son activation bloque les menus déroulant des différents graphs


    df_global = df_summary.groupby("date_acte", as_index=False)["nb_actes"].sum()
    df_global["mois"] = df_global["date_acte"].apply(lambda x: x.strftime("%Y-%m"))
    df_global["jour_semaine"] = df_global["date_acte"].apply(lambda x: x.strftime("%A"))

        # Graphe 1 : actes CSARR par jour (menu mois/jours)
    fig1 = go.Figure()
    mois_uniques = sorted(df_global["mois"].unique())
    jours_uniques = sorted(df_global["jour_semaine"].unique(), key=lambda x: datetime.strptime(x, "%A").weekday())
    jours_traduits = {
        "Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi",
        "Thursday": "Jeudi", "Friday": "Vendredi", "Saturday": "Samedi", "Sunday": "Dimanche"
    }

    for mois in mois_uniques:
        data_mois = df_global[df_global["mois"] == mois]
        trace = go.Bar(x=data_mois["date_acte"], y=data_mois["nb_actes"],
                    name=f"Mois {mois}", visible=True if mois == mois_uniques[0] else False)
        fig1.add_trace(trace)

    for jour in jours_uniques:
        data_jour = df_global[df_global["jour_semaine"] == jour]
        trace = go.Bar(x=data_jour["date_acte"], y=data_jour["nb_actes"],
                        name=f"Jour : {jours_traduits[jour]}", visible=False)
        fig1.add_trace(trace)

    buttons = []
    for i, mois in enumerate(mois_uniques):
        visibility = [j == i for j in range(len(mois_uniques))] + [False]*len(jours_uniques)
        buttons.append(dict(label=f"Mois : {mois}", method="update",
                            args=[{"visible": visibility}, {"title": f"Nombre d’actes CSARR - {mois}"}]))
    for i, jour in enumerate(jours_uniques):
        visibility = [False]*len(mois_uniques) + [j == i for j in range(len(jours_uniques))]
        buttons.append(dict(label=f"Jour : {jours_traduits[jour]}", method="update",
                            args=[{"visible": visibility}, {"title": f"Nombre d’actes CSARR - {jours_traduits[jour]}"}]))
    visibility_all = [True] * len(mois_uniques) + [False]*len(jours_uniques)
    buttons.insert(0, dict(label="Tous les mois", method="update",
                        args=[{"visible": visibility_all}, {"title": "Nombre d’actes CSARR par jour"}]))

    fig1.update_layout(
        updatemenus=[
            dict(
                type="dropdown",
                showactive=True,
                buttons=buttons,
                x=0.0,
                xanchor="left",
                y=1.15,
                yanchor="top"
            )
        ],
        transition=dict(
            duration=500,
            easing="cubic-in-out"
        )
    )
    st.markdown(
        "<b>Abscisses :</b> dates des actes.<br>"
        "<b>Ordonnées :</b> nombre total d’actes CSARR effectués tous patients confondus chaque jour.<br>"
        "Utilisez le menu déroulant pour filtrer par <b>mois</b> ou <b>jour de la semaine</b>.",
        unsafe_allow_html=True
    )
    st.plotly_chart(fig1)

        # Graphe 2 : par patient
    fig2 = go.Figure()
    patients = df_summary["patient_id"].unique()
    buttons2 = []
    for i, pid in enumerate(patients):
        data_patient = df_summary[df_summary["patient_id"] == pid]
        visible = i == 0
        fig2.add_trace(go.Scatter(x=data_patient["date_acte"], y=data_patient["nb_actes"],
                                mode="lines+markers", name=pid, visible=visible))
    for i, pid in enumerate(patients):
        visibility = [j == i for j in range(len(patients))]
        buttons2.append(dict(label=f"{pid}", method="update",
                            args=[{"visible": visibility}, {"title": f"Nombre d’actes CSARR - {pid}"}]))
    buttons2.insert(0, dict(label="Tous", method="update",
                            args=[{"visible": [True] * len(patients)}, {"title": "Nombre d’actes CSARR par jour par patient"}]))

    fig2.update_layout(
        updatemenus=[
            dict(
                type="dropdown",
                showactive=True,
                buttons=buttons2,
                x=0.0,
                xanchor="left",
                y=1.15,
                yanchor="top"
            )
        ],
        transition=dict(
            duration=500,
            easing="cubic-in-out"
        )
    )
    st.markdown(
        "<b>Abscisses :</b> dates des actes.<br>"
        "<b>Ordonnées :</b> nombre d’actes CSARR effectués ce jour-là pour un patient donné.<br>"
        "Utilisez le menu déroulant pour sélectionner un patient ou afficher tous les patients.",
        unsafe_allow_html=True
    )
    st.plotly_chart(fig2)

        # Liste patients avec un seul acte
    patients_unique_acte = df_summary.groupby("patient_id")["nb_actes"].sum().reset_index()
    patients_unique_acte = patients_unique_acte[patients_unique_acte["nb_actes"] == 1]
    st.subheader("Patients avec un seul acte CSARR")
    st.dataframe(patients_unique_acte)
    st.markdown("### Exporter la liste des patients avec un seul acte")
    telecharger_dataframe(patients_unique_acte, nom_fichier_base="patients_un_seul_acte")


        # Graphique additionnel : distribution du nombre total d'actes par patient
    df_total_par_patient = df_summary.groupby("patient_id")["nb_actes"].sum().reset_index()
    fig3 = px.histogram(
        df_total_par_patient,
        x="nb_actes",
        nbins=30,
        title="Distribution du nombre total d’actes par patient",
        labels={"nb_actes": "Nombre total d’actes CSARR", "count": "Nombre de patients"}
    )
    st.plotly_chart(fig3)
    st.markdown(
        "<i>Ce graphique montre combien de patients ont eu un certain nombre total d’actes CSARR sur la période analysée.</i><br>"
        "<b>Abscisses :</b> total d’actes CSARR par patient.<br>"
        "<b>Ordonnées :</b> nombre de patients correspondant à chaque total.",
        unsafe_allow_html=True
    )
    st.markdown("### Exporter le total d’actes par patient")
    telecharger_dataframe(df_total_par_patient, nom_fichier_base="total_actes_par_patient")

    st.markdown("### Export global de tous les tableaux")

    def telecharger_export_global(dfs: dict, nom_fichier="export_global_CSARR.xlsx"):
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            for nom_feuille, df in dfs.items():
                df.to_excel(writer, index=False, sheet_name=nom_feuille[:31])  # Excel limite à 31 caractères
        st.download_button(
            label="Télécharger tous les tableaux (Excel)",
            data=buffer.getvalue(),
            file_name=nom_fichier,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    dfs_export = {
        "Actes_par_jour_patient": df_summary,
        "Patients_un_seul_acte": patients_unique_acte,
        "Total_actes_par_patient": df_total_par_patient
    }
    telecharger_export_global(dfs_export)
