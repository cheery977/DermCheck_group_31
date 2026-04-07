import { AlertTriangle } from 'lucide-react'

export default function Disclaimer({ compact = false }) {
  if (compact) {
    return (
      <p className="text-xs text-slate-500 text-center">
        For informational purposes only — not a substitute for professional medical advice.
      </p>
    )
  }

  return (
    <div className="flex gap-3 bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-800">
      <AlertTriangle size={18} className="shrink-0 mt-0.5 text-amber-500" />
      <div>
        <span className="font-semibold">Important: </span>
        DermCheck uses AI to provide general information only. It is not a medical device and
        cannot replace a diagnosis from a qualified dermatologist or GP. If you are concerned
        about any skin condition, please seek professional advice promptly.
      </div>
    </div>
  )
}
