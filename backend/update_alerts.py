import sqlite3
import re

conn = sqlite3.connect('D:/BHOOMI_SETU-main/bhoomisetu.db')
cursor = conn.cursor()

alerts = cursor.execute('SELECT alert_id, project_id, title FROM alerts').fetchall()

for alert_id, project_id, title in alerts:
    # Try to extract Khasra number from title (e.g., "Boundary Dispute Flagged - Khasra 101/1")
    match = re.search(r'Khasra ([\d/]+)', title, re.IGNORECASE)
    if match:
        khasra = match.group(1)
        # Find parcel_id
        parcel = cursor.execute('SELECT parcel_id FROM parcels WHERE project_id = ? AND survey_number LIKE ? LIMIT 1', (project_id, f'%{khasra}%')).fetchone()
        if parcel:
            cursor.execute('UPDATE alerts SET parcel_id = ? WHERE alert_id = ?', (parcel[0], alert_id))
    else:
        # Just pick a random parcel from the project
        parcel = cursor.execute('SELECT parcel_id FROM parcels WHERE project_id = ? LIMIT 1', (project_id,)).fetchone()
        if parcel:
            cursor.execute('UPDATE alerts SET parcel_id = ? WHERE alert_id = ?', (parcel[0], alert_id))

conn.commit()
conn.close()
