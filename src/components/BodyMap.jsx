/**
 * Clickable SVG body map — user taps a region to indicate where the
 * skin concern is located. Returns a human-readable location string.
 */

const regions = [
  { id: 'head',          label: 'Head / Face',     d: 'M50,8 a18,18 0 1,1 0,0.01Z', cx: 50, cy: 18, r: 14 },
  { id: 'neck',          label: 'Neck',             cx: 50, cy: 38, r: 6 },
  { id: 'chest',         label: 'Chest',            cx: 50, cy: 58, r: 14 },
  { id: 'left_arm',      label: 'Left Arm',         cx: 24, cy: 62, r: 9 },
  { id: 'right_arm',     label: 'Right Arm',        cx: 76, cy: 62, r: 9 },
  { id: 'abdomen',       label: 'Abdomen',          cx: 50, cy: 80, r: 12 },
  { id: 'left_hand',     label: 'Left Hand',        cx: 16, cy: 86, r: 6 },
  { id: 'right_hand',    label: 'Right Hand',       cx: 84, cy: 86, r: 6 },
  { id: 'left_leg',      label: 'Left Leg',         cx: 38, cy: 108, r: 10 },
  { id: 'right_leg',     label: 'Right Leg',        cx: 62, cy: 108, r: 10 },
  { id: 'left_foot',     label: 'Left Foot',        cx: 34, cy: 130, r: 7 },
  { id: 'right_foot',    label: 'Right Foot',       cx: 66, cy: 130, r: 7 },
]

export default function BodyMap({ selected, onChange }) {
  return (
    <div className="flex flex-col items-center gap-2">
      <p className="text-sm text-slate-500 mb-1">Tap the affected area (optional)</p>
      <svg
        viewBox="0 0 100 145"
        className="w-36 select-none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {regions.map((r) => {
          const isSelected = selected === r.id
          return (
            <circle
              key={r.id}
              cx={r.cx}
              cy={r.cy}
              r={r.r}
              onClick={() => onChange(isSelected ? '' : r.id)}
              className="cursor-pointer transition-colors"
              fill={isSelected ? '#2563eb' : '#cbd5e1'}
              stroke={isSelected ? '#1d4ed8' : '#94a3b8'}
              strokeWidth="1"
            />
          )
        })}
      </svg>

      {selected && (
        <p className="text-sm font-medium text-blue-700">
          {regions.find((r) => r.id === selected)?.label}
        </p>
      )}
      {!selected && (
        <p className="text-sm text-slate-400">No location selected</p>
      )}
    </div>
  )
}

export function locationLabel(id) {
  return regions.find((r) => r.id === id)?.label || id
}
