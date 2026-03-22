export default function Hero({ teamCount = 10 }) {
  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '60px 24px 44px' }}>
      <h1 style={{
        fontSize: 32,
        fontWeight: 500,
        letterSpacing: '-1px',
        lineHeight: 1.15,
        color: '#fff',
        margin: '0 0 18px',
      }}>
        4 spots.<br />
        <span style={{ color: '#FFD700' }}>{teamCount} teams.</span><br />
        Who survives?
      </h1>
      <p style={{
        fontSize: 13,
        color: '#555',
        lineHeight: 1.7,
        maxWidth: 520,
        margin: 0,
      }}>
        Every match day we simulate the rest of the season 100,000 times and
        calculate each team's true playoff probability. Here's where things stand.
      </p>
    </div>
  )
}
