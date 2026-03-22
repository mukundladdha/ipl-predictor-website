export default function BottomMetaStrip({ matchesPlayed, matchesRemaining, playoffSpots }) {
  const stats = [
    { value: matchesPlayed,   label: 'matches played'   },
    { value: matchesRemaining, label: 'remaining'        },
    { value: playoffSpots,    label: 'playoff spots'     },
  ]

  return (
    <div style={{ borderTop: '0.5px solid #1e2130' }}>
      <div className="sec" style={{
        paddingTop: 16,
        paddingBottom: 16,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <div style={{ display: 'flex', gap: 32 }}>
          {stats.map(s => (
            <div key={s.label}>
              <div style={{ fontSize: 18, fontWeight: 500, color: '#fff', lineHeight: 1.2 }}>
                {s.value}
              </div>
              <div style={{ fontSize: 10, color: '#888', marginTop: 2 }}>{s.label}</div>
            </div>
          ))}
        </div>
        <div style={{ fontSize: 11, color: '#888' }}>100,000 simulations</div>
      </div>
    </div>
  )
}
