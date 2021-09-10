# ENT API
Un script Python qui récupère certaines données utilisateurs depuis l'ENT

## Librairies requises
* ``Python 3.6+``
* ``tqdm``
* ``requests``

## Usage
```sh
python3 entapi.py
```

## Fonctionnalités

### Téléchargement de l'annuaire
Téléchargement automatique de l'annuaire depuis l'ENT

### Accès à l'annuaire
* Recherche par nom
* Recherche par classe (division)
* Recherche par groupe (spécialités / langues)
* Recherche par matière (matières étudiées par l'élève)

### Données accessibles

#### Professeurs
* Nom
* Date de naissance
* Identifiant ENT
* Mail ENT
* Classe dont il est le professeur principal (le cas échéant)
* Matières enseignées

#### Élèves
* Nom
* Date de naissance
* Identifiant ENT
* Mail ENT
* Niveau de classe (ex: Terminale, Première...)
* Division de classe
* Groupes (spécialités / langues)
* Matières étudiées

#### Classes / Groupes
* Liste des élèves
* Professeur principal / Professeur du groupe
