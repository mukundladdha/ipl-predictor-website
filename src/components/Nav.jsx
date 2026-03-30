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
}

export default function Nav() {
  return (
    <nav style={S.nav}>
      <div className="sec" style={S.inner}>
        <DuckworthLogo />
      </div>
    </nav>
  )
}
