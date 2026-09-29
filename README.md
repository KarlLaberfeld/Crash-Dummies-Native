# The Incredible Crash Dummies — native Windows port

**Unvollständige Portierung in Arbeit. Keine fertige Vollversion.**

Ziel ist eine möglichst originalgetreue Windows-Neuimplementierung der
Game-Boy-Fassung. Der aktuelle Entwicklungsstand enthält den ersten Stunt
**Roof Jump** mit rekonstruierten Originalgrafiken, vier Objektlisten und
einer ersten nativen Umsetzung seiner Spielregeln. Die übrigen vier Stunts,
Originalmenüs, Ton und ein vollständiger Abgleich fehlen noch.

Die Windows-EXE besteht aus C++ und Win32. Sie enthält keinen Game-Boy-
CPU-Interpreter, keinen JIT-Recompiler, keinen Emulator-Kern und benötigt
keinen separat installierten Emulator. Die ROM wird ausschließlich offline
als Quelle identifizierter Grafiken und Spieldaten gelesen. Zur Laufzeit wird
das daraus erzeugte Datenpaket `crash.dat` geladen.

## Lokal starten

Nach dem Build `build/CrashDummies.exe` öffnen. `crash.dat` muss daneben liegen.
Die erzeugte EXE läuft direkt unter Windows x64; Python und Zig werden nur
zum Erzeugen der Dateien benötigt.

| Taste | Funktion |
|---|---|
| Enter | Stunt starten / pausieren |
| Pfeile links / rechts | Seitwärts bewegen |
| Pfeile oben / unten | Fallhaltung ändern |
| Z oder A | Erste Aktion / Abspringen |
| X oder S | Zweite Aktion |
| Esc | Pause / fortsetzen |
| R | Stunt neu starten |
| 1–4 | Schwierigkeitsstufe auswählen und neu starten |

Der Dachstunt beginnt mit dem rekonstruierten Kameraschwenk. Das ist kein
Ladebildschirm. Fokusverlust pausiert das Spiel.

## Bauen

Voraussetzungen: Windows x64, Python 3.10+ und [Zig 0.16.0](https://ziglang.org/download/).
Python-Zusatzpakete sind nicht nötig. Zig kann im PATH liegen oder per
`-Compiler` angegeben werden.

```powershell
.\build.ps1 -Rom 'Pfad\zur\Originaldatei.gb' -Test
```

Liegt genau eine `.gb`-Datei im Projektordner, genügt `./build.ps1 -Test`.
Akzeptiert wird nur die US/EU-ROM mit 131072 Bytes und SHA-256
`ef563c4a4b063ea045d71b435dd078c19d0738f85079928803167cee8f34a4ec`.

```powershell
python -m unittest discover -s tests -p 'test_*.py'
.\build\CrashDummies.exe --self-test
.\build\CrashDummies.exe --capture
```

Die nativen Tests prüfen einzelne aus dem Original abgeleitete Regeln,
deterministische Wiederholungen und abgeschlossene Stunt-Durchläufe. Sie sind
**kein Nachweis vollständiger Originaltreue**. Automatisch erzeugte Bilder
werden nur lokal im Buildordner abgelegt.

## Projektstruktur

- `src/`: native Spiellogik, Renderer und Windows-Fenster.
- `tools/extract.py`: reproduzierbare, hashgeprüfte Datenextraktion.
- `tools/disassemble.py`: rein statisches Analysewerkzeug; führt keine ROM aus.
- `tests/`: synthetische Formatprüfungen und native Regeln-/Ablauftests.
- [docs/REVERSE_ENGINEERING.md](docs/REVERSE_ENGINEERING.md): belegte Datenstrukturen und Routinen.
- [docs/STATUS.md](docs/STATUS.md): aktueller Stand und nächste Schritte.

ROM, extrahierte Originalgrafiken, Datenpakete und lokale Analysedumps werden
nicht ins Repository aufgenommen. Sie müssen aus der eigenen Originaldatei
erzeugt werden. Marken und Originalspielinhalte gehören ihren jeweiligen
Rechteinhabern. Das Projekt ist inoffiziell.
