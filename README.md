# IOT Temperature Monitoring System

Un système de monitoring de température en temps réel utilisant un ESP32, MQTT, grafana-postgresql-datasource et Docker.

Ce projet à pour but de savoir grâce au calcul de l'évapotranspiration d'une plante quand est ce qu'il faut l'arroser.

Le calcul de l'évapotranspiration est le suivant 

```
T = temperature
HR = humidity

VPS = 0.6108 * math.exp((17.27 * T/(T + 237.3)))
VPD = VPS * (1 - HR/100)

VPD = évapotranspiration
```

# Cahier des charges

## V1
- [x] Récupération des données du capteur
- [x] Envoie des données vers le serveur MQTT
- [x] Récupération des doonnées du serveur MQTT avec un script python
- [x] Ajout des données dans une base de données Postgres
- [x] Ajout d'une page HTML pour voir les données en db

## V2
- [x] Ajout de grafana dans docker
- [x] Connection de grafana avec postgress
- [ ] Envoie de notification avec un webhook (quand est ce qu'il faut arroser)

## V3
- [ ] Ajouter un écran (I2C)
- [ ] Ajouter une pompe pour simuler l'ouverture de vanne d'eau