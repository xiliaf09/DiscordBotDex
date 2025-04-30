import sys
import json
import httpx
from datetime import datetime
from typing import Dict, List, Tuple

WARPCAST_API_URL = "https://client.warpcast.com/v2"

def get_user_fid(username: str) -> int:
    """Récupère le FID d'un utilisateur Warpcast à partir de son nom d'utilisateur."""
    response = httpx.get(f"{WARPCAST_API_URL}/user-by-username?username={username}")
    if response.status_code != 200:
        raise Exception(f"Erreur lors de la récupération du FID pour {username}")
    return response.json()["result"]["user"]["fid"]

def get_following_fids(user_fid: int) -> List[Tuple[int, str, str]]:
    """Récupère la liste des FIDs, noms d'utilisateur et noms d'affichage des comptes suivis."""
    following = []
    cursor = None
    
    while True:
        url = f"{WARPCAST_API_URL}/following?fid={user_fid}&limit=100"
        if cursor:
            url += f"&cursor={cursor}"
            
        response = httpx.get(url)
        if response.status_code != 200:
            raise Exception("Erreur lors de la récupération des comptes suivis")
            
        data = response.json()
        users = data["result"]["users"]
        
        for user in users:
            following.append((user["fid"], user["username"], user["displayName"]))
            
        cursor = data["result"].get("next", {}).get("cursor")
        if not cursor:
            break
            
    return following

def save_results(following: List[Tuple[int, str, str]], output_file: str, target_username: str, target_fid: int):
    """Sauvegarde les résultats dans un fichier texte et un fichier JSON."""
    # Sauvegarde des FIDs dans un fichier texte
    with open(output_file, "w") as f:
        for fid, _, _ in following:
            f.write(f"{fid}\n")
            
    # Sauvegarde des métadonnées dans un fichier JSON
    metadata = {
        "target_username": target_username,
        "target_fid": target_fid,
        "total_fids": len(following),
        "timestamp": datetime.now().isoformat(),
        "details": [
            {
                "fid": fid,
                "username": username,
                "display_name": display_name
            }
            for fid, username, display_name in following
        ]
    }
    
    json_file = output_file.rsplit(".", 1)[0] + "_metadata.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

def main():
    if len(sys.argv) != 3:
        print("Usage: python warpcast_scraper.py <username> <output_file>")
        sys.exit(1)
        
    username = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        print(f"Récupération du FID pour l'utilisateur {username}...")
        target_fid = get_user_fid(username)
        
        print(f"Récupération des comptes suivis par {username} (FID: {target_fid})...")
        following = get_following_fids(target_fid)
        
        print(f"\nNombre total de comptes suivis : {len(following)}")
        save_results(following, output_file, username, target_fid)
        
        print(f"\nRésultats sauvegardés dans :")
        print(f"- Liste des FIDs : {output_file}")
        print(f"- Métadonnées : {output_file.rsplit('.', 1)[0]}_metadata.json")
        
    except Exception as e:
        print(f"Erreur : {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 