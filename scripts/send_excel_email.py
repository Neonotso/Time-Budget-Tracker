import base64
from pathlib import Path
from agentmail import AgentMail

WORKSPACE = Path("/Users/ryantaylorvegh/.openclaw/workspace")
AGENTMAIL_ENV = WORKSPACE / ".secrets" / "agentmail.env"

def _load_env(path: Path) -> dict[str, str]:
    vals = {}
    if not path.exists(): return vals
    for raw in path.read_text().splitlines():
        s = raw.strip()
        if not s or s.startswith("#") or "=" not in s: continue
        k, v = s.split("=", 1)
        vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals

env = _load_env(AGENTMAIL_ENV)
api_key = env.get("AGENTMAIL_API_KEY") or env.get("API_KEY")
inbox = env.get("AGENTMAIL_FROM_INBOX") or "sallysquirrel@agentmail.to"

excel_path = WORKSPACE / "2026 02 February Hours.xlsx"
excel_content = excel_path.read_bytes()
encoded_excel = base64.b64encode(excel_content).decode()

client = AgentMail(api_key=api_key)
client.inboxes.messages.send(
    inbox_id=inbox,
    to="ryan.vegh@gmail.com",
    subject="2026 02 February Hours.xlsx",
    text="Hi Ryan, here is the formatted Excel file for your February hours.",
    attachments=[{
        "filename": "2026 02 February Hours.xlsx",
        "content": encoded_excel
    }]
)
print("Email sent.")
