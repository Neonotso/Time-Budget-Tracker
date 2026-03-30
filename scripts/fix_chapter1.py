import os
import re
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

client_id = os.environ.get('GOOGLE_SHEETS_CLIENT_ID')
client_secret = os.environ.get('GOOGLE_SHEETS_CLIENT_SECRET')
refresh_token = os.environ.get('GOOGLE_SHEETS_REFRESH_TOKEN')

creds = Credentials(None, refresh_token=refresh_token, token_uri='https://oauth2.googleapis.com/token', client_id=client_id, client_secret=client_secret)
creds.refresh(Request())

docs_service = build('docs', 'v1', credentials=creds)
doc_id = '1zzdaDe0VFVtwIcbzuNJscK_b5g6iUEa1Ydi0AUFwtsQ'

# Fixed Chapter 1 text with:
# - Double quotes as default, single quotes for nested quotes
# - No double paragraph breaks
chapter1_fixed = """Chapter 1

"Training felt like we were prepping for a crash landing tomorrow," Nathan chuckled. "Colten had me in the control room for reactor shutdown drills. He kept saying, 'If you hesitate, you die.' Real motivational."

Flora laughed softly. "Sounds like him."

Nathan nodded. "Saw you with Alfred earlier. What do you think of him?"

Flora hesitated, then shrugged. "He's quiet. Protective. I think he's very observant, even when it looks like he's not."

Nathan smirked. "That's Alfred."

They stood together for a moment, the breeze brushing past them. The moment felt normal—almost peaceful. But Nathan could feel the weight behind it. Flora's smile didn't reach her eyes. His own thoughts kept circling back to Zara.

"She would have loved the survival class," Flora said suddenly, her voice softer. Nathan nodded. "She would have aced it and then come to help us if we struggled," he said. Flora smiled, but it faded quickly.

"Something happened."

Nathan turned toward her. "What do you mean?"

She looked down at her hands. "Nalie was in my class. She bumped me—hard. Knocked my notebook out of my hands."

Nathan's jaw tightened. "Did she say anything?"

"Just, 'Watch it,' like it was my fault." Flora's voice was quiet, but steady.

Nathan felt heat rise in his chest. "Did anyone see?"

Flora nodded.

"He didn't say anything right away," Flora continued.

Nathan stared at her, trying to read the emotion behind her words. "Are you okay?"

Flora shrugged. "I'm alright, I didn't expect this to happen on my first day." Flora hugged herself, but then she looked up.

"I hear it's worth it. The progress and the pain of studying lead you to what you love doing. If God has called you, shouldn't you pursue it?"

Nathan nodded and pondered the idea. Zara, Zeb, and even he shared a passion for the stars and space, all wanting to explore them.

"Running towards the call sounds about right, to explore what God created," he replied.

They both stood in silence, and he could sense that Flora was feeling more at ease, which was a good thing. Just then, Dan walked toward them, his face lit with a full smile.

"Hi Nathan, Flora. It's nice to see you again."

Nathan nodded. "Hi Dan. We're just waiting for Zeb, but we can't talk while we wait."

Flora looked at him, stared. "You okay, Dan?"

Dan nodded. "Yeah, why?"

Flora shook her head. "Nothing. You seem pale, that's all."

Dan smiled. "I'm just hungry. Can't wait for Dad to pick us up," he said.

Nathan paused. Did he say… "us"?

Flora apparently heard it too. "What do you mean, 'us'?"

She asked.

Dan winced. "I have a brother here, too."

Nathan's mind trailed off. When did he ever mention having a brother? He couldn't recall a single time. Not once.

Then it hit him. Nathan staggered back. It couldn't be… Could it?
"""

# Delete old Chapter 1 (indices 1 to ~2807) and insert fixed version
# First, get the document to find exact end index
doc = docs_service.documents().get(documentId=doc_id).execute()
content = doc.get('body').get('content')

# Find where Chapter 2 starts (index 2807)
chapter2_start = 2807

# Delete from index 1 to chapter2_start-1, then insert fixed text
requests = [
    {
        'deleteContentRange': {
            'range': {
                'startIndex': 1,
                'endIndex': chapter2_start
            }
        }
    },
    {
        'insertText': {
            'location': {'index': 1},
            'text': chapter1_fixed
        }
    }
]

result = docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
print('Chapter 1 fixed!')
