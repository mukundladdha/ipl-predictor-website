export default function Footer() {
  return (
    <footer style={{ borderTop: '0.5px solid #1e2130', marginTop: 40 }}>
      <div className="sec" style={{ paddingTop: 48, paddingBottom: 56 }}>
        <p style={{ fontSize: 12, color: '#888', lineHeight: 1.8, margin: '0 0 16px' }}>
          <strong style={{ color: '#aaa' }}>Elo model:</strong> Each team's Elo rating is
          built from every IPL match since 2008 using a K-factor of 32 and a base rating of
          1,000. A win against a higher-rated opponent earns more points than a win against a
          weaker one. Home advantage is modelled as a 30-point Elo boost for the home side.
          Ratings partially regress toward the mean between seasons.
        </p>
        <p style={{ fontSize: 12, color: '#888', lineHeight: 1.8, margin: '0 0 28px' }}>
          <strong style={{ color: '#aaa' }}>Form model:</strong> Captures recent momentum
          using the last 12 matches per team with exponential decay weights (0.75ⁱ — most
          recent match counts most, oldest carries ~3% of the weight). A win is 1, a loss is
          0. This form score ∈ [0,1] is converted into a per-match win probability. Both
          models then feed into 100,000 Monte Carlo simulations of all remaining fixtures.
          The playoff % is the fraction of simulations in which a team finishes top 4.
        </p>
        <a
          href="https://cricsheet.org"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            fontSize: 12,
            color: '#aaa',
            textDecoration: 'none',
            borderBottom: '1px solid #444',
            paddingBottom: 1,
          }}
        >
          Data: Cricsheet.org
        </a>
      </div>
    </footer>
  )
}
