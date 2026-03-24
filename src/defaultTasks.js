// src/defaultTasks.js
// These are loaded only on a user's very first login.
// After that, all data comes from Firestore.

export const CATEGORIES = ["Recurring", "Work", "Project (Deadline)", "Project (Open-ended)", "Personal/Home"];

export const CATEGORY_COLORS = {
  "Recurring":             "#4ade80",
  "Work":                  "#c084fc",
  "Project (Deadline)":    "#f87171",
  "Project (Open-ended)":  "#fb923c",
  "Personal/Home":         "#60a5fa",
};

export const DEFAULT_WEEKLY_HOURS = 20;

export const DEFAULT_TASKS = [
  { name: "Worship leading (weekly)",               category: "Work",                   hours: 4,  done: 0, deadline: "", notes: "Slides, practice, Ableton" },
  { name: "Music lessons (weekly)",                 category: "Work",                   hours: 3,  done: 0, deadline: "", notes: "" },
  { name: "Evangelism outings & planning",          category: "Work",                   hours: 3,  done: 0, deadline: "", notes: "Prayer walks + door knocking" },
  { name: "PIER map app tweaks",                    category: "Project (Open-ended)",   hours: 8,  done: 0, deadline: "", notes: "" },
  { name: "7 one-on-one calls (music career)",      category: "Project (Deadline)",     hours: 7,  done: 0, deadline: "2025-04-30", notes: "7 × ~1hr each" },
  { name: "Byron — music theory resources",         category: "Project (Deadline)",     hours: 2,  done: 0, deadline: "", notes: "" },
  { name: "Becky — chord chart + audio file",       category: "Project (Deadline)",     hours: 3,  done: 0, deadline: "", notes: "Music for her poem" },
  { name: "Sylvia — record her song",               category: "Project (Open-ended)",   hours: 8,  done: 0, deadline: "", notes: "" },
  { name: "David — record his song",                category: "Project (Open-ended)",   hours: 8,  done: 0, deadline: "", notes: "" },
  { name: "James & Morgan — full album",            category: "Project (Open-ended)",   hours: 40, done: 0, deadline: "", notes: "" },
  { name: "Own songs — The Writer",                 category: "Project (Open-ended)",   hours: 6,  done: 0, deadline: "", notes: "" },
  { name: "Own songs — Even If You Take Everything",category: "Project (Open-ended)",   hours: 6,  done: 0, deadline: "", notes: "" },
  { name: "Own songs — Taste and See",              category: "Project (Open-ended)",   hours: 6,  done: 0, deadline: "", notes: "" },
  { name: "YouTube / social media posts",           category: "Recurring",              hours: 3,  done: 0, deadline: "", notes: "Weekly habit" },
  { name: "Kitchen cleaning (weekly)",              category: "Recurring",              hours: 1.5,done: 0, deadline: "", notes: "" },
  { name: "Laundry (weekly)",                       category: "Recurring",              hours: 1.5,done: 0, deadline: "", notes: "" },
  { name: "Mow the lawn (weekly)",                  category: "Recurring",              hours: 1.5,done: 0, deadline: "", notes: "" },
  { name: "Paint downstairs bathroom wall",         category: "Personal/Home",          hours: 4,  done: 0, deadline: "", notes: "" },
  { name: "Paint around window trim",               category: "Personal/Home",          hours: 6,  done: 0, deadline: "", notes: "" },
  { name: "Install new toilet seat",                category: "Personal/Home",          hours: 1,  done: 0, deadline: "", notes: "" },
  { name: "Fix shower tub floor",                   category: "Personal/Home",          hours: 5,  done: 0, deadline: "", notes: "" },
  { name: "Sort / organize clothes & belongings",   category: "Personal/Home",          hours: 6,  done: 0, deadline: "", notes: "" },
  { name: "Clean out the garage",                   category: "Personal/Home",          hours: 8,  done: 0, deadline: "", notes: "" },
];
