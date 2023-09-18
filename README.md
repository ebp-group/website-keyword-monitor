# website-keyword-monitor

Website Monitoring mit Schlüsselwörtern.
Sobald ein Eintrag auf einer Webseite mit einem der definierten Schlüsselwörter gefunden wird, wird in MS Teams (im [Team CH_P_222110_00 - Standortmonitoring IKEA](https://teams.microsoft.com/l/team/19%3a8yZRxwfaWuzsCdy3K0yPujteVZFYCGsXUlqAZgKNAyM1%40thread.tacv2/conversations?groupId=3a7a934f-46fe-4807-b8a6-066dee8bdd60&tenantId=b2e3a768-93a5-4171-8310-d2fda9465328) im privaten Kanal "Webseiten-Benachrichtigungen") eine entsprechende Benachrichtigung geschickt.


## Schlüsselwöter 

Für alle Webseiten werden dieselben Schlüsselwörter verwendet.
Die Schlüsselwörter (`keyswords`) sind in der Datei [`keywords.txt`](https://github.com/metaodi/website-keyword-monitor/blob/main/keywords.txt) definiert, jeweils ein Schlüsselwort pro Zeile:

```
rue
geschwindigkeit
fermeture de route
Nouvelles mesures
```

## Webseiten

Das CSV muss die folgende Struktur haben:

```
label,active,slug,error_count,url,selector,type,hash
```

* `label`: a label or title of the website
* `active`: used to enable or disable this entry, use values `yes` or `no`
* `slug`: A short name for this entry (must be unique)
* `error_count`: The number of times an error has occured for this entry
* `url`: the actual URL of the website
* `selector`: as CSS selector for elements on the website
* `type`: determines the type of the website, use `static` for static websites or `dynamic` for websites, that load most of their contant at runtime. Dynamic websites will be parsed using Selenium. Use `static` as a default.

Beispiel:

| `label`              | `active` | `slug`        | `error_count` | `url`                                         | `selector`       | `type` |
|----------------------|----------|---------------|---------------|-----------------------------------------------|------------------|--------|
| "Thalwil informiert" | yes      | thalwil_news  | 0             | https://www.thalwil.ch/aktuellesinformationen | #informationList | static |


Webseiten werden im CSV [`all.csv`](https://github.com/metaodi/website-keyword-monitor/blob/main/csv/all.csv) definiert.
