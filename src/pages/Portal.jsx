import { useEffect, useState } from 'react'
import axios from 'axios'
import { CheckCheck, Clock, AlertOctagon, Eye } from 'lucide-react'
import RiskBadge from '../components/RiskBadge'

export default function Portal() {
  const [cases, setCases] = useState([])
  const [stats, setStats] = useState(null)
  const [selected, setSelected] = useState(null)
  const [notes, setNotes] = useState('')
  const [saving, setSaving] = useState(false)
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(true)

  const fetchCases = async () => {
    const params = filter !== 'all' ? { status: filter } : {}
    const [casesRes, statsRes] = await Promise.all([
      axios.get('/api/portal/cases', { params }),
      axios.get('/api/portal/stats'),
    ])
    setCases(casesRes.data)
    setStats(statsRes.data)
    setLoading(false)
  }

  useEffect(() => { fetchCases() }, [filter])

  const openCase = async (id) => {
    const { data } = await axios.get(`/api/portal/cases/${id}`)
    setSelected(data)
    setNotes(data.professional_notes || '')
  }

  const handleReview = async () => {
    setSaving(true)
    await axios.patch(`/api/portal/cases/${selected.id}/review`, {
      notes,
      status: 'reviewed',
    })
    setSaving(false)
    setSelected(null)
    fetchCases()
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-10 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Professional Portal</h1>
          <p className="text-sm text-slate-500">Review AI-flagged cases submitted for clinical assessment</p>
        </div>
      </div>

      {/* Stats bar */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Total cases',   value: stats.total,    icon: <Eye size={16} />,           color: 'text-blue-600' },
            { label: 'Pending',       value: stats.pending,  icon: <Clock size={16} />,          color: 'text-amber-600' },
            { label: 'Reviewed',      value: stats.reviewed, icon: <CheckCheck size={16} />,     color: 'text-green-600' },
            { label: 'High risk',     value: stats.high_risk,icon: <AlertOctagon size={16} />,   color: 'text-red-600' },
          ].map((s) => (
            <div key={s.label} className="card text-center">
              <div className={`flex justify-center mb-1 ${s.color}`}>{s.icon}</div>
              <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
              <div className="text-xs text-slate-500">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Filter tabs */}
      <div className="flex gap-2">
        {['all', 'pending', 'reviewed'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium capitalize transition-colors ${
              filter === f ? 'bg-blue-600 text-white' : 'bg-white border border-slate-300 text-slate-600 hover:bg-slate-50'
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Cases table */}
      {loading ? (
        <div className="text-center py-12 text-slate-400">Loading cases…</div>
      ) : cases.length === 0 ? (
        <div className="text-center py-16 text-slate-400">
          <Eye size={32} className="mx-auto mb-3 opacity-30" />
          <p>No cases yet. High-risk diagnoses will appear here automatically.</p>
        </div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50">
                <th className="text-left px-4 py-3 font-medium text-slate-600">Image</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Condition</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Risk</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Confidence</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Date</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Status</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {cases.map((c) => (
                <tr key={c.id} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                  <td className="px-4 py-3">
                    <img
                      src={`/uploads/${c.image_filename}`}
                      alt=""
                      className="w-12 h-12 object-cover rounded-lg border border-slate-200"
                    />
                  </td>
                  <td className="px-4 py-3 font-medium text-slate-800">{c.condition_display}</td>
                  <td className="px-4 py-3"><RiskBadge level={c.risk_level} /></td>
                  <td className="px-4 py-3 text-slate-600">{c.confidence}%</td>
                  <td className="px-4 py-3 text-slate-400 text-xs">
                    {c.created_at ? new Date(c.created_at).toLocaleDateString('en-GB') : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${
                      c.status === 'reviewed' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
                    }`}>
                      {c.status === 'reviewed' ? <CheckCheck size={10} /> : <Clock size={10} />}
                      {c.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => openCase(c.id)}
                      className="text-blue-600 hover:underline text-xs font-medium"
                    >
                      Review
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Case detail modal */}
      {selected && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto shadow-xl">
            <div className="p-6 space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">{selected.condition_display}</h2>
                  <p className="text-sm text-slate-500">Case #{selected.id}</p>
                </div>
                <RiskBadge level={selected.risk_level} large />
              </div>

              <img
                src={`/uploads/${selected.image_filename}`}
                alt=""
                className="w-full rounded-xl border border-slate-200"
              />

              <div className="text-sm text-slate-600 space-y-1">
                <p><span className="font-medium">AI confidence:</span> {selected.confidence}%</p>
                <p><span className="font-medium">Location:</span> {selected.body_location || 'Not specified'}</p>
                <p><span className="font-medium">Submitted:</span> {selected.created_at ? new Date(selected.created_at).toLocaleString('en-GB') : '—'}</p>
              </div>

              <div className="bg-slate-50 rounded-lg p-3 text-sm text-slate-600">
                <p className="font-medium mb-1">AI Recommendation</p>
                <p>{selected.recommendation}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Clinical notes
                </label>
                <textarea
                  rows={4}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Add your clinical observations…"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />
              </div>

              <div className="flex justify-between gap-3">
                <button
                  onClick={() => setSelected(null)}
                  className="btn-secondary flex-1"
                >
                  Close
                </button>
                <button
                  onClick={handleReview}
                  disabled={saving}
                  className="btn-primary flex-1"
                >
                  {saving ? 'Saving…' : 'Mark as reviewed'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
