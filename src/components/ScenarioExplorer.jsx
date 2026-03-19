import { useState } from 'react'

function recalculate(teams, results) {
  const updated = teams.map(t => ({ ...t }))
  Object.entries(results).forEach(([fixtureId, winner]) => {
    const team = updated.find(t => t.short === winner)
    if (team) team._bonusPoints = (team._bonusPoints || 0) + 4
  })
  return updated.map(t => {
    const bonus = t._bonusPoints || 0
    const rawPct = t.playoff_pct + bonus * 2.5
    return { ...t, playoff_pct: Math.min(99, Math.max(1, Math.round(rawPct))) }
  })
}

function PlayoffResultBadge({ result }) {
  if (!result) return null
  const isChamp = result.includes('🏆')
  const isQualified = result.includes('Runner') || result.includes('Eliminator') || result.includes('Qualifier 2')
  if (isChamp) return <span className="text-xs font-bold text-yellow-400">🏆 Champions</span>
  if (result.includes('Runner')) return <span className="text-xs font-medium text-gray-300">Runner-up</span>
  if (isQualified) return <span className="text-xs font-medium text-blue-400">Playoff exit</span>
  return null
}

export default function ScenarioExplorer({ teams: initialTeams, fixtures, seasonComplete }) {
  const [results, setResults] = useState({})
  const [teams, setTeams] = useState(initialTeams)

  function teamByShort(short) {
    return initialTeams.find(t => t.short === short)
  }

  function handlePick(fixtureId, winner) {
    if (seasonComplete) return
    const newResults = { ...results, [fixtureId]: winner }
    setResults(newResults)
    setTeams(recalculate(initialTeams, newResults))
  }

  function handleReset() {
    setResults({})
    setTeams(initialTeams)
  }

  const changed = Object.keys(results).length > 0

  return (
    <section className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-lg font-bold text-white">
          {seasonComplete ? 'Playoff Results' : 'Scenario Explorer'}
        </h2>
        {!seasonComplete && changed && (
          <button
            onClick={handleReset}
            className="text-xs px-3 py-1.5 bg-[#2a2d3a] hover:bg-[#3a3d4a] text-gray-300 rounded-lg transition-colors font-medium"
          >
            ↺ Reset
          </button>
        )}
      </div>
      <p className="text-sm text-gray-400 mb-6">
        {seasonComplete
          ? 'Playoff bracket results — all four knockout matches from May 29 – June 3, 2025'
          : 'Simulate upcoming results to see how playoff odds shift in real time'}
      </p>

      <div className="grid lg:grid-cols-2 gap-4">
        {/* Fixtures / Results */}
        <div className="space-y-3">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            {seasonComplete ? 'Playoff Bracket' : 'Upcoming Fixtures'}
          </h3>
          {fixtures.map(fixture => {
            const tA = teamByShort(fixture.teamA)
            const tB = teamByShort(fixture.teamB)
            const winner = results[fixture.id]
            const hasResult = !!fixture.result

            return (
              <div
                key={fixture.id}
                className="bg-[#1a1d27] border border-[#2a2d3a] rounded-xl p-4"
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs text-gray-500">{fixture.date} · {fixture.venue}</span>
                  {hasResult && (
                    <span className="text-xs text-[#FFD700] font-medium">{fixture.result}</span>
                  )}
                  {!hasResult && winner && (
                    <span className="text-xs text-[#FFD700] font-medium">
                      {winner === fixture.teamA ? tA?.name : tB?.name} wins
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handlePick(fixture.id, fixture.teamA)}
                    disabled={seasonComplete}
                    className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-semibold transition-all
                      ${seasonComplete && fixture.result && !fixture.result.startsWith(fixture.teamA)
                        ? 'opacity-40 bg-[#13161f] text-gray-500 cursor-default'
                        : seasonComplete
                          ? 'bg-[#13161f] text-white border border-[#2a2d3a] cursor-default'
                          : winner === fixture.teamA
                            ? 'ring-2 ring-offset-1 ring-offset-[#1a1d27] text-white'
                            : winner && winner !== fixture.teamA
                              ? 'opacity-40 bg-[#13161f] text-gray-500'
                              : 'bg-[#13161f] hover:bg-[#1e2130] text-white border border-[#2a2d3a] hover:border-[#FFD700]'
                      }`}
                    style={(!seasonComplete && winner === fixture.teamA) ? { backgroundColor: tA?.color } : {}}
                  >
                    <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: tA?.color }} />
                    {fixture.teamA}
                  </button>

                  <span className="text-xs text-gray-600 font-bold px-1">VS</span>

                  <button
                    onClick={() => handlePick(fixture.id, fixture.teamB)}
                    disabled={seasonComplete}
                    className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-semibold transition-all
                      ${seasonComplete && fixture.result && !fixture.result.startsWith(fixture.teamB)
                        ? 'opacity-40 bg-[#13161f] text-gray-500 cursor-default'
                        : seasonComplete
                          ? 'bg-[#13161f] text-white border border-[#2a2d3a] cursor-default'
                          : winner === fixture.teamB
                            ? 'ring-2 ring-offset-1 ring-offset-[#1a1d27] text-white'
                            : winner && winner !== fixture.teamB
                              ? 'opacity-40 bg-[#13161f] text-gray-500'
                              : 'bg-[#13161f] hover:bg-[#1e2130] text-white border border-[#2a2d3a] hover:border-[#FFD700]'
                      }`}
                    style={(!seasonComplete && winner === fixture.teamB) ? { backgroundColor: tB?.color } : {}}
                  >
                    <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: tB?.color }} />
                    {fixture.teamB}
                  </button>
                </div>
              </div>
            )
          })}
        </div>

        {/* Final Standings / Updated Odds */}
        <div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
            {seasonComplete ? 'Final Playoff Outcomes' : 'Updated Playoff Odds'}
            {!seasonComplete && changed && <span className="ml-2 text-[#FFD700]">● Live</span>}
          </h3>
          <div className="bg-[#1a1d27] border border-[#2a2d3a] rounded-xl overflow-hidden">
            {[...teams]
              .sort((a, b) => b.points - a.points || b.nrr - a.nrr)
              .map((team, i) => {
                const original = initialTeams.find(t => t.short === team.short)
                const delta = team.playoff_pct - original.playoff_pct
                const isChamp = team.playoff_result?.includes('🏆')

                return (
                  <div
                    key={team.short}
                    className={`flex items-center gap-3 px-4 py-3 border-b border-[#2a2d3a] last:border-0
                      ${i % 2 === 0 ? '' : 'bg-[#13161f]/40'}
                      ${isChamp ? 'ring-1 ring-inset ring-yellow-500/30' : ''}`}
                  >
                    <span className="text-xs text-gray-600 w-4 text-center font-mono">{i + 1}</span>
                    <div
                      className="w-2.5 h-2.5 rounded-sm flex-shrink-0"
                      style={{ backgroundColor: team.color }}
                    />
                    <span className="text-sm text-gray-300 flex-1">{team.name}</span>

                    {seasonComplete ? (
                      <PlayoffResultBadge result={team.playoff_result} />
                    ) : (
                      <>
                        {delta !== 0 && (
                          <span className={`text-xs font-medium ${delta > 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {delta > 0 ? '+' : ''}{delta}%
                          </span>
                        )}
                        <div className="flex items-center gap-2 w-32">
                          <div className="flex-1 h-1.5 rounded-full bg-[#2a2d3a] overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all duration-500"
                              style={{
                                width: `${team.playoff_pct}%`,
                                backgroundColor: team.playoff_pct >= 60 ? '#22c55e' : team.playoff_pct >= 30 ? '#eab308' : '#ef4444'
                              }}
                            />
                          </div>
                          <span className="text-xs font-bold text-gray-300 w-9 text-right">
                            {team.playoff_pct}%
                          </span>
                        </div>
                      </>
                    )}
                  </div>
                )
              })}
          </div>
        </div>
      </div>
    </section>
  )
}
