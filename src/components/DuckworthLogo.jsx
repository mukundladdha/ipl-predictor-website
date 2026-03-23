export default function DuckworthLogo() {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      cursor: 'default',
    }}>
      <svg
        width="28"
        height="28"
        viewBox="0 0 28 28"
        style={{ transition: 'transform 0.15s ease', flexShrink: 0 }}
        onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.05)'}
        onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
      >
        {/* body: wide ellipse */}
        <ellipse cx="13" cy="18" rx="11" ry="7" fill="#FFD700" />
        {/* head: small circle */}
        <circle cx="22" cy="11" r="4" fill="#FFD700" />
        {/* bill: small triangle pointing right */}
        <polygon points="25,9 28,11 25,13" fill="#FFD700" />
      </svg>
      <span style={{ fontSize: 18, letterSpacing: '-0.5px', lineHeight: 1 }}>
        <span style={{ color: '#FFD700', fontWeight: 500 }}>Duck</span>
        <span style={{ color: '#ffffff', fontWeight: 500 }}>worth</span>
      </span>
    </div>
  )
}
