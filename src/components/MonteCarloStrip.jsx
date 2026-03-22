export default function MonteCarloStrip() {
  return (
    <div style={{
      background: '#13151e',
      borderTop: '0.5px solid #1e2130',
      borderBottom: '0.5px solid #1e2130',
    }}>
      <div className="sec" style={{
        paddingTop: 14,
        paddingBottom: 14,
        display: 'flex',
        gap: 14,
        alignItems: 'flex-start',
      }}>
        <span style={{ fontSize: 18, flexShrink: 0, lineHeight: 1.6 }}>🎲</span>
        <p style={{ fontSize: 11, color: '#888', lineHeight: 1.7, margin: 0 }}>
          <strong style={{ color: '#999' }}>Both models use Monte Carlo simulation</strong>
          {' '}— we play out the remaining fixtures 100,000 times, each time sampling from
          the win probabilities each model produces. The % you see is how often each team
          finished in the top 4 across all 100,000 seasons.
        </p>
      </div>
    </div>
  )
}
