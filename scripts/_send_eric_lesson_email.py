from pathlib import Path
from agentmail import AgentMail

env_path = Path('/Users/ryantaylorvegh/.openclaw/workspace/.secrets/agentmail.env')
vals = {}
for raw in env_path.read_text().splitlines():
    s = raw.strip()
    if not s or s.startswith('#') or '=' not in s:
        continue
    k, v = s.split('=', 1)
    vals[k.strip()] = v.strip().strip('"').strip("'")

api_key = vals.get('AGENTMAIL_API_KEY') or vals.get('API_KEY')
inbox = vals.get('AGENTMAIL_FROM_INBOX') or 'sallysquirrel@agentmail.to'

client = AgentMail(api_key=api_key)
client.inboxes.messages.send(
    inbox_id=inbox,
    to=['er841ra@gmail.com'],
    cc=['ryan.vegh@gmail.com'],
    subject='Voice Lesson -- 03-12-26',
    text=(
        'Hi Eric,\n\n'
        "Ryan's voice lesson notes and lesson recording have been uploaded for you.\n"
        'Files uploaded: Eric - page 4.png, Eric — 03-12-26.m4a\n'
        'Drive folder: https://drive.google.com/drive/folders/1ZyLAz8akC1oaxs4Mw1xpriyWwuib9h94\n\n'
        'Best,\n'
        'Sally, Ryan’s assistant'
    ),
)
print('SENT')
