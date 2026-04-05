import { useState, useEffect } from 'react'

function AccuracyColor(pct) {
  if (pct >= 60) return '#4ade80'
  if (pct >= 40) return '#facc15'
  return '#f87171'
}

export default function ModelAccuracy() {
  const [data, setData] = useState(null)

  useEffect(() => {
    fetch('/data/accuracy.json')
      .then(r => r.json())
      .then(setData)
      .catch(() => {})
  }, [])

  if (!data) return null

  const { total_predictions, correct, accuracy_pct, by_model, calibration } = data
  const hasCalibration = total_predictions >= 10
  const color = AccuracyColor(accuracy_pct)

  const CalibRow = ({ label, bucket }) => {
    const b = calibration?.[bucket] || { predictions: 0, correct: 0 }
    const rate = b.predictions > 0 ? Math.round(b.correct / b.predictions * 100) : null
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
        <div style={{ width: 72, fontSize: 11, color: '#555', flexShrink: 0 }}>{label}</div>
        <div style={{ flex: 1, height: 4, background: '#1e2130', borderRadius: 2, overflow: 'hidden' }}>
          {rate !== null && (
            <div style={{
              height: '100%',
              width: `${rate}%`,
              background: AccuracyColor(rate),
              borderRadius: 2,
              transition: 'width 0.4s ease',
            }} />
          )}
        </div>
        <div style={{ width: 36, fontSize: 11, color: '#555', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
          {rate !== null ? `${rate}%` : '—'}
        </div>
        <div style={{ width: 28, fontSize: 10, color: '#444', textAlign: 'right' }}>
          {b.predictions > 0 ? `${b.correct}/${b.predictions}` : ''}
        </div>
      </div>
    )
  }

  return (
    <div className="sec" style={{ paddingTop: 8, paddingBottom: 48 }}>
      <div style={{
        background: '#1a1d27',
        border: '0.5px solid #2a2d3a',
        borderRadius: 12,
        padding: '20px 24px',
      }}>

        {/* Header */}
        <div style={{ fontSize: 11, color: '#FFD700', letterSpacing: '2px', textTransform: 'uppercase', marginBottom: 20 }}>
          Model Accuracy · IPL 2026
        </div>

        {/* Main stat */}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 6 }}>
          <div style={{ fontSize: 24, fontWeight: 600, color, fontVariantNumeric: 'tabular-nums' }}>
            {accuracy_pct.toFixed(1)}%
          </div>
          <div style={{ fontSize: 13, color: '#555' }}>
            ({correct}/{total_predictions} correct)
          </div>
        </div>

        {/* Progress bar */}
        <div style={{ height: 4, background: '#0d0f16', borderRadius: 2, overflow: 'hidden', marginBottom: 20 }}>
          <div style={{
            height: '100%',
            width: `${accuracy_pct}%`,
            background: color,
            borderRadius: 2,
            transition: 'width 0.4s ease',
          }} />
        </div>

        {/* Per-model */}
        <div style={{ display: 'flex', gap: 20, marginBottom: 24 }}>
          {['elo', 'form'].map(m => {
            const bm = by_model?.[m] || { correct: 0, total: 0 }
            const mpct = bm.total > 0 ? Math.round(bm.correct / bm.total * 100) : 0
            return (
              <div key={m} style={{ fontSize: 12 }}>
                <span style={{ color: '#555', textTransform: 'capitalize' }}>{m} model: </span>
                <span style={{ color: AccuracyColor(mpct), fontVariantNumeric: 'tabular-nums' }}>
                  {bm.correct}/{bm.total} {bm.total > 0 ? '✓' : ''}
                </span>
              </div>
            )
          })}
        </div>

        {/* Calibration */}
        <div style={{ borderTop: '0.5px solid #1e2130', paddingTop: 16 }}>
          <div style={{ fontSize: 11, color: '#555', marginBottom: 12 }}>
            {hasCalibration
              ? 'When model says X%, teams actually win:'
              : `Calibration unlocks after 10 matches · ${10 - total_predictions} to go`}
          </div>
          {hasCalibration ? (
            <>
              <CalibRow label="50–60%" bucket="50_60" />
              <CalibRow label="60–70%" bucket="60_70" />
              <CalibRow label="70–80%" bucket="70_80" />
              <CalibRow label="80%+"   bucket="80_plus" />
            </>
          ) : (
            <div style={{
              height: 4, background: '#1e2130', borderRadius: 2,
              position: 'relative', overflow: 'hidden',
            }}>
              <div style={{
                height: '100%',
                width: `${(total_predictions / 10) * 100}%`,
                background: '#2a2d3a',
                borderRadius: 2,
              }} />
            </div>
          )}
        </div>

      </div>
    </div>
  )
}
