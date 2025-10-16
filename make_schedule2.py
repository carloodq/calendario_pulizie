import pandas as pd
from datetime import datetime, timedelta
import random

# Configurazione
reparti_postazioni = {
    '207': 2, '208/218BIS': 2, '261/251': 2, '222': 2, '228': 6, '224': 1,
    '245': 2, '203': 2, 'PAGODA 209': 2, 'CEDRI 251': 3, '236': 2, '217': 2,
    '237': 2, '250': 1, '218': 1, 'PD': 4, 'PN': 3, 'SN': 1, '201 M': 1,
    '240 G': 1, '230 T': 2, '243': 7
}

collaboratori = [
    "DONATO", "STRINA", "QUARANTA MG", "MUSUMECI", "TRAMONTANA", "BRUNELLI",
    "NADDEI", "PRINCIPATO", "BRUNI", "RIGGIERO", "DARIMINI", "GIUSTI",
    "DONNARUMMA", "CHIARION", "SUPPLENTE", "RONCONI", "BAGLIVO", "ERBISTI",
    "PERRELLA", "BALLETTA", "INGARGIOLA", "PERASOLE", "TODISCO", "QUARANTA S",
    "ANGELONE", "ANNINO", "DI DIO", "SCALIA", "ORLANDO", "SALERNO", "COTRONEO",
    "SUPPLENTE 30H", "GRECO", "MONACO", "NAPPI", "PASQUINO", "RUSSO", "VITIELLO",
    "MIRARCHI", "SCALA", "PENSOSI", "VARGAS(su Di Francia)", "DI ROSA",
    "MATTIELLO", "CARDONA", "DE ROSA", "IMPIOMBATO", "SPERA", "SALADINO",
    "Suppl3", "Suppl4"
]

solo_mattina = ["COTRONEO", "GRECO"]
no_sera = ["ANGELONE", "TRAMONTANA", "CHIARION", "RONCONI"]
esclusi_domenica = ["ANGELONE", "TRAMONTANA", "CHIARION", "RONCONI"]

# Assegnazione fissa collaboratori a reparti
assegnazioni_fisse = {
    "RIGGIERO": "228", "DARIMINI": "228", "GIUSTI": "228",
    "DONNARUMMA": "228", "CHIARION": "228",
    "TODISCO": "CEDRI 251", "QUARANTA S": "CEDRI 251", "ANGELONE": "CEDRI 251",
    "BRUNELLI": "PN", "NADDEI": "PN", "RUSSO": "PN"
}

# Distribuzione altri collaboratori
altri_collaboratori = [c for c in collaboratori if c not in assegnazioni_fisse]
altri_reparti = [r for r in reparti_postazioni.keys() if r not in ["228", "CEDRI 251", "PN"]]

random.seed(42)
for i, collab in enumerate(altri_collaboratori):
    reparto = altri_reparti[i % len(altri_reparti)]
    assegnazioni_fisse[collab] = reparto

# Generazione date
data_inizio = datetime(2025, 9, 15)
data_fine = datetime(2026, 7, 5)

settimane = []
current = data_inizio
while current <= data_fine:
    lunedi = current
    venerdi = current + timedelta(days=4)
    settimane.append(f"{lunedi.strftime('%d/%m/%Y')}-{venerdi.strftime('%d/%m/%Y')}")
    current += timedelta(days=7)

domeniche = []
current = data_inizio
while current <= data_fine:
    giorno_settimana = current.weekday()
    giorni_a_domenica = (6 - giorno_settimana) % 7
    domenica = current + timedelta(days=giorni_a_domenica)
    if domenica <= data_fine and domenica.strftime('%d/%m/%Y') not in domeniche:
        domeniche.append(domenica.strftime('%d/%m/%Y'))
    current += timedelta(days=7)

# Dataframe finale
rows = []

# Turni settimanali - TUTTI lavorano OGNI settimana
for settimana in settimane:
    for collab in collaboratori:
        reparto = assegnazioni_fisse[collab]
        
        if reparto == "PN":
            # Rotazione PN: mattina, pomeriggio, sera
            idx_settimana = settimane.index(settimana)
            collab_pn = ["BRUNELLI", "NADDEI", "RUSSO"]
            idx_collab = collab_pn.index(collab)
            turni_pn = ["mattina", "pomeriggio", "sera"]
            turno = turni_pn[(idx_settimana + idx_collab) % 3]
        elif collab in solo_mattina:
            turno = "mattina"
        else:
            # Rotazione solo mattina/pomeriggio (NO sera per turni settimanali)
            idx_settimana = settimane.index(settimana)
            turni_normali = ["mattina", "pomeriggio"]
            turno = turni_normali[(idx_settimana + collaboratori.index(collab)) % 2]
        
        rows.append({
            'collaboratore': collab,
            'reparto': reparto,
            'periodo': settimana,
            'turno': turno
        })

# Domeniche - rotazione
collab_domenica = [c for c in collaboratori if c not in esclusi_domenica]
turni_domenica = ["mattina", "pomeriggio", "sera"]

# Mappatura domenica -> settimana successiva
domenica_to_settimana = {}
for domenica in domeniche:
    data_dom = datetime.strptime(domenica, '%d/%m/%Y')
    lunedi_dopo = data_dom + timedelta(days=1)
    for settimana in settimane:
        inizio_sett = datetime.strptime(settimana.split('-')[0], '%d/%m/%Y')
        if inizio_sett == lunedi_dopo:
            domenica_to_settimana[domenica] = settimana
            break

# Assegnazione domeniche
collab_sera_domenica = {}
for i, domenica in enumerate(domeniche):
    for j, turno in enumerate(turni_domenica):
        idx = (i * 3 + j) % len(collab_domenica)
        collab = collab_domenica[idx]
        
        # Verifica vincolo solo_mattina
        if collab in solo_mattina and turno != "mattina":
            # Cerca un altro collaboratore
            for k in range(len(collab_domenica)):
                idx_alt = (idx + k) % len(collab_domenica)
                collab_alt = collab_domenica[idx_alt]
                if collab_alt not in solo_mattina:
                    collab = collab_alt
                    break
        
        reparto = assegnazioni_fisse[collab]
        rows.append({
            'collaboratore': collab,
            'reparto': reparto,
            'periodo': domenica,
            'turno': turno
        })
        
        if turno == "sera":
            collab_sera_domenica[domenica] = collab

# Verifica e correzione vincolo sera domenica -> no mattina lunedì
for domenica, collab_sera in collab_sera_domenica.items():
    if domenica in domenica_to_settimana:
        settimana_dopo = domenica_to_settimana[domenica]
        # Trova turno del collaboratore nella settimana dopo
        for row in rows:
            if (row['collaboratore'] == collab_sera and 
                row['periodo'] == settimana_dopo and 
                row['turno'] == 'mattina'):
                # Cambia il turno da mattina a pomeriggio
                if collab_sera in solo_mattina:
                    print(f"ATTENZIONE: {collab_sera} ha vincolo solo_mattina ma lavora sera domenica {domenica}")
                else:
                    row['turno'] = 'pomeriggio'

# Creazione DataFrame
df = pd.DataFrame(rows)
df.to_csv('turni.csv', index=False)

# VALIDAZIONI
print("\n=== VALIDAZIONE CALENDARIO ===\n")

# 1. Consistenza Reparto
print("1. VERIFICA CONSISTENZA REPARTO:")
inconsistenze = []
for collab in collaboratori:
    reparti_collab = df[df['collaboratore'] == collab]['reparto'].unique()
    if len(reparti_collab) > 1:
        inconsistenze.append(f"{collab}: {reparti_collab}")

if inconsistenze:
    print("ERRORE - Inconsistenze trovate:")
    for inc in inconsistenze:
        print(f"  {inc}")
else:
    print("✓ Tutti i collaboratori hanno un reparto consistente")

# 2. No Reparto Generico
print("\n2. VERIFICA NO REPARTO GENERICO:")
reparti_generici = df[df['reparto'] == 'DOMENICA']
if len(reparti_generici) > 0:
    print(f"ERRORE - Trovate {len(reparti_generici)} righe con reparto='DOMENICA'")
else:
    print("✓ Nessuna riga con reparto generico")

# 3. Vincolo Sera-Mattina
print("\n3. VERIFICA VINCOLO SERA DOMENICA -> NO MATTINA LUNEDÌ:")
violazioni = []
for domenica, collab_sera in collab_sera_domenica.items():
    if domenica in domenica_to_settimana:
        settimana_dopo = domenica_to_settimana[domenica]
        turno_dopo = df[(df['collaboratore'] == collab_sera) & 
                       (df['periodo'] == settimana_dopo)]['turno'].values
        if len(turno_dopo) > 0 and turno_dopo[0] == 'mattina':
            violazioni.append(f"{collab_sera}: sera {domenica} -> mattina {settimana_dopo}")

if violazioni:
    print("ERRORE - Violazioni vincolo sera-mattina:")
    for v in violazioni:
        print(f"  {v}")
else:
    print("✓ Vincolo sera-mattina rispettato")

# 4. Verifica turni settimanali solo mattina/pomeriggio (tranne PN)
print("\n4. VERIFICA TURNI SETTIMANALI (NO SERA TRANNE PN):")
turni_sera_non_pn = df[(df['periodo'].str.contains('-')) & 
                       (df['turno'] == 'sera') & 
                       (df['reparto'] != 'PN')]
if len(turni_sera_non_pn) > 0:
    print(f"ERRORE - Trovati {len(turni_sera_non_pn)} turni sera settimanali per reparti diversi da PN:")
    for _, row in turni_sera_non_pn.iterrows():
        print(f"  {row['collaboratore']} - {row['reparto']} - {row['periodo']}")
else:
    print("✓ Nessun turno sera settimanale per reparti diversi da PN")

# 5. Riepilogo
print("\n5. RIEPILOGO ASSEGNAZIONI:")
for collab in sorted(collaboratori):
    reparto = df[df['collaboratore'] == collab]['reparto'].iloc[0]
    num_turni = len(df[df['collaboratore'] == collab])
    print(f"  {collab:30} -> {reparto:15} ({num_turni} turni)")

# 6. Conferma Vincoli
print("\n6. VERIFICA VINCOLI SPECIALI:")

# Solo mattina
print("\n  a) Solo Mattina (COTRONEO, GRECO):")
for collab in solo_mattina:
    turni_collab = df[df['collaboratore'] == collab]['turno'].unique()
    if len(turni_collab) == 1 and turni_collab[0] == 'mattina':
        print(f"    ✓ {collab}: solo mattina")
    else:
        print(f"    ✗ {collab}: turni = {turni_collab}")

# No sera (in settimana)
print("\n  b) No Sera Settimanale (tutti tranne PN):")
turni_sera_sett = df[(df['periodo'].str.contains('-')) & 
                     (df['turno'] == 'sera') & 
                     (df['reparto'] != 'PN')]
if len(turni_sera_sett) == 0:
    print(f"    ✓ Nessun collaboratore (tranne PN) ha turni sera settimanali")
else:
    print(f"    ✗ Trovati {len(turni_sera_sett)} turni sera settimanali non PN")

# Esclusi domenica
print("\n  c) Esclusi Domenica (ANGELONE, TRAMONTANA, CHIARION, RONCONI):")
for collab in esclusi_domenica:
    domeniche_collab = df[(df['collaboratore'] == collab) & (df['periodo'].str.contains('/'))]
    periodi_dom = [p for p in domeniche_collab['periodo'].values if '/' in p and '-' not in p]
    if len(periodi_dom) > 0:
        print(f"    ✗ {collab}: lavora {len(periodi_dom)} domeniche")
    else:
        print(f"    ✓ {collab}: non lavora domeniche")

# PN rotazione
print("\n  d) PN Rotazione (BRUNELLI, NADDEI, RUSSO):")
for collab in ["BRUNELLI", "NADDEI", "RUSSO"]:
    turni_collab = df[(df['collaboratore'] == collab) & (df['reparto'] == 'PN')]['turno'].unique()
    print(f"    {collab}: turni = {turni_collab}")

# 7. Verifica tutti lavorano tutte le settimane
print("\n7. VERIFICA TUTTI LAVORANO TUTTE LE SETTIMANE:")
for collab in collaboratori:
    settimane_lavorate = df[(df['collaboratore'] == collab) & (df['periodo'].str.contains('-'))]['periodo'].nunique()
    if settimane_lavorate != len(settimane):
        print(f"  ✗ {collab}: lavora {settimane_lavorate}/{len(settimane)} settimane")
    else:
        print(f"  ✓ {collab}: lavora tutte le {len(settimane)} settimane")

print("\n=== FILE turni.csv CREATO CON SUCCESSO ===")