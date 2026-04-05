import { useState, useEffect } from 'react'

export default function PlayerLeaderboard() {
  const [data, setData]   = useState(null)
  const [tab, setTab]     = useState('orange') // 'orange' | 'purple'
  const [mobile, setMobile] = useState(window.innerWidth <= 768)

  useEffect(() => {
    fetch('/data/player_stats.json')
      .then(r => r.json())
      .then(setData)
      .catch(() => {})
    const onResize = () => setMobile(window.innerWidth <= 768)
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  if (!data) return null

  const rows = tab === 'orange'
    ? data.leaderboards.orange_cap
    : data.leaderboards.purple_cap

  const tabBtn = (id, label) => {
    const active = tab === id
    return (
      <button
        key={id}
        onClick={() => setTab(id)}
        style={{
          padding: '5px 16px', borderRadius: 20,
          border: `1px solid ${active ? '#FFD700' : '#2a2d3a'}`,
          background: active ? 'rgba(255,215,0,0.06)' : 'transparent',
          color: active ? '#FFD700' : '#aaa',
          fontSize: 12, fontWeight: active ? 500 : 400,
          cursor: 'pointer', transition: 'all 0.2s',
        }}
      >
        {label}
      </button>
    )
  }

  const cellStyle = (first) => ({
    padding: '10px 12px',
    borderBottom: '0.5px solid #1e2130',
    fontSize: 13,
    color: first ? '#fff' : '#aaa',
    fontWeight: first ? 500 : 400,
    fontVariantNumeric: 'tabular-nums',
    whiteSpace: 'nowrap',
  })

  return (
    <div className="sec" style={{ paddingTop: 40, paddingBottom: 48 }}>

      {/* Header */}
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom: 24 }}>
        <div style={{ fontSize: 11, color: '#FFD700', letterSpacing: '2px', textTransform: 'uppercase' }}>
          Season Stats
        </div>
        <div style={{ display:'flex', gap: 6 }}>
          {tabBtn('orange', '🧡 Orange Cap')}
          {tabBtn('purple', '💜 Purple Cap')}
        </div>
      </div>

      {/* Table */}
      <div style={{
        background: '#1a1d27',
        border: '0.5px solid #2a2d3a',
        borderRadius: 12,
        overflow: 'hidden',
      }}>

        {/* Table header */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: tab === 'orange'
            ? (mobile ? '32px 1fr 56px 48px' : '32px 1fr 56px 56px 56px 48px')
            : (mobile ? '32px 1fr 48px 52px' : '32px 1fr 48px 56px 60px 48px'),
          padding: '10px 12px',
          borderBottom: '0.5px solid #2a2d3a',
        }}>
          {(tab === 'orange'
            ? ['#', 'Player', 'Runs', ...(mobile ? [] : ['Balls']), 'SR', 'M']
            : ['#', 'Player', 'Wkts', ...(mobile ? [] : ['Econ']), 'Best', 'M']
          ).map((h, i) => (
            <div key={i} style={{
              fontSize: 10, color: '#FFD700',
              textTransform: 'uppercase', letterSpacing: '1.5px',
              textAlign: i === 1 ? 'left' : 'right',
            }}>{h}</div>
          ))}
        </div>

        {/* Rows */}
        {rows.map((p, i) => {
          const isFirst = i === 0
          return (
            <div
              key={p.name}
              style={{
                display: 'grid',
                gridTemplateColumns: tab === 'orange'
                  ? (mobile ? '32px 1fr 56px 48px' : '32px 1fr 56px 56px 56px 48px')
                  : (mobile ? '32px 1fr 48px 52px' : '32px 1fr 48px 56px 60px 48px'),
                padding: '0',
                borderLeft: isFirst ? `4px solid ${p.team_color}` : '4px solid transparent',
                transition: 'background 0.15s',
                cursor: 'default',
              }}
              onMouseEnter={e => e.currentTarget.style.background = '#1e2130'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              {/* Rank */}
              <div style={{ ...cellStyle(false), textAlign: 'right', color: isFirst ? '#FFD700' : '#555' }}>
                {i + 1}
              </div>

              {/* Player name + team dot */}
              <div style={{ ...cellStyle(isFirst), display:'flex', alignItems:'center', gap: 8 }}>
                <div style={{
                  width: 7, height: 7, borderRadius: '50%',
                  background: p.team_color, flexShrink: 0,
                }} />
                <span>{p.name}</span>
                <span style={{ fontSize: 11, color: '#555', fontWeight: 400 }}>{p.team}</span>
              </div>

              {/* Stat columns */}
              {tab === 'orange' ? (
                <>
                  <div style={{ ...cellStyle(isFirst), textAlign:'right' }}>{p.runs}</div>
                  {!mobile && <div style={{ ...cellStyle(false), textAlign:'right' }}>{p.balls}</div>}
                  <div style={{ ...cellStyle(false), textAlign:'right' }}>{p.strike_rate.toFixed(1)}</div>
                  <div style={{ ...cellStyle(false), textAlign:'right' }}>{p.matches}</div>
                </>
              ) : (
                <>
                  <div style={{ ...cellStyle(isFirst), textAlign:'right' }}>{p.wickets}</div>
                  {!mobile && <div style={{ ...cellStyle(false), textAlign:'right' }}>{p.economy.toFixed(1)}</div>}
                  <div style={{ ...cellStyle(false), textAlign:'right' }}>{p.best}</div>
                  <div style={{ ...cellStyle(false), textAlign:'right' }}>{p.matches}</div>
                </>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
