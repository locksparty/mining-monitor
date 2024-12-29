#!/bin/bash

# Mise à jour des paquets
sudo apt-get update

# Installation de Python3 et pip si non installés
sudo apt-get install -y python3 python3-pip

# Installation des dépendances Python
pip3 install psutil tabulate py-cpuinfo --break-system-packages

# Installation des pilotes NVIDIA si non installés
if ! command -v nvidia-smi &> /dev/null
then
    echo "Les pilotes NVIDIA ne sont pas installés. Installation en cours..."
    sudo apt-get install -y nvidia-driver-470
else
    echo "Les pilotes NVIDIA sont déjà installés."
fi

echo "Installation terminée. Vous pouvez maintenant exécuter l'outil de gestion de minage."

