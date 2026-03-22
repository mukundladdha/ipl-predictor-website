const S = {
  nav: {
    borderBottom: '0.5px solid #2a2d3a',
    background: '#0f1117',
  },
  inner: {
    padding: '14px 0',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  logo: {
    fontSize: 15,
    fontWeight: 500,
    color: '#fff',
    letterSpacing: '-0.3px',
  },
  updated: {
    fontSize: 12,
    color: '#888',
  },
}

export default function Nav({ lastUpdated }) {
  return (
    <nav style={S.nav}>
      <div className="sec" style={S.inner}>
        <div style={S.logo}>
          <span style={{ color: '#FFD700' }}>Duckworth</span>
        </div>
        <div style={S.updated}>Updated · {lastUpdated}</div>
      </div>
    </nav>
  )
}
