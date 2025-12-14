import { useState } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Play, Shield, Heart, Activity, CheckCircle, AlertTriangle, FileText, RefreshCw, Zap } from 'lucide-react';

// Types
interface ProtocolState {
  user_intent: string;
  current_draft: string;
  previous_drafts: string[];
  feedback_from_agents: Record<string, string>;
  safety_score: number;
  empathy_score: number;
  iteration_count: number;
  status: "drafting" | "reviewing" | "halted" | "approved";
}

interface ThreadResponse {
  thread_id: string;
  state: ProtocolState;
  next: string[] | null;
  status: "interrupted" | "completed";
}

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [threadId, setThreadId] = useState<string | null>(null);
  const [intent, setIntent] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<ThreadResponse | null>(null);
  const [draftEdit, setDraftEdit] = useState("");

  // Start Workflow
  const startWorkflow = async () => {
    if (!intent) return;
    setLoading(true);
    try {
      const res = await axios.post(`${API_URL}/thread`, { user_intent: intent });
      setThreadId(res.data.thread_id);
      setData(res.data);
      setDraftEdit(res.data.state.current_draft || "");
    } catch (err) {
      console.error(err);
      alert("Failed to start workflow. Ensure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const [feedback, setFeedback] = useState("");

  // Resume Workflow with Action
  const handleAction = async (action: "approve" | "revise") => {
    if (!threadId) return;
    setLoading(true);
    try {
      const payload = {
        current_draft: draftEdit,
        action,
        feedback: action === "revise" ? feedback : undefined
      };

      const res = await axios.post(`${API_URL}/thread/${threadId}/resume`, payload);
      setData(res.data);
      setDraftEdit(res.data.state.current_draft || "");
      if (res.data.status !== "interrupted") {
        setFeedback(""); // Clear feedback if done
      }
    } catch (err) {
      console.error(err);
      alert(`Failed to ${action} workflow.`);
    } finally {
      setLoading(false);
    }
  };

  if (!threadId || !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-4 w-full relative overflow-hidden">
        {/* Decorative Background Elements */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-[100px] pointer-events-none" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-[100px] pointer-events-none" />

        <div className="glass-panel p-12 max-w-2xl w-full text-center space-y-8 animate-fade-in relative z-10 border-t border-white/10">
          <div className="flex justify-center mb-6">
            <div className="p-4 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-white/5 shadow-2xl shadow-blue-500/20">
              <Activity size={48} className="text-blue-400" />
            </div>
          </div>

          <div className="space-y-4">
            <h1 className="text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 tracking-tight">
              FlowState
            </h1>
            <p className="text-gray-400 text-lg max-w-md mx-auto leading-relaxed">
              Design clinical-grade CBT protocols with an autonomous multi-agent team.
            </p>
          </div>

          <div className="flex gap-3 mt-10 w-full relative">
            <input
              type="text"
              className="glass-input text-lg pl-6 pr-32 h-14"
              placeholder="Describe the clinical intent..."
              value={intent}
              onChange={(e) => setIntent(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && startWorkflow()}
            />
            <button
              className="absolute right-2 top-2 bottom-2 btn-primary flex items-center gap-2 h-10 px-6 text-sm"
              onClick={startWorkflow}
              disabled={loading}
            >
              {loading ? (
                <RefreshCw size={18} className="animate-spin" />
              ) : (
                <>Generate <Zap size={16} className="fill-current" /></>
              )}
            </button>
          </div>

          <div className="flex justify-center gap-6 pt-4 border-b border-white/5 pb-8 mb-8">
            {['Exposure Therapy', 'Cognitive Reframing', 'Sleep Hygiene'].map((tag) => (
              <button
                key={tag}
                onClick={() => setIntent(`Create a protocol for ${tag}`)}
                className="text-xs text-gray-500 hover:text-blue-400 transition-colors uppercase tracking-widest font-semibold hover:bg-white/5 px-3 py-1 rounded-full"
              >
                {tag}
              </button>
            ))}
          </div>


        </div>
      </div>
    );
  }

  const { state, status } = data;
  const isInterrupted = status === "interrupted";

  return (
    <div className="dashboard-grid w-full h-screen overflow-hidden animate-fade-in">
      {/* Left Sidebar: Context & Metrics */}
      <div className="glass-panel p-6 flex flex-col gap-6 h-full overflow-hidden flex-shrink-0 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/5">
          <div>
            <h2 className="text-lg font-semibold text-white tracking-tight">Mission Control</h2>
            <div className="flex items-center gap-2 mt-1">
              <div className={`w-2 h-2 rounded-full ${isInterrupted ? 'bg-yellow-400 animate-pulse' : 'bg-green-400'}`} />
              <span className="text-xs text-gray-400 uppercase tracking-wider font-medium">
                {isInterrupted ? "Awaiting Review" : "System Idle"}
              </span>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-mono text-gray-500 font-bold opacity-30">v{state.iteration_count}</div>
          </div>
        </div>

        {/* Metrics */}
        <div className="space-y-3">
          <h3 className="text-xs uppercase text-gray-500 font-bold tracking-widest pl-1">Safety & Quality</h3>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-white/5 p-4 rounded-xl border border-white/5 flex flex-col items-center justify-center gap-2">
              <Shield size={24} className={state.safety_score < 0.8 ? "text-red-400" : "text-emerald-400"} />
              <div className="text-2xl font-bold font-mono">{state.safety_score.toFixed(2)}</div>
              <div className="text-xs text-gray-500">Safety</div>
            </div>
            <div className="bg-white/5 p-4 rounded-xl border border-white/5 flex flex-col items-center justify-center gap-2">
              <Heart size={24} className={state.empathy_score < 3 ? "text-amber-400" : "text-purple-400"} />
              <div className="text-2xl font-bold font-mono">{state.empathy_score.toFixed(1)}</div>
              <div className="text-xs text-gray-500">Empathy</div>
            </div>
          </div>
        </div>

        {/* Agent Feedback */}
        <div className="flex-1 flex flex-col min-h-0">
          <h3 className="text-xs uppercase text-gray-500 font-bold tracking-widest pl-1 mb-3">Agent Communications</h3>
          <div className="overflow-y-auto space-y-3 pr-2 scrollable flex-1">
            {state.feedback_from_agents && Object.entries(state.feedback_from_agents).map(([agent, note]) => (
              <div key={agent} className="bg-white/5 p-4 rounded-xl border-l-2 border-blue-500/50 hover:bg-white/10 transition-colors">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                  <span className="text-xs text-blue-300 uppercase font-bold tracking-wider">{agent}</span>
                </div>
                <p className="text-sm text-gray-300 leading-relaxed font-light">{note}</p>
              </div>
            ))}
            {(!state.feedback_from_agents || Object.keys(state.feedback_from_agents).length === 0) && (
              <div className="text-center py-8 text-gray-600 italic text-sm border-2 border-dashed border-white/5 rounded-xl">
                No active feedback loop.
              </div>
            )}
          </div>
        </div>

        {/* Human Feedback Input logic */}
        {isInterrupted && (
          <div className="pt-4 border-t border-white/5 animate-fade-in">
            <label className="text-xs text-gray-400 font-semibold uppercase tracking-wider mb-2 block flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-blue-500 flex items-center justify-center text-[10px] text-white font-bold">You</div>
              Supervisor Override
            </label>
            <textarea
              className="glass-input text-sm h-24 resize-none mb-3 bg-black/20 focus:bg-black/40"
              placeholder="Direct the agents on how to refine this protocol..."
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
            />
          </div>
        )}
      </div>

      {/* Right Main: Draft Editor/View */}
      <div className="glass-panel p-8 flex flex-col h-full overflow-hidden relative">
        <div className="flex items-center justify-between mb-8 flex-shrink-0 z-10 relative">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-500/10 rounded-xl border border-blue-500/20">
              <FileText className="text-blue-400" size={24} />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight">Active Protocol Draft</h2>
              <div className="text-sm text-gray-500 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-gray-600"></span>
                {intent}
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            {isInterrupted && (
              <>
                <button className="btn-secondary text-red-300 hover:text-red-200 hover:bg-red-500/10 hover:border-red-500/20" onClick={() => handleAction("revise")}>
                  Request Revision
                </button>
                <button className="btn-primary flex items-center gap-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:shadow-emerald-500/20" onClick={() => handleAction("approve")} disabled={loading}>
                  {loading ? "Processing..." : <>Approve Protocol <CheckCircle size={18} /></>}
                </button>
              </>
            )}
            {!isInterrupted && (
              <button className="btn-primary" onClick={() => { setThreadId(null); setData(null); }}>
                Initialize New Sequence
              </button>
            )}
          </div>
        </div>

        <div className="flex-1 overflow-hidden flex flex-col relative rounded-xl border border-white/5 bg-black/20">
          {isInterrupted ? (
            <div className="flex h-full">
              {/* Split view for editing: Left is Editor, Right is Preview */}
              <div className="w-1/2 h-full border-r border-white/5 flex flex-col">
                <div className="px-4 py-2 bg-white/5 border-b border-white/5 text-xs font-mono text-gray-400 uppercase tracking-widest">Raw Editor</div>
                <textarea
                  className="w-full h-full bg-transparent text-gray-300 p-6 focus:outline-none resize-none font-mono leading-relaxed text-sm"
                  value={draftEdit}
                  onChange={(e) => setDraftEdit(e.target.value)}
                  spellCheck={false}
                />
              </div>
              <div className="w-1/2 h-full flex flex-col bg-black/20">
                <div className="px-4 py-2 bg-white/5 border-b border-white/5 text-xs font-mono text-gray-400 uppercase tracking-widest">Live Preview</div>
                <div className="overflow-y-auto p-8 prose prose-invert max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{draftEdit}</ReactMarkdown>
                </div>
              </div>
            </div>
          ) : (
            <div className="w-full h-full text-gray-200 overflow-y-auto p-12 scrollable">
              <div className="prose prose-invert prose-lg max-w-3xl mx-auto">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{state.current_draft}</ReactMarkdown>
              </div>
            </div>
          )}
        </div>

        {isInterrupted && (
          <div className="absolute bottom-6 right-8 left-8 pointer-events-none flex justify-center">
            <div className="bg-yellow-500/10 border border-yellow-500/20 backdrop-blur-md px-4 py-2 rounded-full flex items-center gap-2 text-yellow-200 text-sm shadow-xl pointer-events-auto">
              <AlertTriangle size={14} />
              <span className="font-semibold">Review Mode Active</span>
              <span className="w-px h-3 bg-yellow-500/30 mx-1"></span>
              <span className="opacity-80">Edit the Markdown content directly to refine logic.</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
