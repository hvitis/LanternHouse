# Domek Muminków

[English](README.md) · **Polski**

**Domek dla lalek ze sklejki, w całości generowany z kodu.** Jeden model w Pythonie i jeden plik konfiguracji tworzą dokument FreeCAD, rozkroje arkuszy, książkę budowy na A4 z szablonami 1:1, rendery i interaktywną przeglądarkę 3D. Automatyczne kontrole sprawdzają, czy ściany, drzwi, szuflada i dach poruszają się bez kolizji.

<p align="center">
  <img src="docs/images/cover.jpg" width="380" alt="Okładka książki: okrągła niebieska wieża z czerwonym stożkowym dachem i małą werandą na letniej łące">
</p>

Domek to niebieska wieża o wysokości 894 mm, z czerwonym spiczastym dachem, trzema kondygnacjami i poddaszem. Dwanaście płaskich ścian można wyciąć wyrzynarką, a cienkie elementy — laserem. Przednie ściany otwierają się na zawiasach. Dach jest zdejmowany, weranda stoi na stałe z boku, a kamienny cokół kryje szufladę. Na trzech kondygnacjach mieszkają trzy Muminki z modeliny termoutwardzalnej.

<p align="center">
  <b><a href="https://hvitis.github.io/houseofmoomin/">Otwórz model 3D w przeglądarce</a></b> &nbsp;·&nbsp;
  <b><a href="https://github.com/hvitis/houseofmoomin/releases/latest">Pobierz książkę budowy (PDF)</a></b>
</p>

> To nieoficjalny, niekomercyjny projekt fanowski. Nie jest powiązany z Moomin Characters Oy ani producentami komercyjnych zestawów domku Muminków. Żaden z tych podmiotów go nie zatwierdził. Zobacz [znaki towarowe i licencję](#znaki-towarowe-i-licencja).

<table>
  <tr>
    <td align="center"><img src="docs/images/house-closed.webp" width="250" alt="Zamknięty domek od strony werandy"><br><sub>Zamknięty, od strony werandy</sub></td>
    <td align="center"><img src="docs/images/house-open.webp" width="290" alt="Otwarte ściany i podniesiony dach odsłaniają umeblowane kondygnacje"><br><sub>Otwarte ściany, podniesiony dach</sub></td>
    <td align="center"><img src="docs/images/house-exploded.webp" width="250" alt="Widok rozstrzelony zespołów konstrukcyjnych"><br><sub>Widok rozstrzelony</sub></td>
  </tr>
</table>

<p align="center">
  <img src="docs/images/clay-family.webp" width="520" alt="Figurki z modeliny: Tatuś Muminka w cylindrze, Mamusia Muminka w pasiastym fartuszku z torebką i Muminek"><br>
  <sub>Rodzina z modeliny: model z brył, objętości i gramatura każdego koloru</sub>
</p>

## Możliwości

- **Dokumentacja do wykonania domku.** Każda część ma grubość sklejki, obrys, otwory i otwory startowe dla wyrzynarki. Rozkrój uwzględnia rzeczywiste wymiary arkuszy. Książka zawiera szablony 1:1 podzielone na strony, kwadrat kalibracyjny, szablony kontroli zawiasów, listę okuć i instrukcję montażu.
- **Ruchome elementy.** Dwie przednie części ściany otwierają się do 100°. Magnesy w słupkach ogrodowych utrzymują je w tej pozycji. Zaczepy magnetyczne pod podłogą poddasza utrzymują ściany zamknięte. Dwoje drzwi otwiera się na zewnątrz. Dach można zdjąć po zwolnieniu dwóch obrotowych zaczepów. Szuflada wysuwa się z cokołu na 220 mm. Każda kondygnacja ma dwa pokoje.
- **Jedna konfiguracja steruje całością.** Wysokość, podstawa, cokół, szuflada, drzwi, położenie i wymiary werandy, otwory zawiasów, arkusze sklejki i kolory znajdują się w `source/config.json`.
- **Automatyczne kontrole.** Każda kompilacja sprawdza przenikanie brył, ruch ścian co 5° aż do ogranicznika 100° i ruch obu drzwi. Sprawdza też szufladę, podnoszenie dachu, prześwity okien, przejście każdej figurki w pozycji stojącej przez każde drzwi, odstępy rozkroju, otwory startowe, liczbę części i okuć oraz skalę PDF. Osobna kontrola odtwarza domek dla najcieńszej i najgrubszej zmierzonej sklejki. Niepowodzenie dowolnej kontroli zatrzymuje kompilację.
- **Figurki z modeliny.** Tatuś Muminka, Mamusia Muminka i Muminek powstają z łączonych brył opisanych polem odległości. Model oblicza objętość figurki, gramaturę każdego koloru i oszczędność przy zastosowaniu rdzenia z folii aluminiowej.
- **Wiele formatów wyjściowych.** Edytowalny dokument FreeCAD, bryły STEP (domek zamknięty, otwarty, rozstrzelony i każda część osobno), profile DXF, rozkroje SVG, pliki do lasera SVG i DXF, dokumenty PDF oraz listy zakupów CSV.

## Wypróbuj przeglądarkę 3D — bez FreeCAD

Najłatwiej otworzyć [przeglądarkę online](https://hvitis.github.io/houseofmoomin/). GitHub przebudowuje ją po każdym wysłaniu zmian na gałąź `main`. Do uruchomienia lokalnego lub podglądu własnej konfiguracji potrzebujesz Pythona 3.12 lub nowszego oraz Git.

```sh
git clone https://github.com/hvitis/houseofmoomin.git
cd houseofmoomin
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python source/serve.py --open
```

W Windows użyj `py -3.12 -m venv .venv`. Zastąp `.venv/bin/python` poleceniem `.venv\Scripts\python`.

Przy pierwszym uruchomieniu `serve.py` tworzy `output/parts.json` na podstawie modelu. Trwa to około 10 sekund. Następnie otwiera <http://127.0.0.1:8765/> lub kolejny wolny port. Przeglądarka działa bez internetu, ponieważ repozytorium zawiera three.js. Serwer domyślnie przyjmuje połączenia tylko z Twojego komputera.

Meble występują wyłącznie w przeglądarce 3D i na renderach. Zestaw budowlany nie zawiera ich planów CAD, rozkrojów ani wydruków.

W przeglądarce możesz:

- otwierać ściany wokół rzeczywistych osi zawiasów, otwierać drzwi, podnosić lub zdejmować dach i wysuwać szufladę;
- pokazywać lub ukrywać werandę, meble, figurki, śruby, osie zawiasów i wymiary;
- włączać przezroczystość ścian, rozsuwać zespoły i odcinać model powyżej wybranej wysokości;
- kliknąć część, aby zobaczyć jej identyfikator, wymiary, liczbę i uwagę montażową, lub figurkę, aby zobaczyć zapotrzebowanie na modelinę.

Po zmianie `source/config.json` uruchom `serve.py --rebuild`, aby odświeżyć model.

## Wygeneruj pliki do budowy

Pliki PDF, CAD i rozkroje **nie znajdują się w repozytorium**. Zajmują łącznie około 100 MB i powstają z kodu źródłowego.

**Jeśli chcesz tylko zbudować domek,** pobierz dokumenty PDF i zestaw z [najnowszego wydania](https://github.com/hvitis/houseofmoomin/releases/latest). Samodzielnie generuj pliki, gdy zmieniasz projekt.

**1. Zainstaluj FreeCAD 1.1 lub nowszy.** Etapy CAD używają Pythona dostarczanego z FreeCAD. Udostępnia on jądro OpenCASCADE, numpy i shapely.

| System | Instalacja | `--freecad-python` |
| --- | --- | --- |
| macOS (sprawdzony) | `brew install --cask freecad` | `/Applications/FreeCAD.app/Contents/Resources/bin/python` |
| Linux (niesprawdzony) | Pobierz AppImage z [freecad.org](https://www.freecad.org/downloads.php), następnie uruchom `./FreeCAD_*.AppImage --appimage-extract` | `squashfs-root/usr/bin/python` |
| Windows (niesprawdzony) | Użyj instalatora z [freecad.org](https://www.freecad.org/downloads.php) | na przykład `"C:\Program Files\FreeCAD 1.1\bin\python.exe"` |

Przed pełną kompilacją sprawdź, czy ten interpreter wczytuje potrzebne moduły:

```sh
FREECAD_PYTHON=/Applications/FreeCAD.app/Contents/Resources/bin/python
"$FREECAD_PYTHON" -c "import sys,pathlib; sys.path.insert(0,str(pathlib.Path(sys.executable).resolve().parent.parent/'lib')); import FreeCAD, Part, Sketcher, numpy, shapely; print('FreeCAD', '.'.join(FreeCAD.Version()[:3]), 'OK')"
```

**2. Przygotuj zwykłe środowisko Pythona**, tak samo jak dla przeglądarki 3D.

**3. Wygeneruj całość:**

```sh
make all        # kontrola konfiguracji, testy, pełna kompilacja i kontrola grubości sklejki
```

`make` domyślnie używa ścieżki FreeCAD dla macOS. W innym systemie podaj własną, na przykład `make all FREECAD_PYTHON=squashfs-root/usr/bin/python`. Polecenie `make help` pokazuje poszczególne etapy: `check`, `build`, `tolerance`, `clean`, `viewer` i `site`. Bez Make uruchom `.venv/bin/python source/rebuild.py --freecad-python "$FREECAD_PYTHON"`, a następnie `source/thickness_check.py` w Pythonie FreeCAD.

Pełna kompilacja trwa około dwóch minut, a kontrola grubości — około minuty. Kompilacja najpierw opróżnia `output/`, aby usunąć pliki z poprzedniego uruchomienia. Następnie tworzy CAD, rozkroje, rendery, książkę, kontrole wydania i paczkę. Zatrzymuje się po pierwszym błędzie kontroli. Wyniki:

| Ścieżka | Zawartość |
| --- | --- |
| `output/pdf/` | Osiem dokumentów PDF: pełna książka, instrukcja, szablony do wycinania, zwymiarowane części, dekoracje (paleta, okładziny kamienne, pasy gontów), rodzina z modeliny, ręczne szablony części 3 mm i załącznik dla wykonawcy. Strony warsztatowe mają format A4, a arkusze produkcyjne także A3. |
| `output/cad/` | `MoominHouse.FCStd` (edytowalny dokument), zespoły STEP (zamknięty, otwarty, rozstrzelony) i `parts/*.step` |
| `output/dxf/` | DXF dla każdego profilu, rozkroje w pełnej skali (`*-layout.svg`) i pliki do lasera dla arkuszy 3 mm (`*-laser.svg`, `*-laser.dxf`) |
| `output/previews/` | Rendery na podstawie CAD i rendery figurek |
| `output/reports/` | `release-validation.json` (wszystkie kontrole), `cad-validation.json`, `thickness-tolerance.json`, `parts.csv`, `hardware.csv`, `stock.csv` |
| `output/Moomin-House-Build-Kit.zip` | Wszystkie powyższe pliki wraz ze źródłami w jednej paczce |

Przed drukowaniem przeczytaj [przewodnik budowy](docs/BUILD-GUIDE.md). Szablony 1:1 drukuj w skali 100% i sprawdź ich wymiary.

Do zlecenia wycinania części domku ze sklejki 3 mm wyślij `Moomin-House-Supplier.pdf`. Zawiera polską specyfikację, spis części i mapy odniesienia, a następnie czyste strony produkcyjne A3/A4. Każdy panel dachu mieści się w całości na A3. Dokument nie obejmuje mebli. Pełna książka ma klikalny spis treści i ten sam załącznik na końcu. Do przyklejania papierowych szablonów A4 użyj `Moomin-House-3mm-Hand-Templates.pdf`. Tekstury znajdują się w PDF z dekoracjami. Uzgodnij z wykonawcą tolerancje i szerokość cięcia. Aby wygenerować załącznik po angielsku, dodaj `--lang en` do `source/rebuild.py`.

## Zmień projekt

1. Edytuj `source/config.json`. Zmień na przykład `height`, `veranda.facet`, `doors`, `plinth.drawer.travel`, `figures.levels` lub `stock`. Edytory obsługujące JSON Schema podpowiadają klucze i pokazują ich opisy z `source/config.schema.json`.
2. Uruchom `.venv/bin/python source/config_check.py`. Kontrola trwa około sekundy. Wykrywa literówki, błędne typy i sprzeczności, na przykład dwoje drzwi na jednej ścianie lub zbyt duży zawias.
3. Otwórz podgląd: `.venv/bin/python source/serve.py --rebuild --open`.
4. Uruchom szybkie testy, które trwają około 10 sekund i nie wymagają FreeCAD:

   ```sh
   .venv/bin/python -m pip install -r requirements-dev.txt
   make check
   ```

5. Uruchom `make all` i przeczytaj `output/reports/release-validation.json`. Kontrole pokazują, czy ściany otwierają się bez kolizji, szuflada się wysuwa, figurki mieszczą się w drzwiach i części mieszczą się na arkuszach. Raport `thickness-tolerance.json` pokazuje, czy rzeczywista grubość sklejki w przedziale `thickness_tolerance` likwiduje któryś prześwit.

[docs/PIPELINE.md](docs/PIPELINE.md) opisuje etapy, model danych, klucze konfiguracji oraz publikację wydań i przeglądarki online.

## Układ repozytorium

```text
source/                  źródła generujące domek
  config.json            parametry projektu
  config.schema.json     znaczenie parametrów, jednostki i ograniczenia
  config_check.py        kontrola konfiguracji przed kompilacją
  model.py               części i ich położenia: jedno źródło danych
  architecture.py        weranda, wejścia i lukarna
  clay.py                figurki z modeliny
  build_cad.py, nest.py   CAD i kontrole FreeCAD, rozkroje (Python FreeCAD)
  render.py, cover.py, book.py, verify.py, package.py             (zwykły Python)
  rebuild.py             opróżnia output/ i uruchamia cały proces
  thickness_check.py     kontrola domku dla zmierzonej grubości sklejki (Python FreeCAD)
  serve.py, viewer/      interaktywna przeglądarka 3D (lokalny three.js r160)
  export_viewer.py       eksport przeglądarki jako strony statycznej (GitHub Pages)
  release.py             wysyła PDF i zestaw budowlany do wydania GitHub
tests/                   szybkie testy modelu i eksportu oraz kontrola przeglądarki
.github/workflows/       CI: testy źródeł i przeglądarki, publikacja strony z main
docs/                    przewodnik, opis procesu, publikacja, pomysły i ilustracje
original/                lokalne zdjęcia referencyjne (ignorowane przez Git)
output/                  wygenerowane pliki (ignorowane przez Git)
_site/                   wyeksportowana strona 3D (ignorowana przez Git)
Makefile                 make all / check / build / tolerance / clean / viewer / site
package.json             narzędzia do kontroli przeglądarki (opcjonalne lokalnie)
README.md                dokumentacja po angielsku
README.pl.md             dokumentacja po polsku
TODO.md                  lista dalszych prac nad domkiem
PLAN.md                  zapis zmian projektowych wersji 2–6
LICENSE                  CC BY-NC-SA 4.0
```

## Dokumentacja

- [Przewodnik budowy](docs/BUILD-GUIDE.md): wydruki, wycinanie, materiały, okucia, montaż, figurki i kontrole.
- [Jak działa generowanie](docs/PIPELINE.md): środowiska, etapy, model danych, konfiguracja i automatyzacja.
- [Publikacja na GitHub](docs/PUBLISHING.md): przygotowanie repozytorium, GitHub Pages i kontrola przeglądarki.
- [Pomysły](docs/IDEAS.md): format Letter, kompilacja w kontenerze, wersja laserowa i gotowe konfiguracje.
- [TODO](TODO.md): dalsze usprawnienia domku.

Dokumenty w katalogu `docs/` są po angielsku. Obie wersje README opisują ten sam projekt i używają tych samych poleceń.

## Bezpieczeństwo

To projekt drewnianej zabawki do samodzielnego wykonania, bez certyfikacji. Kontrole CAD sprawdzają prześwity, ale nie wytrzymałość kleju, stabilność ani bezpieczeństwo zabawki. Najpierw złóż części na sucho z rzeczywistej sklejki i zawiasów. Zaokrąglij wszystkie odsłonięte krawędzie. Dla małych dzieci przechowuj drobne akcesoria i figurki osobno, do zabawy pod nadzorem. Chroń palce przed szczelinami przy zawiasach. Osadź cztery magnesy zaczepów i ograniczników w żywicy epoksydowej i sprawdzaj je przed każdą zabawą: połknięcie magnesów jest niebezpieczne. Używaj wyłącznie podkładu, farby i lakieru z deklaracją zgodności z EN 71-3. Książka podaje przykładowe produkty.

## Stan projektu

- Sprawdzony na macOS (Apple silicon) z Pythonem 3.12 i FreeCAD 1.1.4. Linux i Windows mogą działać z Pythonem dostarczonym przez FreeCAD, ale nie zostały jeszcze sprawdzone.
- Projekt przeszedł kontrole CAD, ale domek nie powstał jeszcze ze sklejki. Po pierwszym montażu na sucho może być potrzebna korekta tolerancji.

## Znaki towarowe i licencja

Copyright © 2026 hvitis. Kod, projekt i wygenerowane z nich pliki są objęte licencją [Creative Commons Uznanie autorstwa–Użycie niekomercyjne–Na tych samych warunkach 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) ([`LICENSE`](LICENSE)). Możesz udostępniać i modyfikować domek do celów niekomercyjnych. Podaj autora i udostępniaj zmiany na tej samej licencji.

Pliki three.js w `source/viewer/vendor/` zachowują własną licencję MIT (`THREE-LICENSE.txt`). Czcionki DejaVu zachowują licencję z `source/fonts/LICENSE_DEJAVU`.

Moomin, postacie Muminków i domek Muminków są znakami towarowymi i utworami chronionymi prawem autorskim Moomin Characters Oy. Licencja projektu nie przyznaje praw do tych elementów. To osobisty, niekomercyjny projekt fanowski. Repozytorium nie zawiera oficjalnych ilustracji ani zdjęć produktów i nie służy do ich rozpowszechniania. Nie sprzedawaj zestawów, książek ani figurek wykonanych na podstawie tego projektu.
