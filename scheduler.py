import requests
import schedule
import time

def make_request():
    url = 'https://lita1-1dhwonog.b4a.run/'
    response = requests.get(url)
    if response.status_code == 200:
        print(f'Requête réussie vers {url}')
    else:
        print(f'Échec de la requête vers {url}')

# Planifiez la fonction make_request pour s'exécuter toutes les 25 minutes
schedule.every(25).minutes.do(make_request)

# Exécutez la planification en boucle
while True:
    schedule.run_pending()
    time.sleep(1)
