import { useState, useEffect } from 'react'
import { useModel } from '../context/ModelContext'

function recalculate(teams, results, model) {
  return teams.map(t => {
    const bonus = (results[t.short] ?? 0) * 2  // +2 pts per simulated win
    const base  = t.models?.[model]?.playoff_pct ?? 0
    return {
      ...t,
      _simPct: Math.min(99, Math.max(1, Math.round(base + bonus * 2.5))),
    }
  })
}

export default function ScenarioExplorer({ teams }) {
  const { model } = useModel()
  const [fixtures, setFixtures] = useState([])
  const [results, setResults] = useState({})   // short -> wins count
  const [simTeams, setSimTeams] = useState(teams)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/data/fixtures.json')
      .then(r => r.json())
      .then(d => { setFixtures(d.fixtures ?? []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  // Re-run whenever teams, results or model changes
  useEffect(() => {
    setSimTeams(recalculate(teams, results, model))
  }, [teams, results, model])

  const teamByShort = short => teams.find(t => t.short === short)

  function handlePick(fixtureId, winnerShort, loserShort) {
    setResults(prev => {
      const next = { ...prev }
      // Toggle: clicking same winner again deselects
      if (next[`fix_${fixtureId}`] === winnerShort) {
        delete next[`fix_${fixtureId}`]
        // undo point
        next[winnerShort] = Math.max(0, (next[winnerShort] ?? 0) - 1)
      } else {
        // Remove old winner's point if previously set
        const old = next[`fix_${fixtureId}`]
        if (old) next[old] = Math.max(0, (next[old] ?? 0) - 1)
        next[`fix_${fixtureId}`] = winnerShort
        next[winnerShort] = (next[winnerShort] ?? 0) + 1
      }
      return next
    })
  }

  function handleReset() {
    setResults({})
  }

  const hasSelections = Object.keys(results).some(k => k.startsWith('fix_'))

  return (
    <section className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-bold text-white">Scenario Explorer</h2>
          <span className={`px-2 py-0.5 text-xs font-bold rounded-full ${
            model === 'elo'
              ? 'bg-[#FFD700]/20 text-[#FFD700] border border-[#FFD700]/30'
              : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
          }`}>
            {model === 'elo' ? 'Elo base' : 'Form base'}
          </span>
        </div>
        {hasSelections && (
          <button
            onClick={handleReset}
            className="text-xs px-3 py-1.5 bg-[#2a2d3a] hover:bg-[#3a3d4a] text-gray-300 rounded-lg transition-colors font-medium"
          >
            ↺ Reset
          </button>
        )}
      </div>
      <p className="text-sm text-gray-400 mb-6">
        Pick winners for upcoming fixtures — playoff odds update in real time
      </p>

      <div className="grid lg:grid-cols-2 gap-4">

        {/* Fixtures */}
        <div className="space-y-3">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
            Upcoming Fixtures
          </h3>

          {loading && (
            <div className="text-sm text-gray-500 text-center py-8">Loading fixtures…</div>
          )}

          {!loading && fixtures.map(fix => {
            const tA = teamByShort(fix.teamA)
            const tB = teamByShort(fix.teamB)
            const selected = results[`fix_${fix.id}`]

            return (
              <div key={fix.id} className="bg-[#1a1d27] border border-[#2a2d3a] rounded-xl p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs text-gray-500">
                    {fix.date} · {fix.venue?.split(',')[0]}
                  </span>
                  {selected && (
                    <span className="text-xs text-[#FFD700] font-medium">
                      {teamByShort(selected)?.name ?? selected} wins
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  {[fix.teamA, fix.teamB].map(short => {
                    const t = teamByShort(short)
                    const isSelected = selected === short
                    const otherSelected = selected && selected !== short
                    return (
                      <button
                        key={short}
                        onClick={() => handlePick(fix.id, short, short === fix.teamA ? fix.teamB : fix.teamA)}
                        className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg
                          text-sm font-semibold transition-all
                          ${isSelected
                            ? 'text-white ring-2 ring-offset-1 ring-offset-[#1a1d27]'
                            : otherSelected
                              ? 'opacity-35 bg-[#13161f] text-gray-500 border border-[#2a2d3a]'
                              : 'bg-[#13161f] text-white border border-[#2a2d3a] hover:border-[#FFD700]'
                          }`}
                        style={isSelected ? { backgroundColor: t?.color, borderColor: t?.color } : {}}
                      >
                        <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: t?.color }} />
                        {short}
                      </button>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </div>

        {/* Live odds */}
        <div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
            Updated Playoff Odds
            {hasSelections && <span className="ml-2 text-[#FFD700]">● Live</span>}
          </h3>
          <div className="bg-[#1a1d27] border border-[#2a2d3a] rounded-xl overflow-hidden">
            {[...simTeams]
              .sort((a, b) => (b._simPct ?? 0) - (a._simPct ?? 0))
              .map((team, i) => {
                const base   = team.models?.[model]?.playoff_pct ?? 0
                const simPct = team._simPct ?? base
                const delta  = simPct - base

                return (
                  <div
                    key={team.short}
                    className={`flex items-center gap-3 px-4 py-3 border-b border-[#2a2d3a] last:border-0
                      ${i % 2 === 0 ? '' : 'bg-[#13161f]/40'}`}
                  >
                    <span className="text-xs text-gray-600 w-4 text-center font-mono tabular-nums">{i+1}</span>
                    <div className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ backgroundColor: team.color }} />
                    <span className="text-sm text-gray-300 flex-1 truncate">{team.name}</span>

                    {delta !== 0 && (
                      <span className={`text-xs font-bold tabular-nums flex-shrink-0 ${delta > 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {delta > 0 ? '+' : ''}{delta}%
                      </span>
                    )}

                    <div className="flex items-center gap-2 w-28 flex-shrink-0">
                      <div className="flex-1 h-1.5 rounded-full bg-[#2a2d3a] overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${Math.min(simPct, 100)}%`,
                            backgroundColor: simPct >= 60 ? '#22c55e' : simPct >= 30 ? '#eab308' : '#ef4444'
                          }}
                        />
                      </div>
                      <span className="text-xs font-bold text-gray-300 w-9 text-right tabular-nums">
                        {simPct}%
                      </span>
                    </div>
                  </div>
                )
              })}
          </div>
        </div>
      </div>
    </section>
  )
}
