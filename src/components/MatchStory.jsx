import { useState, useEffect } from 'react'

export default function MatchStory() {
  const [story, setStory] = useState(null)
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    fetch('/data/stories.json')
      .then(r => r.json())
      .then(data => {
        // Latest match story (type: 'match'), newest last
        const matchStories = (data.stories || []).filter(s => s.type === 'match' || !s.type)
        if (matchStories.length > 0) {
          setStory(matchStories[matchStories.length - 1])
        }
        setLoaded(true)
      })
      .catch(() => setLoaded(true))
  }, [])

  if (!loaded) return null

  return (
    <div style={{
      background: '#0d0f16',
      borderTop: '0.5px solid #1e2130',
      borderBottom: '0.5px solid #1e2130',
    }}>
      <div className="sec" style={{ paddingTop: 40, paddingBottom: 44 }}>

        {/* Section label + date */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <div style={{ fontSize: 11, color: '#FFD700', letterSpacing: '2px', textTransform: 'uppercase' }}>
            Latest Match Story
          </div>
          {story && (
            <div style={{ fontSize: 11, color: '#555' }}>
              {new Date(story.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}
            </div>
          )}
        </div>

        <div style={{ height: '0.5px', background: '#1e2130', marginBottom: 24 }} />

        {!story ? (
          // Placeholder
          <div style={{ fontSize: 14, color: '#555', lineHeight: 1.8 }}>
            Match story generates automatically after each match. Check back tonight.
          </div>
        ) : (
          <>
            {/* Headline */}
            <h2 style={{
              fontSize: 22, fontWeight: 500, color: '#fff',
              letterSpacing: '-0.5px', lineHeight: 1.35,
              margin: '0 0 20px 0',
            }}>
              {story.headline}
            </h2>

            {/* Body */}
            <div style={{ fontSize: 14, color: '#aaa', lineHeight: 1.8, marginBottom: 28 }}>
              {story.body.split('\n\n').filter(Boolean).map((para, i) => (
                <p key={i} style={{ margin: i === 0 ? 0 : '14px 0 0 0' }}>{para}</p>
              ))}
            </div>

            {/* Odds change pills */}
            {story.odds_changes && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {Object.entries(story.odds_changes)
                  .filter(([, c]) => Math.abs(c.delta) >= 0.5)
                  .sort(([, a], [, b]) => Math.abs(b.delta) - Math.abs(a.delta))
                  .map(([short, c]) => {
                    const up = c.delta >= 0
                    return (
                      <div key={short} style={{
                        display: 'flex', alignItems: 'center', gap: 6,
                        padding: '5px 12px', borderRadius: 20,
                        background: up ? 'rgba(74,222,128,0.08)' : 'rgba(248,113,113,0.08)',
                        border: `0.5px solid ${up ? 'rgba(74,222,128,0.2)' : 'rgba(248,113,113,0.2)'}`,
                        fontSize: 12, fontWeight: 500,
                        color: up ? '#4ade80' : '#f87171',
                        fontVariantNumeric: 'tabular-nums',
                      }}>
                        <span style={{ color: '#aaa', fontWeight: 400 }}>{short}</span>
                        {up ? '↑' : '↓'}{Math.abs(c.delta).toFixed(1)}%
                      </div>
                    )
                  })
                }
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
