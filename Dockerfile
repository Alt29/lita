# Utiliser l'image Python officielle en tant qu'image de base
FROM python:3.9

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier le fichier requirements.txt dans le conteneur
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste des fichiers de l'application dans le conteneur
COPY . .

# Exposer le port sur lequel l'application écoute (si nécessaire)
# EXPOSE 8080

# Commande à exécuter lors du démarrage du conteneur
CMD ["python", "a.py"]
