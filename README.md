# Traduction FR ⇄ EN ⇄ HE

Petit logiciel Windows pour traduire un texte entre le **français**, l'**anglais** et l'**hébreu** (dans tous les sens), avec un bouton pour **copier la traduction**.

## Télécharger

Dernier `Traduction.exe` : onglet **Releases** du dépôt. Double-cliquez dessus, aucune installation nécessaire.
(Windows SmartScreen peut afficher un avertissement : « Informations complémentaires » → « Exécuter quand même ».)

## Utilisation

1. Choisissez la langue source et la langue cible (bouton ⇄ pour inverser).
2. Tapez ou collez le texte, puis **Traduire** (ou `Ctrl+Entrée`).
3. **📋 Copier la traduction** place le résultat dans le presse-papiers.

Une connexion Internet est nécessaire (service Google Traduction).

## Lancer depuis les sources

```
python traduction.py
```

## Construire l'exe

Le workflow GitHub Actions construit l'exe à chaque push. Pour publier une release :

```
git tag v1.0.1 && git push --tags
```

Ou localement sous Windows : `pip install pyinstaller` puis `pyinstaller --onefile --windowed --name Traduction traduction.py`.
