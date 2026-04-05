import { useState, useEffect } from 'react'

export default function WeeklyNarrative() {
  const [weekly, setWeekly] = useState(null)

  useEffect(() => {
    fetch('/data/stories.json')
      .then(r => r.json())
      .then(data => {
        const weeklies = (data.stories || []).filter(s => s.type === 'weekly')
        if (weeklies.length > 0) setWeekly(weeklies[weeklies.length - 1])
      })
      .catch(() => {})
  }, [])

  if (!weekly) return null

  return (
    <div className="sec" style={{ paddingBottom: 32 }}>
      <div style={{
        background: '#1a1d27',
        border: '0.5px solid #2a2d3a',
        borderRadius: 12,
        padding: '20px 24px',
      }}>
        <div style={{
          fontSize: 10, color: '#FFD700',
          letterSpacing: '1.5px', textTransform: 'uppercase',
          marginBottom: 12,
        }}>
          {weekly.week_label || 'Weekly Outlook'}
        </div>
        <p style={{
          fontSize: 13, color: '#888',
          lineHeight: 1.8, margin: 0,
        }}>
          {weekly.body}
        </p>
      </div>
    </div>
  )
}
