import React from 'react'
import { useModel } from '../context/ModelContext'

function pctColor(pct) {
  if (pct >= 60) return '#4ade80'
  if (pct >= 30) return '#facc15'
  return '#f87171'
}

export default function PlayoffRace({ teams }) {
  const { activeModel, setActiveModel, scenarioOverrides } = useModel()

  // Apply scenario overrides and sort
  const sorted = [...teams]
    .map(t => {
      const base = t.models[activeModel]?.playoff_pct ?? 0
      const bonus = scenarioOverrides[t.short] ?? 0
      return { ...t, adjPct: Math.max(0, Math.min(100, base + bonus * 2)) }
    })
    .sort((a, b) => b.adjPct - a.adjPct)

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '40px 24px 32px' }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div style={{ fontSize: 11, color: '#FFD700', letterSpacing: '1.5px', textTransform: 'uppercase' }}>
          Playoff Race
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          {['elo', 'form'].map(m => {
            const active = activeModel === m
            return (
              <button
                key={m}
                onClick={() => setActiveModel(m)}
                style={{
                  padding: '5px 16px',
                  borderRadius: 20,
                  border: `1px solid ${active ? '#FFD700' : '#2a2d3a'}`,
                  background: active ? 'rgba(255,215,0,0.06)' : 'transparent',
                  color: active ? '#FFD700' : '#555',
                  fontSize: 12,
                  fontWeight: active ? 600 : 400,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                {m === 'elo' ? 'Elo' : 'Form'}
              </button>
            )
          })}
        </div>
      </div>

      {/* Rows */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
        {sorted.map((team, i) => (
          <React.Fragment key={team.short}>
            {/* Cutoff divider after rank 4 */}
            {i === 4 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 0' }}>
                <div style={{ flex: 1, borderTop: '1px dashed rgba(255,215,0,0.4)' }} />
                <span style={{ fontSize: 10, color: 'rgba(255,215,0,0.4)', whiteSpace: 'nowrap' }}>
                  — playoff cutoff —
                </span>
              </div>
            )}

            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              {/* Rank */}
              <div style={{ width: 18, fontSize: 11, color: '#333', textAlign: 'right', flexShrink: 0 }}>
                {i + 1}
              </div>

              {/* Short code */}
              <div style={{ width: 34, fontSize: 10, color: '#555', flexShrink: 0 }}>
                {team.short}
              </div>

              {/* Bar */}
              <div style={{
                flex: 1,
                height: 30,
                background: '#1a1d27',
                border: '0.5px solid #1e2130',
                borderRadius: 4,
                overflow: 'hidden',
                position: 'relative',
              }}>
                <div style={{
                  height: '100%',
                  width: `${team.adjPct}%`,
                  backgroundColor: team.color,
                  borderRadius: 4,
                  transition: 'width 0.4s ease',
                  display: 'flex',
                  alignItems: 'center',
                  paddingLeft: team.adjPct > 25 ? 10 : 0,
                  minWidth: team.adjPct > 0 ? 4 : 0,
                  overflow: 'hidden',
                }}>
                  {team.adjPct > 25 && (
                    <span style={{
                      fontSize: 11,
                      fontWeight: 500,
                      color: team.textDark ? '#111' : '#fff',
                      whiteSpace: 'nowrap',
                    }}>
                      {team.name}
                    </span>
                  )}
                </div>

                {/* Name outside bar for narrow bars */}
                {team.adjPct <= 25 && (
                  <span style={{
                    position: 'absolute',
                    left: `calc(${team.adjPct}% + 8px)`,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    fontSize: 11,
                    color: '#666',
                    whiteSpace: 'nowrap',
                  }}>
                    {team.name}
                  </span>
                )}
              </div>

              {/* Pct */}
              <div style={{
                width: 38,
                fontSize: 13,
                fontWeight: 600,
                color: pctColor(team.adjPct),
                textAlign: 'right',
                flexShrink: 0,
                fontVariantNumeric: 'tabular-nums',
              }}>
                {Math.round(team.adjPct)}%
              </div>
            </div>
          </React.Fragment>
        ))}
      </div>
    </div>
  )
}
