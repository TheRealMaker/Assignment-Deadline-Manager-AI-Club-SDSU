import { useState, useEffect, useRef } from "react";
import "./App.css";

/* ── API helpers ──────────────────────────────────────────────────────────── */
const api = {
  async courses(token) {
    const r = await fetch("/api/courses", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    });
    return r.json();
  },
  async assignments(token, course_id) {
    const r = await fetch("/api/assignments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, course_id }),
    });
    return r.json();
  },
  async ai({ pending, finished, message, token }) {
    const r = await fetch("/api/ai", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pending, finished, message, token }),
    });
    return r.json();
  },
};

/* ── Helpers ──────────────────────────────────────────────────────────────── */
function fmtDate(iso) {
  if (!iso || iso === "No due date") return "No due date";
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short", day: "numeric", hour: "numeric", minute: "2-digit",
  });
}

function getDifficulty(due_at, submitted_at) {
  if (!submitted_at) return { label: "Pending", cls: "diff-unknown" };
  if (!due_at || due_at === "No due date") return { label: "Unknown", cls: "diff-unknown" };
  const due = new Date(due_at);
  const sub = new Date(submitted_at);
  const gapHours = (due - sub) / 36e5;

  if (gapHours < 0) return { label: "Late", cls: "diff-late" };
  if (gapHours < 6) return { label: "Hard", cls: "diff-hard" };
  if (gapHours < 48) return { label: "Medium", cls: "diff-medium" };
  return { label: "Easy", cls: "diff-easy" };
}

/* ── Donut chart ──────────────────────────────────────────────────────────── */
function Donut({ pct }) {
  const r = 26, circ = 2 * Math.PI * r;
  const filled = (pct / 100) * circ;
  return (
    <div className="donut-wrap">
      <svg viewBox="0 0 64 64" style={{ transform: "rotate(-90deg)" }}>
        <circle cx="32" cy="32" r={r} fill="none" stroke="#1a1a1a" strokeWidth="8" />
        <circle cx="32" cy="32" r={r} fill="none" stroke="#e24b4a"
          strokeWidth="8" strokeDasharray={`${filled} ${circ - filled}`} strokeLinecap="round" />
        <circle cx="32" cy="32" r={r} fill="none" stroke="#34d399"
          strokeWidth="8"
          strokeDasharray={`${circ - filled} ${filled}`}
          strokeDashoffset={-filled}
          strokeLinecap="round" />
      </svg>
      <span className="donut-pct">{pct}%</span>
    </div>
  );
}

/* ── Calendar ─────────────────────────────────────────────────────────────── */
function CalendarView({ allAssignments }) {
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth());
  const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const MONTHS = ["January","February","March","April","May","June",
                  "July","August","September","October","November","December"];

  const submittedDays = new Set(
    allAssignments
      .filter(a => a.submitted_at)
      .map(a => {
        const d = new Date(a.submitted_at);
        return d.getFullYear() === year && d.getMonth() === month ? d.getDate() : null;
      })
      .filter(Boolean)
  );

  const dueDays = new Set(
    allAssignments
      .filter(a => a.due_at && a.due_at !== "No due date")
      .map(a => {
        const d = new Date(a.due_at);
        return d.getFullYear() === year && d.getMonth() === month ? d.getDate() : null;
      })
      .filter(Boolean)
  );

  const firstDay = new Date(year, month, 1).getDay();
  const totalDays = new Date(year, month + 1, 0).getDate();
  const today = new Date();

  function prevMonth() {
    if (month === 0) { setMonth(11); setYear(y => y - 1); }
    else setMonth(m => m - 1);
  }
  function nextMonth() {
    if (month === 11) { setMonth(0); setYear(y => y + 1); }
    else setMonth(m => m + 1);
  }

  return (
    <div className="view-body">
      <div className="cal-nav">
        <button className="icon-btn" onClick={prevMonth}>‹</button>
        <span className="cal-title">{MONTHS[month]} {year}</span>
        <button className="icon-btn" onClick={nextMonth}>›</button>
      </div>
      <div className="cal-legend">
        <span className="leg-item"><span className="leg-dot leg-due" />Due date</span>
        <span className="leg-item"><span className="leg-dot leg-sub" />Submitted</span>
      </div>
      <div className="cal-grid">
        {DAYS.map(d => <div key={d} className="cal-day-label">{d}</div>)}
        {Array(firstDay).fill(null).map((_, i) => <div key={`e${i}`} />)}
        {Array(totalDays).fill(null).map((_, i) => {
          const d = i + 1;
          const isToday = d === today.getDate() && month === today.getMonth() && year === today.getFullYear();
          const isDue = dueDays.has(d);
          const isSub = submittedDays.has(d);
          return (
            <div key={d} className={`cal-cell${isDue ? " is-due" : ""}${isSub ? " is-sub" : ""}${isToday ? " today" : ""}`}>
              {d}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ── Schedule ─────────────────────────────────────────────────────────────── */
function ScheduleView({ courses }) {
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri"];
  return (
    <div className="view-body">
      <div className="sched-grid">
        {days.map(day => (
          <div key={day} className="day-col">
            <div className="day-header">{day}</div>
            <div className="day-body">
              {courses.slice(0, 2).map((c, i) => (
                <div key={c.id} className="class-chip">
                  <div className="chip-name">{c.course_code || c.name}</div>
                  <div className="chip-time">{i === 0 ? "10:00–11:15" : "14:00–15:15"}</div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      {courses.length === 0 && <p className="empty-msg">Log in to see your schedule.</p>}
    </div>
  );
}

/* ── Chat ─────────────────────────────────────────────────────────────────── */
function ChatView({ activeAssignments, token }) {
  const [msgs, setMsgs] = useState([
    { role: "ai", text: "Hi! I'm your SDSU deadline assistant. Select a course and click \"Ask AI\" to get difficulty rankings and prioritized advice, or ask me anything." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs]);

  async function send(textOverride) {
    const text = textOverride || input.trim();
    if (!text) return;
    setInput("");
    setMsgs(m => [...m, { role: "user", text }]);
    setLoading(true);

    const pending = activeAssignments.pending || [];
    const finished = activeAssignments.finished || [];

    const data = await api.ai({ pending, finished, message: text, token });
    setLoading(false);
    setMsgs(m => [...m, { role: "ai", text: data.ai_response || data.error || "No response." }]);
  }

  return (
    <div className="chat-outer">
      <div className="chat-messages">
        {msgs.map((m, i) => (
          <div key={i} className={`bubble bubble-${m.role}`}>{m.text}</div>
        ))}
        {loading && (
          <div className="bubble bubble-ai">
            <span className="dots"><span /><span /><span /></span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="chat-input-row">
        <input
          className="chat-input"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && send()}
          placeholder="Ask about your assignments…"
        />
        <button className="send-btn" onClick={() => send()}>
          <svg viewBox="0 0 16 16" fill="currentColor"><path d="M1 1l14 7-14 7V9.5l10-1.5L1 6.5V1z" /></svg>
        </button>
      </div>
    </div>
  );
}

/* ── Class / Dashboard ────────────────────────────────────────────────────── */
function ClassView({ course, token, onAskAI, setActiveAssignments }) {
  const [assignments, setAssignments] = useState(null);
  const [pending, setPending] = useState([]);
  const [finished, setFinished] = useState([]);
  const [loading, setLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiResult, setAiResult] = useState("");

  useEffect(() => {
    if (!course || !token) return;
    setAssignments(null);
    setAiResult("");
    setLoading(true);
    api.assignments(token, course.id).then(d => {
      const p = d.pending || [];
      const f = d.finished || [];
      setPending(p);
      setFinished(f);
      setAssignments([...p, ...f]);
      setActiveAssignments({ pending: p, finished: f });
      setLoading(false);
    });
  }, [course?.id]);

  async function handleAskAI() {
    if (!pending.length && !finished.length) return;
    setAiLoading(true);
    const d = await api.ai({
      pending,
      finished,
      message: "Please prioritize my assignments.",
      token,
    });
    setAiResult(d.ai_response || d.error || "No response.");
    setAiLoading(false);
    onAskAI();
  }

  const diffScore = finished.length
    ? Math.round(
        (finished.filter(a => {
          const diff = getDifficulty(a.due_at, a.submitted_at);
          return diff.label === "Hard" || diff.label === "Late";
        }).length / finished.length) * 100
      )
    : 0;

  return (
    <div className="view-body">
      {!course && <p className="empty-msg">Select a course from the sidebar.</p>}
      {course && loading && <p className="empty-msg">Loading assignments…</p>}

      {course && assignments && assignments.length === 0 && (
        <p className="empty-msg">No assignments found for this course.</p>
      )}

      {course && assignments && assignments.length > 0 && (
        <>
          {/* Stats row */}
          <div className="stats-row">
            <div className="stat-card">
              <div className="stat-label">Pending</div>
              <div className="stat-value">{pending.length}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Submitted</div>
              <div className="stat-value">{finished.length}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Hard / Late</div>
              <div className="stat-value red">
                {finished.filter(a => ["Hard","Late"].includes(getDifficulty(a.due_at, a.submitted_at).label)).length}
              </div>
            </div>
          </div>

          {/* Difficulty overview card */}
          <div className="procrast-card">
            <div className="procrast-info">
              <div className="section-label" style={{ marginBottom: 4 }}>Course difficulty estimate</div>
              <p className="procrast-sub">
                Based on how close to the deadline you submitted past assignments.
                Smaller gaps = harder course.
              </p>
              <button className="ai-btn" onClick={handleAskAI} disabled={aiLoading}>
                {aiLoading ? "Asking AI…" : "Ask AI to rank difficulty ↗"}
              </button>
            </div>
            <Donut pct={diffScore} />
          </div>

          {/* Pending assignments */}
          {pending.length > 0 && (
            <>
              <div className="section-label" style={{ marginTop: 16 }}>Upcoming assignments</div>
              {pending.map(a => {
                const diff = a.difficulty || { label: "Unknown", cls: "diff-unknown" };
                return (
                  <div key={a.assignment_id} className="due-item">
                    <div className="due-info">
                      <div className="due-name">{a.name}</div>
                      <div className="due-meta">
                        <span className="meta-item">Due {fmtDate(a.due_at)}</span>
                        {diff.label !== "Unknown" && (
                          <>
                            <span className="meta-sep">·</span>
                            <span className="meta-item">Based on past work</span>
                          </>
                        )}
                      </div>
                    </div>
                    <span className={`diff-tag ${diff.cls}`}>{diff.label}</span>
                  </div>
                );
              })}
            </>
          )}

          {/* Finished assignments */}
          {finished.length > 0 && (
            <>
              <div className="section-label" style={{ marginTop: 16 }}>Submitted assignments</div>
              {finished.map(a => {
                const diff = getDifficulty(a.due_at, a.submitted_at);
                return (
                  <div key={a.assignment_id} className="due-item">
                    <div className="due-info">
                      <div className="due-name">{a.name}</div>
                      <div className="due-meta">
                        <span className="meta-item">Due {fmtDate(a.due_at)}</span>
                        <span className="meta-sep">·</span>
                        <span className="meta-item">Submitted {fmtDate(a.submitted_at)}</span>
                      </div>
                    </div>
                    <span className={`diff-tag ${diff.cls}`}>{diff.label}</span>
                  </div>
                );
              })}
            </>
          )}

          {/* AI result inline */}
          {aiResult && (
            <div className="ai-response-box">
              <div className="section-label" style={{ marginBottom: 8 }}>AI Advisor</div>
              <p className="ai-response-text">{aiResult}</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}

/* ── Login ────────────────────────────────────────────────────────────────── */
function LoginScreen({ onLogin }) {
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit() {
    if (!token.trim()) return;
    setLoading(true);
    setError("");
    const data = await api.courses(token.trim());
    setLoading(false);
    if (data.error) { setError(data.error); return; }
    onLogin(token.trim(), data.courses || []);
  }

  return (
    <div className="login-screen">
      <div className="login-card">
        <div className="login-logo">📚</div>
        <h1 className="login-title">Deadline Manager</h1>
        <p className="login-sub">Connect your Canvas account to get started.</p>
        <input
          className="login-input"
          type="password"
          placeholder="Paste your Canvas API token"
          value={token}
          onChange={e => setToken(e.target.value)}
          onKeyDown={e => e.key === "Enter" && handleSubmit()}
        />
        {error && <p className="login-error">{error}</p>}
        <button className="login-btn" onClick={handleSubmit} disabled={loading || !token}>
          {loading ? "Connecting…" : "Connect to Canvas"}
        </button>
        <p className="login-hint">
          Get your token: <strong>Canvas → Account → Settings → New Access Token</strong>
        </p>
      </div>
    </div>
  );
}

/* ── Root ─────────────────────────────────────────────────────────────────── */
export default function App() {
  const [token, setToken] = useState("");
  const [courses, setCourses] = useState([]);
  const [activeCourse, setActiveCourse] = useState(null);
  const [activeView, setActiveView] = useState("class");
  const [activeAssignments, setActiveAssignments] = useState({ pending: [], finished: [] });
  const [allAssignments, setAllAssignments] = useState([]);

  function handleLogin(tok, courseList) {
    setToken(tok);
    setCourses(courseList);
  }

  function handleSelectCourse(course) {
    setActiveCourse(course);
    setActiveView("class");
  }

  function mergeAssignments({ pending, finished }) {
    setActiveAssignments({ pending, finished });
    setAllAssignments(prev => {
      const ids = new Set(prev.map(a => a.assignment_id));
      const all = [...pending, ...finished];
      return [...prev, ...all.filter(a => !ids.has(a.assignment_id))];
    });
  }

  if (!token) return <LoginScreen onLogin={handleLogin} />;

  const viewTitle = {
    class: activeCourse ? activeCourse.name : "Select a course",
    calendar: "Smart Calendar",
    schedule: "Weekly Schedule",
    chat: "AI Advisor",
  }[activeView];

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="sidebar-brand">Deadline Manager</div>
        <div className="sidebar-section-label">Courses</div>
        {courses
          .filter(c => !c.name.includes("Homeroom") && !c.name.includes("Tech How-to"))
          .map(c => (
            <button
              key={c.id}
              className={`nav-btn${activeCourse?.id === c.id && activeView === "class" ? " active" : ""}`}
              onClick={() => handleSelectCourse(c)}
            >
              {c.course_code || c.name}
            </button>
          ))}
        <div className="sidebar-divider" />
        {["chat", "calendar", "schedule"].map(v => (
          <button
            key={v}
            className={`nav-btn${activeView === v ? " active" : ""}`}
            onClick={() => setActiveView(v)}
          >
            {{ chat: "Chat", calendar: "Calendar", schedule: "Schedule" }[v]}
          </button>
        ))}
        <div className="sidebar-footer">
          <button className="logout-btn" onClick={() => { setToken(""); setCourses([]); }}>
            Log out
          </button>
        </div>
      </aside>

      <main className="main">
        <div className="view-header">{viewTitle}</div>
        {activeView === "class" && (
          <ClassView
            course={activeCourse}
            token={token}
            onAskAI={() => setActiveView("chat")}
            setActiveAssignments={mergeAssignments}
          />
        )}
        {activeView === "calendar" && <CalendarView allAssignments={allAssignments} />}
        {activeView === "schedule" && <ScheduleView courses={courses} />}
        {activeView === "chat" && (
          <ChatView activeAssignments={activeAssignments} token={token} />
        )}
      </main>
    </div>
  );
}