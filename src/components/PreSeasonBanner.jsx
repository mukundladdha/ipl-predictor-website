export default function PreSeasonBanner({ modelNote }) {
  return (
    <div style={{
      background: '#1a1d27',
      borderBottom: '0.5px solid #2a2d3a',
    }}>
      <div className="sec" style={{
        padding: '10px 0',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
      }}>
        {/* Left: live indicator + label */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
          <div style={{
            width: 6,
            height: 6,
            borderRadius: '50%',
            background: '#FFD700',
            flexShrink: 0,
          }} />
          <span style={{
            fontSize: 12,
            color: '#FFD700',
            fontWeight: 500,
            whiteSpace: 'nowrap',
          }}>
            IPL 2026 opens today · Pre-season forecast
          </span>
        </div>

        {/* Right: model note */}
        {modelNote && (
          <div style={{
            marginLeft: 'auto',
            fontSize: 11,
            color: '#666',
            maxWidth: 500,
            textAlign: 'right',
            lineHeight: 1.5,
          }}>
            {modelNote}
          </div>
        )}
      </div>
    </div>
  )
}
