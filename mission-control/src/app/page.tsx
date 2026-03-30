'use client';

import { useState, useEffect, useRef } from 'react';

type View = 'chat' | 'conversations' | 'tasks' | 'calendar' | 'projects' | 'memory' | 'docs' | 'team' | 'office';

const navItems: { id: View; label: string; icon: string }[] = [
  { id: 'chat', label: 'Project Chat', icon: '💬' },
  { id: 'conversations', label: 'Conversations', icon: '🛰️' },
  { id: 'tasks', label: 'Task Board', icon: '📋' },
  { id: 'calendar', label: 'Calendar', icon: '📅' },
  { id: 'projects', label: 'Projects', icon: '📁' },
  { id: 'memory', label: 'Memory', icon: '🧠' },
  { id: 'docs', label: 'Docs', icon: '📄' },
  { id: 'team', label: 'Team', icon: '👥' },
  { id: 'office', label: 'Office', icon: '🏢' },
];

type Project = { id: number; name: string; category: 'Active' | 'Ongoing' | 'Ideas'; progress: number };

// Real channel/project structure from Ryan's Discord screenshot (2026-03-09)
const projects: Project[] = [
  { id: 1, name: 'Monthly Budget', category: 'Active', progress: 65 },
  { id: 2, name: 'Mission Control', category: 'Active', progress: 55 },
  { id: 3, name: 'Backing Track Generation', category: 'Active', progress: 50 },
  { id: 4, name: 'iOS Ableton Remote', category: 'Ongoing', progress: 45 },
  { id: 5, name: 'Ableton Live Control', category: 'Ongoing', progress: 40 },
  { id: 6, name: 'Chord Charts', category: 'Ongoing', progress: 35 },
  { id: 7, name: 'Slide Images for Church', category: 'Ideas', progress: 20 },
  { id: 8, name: 'PIER Song Database', category: 'Ideas', progress: 25 },
  { id: 9, name: 'PIER Map App', category: 'Active', progress: 70 },
  { id: 10, name: 'PIER Ableton Setup', category: 'Active', progress: 60 },
];

// From MEMORY.md
const missionStatement = "Help Ryan be more productive and creative by automating workflows, managing projects, and building useful tools.";

// Cron jobs / scheduled tasks
const scheduledTasks = [
  { id: 1, title: 'Morning standup (heartbeat)', time: '9:00 AM', type: 'cron' },
  { id: 2, title: 'Check calendar/events', time: 'Ongoing', type: 'cron' },
  { id: 3, title: 'Weather check', time: '6:00 PM', type: 'cron' },
  { id: 4, title: 'Weekly: Sunday Songs setup', time: 'Sundays', type: 'cron' },
];

type DocItem = { id: number; title: string; type: string; path: string };
type ProjectBrief = { id: string; category: string; title: string; summary: string; updated: string };
type ChatProject = { id: string; category: string; title: string; summary: string; updated: string };

// Docs from workspace
const docs: DocItem[] = [
  { id: 1, title: 'PIER Map Architecture', type: 'md', path: 'docs/pier-map.md' },
  { id: 2, title: 'Ableton Workflow Notes', type: 'md', path: 'memory/...' },
  { id: 3, title: 'Monthly Budget Workflow', type: 'md', path: 'memory/monthly-budget-workflow.md' },
  { id: 4, title: 'MEMORY.md', type: 'md', path: 'MEMORY.md' },
  { id: 5, title: 'USER.md', type: 'md', path: 'USER.md' },
  { id: 6, title: 'PIER Ableton Songs Script', type: 'py', path: 'scripts/pier_ableton_songs.py' },
];

const projectBriefs: ProjectBrief[] = [
  {
    id: 'monthly-budget',
    category: 'Core Ops',
    title: 'Monthly Budget',
    updated: '2026-03-09',
    summary:
      'Completed monthly workflow automation: snapshots (2026_02 / 2026_02trans), transaction reset, numeric amount fixes, March transaction imports, summary formula recovery, and monthly cron reminder at 9:00 AM on the 1st.',
  },
  {
    id: 'mission-control',
    category: 'Core Ops',
    title: 'Mission Control',
    updated: '2026-03-09',
    summary:
      'Built Next.js Mission Control prototype from transcript-driven requirements, launched locally, then grounded with real Discord channel/project structure and category-based dashboard organization.',
  },
  {
    id: 'backing-track-generation',
    category: 'Ableton Live',
    title: 'Backing Track Generation',
    updated: '2026-03-09',
    summary:
      'Implemented sheet-music pipeline in backing-track-pipeline/: PDF/OMR → MusicXML/MIDI stems → Ableton import plan artifacts, with one-shot wrapper script and OSC bootstrap option.',
  },
  {
    id: 'ios-ableton-remote',
    category: 'Ableton Live',
    title: 'iOS Ableton Remote',
    updated: '2026-03-09',
    summary:
      'Hardened transport/metronome/record/locator workflows, added sticky collapsible UI sections, improved tempo controls and arm/group handling, plus stabilized Max push pipeline with cache + watchdog dedupe.',
  },
  {
    id: 'ableton-live-control',
    category: 'Ableton Live',
    title: 'Ableton Live Control',
    updated: '2026-03-09',
    summary:
      'Validated OSC/MCP capabilities and limits for per-clip scale, patched AbletonOSC introspection/safety paths, and scaffolded bridge-based clip-scale command/state plumbing (server + Max JS + patch sync).',
  },
  {
    id: 'pier-ableton-setup',
    category: 'PIER Church',
    title: 'PIER Ableton Setup',
    updated: '2026-03-09',
    summary:
      'Locked repeatable Sunday set workflow with save/verify checkpoints (scenes → pads → tempos). Confirmed March 22 set with correct scenes, pad keys (C, D, E, D, D), tempos (150, 72, 74, 86, 70), and final save path.',
  },
  {
    id: 'pier-map-app',
    category: 'PIER Church',
    title: 'PIER Map App',
    updated: '2026-03-09',
    summary:
      'Improved live navigation UX and coupling with tracking lifecycle, added reroute/end controls, step labeling, device-first theme behavior, legend/info-window fixes, then built/pushed/deployed to Firebase and synced clones.',
  },
  {
    id: 'pier-song-database',
    category: 'PIER Church',
    title: 'PIER Song Database',
    updated: '2026-03-09',
    summary:
      'Built end-to-end pipeline: Planning Center API access, full-history analytics (565 plans, 2,797 events, 507 songs), organized exports, and published formatted multi-tab Google Sheet with sortable keep/review/retire outputs.',
  },
  {
    id: 'slide-images-for-church',
    category: 'PIER Church',
    title: 'Slide Images for Church',
    updated: '2026-03-09',
    summary:
      'Generated first 1280×800 hopeful tree image and initiated Fooocus-based higher-quality pipeline (Python 3.10, venv, presets/church.json, config defaults, model download path).',
  },
  {
    id: 'chord-charts',
    category: 'PIER Church',
    title: 'Chord Charts',
    updated: '2026-03-09',
    summary:
      'Confirmed SongSelect API limitations and mapped alternatives: Planning Center linked attachments + legal source conversion path to ChordPro, with proposed weekly automation workflow.',
  },
];

export default function Home() {
  const [activeView, setActiveView] = useState<View>('chat');
  const [currentTime, setCurrentTime] = useState('');

  useEffect(() => {
    setCurrentTime(new Date().toLocaleTimeString());
    const timer = setInterval(() => setCurrentTime(new Date().toLocaleTimeString()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-56 bg-[#171717] border-r border-[#2e2e2e] flex flex-col">
        <div className="p-4 border-b border-[#2e2e2e]">
          <h1 className="text-lg font-semibold text-white">Mission Control</h1>
          <p className="text-xs text-[#525252]">Ryan's Dashboard</p>
        </div>
        
        <nav className="flex-1 p-2 space-y-1">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveView(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                activeView === item.id
                  ? 'bg-[#8b5cf6] text-white'
                  : 'text-[#a3a3a3] hover:bg-[#262626] hover:text-white'
              }`}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="p-4 border-t border-[#2e2e2e] space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-[#22c55e] animate-pulse"></div>
            <span className="text-xs text-[#525252]">Gateway: Online</span>
          </div>
          <div className="text-xs text-[#525252]">{currentTime}</div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {activeView === 'chat' && <ProjectChatView />}
        {activeView === 'conversations' && <ConversationsView />}
        {activeView === 'tasks' && <TaskBoard />}
        {activeView === 'calendar' && <CalendarView tasks={scheduledTasks} />}
        {activeView === 'projects' && <ProjectsView projects={projects} />}
        {activeView === 'memory' && <MemoryView />}
        {activeView === 'docs' && <DocsView docs={docs} />}
        {activeView === 'team' && <TeamView mission={missionStatement} />}
        {activeView === 'office' && <OfficeView />}
      </main>
    </div>
  );
}

const PROJECT_CHAT_STORAGE_KEY = 'mission-control.selected-project-chat';
const PROJECT_CHAT_CONFIG_STORAGE_KEY = 'mission-control.project-chat-config';
const PROJECT_CHAT_READ_STATE_KEY = 'mission-control.project-chat-read-state';
const defaultChatProjects: ChatProject[] = [...projectBriefs];
const defaultGroupOrder = Array.from(new Set(defaultChatProjects.map((p) => p.category)));

const slugify = (value: string) =>
  value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');

function ProjectChatView() {
  const [selectedProjectId, setSelectedProjectId] = useState<string>('squirrely-chat');
  const [draft, setDraft] = useState('');
  const [isAssistantTyping, setIsAssistantTyping] = useState(false);
  const [pendingProjectId, setPendingProjectId] = useState<string | null>(null);
  const [lastError, setLastError] = useState<string | null>(null);
  const [isManagingProjects, setIsManagingProjects] = useState(false);

  const [chatProjects, setChatProjects] = useState<ChatProject[]>(defaultChatProjects);
  const [groupOrder, setGroupOrder] = useState<string[]>(defaultGroupOrder);
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const [messages, setMessages] = useState<Array<{ id: number; projectId: string; role: 'user' | 'assistant'; text: string; at: string; attachments?: Array<{ name: string; path?: string; contentType?: string; size?: number }> }>>([]);
  const [scrollToBottomAfterNextRender, setScrollToBottomAfterNextRender] = useState(false);
  const [showNewMessagesNotice, setShowNewMessagesNotice] = useState(false);
  const [draggedProjectId, setDraggedProjectId] = useState<string | null>(null);
  const [dropTarget, setDropTarget] = useState<{ category: string; projectId?: string; after?: boolean } | null>(null);
  const [isPointerDragging, setIsPointerDragging] = useState(false);
  const [unreadCounts, setUnreadCounts] = useState<Record<string, number>>({});
  const [lastReadByProject, setLastReadByProject] = useState<Record<string, number>>({});
  const messagePaneRef = useRef<HTMLDivElement | null>(null);
  const lastVisibleCountRef = useRef(0);
  const wasNearBottomRef = useRef(true);
  const hasBootstrappedReadStateRef = useRef(false);
  const hasLoadedProjectConfigRef = useRef(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const formatBytes = (bytes?: number) => {
    if (!bytes || bytes <= 0) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const grouped = groupOrder.reduce<Record<string, ChatProject[]>>((acc, category) => {
    acc[category] = chatProjects.filter((p) => p.category === category);
    return acc;
  }, {});

  const mergeMessages = (
    current: Array<{ id: number; projectId: string; role: 'user' | 'assistant'; text: string; at: string; attachments?: Array<{ name: string; path?: string; contentType?: string; size?: number }> }>,
    incoming: Array<{ id: number; projectId: string; role: 'user' | 'assistant'; text: string; at: string; attachments?: Array<{ name: string; path?: string; contentType?: string; size?: number }> }>
  ) => {
    const byKey = new Map<string, (typeof current)[number]>();
    for (const m of current) byKey.set(`${m.projectId}:${m.id}:${m.role}`, m);
    for (const m of incoming) byKey.set(`${m.projectId}:${m.id}:${m.role}`, m);

    const all = Array.from(byKey.values());
    const persistedSignatures = new Set(
      all
        .filter((m) => m.id < 1_000_000_000_000)
        .map((m) => `${m.projectId}|${m.role}|${m.text}|${(m.attachments || []).map((a) => `${a.name}:${a.size || 0}`).join(',')}`)
    );

    return all
      .filter((m) => {
        const isOptimistic = m.id >= 1_000_000_000_000;
        if (!isOptimistic) return true;
        const signature = `${m.projectId}|${m.role}|${m.text}|${(m.attachments || []).map((a) => `${a.name}:${a.size || 0}`).join(',')}`;
        return !persistedSignatures.has(signature);
      })
      .sort((a, b) => a.id - b.id);
  };

  const selectedProject =
    selectedProjectId === 'squirrely-chat'
      ? { id: 'squirrely-chat', title: 'Squirrely Chat', category: 'General', summary: 'Generic chat that is intentionally separate from project lanes.' }
      : chatProjects.find((p) => p.id === selectedProjectId) || chatProjects[0] || { id: 'squirrely-chat', title: 'Squirrely Chat', category: 'General', summary: 'Generic chat that is intentionally separate from project lanes.' };

  const visible = messages.filter((m) => m.projectId === selectedProjectId);

  const openProject = (projectId: string) => {
    const currentProjectId = selectedProjectId;
    const currentProjectMaxId = messages
      .filter((m) => m.projectId === currentProjectId)
      .reduce((max, m) => Math.max(max, m.id || 0), 0);

    const targetProjectMaxId = messages
      .filter((m) => m.projectId === projectId)
      .reduce((max, m) => Math.max(max, m.id || 0), 0);

    setLastReadByProject((prev) => ({
      ...prev,
      [currentProjectId]: Math.max(prev[currentProjectId] || 0, currentProjectMaxId),
      [projectId]: Math.max(prev[projectId] || 0, targetProjectMaxId),
    }));

    setSelectedProjectId(projectId);
  };

  useEffect(() => {
    let cancelled = false;

    const loadMessages = () => {
      fetch('/api/project-chat', { cache: 'no-store' })
        .then((r) => r.json())
        .then((d) => {
          if (!cancelled) {
            const incoming = d.messages || [];
            setMessages((prev) => mergeMessages(prev, incoming));
          }
        })
        .catch(() => {});
    };

    loadMessages();
    const timer = setInterval(loadMessages, 4000);

    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    const savedConfig = window.localStorage.getItem(PROJECT_CHAT_CONFIG_STORAGE_KEY);
    if (savedConfig) {
      try {
        const parsed = JSON.parse(savedConfig) as { chatProjects?: ChatProject[]; groupOrder?: string[] };
        if (parsed.chatProjects?.length) setChatProjects(parsed.chatProjects);
        if (parsed.groupOrder?.length) setGroupOrder(parsed.groupOrder);
      } catch {
        // ignore malformed localStorage
      }
    }

    hasLoadedProjectConfigRef.current = true;

    const savedReadState = window.localStorage.getItem(PROJECT_CHAT_READ_STATE_KEY);
    if (savedReadState) {
      try {
        const parsed = JSON.parse(savedReadState) as Record<string, number>;
        setLastReadByProject(parsed || {});
      } catch {
        // ignore malformed localStorage
      }
    }

    const saved = window.localStorage.getItem(PROJECT_CHAT_STORAGE_KEY);
    if (saved) {
      setSelectedProjectId(saved);
      setScrollToBottomAfterNextRender(true);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem(PROJECT_CHAT_STORAGE_KEY, selectedProjectId);
  }, [selectedProjectId]);

  useEffect(() => {
    if (!hasLoadedProjectConfigRef.current) return;
    window.localStorage.setItem(
      PROJECT_CHAT_CONFIG_STORAGE_KEY,
      JSON.stringify({ chatProjects, groupOrder })
    );
  }, [chatProjects, groupOrder]);

  useEffect(() => {
    window.localStorage.setItem(PROJECT_CHAT_READ_STATE_KEY, JSON.stringify(lastReadByProject));
  }, [lastReadByProject]);

  useEffect(() => {
    if (!messages.length) return;

    // On first load with no saved read state, mark everything as read to avoid false unread floods.
    if (!hasBootstrappedReadStateRef.current && Object.keys(lastReadByProject).length === 0) {
      const bootstrapped: Record<string, number> = {};
      for (const msg of messages) {
        bootstrapped[msg.projectId] = Math.max(bootstrapped[msg.projectId] || 0, msg.id || 0);
      }
      setLastReadByProject(bootstrapped);
      hasBootstrappedReadStateRef.current = true;
      return;
    }

    hasBootstrappedReadStateRef.current = true;

    const nextUnread: Record<string, number> = {};
    for (const msg of messages) {
      const lastRead = lastReadByProject[msg.projectId] || 0;
      const isUnread = (msg.id || 0) > lastRead;
      const shouldCount = msg.role === 'assistant';
      if (isUnread && shouldCount) {
        nextUnread[msg.projectId] = (nextUnread[msg.projectId] || 0) + 1;
      }
    }

    // Never show unread on the currently open project
    nextUnread[selectedProjectId] = 0;
    setUnreadCounts(nextUnread);
  }, [messages, lastReadByProject, selectedProjectId]);

  const isNearBottom = () => {
    const pane = messagePaneRef.current;
    if (!pane) return true;
    const distanceFromBottom = pane.scrollHeight - pane.scrollTop - pane.clientHeight;
    return distanceFromBottom < 40;
  };

  useEffect(() => {
    if (!scrollToBottomAfterNextRender) return;
    const pane = messagePaneRef.current;
    if (pane) {
      pane.scrollTop = pane.scrollHeight;
      wasNearBottomRef.current = true;
    }
    setShowNewMessagesNotice(false);
    setScrollToBottomAfterNextRender(false);
  }, [scrollToBottomAfterNextRender, visible.length, selectedProjectId]);

  useEffect(() => {
    const previousCount = lastVisibleCountRef.current;
    const hasNewMessage = visible.length > previousCount;

    if (hasNewMessage && !scrollToBottomAfterNextRender) {
      if (wasNearBottomRef.current) {
        setScrollToBottomAfterNextRender(true);
      } else {
        setShowNewMessagesNotice(true);
      }
    }

    lastVisibleCountRef.current = visible.length;
  }, [visible.length, scrollToBottomAfterNextRender]);

  useEffect(() => {
    lastVisibleCountRef.current = visible.length;
    wasNearBottomRef.current = true;
    setShowNewMessagesNotice(false);
    setScrollToBottomAfterNextRender(true);
  }, [selectedProjectId]);

  useEffect(() => {
    if (selectedProjectId === 'squirrely-chat') return;
    const maxVisibleId = visible.reduce((max, m) => Math.max(max, m.id || 0), 0);
    if (!maxVisibleId) return;
    setLastReadByProject((prev) => {
      const current = prev[selectedProjectId] || 0;
      if (maxVisibleId <= current) return prev;
      return { ...prev, [selectedProjectId]: maxVisibleId };
    });
  }, [selectedProjectId, visible]);

  useEffect(() => {
    if (selectedProjectId !== 'squirrely-chat' && !chatProjects.some((p) => p.id === selectedProjectId)) {
      setSelectedProjectId('squirrely-chat');
    }
  }, [chatProjects, selectedProjectId]);

  useEffect(() => {
    if (!isPointerDragging) return;

    const onPointerUp = () => {
      if (draggedProjectId && dropTarget) {
        moveDraggedProject(dropTarget.category, dropTarget.projectId, !!dropTarget.after);
      } else {
        setDraggedProjectId(null);
      }
      setDropTarget(null);
      setIsPointerDragging(false);
    };

    window.addEventListener('pointerup', onPointerUp);
    return () => window.removeEventListener('pointerup', onPointerUp);
  }, [isPointerDragging, draggedProjectId, dropTarget]);

  const moveGroup = (category: string, direction: -1 | 1) => {
    const idx = groupOrder.indexOf(category);
    const nextIdx = idx + direction;
    if (idx < 0 || nextIdx < 0 || nextIdx >= groupOrder.length) return;
    const next = [...groupOrder];
    [next[idx], next[nextIdx]] = [next[nextIdx], next[idx]];
    setGroupOrder(next);
  };

  const addGroup = () => {
    const name = window.prompt('New group name:')?.trim();
    if (!name || groupOrder.includes(name)) return;
    setGroupOrder((prev) => [...prev, name]);
  };

  const renameGroup = (oldName: string) => {
    const name = window.prompt('Rename group:', oldName)?.trim();
    if (!name || name === oldName || groupOrder.includes(name)) return;
    setGroupOrder((prev) => prev.map((g) => (g === oldName ? name : g)));
    setChatProjects((prev) => prev.map((p) => (p.category === oldName ? { ...p, category: name } : p)));
  };

  const deleteGroup = (category: string) => {
    const hasProjects = chatProjects.some((p) => p.category === category);
    const confirmed = window.confirm(
      hasProjects
        ? `Delete group "${category}" and all chats inside it?`
        : `Delete group "${category}"?`
    );
    if (!confirmed) return;
    setGroupOrder((prev) => prev.filter((g) => g !== category));
    setChatProjects((prev) => prev.filter((p) => p.category !== category));
  };

  const addProject = (category: string) => {
    const title = window.prompt('New project chat name:')?.trim();
    if (!title) return;
    const baseId = slugify(title) || `project-${Date.now()}`;
    let id = baseId;
    let n = 2;
    while (chatProjects.some((p) => p.id === id) || id === 'squirrely-chat') {
      id = `${baseId}-${n++}`;
    }
    setChatProjects((prev) => [
      ...prev,
      { id, title, category, summary: 'Custom project chat.', updated: new Date().toISOString().slice(0, 10) },
    ]);
    openProject(id);
  };

  const renameProject = (id: string) => {
    const current = chatProjects.find((p) => p.id === id);
    if (!current) return;
    const title = window.prompt('Rename project chat:', current.title)?.trim();
    if (!title || title === current.title) return;
    setChatProjects((prev) => prev.map((p) => (p.id === id ? { ...p, title } : p)));
  };

  const moveDraggedProject = (targetCategory: string, targetProjectId?: string, after = false) => {
    if (!draggedProjectId) return;
    const dragged = chatProjects.find((p) => p.id === draggedProjectId);
    if (!dragged) return;

    const withoutDragged = chatProjects.filter((p) => p.id !== draggedProjectId);
    const moved = { ...dragged, category: targetCategory };

    let insertIndex = withoutDragged.length;
    if (targetProjectId) {
      const idx = withoutDragged.findIndex((p) => p.id === targetProjectId);
      if (idx >= 0) insertIndex = idx + (after ? 1 : 0);
    } else {
      const lastInCategory = withoutDragged.reduce((last, p, idx) => (p.category === targetCategory ? idx : last), -1);
      insertIndex = lastInCategory + 1;
    }

    withoutDragged.splice(insertIndex, 0, moved);
    setChatProjects(withoutDragged);
    setDraggedProjectId(null);
  };

  const deleteProject = (id: string) => {
    const project = chatProjects.find((p) => p.id === id);
    if (!project) return;
    if (!window.confirm(`Delete project chat "${project.title}"?`)) return;
    setChatProjects((prev) => prev.filter((p) => p.id !== id));
  };

  const send = async () => {
    if (!draft.trim() && pendingFiles.length === 0) return;
    const text = draft.trim();
    const filesToSend = [...pendingFiles];
    setDraft('');
    setPendingFiles([]);
    setLastError(null);
    setIsAssistantTyping(true);
    setPendingProjectId(selectedProjectId);
    setScrollToBottomAfterNextRender(true);

    const optimisticUser = {
      id: Date.now(),
      projectId: selectedProjectId,
      role: 'user' as const,
      text: text || '(attachment)',
      attachments: filesToSend.map((f) => ({ name: f.name, contentType: f.type, size: f.size })),
      at: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages((prev) => [...prev, optimisticUser]);

    try {
      let res: Response;
      if (filesToSend.length > 0) {
        const formData = new FormData();
        formData.append('projectId', selectedProjectId);
        formData.append('text', text);
        filesToSend.forEach((file) => formData.append('attachments', file));
        res = await fetch('/api/project-chat', {
          method: 'POST',
          body: formData,
        });
      } else {
        res = await fetch('/api/project-chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ projectId: selectedProjectId, text }),
        });
      }

      if (res.ok) {
        const data = await res.json();
        setMessages((prev) => {
          const withoutOptimistic = prev.filter((m) => m.id !== optimisticUser.id);
          return mergeMessages(withoutOptimistic, data.messages || []);
        });
      } else {
        setLastError('Reply failed. Try sending again.');
      }
    } catch {
      setLastError('Network error while waiting for reply.');
    } finally {
      setIsAssistantTyping(false);
      setPendingProjectId(null);
    }
  };

  return (
    <div className="h-full min-h-0 overflow-hidden grid grid-cols-1 lg:grid-cols-[280px_1fr]">
      <aside className="border-r border-[#2e2e2e] bg-[#171717] p-4 overflow-auto min-h-0">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-white font-semibold">Project Chats</h2>
          <button
            onClick={() => setIsManagingProjects((v) => !v)}
            className="text-xs px-2 py-1 rounded border border-[#3a3a3a] text-[#d4d4d4] hover:bg-[#262626]"
          >
            {isManagingProjects ? 'Done' : 'Manage'}
          </button>
        </div>

        <button
          onClick={() => openProject('squirrely-chat')}
          className={`w-full text-left px-3 py-2 rounded-md mb-4 text-sm ${
            selectedProjectId === 'squirrely-chat'
              ? 'bg-[#8b5cf6] text-white'
              : unreadCounts['squirrely-chat']
                ? 'bg-[#262626] text-white font-semibold hover:bg-[#303030]'
                : 'bg-[#262626] text-[#d4d4d4] hover:bg-[#303030]'
          }`}
        >
          💬 Squirrely Chat{unreadCounts['squirrely-chat'] ? ` (${unreadCounts['squirrely-chat']})` : ''}
        </button>

        {isManagingProjects && (
          <div className="mb-4 space-y-2">
            <div className="flex gap-2">
              <button onClick={addGroup} className="text-xs px-2 py-1 rounded bg-[#262626] text-[#d4d4d4] hover:bg-[#303030]">+ Group</button>
            </div>
            <p className="text-[11px] text-[#8b8b8b]">Drag and drop chats to reorder within a group or move to another group.</p>
          </div>
        )}

        {Object.entries(grouped).map(([category, items]) => (
          <div
            key={category}
            className={`mb-4 rounded p-2 border ${isManagingProjects ? (draggedProjectId ? 'border-dashed border-[#8b5cf6]/50' : 'border-[#2e2e2e]') : 'border-transparent'}`}
            onPointerMove={(e) => {
              if (!isManagingProjects || !isPointerDragging) return;
              if (e.target !== e.currentTarget) return;
              setDropTarget({ category });
            }}
          >
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs uppercase tracking-wide text-[#737373]">{category}</p>
              {isManagingProjects && (
                <div className="flex gap-1">
                  <button onClick={() => addProject(category)} className="text-[10px] px-1.5 py-0.5 rounded bg-[#262626] text-[#bdbdbd]">+ Chat</button>
                  <button onClick={() => renameGroup(category)} className="text-[10px] px-1.5 py-0.5 rounded bg-[#262626] text-[#bdbdbd]">Rename</button>
                  <button onClick={() => deleteGroup(category)} className="text-[10px] px-1.5 py-0.5 rounded bg-red-900/30 text-red-300">Del</button>
                </div>
              )}
            </div>
            <div className="space-y-1">
              {items.map((item) => (
                <div key={item.id} className={draggedProjectId === item.id ? 'opacity-50' : ''}>
                  {isManagingProjects && dropTarget?.category === category && dropTarget?.projectId === item.id && !dropTarget?.after && (
                    <div className="w-full border-t-2 border-[#a78bfa] my-1" />
                  )}

                  <div
                    onPointerMove={(e) => {
                      if (!isManagingProjects || !isPointerDragging) return;
                      const rect = (e.currentTarget as HTMLDivElement).getBoundingClientRect();
                      const after = e.clientY > rect.top + rect.height / 2;
                      setDropTarget({ category, projectId: item.id, after });
                    }}
                    className="flex items-center gap-1 select-none"
                    style={{ touchAction: 'none' }}
                  >
                    {isManagingProjects && (
                      <div
                        onPointerDown={(e) => {
                          e.preventDefault();
                          setDraggedProjectId(item.id);
                          setIsPointerDragging(true);
                        }}
                        className="select-none cursor-grab active:cursor-grabbing px-2 py-2 text-[#a3a3a3] rounded bg-[#262626]"
                        title="Drag to reorder"
                      >
                        ⋮⋮
                      </div>
                    )}
                    <button
                      onClick={() => openProject(item.id)}
                      className={`flex-1 text-left px-3 py-2 rounded-md text-sm ${
                        selectedProjectId === item.id
                          ? 'bg-[#8b5cf6] text-white'
                          : unreadCounts[item.id]
                            ? 'text-white font-semibold bg-[#262626] hover:bg-[#303030]'
                            : 'text-[#d4d4d4] hover:bg-[#262626]'
                      }`}
                    >
                      {item.title}{unreadCounts[item.id] ? ` (${unreadCounts[item.id]})` : ''}
                    </button>
                    {isManagingProjects && (
                      <div className="flex gap-1">
                        <button data-no-drag="true" onClick={() => renameProject(item.id)} className="text-[10px] px-1.5 py-0.5 rounded bg-[#262626] text-[#bdbdbd]">Rename</button>
                        <button data-no-drag="true" onClick={() => deleteProject(item.id)} className="text-[10px] px-1.5 py-0.5 rounded bg-red-900/30 text-red-300">Del</button>
                      </div>
                    )}
                  </div>

                  {isManagingProjects && dropTarget?.category === category && dropTarget?.projectId === item.id && dropTarget?.after && (
                    <div className="w-full border-t-2 border-[#a78bfa] my-1" />
                  )}
                </div>
              ))}
              {isManagingProjects && dropTarget?.category === category && !dropTarget?.projectId && (
                <div className="w-full border-t-2 border-[#a78bfa] my-1" />
              )}
              {isManagingProjects && items.length === 0 && (
                <div className="text-[11px] text-[#8b8b8b] border border-dashed border-[#3a3a3a] rounded px-2 py-2">
                  Drop chat here
                </div>
              )}
            </div>
          </div>
        ))}
      </aside>

      <section className="flex flex-col h-full min-h-0">
        <div className="border-b border-[#2e2e2e] p-4 bg-[#171717]">
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <div>
              <h3 className="text-white font-semibold">{selectedProject.title}</h3>
              <p className="text-xs text-[#a3a3a3] mt-1">{selectedProject.summary}</p>
            </div>
            <div className="flex items-center gap-2">
              {isAssistantTyping && pendingProjectId === selectedProjectId && (
                <span className="text-[11px] px-2 py-1 rounded bg-[#22c55e]/15 text-[#86efac] border border-[#22c55e]/30 animate-pulse">
                  Sally is typing…
                </span>
              )}
              <span className="text-[11px] px-2 py-1 rounded bg-[#8b5cf6]/20 text-[#c4b5fd] border border-[#8b5cf6]/30">
                Shared brain: agent:main:main
              </span>
            </div>
          </div>
        </div>

        <div
          ref={messagePaneRef}
          onScroll={() => {
            const nearBottom = isNearBottom();
            wasNearBottomRef.current = nearBottom;
            if (showNewMessagesNotice && nearBottom) {
              setShowNewMessagesNotice(false);
            }
          }}
          className="flex-1 min-h-0 overflow-auto p-4 space-y-3 bg-[#111111]"
        >
          {visible.map((m, idx) => (
            <div key={`${m.id}-${idx}`} className={`max-w-3xl ${m.role === 'user' ? 'ml-auto' : ''}`}>
              <div
                className={`rounded-lg px-3 py-2 text-sm ${
                  m.role === 'user' ? 'bg-[#8b5cf6] text-white' : 'bg-[#262626] text-[#e5e5e5]'
                }`}
              >
                {m.text}
                {!!m.attachments?.length && (
                  <div className="mt-2 space-y-1">
                    {m.attachments.map((a, attachmentIdx) => (
                      <div
                        key={`${m.id}-att-${attachmentIdx}`}
                        className={`text-xs rounded px-2 py-1 border ${
                          m.role === 'user'
                            ? 'bg-white/10 border-white/20 text-white'
                            : 'bg-[#1f1f1f] border-[#3a3a3a] text-[#d4d4d4]'
                        }`}
                      >
                        📎 {a.name}{a.size ? ` (${formatBytes(a.size)})` : ''}
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div className="text-[10px] text-[#737373] mt-1">{m.role} • {m.at}</div>
            </div>
          ))}
          {isAssistantTyping && pendingProjectId === selectedProjectId && (
            <div className="max-w-3xl">
              <div className="rounded-lg px-3 py-2 text-sm bg-[#262626] text-[#a3a3a3] inline-flex items-center gap-2">
                <span className="inline-flex gap-1" aria-label="typing">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#a3a3a3] animate-bounce"></span>
                  <span className="w-1.5 h-1.5 rounded-full bg-[#a3a3a3] animate-bounce [animation-delay:120ms]"></span>
                  <span className="w-1.5 h-1.5 rounded-full bg-[#a3a3a3] animate-bounce [animation-delay:240ms]"></span>
                </span>
                Sally is crafting a reply…
              </div>
            </div>
          )}
          {visible.length === 0 && <p className="text-sm text-[#737373]">No messages in this project yet.</p>}
        </div>

        <div className="border-t border-[#2e2e2e] p-3 bg-[#171717]">
          {showNewMessagesNotice && (
            <button
              onClick={() => setScrollToBottomAfterNextRender(true)}
              className="mb-2 w-full text-center text-xs rounded-md border border-[#8b5cf6]/40 bg-[#8b5cf6] text-white px-3 py-2 hover:bg-[#7c3aed] transition-colors"
            >
              New message(s) — Jump to latest
            </button>
          )}
          {lastError && <p className="text-xs text-red-300 mb-2">{lastError}</p>}
          {!!pendingFiles.length && (
            <div className="mb-2 flex flex-wrap gap-2">
              {pendingFiles.map((file, idx) => (
                <span
                  key={`${file.name}-${idx}`}
                  className="inline-flex items-center gap-2 text-xs px-2 py-1 rounded border border-[#3a3a3a] bg-[#262626] text-[#d4d4d4]"
                >
                  📎 {file.name} {file.size ? `(${formatBytes(file.size)})` : ''}
                  <button
                    onClick={() => setPendingFiles((prev) => prev.filter((_, i) => i !== idx))}
                    className="text-[#a3a3a3] hover:text-white"
                    aria-label={`Remove ${file.name}`}
                  >
                    ✕
                  </button>
                </span>
              ))}
            </div>
          )}
          <div className="flex gap-2">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={(e) => {
              const selected = Array.from(e.target.files || []);
              if (!selected.length) return;
              setPendingFiles((prev) => [...prev, ...selected]);
              e.currentTarget.value = '';
            }}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-3 py-2 rounded-md bg-[#262626] border border-[#333] text-sm text-[#d4d4d4] hover:bg-[#303030]"
            title="Attach files"
          >
            📎
          </button>
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            placeholder={`Message ${selectedProject.title}...`}
            rows={1}
            className="flex-1 px-3 py-2 rounded-md bg-[#262626] border border-[#333] text-sm text-white placeholder-[#737373] resize-y min-h-[40px] max-h-56"
          />
          <button onClick={send} className="px-4 py-2 rounded-md bg-[#8b5cf6] text-white text-sm hover:bg-[#7c3aed]">
            Send
          </button>
          </div>
        </div>
      </section>
    </div>
  );
}

function ConversationsView() {
  const lanes = [
    {
      name: 'Core Ops',
      items: [
        { source: '#monthly-budget', title: 'Track expenses/income and monthly reset flow', project: 'Monthly Budget', status: 'hot' },
        { source: '#mission-control', title: 'Dashboard and orchestration improvements', project: 'Mission Control', status: 'active' },
      ],
    },
    {
      name: 'Ableton Live',
      items: [
        { source: '#backing-track-generation', title: 'Generate/process backing tracks', project: 'Backing Track Generation', status: 'active' },
        { source: '#ios-ableton-remote', title: 'iOS app control surface work', project: 'iOS Ableton Remote', status: 'queued' },
        { source: '#ableton-live-control', title: 'Control and automation workflows', project: 'Ableton Live Control', status: 'queued' },
      ],
    },
    {
      name: 'PIER Church',
      items: [
        { source: '#chord-charts', title: 'Song/chord prep and formatting', project: 'Chord Charts', status: 'active' },
        { source: '#slide-images-for-church', title: 'Visual assets for services', project: 'Slide Images for Church', status: 'queued' },
        { source: '#pier-song-database', title: 'Catalog songs + metadata', project: 'PIER Song Database', status: 'queued' },
        { source: '#pier-map-app', title: 'PIER map app feature/dev work', project: 'PIER Map App', status: 'active' },
        { source: '#pier-ableton-setup', title: 'Service Ableton setup pipeline', project: 'PIER Ableton Setup', status: 'active' },
      ],
    },
  ];

  const statusStyles: Record<string, string> = {
    hot: 'bg-red-500/15 text-red-300 border-red-500/30',
    active: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
    queued: 'bg-zinc-500/20 text-zinc-300 border-zinc-500/30',
  };

  return (
    <div className="p-6 space-y-6">
      <div className="bg-[#171717] rounded-lg p-4 border border-[#2e2e2e]">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h2 className="text-xl font-semibold text-white">Unified Conversation Hub</h2>
            <p className="text-sm text-[#a3a3a3] mt-1">
              One brain/session, multiple visual lanes by channel + project.
            </p>
          </div>
          <div className="px-3 py-1.5 rounded-md bg-[#8b5cf6]/20 text-[#c4b5fd] text-xs border border-[#8b5cf6]/30">
            Session: agent:main:main
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {lanes.map((lane) => (
          <div key={lane.name} className="bg-[#171717] rounded-lg p-4 border border-[#2e2e2e]">
            <h3 className="text-sm font-medium text-white mb-3">{lane.name}</h3>
            <div className="space-y-3">
              {lane.items.map((item) => (
                <div key={`${item.source}-${item.title}`} className="bg-[#262626] rounded-md p-3">
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="text-xs text-[#c4b5fd]">{item.source}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded border ${statusStyles[item.status]}`}>
                      {item.status}
                    </span>
                  </div>
                  <p className="text-sm text-white">{item.title}</p>
                  <p className="text-xs text-[#737373] mt-1">Project: {item.project}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="bg-[#171717] rounded-lg p-4 border border-[#2e2e2e]">
        <h3 className="text-sm font-medium text-white mb-3">Seeded Project Context</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {projectBriefs.map((brief) => (
            <div key={brief.id} className="bg-[#262626] rounded-md p-3 border border-[#2e2e2e]">
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="text-sm text-white font-medium">{brief.title}</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-[#8b5cf6]/20 text-[#c4b5fd]">{brief.category}</span>
              </div>
              <p className="text-xs text-[#a3a3a3]">{brief.summary}</p>
              <p className="text-[10px] text-[#737373] mt-2">Updated {brief.updated}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-[#171717] rounded-lg p-4 border border-[#2e2e2e]">
        <h3 className="text-sm font-medium text-white mb-3">Routing Notes</h3>
        <ul className="text-sm text-[#a3a3a3] space-y-2 list-disc pl-5">
          <li>Discord channels are still isolated by platform routing, but this view gives you one control surface.</li>
          <li><span className="text-[#c4b5fd]">#squirrely-fun</span> is intentionally excluded here as generic chat (non-project).</li>
          <li>Use tags in your prompts like <span className="text-[#c4b5fd]">[project:PIER]</span> to keep continuity across channels.</li>
          <li>Promote final decisions to MEMORY.md so context survives channel boundaries.</li>
        </ul>
      </div>
    </div>
  );
}

function TaskBoard() {
  const [tasks, setTasks] = useState([
    { id: 1, title: 'Set up Mission Control', status: 'done', assignee: 'Sally' },
    { id: 2, title: 'Connect real data to dashboard', status: 'in-progress', assignee: 'Sally' },
    { id: 3, title: 'Update PIER Map Firebase deploy', status: 'review', assignee: 'Sally' },
    { id: 4, title: 'Healthcheck hardening', status: 'backlog', assignee: 'Sally' },
  ]);

  const columns = [
    { id: 'backlog', label: 'Backlog', color: '#525252' },
    { id: 'in-progress', label: 'In Progress', color: '#f59e0b' },
    { id: 'review', label: 'Review', color: '#8b5cf6' },
    { id: 'done', label: 'Done', color: '#22c55e' },
  ];

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">Task Board</h2>
        <button className="px-4 py-2 bg-[#8b5cf6] text-white rounded-md text-sm hover:bg-[#7c3aed] transition-colors">
          + New Task
        </button>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {columns.map((col) => (
          <div key={col.id} className="bg-[#171717] rounded-lg p-4">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: col.color }}></div>
              <span className="text-sm font-medium text-white">{col.label}</span>
              <span className="text-xs text-[#525252]">
                {tasks.filter(t => t.status === col.id).length}
              </span>
            </div>
            <div className="space-y-2">
              {tasks
                .filter(t => t.status === col.id)
                .map(task => (
                  <div
                    key={task.id}
                    className="bg-[#262626] p-3 rounded-md cursor-pointer hover:bg-[#303030] transition-colors"
                  >
                    <p className="text-sm text-white">{task.title}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-xs text-[#8b5cf6]">👤 {task.assignee}</span>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 bg-[#171717] rounded-lg p-4">
        <h3 className="text-sm font-medium text-white mb-4">Live Activity</h3>
        <div className="space-y-2 text-sm text-[#a3a3a3]">
          <p>• Sally is working on: "Connect real data to dashboard"</p>
          <p>• Gateway: Connected to workspace</p>
          <p>• Last heartbeat: Active</p>
        </div>
      </div>
    </div>
  );
}

function CalendarView({ tasks }: { tasks: typeof scheduledTasks }) {
  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold text-white mb-6">Calendar</h2>
      
      <div className="bg-[#171717] rounded-lg p-4">
        <h3 className="text-sm font-medium text-white mb-4">Scheduled Tasks & Cron Jobs</h3>
        <div className="space-y-2">
          {tasks.map(task => (
            <div key={task.id} className="flex items-center justify-between p-3 bg-[#262626] rounded-md">
              <div className="flex items-center gap-3">
                <span className="text-[#f59e0b]">⏰</span>
                <span className="text-sm text-white">{task.title}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-[#525252]">{task.time}</span>
                <span className="px-2 py-0.5 bg-[#8b5cf6]/20 text-[#8b5cf6] text-xs rounded">cron</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-4 bg-[#171717] rounded-lg p-4">
        <p className="text-sm text-[#525252]">
          Ask Sally: <span className="text-[#8b5cf6]">"What's scheduled for today?"</span>
        </p>
      </div>
    </div>
  );
}

function ProjectsView({ projects }: { projects: Project[] }) {
  const categories = ['Active', 'Ongoing', 'Ideas'];
  
  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">Projects</h2>
      </div>

      {categories.map(cat => (
        <div key={cat} className="mb-6">
          <h3 className="text-sm font-medium text-[#525252] uppercase tracking-wide mb-3">{cat}</h3>
          <div className="grid grid-cols-2 gap-4">
            {projects.filter(p => p.category === cat).map(project => (
              <div key={project.id} className="bg-[#171717] rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-white font-medium">{project.name}</h4>
                </div>
                <div className="w-full bg-[#262626] rounded-full h-2">
                  <div
                    className="bg-[#8b5cf6] h-2 rounded-full"
                    style={{ width: `${project.progress}%` }}
                  ></div>
                </div>
                <p className="text-xs text-[#525252] mt-2">{project.progress}% complete</p>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function MemoryView() {
  const memories = [
    { id: 1, date: 'Today', content: 'Built Mission Control dashboard' },
    { id: 2, date: 'Mar 8', content: 'Healthcheck skill created' },
    { id: 3, date: 'Mar 3', content: 'Monthly budget workflow documented' },
    { id: 4, date: 'Mar 2', content: 'PIER Map app edits workflow established' },
  ];

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold text-white mb-6">Memory</h2>

      <div className="space-y-4">
        {memories.map(memory => (
          <div key={memory.id} className="bg-[#171717] rounded-lg p-4">
            <p className="text-xs text-[#8b5cf6] mb-2">{memory.date}</p>
            <p className="text-sm text-white">{memory.content}</p>
          </div>
        ))}
      </div>

      <div className="mt-6 bg-[#171717] rounded-lg p-4">
        <h3 className="text-sm font-medium text-white mb-2">Long-term Memory</h3>
        <p className="text-sm text-[#525252]">
          Full MEMORY.md is loaded — includes Ableton tools, Planning Center API, GitHub repos, and Google Sheets integration.
        </p>
      </div>
    </div>
  );
}

function DocsView({ docs }: { docs: DocItem[] }) {
  const [search, setSearch] = useState('');

  const filteredDocs = docs.filter(d => 
    d.title.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">Documents</h2>
        <input
          type="text"
          placeholder="Search docs..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-3 py-2 bg-[#262626] border border-[#2e2e2e] rounded-md text-sm text-white placeholder-[#525252] w-64"
        />
      </div>

      <div className="space-y-2">
        {filteredDocs.map(doc => (
          <div key={doc.id} className="flex items-center justify-between p-3 bg-[#171717] rounded-lg hover:bg-[#262626] cursor-pointer transition-colors">
            <div className="flex items-center gap-3">
              <span className="text-[#8b5cf6]">📄</span>
              <span className="text-sm text-white">{doc.title}</span>
              <span className="px-2 py-0.5 bg-[#262626] text-[#525252] text-xs rounded">{doc.type}</span>
            </div>
            <span className="text-xs text-[#525252]">{doc.path}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function TeamView({ mission }: { mission: string }) {
  const agents = [
    { id: 1, name: 'Sally', role: 'Main Assistant', status: 'online', device: "Ryan's M1" },
    { id: 2, name: 'Sub-agents', role: 'Task Workers', status: 'idle', device: 'On-demand' },
  ];

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold text-white mb-6">Team</h2>

      <div className="bg-[#171717] rounded-lg p-4 mb-6">
        <h3 className="text-xs text-[#525252] uppercase tracking-wide mb-2">Mission Statement</h3>
        <p className="text-white">{mission}</p>
      </div>

      <div className="space-y-3">
        {agents.map(agent => (
          <div key={agent.id} className="flex items-center justify-between p-4 bg-[#171717] rounded-lg">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-[#8b5cf6] flex items-center justify-center text-white font-medium">
                {agent.name[0]}
              </div>
              <div>
                <p className="text-white font-medium">{agent.name}</p>
                <p className="text-xs text-[#525252]">{agent.role}</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-xs text-[#525252]">{agent.device}</span>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${agent.status === 'online' ? 'bg-[#22c55e]' : 'bg-[#525252]'}`}></div>
                <span className="text-xs text-[#a3a3a3] capitalize">{agent.status}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function OfficeView() {
  const desks = [
    { id: 1, name: 'Sally', status: 'working', task: 'Building Mission Control' },
    { id: 2, name: 'Sub-agents', status: 'idle', task: 'Waiting for tasks' },
  ];

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold text-white mb-6">Office</h2>

      <div className="bg-[#171717] rounded-lg p-6">
        <div className="grid grid-cols-2 gap-6">
          {desks.map(desk => (
            <div key={desk.id} className="bg-[#262626] rounded-lg p-4 border-2 border-dashed border-[#2e2e2e]">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded bg-[#8b5cf6] flex items-center justify-center">
                    <span className="text-white text-sm">🖥️</span>
                  </div>
                  <span className="text-white font-medium">{desk.name}</span>
                </div>
                <span className={`px-2 py-0.5 text-xs rounded ${
                  desk.status === 'working' 
                    ? 'bg-[#22c55e]/20 text-[#22c55e]' 
                    : 'bg-[#525252]/20 text-[#525252]'
                }`}>
                  {desk.status}
                </span>
              </div>
              <p className="text-xs text-[#525252]">{desk.task}</p>
            </div>
          ))}
        </div>

        <div className="mt-6 pt-6 border-t border-[#2e2e2e]">
          <h3 className="text-sm font-medium text-white mb-3">💧 Water Cooler</h3>
          <p className="text-xs text-[#525252]">Agents can meet and collaborate here.</p>
        </div>
      </div>
    </div>
  );
}
