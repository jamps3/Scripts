import json
import re
from datetime import datetime

input_file = "Suomen ohjelmistoyritys tiedot.json"
output_file = "joensuu_yritykset.json"

# Lue koko tiedosto tekstinä
with open(input_file, "r", encoding="utf-8") as f:
    raw = f.read()

# Poista ObjectId(...) ja ISODate(...)
cleaned = re.sub(r'ObjectId\("([^"]+)"\)', r'"\1"', raw)
cleaned = re.sub(r'ISODate\("([^"]+)"\)', r'"\1"', cleaned)

# Erota kaikki JSON-objektit
blocks = re.findall(r'\{.*?\}', cleaned, re.DOTALL)

joensuu_yritykset = []

for block in blocks:
    try:
        yritys = json.loads(block)
        kaupunki = yritys.get("Kaupunki")
        if isinstance(kaupunki, str) and kaupunki.upper() == "JOENSUU":
            joensuu_yritykset.append(yritys)
    except Exception as e:
        print("Virheellinen lohko ohitettu.")
        print("Virheilmoitus:", e)

# Järjestetään rekisteröintipäivän mukaan
def parse_date(yritys):
    pvm = yritys.get("Rekisterointi_pvm")
    try:
        return datetime.strptime(pvm, "%Y-%m-%dT%H:%M:%S.%f%z")
    except Exception:
        return datetime.min  # Jos virhe, siirretään alkuun

joensuu_yritykset.sort(key=parse_date)

# Tallenna tulokset
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(joensuu_yritykset, f, ensure_ascii=False, indent=2)

print(f"Tallennettu {len(joensuu_yritykset)} Joensuun yritystä tiedostoon '{output_file}' järjestettynä rekisteröintipäivän mukaan.")