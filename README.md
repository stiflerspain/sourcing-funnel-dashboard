# Sourcing Funnel · Dashboard (MLC)

Dashboard **estático** (solo HTML + JSON, sin servidor) para explorar la oferta/competencia
de keywords en MercadoLibre Chile, con historial semanal.

👉 **Ver online:** https://stiflerspain.github.io/sourcing-funnel-dashboard/

## Qué muestra
- **Selector de semana** (las keywords de MeLi se actualizan cada semana → historial).
- **3 flujos de navegación** (botón):
  - **Jerárquico:** categoría raíz → subcategoría → keyword.
  - **Directo:** categoría → keyword.
  - **Por keyword:** lista plana de todas las keywords.
- **Ranking oportunidad-primero**: score 1–5 (5 = poca competencia) según la mediana de
  publicaciones (competidores) de cada nivel.
- Filtros: búsqueda, máx competidores, mín score.

## Estructura
```
index.html              # el dashboard (carga ./data/*.json)
data/
  weeks.json            # índice de semanas disponibles
  <YYYY-Www>/
    results.json        # keywords (keyword, subcategoría, raíz, competidores, score)
    roots.json          # agregado por categoría raíz
    subs.json           # mapa raíz -> subcategorías
    categories.json     # subcategorías planas
build_static.py         # regenera los JSON desde los datos del scraper (no incluye el scraper)
```

## Ver localmente
Por la política de `fetch` del navegador, abrilo con un server (no por `file://`):
```bash
python3 -m http.server 8090
# abrir http://localhost:8090
```

## Actualizar los datos
Los JSON se generan desde el pipeline de scraping (repo aparte). Para regenerar:
```bash
python3 build_static.py   # lee los competitors.jsonl del scraper y reescribe data/
```

> Datos referenciales de MercadoLibre Chile. El score solo ordena; el criterio comercial es tuyo.
