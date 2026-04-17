import { useState, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload as UploadIcon, X, ChevronRight, ChevronLeft, Loader2 } from 'lucide-react'
import axios from 'axios'
import Disclaimer from '../components/Disclaimer'
import BodyMap from '../components/BodyMap'
import SymptomForm from '../components/SymptomForm'

const STEPS = ['Upload Photo', 'Symptoms', 'Location', 'Review']

export default function Upload() {
  const navigate = useNavigate()
  const fileInputRef = useRef(null)

  const [step, setStep] = useState(0)
  const [imageFile, setImageFile] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [symptoms, setSymptoms] = useState({})
  const [bodyLocation, setBodyLocation] = useState('')
  const [dragging, setDragging] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleFile = useCallback((file) => {
    if (!file) return
    if (!file.type.startsWith('image/')) {
      setError('Please upload an image file (JPG, PNG, or WebP).')
      return
    }
    setError('')
    setImageFile(file)
    setImagePreview(URL.createObjectURL(file))
  }, [])

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }, [handleFile])

  const clearImage = useCallback(() => {
    setImageFile(null)
    setImagePreview(null)
  }, [])

  const canProceed = step === 0 ? !!imageFile : true

  const handleSubmit = async () => {
    setSubmitting(true)
    setError('')

    const form = new FormData()
    form.append('file', imageFile)
    form.append('body_location', bodyLocation)
    form.append('symptoms', JSON.stringify(symptoms))

    try {
      const { data } = await axios.post('/api/diagnosis/analyse', form)
      navigate(`/results/${data.case_id}`, { state: data })
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong. Please try again.')
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-10 space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">Analyse a skin concern</h1>

      <Disclaimer />

      {/* Step indicator */}
      <div className="flex items-center gap-2">
        {STEPS.map((label, i) => (
          <div key={i} className="flex items-center gap-2 flex-1">
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
              i < step ? 'bg-blue-600 text-white' :
              i === step ? 'bg-blue-100 text-blue-700 ring-2 ring-blue-600' :
              'bg-slate-100 text-slate-400'
            }`}>
              {i + 1}
            </div>
            <span className={`text-xs hidden sm:block ${i === step ? 'text-blue-700 font-medium' : 'text-slate-400'}`}>
              {label}
            </span>
            {i < STEPS.length - 1 && <div className="flex-1 h-px bg-slate-200" />}
          </div>
        ))}
      </div>

      {/* Step 0: Upload */}
      {step === 0 && (
        <div className="card space-y-4">
          <h2 className="font-semibold text-slate-800">Upload a photo</h2>
          <p className="text-sm text-slate-500">
            Take a clear, well-lit photo of the affected area. Avoid blurry or low-quality images
            as this will reduce accuracy.
          </p>

          {!imagePreview ? (
            <div
              onDrop={onDrop}
              onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
              onDragLeave={() => setDragging(false)}
              onClick={() => fileInputRef.current.click()}
              className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${
                dragging ? 'border-blue-500 bg-blue-50' : 'border-slate-300 hover:border-blue-400 hover:bg-slate-50'
              }`}
            >
              <UploadIcon size={32} className="mx-auto text-slate-400 mb-3" />
              <p className="text-sm font-medium text-slate-600">Drag and drop or click to upload</p>
              <p className="text-xs text-slate-400 mt-1">JPG, PNG, WebP — max 10 MB</p>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                className="hidden"
                onChange={(e) => handleFile(e.target.files[0])}
              />
            </div>
          ) : (
            <div className="relative">
              <img
                src={imagePreview}
                alt="Preview"
                className="w-full max-h-64 object-contain rounded-xl border border-slate-200 bg-slate-50"
              />
              <button
                onClick={clearImage}
                className="absolute top-2 right-2 bg-white rounded-full p-1 shadow border border-slate-200 hover:bg-red-50"
              >
                <X size={14} className="text-slate-500" />
              </button>
            </div>
          )}

          {error && <p className="text-sm text-red-600">{error}</p>}
        </div>
      )}

      {/* Step 1: Symptoms */}
      {step === 1 && (
        <div className="card space-y-4">
          <h2 className="font-semibold text-slate-800">Tell us about your symptoms</h2>
          <p className="text-sm text-slate-500">
            These answers help refine the AI's risk assessment. All fields are optional.
          </p>
          <SymptomForm values={symptoms} onChange={setSymptoms} />
        </div>
      )}

      {/* Step 2: Body location */}
      {step === 2 && (
        <div className="card">
          <h2 className="font-semibold text-slate-800 mb-4">Where is the affected area?</h2>
          <BodyMap selected={bodyLocation} onChange={setBodyLocation} />
        </div>
      )}

      {/* Step 3: Review */}
      {step === 3 && (
        <div className="card space-y-5">
          <h2 className="font-semibold text-slate-800">Review and submit</h2>

          <div className="flex gap-4 items-start">
            <img
              src={imagePreview}
              alt="Preview"
              className="w-28 h-28 object-cover rounded-lg border border-slate-200"
            />
            <div className="text-sm space-y-1 text-slate-600">
              <p><span className="font-medium">File:</span> {imageFile?.name}</p>
              <p><span className="font-medium">Location:</span> {bodyLocation || 'Not specified'}</p>
              <p><span className="font-medium">Symptoms answered:</span> {Object.keys(symptoms).length} / 5</p>
            </div>
          </div>

          <p className="text-xs text-slate-500 bg-slate-50 rounded-lg p-3">
            By submitting, you confirm this image is of your own skin and you consent to it
            being analysed by an AI model. If a high-risk condition is detected, your image
            and report will be shared with the professional review portal.
          </p>

          {error && <p className="text-sm text-red-600">{error}</p>}
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          className="btn-secondary flex items-center gap-1"
          onClick={() => setStep((s) => s - 1)}
          disabled={step === 0}
        >
          <ChevronLeft size={16} /> Back
        </button>

        {step < STEPS.length - 1 ? (
          <button
            className="btn-primary flex items-center gap-1"
            onClick={() => setStep((s) => s + 1)}
            disabled={!canProceed}
          >
            Next <ChevronRight size={16} />
          </button>
        ) : (
          <button
            className="btn-primary flex items-center gap-2"
            onClick={handleSubmit}
            disabled={submitting}
          >
            {submitting
              ? <><Loader2 size={16} className="animate-spin" /> Analysing…</>
              : 'Submit for Analysis'
            }
          </button>
        )}
      </div>
    </div>
  )
}
