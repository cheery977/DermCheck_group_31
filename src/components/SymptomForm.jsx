/**
 * Short symptom questionnaire — feeds into the backend's NLP-style
 * risk adjustment alongside the CNN prediction.
 */

const questions = [
  {
    key: 'duration_weeks',
    label: 'How long have you had this?',
    type: 'select',
    options: [
      { value: '',   label: 'Select…' },
      { value: '1',  label: 'Less than a week' },
      { value: '3',  label: '1–4 weeks' },
      { value: '8',  label: '1–2 months' },
      { value: '20', label: 'More than 2 months' },
    ],
  },
  {
    key: 'growing',
    label: 'Has it changed in size or shape recently?',
    type: 'yesno',
  },
  {
    key: 'bleeding',
    label: 'Does it bleed or crust over?',
    type: 'yesno',
  },
  {
    key: 'irregular_border',
    label: 'Does it have an irregular or uneven border?',
    type: 'yesno',
  },
  {
    key: 'family_history',
    label: 'Any family history of skin cancer?',
    type: 'yesno',
  },
]

export default function SymptomForm({ values, onChange }) {
  const handleChange = (key, value) => {
    onChange({ ...values, [key]: value })
  }

  return (
    <div className="space-y-4">
      {questions.map((q) => (
        <div key={q.key}>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            {q.label}
          </label>

          {q.type === 'select' && (
            <select
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={values[q.key] || ''}
              onChange={(e) => handleChange(q.key, e.target.value)}
            >
              {q.options.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          )}

          {q.type === 'yesno' && (
            <div className="flex gap-3">
              {['yes', 'no', 'unsure'].map((opt) => (
                <button
                  key={opt}
                  type="button"
                  onClick={() => handleChange(q.key, opt)}
                  className={`flex-1 py-1.5 rounded-lg border text-sm font-medium transition-colors capitalize ${
                    values[q.key] === opt
                      ? 'bg-blue-600 border-blue-600 text-white'
                      : 'border-slate-300 text-slate-600 hover:border-blue-400'
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
