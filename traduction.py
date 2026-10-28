"""Petit traducteur Français / English / עברית avec bouton de copie."""

import json
import os
import re
import sys
import threading
import tkinter as tk
import urllib.parse
import urllib.request
from tkinter import ttk

LANGUES = {"Français": "fr", "English": "en", "עברית (Hébreu)": "iw"}
NOMS = list(LANGUES)
URL = "https://translate.googleapis.com/translate_a/single"
TAILLE_BLOC = 4000
MAX_PHRASES_VARIANTES = 10
ICONE = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))), "icone.ico")


def _requete(texte, source, cible, types):
    params = urllib.parse.urlencode([("client", "gtx"), ("sl", source), ("tl", cible)] + [("dt", t) for t in types])
    donnees = urllib.parse.urlencode({"q": texte}).encode("utf-8")
    requete = urllib.request.Request(
        f"{URL}?{params}",
        data=donnees,
        headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"},
    )
    with urllib.request.urlopen(requete, timeout=20) as reponse:
        return json.loads(reponse.read().decode("utf-8"))


def traduire(texte, source, cible):
    """Traduit le texte en le découpant par lignes pour rester sous la limite de taille."""
    blocs, courant = [], ""
    for ligne in texte.splitlines(keepends=True):
        if courant and len(courant) + len(ligne) > TAILLE_BLOC:
            blocs.append(courant)
            courant = ""
        courant += ligne
    if courant:
        blocs.append(courant)
    return "".join(
        "".join(segment[0] for segment in _requete(bloc, source, cible, ["t"])[0] if segment[0])
        for bloc in blocs
    )


def variantes(texte, source, cible):
    """Autres formulations proposées par Google, phrase par phrase : [(phrase, [options])].

    Google ne les donne que pour une phrase isolée ; on se limite aux textes courts."""
    phrases = [p for p in re.split(r"(?<=[.!?…])\s+|\n+", texte) if p.strip()]
    if len(phrases) > MAX_PHRASES_VARIANTES:
        return []
    resultat = []
    for phrase in phrases:
        reponse = _requete(phrase, source, cible, ["at"])
        for segment in reponse[5] if len(reponse) > 5 and reponse[5] else []:
            options = [option[0] for option in (segment[2] or [])[1:] if option and option[0]]
            if options:
                resultat.append((segment[0], options))
    return resultat


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Traduction  FR ⇄ EN ⇄ HE")
        self.geometry("780x720")
        self.minsize(520, 420)
        if os.path.exists(ICONE):
            try:
                self.iconbitmap(ICONE)
            except tk.TclError:
                pass

        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        police = ("Segoe UI", 11)

        # Barre de langues
        barre = ttk.Frame(self, padding=(10, 10, 10, 0))
        barre.pack(fill="x")
        self.source = ttk.Combobox(barre, values=NOMS, state="readonly", width=18)
        self.source.set("Français")
        self.source.pack(side="left")
        ttk.Button(barre, text="⇄", width=4, command=self.inverser).pack(side="left", padx=8)
        self.cible = ttk.Combobox(barre, values=NOMS, state="readonly", width=18)
        self.cible.set("English")
        self.cible.pack(side="left")
        self.bouton_traduire = ttk.Button(barre, text="Traduire  (Ctrl+Entrée)", command=self.lancer)
        self.bouton_traduire.pack(side="right")
        self.source.bind("<<ComboboxSelected>>", lambda e: self.ajuster_direction())
        self.cible.bind("<<ComboboxSelected>>", lambda e: self.ajuster_direction())

        # Zones de texte
        ttk.Label(self, text="Texte à traduire :", padding=(10, 8, 10, 2)).pack(anchor="w")
        self.entree = tk.Text(self, height=9, wrap="word", font=police, undo=True)
        self.entree.pack(fill="both", expand=True, padx=10)

        ligne = ttk.Frame(self, padding=(10, 8, 10, 2))
        ligne.pack(fill="x")
        ttk.Label(ligne, text="Traduction :").pack(side="left")
        self.bouton_copier = ttk.Button(ligne, text="📋 Copier la traduction", command=self.copier)
        self.bouton_copier.pack(side="right")

        self.sortie = tk.Text(self, height=9, wrap="word", font=police, state="disabled", background="#f4f4f4")
        self.sortie.pack(fill="both", expand=True, padx=10)

        ttk.Label(
            self, text="Vérification : retraduction dans la langue d'origine et autres formulations",
            padding=(10, 8, 10, 2),
        ).pack(anchor="w")
        self.controle = tk.Text(self, height=6, wrap="word", font=("Segoe UI", 10), state="disabled",
                                background="#f4f4f4", foreground="#333")
        self.controle.pack(fill="both", expand=True, padx=10)

        self.statut = ttk.Label(self, text="", padding=(10, 4, 10, 8), foreground="#555")
        self.statut.pack(anchor="w")

        for zone in (self.entree, self.sortie, self.controle):
            zone.tag_configure("rtl", justify="right")
            zone.tag_configure("ltr", justify="left")

        self.bind("<Control-Return>", lambda e: (self.lancer(), "break")[1])
        self.entree.bind("<KeyRelease>", lambda e: self.aligner(self.entree, self.source.get()))
        self.entree.focus_set()

    def ajuster_direction(self):
        if self.source.get() == self.cible.get():
            autre = next(nom for nom in NOMS if nom != self.source.get())
            self.cible.set(autre)
        self.aligner(self.entree, self.source.get())
        self.aligner(self.sortie, self.cible.get())

    def aligner(self, zone, langue):
        tag = "rtl" if LANGUES[langue] == "iw" else "ltr"
        zone.tag_remove("rtl", "1.0", "end")
        zone.tag_remove("ltr", "1.0", "end")
        zone.tag_add(tag, "1.0", "end")

    def inverser(self):
        source, cible = self.source.get(), self.cible.get()
        self.source.set(cible)
        self.cible.set(source)
        traduit = self.sortie.get("1.0", "end-1c")
        if traduit.strip():
            self.entree.delete("1.0", "end")
            self.entree.insert("1.0", traduit)
            self.afficher("")
            self.afficher_controle("", [], self.cible.get())
        self.ajuster_direction()

    def afficher(self, texte):
        self.sortie.configure(state="normal")
        self.sortie.delete("1.0", "end")
        self.sortie.insert("1.0", texte)
        self.aligner(self.sortie, self.cible.get())
        self.sortie.configure(state="disabled")

    def afficher_controle(self, retraduction, variantes, langue_variantes):
        self.controle.configure(state="normal")
        self.controle.delete("1.0", "end")
        if retraduction:
            self.controle.insert("end", "Retraduction : ", "titre")
            self.controle.insert("end", retraduction + "\n", "ltr" if LANGUES[self.source.get()] != "iw" else "rtl")
        if variantes:
            self.controle.insert("end", "\nAutres formulations possibles :\n", "titre")
            rtl = LANGUES[langue_variantes] == "iw"
            for phrase, options in variantes:
                self.controle.insert("end", f"« {phrase.strip()} »\n", "phrase")
                for option in options:
                    self.controle.insert("end", f"   • {option}\n" if not rtl else f"{option} •   \n",
                                         "rtl" if rtl else "ltr")
        self.controle.tag_configure("titre", font=("Segoe UI", 10, "bold"))
        self.controle.tag_configure("phrase", foreground="#777")
        self.controle.configure(state="disabled")

    def lancer(self):
        texte = self.entree.get("1.0", "end-1c").strip()
        if not texte:
            self.statut.configure(text="Entrez un texte à traduire.")
            return
        source, cible = LANGUES[self.source.get()], LANGUES[self.cible.get()]
        self.bouton_traduire.configure(state="disabled")
        self.statut.configure(text="Traduction en cours…")

        def travail():
            try:
                traduction = traduire(texte, source, cible)
                retraduction = traduire(traduction, cible, source)
                resultat, erreur = (traduction, variantes(texte, source, cible), retraduction), None
            except Exception as exc:  # réseau, quota, etc.
                resultat, erreur = None, exc
            self.after(0, self.terminer, resultat, erreur)

        threading.Thread(target=travail, daemon=True).start()

    def terminer(self, resultat, erreur):
        self.bouton_traduire.configure(state="normal")
        if erreur:
            self.statut.configure(text=f"Erreur : {erreur}  (vérifiez la connexion Internet)")
            return
        traduction, variantes, retraduction = resultat
        self.afficher(traduction)
        self.afficher_controle(retraduction, variantes, self.cible.get())
        self.statut.configure(text="Traduction terminée.")

    def copier(self):
        texte = self.sortie.get("1.0", "end-1c")
        if not texte.strip():
            self.statut.configure(text="Rien à copier.")
            return
        self.clipboard_clear()
        self.clipboard_append(texte)
        self.update()
        self.statut.configure(text="✔ Traduction copiée dans le presse-papiers.")


if __name__ == "__main__":
    Application().mainloop()
