# final
       Les membres du groupes
HAZOUME Lucius

HOUETEHOU Jubiléenne

OGOUTCHORO Modeste

VEHOUNKPE Daren

ZITTI Hosana

      Difficultés rencontrées 
1️⃣ Gestion des chemins et compatibilité multi-OS
📌 Problème :

Les chemins diffèrent entre Windows (C:\Users\...) et Linux/macOS (/home/...).

Utiliser os.path.join() pour éviter des erreurs de compatibilité.

✅ Solution adoptée :

os.path.join() pour concaténer les chemins sans erreur.

os.path.expanduser("~") pour récupérer le dossier utilisateur de manière portable.

🔍 Code correspondant :
python
def navigate_to(self, path):
    """Navigue vers le chemin spécifié"""
    if os.path.exists(path):
        self.current_path = path
        self.add_to_history(path)
        self.refresh()
    else:
        messagebox.showerror("Erreur", "Le chemin spécifié n'existe pas")

def go_home(self):
    """Navigue vers le dossier home de l'utilisateur"""
    home_path = os.path.expanduser("~")  # Récupère le dossier utilisateur
    self.navigate_to(home_path)
    self.add_to_recent(home_path)

2️⃣ Rafraîchissement de l’interface après chaque action
📌 Problème :

L'affichage doit se mettre à jour après une suppression, un renommage, ou un ajout aux favoris.

Trop de rafraîchissements pourraient ralentir l’application.

✅ Solution adoptée :

self.refresh() est appelé après chaque modification.

self.tree.delete(*self.tree.get_children()) permet de vider la liste avant de la recharger.

🔍 Code correspondant :
python
def delete_selected(self):
    """Supprime l'élément sélectionné"""
    item = self.tree.selection()[0]
    text = self.tree.item(item, "text")
    full_path = os.path.join(self.current_path, text)

    if messagebox.askyesno("Confirmation", f"Voulez-vous vraiment supprimer {text} ?"):
        try:
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
            else:
                os.remove(full_path)

            self.favorites.discard(full_path)
            self.recent_files.pop(full_path, None)
            self.save_data()

            self.refresh()  # Met à jour l'affichage
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de supprimer: {e}")

3️⃣ Suppression et renommage sécurisés des fichiers
📌 Problème :

Un fichier peut être utilisé par un autre programme, empêchant sa suppression ou son renommage.

Une suppression définitive est risquée.

✅ Solution adoptée :

Utilisation de try/except pour gérer les erreurs.

Demande de confirmation avant suppression.

🔍 Code correspondant :
python
def rename_selected(self):
    """Renomme l'élément sélectionné"""
    item = self.tree.selection()[0]
    text = self.tree.item(item, "text")
    old_path = os.path.join(self.current_path, text)

    new_name = simpledialog.askstring("Renommer", "Nouveau nom:", initialvalue=text)
    if new_name and new_name != text:
        new_path = os.path.join(self.current_path, new_name)
        try:
            os.rename(old_path, new_path)

            if old_path in self.favorites:
                self.favorites.remove(old_path)
                self.favorites.add(new_path)

            if old_path in self.recent_files:
                self.recent_files[new_path] = self.recent_files.pop(old_path)

            self.save_data()
            self.refresh()  # Mise à jour après renommage
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de renommer: {e}")

4️⃣ Gestion des fichiers récents et favoris
📌 Problème :

Il faut sauvegarder les fichiers favoris et récents entre les sessions.

Si un fichier favori est supprimé, il ne doit pas causer d'erreur.

✅ Solution adoptée :

Stockage des favoris dans self.favorites (ensemble).

Vérification de l’existence des fichiers avant affichage.

🔍 Code correspondant :
python
def add_to_favorites(self):
    """Ajoute l'élément sélectionné aux favoris"""
    item = self.tree.selection()[0]
    text = self.tree.item(item, "text")
    full_path = os.path.join(self.current_path, text)

    if full_path in self.favorites:
        messagebox.showinfo("Info", "Ce fichier/dossier est déjà dans les favoris")
    else:
        self.favorites.add(full_path)
        self.save_data()  # Sauvegarde les favoris
        messagebox.showinfo("Info", "Ajouté aux favoris")

def show_favorites(self):
    """Affiche la fenêtre des favoris"""
    if not self.favorites:
        messagebox.showinfo("Favoris", "Aucun favori enregistré")
        return

    for path in sorted(self.favorites, key=lambda x: os.path.basename(x).lower()):
        if not os.path.exists(path):  # Vérifie si le favori existe toujours
            self.favorites.remove(path)

5️⃣ Gestion des erreurs et robustesse de l’application
📌 Problème :

Un fichier peut être supprimé en dehors de l'application, provoquant une erreur.

Il faut éviter que l’application ne se ferme en cas d’erreur.

✅ Solution adoptée :

Utilisation de try/except pour capturer les erreurs.

Messages d'erreur avec messagebox.showerror().

🔍 Code correspondant :
python
def open_selected(self):
    """Ouvre l'élément sélectionné"""
    item = self.tree.selection()[0]
    text = self.tree.item(item, "text")
    full_path = os.path.join(self.current_path, text)

    try:
        os.startfile(full_path)
        self.add_to_recent(full_path)
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible d'ouvrir le fichier: {e}")

6️⃣ Implémentation de la recherche et du filtrage
📌 Problème :

La recherche doit être rapide et intuitive.

Il faut surligner les fichiers trouvés sans ralentir l'affichage.

✅ Solution adoptée :

Comparaison des noms en minuscules pour ne pas être sensible à la casse.

tree.selection_set() pour mettre en surbrillance l'élément trouvé.

🔍 Code correspondant :
python
def search_files(self, event):
    """Recherche des fichiers dans le dossier courant"""
    query = self.search_entry.get().lower()

    if not query:
        return

    for item in self.tree.get_children():
        text = self.tree.item(item, "text").lower()
        if query in text:
            self.tree.selection_set(item)  # Sélectionne l'élément correspondant
            self.tree.see(item)  # Fait défiler la vue jusqu'à l'élément
            break
