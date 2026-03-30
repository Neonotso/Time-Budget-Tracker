import os
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

# Chapter 4 content - cleaned up
chapter4_text = """Chapter 4

Letzier P.O.V

Letzier positioned himself for battle as Blade lunged with a kick. In one swift motion, he caught Blade's foot, yanked him down, and locked him in a chokehold, securing his wrists and keeping him grounded—merciful, but firm.
Coach Andrew's familiar grin lingered. But something about it felt off. A flicker in his expression gave Letzier a strange vibe.
"Time! Letzier, you win!" the coach called, his smile still fixed in place.
Letzier straightened, breath steady, muscles humming from the match. Questions loomed—about the coach's expression, about the unease in the room—but he shoved them aside.
"Of course I did," Letzier said, brushing dust from his sleeve. But his eyes stayed on the coach's faltering smile.
He walked over to Blade and lifted his hand.
"Thanks," Blade muttered.
Letzier nodded. "No problem." He considered offering training help—Blade could use it—but decided against it. His life was too full.
Space School was his focus. And beneath the drills and classes, one mission drove him: finding Zara.
It wasn't about whether she was dead. That wasn't the question. It was about the lie. The launch had been rushed. The scientists said everything was fine. But Letzier didn't believe them.
Zara had been like a sister. She'd brought him and Daisy together. And Daisy—he couldn't bear the sorrow in her eyes. Every time he thought of Zara, his chest tightened. She didn't just vanish. She was stolen by a promise that wasn't kept.
He sat on the bench, water bottle in hand, but barely tasted it. His mind was elsewhere—racing, aching. He should've checked the ship himself. Should've asked harder questions. Should've stopped her.
The crash hadn't given him enough proof. Just fragments. Just silence.
He would find out what really happened. And when he does, he will make them pay.
"Hey, Letzier, you good?" Coach Andrew's voice cut through the haze. Letzier blinked, then nodded. "Yeah."
Andrew studied him for a moment, concern flickering behind his usual calm. But he didn't press.
"Okay. Tell Alfred I said hi, would ya?"
Letzier gave him a questioning look. But nodded.
"I will. I'm heading to my next class. See you next week."
Letzier stood, the weight of his promise pressing against his chest. He'd made it to Daisy. To himself. To Zara.
He wouldn't let her story end in a lie.
Class 87 was next.
The halls leading there were quieter, the air heavier. Fewer students walked this path—only those willing to confront what others ignored. It wasn't just a class. It was a threshold. A place built for those who had lost someone, or suspected the truth had been buried beneath protocol and polished reports.
He and Alfred had chosen it together. Not for credits. Not for prestige. But for answers.
Class 87 was confidential. A course designed for those investigating failed missions, vanished crew, and the shadows left behind. It was where whispers became data, where grief met resolve, where Letzier hoped to find the thread that would lead him back to Zara—or at least to the truth of what stole her.
He walked toward the door, pulse steady, heart braced. Whatever Class 87 held, he was ready to face it.
"""

# Insert at end of document (position 9704)
requests = [{
    'insertText': {
        'location': {'index': 9704},
        'text': chapter4_text
    }
}]

result = docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
print('Chapter 4 added successfully!')
print(f'Revision ID: {result.get("revisionsId")}')
