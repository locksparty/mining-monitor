# mining-monitor
A simple mining monitor and GPU config like with HiveOS NVtool


# Mining Rig Management Tool

Un outil de gestion de minage qui permet de surveiller et de configurer les paramètres des GPU sur un système. Il fournit des informations sur l'utilisation des ressources système, y compris le CPU, la RAM et les GPU.

## Fonctionnalités

- Affichage des informations système (OS, version, CPU, RAM).
- Surveillance en temps réel de l'utilisation des ressources (CPU, RAM, GPU).
- Configuration des paramètres des GPU (fréquence mémoire et limite de puissance).

## Prérequis

- Python 3.x
- Pilotes NVIDIA installés pour utiliser NVML.

## Installation

Pour installer toutes les dépendances nécessaires, exécutez le script suivant :

chmod +x install.sh
./install.sh
text

### Dépendances

Ce projet nécessite les bibliothèques suivantes :

- `psutil`
- `tabulate`
- `py-cpuinfo`

Ces bibliothèques seront installées automatiquement par le script d'installation.

## Utilisation

Pour exécuter l'outil de gestion de minage, utilisez la commande suivante :

python3 mining_tool_corrected.py
text

### Menu Principal

Le menu principal vous permet de choisir parmi les options suivantes :

1. **View System Information**: Affiche les informations système et les détails des GPU.
2. **Monitor Resource Usage**: Surveille l'utilisation des ressources en temps réel.
3. **Configure GPU Settings**: Configure les paramètres des GPU sélectionnés.
4. **Exit**: Quitte l'application.

## Aide

Si vous avez besoin d'aide ou si vous rencontrez des problèmes, n'hésitez pas à ouvrir une issue sur le dépôt GitHub.

## Contributeurs

Merci à tous ceux qui ont contribué à ce projet !

## License

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.
