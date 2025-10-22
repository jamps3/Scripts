import requests
import json
import time

# Kysy kaupunki käyttäjältä
kaupunki_suodatus = input("Anna kaupunki suodatukseen (Enter = Joensuu): ").strip().lower()
if not kaupunki_suodatus:
    kaupunki_suodatus = "joensuu"

# TOL-koodit ja niiden kuvaukset
toimialat = {
    "62020": "Atk-laitteisto- ja ohjelmistokonsultointi",
    "74300": "Kääntäminen ja tulkkaus",
    "27900": "Muiden sähkölaitteiden valmistus",
    "62090": "Muu laitteisto- ja tietotekninen palvelutoiminta",
    "58290": "Muu ohjelmistojen kustantaminen",
    "71129": "Muu tekninen palvelu",
    "71209": "Muu tekninen testaus ja analysointi",
    "61900": "Muut televiestintäpalvelut",
    "62010": "Ohjelmistojen suunnittelu ja valmistus",
    "62000": "Ohjelmistot, konsultointi ja siihen liittyvä toiminta",
    "42220": "Sähkö- ja tietoliikenneverkkojen rakentaminen",
    "33140": "Sähkölaitteiden korjaus ja huolto",
    "33200": "Teollisuuden koneiden ja laitteiden ym. asennus",
    "63110": "Tietojenkäsittely, palvelintilan vuokraus ja niihin liittyvät palvelut",
    "62030": "Tietojenkäsittelyn ja laitteistojen käyttö- ja hallintapalvelut",
    "26200": "Tietokoneiden ja niiden oheislaitteiden valmistus",
    "47410": "Tietokoneiden, niiden oheislaitteiden ja ohjelmistojen vähittäiskauppa",
    "63120": "Verkkoportaalit",
    "95120": "Viestintälaitteiden korjaus",
    "59200": "Ääni-, kuva- ja atk-tallenteiden tuotanto"
}

aktiiviset_yritykset = []

def onko_aktiivinen(yritys):
    return (
        yritys.get("endDate") is None and
        yritys.get("status") == "1" and
        yritys.get("tradeRegisterStatus") != "4" and
        not any(entry.get("type") == "4" for entry in yritys.get("registeredEntries", []))
    )

for tol_koodi, kuvaus in toimialat.items():
    print(f"\n🔍 Haetaan toimialaa: {kuvaus} ({tol_koodi})")
    offset = 0
    previous_ids = set()

    while True:
        url = (
            f"https://avoindata.prh.fi/opendata-ytj-api/v3/companies"
            f"?mainBusinessLine={tol_koodi}&limit=100&offset={offset}&registrationFrom=2000-01-01&location=Joensuu"
        )
        response = requests.get(url)
        if response.status_code != 200:
            print(f"❌ Virhe haettaessa toimialaa {kuvaus} ({tol_koodi})")
            break

        data = response.json()
        companies = data.get("companies", [])
        print(f"➡️ Offset {offset}: {len(companies)} yritystä haettu")

        if not companies:
            break

        current_ids = {c.get("businessId", {}).get("value") for c in companies}
        if current_ids & previous_ids:
            print("🔁 Samat yritykset toistuvat — lopetetaan sivutus.")
            break
        previous_ids.update(current_ids)

        for yritys in companies:
            if onko_aktiivinen(yritys):
                osoitteet = yritys.get("addresses", [])
                kaupunki = osoitteet[0].get("city", "Tuntematon") if osoitteet else "Tuntematon"

                if kaupunki.lower() != kaupunki_suodatus:
                    continue

                tiivis = {
                    "nimi": yritys.get("name"),
                    "y_tunnus": yritys.get("businessId"),
                    "toimiala": kuvaus,
                    "rekisteroity": yritys.get("registrationDate"),
                    "kaupunki": kaupunki
                }
                aktiiviset_yritykset.append(tiivis)
                print(f"✅ Aktiivinen yritys: {tiivis}")
            else:
                print("⛔", end="")

        offset += len(companies)
        time.sleep(0.5)

print(f"\n📦 Tallennetaan {len(aktiiviset_yritykset)} aktiivista yritystä tiedostoon...")

with open("aktiiviset_yritykset.json", "w", encoding="utf-8") as f:
    json.dump(aktiiviset_yritykset, f, ensure_ascii=False, indent=2)

print("✅ Tallennus valmis: aktiiviset_yritykset.json")