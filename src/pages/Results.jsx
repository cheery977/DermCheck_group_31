import { useEffect, useState } from 'react'
import { useParams, useLocation, Link } from 'react-router-dom'
import { CheckCircle, AlertTriangle, AlertOctagon, ArrowRight, Info } from 'lucide-react'
import axios from 'axios'
import RiskBadge from '../components/RiskBadge'
import Disclaimer from '../components/Disclaimer'

const CONDITION_INFO = {
  mel:   { full: 'Melanoma', desc: 'A type of skin cancer that develops from melanocytes. Early detection is critical.' },
  bcc:   { full: 'Basal Cell Carcinoma', desc: 'The most common type of skin cancer, usually growing slowly in sun-exposed areas.' },
  akiec: { full: 'Actinic Keratosis', desc: 'Rough, scaly patches caused by years of sun exposure. Can progress to cancer if untreated.' },
  bkl:   { full: 'Benign Keratosis', desc: 'Non-cancerous skin growths including seborrhoeic keratoses and solar lentigines.' },
  nv:    { full: 'Melanocytic Nevus', desc: 'A common benign mole. Most are harmless, but changes in appearance warrant monitoring.' },
  df:    { full: 'Dermatofibroma', desc: 'A benign skin growth, often appearing as a small, firm bump. Rarely requires treatment.' },
  vasc:  { full: 'Vascular Lesion', desc: 'Includes haemangiomas and other blood vessel abnormalities. Usually benign.' },
}

const RiskIcon = ({ level }) => {
  if (level === 'HIGH')   return <AlertOctagon size={28} className="text-red-500" />
  if (level === 'MEDIUM') return <AlertTriangle size={28} className="text-amber-500" />
  return <CheckCircle size={28} className="text-green-500" />
}

export default function Results() {
  const { id } = useParams()
  const { state } = useLocation()
  const [data, setData] = useState(state || null)
  const [loading, setLoading] = useState(!state)

  useEffect(() => {
    if (!state) {
      axios.get(`/api/diagnosis/case/${id}`)
        .then((r) => setData(r.data))
        .catch(() => setData(null))
        .finally(() => setLoading(false))
    }
  }, [id, state])

  if (loading) return <div className="text-center py-20 text-slate-500">Loading results…</div>
  if (!data)   return <div className="text-center py-20 text-slate-500">Case not found.</div>

  const condInfo = CONDITION_INFO[data.condition] || { full: data.condition_display, desc: '' }
  const confidencePct = Math.round((data.confidence || 0) * 100)

  return (
    <div className="max-w-2xl mx-auto px-4 py-10 space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">Your Results</h1>

      {/* Primary result card */}
      <div className={`card border-l-4 ${
        data.risk_level === 'HIGH' ? 'border-l-red-500' :
        data.risk_level === 'MEDIUM' ? 'border-l-amber-500' :
        'border-l-green-500'
      }`}>
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <RiskIcon level={data.risk_level} />
              <h2 className="text-xl font-bold text-slate-900">{condInfo.full}</h2>
            </div>
            <p className="text-sm text-slate-500">{condInfo.desc}</p>
          </div>
          <RiskBadge level={data.risk_level} large />
        </div>

        {/* Confidence bar */}
        <div className="mt-4">
          <div className="flex justify-between text-xs text-slate-500 mb-1">
            <span>Confidence</span>
            <span className="font-medium">{confidencePct}%</span>
          </div>
          <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                data.risk_level === 'HIGH' ? 'bg-red-500' :
                data.risk_level === 'MEDIUM' ? 'bg-amber-500' : 'bg-green-500'
              }`}
              style={{ width: `${confidencePct}%` }}
            />
          </div>
        </div>
      </div>

      {/* Recommendation */}
      <div className="card space-y-2">
        <h3 className="font-semibold text-slate-800 flex items-center gap-2">
          <Info size={16} className="text-blue-600" /> What to do next
        </h3>
        <p className="text-sm text-slate-600 leading-relaxed">{data.recommendation}</p>

        {data.submitted_to_portal && (
          <div className="mt-3 bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 text-sm text-blue-800">
            Your case has been automatically submitted to the professional review portal.
            A clinician will be able to view your image and this report.
          </div>
        )}
      </div>

      {/* Images side by side */}
      {(data.image_filename || data.gradcam_filename) && (
        <div className="card space-y-3">
          <h3 className="font-semibold text-slate-800">Image Analysis</h3>
          <div className="grid grid-cols-2 gap-4">
            {data.image_filename && (
              <div className="space-y-1">
                <p className="text-xs text-slate-500 text-center">Original</p>
                <img
                  src={`/uploads/${data.image_filename}`}
                  alt="Original"
                  className="w-full rounded-lg border border-slate-200"
                />
              </div>
            )}
            {data.gradcam_filename && (
              <div className="space-y-1">
                <p className="text-xs text-slate-500 text-center">Grad-CAM heatmap</p>
                <img
                  src={`/uploads/${data.gradcam_filename}`}
                  alt="Grad-CAM"
                  className="w-full rounded-lg border border-slate-200"
                />
              </div>
            )}
          </div>
          {data.gradcam_filename && (
            <p className="text-xs text-slate-400">
              The heatmap highlights regions the model weighted most heavily in its prediction.
              Warmer colours (red/yellow) indicate higher influence.
            </p>
          )}
        </div>
      )}

      {/* Other top predictions */}
      {data.top_predictions && data.top_predictions.length > 1 && (
        <div className="card space-y-3">
          <h3 className="font-semibold text-slate-800">Other possibilities considered</h3>
          <div className="space-y-2">
            {data.top_predictions.slice(1).map((p) => (
              <div key={p.condition} className="flex items-center gap-3">
                <span className="text-sm text-slate-600 w-44 truncate">{p.condition_display}</span>
                <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-slate-400 rounded-full" style={{ width: `${p.probability}%` }} />
                </div>
                <span className="text-xs text-slate-400 w-10 text-right">{p.probability}%</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <Disclaimer compact />

      <div className="flex justify-between">
        <Link to="/analyse" className="btn-secondary">Analyse another</Link>
        {data.risk_level !== 'LOW' && (
          <Link to="/portal" className="btn-primary flex items-center gap-1">
            View professional portal <ArrowRight size={14} />
          </Link>
        )}
      </div>
    </div>
  )
}
