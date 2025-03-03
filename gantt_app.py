import streamlit as st
import pandas as pd
import plotly.figure_factory as ff

# -----------------------------
# 1. FONCTION POUR CALCULER LES DATES DE DÉBUT/FIN
# -----------------------------
def calculer_planning(tasks):
    """
    Calcule pour chaque tâche sa date de début (en jours)
    et sa date de fin en fonction de la durée et des dépendances.
    Retourne un DataFrame avec colonnes:
    - Task
    - Start
    - Finish
    - Resource (optionnel, pour colorer)
    """
    # Pour stocker les informations calculées
    results = []

    # On crée un dictionnaire pour accéder rapidement
    # aux dates de fin de chaque tâche
    end_dates = {}

    for t in tasks:
        task_name = t['Nom']
        duration = t['Durée']
        dependencies = t['Dépendances']

        # Si pas de dépendances, la tâche commence à 0
        if not dependencies:
            start_day = 0
        else:
            # On récupère la date de fin maximale parmi les dépendances
            start_day = max(end_dates[dep] for dep in dependencies if dep in end_dates)

        finish_day = start_day + duration

        # On enregistre la date de fin pour réutiliser dans les dépendances suivantes
        end_dates[task_name] = finish_day

        results.append({
            'Task': task_name,
            'Start': start_day,
            'Finish': finish_day,
            'Resource': 'Tâche'  # juste pour colorer éventuellement
        })

    df = pd.DataFrame(results)
    return df

# -----------------------------
# 2. INTERFACE STREAMLIT
# -----------------------------
def main():
    st.title("Générateur de diagramme de Gantt")

    st.write("""
    **Mode d'emploi** :
    1. Renseignez vos tâches (Nom, Durée en jours, et dépendances éventuelles).
    2. Cliquez sur **Ajouter la tâche** pour l'enregistrer.
    3. Lorsque toutes les tâches sont ajoutées, cliquez sur **Générer le planning**.
    """)

    # Pour stocker les tâches saisies en session
    if "tasks" not in st.session_state:
        st.session_state.tasks = []

    # Formulaire pour saisir une tâche
    with st.form("form-ajout-tache", clear_on_submit=True):
        nom_tache = st.text_input("Nom de la tâche")
        duree_tache = st.number_input("Durée (en jours)", min_value=1, value=5)
        dependances_str = st.text_input("Dépendances (séparer par des virgules)")

        submitted = st.form_submit_button("Ajouter la tâche")
        if submitted:
            # On parse les dépendances
            if dependances_str.strip():
                dependances = [d.strip() for d in dependances_str.split(",")]
            else:
                dependances = []

            st.session_state.tasks.append({
                "Nom": nom_tache,
                "Durée": duree_tache,
                "Dépendances": dependances
            })
            st.success(f"Tâche '{nom_tache}' ajoutée.")

    # Afficher la liste des tâches déjà saisies
    if st.session_state.tasks:
        st.subheader("Tâches enregistrées")
        df_tasks = pd.DataFrame(st.session_state.tasks)
        st.table(df_tasks)

        # Bouton pour générer le diagramme de Gantt
        if st.button("Générer le planning"):
            df_gantt = calculer_planning(st.session_state.tasks)

            # On génère le diagramme de Gantt avec plotly
            # Supprimé l'argument 'showgrid' qui causait l'erreur
            fig = ff.create_gantt(
                df_gantt,
                index_col='Resource',
                show_colorbar=True,
                group_tasks=True,
                title="Diagramme de Gantt"
            )
            st.plotly_chart(fig, use_container_width=True)

            st.write("**Tableau récapitulatif** :")
            st.dataframe(df_gantt)

    else:
        st.info("Aucune tâche enregistrée pour le moment.")

if __name__ == "__main__":
    main()