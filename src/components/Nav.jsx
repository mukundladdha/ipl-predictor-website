import DuckworthLogo from './DuckworthLogo'

const S = {
  nav: {
    borderBottom: '0.5px solid #2a2d3a',
    background: '#0f1117',
  },
  inner: {
    height: 64,
    display: 'flex',
    alignItems: 'center',
  },
  updated: {
    fontSize: 12,
    color: '#888',
    marginLeft: 'auto',
  },
}

export default function Nav({ lastUpdated }) {
  return (
    <nav style={S.nav}>
      <div className="sec" style={S.inner}>
        <DuckworthLogo />
        <div style={S.updated}>Updated · {lastUpdated}</div>
      </div>
    </nav>
  )
}
