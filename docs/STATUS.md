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
- Erste native Ablauf-/Regeltests liefen durch. Nach Änderungen erneut prüfen.

## Offen

1. Native Tests und erzeugte Ansichten nach den letzten Änderungen prüfen.
2. Quellcode und Dokumentation ins bereits angelegte private Repository übertragen.
3. Dachstunt mit Referenzverhalten vergleichen: Animationstiming, Objektlebensdauer,
   Flugzeug, Ballon, Seil, Ziel/Landung. Bekannte Lücken stehen in
   `REVERSE_ENGINEERING.md`. Keine Vollständigkeit behaupten.
4. Vier weitere Stunts aus ihren Initialisierungen und Handlern rekonstruieren.
5. Originalmenüs, Kampagne, Endsequenz, Musik/Sound portieren.
6. Durchspielbarkeit und Originaltreue verifizieren, portable Distribution erzeugen.

## Automatische Fortsetzung

Der Nutzer hat ausdrücklich angeordnet, nach Erreichen des Nutzungslimits nach
dem Reset automatisch weiterzuarbeiten. Eine aktive Chat-Automatisierung ist
angelegt: `crash-dummies-nach-limit-reset-fortsetzen`, stündlich um Minute 05.
Bei einem Limitabbruch nach Reset hier und im bestehenden Chat fortsetzen.
Keine ROM oder extrahierten Assets auf GitHub hochladen. Den Status aktualisieren,
bevor eine Arbeitseinheit endet. Nur bei wirklichem Gesamtabschluss die
Automatisierung deaktivieren.
