# Machine Prediction API

## Base URL

⚠️ Replace `localhost:PORT` based on your environment:
- **Development** (`uv run dev`): `http://localhost:8000`
- **Docker** (`docker compose up`): `http://localhost:8080`
- **Deployed**: Cloud service URL

## Endpoint

```
GET /api/machine/{machine_id}/prediction
```

## Description

Cette route permet de prédire la disponibilité d'une machine de fitness à un moment donné. Elle peut être utilisée de deux façons :

1. **Mode Présent** : Sans paramètres de date/heure, retourne l'état actuel de la machine
2. **Mode Futur** : Avec paramètres `day` et `time`, prédit la disponibilité future basée sur l'historique

---

## Paramètres

### Path Parameters

| Paramètre | Type | Requis | Description |
|-----------|------|--------|-------------|
| `machine_id` | string | ✅ | Identifiant unique de la machine (ex: `DC_BENCH_001`) |

### Query Parameters

| Paramètre | Type | Requis | Description | Exemple |
|-----------|------|--------|-------------|---------|
| `day` | string | ❌ | Jour de la semaine (en anglais) | `thursday` |
| `time` | string | ❌ | Heure au format HH:MM | `14:00` |

> ⚠️ **Important** : `day` et `time` doivent être fournis ensemble ou pas du tout.

### Valeurs acceptées pour `day`

- `monday`
- `tuesday`
- `wednesday`
- `thursday`
- `friday`
- `saturday`
- `sunday`

---

## Comportement

### Mode Présent (sans day/time)

```
GET /api/machine/DC_BENCH_001/prediction
```

L'API vérifie dans la base de données simulée si la machine est actuellement utilisée :

1. Recherche d'une activité en cours (`end_time = null`) pour le capteur de cette machine
2. Si **libre** → retourne `available: true, time_to_wait: 0`
3. Si **occupée** → calcule le temps restant estimé basé sur :
   - L'heure de début de l'activité en cours
   - La durée moyenne historique des sessions précédentes

### Mode Futur (avec day/time)

```
GET /api/machine/DC_BENCH_001/prediction?day=thursday&time=14:00
```

L'API prédit la disponibilité basée sur les patterns historiques :

1. Récupère le taux d'occupation historique pour ce jour/heure
2. Si probabilité < 60% → prédit `available: true`
3. Si probabilité ≥ 60% → prédit `available: false` et estime le temps d'attente

### Datetime dans le passé

Si le jour/heure spécifié est dans le passé (par rapport à maintenant), l'API retourne une **erreur 400**.

---

## Réponses

### ✅ Succès (200)

```json
{
  "status": true,
  "data": {
    "available": false,
    "time_to_wait": 5
  },
  "request_type": "present",
  "message": "Machine currently in use. Based on historical average session duration of 11.0 minutes, estimated 5 minutes remaining."
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `status` | boolean | `true` si la requête a réussi |
| `data.available` | boolean | `true` si la machine est/sera disponible |
| `data.time_to_wait` | integer | Minutes d'attente estimées (0 si disponible) |
| `request_type` | string | `"present"` ou `"future"` |
| `message` | string | Message explicatif optionnel |

### ❌ Erreur 400 - Paramètres invalides

```json
{
  "status": false,
  "error": "Invalid parameters",
  "detail": "Both 'day' and 'time' must be provided together, or neither."
}
```

### ❌ Erreur 400 - Datetime passé

```json
{
  "status": false,
  "error": "Invalid datetime",
  "detail": "Cannot query past datetime. Please provide a future datetime or omit for current state."
}
```

### ❌ Erreur 404 - Machine non trouvée

```json
{
  "status": false,
  "error": "Machine not found",
  "detail": "Machine 'INVALID_ID' not found"
}
```

---

## Exemples d'utilisation

### Vérifier l'état actuel d'une machine

```bash
curl -X GET "http://localhost:8000/api/machine/DC_BENCH_001/prediction"
```

### Prédire la disponibilité jeudi à 14h

```bash
curl -X GET "http://localhost:8000/api/machine/DC_BENCH_001/prediction?day=thursday&time=14:00"
```

### Lister toutes les machines disponibles

```bash
curl -X GET "http://localhost:8000/api/machine/list"
```

---

## Algorithme de prédiction

### Pour le mode Présent

1. **Détection d'occupation** : Vérifie `sensor_activity` pour une activité sans `end_time`
2. **Calcul du temps restant** :
   - Récupère les durées des sessions passées depuis `set_summary`
   - Calcule la moyenne des durées
   - `temps_restant = durée_moyenne - temps_écoulé`

### Pour le mode Futur

1. **Probabilité d'occupation** : Consulte `historical_usage_patterns` pour le jour/heure
2. **Seuil de décision** : Si probabilité ≥ 60% → machine considérée comme occupée
3. **Estimation d'attente** : Basée sur la durée moyenne des sessions × facteur de probabilité

---

## Machines disponibles (données simulées)

| Machine ID | Description |
|------------|-------------|
| `DC_BENCH_001` | Banc de développé couché |
| `SQUAT_RACK_001` | Rack à squat |
| `LEG_PRESS_001` | Presse à jambes |

---

## Use Case - Intégration Frontend

```
Frontend → Backend API → Predict API (cette API) → Réponse
```

1. L'utilisateur est sur l'app, son prochain exercice est DC (développé couché)
2. Il a besoin d'un banc dans 15 minutes, soit 14h00 un jeudi
3. Le frontend demande au Backend API
4. Backend API demande à **Predict API** : `GET /machine/DC_BENCH_001/prediction?day=thursday&time=14:00`
5. Predict API répond : `{status: true, data: {available: false, time_to_wait: 5}}`
6. Backend API traite : si `time_to_wait > threshold` → propose un exercice alternatif
