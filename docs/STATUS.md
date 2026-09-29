# Arbeitsstand — 29. September 2026

## Auftrag

Möglichst originalgetreue **native** Windows-Portierung der vorhandenen Game-Boy-
ROM, ausdrücklich ohne Emulation und ohne freien Nachbau. Privates Repository:
https://github.com/KarlLaberfeld/TICD-Recompilation

**Der Gesamtauftrag ist nicht abgeschlossen.** Die derzeitige Windows-EXE ist
ein Entwicklungsstand des Dachstunts, keine vollständige Portierung.

## Bisher vorhanden

- Hashgeprüfte lokale Datenextraktion und statisches Disassemblierungswerkzeug.
- Originale Dach-Hintergründe, 69 Sprite-Definitionen, vier Schwierigkeitslisten.
- Native C++-/Win32-Anwendung mit Tastatursteuerung, Pause und Neustart.
- Erste Übersetzung der Dachstunt-Physik, Animationen und Objektinteraktionen.
- Lokaler Compiler: `.tools/zig-x86_64-windows-0.16.0/zig.exe`.
- Build: `powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1 -Test`.
- Buildausgabe: `build/CrashDummies.exe`, dazu lokal `build/crash.dat`.
- Quellcode und Dokumentation sind im privaten GitHub-Repository veröffentlicht.
- Windows-x64-GUI-Build ohne Konsolenfenster geprüft (PE-Subsystem 2).

## Fortsetzung nach Limitreset — 29. September, ab 16:59 Uhr

Der Chatverlauf bestätigt Limitabbrüche um 14:07, 15:05 und 16:07 Uhr
(Europe/Berlin). Bei Wiederaufnahme erlaubte das Konto normale Nutzung;
das Fünfstundenfenster war zu 5 % genutzt. Kein Reset-Guthaben verbraucht.

Neu rekonstruiert und korrigiert:

- Sprite-Ursprung und Spiegelzentrum aus dem Originalrenderer; Grafiken passen
  jetzt zu den Kollisionspositionen. Neues lokales Datenformat `TICDNAT2`.
- Sichtbarkeitsgrenzen, Wiedererscheinen von Objekten und dauerhafte Zielentnahme.
- Aktivierung der Flugzeuge/Ballons nach dem Kameraschwenk, Sprungeingabereihenfolge.
- Aufwärtskollision an Markisen, Flugzeugbetäubung und gleichzeitige Haltungstasten.
- Landung mit Original-Zerlegeanimation, Kopfaufprall, verzögertem Ergebnis und
  Unterscheidung zwischen Erfolg, perfektem Ergebnis und zu wenigen Treffern.

Prüfung: 10 Python-Tests und 48.853 native Prüfungen erfolgreich; alle vier
Schwierigkeitslisten erreichen ein Stuntende ohne ungültige Animationsbefehle.
Die Zahl enthält wiederholte Invariantenprüfungen, keine ebenso große Zahl
unabhängiger Testfälle. Fensterstart und Bildausgabe erfolgreich. Kein Beleg
vollständiger Originaltreue: bisher statischer Vergleich mit Originalroutinen.

## Offen

1. Dachstunt weiter mit Originalroutinen abgleichen: Animationstiming, Objektlebensdauer,
   Flugzeug, Ballon, Seil, Ziel/Landung. Bekannte Lücken stehen in
   `REVERSE_ENGINEERING.md`. Keine Vollständigkeit behaupten.
2. Vier weitere Stunts aus ihren Initialisierungen und Handlern rekonstruieren.
3. Originalmenüs, Kampagne, Endsequenz, Musik/Sound portieren.
4. Durchspielbarkeit und Originaltreue verifizieren, portable Distribution erzeugen.

## Automatische Fortsetzung

Der Nutzer hat ausdrücklich angeordnet, nach Erreichen des Nutzungslimits nach
dem Reset automatisch weiterzuarbeiten. Eine aktive Chat-Automatisierung ist
angelegt: `crash-dummies-nach-limit-reset-fortsetzen`, stündlich um Minute 05.
Bei einem Limitabbruch nach Reset hier und im bestehenden Chat fortsetzen.
Keine ROM oder extrahierten Assets auf GitHub hochladen. Den Status aktualisieren,
bevor eine Arbeitseinheit endet. Nur bei wirklichem Gesamtabschluss die
Automatisierung deaktivieren.
