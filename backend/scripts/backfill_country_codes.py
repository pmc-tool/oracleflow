#!/usr/bin/env python3
"""Backfill country_code for ALL signals where it is NULL or empty.

Uses a comprehensive 100+ keyword map covering country names, capitals,
leaders, demonyms, major cities, and well-known landmarks/institutions.
"""

import sys
from sqlalchemy import create_engine, text

DB_URL = "postgresql://oracleflow:oracleflow@localhost:5433/oracleflow"
BATCH_SIZE = 200

# ---------------------------------------------------------------------------
# Comprehensive country keyword map (100+ entries)
# Keys: ISO 3166-1 alpha-2 codes
# Values: list of lowercase keywords that indicate that country
# ---------------------------------------------------------------------------
COUNTRY_KEYWORDS: dict[str, list[str]] = {
    # --- Americas ---
    "US": [
        "united states", "u.s.", "usa", "america", "american",
        "washington", "new york", "los angeles", "chicago", "houston",
        "san francisco", "silicon valley", "wall street",
        "congress", "senate", "pentagon", "white house", "capitol hill",
        "federal reserve", "biden", "trump", "cia", "fbi", "nsa",
        "california", "texas", "florida", "virginia",
    ],
    "CA": [
        "canada", "canadian", "ottawa", "toronto", "vancouver", "montreal",
        "trudeau", "alberta", "quebec",
    ],
    "MX": [
        "mexico", "mexican", "mexico city", "amlo", "sheinbaum", "guadalajara",
        "cancun", "tijuana",
    ],
    "BR": [
        "brazil", "brazilian", "brasilia", "sao paulo", "rio de janeiro",
        "lula", "bolsonaro", "amazon rainforest",
    ],
    "AR": [
        "argentina", "argentine", "buenos aires", "milei",
    ],
    "CL": [
        "chile", "chilean", "santiago", "boric",
    ],
    "CO": [
        "colombia", "colombian", "bogota", "petro", "medellin",
    ],
    "VE": [
        "venezuela", "venezuelan", "caracas", "maduro",
    ],
    "CU": [
        "cuba", "cuban", "havana",
    ],
    "PE": [
        "peru", "peruvian", "lima",
    ],
    "EC": [
        "ecuador", "ecuadorian", "quito", "guayaquil",
    ],
    "JM": [
        "jamaica", "jamaican", "kingston", "holness", "pnp", "jlp",
    ],
    "TT": [
        "trinidad", "tobago", "port of spain", "rowley",
    ],
    "BB": [
        "barbados", "bridgetown", "mottley",
    ],
    "HT": [
        "haiti", "haitian", "port-au-prince",
    ],
    "DO": [
        "dominican republic", "santo domingo",
    ],
    "PR": [
        "puerto rico",
    ],

    # --- Europe ---
    "GB": [
        "united kingdom", "britain", "british", "england", "english",
        "london", "scotland", "wales", "belfast", "manchester", "birmingham",
        "parliament", "downing street", "starmer", "sunak", "mi6", "gchq",
        "bank of england",
    ],
    "DE": [
        "germany", "german", "berlin", "bundestag", "scholz", "merz",
        "munich", "frankfurt", "hamburg", "bundeswehr",
    ],
    "FR": [
        "france", "french", "paris", "macron", "elysee", "lyon", "marseille",
        "dgse",
    ],
    "IT": [
        "italy", "italian", "rome", "milan", "meloni", "naples", "venice",
    ],
    "ES": [
        "spain", "spanish", "madrid", "barcelona", "sanchez",
    ],
    "PT": [
        "portugal", "portuguese", "lisbon",
    ],
    "NL": [
        "netherlands", "dutch", "amsterdam", "hague", "rotterdam",
    ],
    "BE": [
        "belgium", "belgian", "brussels",
    ],
    "CH": [
        "switzerland", "swiss", "bern", "zurich", "geneva", "davos",
    ],
    "AT": [
        "austria", "austrian", "vienna",
    ],
    "PL": [
        "poland", "polish", "warsaw", "tusk", "krakow",
    ],
    "SE": [
        "sweden", "swedish", "stockholm",
    ],
    "NO": [
        "norway", "norwegian", "oslo",
    ],
    "DK": [
        "denmark", "danish", "copenhagen",
    ],
    "FI": [
        "finland", "finnish", "helsinki",
    ],
    "IE": [
        "ireland", "irish", "dublin",
    ],
    "CZ": [
        "czech republic", "czechia", "czech", "prague",
    ],
    "RO": [
        "romania", "romanian", "bucharest",
    ],
    "GR": [
        "greece", "greek", "athens",
    ],
    "HU": [
        "hungary", "hungarian", "budapest", "orban",
    ],
    "UA": [
        "ukraine", "ukrainian", "kyiv", "kiev", "zelensky", "odesa",
        "kherson", "donetsk", "zaporizhzhia", "donbas", "crimea", "mariupol",
        "bakhmut", "avdiivka", "kharkiv",
    ],
    "SK": [
        "slovakia", "slovak", "bratislava",
    ],
    "BG": [
        "bulgaria", "bulgarian", "sofia",
    ],
    "HR": [
        "croatia", "croatian", "zagreb",
    ],
    "RS": [
        "serbia", "serbian", "belgrade",
    ],
    "BA": [
        "bosnia", "bosnian", "sarajevo",
    ],
    "LT": [
        "lithuania", "lithuanian", "vilnius",
    ],
    "LV": [
        "latvia", "latvian", "riga",
    ],
    "EE": [
        "estonia", "estonian", "tallinn",
    ],
    "GE": [
        "georgia (country)", "tbilisi", "georgian republic",
    ],
    "MD": [
        "moldova", "moldovan", "chisinau",
    ],

    # --- Russia & Central Asia ---
    "RU": [
        "russia", "russian", "moscow", "putin", "kremlin", "st petersburg",
        "lavrov", "shoigu", "medvedev", "siberia", "rostov", "wagner group",
        "fsb", "gru", "svr", "duma",
    ],
    "KZ": [
        "kazakhstan", "kazakh", "astana", "almaty",
    ],
    "UZ": [
        "uzbekistan", "uzbek", "tashkent",
    ],

    # --- Middle East ---
    "IR": [
        "iran", "iranian", "tehran", "khamenei", "raisi", "irgc",
        "persian gulf", "strait of hormuz",
    ],
    "IQ": [
        "iraq", "iraqi", "baghdad", "mosul", "basra", "kurdistan",
    ],
    "IL": [
        "israel", "israeli", "tel aviv", "jerusalem", "netanyahu",
        "mossad", "idf", "knesset", "west bank", "gaza",
    ],
    "PS": [
        "palestine", "palestinian", "gaza", "hamas", "rafah",
        "west bank", "ramallah",
    ],
    "SA": [
        "saudi arabia", "saudi", "riyadh", "jeddah", "mbs",
        "mohammed bin salman", "aramco",
    ],
    "AE": [
        "united arab emirates", "uae", "emirati", "dubai", "abu dhabi",
    ],
    "QA": [
        "qatar", "qatari", "doha",
    ],
    "KW": [
        "kuwait", "kuwaiti",
    ],
    "OM": [
        "oman", "omani", "muscat",
    ],
    "BH": [
        "bahrain", "bahraini", "manama",
    ],
    "YE": [
        "yemen", "yemeni", "sanaa", "houthi", "aden",
    ],
    "SY": [
        "syria", "syrian", "damascus", "assad", "aleppo", "idlib",
    ],
    "LB": [
        "lebanon", "lebanese", "beirut", "hezbollah",
    ],
    "JO": [
        "jordan", "jordanian", "amman",
    ],
    "TR": [
        "turkey", "turkiye", "turkish", "ankara", "istanbul", "erdogan",
    ],

    # --- Asia ---
    "CN": [
        "china", "chinese", "beijing", "shanghai", "xi jinping",
        "ccp", "pla", "guangzhou", "shenzhen", "hong kong",
        "south china sea", "taiwan strait", "pboc", "xinjiang", "tibet",
    ],
    "JP": [
        "japan", "japanese", "tokyo", "osaka", "kishida", "boj",
    ],
    "KR": [
        "south korea", "korean", "seoul", "yoon suk", "busan",
    ],
    "KP": [
        "north korea", "pyongyang", "kim jong un", "dprk",
    ],
    "TW": [
        "taiwan", "taiwanese", "taipei",
    ],
    "IN": [
        "india", "indian", "delhi", "mumbai", "modi", "bangalore",
        "chennai", "kolkata", "kashmir", "jammu",
    ],
    "PK": [
        "pakistan", "pakistani", "islamabad", "karachi", "lahore",
        "kashmir", "balochistan",
    ],
    "BD": [
        "bangladesh", "bangladeshi", "dhaka",
    ],
    "LK": [
        "sri lanka", "sri lankan", "colombo",
    ],
    "AF": [
        "afghanistan", "afghan", "kabul", "taliban", "kandahar",
    ],
    "MM": [
        "myanmar", "burma", "burmese", "yangon", "naypyidaw",
    ],
    "TH": [
        "thailand", "thai", "bangkok",
    ],
    "VN": [
        "vietnam", "vietnamese", "hanoi", "ho chi minh",
    ],
    "ID": [
        "indonesia", "indonesian", "jakarta", "jokowi", "prabowo",
    ],
    "PH": [
        "philippines", "filipino", "manila", "marcos",
    ],
    "MY": [
        "malaysia", "malaysian", "kuala lumpur", "anwar ibrahim",
    ],
    "SG": [
        "singapore", "singaporean",
    ],
    "KH": [
        "cambodia", "cambodian", "phnom penh",
    ],
    "NP": [
        "nepal", "nepalese", "kathmandu",
    ],

    # --- Oceania ---
    "AU": [
        "australia", "australian", "canberra", "sydney", "melbourne",
        "albanese", "brisbane",
    ],
    "NZ": [
        "new zealand", "wellington", "auckland",
    ],

    # --- Africa ---
    "ZA": [
        "south africa", "south african", "pretoria", "cape town",
        "johannesburg", "ramaphosa", "anc",
    ],
    "NG": [
        "nigeria", "nigerian", "abuja", "lagos", "tinubu",
    ],
    "KE": [
        "kenya", "kenyan", "nairobi", "ruto",
    ],
    "EG": [
        "egypt", "egyptian", "cairo", "al-sisi",
    ],
    "ET": [
        "ethiopia", "ethiopian", "addis ababa",
    ],
    "SD": [
        "sudan", "sudanese", "khartoum", "darfur",
    ],
    "SS": [
        "south sudan",
    ],
    "CD": [
        "congo", "congolese", "kinshasa", "drc",
    ],
    "SO": [
        "somalia", "somali", "mogadishu",
    ],
    "GH": [
        "ghana", "ghanaian", "accra",
    ],
    "TZ": [
        "tanzania", "tanzanian", "dar es salaam",
    ],
    "UG": [
        "uganda", "ugandan", "kampala",
    ],
    "RW": [
        "rwanda", "rwandan", "kigali",
    ],
    "MZ": [
        "mozambique", "mozambican", "maputo",
    ],
    "AO": [
        "angola", "angolan", "luanda",
    ],
    "CM": [
        "cameroon", "cameroonian", "yaounde",
    ],
    "ML": [
        "mali", "malian", "bamako",
    ],
    "BF": [
        "burkina faso", "ouagadougou",
    ],
    "NE": [
        "niger", "niamey", "nigerien",
    ],
    "LY": [
        "libya", "libyan", "tripoli", "benghazi",
    ],
    "TN": [
        "tunisia", "tunisian", "tunis",
    ],
    "DZ": [
        "algeria", "algerian", "algiers",
    ],
    "MA": [
        "morocco", "moroccan", "rabat", "casablanca",
    ],
}

# Ambiguous keywords that map to multiple countries — we return the FIRST match
# but weight these lower. Gaza/Kashmir handled by giving them to the most-mentioned side.
# (The primary country list above already has Gaza under both IL and PS.)


def guess_country(title: str, summary: str) -> str:
    """Return the best-guess ISO country code from title+summary text."""
    text = (title + " " + (summary or "")).lower()
    if not text.strip():
        return ""

    # Score each country by number of keyword hits
    scores: dict[str, int] = {}
    for code, keywords in COUNTRY_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in text)
        if hits > 0:
            scores[code] = hits

    if not scores:
        return ""

    # Return the country with the most keyword matches
    best = max(scores, key=scores.get)
    return best


def main():
    print(f"Connecting to {DB_URL} ...")
    engine = create_engine(DB_URL)

    with engine.connect() as conn:
        # Count signals needing backfill
        total_missing = conn.execute(text(
            "SELECT COUNT(*) FROM signals WHERE country_code IS NULL OR country_code = ''"
        )).scalar()
        print(f"Signals with missing country_code: {total_missing}")

        if total_missing == 0:
            print("Nothing to backfill. Done.")
            return

        # Fetch all signals with missing country_code
        rows = conn.execute(text(
            "SELECT id, title, summary FROM signals "
            "WHERE country_code IS NULL OR country_code = '' "
            "ORDER BY id"
        )).fetchall()

        updated = 0
        still_empty = 0

        for i, row in enumerate(rows):
            sig_id, title, summary = row[0], row[1] or "", row[2] or ""
            code = guess_country(title, summary)

            if code:
                conn.execute(text(
                    "UPDATE signals SET country_code = :cc WHERE id = :sid"
                ), {"cc": code, "sid": sig_id})
                updated += 1
            else:
                still_empty += 1

            if (i + 1) % BATCH_SIZE == 0:
                conn.commit()
                print(f"  Progress: {i+1}/{total_missing} processed, {updated} attributed so far")

        conn.commit()

        # Verify
        remaining = conn.execute(text(
            "SELECT COUNT(*) FROM signals WHERE country_code IS NULL OR country_code = ''"
        )).scalar()

        print(f"\nDone! Backfill complete.")
        print(f"  Signals processed: {total_missing}")
        print(f"  Country codes assigned: {updated}")
        print(f"  Still empty (no match): {still_empty}")
        print(f"  Remaining NULL/empty: {remaining}")

        # Show distribution of top countries
        top = conn.execute(text(
            "SELECT country_code, COUNT(*) as cnt FROM signals "
            "WHERE country_code IS NOT NULL AND country_code != '' "
            "GROUP BY country_code ORDER BY cnt DESC LIMIT 20"
        )).fetchall()
        print("\nTop 20 country distribution:")
        for r in top:
            print(f"  {r[0]}: {r[1]}")


if __name__ == "__main__":
    main()
