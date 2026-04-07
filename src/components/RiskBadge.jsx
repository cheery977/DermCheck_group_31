const config = {
  HIGH: {
    label: 'High Risk',
    classes: 'bg-red-100 text-red-700 border-red-200',
    dot: 'bg-red-500',
  },
  MEDIUM: {
    label: 'Medium Risk',
    classes: 'bg-amber-100 text-amber-700 border-amber-200',
    dot: 'bg-amber-500',
  },
  LOW: {
    label: 'Low Risk',
    classes: 'bg-green-100 text-green-700 border-green-200',
    dot: 'bg-green-500',
  },
}

export default function RiskBadge({ level, large = false }) {
  const cfg = config[level] || config.LOW
  const sizeClasses = large
    ? 'text-base px-3 py-1.5 rounded-lg gap-2'
    : 'text-xs px-2 py-0.5 rounded-full gap-1.5'

  return (
    <span className={`inline-flex items-center border font-medium ${cfg.classes} ${sizeClasses}`}>
      <span className={`rounded-full shrink-0 ${cfg.dot} ${large ? 'w-2.5 h-2.5' : 'w-1.5 h-1.5'}`} />
      {cfg.label}
    </span>
  )
}
