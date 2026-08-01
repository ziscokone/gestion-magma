from datetime import date, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.shortcuts import render
from django.views import View

from apps.abonnements.models import Abonnement
from apps.budget.models import OperationBudget
from apps.clients.models import Client, Seance
from apps.clients.services import PALETTE, repartition_clients_par_zone
from apps.stock.models import Produit, Vente

JOURS_RENOUVELLEMENT = 7
JOURS_TENDANCE = 7

# Couleurs de la tendance/composition — mêmes teintes que les puces de module
# du hub, pour que la source d'un chiffre se reconnaisse au coup d'œil.
COULEUR_SEANCES = '#2f5fa8'
COULEUR_BOUTIQUE = '#b8791a'
COULEUR_ABONNEMENTS = '#0f8b8d'

# Géométrie du graphique de tendance (SVG, viewBox 0 0 720 200)
CHART_X0, CHART_X1 = 20, 700
CHART_Y_TOP, CHART_Y_BASE = 20, 170


class TableauDeBordView(LoginRequiredMixin, View):
    template_name = 'dashboard/accueil.html'

    def get(self, request):
        today = date.today()
        hier = today - timedelta(days=1)

        # --- Clients (la répartition par zone donne déjà le total, pas la peine de recompter) ---
        zones = repartition_clients_par_zone(max_parts=4, rayon=54)
        total_clients = zones['total_clients']
        nouveaux_clients_mois = Client.objects.filter(
            date_creation__year=today.year, date_creation__month=today.month
        ).count()

        # --- Caisse / recettes / dépenses — source unique : OperationBudget,
        # alimenté automatiquement par les séances, ventes et abonnements. ---
        solde_caisse = OperationBudget.solde_caisse()
        ops_jour = OperationBudget.objects.filter(date__date=today)
        ops_hier = OperationBudget.objects.filter(date__date=hier)
        ops_mois = OperationBudget.objects.filter(date__year=today.year, date__month=today.month)

        recette_jour = sum(o.montant for o in ops_jour.filter(type_operation='entree'))
        depense_jour = sum(o.montant for o in ops_jour.filter(type_operation='sortie'))
        recette_hier = sum(o.montant for o in ops_hier.filter(type_operation='entree'))
        recette_mois = sum(o.montant for o in ops_mois.filter(type_operation='entree'))
        depense_mois = sum(o.montant for o in ops_mois.filter(type_operation='sortie'))

        delta_recette_jour = round((recette_jour - recette_hier) * 100 / recette_hier, 1) if recette_hier else None

        mois_prec = today.month - 1 or 12
        annee_prec = today.year - 1 if today.month == 1 else today.year
        depense_mois_dernier = sum(o.montant for o in OperationBudget.objects.filter(
            date__year=annee_prec, date__month=mois_prec, type_operation='sortie'
        ))
        delta_depense_mois = (
            round((depense_mois - depense_mois_dernier) * 100 / depense_mois_dernier, 1)
            if depense_mois_dernier else None
        )

        # --- Composition des recettes du jour (séances / boutique / abonnements) ---
        totaux_categorie = dict(
            ops_jour.filter(type_operation='entree').values('categorie').annotate(total=Sum('montant'))
            .values_list('categorie', 'total')
        )
        composition_jour = []
        for categorie, couleur, libelle in (
            ('recette_seance', COULEUR_SEANCES, 'Séances'),
            ('vente_produit', COULEUR_BOUTIQUE, 'Boutique'),
            ('recette_abonnement', COULEUR_ABONNEMENTS, 'Abonnements'),
        ):
            montant = totaux_categorie.get(categorie, 0)
            if montant:
                composition_jour.append({'libelle': libelle, 'montant': montant, 'couleur': couleur})
        for part in composition_jour:
            part['pourcentage'] = round(part['montant'] * 100 / recette_jour, 1) if recette_jour else 0

        # --- Tendance des recettes sur 7 jours (aire + ligne) ---
        debut_semaine = today - timedelta(days=JOURS_TENDANCE - 1)
        totaux_par_jour = {}
        for ligne in OperationBudget.objects.filter(
            date__date__gte=debut_semaine, date__date__lte=today, type_operation='entree'
        ).values('date__date').annotate(total=Sum('montant')):
            totaux_par_jour[ligne['date__date']] = ligne['total']

        JOURS_ABBR = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
        tendance = []
        for i in range(JOURS_TENDANCE):
            jour = debut_semaine + timedelta(days=i)
            tendance.append({
                'jour': jour,
                'label': JOURS_ABBR[jour.weekday()],
                'montant': totaux_par_jour.get(jour, 0),
                'est_aujourdhui': jour == today,
            })
        recette_semaine = sum(j['montant'] for j in tendance)

        valeur_max = max((j['montant'] for j in tendance), default=0) or 1
        plage = valeur_max * 1.15
        largeur_pas = (CHART_X1 - CHART_X0) / (len(tendance) - 1) if len(tendance) > 1 else 0
        for i, j in enumerate(tendance):
            # Chaînes déjà formatées : un rendu Django en locale fr affiche les
            # décimales avec une virgule, ce qui casse les attributs SVG (x/y).
            y_val = CHART_Y_BASE - (j['montant'] / plage) * (CHART_Y_BASE - CHART_Y_TOP)
            j['x'] = f"{CHART_X0 + i * largeur_pas:.1f}"
            j['y'] = f"{y_val:.1f}"
            j['y_label'] = f"{y_val - 17:.1f}"
        points_ligne = ' '.join(f"{j['x']},{j['y']}" for j in tendance)
        aire_chemin = (
            f"M{tendance[0]['x']},{CHART_Y_BASE} "
            + ' '.join(f"L{j['x']},{j['y']}" for j in tendance)
            + f" L{tendance[-1]['x']},{CHART_Y_BASE} Z"
        )

        # --- Abonnements à renouveler bientôt ---
        abonnements_qs = Abonnement.objects.select_related('client', 'type_abonnement').filter(
            date_fin__gte=today, date_fin__lte=today + timedelta(days=JOURS_RENOUVELLEMENT)
        ).order_by('date_fin')
        nb_abonnements_a_renouveler = abonnements_qs.count()

        # --- Alertes stock (calculé en Python : stock_actuel n'est pas un
        # champ stocké, donc pas filtrable directement en SQL) ---
        produits_stock_faible = sorted(
            (p for p in Produit.objects.filter(actif=True) if p.stock_faible),
            key=lambda p: p.stock_actuel,
        )
        nb_produits_stock_faible = len(produits_stock_faible)

        # --- Séances impayées ---
        seances_impayees_qs = Seance.objects.select_related('client').filter(
            statut_paiement='en_attente'
        ).order_by('-date')
        nb_seances_impayees = seances_impayees_qs.count()

        # --- Statut d'abonnement des clients : qui est un membre actif, qui
        # ne l'est pas (jamais abonné ou abonnement expiré) — pour repérer
        # les clients à convertir vers un abonnement. ---
        clients_avec_abo_ids = set(
            Abonnement.objects.filter(date_fin__gte=today).values_list('client_id', flat=True).distinct()
        )
        nb_clients_avec_abo = len(clients_avec_abo_ids)
        nb_clients_sans_abo = total_clients - nb_clients_avec_abo
        pct_avec_abo = round(nb_clients_avec_abo * 100 / total_clients, 1) if total_clients else 0
        pct_sans_abo = round(nb_clients_sans_abo * 100 / total_clients, 1) if total_clients else 0
        # Les plus assidus d'abord : ce sont les meilleurs candidats à la conversion.
        clients_sans_abo = list(
            Client.objects.exclude(pk__in=clients_avec_abo_ids)
            .annotate(nb_seances_total=Count('seances'))
            .order_by('-nb_seances_total', 'nom_complet')[:5]
        )

        # --- Top clients du mois, par nombre de séances ---
        top_clients = list(Client.objects.annotate(
            nb_seances_mois=Count('seances', filter=Q(
                seances__date__year=today.year, seances__date__month=today.month
            ))
        ).filter(nb_seances_mois__gt=0).order_by('-nb_seances_mois', 'nom_complet')[:5])
        for i, client in enumerate(top_clients):
            mots = client.nom_complet.split()
            client.initiales = (mots[0][0] + mots[-1][0]).upper() if len(mots) > 1 else client.nom_complet[:2].upper()
            client.couleur = PALETTE[i % len(PALETTE)]

        # --- Activité récente, fil combiné tous modules ---
        activites = []
        for s in Seance.objects.select_related('client', 'type_prestation').order_by('-date')[:5]:
            activites.append({
                'date': s.date, 'couleur': COULEUR_SEANCES,
                'texte': f"{s.client.nom_complet} a enregistré une séance de {s.type_prestation.nom}",
            })
        for v in Vente.objects.order_by('-date')[:5]:
            activites.append({
                'date': v.date, 'couleur': COULEUR_BOUTIQUE,
                'texte': f"Vente boutique — {v.numero_vente}", 'montant': v.montant_total,
            })
        for a in Abonnement.objects.select_related('client', 'type_abonnement').order_by('-date_souscription')[:5]:
            activites.append({
                'date': a.date_souscription, 'couleur': COULEUR_ABONNEMENTS,
                'texte': f"{a.client.nom_complet} a souscrit {a.type_abonnement.nom}",
            })
        for c in Client.objects.order_by('-date_creation')[:5]:
            activites.append({
                'date': c.date_creation, 'couleur': '#6b3fa0',
                'texte': f"Nouveau client — {c.nom_complet} inscrit",
            })
        activites.sort(key=lambda a: a['date'], reverse=True)
        activites = activites[:6]

        return render(request, self.template_name, {
            'today': today,
            'total_clients': total_clients,
            'nouveaux_clients_mois': nouveaux_clients_mois,
            'solde_caisse': solde_caisse,
            'recette_jour': recette_jour,
            'depense_jour': depense_jour,
            'delta_recette_jour': delta_recette_jour,
            'recette_mois': recette_mois,
            'depense_mois': depense_mois,
            'delta_depense_mois': delta_depense_mois,
            'nb_seances_jour': Seance.objects.filter(date__date=today).count(),
            'nb_ventes_jour': Vente.objects.filter(date__date=today).count(),
            'nb_renouvellements_jour': Abonnement.objects.filter(date_souscription__date=today).count(),
            'composition_jour': composition_jour,
            'tendance': tendance,
            'recette_semaine': recette_semaine,
            'points_ligne': points_ligne,
            'aire_chemin': aire_chemin,
            'chart_y_base': CHART_Y_BASE,
            'dernier_point': tendance[-1],
            'abonnements_a_renouveler': abonnements_qs[:5],
            'nb_abonnements_a_renouveler': nb_abonnements_a_renouveler,
            'produits_stock_faible': produits_stock_faible[:5],
            'nb_produits_stock_faible': nb_produits_stock_faible,
            'seances_impayees': seances_impayees_qs[:5],
            'nb_seances_impayees': nb_seances_impayees,
            'top_clients': top_clients,
            'activites': activites,
            'zones': zones,
            'nb_clients_avec_abo': nb_clients_avec_abo,
            'nb_clients_sans_abo': nb_clients_sans_abo,
            'pct_avec_abo': pct_avec_abo,
            'pct_sans_abo': pct_sans_abo,
            'clients_sans_abo': clients_sans_abo,
        })
