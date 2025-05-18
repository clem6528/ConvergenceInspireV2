import matplotlib.pyplot as plt
import re
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import os
import shutil


OPTIMISATIONS = {
    "Optimisation de la masse": "Objective Function (Minimize MASS )",
    "Optimisation de la raideur": "Objective Function (Minimize WCOMP)",
    "Optimisation de la fréquence": "Objective Function (Maximize WFREQ)"
}

OBJ_SUFFIX = {
    "Optimisation de la masse": "MASS",
    "Optimisation de la raideur": "WCOMP",
    "Optimisation de la fréquence": "WFREQ"
}

# Mapping pour affichage utilisateur
USER_LABELS = {
    "mass": "Masse (Kg)",
    "violation": "Maximum Constraint Violation (%)",
    "objective": "Fonction Objective",
    "epsilon": "Epsilon (Ratio de l'énergie de déformation résiduelle)"
}

def charger_fichier(obj_label):
    global file_path, iterations, masses, violations, objectives, epsilons
    file_path = filedialog.askopenfilename(
        title="Sélectionnez le fichier source",
        filetypes=[("Fichiers résultats", "*.out"), ("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")]
    )
    if not file_path:
        messagebox.showerror("Erreur", "Aucun fichier sélectionné. Arrêt du programme.")
        root.quit()
        return

    # Copie .out -> .txt si besoin (le .out reste présent)
    base, ext = os.path.splitext(file_path)
    if ext.lower() == ".out":
        new_file_path = base + ".txt"
        shutil.copy(file_path, new_file_path)
        file_path = new_file_path

    # Extraction des données
    iterations.clear()
    masses.clear()
    violations.clear()
    objectives.clear()
    epsilons.clear()

    last_objective = None
    iter_regex = re.compile(r'\s*ITERATION\s+(\d+)')
    mass_regex = re.compile(r'Mass\s*=\s*([0-9.Ee+-]+)')
    viol_regex = re.compile(r'Maximum Constraint Violation %\s*=\s*([0-9.Ee+-]+)')
    epsilon_regex = re.compile(r'\s*1\s+[0-9.Ee+-]+\s+([0-9.Ee+-]+)\s+([0-9.Ee+-]+)')
    obj_regex = re.compile(rf'{re.escape(obj_label)}\s*=\s*([0-9.Ee+-]+)')

    start_extract = False
    with open(file_path, 'r', encoding='utf-8') as f:
        current_iter = None
        current_mass = None
        current_violation = None
        current_epsilon = None
        current_objective = None
        for line in f:
            match_iter = iter_regex.match(line)
            if match_iter:
                # Ajoute les valeurs précédentes si ce n'est pas la première itération
                if current_iter is not None and start_extract:
                    iterations.append(current_iter)
                    masses.append(current_mass)
                    violations.append(current_violation)
                    objectives.append(current_objective)
                    epsilons.append(current_epsilon)
                current_iter = int(match_iter.group(1))
                current_mass = None
                current_violation = None
                current_objective = None
                current_epsilon = None
                if current_iter == 1:
                    start_extract = True
                continue

            if not start_extract:
                continue

            match_obj = obj_regex.search(line)
            if match_obj:
                current_objective = float(match_obj.group(1))
                continue

            match_mass = mass_regex.search(line)
            if match_mass:
                current_mass = float(match_mass.group(1))
                continue

            match_violation = viol_regex.search(line)
            if match_violation:
                current_violation = float(match_violation.group(1))
                continue

            match_epsilon = epsilon_regex.match(line)
            if match_epsilon:
                current_epsilon = float(match_epsilon.group(2))
                continue

        # Ajoute la dernière itération à la fin du fichier
        if current_iter is not None and start_extract:
            iterations.append(current_iter)
            masses.append(current_mass)
            violations.append(current_violation)
            objectives.append(current_objective)
            epsilons.append(current_epsilon)

    if all(obj is None for obj in objectives):
        messagebox.showerror(
            "Erreur de paramètre",
            "La fonction objective n'est pas présente dans le fichier de sortie. "
            "Probablement dûe au type d'optimisation réalisé sur Inspire"
        )

def plot_selected():
    obj_suffix = OBJ_SUFFIX[opt_var.get()]
    obj_label_checkbox = f"{USER_LABELS['objective']} ({obj_suffix})"
    params = {
        obj_label_checkbox: objectives,
        USER_LABELS["mass"]: masses,
        USER_LABELS["violation"]: violations,
        USER_LABELS["epsilon"]: epsilons
    }
    selected = [param for param, var in vars_dict.items() if var.get()]
    if not selected:
        messagebox.showwarning("Aucun choix", "Veuillez sélectionner au moins un paramètre.")
        return
    if len(selected) > 2:
        messagebox.showwarning("Trop de choix", "Veuillez sélectionner au maximum deux paramètres.")
        return

    if len(selected) == 1:
        plt.figure(figsize=(10, 5))
        plt.plot(iterations, params[selected[0]], marker='o', label=selected[0])
        plt.xlabel("Itération")
        plt.ylabel(selected[0])
        plt.title(f"Graphe de convergence : {selected[0]}")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        # Affichage de la dernière itération et valeur sur les axes
        if iterations and params[selected[0]]:
            ax = plt.gca()
            y_final = params[selected[0]][-1]
            x_final = iterations[-1]
            # Axe X : ajouter la dernière itération si absente
            xticks = list(ax.get_xticks())
            if x_final not in xticks:
                xticks.append(x_final)
                xticks = sorted(xticks)
                ax.set_xticks(xticks)
            labels = [item.get_text() for item in ax.get_xticklabels()]
            new_labels = []
            for label in labels:
                try:
                    val = int(float(label))
                    if val == x_final:
                        new_labels.append(f"{val}")
                    else:
                        new_labels.append(label)
                except:
                    new_labels.append(label)
            ax.set_xticklabels(new_labels, color='black')
            # Axe Y : ajouter la dernière valeur si absente
            yticks = list(ax.get_yticks())
            if y_final not in yticks:
                yticks.append(y_final)
                yticks = sorted(yticks)
                ax.set_yticks(yticks)
            ylabels = [item.get_text() for item in ax.get_yticklabels()]
            new_ylabels = []
            for label in ylabels:
                try:
                    val = float(label)
                    if abs(val - y_final) < 1e-8:
                        new_ylabels.append(f"{val:.4g}")
                    else:
                        new_ylabels.append(label)
                except:
                    new_ylabels.append(label)
            ax.set_yticklabels(new_ylabels, color='black')
        plt.show()
    elif len(selected) == 2:
        fig, ax1 = plt.subplots(figsize=(10, 5))
        color1 = 'tab:blue'
        color2 = 'tab:green'
        ax1.set_xlabel("Itération")
        ax1.set_ylabel(selected[0], color=color1)
        ax1.plot(iterations, params[selected[0]], marker='o', color=color1, label=selected[0])
        ax1.tick_params(axis='y', labelcolor=color1)

        ax2 = ax1.twinx()
        ax2.set_ylabel(selected[1], color=color2)
        ax2.plot(iterations, params[selected[1]], marker='s', color=color2, label=selected[1])
        ax2.tick_params(axis='y', labelcolor=color2)

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

        plt.title(f"Graphe de convergence : {selected[0]} et {selected[1]}")
        fig.tight_layout()
        plt.grid(True)
        # Affichage de la dernière itération et valeurs sur les axes
        if iterations and params[selected[0]] and params[selected[1]]:
            y1_final = params[selected[0]][-1]
            y2_final = params[selected[1]][-1]
            x_final = iterations[-1]
            # Axe X
            xticks = list(ax1.get_xticks())
            if x_final not in xticks:
                xticks.append(x_final)
                xticks = sorted(xticks)
                ax1.set_xticks(xticks)
            labels = [item.get_text() for item in ax1.get_xticklabels()]
            new_labels = []
            for label in labels:
                try:
                    val = int(float(label))
                    if val == x_final:
                        new_labels.append(f"{val}")
                    else:
                        new_labels.append(label)
                except:
                    new_labels.append(label)
            ax1.set_xticklabels(new_labels, color='black')
            # Axe Y gauche
            yticks1 = list(ax1.get_yticks())
            if y1_final not in yticks1:
                yticks1.append(y1_final)
                yticks1 = sorted(yticks1)
                ax1.set_yticks(yticks1)
            ylabels1 = [item.get_text() for item in ax1.get_yticklabels()]
            new_ylabels1 = []
            for label in ylabels1:
                try:
                    val = float(label)
                    if abs(val - y1_final) < 1e-8:
                        new_ylabels1.append(f"{val:.4g}")
                    else:
                        new_ylabels1.append(label)
                except:
                    new_ylabels1.append(label)
            ax1.set_yticklabels(new_ylabels1, color=color1)
            # Axe Y droit
            yticks2 = list(ax2.get_yticks())
            if y2_final not in yticks2:
                yticks2.append(y2_final)
                yticks2 = sorted(yticks2)
                ax2.set_yticks(yticks2)
            ylabels2 = [item.get_text() for item in ax2.get_yticklabels()]
            new_ylabels2 = []
            for label in ylabels2:
                try:
                    val = float(label)
                    if abs(val - y2_final) < 1e-8:
                        new_ylabels2.append(f"{val:.4g}")
                    else:
                        new_ylabels2.append(label)
                except:
                    new_ylabels2.append(label)
            ax2.set_yticklabels(new_ylabels2, color=color2)
        plt.show()

def choisir_fichier_et_parametres():
    obj_label = OPTIMISATIONS[opt_var.get()]
    obj_label_var.set(obj_label)
    obj_suffix = OBJ_SUFFIX[opt_var.get()]
    obj_label_checkbox = f"{USER_LABELS['objective']} ({obj_suffix})"
    checkbox_labels = [
        obj_label_checkbox,
        USER_LABELS["mass"],
        USER_LABELS["violation"],
        USER_LABELS["epsilon"]
    ]
    charger_fichier(obj_label)
    # Efface les anciens widgets de sélection de paramètres
    for widget in root.winfo_children():
        if isinstance(widget, tk.Button) or isinstance(widget, tk.Checkbutton):
            widget.destroy()
    global vars_dict
    vars_dict = {}
    row = 2
    for param in checkbox_labels:
        var = tk.BooleanVar()
        cb = tk.Checkbutton(root, text=param, variable=var)
        cb.grid(row=row, column=0, sticky='w', padx=10, pady=5)
        vars_dict[param] = var
        row += 1
    btn_plot = tk.Button(root, text="Tracer", command=plot_selected)
    btn_plot.grid(row=row, column=0, pady=10)
    btn_file = tk.Button(root, text="Resélectionner un fichier", command=choisir_fichier_et_parametres)
    btn_file.grid(row=row+1, column=0, pady=5)
    btn_quit = tk.Button(root, text="Quitter", command=root.destroy)
    btn_quit.grid(row=row+2, column=0, pady=10)

# Initialisation des listes et paramètres globaux
iterations = []
masses = []
violations = []
objectives = []
epsilons = []
vars_dict = {}

# Création de la fenêtre tkinter principale
root = tk.Tk()
root.title("Convergence Inspire")

obj_label_var = tk.StringVar()

# Menu déroulant pour le choix de l'optimisation
tk.Label(root, text="Choisissez le type d'optimisation :").grid(row=0, column=0, padx=10, pady=10, sticky='w')
opt_var = tk.StringVar(value=list(OPTIMISATIONS.keys())[0])
opt_menu = ttk.Combobox(root, textvariable=opt_var, values=list(OPTIMISATIONS.keys()), state="readonly")
opt_menu.grid(row=1, column=0, padx=10, pady=5, sticky='w')

# Bouton pour sélectionner le fichier et afficher les paramètres à tracer
btn_next = tk.Button(root, text="Sélectionner un fichier", command=choisir_fichier_et_parametres)
btn_next.grid(row=2, column=0, pady=10)

root.mainloop()