import { useModel } from '../context/ModelContext'

const CARDS = [
  {
    id: 'elo',
    icon: '⚖️',
    title: 'Elo rating',
    body: "A running strength rating built across every IPL season. Beating a stronger team earns more rating points than beating a weaker one — and losing to a weaker team costs more. A team's full history is baked in, but recent seasons carry more weight.",
  },
  {
    id: 'form',
    icon: '🔥',
    title: 'Form model',
    body: 'Win/loss record across the last 12 matches, with each older match weighted progressively less. A team winning their last 3 straight is treated very differently to one that won 3 of their last 12. Captures momentum the Elo model is slower to reflect.',
  },
]

export default function ConceptCards() {
  const { activeModel, setActiveModel } = useModel()

  return (
    <div className="sec" style={{ paddingTop: 56, paddingBottom: 40 }}>
      <div style={{
        fontSize: 11,
        color: '#FFD700',
        letterSpacing: '2px',
        textTransform: 'uppercase',
        marginBottom: 16,
      }}>
        How we build the forecast
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 12,
      }}>
        {CARDS.map(card => {
          const active = activeModel === card.id
          return (
            <button
              key={card.id}
              onClick={() => setActiveModel(card.id)}
              style={{
                textAlign: 'left',
                background: '#1a1d27',
                border: `1px solid ${active ? '#FFD700' : '#2a2d3a'}`,
                borderRadius: 12,
                padding: '20px 20px 22px',
                cursor: 'pointer',
                transition: 'border-color 0.2s',
                width: '100%',
              }}
            >
              <div style={{ fontSize: 22, marginBottom: 10 }}>{card.icon}</div>
              <div style={{
                fontSize: 13,
                fontWeight: 500,
                color: active ? '#FFD700' : '#ccc',
                marginBottom: 10,
                transition: 'color 0.2s',
              }}>
                {card.title}
              </div>
              <div style={{
                fontSize: 13,
                color: active ? '#aaa' : '#666',
                lineHeight: 1.75,
                transition: 'color 0.2s',
              }}>
                {card.body}
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
