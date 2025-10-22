import json
import re

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
    except json.JSONDecodeError as e:
        print("Virhe rivissä:\n", block)
        print("Virheilmoitus:", e)

# Tallenna Joensuun yritykset uuteen tiedostoon
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(joensuu_yritykset, f, ensure_ascii=False, indent=2)

print(f"Tallennettu {len(joensuu_yritykset)} Joensuun yritystä tiedostoon '{output_file}'.")