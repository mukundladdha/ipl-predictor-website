const S = {
  nav: {
    borderBottom: '0.5px solid #2a2d3a',
    background: '#0f1117',
  },
  inner: {
    maxWidth: 900,
    margin: '0 auto',
    padding: '14px 24px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  logo: {
    fontSize: 15,
    fontWeight: 600,
    color: '#fff',
    letterSpacing: '-0.3px',
  },
  updated: {
    fontSize: 12,
    color: '#444',
  },
}

export default function Nav({ lastUpdated }) {
  return (
    <nav style={S.nav}>
      <div style={S.inner}>
        <div style={S.logo}>
          IPL <span style={{ color: '#FFD700' }}>Forecast</span> 2025
        </div>
        <div style={S.updated}>Updated · {lastUpdated}</div>
      </div>
    </nav>
  )
}
