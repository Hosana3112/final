import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime
import shutil
import json
from collections import OrderedDict


class FileExplorer:
    def _init_(self, root):
        self.root = root
        self.root.title("Explorateur de Fichiers")
        self.root.geometry("1000x700")

        # Configuration des icônes
        self.folder_icon = "📁"
        self.file_icon = "📄"
        self.favorite_icon = "★"
        self.recent_icon = "⏱"

        # Variables
        self.current_path = os.path.expanduser("~")
        self.favorites = set()
        self.recent_files = OrderedDict()
        self.MAX_RECENT_ITEMS = 20
        self.load_data()
        self.filter_var = tk.StringVar(value="Tous les fichiers")
        self.history = []
        self.history_index = -1

        # Style
        self.style = ttk.Style()
        self.style.configure("Treeview", rowheight=25)
        self.style.configure("TButton", padding=5)

        # Barre de chemin
        self.path_frame = ttk.Frame(self.root)
        self.path_frame.pack(fill=tk.X, padx=5, pady=5)

        # Boutons de navigation
        self.nav_btn_frame = ttk.Frame(self.path_frame)
        self.nav_btn_frame.pack(side=tk.LEFT, padx=2)

        self.back_btn = ttk.Button(self.nav_btn_frame, text="◄", command=self.go_back, width=3)
        self.back_btn.pack(side=tk.LEFT, padx=2)

        self.forward_btn = ttk.Button(self.nav_btn_frame, text="►", command=self.go_forward, width=3)
        self.forward_btn.pack(side=tk.LEFT, padx=2)

        self.path_entry = ttk.Entry(self.path_frame)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.path_entry.insert(0, self.current_path)
        self.path_entry.bind("<Return>", self.navigate_from_entry)

        self.refresh_btn = ttk.Button(self.path_frame, text="🔄", command=self.refresh, width=3)
        self.refresh_btn.pack(side=tk.LEFT, padx=2)

        # Barre de recherche
        self.search_frame = ttk.Frame(self.root)
        self.search_frame.pack(fill=tk.X, padx=5, pady=5)

        self.search_label = ttk.Label(self.search_frame, text="Rechercher:")
        self.search_label.pack(side=tk.LEFT)

        self.search_entry = ttk.Entry(self.search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", self.search_files)

        self.filter_btn = ttk.Button(self.search_frame, text="Filtrer", command=self.show_filter_menu)
        self.filter_btn.pack(side=tk.RIGHT, padx=5)

        # Panneau principal
        self.main_panel = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_panel.pack(fill=tk.BOTH, expand=True)

        # Sidebar
        self.sidebar = ttk.Frame(self.main_panel, width=180)
        self.main_panel.add(self.sidebar, weight=0)

        # Boutons sidebar
        sidebar_buttons = [
            ("★ Favoris", self.show_favorites),
            ("⏱ Récent", self.show_recent_files),
            ("🏠 Accueil", self.go_home),
            ("📂 Ouvrir", self.browse_folder),
        ]

        for text, command in sidebar_buttons:
            btn = ttk.Button(self.sidebar, text=text, command=command)
            btn.pack(fill=tk.X, padx=5, pady=2)

        # Treeview pour les fichiers
        self.tree_frame = ttk.Frame(self.main_panel)
        self.main_panel.add(self.tree_frame, weight=1)

        self.tree = ttk.Treeview(self.tree_frame, columns=("Size", "Type", "Modified"), selectmode="browse")
        self.tree.heading("#0", text="Nom", anchor=tk.W)
        self.tree.heading("Size", text="Taille", anchor=tk.W)
        self.tree.heading("Type", text="Type", anchor=tk.W)
        self.tree.heading("Modified", text="Modifié", anchor=tk.W)

        self.tree.column("#0", stretch=tk.YES, minwidth=200, width=300)
        self.tree.column("Size", stretch=tk.YES, minwidth=50, width=100)
        self.tree.column("Type", stretch=tk.YES, minwidth=50, width=100)
        self.tree.column("Modified", stretch=tk.YES, minwidth=50, width=150)

        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Détails du fichier
        self.details_frame = ttk.Frame(self.root)
        self.details_frame.pack(fill=tk.X, padx=5, pady=5)

        self.details_text = tk.Text(self.details_frame, height=4, state=tk.DISABLED)
        self.details_text.pack(fill=tk.X, expand=True)

        # Événements
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<<TreeviewSelect>>", self.show_file_details)

        # Menu contextuel
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Ouvrir", command=self.open_selected)
        self.context_menu.add_command(label="Supprimer", command=self.delete_selected)
        self.context_menu.add_command(label="Renommer", command=self.rename_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Ajouter aux favoris", command=self.add_to_favorites)
        self.context_menu.add_command(label="Copier le chemin", command=self.copy_path)
        self.context_menu.add_command(label="Ajouter aux récents", command=self.add_to_recent)

        # Menu filtre
        self.filter_menu = tk.Menu(self.root, tearoff=0)
        file_types = [
            ("Tous les fichiers", "Tous les fichiers"),
            ("Images", "Images (jpg, png, gif)"),
            ("Documents", "Documents (txt, pdf, docx)"),
            ("Vidéos", "Vidéos (mp4, avi, mkv)"),
            ("Musique", "Musique (mp3, wav)")
        ]

        for label, value in file_types:
            self.filter_menu.add_radiobutton(
                label=label,
                variable=self.filter_var,
                value=value,
                command=self.refresh
            )

        # Initialiser l'affichage
        self.add_to_history(self.current_path)
        self.refresh()
        self.update_nav_buttons()

    def load_data(self):
        """Charge les favoris et les fichiers récents depuis le disque"""
        try:
            with open("file_explorer_data.json", "r") as f:
                data = json.load(f)
                self.favorites = set(data.get("favorites", []))
                self.recent_files = OrderedDict((k, v) for k, v in data.get("recent_files", {}).items())
        except (FileNotFoundError, json.JSONDecodeError):
            self.favorites = set()
            self.recent_files = OrderedDict()

    def save_data(self):
        """Sauvegarde les favoris et les fichiers récents sur le disque"""
        data = {
            "favorites": list(self.favorites),
            "recent_files": dict(self.recent_files)
        }
        with open("file_explorer_data.json", "w") as f:
            json.dump(data, f)

    def add_to_history(self, path):
        """Ajoute un chemin à l'historique de navigation"""
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]

        self.history.append(path)
        self.history_index = len(self.history) - 1
        self.update_nav_buttons()

    def go_back(self):
        """Retourne au dossier précédent dans l'historique"""
        if self.history_index > 0:
            self.history_index -= 1
            path = self.history[self.history_index]
            self.current_path = path
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)
            self.refresh()
            self.update_nav_buttons()

    def go_forward(self):
        """Avance au dossier suivant dans l'historique"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            path = self.history[self.history_index]
            self.current_path = path
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)
            self.refresh()
            self.update_nav_buttons()

    def update_nav_buttons(self):
        """Met à jour l'état des boutons de navigation"""
        self.back_btn.state(["!disabled" if self.history_index > 0 else "disabled"])
        self.forward_btn.state(["!disabled" if self.history_index < len(self.history) - 1 else "disabled"])

    def add_to_recent(self, path=None):
        """Ajoute un fichier/dossier à la liste des récents"""
        if path is None:
            item = self.tree.selection()[0]
            text = self.tree.item(item, "text")
            path = os.path.join(self.current_path, text)

        self.recent_files[path] = datetime.now().isoformat()

        if len(self.recent_files) > self.MAX_RECENT_ITEMS:
            self.recent_files.popitem(last=False)

        self.save_data()

    def show_recent_files(self):
        """Affiche une fenêtre avec les fichiers récemment consultés"""
        if not self.recent_files:
            messagebox.showinfo("Fichiers récents", "Aucun fichier récent")
            return

        recent_window = tk.Toplevel(self.root)
        recent_window.title(f"Fichiers récents (derniers {self.MAX_RECENT_ITEMS})")
        recent_window.geometry("600x400")

        tree = ttk.Treeview(recent_window, columns=("Type", "Date"), selectmode="browse")
        tree.heading("#0", text="Nom", anchor=tk.W)
        tree.heading("Type", text="Type", anchor=tk.W)
        tree.heading("Date", text="Dernier accès", anchor=tk.W)

        tree.column("#0", stretch=tk.YES, minwidth=200, width=300)
        tree.column("Type", stretch=tk.YES, minwidth=50, width=100)
        tree.column("Date", stretch=tk.YES, minwidth=50, width=150)

        scrollbar = ttk.Scrollbar(recent_window, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)

        for path in reversed(self.recent_files.keys()):
            if os.path.exists(path):
                name = os.path.basename(path)
                last_access = datetime.fromisoformat(self.recent_files[path]).strftime("%Y-%m-%d %H:%M")

                if os.path.isdir(path):
                    tree.insert("", "end", text=name, values=("Dossier", last_access), tags=("directory",))
                else:
                    file_type = self.get_file_type(name)
                    tree.insert("", "end", text=name, values=(file_type, last_access), tags=("file",))
            else:
                self.recent_files.pop(path)

        tree.tag_configure("directory", background="#e1e1e1")
        tree.tag_configure("file", background="#ffffff")

        btn_frame = ttk.Frame(recent_window)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        def open_selected_recent():
            selected = tree.selection()
            if selected:
                path = list(reversed(self.recent_files.keys()))[tree.index(selected[0])]
                if os.path.exists(path):
                    self.add_to_recent(path)
                    if os.path.isdir(path):
                        self.navigate_to(path)
                        recent_window.destroy()
                    else:
                        try:
                            os.startfile(path)
                        except Exception as e:
                            messagebox.showerror("Erreur", f"Impossible d'ouvrir le fichier: {e}")
                else:
                    messagebox.showerror("Erreur", "Le fichier/dossier n'existe plus")
                    self.recent_files.pop(path, None)
                    self.save_data()
                    tree.delete(selected[0])

        ttk.Button(btn_frame, text="Ouvrir", command=open_selected_recent).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Effacer la liste", command=lambda: self.clear_recent_files(recent_window)).pack(
            side=tk.RIGHT)

        tree.bind("<Double-1>", lambda e: open_selected_recent())

    def clear_recent_files(self, window):
        """Efface tous les fichiers récents"""
        if messagebox.askyesno("Confirmation", "Voulez-vous vraiment effacer toute la liste des fichiers récents ?"):
            self.recent_files.clear()
            self.save_data()
            window.destroy()
            messagebox.showinfo("Info", "Liste des fichiers récents effacée")

    def browse_folder(self):
        """Ouvre une boîte de dialogue pour naviguer vers un dossier"""
        folder = filedialog.askdirectory(initialdir=self.current_path)
        if folder:
            self.navigate_to(folder)
            self.add_to_recent(folder)

    def refresh(self):
        """Actualise l'affichage du contenu du dossier courant"""
        self.tree.delete(*self.tree.get_children())
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, self.current_path)

        try:
            parent_dir = os.path.dirname(self.current_path)
            if parent_dir != self.current_path:
                self.tree.insert("", "end", text="..", values=("", "Dossier", ""), tags=("directory",))

            for item in sorted(os.listdir(self.current_path), key=lambda x: x.lower()):
                full_path = os.path.join(self.current_path, item)

                if os.path.isdir(full_path):
                    self.tree.insert("", "end", text=item, values=("", "Dossier", ""), tags=("directory",))
                else:
                    size = os.path.getsize(full_path)
                    modified = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y-%m-%d %H:%M:%S")
                    file_type = self.get_file_type(item)

                    if self.should_show_file(file_type):
                        self.tree.insert("", "end", text=item,
                                         values=(self.format_size(size), file_type, modified),
                                         tags=("file",))

            self.tree.tag_configure("directory", background="#e1e1e1")
            self.tree.tag_configure("file", background="#ffffff")

        except PermissionError:
            messagebox.showerror("Erreur", "Accès refusé à ce dossier")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def should_show_file(self, file_type):
        """Détermine si un fichier doit être affiché selon le filtre actif"""
        filter_value = self.filter_var.get()

        if filter_value == "Tous les fichiers":
            return True
        elif filter_value == "Images (jpg, png, gif)":
            return file_type.lower() in ["jpg", "jpeg", "png", "gif"]
        elif filter_value == "Documents (txt, pdf, docx)":
            return file_type.lower() in ["txt", "pdf", "docx", "doc", "odt"]
        elif filter_value == "Vidéos (mp4, avi, mkv)":
            return file_type.lower() in ["mp4", "avi", "mkv", "mov", "wmv"]
        elif filter_value == "Musique (mp3, wav)":
            return file_type.lower() in ["mp3", "wav", "ogg", "flac"]
        return True

    def format_size(self, size):
        """Formate la taille du fichier pour l'affichage"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    def get_file_type(self, filename):
        """Retourne l'extension du fichier"""
        ext = os.path.splitext(filename)[1][1:].lower()
        return ext if ext else "Inconnu"

    def on_double_click(self, event):
        """Gère le double-clic sur un élément"""
        item = self.tree.selection()[0]
        text = self.tree.item(item, "text")

        if text == "..":
            self.navigate_up()
        elif self.tree.item(item, "tags")[0] == "directory":
            new_path = os.path.join(self.current_path, text)
            self.navigate_to(new_path)
            self.add_to_recent(new_path)
        else:
            self.open_selected()

    def navigate_up(self):
        """Remonte d'un niveau dans l'arborescence"""
        parent_dir = os.path.dirname(self.current_path)
        if parent_dir != self.current_path:
            self.navigate_to(parent_dir)

    def navigate_to(self, path):
        """Navigue vers le chemin spécifié"""
        if os.path.exists(path):
            self.current_path = path
            self.add_to_history(path)
            self.refresh()
        else:
            messagebox.showerror("Erreur", "Le chemin spécifié n'existe pas")

    def navigate_from_entry(self, event):
        """Navigue vers le chemin saisi dans la barre d'adresse"""
        path = self.path_entry.get()
        self.navigate_to(path)

    def show_context_menu(self, event):
        """Affiche le menu contextuel"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()

    def open_selected(self):
        """Ouvre l'élément sélectionné"""
        item = self.tree.selection()[0]
        text = self.tree.item(item, "text")

        if text == "..":
            self.navigate_up()
        elif self.tree.item(item, "tags")[0] == "directory":
            new_path = os.path.join(self.current_path, text)
            self.navigate_to(new_path)
            self.add_to_recent(new_path)
        else:
            full_path = os.path.join(self.current_path, text)
            try:
                os.startfile(full_path)
                self.add_to_recent(full_path)
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'ouvrir le fichier: {e}")

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

                self.refresh()
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de supprimer: {e}")

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
                self.refresh()
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de renommer: {e}")

    def add_to_favorites(self):
        """Ajoute l'élément sélectionné aux favoris"""
        item = self.tree.selection()[0]
        text = self.tree.item(item, "text")
        full_path = os.path.join(self.current_path, text)

        if full_path in self.favorites:
            messagebox.showinfo("Info", "Ce fichier/dossier est déjà dans les favoris")
        else:
            self.favorites.add(full_path)
            self.save_data()
            messagebox.showinfo("Info", "Ajouté aux favoris")

    def show_favorites(self):
        """Affiche la fenêtre des favoris"""
        if not self.favorites:
            messagebox.showinfo("Favoris", "Aucun favori enregistré")
            return

        fav_window = tk.Toplevel(self.root)
        fav_window.title("Favoris")
        fav_window.geometry("600x400")

        tree = ttk.Treeview(fav_window, columns=("Type", "Path"), selectmode="browse")
        tree.heading("#0", text="Nom", anchor=tk.W)
        tree.heading("Type", text="Type", anchor=tk.W)
        tree.heading("Path", text="Chemin", anchor=tk.W)

        tree.column("#0", stretch=tk.YES, minwidth=200, width=250)
        tree.column("Type", stretch=tk.YES, minwidth=50, width=100)
        tree.column("Path", stretch=tk.YES, minwidth=50, width=250)

        scrollbar = ttk.Scrollbar(fav_window, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)

        for path in sorted(self.favorites, key=lambda x: os.path.basename(x).lower()):
            if os.path.exists(path):
                name = os.path.basename(path)
                if os.path.isdir(path):
                    tree.insert("", "end", text=name, values=("Dossier", path), tags=("directory",))
                else:
                    file_type = self.get_file_type(name)
                    tree.insert("", "end", text=name, values=(file_type, path), tags=("file",))
            else:
                self.favorites.remove(path)

        tree.tag_configure("directory", background="#e1e1e1")
        tree.tag_configure("file", background="#ffffff")

        btn_frame = ttk.Frame(fav_window)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        def open_selected_favorite():
            selected = tree.selection()
            if selected:
                path = tree.item(selected[0], "values")[1]
                if os.path.exists(path):
                    self.add_to_recent(path)
                    if os.path.isdir(path):
                        self.navigate_to(path)
                        fav_window.destroy()
                    else:
                        try:
                            os.startfile(path)
                        except Exception as e:
                            messagebox.showerror("Erreur", f"Impossible d'ouvrir le fichier: {e}")
                else:
                    messagebox.showerror("Erreur", "Le fichier/dossier n'existe plus")
                    self.favorites.remove(path)
                    self.save_data()
                    tree.delete(selected[0])

        def remove_from_favorites():
            selected = tree.selection()
            if selected:
                path = tree.item(selected[0], "values")[1]
                self.favorites.remove(path)
                self.save_data()
                tree.delete(selected[0])

        def clear_all_favorites():
            if messagebox.askyesno("Confirmation", "Voulez-vous vraiment supprimer tous les favoris ?"):
                self.favorites.clear()
                self.save_data()
                fav_window.destroy()
                messagebox.showinfo("Info", "Tous les favoris ont été supprimés")

        ttk.Button(btn_frame, text="Ouvrir", command=open_selected_favorite).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Tout supprimer", command=clear_all_favorites).pack(side=tk.RIGHT, padx=5)

        tree.bind("<Double-1>", lambda e: open_selected_favorite())

    def copy_path(self):
        """Copie le chemin de l'élément sélectionné dans le presse-papiers"""
        item = self.tree.selection()[0]
        text = self.tree.item(item, "text")
        full_path = os.path.join(self.current_path, text)
        self.root.clipboard_clear()
        self.root.clipboard_append(full_path)
        messagebox.showinfo("Info", "Chemin copié dans le presse-papiers")

    def search_files(self, event):
        """Recherche des fichiers dans le dossier courant"""
        query = self.search_entry.get().lower()

        if not query:
            return

        for item in self.tree.get_children():
            text = self.tree.item(item, "text").lower()
            if query in text:
                self.tree.selection_set(item)
                self.tree.see(item)
                break

    def show_file_details(self, event):
        """Affiche les détails de l'élément sélectionné"""
        item = self.tree.selection()[0]
        text = self.tree.item(item, "text")

        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)

        if text == "..":
            self.details_text.insert(tk.END, "Dossier parent")
        else:
            full_path = os.path.join(self.current_path, text)
            try:
                if os.path.isdir(full_path):
                    self.details_text.insert(tk.END, f"Dossier: {text}\n")
                    self.details_text.insert(tk.END, f"Chemin: {full_path}\n")
                    self.details_text.insert(tk.END, f"Créé: {datetime.fromtimestamp(os.path.getctime(full_path))}\n")
                    self.details_text.insert(tk.END,
                                             f"Modifié: {datetime.fromtimestamp(os.path.getmtime(full_path))}\n")
                else:
                    self.details_text.insert(tk.END, f"Fichier: {text}\n")
                    self.details_text.insert(tk.END, f"Taille: {self.format_size(os.path.getsize(full_path))}\n")
                    self.details_text.insert(tk.END, f"Type: {self.get_file_type(text)}\n")
                    self.details_text.insert(tk.END,
                                             f"Modifié: {datetime.fromtimestamp(os.path.getmtime(full_path))}\n")
                    self.details_text.insert(tk.END, f"Chemin: {full_path}\n")
            except Exception as e:
                self.details_text.insert(tk.END, f"Erreur: {str(e)}")

        self.details_text.config(state=tk.DISABLED)

    def go_home(self):
        """Navigue vers le dossier home de l'utilisateur"""
        home_path = os.path.expanduser("~")
        self.navigate_to(home_path)
        self.add_to_recent(home_path)

    def show_filter_menu(self):
        """Affiche le menu des filtres"""
        try:
            self.filter_menu.tk_popup(
                self.filter_btn.winfo_rootx(),
                self.filter_btn.winfo_rooty() + self.filter_btn.winfo_height()
            )
        finally:
            self.filter_menu.grab_release()


if _name_ == "_main_":
    root = tk.Tk()
    app = FileExplorer(root)
    root.mainloop()