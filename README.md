[![Check all websites](https://github.com/ebp-group/website-keyword-monitor/actions/workflows/all.yml/badge.svg)](https://github.com/ebp-group/website-keyword-monitor/actions/workflows/all.yml)

# website-keyword-monitor

Website Monitoring mit Schlüsselwörtern, implementiert in Python und GitHub Actions.

## Schlüsselwörter 

Die Schlüsselwörter (`keywords`) sind in Textdateien im Ordner [`keywords`](https://github.com/ebp-group/website-keyword-monitor/tree/main/keywords) definiert, jeweils ein Schlüsselwort pro Zeile.
Jedes Schlüsselwort wird als [regulärer Ausdruck](https://danielfett.de/2006/03/20/regulaere-ausdruecke-tutorial/) (Regex) interpretiert, so lassen sich auch komplexere Begriffe in Texten finden.

Beispiel-Datei: 
```
rue
geschwindigkeit
fermeture de route
Nouvelles mesures
Plan d[’']affectation
(?:Dévelopment)\s+(?:urbaine|de la ville|de la commune|du quartier)?
```

## Webseiten

Das CSV muss die folgende Struktur haben:

```
label,active,slug,error_count,url,timeout,type
```

* `label`: a label or title of the website
* `active`: used to enable or disable this entry, use values `yes` or `no`
* `slug`: A short name for this entry (must be unique)
* `error_count`: The number of times an error has occured for this entry
* `url`: the actual URL of the website
* `timeout`: timeout in seconds to wait until a webpage is loaded (only for dynamic websites)
* `type`: determines the type of the website, use `static` for static websites or `dynamic` for websites, that load most of their contant at runtime. Dynamic websites will be parsed using Selenium. Use `static` as a default.

Beispiel:

| `label`              | `active` | `slug`        | `error_count` | `url`                                         | `timeout`     | `type` |
|----------------------|----------|---------------|---------------|-----------------------------------------------|---------------|--------|
| "Thalwil informiert" | yes      | thalwil_news  | 0             | https://www.thalwil.ch/aktuellesinformationen | 5             | static |


Webseiten werden im Ordner [`csv`](https://github.com/ebp-group/website-keyword-monitor/blob/main/csv) definiert.

## Benachrichtigungen in MS Teams

Sobald ein Eintrag auf einer Webseite mit einem der definierten Schlüsselwörter gefunden wird, wird in MS Teams (im [Team CH_P_222110_00 - Standortmonitoring](https://teams.microsoft.com/l/team/19%3a8yZRxwfaWuzsCdy3K0yPujteVZFYCGsXUlqAZgKNAyM1%40thread.tacv2/conversations?groupId=3a7a934f-46fe-4807-b8a6-066dee8bdd60&tenantId=b2e3a768-93a5-4171-8310-d2fda9465328) im privaten Kanal "Webseiten-Benachrichtigungen") eine entsprechende Benachrichtigung geschickt.

Der MS Teams Kanal wird über einen sogenannten "Incoming Webhook" angesprochen.
In Teams kann in einem Kanal ein neuer Connector "Incoming Webhook" hinzugefügt werden.

![Connector in Teams](https://github.com/ebp-group/website-keyword-monitor/assets/538415/b3be5355-00d5-4d12-aad3-8cf2aa3df8ec)

![Incomeing Webhook Connector](https://github.com/metaodi/website-keyword-monitor/assets/538415/272e0b9f-808e-4c6b-b1a5-ea1305879d92)

Die generierte URL muss dann auf GitHub als [Secret](https://github.com/ebp-group/website-keyword-monitor/settings/secrets/actions) mit dem Namen `MS_TEAMS_WEBHOOK_URL` gespeichert werden.


## GitHub Actions

GitHub Actions steuert die ganze Ausführung des Workflows.

Die Actions brauchen **Schreibberechtigungen** um Commits erstellen zu können:

![Schreibberechtigungen für Actions](https://github.com/metaodi/website-keyword-monitor/assets/538415/bc0ff7d4-d5b1-4bbd-a97b-ea3145216d9b)

