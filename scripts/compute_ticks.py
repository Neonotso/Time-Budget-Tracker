from datetime import datetime

# February 1, 2026 00:00:00
start_dt = datetime(2026, 2, 1)
# March 1, 2026 00:00:00
end_dt = datetime(2026, 3, 1)

# .NET ticks: 100-nanosecond intervals
# The ticks from 0001-01-01 to 2026-02-01
start_ticks = int(start_dt.timestamp() * 10000000) + 621355968000000000
end_ticks = int(end_dt.timestamp() * 10000000) + 621355968000000000

print(f"Start Ticks: {start_ticks}")
print(f"End Ticks: {end_ticks}")
