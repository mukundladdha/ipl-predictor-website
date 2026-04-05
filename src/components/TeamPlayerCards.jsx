import { useState, useEffect } from 'react'

export default function TeamPlayerCards({ teamShort }) {
  const [data, setData] = useState(null)

  useEffect(() => {
    fetch('/data/player_stats.json')
      .then(r => r.json())
      .then(setData)
      .catch(() => {})
  }, [])

  if (!data) return null

  const tp = data.team_performers?.[teamShort]
  if (!tp) return null

  const cards = [
    tp.top_batter ? {
      icon: '🏏',
      label: 'Top bat',
      name: tp.top_batter.name.split(' ').slice(-1)[0],  // last name
      full: tp.top_batter.name,
      stat: `${tp.top_batter.runs}(${tp.top_batter.balls})`,
      sub:  `SR: ${tp.top_batter.sr.toFixed(0)}`,
    } : null,
    tp.top_bowler ? {
      icon: '🎳',
      label: 'Top bowl',
      name: tp.top_bowler.name.split(' ').slice(-1)[0],
      full: tp.top_bowler.name,
      stat: `${tp.top_bowler.wickets}/${tp.top_bowler.runs}`,
      sub:  `Econ: ${tp.top_bowler.econ.toFixed(1)}`,
    } : null,
    tp.biggest_impact ? {
      icon: '⚡',
      label: 'Top impact',
      name: tp.biggest_impact.name.split(' ').slice(-1)[0],
      full: tp.biggest_impact.name,
      stat: `${tp.biggest_impact.score > 0 ? '+' : ''}${tp.biggest_impact.score.toFixed(1)}`,
      sub:  'Impact score',
    } : null,
  ].filter(Boolean)

  if (cards.length === 0) return null

  return (
    <div style={{
      background: '#13151e',
      borderTop: '0.5px solid #1e2130',
      borderBottom: '0.5px solid #1e2130',
      padding: '10px 0',
    }}>
      <div className="sec">
        <div style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${cards.length}, 1fr)`,
          gap: 8,
        }}>
          {cards.map((c, i) => (
            <div key={i} style={{
              display: 'flex', flexDirection: 'column', gap: 2,
              padding: '8px 12px',
              background: 'rgba(255,255,255,0.02)',
              borderRadius: 8,
              border: '0.5px solid #1e2130',
            }}>
              <div style={{ fontSize: 10, color: '#555', letterSpacing: '0.5px' }}>
                {c.icon} {c.label}
              </div>
              <div style={{ fontSize: 13, color: '#ddd', fontWeight: 500 }}>
                {c.name}
              </div>
              <div style={{ fontSize: 12, color: '#fff', fontVariantNumeric: 'tabular-nums' }}>
                {c.stat}
              </div>
              <div style={{ fontSize: 11, color: '#555' }}>
                {c.sub}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
