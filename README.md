# Semestrální práce - ORIS analyser

## Spuštění:

Aplikace se spouští ve složce semestral příkazem:
*~ python main.py*

Po spuštění se v prohlížeči otevře okno s aplikací na adrese http://localhost:8501

## Základní funkcionality

Stránka se skládá z hlavní části a bočního panelu, kde uživatel nastavuje, co se mu má zobrazit.
Aplikace má dvě funkcionality:
- analýza mezičasů libovolné kategorie
- analýza výsledků závodníka

Aplikace umí interpretovat všechny individuální jednorázové závody, které mají výsledky nahrané přímo v ORISu.

### Analýza mezičasů

Na bočním panelu musí uživatel pro analýzu zadat unikátní kód kategorie nebo vyplnit ID závodu a jméno kategorie.
Pokud by neznal id závodu, lze si ho vyhledat v kalendáři. Kalendář zobrazuje vždy jeden rok, který je možné filtrovat pokročilýmí filtry dle části jména nebo úrovně závodu, lze zde i povolit zobrazení všech typů orientačních sportů (výchozí nastavení je pouze OB) a neoficiálních závodů ve vyhledávání.

Po zadání id kategorie nebo jména se načte stránka s grafem a tabulkou. V grafu jsou zobrazeny časy všech závodníků(závodnic) na kontrolách, v základu podle startovního času, nebo podle ztráty na průběžně vedoucího.
V tabulce jsou mezičasy na kontrolách i s pořadím, v jedné mezičasy na úsecích, v druhé celkové časy.

Graf je interaktivní, na každé kontrole se po najetí myší ukážou časy zobrazených závodníků, každého závodníka lze ručně vypnout, nebo upravit počet zobrazovaných lidí sliderem nad grafem. V multiselectu lze filtrovat i jednotlivé lidi, ti jsou pak v tabulce podbarveni.

Dole na stánce se nachází tlačítko *Export Analysis*. Po kliknutí se vygeneruje pdfko, které pak lze přes odkaz stáhnout.
V pdf se nachází úvodní stránka, a dvakrát vyexportovaný graf (omezený na max 22 závodníků, víc se jich nevejde do legendy) a tabulka s časy a pořadími všech závodníků (přizpůsobuje svojí šířku obsahu), první s celkovým časem, a druhé s jednotlivými mezičasy.

### Analýza závodníka

*bohužel ORIS API nemá metodu pro přímé vytažení výsledků, takže je k vykonání třeba série requestů a načítání trvá déle, cca 1 vteřinu za každý závod*

Pro analýzu musí uživatel zadat registrační číslo závodníka a vybrat rok k analýze. Po časové prodlevě se načte stránka s tabulkou s výsledky v dané sezóně a grafy dle úrovně závodů s puntíky v barvě dle disciplíny (sprint, krátká, klasika). Po najetí na bod v grafu se zobrazí podrobnosti o daném závodě.