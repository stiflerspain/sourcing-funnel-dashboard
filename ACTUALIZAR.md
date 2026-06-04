# Runbook — Actualizar el dashboard (lo ejecuta Claude)

> Álvaro no corre esto a mano. Cuando diga *"actualizá el dashboard"* / *"subí la semana nueva"*,
> Claude ejecuta estos pasos.

## Precondición
La semana nueva ya tiene que estar scrapeada en el repo del scraper:
`~/Dev/Proyectos/meli-market-scraper/experimentos/sourcing-funnel/data/weeks/<YYYY-Www>/competitors.jsonl`

(Si no está, primero correr el scraper — ver `ESTADO.md` de ese repo.)

## Pasos

1. Regenerar los JSON estáticos desde los datos del scraper:
```bash
cd ~/Dev/Proyectos/sourcing-funnel-dashboard
/Users/alvaro/Dev/Proyectos/meli-market-scraper/.venv/bin/python build_static.py
```
   Esto reescribe `data/weeks.json` y `data/<semana>/{results,roots,subs,categories}.json`
   para TODAS las semanas presentes en el scraper (incluye el historial).

2. Commit + push:
```bash
cd ~/Dev/Proyectos/sourcing-funnel-dashboard
git add -A
git commit -m "data: <YYYY-Www> (<N> keywords)"
git push
```

3. GitHub Pages redeploya solo (~1 min). Verificar que quedó live:
```bash
curl -s -o /dev/null -w "%{http_code}\n" https://stiflerspain.github.io/sourcing-funnel-dashboard/data/weeks.json
# esperar 200
```

## Notas
- **No subir** perfiles de Chrome (`.chrome-*`), logs ni secretos — el repo solo tiene HTML + JSON
  + `build_static.py`. El `.gitignore` ya cubre `__pycache__`/`.DS_Store`.
- `build_static.py` **no scrapea**; solo transforma `competitors.jsonl` → JSON del dashboard.
- Si una semana quedó incompleta (ej. ban de MeLi), igual se publica con lo que haya; al re-scrapear
  y volver a correr este runbook, se actualiza.
- URL pública: https://stiflerspain.github.io/sourcing-funnel-dashboard/
