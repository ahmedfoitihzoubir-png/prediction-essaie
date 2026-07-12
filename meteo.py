import streamlit as st
import pandas as pd
import re
import sys

# ------------------------------------------------------------------
# MODE : DEMO (données simulées) ou RÉEL (API Facebook)
# ------------------------------------------------------------------
DEMO = True   # <-- passez à False une fois votre token Facebook prêt

# ------------------------------------------------------------------
# CONFIGURATION - à adapter (mode RÉEL uniquement)
# ------------------------------------------------------------------
PAGE_ID = "100093054514209"
ACCESS_TOKEN = "VOTRE_ACCESS_TOKEN"

# Option A : ID exact de la publication (format PAGE_ID_POSTID)
POST_ID = None

# Option B : mot-clé unique du texte de la publication, pour la retrouver
# automatiquement parmi les publications récentes (utile si vous n'avez
# qu'un lien de partage facebook.com/share/p/...)
MOT_CLE_RECHERCHE = "un mot du texte de la publication"

GRAPH_API_VERSION = "v19.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
MAX_POSTS_RECHERCHE = 30


# ------------------------------------------------------------------
# DONNÉES D'EXEMPLE (utilisées uniquement si DEMO = True)
# ------------------------------------------------------------------
PUBLICATION_EXEMPLE = {
    "id": "100093054514209_exemple123",
    "message": "Découvrez notre nouvelle collection disponible dès aujourd'hui en magasin et en ligne !",
    "created_time": "2026-07-10T09:00:00+0000"
}

COMMENTAIRES_EXEMPLE = [
    {"auteur": "Amine B.", "date": "2026-07-10T09:15:00", "texte": "Super collection, j'adore les couleurs ! Bravo à toute l'équipe."},
    {"auteur": "Sarah M.", "date": "2026-07-10T09:20:00", "texte": "Livraison catastrophique la dernière fois, jamais reçu ma commande."},
    {"auteur": "Karim T.", "date": "2026-07-10T09:32:00", "texte": "Merci pour la qualité, toujours aussi impeccable !"},
    {"auteur": "Leïla H.", "date": "2026-07-10T10:01:00", "texte": "C'est disponible en quelle taille ?"},
    {"auteur": "Yacine R.", "date": "2026-07-10T10:15:00", "texte": "Déçu par le service client, aucune réponse depuis 3 jours."},
    {"auteur": "Nadia F.", "date": "2026-07-10T10:40:00", "texte": "Franchement le meilleur rapport qualité prix, je recommande à 100%."},
    {"auteur": "Omar D.", "date": "2026-07-10T11:02:00", "texte": "Arnaque totale, produit reçu abîmé et remboursement refusé."},
    {"auteur": "Ines K.", "date": "2026-07-10T11:20:00", "texte": "Trop cher pour la qualité proposée, très mauvaise expérience."},
    {"auteur": "Walid S.", "date": "2026-07-10T11:45:00", "texte": "Génial, exactement ce que je cherchais, livraison rapide en plus !"},
    {"auteur": "Amel Z.", "date": "2026-07-10T12:10:00", "texte": "Vous ouvrez à quelle heure demain ?"},
]


# ------------------------------------------------------------------
# MODE RÉEL : APPELS À L'API GRAPH FACEBOOK
# ------------------------------------------------------------------
def verifier_token(access_token):
    import requests
    url = f"{BASE_URL}/me"
    params = {"access_token": access_token, "fields": "id,name"}
    data = requests.get(url, params=params).json()

    if "error" in data:
        print("Le token d'accès est invalide ou a expiré.")
        print("Détail Facebook :", data["error"].get("message"))
        print("\n-> Régénérez un Page Access Token via Graph API Explorer :")
        print("   https://developers.facebook.com/tools/explorer/")
        return False

    print(f"Token valide, connecté en tant que : {data.get('name')} (id: {data.get('id')})")
    return True


def trouver_post_par_mot_cle(page_id, access_token, mot_cle, limit=MAX_POSTS_RECHERCHE):
    import requests
    url = f"{BASE_URL}/{page_id}/posts"
    params = {
        "access_token": access_token,
        "limit": limit,
        "fields": "id,message,created_time,permalink_url"
    }
    mot_cle_normalise = mot_cle.lower().strip()

    while url:
        data = requests.get(url, params=params).json()

        if "error" in data:
            print("Erreur API (recherche de publication) :", data["error"].get("message"))
            return None

        for post in data.get("data", []):
            texte = (post.get("message") or "").lower()
            if mot_cle_normalise and mot_cle_normalise in texte:
                print(f"Publication trouvée : {post['id']} ({post.get('created_time')})")
                print(f"Extrait : {post.get('message', '')[:120]}...")
                return post["id"]

        paging = data.get("paging", {})
        url = paging.get("next")
        params = {}

    print("Aucune publication correspondant au mot-clé n'a été trouvée.")
    return None


def get_comments_reels(post_id, access_token):
    import requests
    url = f"{BASE_URL}/{post_id}/comments"
    params = {
        "access_token": access_token,
        "fields": "id,message,created_time,from",
        "filter": "stream",
        "limit": 100
    }
    comments = []
    while url:
        data = requests.get(url, params=params).json()

        if "error" in data:
            print("Erreur API (commentaires) :", data["error"].get("message"))
            break

        comments.extend(data.get("data", []))
        paging = data.get("paging", {})
        url = paging.get("next")
        params = {}

    lignes = []
    for c in comments:
        lignes.append({
            "auteur": c.get("from", {}).get("name", "inconnu"),
            "date": c.get("created_time"),
            "texte": c.get("message", "")
        })
    return lignes


# ------------------------------------------------------------------
# ANALYSE DE SENTIMENT (approche par mots-clés, identique dans les 2 modes)
# ------------------------------------------------------------------
MOTS_SATISFACTION = [
    "merci", "excellent", "génial", "super", "top", "bravo", "parfait",
    "content", "contente", "satisfait", "satisfaite", "j'adore", "j adore",
    "au top", "recommande", "recommandé", "impeccable", "rapide", "efficace",
    "professionnel", "agréable", "meilleur", "incroyable", "magnifique",
    "bien joué", "5 étoiles", "cool", "sympa"
]

MOTS_MECONTENTEMENT = [
    "déçu", "deçu", "déçue", "nul", "arnaque", "honteux", "scandale",
    "mauvais", "mauvaise", "horrible", "catastrophe", "insatisfait",
    "insatisfaite", "jamais", "problème", "probleme", "lent", "cher",
    "inadmissible", "incompétent", "incompetent", "remboursement",
    "plainte", "colère", "colere", "inacceptable", "pire", "regrette",
    "annulé", "annule", "attente", "sans réponse", "sans reponse", "raté",
    "abimé", "abîmé", "refusé"
]


def nettoyer_texte(texte):
    texte = texte.lower()
    texte = re.sub(r"[^\w\sàâäéèêëîïôöùûüç']", " ", texte)
    return texte


def analyser_sentiment(texte):
    """Classe un commentaire en satisfaction / mécontentement / neutre."""
    if not texte:
        return "neutre"

    texte_propre = nettoyer_texte(texte)

    score_positif = sum(1 for mot in MOTS_SATISFACTION if mot in texte_propre)
    score_negatif = sum(1 for mot in MOTS_MECONTENTEMENT if mot in texte_propre)

    if score_positif > score_negatif:
        return "satisfaction"
    elif score_negatif > score_positif:
        return "mécontentement"
    else:
        return "neutre"


# ------------------------------------------------------------------
# PROGRAMME PRINCIPAL
# ------------------------------------------------------------------
def main():
    if DEMO:
        print(">>> MODE DÉMONSTRATION (données simulées) <<<\n")
        publication = PUBLICATION_EXEMPLE
        commentaires = COMMENTAIRES_EXEMPLE
    else:
        print(">>> MODE RÉEL (API Facebook) <<<\n")
        if not verifier_token(ACCESS_TOKEN):
            sys.exit(1)

        post_id = POST_ID
        if not post_id:
            print(f"\nAucun POST_ID fourni : recherche par mot-clé \"{MOT_CLE_RECHERCHE}\"...")
            post_id = trouver_post_par_mot_cle(PAGE_ID, ACCESS_TOKEN, MOT_CLE_RECHERCHE)

        if not post_id:
            print("Impossible de déterminer la publication à analyser. "
                  "Renseignez POST_ID directement ou ajustez MOT_CLE_RECHERCHE.")
            sys.exit(1)

        publication = {"id": post_id, "message": "(récupéré via l'API)", "created_time": ""}
        commentaires = get_comments_reels(post_id, ACCESS_TOKEN)

    print("=== Publication analysée ===")
    print(f"ID    : {publication['id']}")
    if publication.get("message"):
        print(f"Texte : {publication['message']}")
    print()

    df = pd.DataFrame(commentaires)

    if df.empty:
        print("Aucun commentaire trouvé.")
        return

    df["sentiment"] = df["texte"].apply(analyser_sentiment)

    print("=== Détail des commentaires ===")
    for _, ligne in df.iterrows():
        print(f"[{ligne['sentiment'].upper():15}] {ligne['auteur']:12} : {ligne['texte']}")

    nom_fichier = "commentaires_exemple_analyses.csv" if DEMO else "commentaires_publication.csv"
    df.to_csv(nom_fichier, index=False, encoding="utf-8-sig")
    print(f"\nRésultats exportés dans {nom_fichier}")

    print("\n=== Résumé ===")
    print(df["sentiment"].value_counts())

    total = len(df)
    satisfaction = (df["sentiment"] == "satisfaction").sum()
    mecontentement = (df["sentiment"] == "mécontentement").sum()
    print(f"\nTaux de satisfaction    : {satisfaction / total * 100:.0f}%")
    print(f"Taux de mécontentement  : {mecontentement / total * 100:.0f}%")


if __name__ == "__main__":
    main()
