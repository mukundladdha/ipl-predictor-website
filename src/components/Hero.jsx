export default function Hero({ teamCount = 10 }) {
  return (
    <div className="sec" style={{ paddingTop: 64, paddingBottom: 48 }}>
      <h1 style={{
        fontSize: 44,
        fontWeight: 500,
        letterSpacing: '-1.5px',
        lineHeight: 1.1,
        color: '#fff',
        margin: '0 0 18px',
      }}>
        4 spots.<br />
        <span style={{ color: '#FFD700' }}>{teamCount} teams.</span><br />
        Who survives?
      </h1>
      <p style={{
        fontSize: 15,
        color: '#bbb',
        lineHeight: 1.75,
        maxWidth: 520,
        margin: 0,
      }}>
        Every match day we simulate the rest of the season 100,000 times and
        calculate each team's true playoff probability. Here's where things stand.
      </p>
    </div>
  )
}
