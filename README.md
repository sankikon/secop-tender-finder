# SECOP II tender finder

I built this because finding public contracts in Colombia is painful. SECOP's
website makes you search one process at a time. This script pulls every
process that matches a keyword from Colombia's open data portal and drops
them into a spreadsheet you can filter in Excel.

## What you get

A CSV with one row per process: publish date, government entity, city,
description, contract type, base price in COP and a direct link to the
process on SECOP.

Example: `ejemplo_software_bogota.csv` has 220 processes that mention
"software", published in Bogotá in the last 60 days.

## How to run it

Needs Python 3. No extra packages.

```bash
python secop_oportunidades.py "software" --dias 60 --ciudad Bogotá
```

| Option | What it does |
|---|---|
| `"term"` | Word or phrase to look for in the description |
| `--dias` | How many days back to search (default 30) |
| `--ciudad` | Only entities in this city |
| `--max` | Max results (default 5000) |
| `--salida` | Output file name |
| `--test` | Runs the built-in check |

## Notes

- Data comes from the official open data API at datos.gov.co, so there's no
  scraping of private pages and nothing that breaks the site's rules.
- The "status" field in the public dataset is often out of date, so I don't
  filter by it. Open the link to check if a process is still taking offers.
