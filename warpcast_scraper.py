import requests
import json
import sys
from datetime import datetime

WARPCAST_API_URL = "https://client.warpcast.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json"
}

def test_api_connection():
    """Test the connection to the Warpcast API."""
    try:
        # Try to get the channels list as a test (public endpoint)
        response = requests.get(f"{WARPCAST_API_URL}/v2/all-channels", headers=HEADERS)
        if response.status_code == 200:
            print("✅ Connection à l'API Warpcast réussie!")
            return True
        else:
            print(f"❌ Erreur lors de la connexion à l'API. Code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de la connexion à l'API: {str(e)}")
        return False

def get_user_fid(username):
    """Get the FID of a user by their username."""
    try:
        response = requests.get(f"{WARPCAST_API_URL}/v2/user-search?q={username}", headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            if data.get('result', {}).get('users'):
                return data['result']['users'][0]['fid']
        return None
    except Exception:
        return None

def get_following_fids(username):
    """Get the FIDs of all accounts followed by a user."""
    print(f"📥 Récupération des comptes suivis par @{username}...")
    
    user_fid = get_user_fid(username)
    if not user_fid:
        print(f"❌ Impossible de trouver l'utilisateur {username}")
        return []

    try:
        all_following = []
        offset = 0
        limit = 100  # Nombre maximum de résultats par requête
        
        while True:
            response = requests.get(
                f"{WARPCAST_API_URL}/v2/following",
                params={
                    "fid": user_fid,
                    "limit": limit,
                    "offset": offset
                },
                headers=HEADERS
            )
            
            if response.status_code != 200:
                print(f"❌ Erreur lors de la récupération des following. Code: {response.status_code}")
                return []
                
            data = response.json()
            users = data['result'].get('users', [])
            
            if not users:
                break
                
            all_following.extend(users)
            print(f"📥 Récupération en cours... {len(all_following)} comptes trouvés", end='\r')
            
            # Si on a reçu moins que la limite, c'est qu'on a tout récupéré
            if len(users) < limit:
                break
                
            offset += limit
            
        print(f"📥 Récupération en cours... {len(all_following)} comptes trouvés")
            
        # Extract FIDs and metadata
        fids_data = []
        for user in all_following:
            fids_data.append({
                'fid': user['fid'],
                'username': user['username'],
                'displayName': user['displayName']
            })
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save just FIDs to a text file
        with open(f'fids_{username}_{timestamp}.txt', 'w') as f:
            for user in fids_data:
                f.write(f"{user['fid']}\n")
        
        # Save complete data to JSON
        with open(f'fids_data_{username}_{timestamp}.json', 'w') as f:
            json.dump({
                'source_user': username,
                'total_following': len(fids_data),
                'timestamp': timestamp,
                'users': fids_data
            }, f, indent=2)
        
        print(f"✅ {len(fids_data)} FIDs extraits et sauvegardés!")
        return fids_data
            
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des following: {str(e)}")
        return []

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python warpcast_scraper.py <username|test>")
        sys.exit(1)
        
    command = sys.argv[1]
    
    if command == "test":
        test_api_connection()
    else:
        get_following_fids(command) 