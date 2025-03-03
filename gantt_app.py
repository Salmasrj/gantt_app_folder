import streamlit as st
import pandas as pd
import plotly.figure_factory as ff
import plotly.graph_objects as go
from datetime import datetime, timedelta
from numpy import asarray, prod, float16, round, floor, uint8
from grapheMPM import GrapheMPM  


# -----------------------------
# 1. FONCTION POUR CALCULER LES DATES DE DÉBUT/FIN
# -----------------------------
def calculer_planning(tasks, date_debut):
    results = []
    end_dates = {}
    task_levels = {}

    for t in tasks:
        task_name = t['Nom']
        duration = t['Durée']
        dependencies = t['Dépendances']

        if not dependencies:
            start_day = 0
            level = 1  # Commence à 1 au lieu de 0
        else:
            start_day = max(end_dates[dep] for dep in dependencies if dep in end_dates)
            level = max(task_levels[dep] for dep in dependencies if dep in task_levels) + 1

        finish_day = start_day + duration
        end_dates[task_name] = finish_day
        task_levels[task_name] = level

        date_debut_tache = date_debut + timedelta(days=start_day)
        date_fin_tache = date_debut + timedelta(days=finish_day)
        
        date_debut_str = date_debut_tache.strftime('%Y-%m-%d')
        date_fin_str = date_fin_tache.strftime('%Y-%m-%d')

        results.append({
            'Task': task_name,
            'Start': date_debut_str,
            'Finish': date_fin_str,
            'Resource': 'Tâche',
            'start_jour': start_day,
            'finish_jour': finish_day,
            'Level': level
        })

    df = pd.DataFrame(results)
    return df

# -----------------------------
# 2. FONCTION POUR CREER LE TABLEAU DES NIVEAUX DE TÂCHES
# -----------------------------
def transformer_niveaux(df):
    niveaux = df.pivot_table(index='Task', columns='Level', aggfunc='size', fill_value=0)
    niveaux.columns = [f'Niveau {col}' for col in niveaux.columns]
    return niveaux

# -----------------------------
# 3. FONCTION POUR CALCULER LES DATES AU PLUS TÔT ET AU PLUS TARD
# -----------------------------
def calculer_dates_mpm(tasks):
    tasks_dict = {task['Nom']: task for task in tasks}
    dates_au_plus_tot = {}
    dates_au_plus_tard = {}

    def calculer_date_au_plus_tot(task_name):
        if task_name in dates_au_plus_tot:
            return dates_au_plus_tot[task_name]
        task = tasks_dict[task_name]
        if not task['Dépendances']:
            dates_au_plus_tot[task_name] = 0
        else:
            dates_au_plus_tot[task_name] = max(calculer_date_au_plus_tot(dep) + tasks_dict[dep]['Durée'] for dep in task['Dépendances'])
        return dates_au_plus_tot[task_name]

    def calculer_date_au_plus_tard(task_name, project_duration):
        if task_name in dates_au_plus_tard:
            return dates_au_plus_tard[task_name]
        task = tasks_dict[task_name]
        if not any(task_name in tasks_dict[dep]['Dépendances'] for dep in tasks_dict):
            dates_au_plus_tard[task_name] = project_duration - task['Durée']
        else:
            dates_au_plus_tard[task_name] = min(calculer_date_au_plus_tard(dep, project_duration) - task['Durée'] for dep in tasks_dict if task_name in tasks_dict[dep]['Dépendances'])
        return dates_au_plus_tard[task_name]

    project_duration = max(calculer_date_au_plus_tot(task['Nom']) + task['Durée'] for task in tasks)
    for task in tasks:
        calculer_date_au_plus_tard(task['Nom'], project_duration)

    return dates_au_plus_tot, dates_au_plus_tard, project_duration

# -----------------------------
# 4. FONCTION POUR LE GRAPHE MPM LE CHEMIN CRITIQUE
# -----------------------------
def determiner_chemin_critique(tasks, dates_au_plus_tot, dates_au_plus_tard):
    chemin_critique = []
    for task in tasks:
        task_name = task['Nom']
        if dates_au_plus_tot[task_name] == dates_au_plus_tard[task_name]:
            chemin_critique.append(task_name)
    return chemin_critique

# -----------------------------
# 5. INTERFACE STREAMLIT
# -----------------------------
def main():
    st.title("Générateur de diagramme de Gantt et MPM")

    st.write("""
    **Mode d'emploi** :
    1. Sélectionnez une date de début pour votre projet.
    2. Renseignez vos tâches (Nom, Durée en jours, et dépendances éventuelles).
    3. Cliquez sur **Ajouter la tâche** pour l'enregistrer.
    4. Lorsque toutes les tâches sont ajoutées, cliquez sur **Générer le planning**.
    """)

    if "tasks" not in st.session_state:
        st.session_state.tasks = []

    date_debut = st.date_input(
        "Date de début du projet",
        datetime.now().date(),
        help="Cette date sera utilisée comme point de départ du diagramme de Gantt"
    )

    with st.form("form-ajout-tache", clear_on_submit=True):
        nom_tache = st.text_input("Nom de la tâche")
        duree_tache = st.number_input("Durée (en jours)", min_value=1, value=5)
        dependances_str = st.text_input("Dépendances (séparer par des virgules)")

        submitted = st.form_submit_button("Ajouter la tâche")
        if submitted:
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

    if st.session_state.tasks:
        st.subheader("Tâches enregistrées")
        df_tasks = pd.DataFrame(st.session_state.tasks)
        st.table(df_tasks)

        if st.button("Générer le planning"):
            df_gantt = calculer_planning(st.session_state.tasks, date_debut)

            st.write("**Tableau des niveaux de tâches** :")
            df_levels = transformer_niveaux(df_gantt)
            st.table(df_levels)

            fig_gantt = ff.create_gantt(
                df_gantt,
                index_col='Resource',
                show_colorbar=True,
                group_tasks=True,
                title=f"Diagramme de Gantt - Début : {date_debut.strftime('%d/%m/%Y')}"
            )
            st.plotly_chart(fig_gantt, use_container_width=True)

            st.write("**Tableau récapitulatif** :")
            df_display = df_gantt.copy()
            df_display['Début (jour)'] = df_display['start_jour']
            df_display['Fin (jour)'] = df_display['finish_jour']
            df_display['Début (date)'] = df_display['Start']
            df_display['Fin (date)'] = df_display['Finish']
            st.dataframe(df_display[['Task', 'Début (jour)', 'Fin (jour)', 'Début (date)', 'Fin (date)']])

            st.write("**Diagramme MPM** :")
            dates_au_plus_tot, dates_au_plus_tard, project_duration = calculer_dates_mpm(st.session_state.tasks)
            chemin_critique = determiner_chemin_critique(st.session_state.tasks, dates_au_plus_tot, dates_au_plus_tard)

            fig_mpm = go.Figure()

            for task in st.session_state.tasks:
                task_name = task['Nom']
                start = dates_au_plus_tot[task_name]
                finish = start + task['Durée']
                color = 'red' if task_name in chemin_critique else 'blue'
                fig_mpm.add_trace(go.Scatter(
                    x=[start, finish],
                    y=[task_name, task_name],
                    mode='lines+markers',
                    line=dict(color=color),
                    name=task_name
                ))

            fig_mpm.update_layout(
                title="Diagramme MPM",
                xaxis_title="Temps (jours)",
                yaxis_title="Tâches",
                showlegend=False
            )
            st.plotly_chart(fig_mpm, use_container_width=True)

            # dico des prédecesseurs
            predecessors = {"A": "", "B": "", "C": "A", "D": "AB", "E":"B",
                "F":"DE", "G": "E", "H":"CF", "I":"FG", "J": "HI", "K": "I"}
            # dico des pondérations
            weights = {"A": 7, "B": 3, "C": 4.1, "D": 2.3, "E": 8,
                "F": 6, "G": 5, "H": 7, "I": 5, "J": 3, "K": 3.5}

            G = GrapheMPM(pred=predecessors, pond=weights, marges=False) # par défaut marges=False
            G.earliestdate()
            G.makeGraphviz()
            G.gv.render("ex-ed-nomarge")
            G.gv.format = "svg"
            G.gv.render("ex-ed-nomarge")
            G.latestdate()
            G.makeGraphviz()
            G.gv.render("ex-full-nomarge")
            G1 = GrapheMPM(pred=p, pond=w, marges=False, presentation=1, show_level=False)
            G.gv.attr(rankdir="RL") # right-left
            G.gv.render("image")

    else:
        st.info("Aucune tâche enregistrée pour le moment.")

if __name__ == "__main__":
    main()
