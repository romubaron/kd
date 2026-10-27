# Site de Klervi Dalibot

Portfolio de Klervi Dalibot (journaliste, rédactrice, présentatrice). Site statique : `index.html` + `style.css`, aucun build, aucune dépendance.
Développé par Gravity (voir `gravity.yaml`) : une issue = une tâche, avec les sections Goal / Acceptance criteria / Dependencies.

## Règles
- HTML/CSS natif. Pas de framework, pas de npm. JS seulement si le HTML/CSS ne suffit pas, inline et court.
- Texte du site en français. Garder `lang="fr"` et un `<title>` sur chaque page.
- Couleurs via les variables de `:root` dans `style.css` (le mode sombre les redéfinit).
- Mobile d'abord : rien ne doit déborder horizontalement à 360px de large.
- Images dans `images/`, compressées, avec un `alt` descriptif.
- Ne pas inventer de faits sur Klervi : chaque info doit venir d'une source (France 3, Ginkio) ou de l'issue.

## Vérifier
`python3 check.py` (lang, title, liens et ancres locaux). C'est la commande que Gravity et la CI lancent.
Aperçu local : `python3 -m http.server` puis http://localhost:8000.
