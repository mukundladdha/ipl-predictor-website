import { useState } from 'react'

function pctColor(pct) {
  if (pct >= 60) return '#4ade80'
  if (pct >= 30) return '#facc15'
  return '#f87171'
}

function getDelta(team, model) {
  const hist = team.history?.[model] ?? []
  const current = team.models[model]?.playoff_pct ?? 0
  if (hist.length < 2) return null
  return current - hist[hist.length - 2]
}

function getHeadlineData(teams, model) {
  // Priority 1: big drop (pct < 30 AND delta <= -6)
  const dropper = teams.find(t => {
    const pct = t.models[model]?.playoff_pct ?? 0
    const delta = getDelta(t, model)
    return pct < 30 && delta !== null && delta <= -6
  })
  if (dropper) {
    const d = getDelta(dropper, model)
    const pct = dropper.models[model].playoff_pct
    return {
      headline: `${dropper.name} just fell off a cliff.`,
      sub: `Their playoff probability dropped ${Math.abs(d)}% after the last match. Our model now gives them just ${pct}% — here's where all 10 teams stand.`,
    }
  }

  // Priority 2: biggest riser >= 6
  let bestTeam = null
  let bestDelta = 5
  teams.forEach(t => {
    const d = getDelta(t, model)
    if (d !== null && d > bestDelta) {
      bestDelta = d
      bestTeam = t
    }
  })
  if (bestTeam) {
    return {
      headline: `${bestTeam.name} are pulling away.`,
      sub: `Up ${bestDelta}% after the last result. The gap between the top 4 and the rest is widening — here's what the model says.`,
    }
  }

  // Priority 3: fallback
  return {
    headline: '4 spots.',
    headlineEm: 'No team is safe.',
    sub: "The race is tighter than the points table suggests. We simulate the remaining season 100,000 times so you don't have to guess.",
  }
}

export default function Hero({
  teams = [],
  matchesPlayed = 0,
  matchesRemaining = 0,
  playoffSpots = 4,
}) {
  const [model, setModel] = useState('elo')

  const sorted = [...teams].sort(
    (a, b) => (b.models[model]?.playoff_pct ?? 0) - (a.models[model]?.playoff_pct ?? 0)
  )
  const top4 = sorted.slice(0, 4)
  const { headline, headlineEm, sub } = getHeadlineData(teams, model)

  return (
    <div className="sec" style={{ paddingTop: 20, paddingBottom: 0 }}>
      <div style={{
        border: '0.5px solid #2a2d3a',
        borderRadius: 14,
        overflow: 'hidden',
      }}>

        {/* ── Section 1: hero-top ── */}
        <div className="hero-top">
          {/* Live pill */}
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 7,
            background: '#1a1d27',
            border: '0.5px solid #2a2d3a',
            borderRadius: 20,
            padding: '5px 14px',
            marginBottom: 20,
          }}>
            <span className="pulse-dot" />
            <span style={{ fontSize: 10, color: '#888', letterSpacing: '0.8px', textTransform: 'uppercase' }}>
              Updated today · 100,000 simulations
            </span>
          </div>

          {/* Dynamic headline */}
          <h1 className="hero-h1" style={{
            fontWeight: 500,
            letterSpacing: '-1px',
            lineHeight: 1.15,
            color: '#fff',
            margin: '0 0 12px',
          }}>
            {headlineEm ? (
              <>
                {headline}<br />
                <em style={{ color: '#FFD700', fontStyle: 'normal' }}>{headlineEm}</em>
              </>
            ) : headline}
          </h1>

          {/* Dynamic subtext */}
          <p style={{ fontSize: 13, color: '#777', lineHeight: 1.75, maxWidth: 580, margin: 0 }}>
            {sub}
          </p>
        </div>

        {/* ── Section 2: hero-cards ── */}
        <div className="hero-cards" style={{ borderTop: '0.5px solid #1e2130' }}>
          {top4.map((team, i) => {
            const pct = team.models[model]?.playoff_pct ?? 0
            const delta = getDelta(team, model)
            const hist = team.history?.[model] ?? []

            let deltaText, deltaColor
            if (hist.length < 2) {
              deltaText = '— first match day'
              deltaColor = '#444'
            } else if (delta > 0) {
              deltaText = `↑ ${delta}% since last match`
              deltaColor = '#4ade80'
            } else if (delta < 0) {
              deltaText = `↓ ${Math.abs(delta)}% since last match`
              deltaColor = '#f87171'
            } else {
              deltaText = '— no change'
              deltaColor = '#444'
            }

            return (
              <div
                key={team.short}
                className="hero-card"
                style={{ padding: '20px 24px', cursor: 'default', transition: 'background 0.15s' }}
                onMouseEnter={e => e.currentTarget.style.background = '#1a1d27'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 10 }}>
                  <div style={{
                    width: 10, height: 10, borderRadius: '50%',
                    background: team.color, flexShrink: 0,
                  }} />
                  <span style={{ fontSize: 11, color: '#666' }}>{team.name}</span>
                </div>
                <div style={{ fontSize: 26, fontWeight: 500, color: pctColor(pct), marginBottom: 6 }}>
                  {pct}%
                </div>
                <div style={{ fontSize: 10, color: '#444', marginBottom: 4 }}>
                  Rank #{i + 1} · Playoff odds
                </div>
                <div style={{ fontSize: 11, color: deltaColor }}>
                  {deltaText}
                </div>
              </div>
            )
          })}
        </div>

        {/* ── Section 3: hero-footer ── */}
        <div className="hero-footer-pad" style={{
          background: '#0d0f16',
          borderTop: '0.5px solid #1e2130',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          {/* Meta stats */}
          <div style={{ display: 'flex', gap: 28 }}>
            {[
              { value: matchesPlayed,    label: 'Played' },
              { value: matchesRemaining, label: 'Remaining' },
              { value: playoffSpots,     label: 'Playoff spots' },
            ].map(({ value, label }) => (
              <div key={label}>
                <div style={{ fontSize: 15, fontWeight: 500, color: '#fff' }}>{value}</div>
                <div style={{ fontSize: 10, color: '#444', marginTop: 1 }}>{label}</div>
              </div>
            ))}
          </div>

          {/* Model toggle */}
          <div style={{ display: 'flex', gap: 6 }}>
            {['elo', 'form'].map(m => {
              const active = model === m
              return (
                <button
                  key={m}
                  onClick={() => setModel(m)}
                  style={{
                    padding: '4px 14px',
                    borderRadius: 20,
                    border: `1px solid ${active ? '#FFD700' : '#2a2d3a'}`,
                    background: active ? 'rgba(255,215,0,0.06)' : 'transparent',
                    color: active ? '#FFD700' : '#555',
                    fontSize: 11,
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                >
                  {m === 'elo' ? 'Elo' : 'Form'}
                </button>
              )
            })}
          </div>

          {/* Scroll CTA */}
          <div style={{ fontSize: 11, color: '#333' }}>
            Scroll to explore all 10 teams ↓
          </div>
        </div>

      </div>
    </div>
  )
}
