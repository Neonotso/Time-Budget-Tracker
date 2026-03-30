import sqlite3
from datetime import datetime, timedelta

def ticks_to_datetime(ticks):
    # .NET ticks are 100-nanosecond intervals since 0001-01-01
    return datetime(1, 1, 1) + timedelta(microseconds=ticks // 10)

conn = sqlite3.connect('/Users/ryantaylorvegh/.openclaw/workspace/backup_2026-03-13_v4.db')
cursor = conn.cursor()

# Project ID for 'The PIER' is 3
project_id = 3

# Correct Feb 2026 Ticks
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

print("Start,End,DurationHours,Description,Tags")
for r in rows:
    start = ticks_to_datetime(r[0]).strftime("%Y-%m-%d %H:%M")
    end = ticks_to_datetime(r[1]).strftime("%Y-%m-%d %H:%M")
    duration = f"{r[2]:.2f}"
    desc = f'"{str(r[3]).replace("\"", "\"\"")}"' if r[3] else ""
    tags = f'"{str(r[4]).replace("\"", "\"\"")}"' if r[4] else ""
    print(f"{start},{end},{duration},{desc},{tags}")
