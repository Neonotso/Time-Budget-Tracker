import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

type Attachment = {
  name: string;
  path: string;
  contentType?: string;
  size?: number;
};

type Message = {
  id: number;
  projectId: string;
  role: 'user' | 'assistant';
  text: string;
  at: string;
  attachments?: Attachment[];
};

type Store = { messages: Message[] };

const dataPath = path.join(process.cwd(), '.data', 'project-chat.json');
const uploadsRoot = path.join(process.cwd(), '.data', 'project-chat-uploads');
const execFileAsync = promisify(execFile);
const SHARED_SESSION_ID = 'mission-control-shared-reset-hard-20260311';
const OPENCLAW_TIMEOUT_SECONDS = '65';
const OPENCLAW_PROCESS_TIMEOUT_MS = 90000;
const OPENCLAW_MAX_RETRIES = 2;

async function ensureStore(): Promise<Store> {
  await fs.mkdir(path.dirname(dataPath), { recursive: true });
  try {
    const raw = await fs.readFile(dataPath, 'utf8');
    return JSON.parse(raw) as Store;
  } catch {
    const seed: Store = { messages: [] };
    await fs.writeFile(dataPath, JSON.stringify(seed, null, 2), 'utf8');
    return seed;
  }
}

function nowLabel() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

async function saveAttachments(files: File[]): Promise<Attachment[]> {
  if (!files.length) return [];

  const stamp = Date.now().toString();
  const dir = path.join(uploadsRoot, stamp);
  await fs.mkdir(dir, { recursive: true });

  const saved: Attachment[] = [];
  for (const file of files) {
    const safeName = (file.name || 'attachment').replace(/[^a-zA-Z0-9._-]/g, '_');
    const outPath = path.join(dir, safeName);
    const buffer = Buffer.from(await file.arrayBuffer());
    await fs.writeFile(outPath, buffer);
    saved.push({
      name: file.name || safeName,
      path: outPath,
      contentType: file.type || undefined,
      size: file.size || buffer.length,
    });
  }

  return saved;
}

function extractTextFromOpenClawJson(raw: string): string | null {
  const parsed = JSON.parse(raw || '{}');
  const payloads = parsed?.result?.payloads;
  if (Array.isArray(payloads)) {
    for (const p of payloads) {
      if (typeof p?.text === 'string' && p.text.trim()) return p.text.trim();
    }
  }

  const directText = parsed?.result?.text;
  if (typeof directText === 'string' && directText.trim()) return directText.trim();

  return null;
}

async function askOpenClaw(projectId: string, userText: string, attachments: Attachment[] = []): Promise<string> {
  const attachmentContext = attachments.length
    ? [
        'Attachments included with this message:',
        ...attachments.map((a, i) => `  ${i + 1}. ${a.name} (${a.contentType || 'file'}) at ${a.path}`),
        'Use these files as context if relevant to the user request.',
      ]
    : [];

  const scopedPrompt = [
    `Project chat context: ${projectId}`,
    'Respond naturally and helpfully.',
    'Keep awareness that this project uses a shared brain across all project chats.',
    ...attachmentContext,
    `User message: ${userText}`,
  ].join('\n');

  let lastError: unknown = null;

  for (let attempt = 1; attempt <= OPENCLAW_MAX_RETRIES; attempt += 1) {
    try {
      const { stdout } = await execFileAsync(
        'openclaw',
        [
          'agent',
          '--session-id',
          SHARED_SESSION_ID,
          '--message',
          scopedPrompt,
          '--timeout',
          OPENCLAW_TIMEOUT_SECONDS,
          '--json',
        ],
        {
          cwd: process.cwd(),
          maxBuffer: 1024 * 1024 * 8,
          timeout: OPENCLAW_PROCESS_TIMEOUT_MS,
        }
      );

      const text = extractTextFromOpenClawJson(stdout || '{}');
      if (text) return text;
      lastError = new Error('No text payload returned from openclaw agent JSON response.');
    } catch (err) {
      lastError = err;
    }

    if (attempt < OPENCLAW_MAX_RETRIES) {
      await new Promise((resolve) => setTimeout(resolve, 350 * attempt));
    }
  }

  throw lastError ?? new Error('Unknown OpenClaw failure.');
}

export async function GET(req: NextRequest) {
  const projectId = req.nextUrl.searchParams.get('projectId');
  const store = await ensureStore();
  const messages = projectId
    ? store.messages.filter((m) => m.projectId === projectId)
    : store.messages;
  return NextResponse.json({ messages });
}

export async function POST(req: NextRequest) {
  const contentType = req.headers.get('content-type') || '';

  let projectId = 'squirrely-chat';
  let text = '';
  let attachments: Attachment[] = [];

  if (contentType.includes('multipart/form-data')) {
    const form = await req.formData();
    projectId = String(form.get('projectId') || 'squirrely-chat');
    text = String(form.get('text') || '').trim();
    const files = form
      .getAll('attachments')
      .filter((v): v is File => v instanceof File && !!v.name && v.size > 0);
    attachments = await saveAttachments(files);
  } else {
    const body = await req.json();
    projectId = String(body.projectId || 'squirrely-chat');
    text = String(body.text || '').trim();
  }

  if (!text && attachments.length === 0) {
    return NextResponse.json({ error: 'text or attachment required' }, { status: 400 });
  }

  const store = await ensureStore();
  const usedIds = new Set(store.messages.map((m) => m.id));
  let nextId = (store.messages.at(-1)?.id || 0) + 1;
  while (usedIds.has(nextId)) nextId += 1;

  const userMsg: Message = {
    id: nextId,
    projectId,
    role: 'user',
    text: text || '(attachment)',
    at: nowLabel(),
    attachments: attachments.length ? attachments : undefined,
  };

  store.messages.push(userMsg);
  await fs.writeFile(dataPath, JSON.stringify(store, null, 2), 'utf8');

  let assistantText = '';
  try {
    assistantText = await askOpenClaw(projectId, text || 'Please process the attachment(s).', attachments);
  } catch (err) {
    assistantText = 'I hit an error reaching the live agent. Try again in a moment.';
  }

  let assistantId = nextId + 1;
  while (usedIds.has(assistantId) || assistantId === nextId) assistantId += 1;

  const assistantMsg: Message = {
    id: assistantId,
    projectId,
    role: 'assistant',
    text: assistantText,
    at: nowLabel(),
  };

  store.messages.push(assistantMsg);
  await fs.writeFile(dataPath, JSON.stringify(store, null, 2), 'utf8');

  return NextResponse.json({ messages: [userMsg, assistantMsg] });
}
