#!/usr/bin/env python3
"""Generate country YAML configs for the 45 additional intelligence-priority countries."""

import os

COUNTRIES_DIR = os.path.join(
    os.path.dirname(__file__),
    "app", "oracleflow", "registry", "countries",
)

COUNTRIES = [
    # (code, name, region, filename, languages, timezone, gov_sources, key_entities)
    ("GB", "United Kingdom", "europe", "united_kingdom.yaml", ["en"], "Europe/London",
     [("https://www.gov.uk", "government_portal"), ("https://www.parliament.uk", "legislature")],
     [("King Charles III", "person", "Head of State"), ("Keir Starmer", "person", "Prime Minister")]),

    ("DE", "Germany", "europe", "germany.yaml", ["de"], "Europe/Berlin",
     [("https://www.bundesregierung.de", "government_portal"), ("https://www.bundestag.de", "legislature")],
     [("Friedrich Merz", "person", "Chancellor")]),

    ("FR", "France", "europe", "france.yaml", ["fr"], "Europe/Paris",
     [("https://www.elysee.fr", "government_portal"), ("https://www.assemblee-nationale.fr", "legislature")],
     [("Emmanuel Macron", "person", "President")]),

    ("CN", "China", "east_asia", "china.yaml", ["zh"], "Asia/Shanghai",
     [("https://www.gov.cn", "government_portal"), ("http://www.npc.gov.cn", "legislature")],
     [("Xi Jinping", "person", "President"), ("Chinese Communist Party", "political_party", "Ruling Party")]),

    ("RU", "Russia", "europe", "russia.yaml", ["ru"], "Europe/Moscow",
     [("http://government.ru", "government_portal"), ("http://duma.gov.ru", "legislature")],
     [("Vladimir Putin", "person", "President"), ("United Russia", "political_party", "Ruling Party")]),

    ("JP", "Japan", "east_asia", "japan.yaml", ["ja"], "Asia/Tokyo",
     [("https://www.kantei.go.jp", "government_portal"), ("https://www.shugiin.go.jp", "legislature")],
     [("Shigeru Ishiba", "person", "Prime Minister")]),

    ("KR", "South Korea", "east_asia", "south_korea.yaml", ["ko"], "Asia/Seoul",
     [("https://www.president.go.kr", "government_portal"), ("https://www.assembly.go.kr", "legislature")],
     [("Yoon Suk Yeol", "person", "President")]),

    ("AU", "Australia", "oceania", "australia.yaml", ["en"], "Australia/Sydney",
     [("https://www.pm.gov.au", "government_portal"), ("https://www.aph.gov.au", "legislature")],
     [("Anthony Albanese", "person", "Prime Minister")]),

    ("CA", "Canada", "north_america", "canada.yaml", ["en", "fr"], "America/Toronto",
     [("https://www.canada.ca", "government_portal"), ("https://www.parl.ca", "legislature")],
     [("Mark Carney", "person", "Prime Minister")]),

    ("BR", "Brazil", "south_america", "brazil.yaml", ["pt"], "America/Sao_Paulo",
     [("https://www.gov.br", "government_portal"), ("https://www.camara.leg.br", "legislature")],
     [("Luiz Inacio Lula da Silva", "person", "President")]),

    ("MX", "Mexico", "north_america", "mexico.yaml", ["es"], "America/Mexico_City",
     [("https://www.gob.mx", "government_portal"), ("https://www.diputados.gob.mx", "legislature")],
     [("Claudia Sheinbaum", "person", "President")]),

    ("AR", "Argentina", "south_america", "argentina.yaml", ["es"], "America/Argentina/Buenos_Aires",
     [("https://www.argentina.gob.ar", "government_portal")],
     [("Javier Milei", "person", "President")]),

    ("CL", "Chile", "south_america", "chile.yaml", ["es"], "America/Santiago",
     [("https://www.gob.cl", "government_portal")],
     [("Gabriel Boric", "person", "President")]),

    ("CO", "Colombia", "south_america", "colombia.yaml", ["es"], "America/Bogota",
     [("https://www.gov.co", "government_portal")],
     [("Gustavo Petro", "person", "President")]),

    ("ZA", "South Africa", "africa", "south_africa.yaml", ["en", "af", "zu"], "Africa/Johannesburg",
     [("https://www.gov.za", "government_portal"), ("https://www.parliament.gov.za", "legislature")],
     [("Cyril Ramaphosa", "person", "President"), ("African National Congress", "political_party", "Ruling Party")]),

    ("NG", "Nigeria", "africa", "nigeria.yaml", ["en"], "Africa/Lagos",
     [("https://statehouse.gov.ng", "government_portal")],
     [("Bola Tinubu", "person", "President")]),

    ("KE", "Kenya", "africa", "kenya.yaml", ["en", "sw"], "Africa/Nairobi",
     [("https://www.president.go.ke", "government_portal")],
     [("William Ruto", "person", "President")]),

    ("EG", "Egypt", "middle_east", "egypt.yaml", ["ar"], "Africa/Cairo",
     [("https://www.presidency.eg", "government_portal")],
     [("Abdel Fattah al-Sisi", "person", "President")]),

    ("SA", "Saudi Arabia", "middle_east", "saudi_arabia.yaml", ["ar"], "Asia/Riyadh",
     [("https://www.my.gov.sa", "government_portal")],
     [("Mohammed bin Salman", "person", "Crown Prince"), ("King Salman", "person", "Head of State")]),

    ("AE", "United Arab Emirates", "middle_east", "uae.yaml", ["ar", "en"], "Asia/Dubai",
     [("https://u.ae", "government_portal")],
     [("Mohammed bin Zayed Al Nahyan", "person", "President")]),

    ("IL", "Israel", "middle_east", "israel.yaml", ["he", "ar"], "Asia/Jerusalem",
     [("https://www.gov.il", "government_portal"), ("https://www.knesset.gov.il", "legislature")],
     [("Benjamin Netanyahu", "person", "Prime Minister")]),

    ("IR", "Iran", "middle_east", "iran.yaml", ["fa"], "Asia/Tehran",
     [("https://www.president.ir", "government_portal")],
     [("Ali Khamenei", "person", "Supreme Leader")]),

    ("IQ", "Iraq", "middle_east", "iraq.yaml", ["ar", "ku"], "Asia/Baghdad",
     [("https://www.pmo.iq", "government_portal")],
     [("Mohammed Shia al-Sudani", "person", "Prime Minister")]),

    ("SY", "Syria", "middle_east", "syria.yaml", ["ar"], "Asia/Damascus",
     [("https://www.sana.sy", "government_portal")],
     [("Ahmad al-Sharaa", "person", "Head of State")]),

    ("TR", "Turkey", "middle_east", "turkey.yaml", ["tr"], "Europe/Istanbul",
     [("https://www.tccb.gov.tr", "government_portal"), ("https://www.tbmm.gov.tr", "legislature")],
     [("Recep Tayyip Erdogan", "person", "President"), ("AKP", "political_party", "Ruling Party")]),

    ("UA", "Ukraine", "europe", "ukraine.yaml", ["uk"], "Europe/Kyiv",
     [("https://www.president.gov.ua", "government_portal"), ("https://www.rada.gov.ua", "legislature")],
     [("Volodymyr Zelensky", "person", "President")]),

    ("PL", "Poland", "europe", "poland.yaml", ["pl"], "Europe/Warsaw",
     [("https://www.gov.pl", "government_portal"), ("https://www.sejm.gov.pl", "legislature")],
     [("Donald Tusk", "person", "Prime Minister")]),

    ("BD", "Bangladesh", "south_asia", "bangladesh.yaml", ["bn"], "Asia/Dhaka",
     [("https://www.bangladesh.gov.bd", "government_portal")],
     [("Muhammad Yunus", "person", "Chief Adviser")]),

    ("PK", "Pakistan", "south_asia", "pakistan.yaml", ["ur", "en"], "Asia/Karachi",
     [("https://www.pakistan.gov.pk", "government_portal")],
     [("Shehbaz Sharif", "person", "Prime Minister")]),

    ("AF", "Afghanistan", "south_asia", "afghanistan.yaml", ["ps", "fa"], "Asia/Kabul",
     [("https://www.alemarah-english.net", "government_portal")],
     [("Hibatullah Akhundzada", "person", "Supreme Leader")]),

    ("MM", "Myanmar", "southeast_asia", "myanmar.yaml", ["my"], "Asia/Yangon",
     [("https://www.moi.gov.mm", "government_portal")],
     [("Min Aung Hlaing", "person", "Head of State")]),

    ("TH", "Thailand", "southeast_asia", "thailand.yaml", ["th"], "Asia/Bangkok",
     [("https://www.thaigov.go.th", "government_portal")],
     [("Paetongtarn Shinawatra", "person", "Prime Minister")]),

    ("VN", "Vietnam", "southeast_asia", "vietnam.yaml", ["vi"], "Asia/Ho_Chi_Minh",
     [("https://www.chinhphu.vn", "government_portal")],
     [("To Lam", "person", "General Secretary")]),

    ("ID", "Indonesia", "southeast_asia", "indonesia.yaml", ["id"], "Asia/Jakarta",
     [("https://www.indonesia.go.id", "government_portal")],
     [("Prabowo Subianto", "person", "President")]),

    ("PH", "Philippines", "southeast_asia", "philippines.yaml", ["en", "tl"], "Asia/Manila",
     [("https://www.officialgazette.gov.ph", "government_portal")],
     [("Ferdinand Marcos Jr.", "person", "President")]),

    ("MY", "Malaysia", "southeast_asia", "malaysia.yaml", ["ms", "en"], "Asia/Kuala_Lumpur",
     [("https://www.malaysia.gov.my", "government_portal")],
     [("Anwar Ibrahim", "person", "Prime Minister")]),

    ("SG", "Singapore", "southeast_asia", "singapore.yaml", ["en", "ms", "zh", "ta"], "Asia/Singapore",
     [("https://www.gov.sg", "government_portal")],
     [("Lawrence Wong", "person", "Prime Minister")]),

    ("TW", "Taiwan", "east_asia", "taiwan.yaml", ["zh"], "Asia/Taipei",
     [("https://www.president.gov.tw", "government_portal"), ("https://www.ly.gov.tw", "legislature")],
     [("Lai Ching-te", "person", "President")]),

    ("NZ", "New Zealand", "oceania", "new_zealand.yaml", ["en", "mi"], "Pacific/Auckland",
     [("https://www.govt.nz", "government_portal"), ("https://www.parliament.nz", "legislature")],
     [("Christopher Luxon", "person", "Prime Minister")]),

    ("SE", "Sweden", "europe", "sweden.yaml", ["sv"], "Europe/Stockholm",
     [("https://www.government.se", "government_portal"), ("https://www.riksdagen.se", "legislature")],
     [("Ulf Kristersson", "person", "Prime Minister")]),

    ("NO", "Norway", "europe", "norway.yaml", ["no"], "Europe/Oslo",
     [("https://www.regjeringen.no", "government_portal"), ("https://www.stortinget.no", "legislature")],
     [("Jonas Gahr Store", "person", "Prime Minister")]),

    ("CH", "Switzerland", "europe", "switzerland.yaml", ["de", "fr", "it"], "Europe/Zurich",
     [("https://www.admin.ch", "government_portal")],
     [("Karin Keller-Sutter", "person", "President of the Confederation")]),

    ("IT", "Italy", "europe", "italy.yaml", ["it"], "Europe/Rome",
     [("https://www.governo.it", "government_portal"), ("https://www.camera.it", "legislature")],
     [("Giorgia Meloni", "person", "Prime Minister")]),

    ("ES", "Spain", "europe", "spain.yaml", ["es"], "Europe/Madrid",
     [("https://www.lamoncloa.gob.es", "government_portal"), ("https://www.congreso.es", "legislature")],
     [("Pedro Sanchez", "person", "Prime Minister")]),

    ("NL", "Netherlands", "europe", "netherlands.yaml", ["nl"], "Europe/Amsterdam",
     [("https://www.government.nl", "government_portal"), ("https://www.tweedekamer.nl", "legislature")],
     [("Dick Schoof", "person", "Prime Minister")]),
]


def generate_yaml(code, name, region, filename, languages, tz, gov_sources, key_entities):
    """Generate a minimal YAML config for a country."""
    lines = []
    lines.append(f'country: {name}')
    lines.append(f'code: {code}')
    lines.append(f'region: {region}')
    lines.append('languages:')
    for lang in languages:
        lines.append(f'  - {lang}')
    lines.append(f'timezone: {tz}')
    lines.append('proxy_pool: ""')
    lines.append('')
    lines.append('sources:')
    lines.append('  government:')
    for url, gtype in gov_sources:
        lines.append(f'    - url: {url}')
        lines.append(f'      type: {gtype}')
        lines.append('      frequency: "2h"')
    lines.append('')
    lines.append('  news: []')
    lines.append('  reddit: []')
    lines.append('  social: {}')
    lines.append('')
    lines.append('  political_entities:')
    for ename, etype, erole in key_entities:
        lines.append(f'    - name: "{ename}"')
        lines.append(f'      type: {etype}')
        lines.append(f'      role: "{erole}"')
    lines.append('')
    return '\n'.join(lines)


def main():
    os.makedirs(COUNTRIES_DIR, exist_ok=True)
    created = 0
    for entry in COUNTRIES:
        code, name, region, filename, languages, tz, gov_sources, key_entities = entry
        filepath = os.path.join(COUNTRIES_DIR, filename)
        content = generate_yaml(code, name, region, filename, languages, tz, gov_sources, key_entities)
        with open(filepath, 'w') as f:
            f.write(content)
        created += 1
        print(f"  Created: {filename}")
    print(f"\nDone. {created} country YAML files generated in {COUNTRIES_DIR}")


if __name__ == "__main__":
    main()
