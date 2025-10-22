import json
import re

input_file = "Suomen ohjelmistoyritys tiedot.json"
output_file = "toimialat.json"

# Lue koko tiedosto tekstinä
with open(input_file, "r", encoding="utf-8") as f:
    raw = f.read()

# Poista ObjectId(...) ja ISODate(...)
cleaned = re.sub(r'ObjectId\("([^"]+)"\)', r'"\1"', raw)
cleaned = re.sub(r'ISODate\("([^"]+)"\)', r'"\1"', cleaned)

# Erota kaikki JSON-objektit
blocks = re.findall(r'\{.*?\}', cleaned, re.DOTALL)

toimialat = set()

for block in blocks:
    try:
        yritys = json.loads(block)
        toimiala = yritys.get("Toimiala")
        if isinstance(toimiala, str):
            toimialat.add(toimiala.strip())
    except Exception as e:
        print("Virheellinen lohko ohitettu.")
        print("Virheilmoitus:", e)

# Tallenna toimialat tiedostoon
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(sorted(list(toimialat)), f, ensure_ascii=False, indent=2)

print(f"Tallennettu {len(toimialat)} uniikkia toimialaa tiedostoon '{output_file}'.")