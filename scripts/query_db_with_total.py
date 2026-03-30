import sqlite3
from datetime import datetime, timedelta

def ticks_to_datetime(ticks):
    return datetime(1, 1, 1) + timedelta(microseconds=ticks // 10)

conn = sqlite3.connect('/Users/ryantaylorvegh/.openclaw/workspace/backup_2026-03-13_v4.db')
cursor = conn.cursor()

project_id = 3
start_tick = 639055188000000000
end_tick = 639079380000000000

query = """
SELECT 
  WU.Start, 
  WU.End, 
  (WU.Duration / 36000000000.0) as DurationHours, 
  WU.Description, 
  GROUP_CONCAT(T.Value, ', ') as Tags 
FROM WorkUnits WU 
LEFT JOIN WorkUnitTags WUT ON WU.WorkUnitId = WUT.WorkUnitId 
LEFT JOIN Tags T ON WUT.TagId = T.TagId 
WHERE WU.ProjectId = ?
  AND WU.Start >= ? 
  AND WU.Start < ?
GROUP BY WU.WorkUnitId
"""

cursor.execute(query, (project_id, start_tick, end_tick))
rows = cursor.fetchall()

total_hours = 0.0
csv_lines = ["Start,End,DurationHours,Description,Tags"]

for r in rows:
    start = ticks_to_datetime(r[0]).strftime("%Y-%m-%d %H:%M")
    end = ticks_to_datetime(r[1]).strftime("%Y-%m-%d %H:%M")
    duration = r[2]
    total_hours += duration
    desc = f'"{str(r[3]).replace("\"", "\"\"")}"' if r[3] else ""
    tags = f'"{str(r[4]).replace("\"", "\"\"")}"' if r[4] else ""
    csv_lines.append(f"{start},{end},{duration:.2f},{desc},{tags}")

csv_lines.append(f",,Total Hours: {total_hours:.2f},,")
print("\n".join(csv_lines))
