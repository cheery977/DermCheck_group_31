import { Link } from 'react-router-dom'
import { Camera, ShieldCheck, Users, Zap } from 'lucide-react'
import Disclaimer from '../components/Disclaimer'

const features = [
  {
    icon: <Camera size={22} className="text-blue-600" />,
    title: 'Photo Analysis',
    desc: 'Upload or take a photo and our AI model will identify potential skin conditions in seconds.',
  },
  {
    icon: <Zap size={22} className="text-blue-600" />,
    title: 'Instant Insights',
    desc: 'Get a confidence-rated diagnosis with a Grad-CAM heatmap showing exactly what the model focused on.',
  },
  {
    icon: <ShieldCheck size={22} className="text-blue-600" />,
    title: 'Safe Triage',
    desc: 'High-risk findings are automatically flagged and sent to the professional portal for clinician review.',
  },
  {
    icon: <Users size={22} className="text-blue-600" />,
    title: 'Professional Portal',
    desc: 'Clinicians can review submitted cases, add notes, and manage their patient queue in one place.',
  },
]

export default function Home() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-12 space-y-14">
      {/* Hero */}
      <div className="text-center space-y-4">
        <span className="inline-block bg-blue-50 text-blue-700 text-xs font-semibold px-3 py-1 rounded-full uppercase tracking-wide">
          Digital Health · AI-Powered
        </span>
        <h1 className="text-4xl font-bold text-slate-900 leading-tight">
          Skin condition analysis,<br />
          <span className="text-blue-600">wherever you are</span>
        </h1>
        <p className="text-slate-500 text-lg max-w-xl mx-auto">
          DermCheck uses a machine learning model trained on over 10,000 clinical
          images to help you understand skin concerns and decide when to see a professional.
        </p>
        <Link to="/analyse" className="btn-primary inline-block mt-2 text-base px-8 py-3 rounded-xl">
          Analyse a skin concern
        </Link>
      </div>

      {/* Disclaimer */}
      <Disclaimer />

      {/* Features */}
      <div>
        <h2 className="text-xl font-semibold text-slate-800 mb-6 text-center">How it works</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {features.map((f) => (
            <div key={f.title} className="card flex gap-4">
              <div className="mt-0.5">{f.icon}</div>
              <div>
                <h3 className="font-semibold text-slate-800 mb-1">{f.title}</h3>
                <p className="text-sm text-slate-500">{f.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tech callout */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl p-8 text-white text-center space-y-3">
        <h2 className="text-xl font-bold">Built on real clinical data</h2>
        <p className="text-blue-100 text-sm max-w-lg mx-auto">
          Our model is trained on the HAM10000 dataset — 10,015 dermoscopic images
          across 7 diagnostic categories, sourced from the International Skin Imaging
          Collaboration (ISIC) archive.
        </p>
        <p className="text-xs text-blue-200">
          EfficientNet-B0 · Transfer learning · Grad-CAM explainability · Weighted class sampling
        </p>
      </div>
    </div>
  )
}
