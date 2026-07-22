# Cahier des Charges — Logiciel de Gestion MAGMA

| | |
|---|---|
| **Projet** | Logiciel de gestion MAGMA |
| **Client** | Ange Coulibaly |
| **Type d'établissement** | Salle de sport |
| **Version du document** | 1.0 |
| **Date** | 19 juillet 2026 |
| **Statut** | Document de référence pour l'implémentation module par module |

---

## 1. Objet du document

Ce document formalise le cahier des charges transmis par le client pour le développement du
logiciel de gestion **MAGMA**. Il reprend fidèlement les besoins exprimés (champs de données,
tarifs, règles de gestion, fonctionnalités transversales) et sert de **référence unique** pour le
développement, module par module, ainsi que pour le suivi comptable côté client.

Toute évolution ou précision apportée par le client en cours de projet devra être reportée dans
ce document afin qu'il reste la source de vérité du besoin.

---

## 2. Vue d'ensemble des modules

Le logiciel est organisé en **4 modules métier** et un socle de **fonctionnalités
transversales** communes à l'ensemble de l'application.

| # | Module | Objet |
|---|--------|-------|
| 1 | Gestion des clients et séances | Enregistrement des passages et prestations à l'unité |
| 2 | Gestion des abonnements | Souscriptions, suivi des échéances et renouvellements |
| 3 | Gestion de stock | Suivi des entrées/sorties de produits et des fournisseurs |
| 4 | Gestion budgétaire | Suivi des recettes, dépenses et solde de caisse |
| — | Fonctionnalités transversales | Tableau de bord, exports, rapports, accès, sauvegarde |

---

## 3. Module 1 — Gestion des clients et séances

### 3.1 Objectif

Enregistrer chaque passage d'un client à la salle (séance à l'unité) et son mode de paiement,
pour permettre le suivi de la fréquentation et des recettes journalières.

### 3.2 Champs à intégrer

| Champ | Description |
|-------|-------------|
| Date | Date de la séance |
| Nom et prénom du client | Identification du client |
| Contact | Numéro de téléphone du client |
| Type de prestation | Voir grille tarifaire ci-dessous |
| Mode de paiement | Espèces, Mobile Money, etc. |
| Statut du paiement | Payé / En attente |

### 3.3 Grille tarifaire — types de prestation

| Type de prestation | Tarif |
|---------------------|------:|
| Séance simple | 1 000 F |
| Séance + tapis de course | 2 000 F |
| Séance VIP (toutes les machines) | 5 000 F |

---

## 4. Module 2 — Gestion des abonnements

### 4.1 Objectif

Gérer les souscriptions d'abonnement des clients et permettre les relances avant expiration,
afin de faciliter les renouvellements.

### 4.2 Champs à intégrer

| Champ | Description |
|-------|-------------|
| Date de souscription | Date à laquelle l'abonnement est contracté |
| Nom et prénom du client | Identification du client |
| Contact | Numéro de téléphone du client |
| Type d'abonnement | Voir grille tarifaire ci-dessous |
| Date de début | Début de validité de l'abonnement |
| Date d'expiration | Fin de validité — sert de base aux relances |
| Statut | Actif / Expiré |

### 4.3 Grille tarifaire — types d'abonnement

| Type d'abonnement | Tarif |
|--------------------|------:|
| Abonnement standard | 15 000 F |
| Abonnement + tapis de course | 20 000 F |
| Abonnement VIP (toutes les machines) | 25 000 F |

### 4.4 Règle métier

- Le statut de l'abonnement (Actif / Expiré) doit se déduire automatiquement de la date
  d'expiration.
- Une relance de renouvellement doit être possible à l'approche de la date d'expiration.

---

## 5. Module 3 — Gestion de stock

### 5.1 Objectif

Suivre les mouvements de produits (entrées/sorties), leurs fournisseurs et permettre une
alerte en cas de stock faible.

### 5.2 Champs à intégrer

| Champ | Description |
|-------|-------------|
| Nom du produit | Désignation de l'article |
| Quantité en entrée | Quantité réceptionnée |
| Quantité en sortie | Quantité vendue/consommée |
| Date de mouvement | Date de l'entrée ou de la sortie |
| Prix unitaire d'achat | Coût d'achat unitaire |
| Prix unitaire de vente | Prix de vente unitaire, si revente de produits |
| Fournisseur | Fournisseur associé au produit |
| Stock restant | **Calcul automatique** (entrées − sorties) |
| Seuil d'alerte | Stock minimum déclenchant une alerte, si possible |

---

## 6. Module 4 — Gestion budgétaire

### 6.1 Objectif

Suivre l'ensemble des mouvements financiers de la salle (recettes et dépenses) et maintenir
un solde de caisse à jour, pour faciliter le rapprochement avec la comptabilité.

### 6.2 Champs à intégrer

| Champ | Description |
|-------|-------------|
| Date de l'opération | Date du mouvement financier |
| Type d'opération | Entrée d'argent / Sortie d'argent |
| Catégorie | Recette séance, recette abonnement, achat produit, charge, salaire, etc. |
| Montant | Montant de l'opération |
| Mode de paiement | Espèces, Mobile Money, etc. |
| Solde de caisse | **Mise à jour automatique** après chaque opération |

---

## 7. Fonctionnalités transversales

Ces fonctionnalités sont communes à l'ensemble des modules et indispensables au suivi avec la
comptabilité du client.

| Fonctionnalité | Description |
|----------------|--------------|
| Tableau de bord synthétique | Recettes du jour/mois, stock critique, solde de caisse |
| Export des données | Format Excel et/ou PDF, pour la comptabilité |
| Rapports périodiques | Génération journalière, hebdomadaire, mensuelle |
| Gestion des accès | Accès par mot de passe/utilisateur (voir §8.2 — rôles) |
| Sauvegarde des données | Automatique ou régulière |

---

## 8. Correspondance avec la structure technique déjà livrée

Cette section fait le lien entre le besoin exprimé par le client et la structure de base du
projet Django `gestion-magma`, déjà en place et validée.

### 8.1 Modules applicatifs

| Module du cahier des charges | App Django | Statut |
|-------------------------------|------------|--------|
| Gestion des clients et séances | `apps.clients` | Structure de base (placeholder) — à implémenter |
| Gestion des abonnements | `apps.abonnements` | Structure de base (placeholder) — à implémenter |
| Gestion de stock | `apps.stock` | Structure de base (placeholder) — à implémenter |
| Gestion budgétaire | `apps.budget` | Structure de base (placeholder) — à implémenter |
| Gestion des accès (transversal) | `apps.comptes` | Fait — connexion, rôles, affectation des modules |
| Branding établissement (support) | `apps.etablissement` | Fait — nom, logo, paramètres |

### 8.2 Gestion des accès par rôle

La gestion des accès par mot de passe/utilisateur demandée en fonctionnalité transversale est
implémentée avec 3 rôles :

| Rôle | Droits |
|------|--------|
| **Super Administrateur** | Accès complet : tous les modules, gestion des utilisateurs, suppression de comptes, paramètres de l'établissement |
| **Manager** | Mêmes droits de gestion que le Super Administrateur (modules, utilisateurs), sauf suppression de compte et paramètres établissement |
| **Utilisateur** | Accès limité aux modules qui lui sont explicitement attribués |

### 8.3 Fonctionnalités transversales restant à implémenter

- Tableau de bord synthétique (dépend des données des 4 modules métier)
- Exports Excel/PDF
- Rapports périodiques (journalier / hebdomadaire / mensuel)
- Sauvegarde automatique/régulière des données

Ces éléments seront développés une fois les 4 modules métier en place, car ils agrègent leurs
données.

---

## 9. Plan d'implémentation — module par module

L'implémentation suivra l'ordre ci-dessous, chaque module étant validé avec le client avant de
passer au suivant :

1. **Module 1 — Clients & Séances** (§3)
2. **Module 2 — Abonnements** (§4)
3. **Module 3 — Gestion de stock** (§5)
4. **Module 4 — Gestion budgétaire** (§6)
5. **Fonctionnalités transversales** — tableau de bord, exports, rapports, sauvegarde (§7, §8.3)

---

## 10. Annexe — document source

Ce cahier des charges reprend intégralement le contenu du document transmis par le client
(« modules de gestion MAGMA.pdf »), signé Ange Coulibaly, faisant suite à un échange avec le
responsable du projet. Aucune information n'a été ajoutée au-delà de ce qui y est explicitement
demandé ; les sections 8 et 9 relient ce besoin à la structure technique déjà construite et au
planning de mise en œuvre.
