import pandas as pd
from datetime import datetime, timedelta

collaboratori = [
    "DONATO", "STRINA", "QUARANTA MG", "MUSUMECI", "TRAMONTANA", "BRUNELLI",
    "NADDEI", "PRINCIPATO", "BRUNI", "RIGGIERO", "DARIMINI", "GIUSTI",
    "DONNARUMMA", "CHIARION", "SUPPLENTE", "RONCONI", "BAGLIVO", "ERBISTI",
    "PERRELLA", "BALLETTA", "INGARGIOLA", "PERASOLE", "TODISCO", "QUARANTA S",
    "ANGELONE", "ANNINO", "DI DIO", "SCALIA", "ORLANDO", "SALERNO",
    "COTRONEO", "SUPPLENTE 30H", "GRECO", "MONACO", "NAPPI", "PASQUINO",
    "RUSSO", "VITIELLO", "MIRARCHI", "SCALA", "PENSOSI", "VARGAS(su Di Francia)",
    "DI ROSA", "MATTIELLO", "CARDONA", "DE ROSA", "IMPIOMBATO", "SPERA",
    "SALADINO", "Suppl3", "Suppl4"
]

reparti_postazioni = {
    '207': 2, '208/218BIS': 2, '261/251': 2, '222': 2, '228': 6, '224': 1,
    '245': 2, '203': 2, 'PAGODA 209': 2, 'CEDRI 251': 3, '236': 2, '217': 2,
    '237': 2, '250': 1, '218': 1, 'PD': 4, 'PN': 3, 'SN': 1, '201 M': 1,
    '240 G': 1, '230 T': 2, '243': 7
}

reparto_228 = ["RIGGIERO", "DARIMINI", "GIUSTI", "DONNARUMMA", "CHIARION"]
reparto_cedri = ["TODISCO", "QUARANTA S", "ANGELONE"]
reparto_pn = ["BRUNELLI", "NADDEI", "RUSSO"]
solo_mattina = ["COTRONEO", "GRECO"]
mattina_pomeriggio_only = ["ANGELONE", "TRAMONTANA", "CHIARION", "RONCONI"]
no_domenica = ["ANGELONE", "TRAMONTANA", "CHIARION", "RONCONI"]

assigned_collaboratori = set(reparto_228 + reparto_cedri + reparto_pn)
remaining_collaboratori = [c for c in collaboratori if c not in assigned_collaboratori]

reparti_list = list(reparti_postazioni.keys())
reparti_no_special = [r for r in reparti_list if r not in ['228', 'CEDRI 251', 'PN']]

collab_to_reparto = {}
for c in reparto_228:
    collab_to_reparto[c] = '228'
for c in reparto_cedri:
    collab_to_reparto[c] = 'CEDRI 251'
for c in reparto_pn:
    collab_to_reparto[c] = 'PN'

idx = 0
for reparto in reparti_no_special:
    num_postazioni = reparti_postazioni[reparto]
    for _ in range(num_postazioni):
        if idx < len(remaining_collaboratori):
            collab_to_reparto[remaining_collaboratori[idx]] = reparto
            idx += 1

start_date = datetime(2025, 9, 15)
end_date = datetime(2026, 7, 5)

weeks = []
current = start_date
while current <= end_date:
    week_start = current
    week_end = current + timedelta(days=6)
    week_label = f"{week_start.strftime('%d/%m/%Y')}-{week_end.strftime('%d/%m/%Y')}"
    weeks.append((week_label, week_start, week_end))
    current += timedelta(days=7)

reparto_to_collabs = {}
for collab, reparto in collab_to_reparto.items():
    if reparto not in reparto_to_collabs:
        reparto_to_collabs[reparto] = []
    reparto_to_collabs[reparto].append(collab)

records = []

reparto_rotation_idx = {reparto: 0 for reparto in reparti_list}
pn_rotation_idx = 0

for week_idx, (week_label, week_start, week_end) in enumerate(weeks):
    for reparto, collabs in reparto_to_collabs.items():
        if reparto == 'PN':
            turni_pn = ['mattina', 'pomeriggio', 'sera']
            for i, turno in enumerate(turni_pn):
                collab_idx = (pn_rotation_idx + i) % len(reparto_pn)
                records.append({
                    'collaboratore': reparto_pn[collab_idx],
                    'reparto': 'PN',
                    'periodo': week_label,
                    'turno': turno
                })
            pn_rotation_idx = (pn_rotation_idx + 1) % len(reparto_pn)
        else:
            rotation_idx = reparto_rotation_idx[reparto]
            mattina_collab = collabs[rotation_idx % len(collabs)]
            
            records.append({
                'collaboratore': mattina_collab,
                'reparto': reparto,
                'periodo': week_label,
                'turno': 'mattina'
            })
            
            for collab in collabs:
                if collab == mattina_collab:
                    continue
                if collab in solo_mattina:
                    records.append({
                        'collaboratore': collab,
                        'reparto': reparto,
                        'periodo': week_label,
                        'turno': 'mattina'
                    })
                elif collab in mattina_pomeriggio_only:
                    continue
                else:
                    records.append({
                        'collaboratore': collab,
                        'reparto': reparto,
                        'periodo': week_label,
                        'turno': 'pomeriggio'
                    })
            
            reparto_rotation_idx[reparto] = (rotation_idx + 1) % len(collabs)

domenica_collaboratori = [c for c in collaboratori if c not in no_domenica]
domenica_rotation_idx = 0
domenica_sera_last_week = None

for week_idx, (week_label, week_start, week_end) in enumerate(weeks):
    domenica = week_end
    domenica_str = domenica.strftime('%d/%m/%Y')
    
    turni_domenica = ['mattina', 'pomeriggio', 'sera']
    
    for turno in turni_domenica:
        valid_collab = False
        attempts = 0
        while not valid_collab and attempts < len(domenica_collaboratori):
            collab_idx = domenica_rotation_idx % len(domenica_collaboratori)
            collab = domenica_collaboratori[collab_idx]
            
            if turno == 'mattina' and domenica_sera_last_week == collab:
                domenica_rotation_idx += 1
                attempts += 1
                continue
            
            valid_collab = True
            records.append({
                'collaboratore': collab,
                'reparto': 'DOMENICA',
                'periodo': domenica_str,
                'turno': turno
            })
            
            if turno == 'sera':
                domenica_sera_last_week = collab
            
            domenica_rotation_idx += 1
            break

df = pd.DataFrame(records)
df.to_csv('turni.csv', index=False, encoding='utf-8-sig')