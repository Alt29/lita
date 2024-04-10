# Utilisez l'image Python officielle comme base
FROM python:3.9-slim

# Définissez le répertoire de travail dans le conteneur
WORKDIR /app

# Copiez le fichier requirements.txt contenant les dépendances de votre application
COPY requirements.txt .

# Installez les dépendances de votre application
RUN pip install -r requirements.txt

# Copiez tous les fichiers de votre application dans le répertoire de travail du conteneur
COPY . .

# Démarrez votre application en utilisant la commande python
CMD ["python", "a.py"]
