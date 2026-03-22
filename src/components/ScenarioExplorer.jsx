import { useState, useEffect } from 'react'
import { useModel } from '../context/ModelContext'

export default function ScenarioExplorer({ teams }) {
  const { setScenarioOverrides } = useModel()
  const [fixtures, setFixtures] = useState([])
  // picks[i] = winning team short, or undefined if no pick for fixture i
  const [picks, setPicks] = useState({})

  useEffect(() => {
    fetch('/data/fixtures.json')
      .then(r => r.json())
      .then(d => setFixtures(d.fixtures ?? []))
      .catch(() => {})
  }, [])

  // Recompute context overrides whenever picks change
  useEffect(() => {
    const overrides = {}
    fixtures.forEach((_, i) => {
      const winner = picks[i]
      if (winner) overrides[winner] = (overrides[winner] ?? 0) + 2
    })
    setScenarioOverrides(overrides)
  }, [picks, fixtures, setScenarioOverrides])

  function togglePick(fixtureIdx, teamShort) {
    setPicks(prev => {
      if (prev[fixtureIdx] === teamShort) {
        const next = { ...prev }
        delete next[fixtureIdx]
        return next
      }
      return { ...prev, [fixtureIdx]: teamShort }
    })
  }

  function reset() {
    setPicks({})
  }

  const teamByShort = Object.fromEntries(teams.map(t => [t.short, t]))
  const hasAnyPick = Object.keys(picks).length > 0

  if (!fixtures.length) return null

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '40px 24px' }}>
      <div style={{
        fontSize: 11,
        color: '#FFD700',
        letterSpacing: '1.5px',
        textTransform: 'uppercase',
        marginBottom: 8,
      }}>
        What if?
      </div>
      <p style={{ fontSize: 12, color: '#444', lineHeight: 1.7, margin: '0 0 20px' }}>
        Toggle match outcomes below and see how playoff odds shift.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {fixtures.map((fix, i) => {
          const t1 = teamByShort[fix.team1]
          const t2 = teamByShort[fix.team2]
          const winner = picks[i]

          const btnStyle = (short, meta) => ({
            flex: 1,
            padding: '8px 12px',
            borderRadius: 8,
            border: 'none',
            background: winner === short ? (meta?.color ?? '#FFD700') : '#13151e',
            color: winner === short
              ? (meta?.textDark ? '#111' : '#fff')
              : (winner && winner !== short) ? '#333' : '#555',
            fontSize: 13,
            fontWeight: 500,
            cursor: 'pointer',
            transition: 'all 0.15s',
            opacity: (winner && winner !== short) ? 0.5 : 1,
          })

          return (
            <div
              key={`${fix.team1}-${fix.team2}`}
              style={{
                background: '#1a1d27',
                border: '0.5px solid #2a2d3a',
                borderRadius: 12,
                padding: '14px 16px',
              }}
            >
              <div style={{ fontSize: 12, color: '#444', marginBottom: 10 }}>
                {fix.date} · {fix.venue}
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button onClick={() => togglePick(i, fix.team1)} style={btnStyle(fix.team1, t1)}>
                  {fix.team1}
                </button>
                <button onClick={() => togglePick(i, fix.team2)} style={btnStyle(fix.team2, t2)}>
                  {fix.team2}
                </button>
              </div>
            </div>
          )
        })}
      </div>

      {hasAnyPick && (
        <button
          onClick={reset}
          style={{
            marginTop: 16,
            padding: '7px 20px',
            borderRadius: 20,
            border: '0.5px solid #2a2d3a',
            background: 'transparent',
            color: '#555',
            fontSize: 12,
            cursor: 'pointer',
          }}
        >
          ↺ Reset
        </button>
      )}
    </div>
  )
}
