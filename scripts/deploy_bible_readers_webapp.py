#!/usr/bin/env python3
from pathlib import Path
import json

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

ENV_PATH = Path('/Users/ryantaylorvegh/.openclaw/workspace/.secrets/google_sheets & drive.env')
SHEET_ID = '16f75U8IZjGkrgNeUyk7haDU-_isrBlmd6glnW0ah5BA'
PROJECT_TITLE = '8:1 Bible Readers Signup App'
DEPLOY_STATE_PATH = Path('/Users/ryantaylorvegh/.openclaw/workspace/scripts/.bible_readers_deploy.json')

GS_PATH = Path('/Users/ryantaylorvegh/.openclaw/workspace/scripts/bible_readers_webapp.gs')
HTML_PATH = Path('/Users/ryantaylorvegh/.openclaw/workspace/scripts/bible_readers_webapp_index.html')


def load_env(path: Path):
    data = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def get_creds(env):
    creds = Credentials(
        token=env.get('GOOGLE_SHEETS_ACCESS_TOKEN') or None,
        refresh_token=env.get('GOOGLE_SHEETS_REFRESH_TOKEN'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=env.get('GOOGLE_SHEETS_CLIENT_ID'),
        client_secret=env.get('GOOGLE_SHEETS_CLIENT_SECRET'),
    )
    if not creds.valid:
        creds.refresh(Request())
    return creds


def load_state():
    if not DEPLOY_STATE_PATH.exists():
        return {}
    return json.loads(DEPLOY_STATE_PATH.read_text())


def save_state(state: dict):
    DEPLOY_STATE_PATH.write_text(json.dumps(state, indent=2) + '\n')


def build_content_body():
    return {
        'files': [
            {
                'name': 'Code',
                'type': 'SERVER_JS',
                'source': GS_PATH.read_text(),
            },
            {
                'name': 'index',
                'type': 'HTML',
                'source': HTML_PATH.read_text(),
            },
            {
                'name': 'appsscript',
                'type': 'JSON',
                'source': json.dumps({
                    'timeZone': 'America/Detroit',
                    'exceptionLogging': 'STACKDRIVER',
                    'runtimeVersion': 'V8',
                    'webapp': {
                        'access': 'ANYONE_ANONYMOUS',
                        'executeAs': 'USER_DEPLOYING'
                    }
                }),
            },
        ]
    }


def ensure_project(svc, state):
    script_id = state.get('scriptId')
    if script_id:
        return script_id

    project = svc.projects().create(body={
        'title': PROJECT_TITLE,
        'parentId': SHEET_ID,
    }).execute()
    script_id = project['scriptId']
    print('Created script project:', script_id)
    state['scriptId'] = script_id
    save_state(state)
    return script_id


def create_version(svc, script_id):
    version = svc.projects().versions().create(
        scriptId=script_id,
        body={'description': 'Deploy from OpenClaw automation'}
    ).execute()
    version_number = version['versionNumber']
    print('Created version:', version_number)
    return version_number


def ensure_deployment(svc, state, script_id, version_number):
    deployment_id = state.get('deploymentId')

    if not deployment_id:
        deployment = svc.projects().deployments().create(
            scriptId=script_id,
            body={
                'versionNumber': version_number,
                'manifestFileName': 'appsscript',
                'description': 'Public signup web app',
            }
        ).execute()
        deployment_id = deployment['deploymentId']
        state['deploymentId'] = deployment_id
        save_state(state)
        print('Created deployment:', deployment_id)
    else:
        svc.projects().deployments().update(
            scriptId=script_id,
            deploymentId=deployment_id,
            body={
                'deploymentConfig': {
                    'scriptId': script_id,
                    'versionNumber': version_number,
                    'manifestFileName': 'appsscript',
                    'description': 'Public signup web app',
                }
            }
        ).execute()
        print('Updated deployment:', deployment_id)

    dep = svc.projects().deployments().get(scriptId=script_id, deploymentId=deployment_id).execute()
    return dep


def main():
    env = load_env(ENV_PATH)
    creds = get_creds(env)
    svc = build('script', 'v1', credentials=creds)

    state = load_state()
    script_id = ensure_project(svc, state)

    svc.projects().updateContent(scriptId=script_id, body=build_content_body()).execute()
    print('Uploaded project content.')

    version_number = create_version(svc, script_id)
    dep = ensure_deployment(svc, state, script_id, version_number)

    web_url = None
    for ep in dep.get('entryPoints', []):
        web = ep.get('webApp', {})
        if web.get('url'):
            web_url = web['url']
            break

    print('Deployment details:')
    print(json.dumps(dep, indent=2))
    if web_url:
        print('\nWeb app URL:')
        print(web_url)


if __name__ == '__main__':
    main()
