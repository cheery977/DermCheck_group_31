import { Link, useLocation } from 'react-router-dom'
import { Activity } from 'lucide-react'

export default function Navbar() {
  const { pathname } = useLocation()

  const links = [
    { to: '/',        label: 'Home' },
    { to: '/analyse', label: 'Analyse' },
    { to: '/portal',  label: 'Professional Portal' },
  ]

  return (
    <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 font-semibold text-blue-600 text-lg">
          <Activity size={20} />
          DermCheck
        </Link>

        <div className="flex gap-1">
          {links.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                pathname === to
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              {label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  )
}
