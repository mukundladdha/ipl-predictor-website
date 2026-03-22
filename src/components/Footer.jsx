export default function Footer() {
  return (
    <footer className="border-t border-[#2a2d3a] bg-[#0f1117] mt-8">
      <div className="max-w-7xl mx-auto px-4 py-10">
        <div className="grid md:grid-cols-3 gap-8">

          <div>
            <h3 className="text-sm font-semibold text-white mb-3">Elo Model</h3>
            <p className="text-xs text-gray-500 leading-relaxed">
              Uses every IPL match since 2008 (1,100+ games from Cricsheet) to build a
              running Elo rating for each franchise. K-factor of 32, base rating 1000.
              Higher Elo = consistently strong franchise. Home advantage modeled as
              +30 Elo points for the home side.
            </p>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-white mb-3">Form Model</h3>
            <p className="text-xs text-gray-500 leading-relaxed">
              Captures recent momentum using the last 8 matches per team with exponential
              decay weights (0.5ⁱ — most recent match counts most). Win = 1, loss = 0.
              Produces a form score ∈ [0,1]. Home advantage +4% per match. Volatile by
              design — reacts quickly to hot/cold streaks.
            </p>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-white mb-3">Monte Carlo Simulation</h3>
            <p className="text-xs text-gray-500 leading-relaxed">
              Both models feed win probabilities into 100,000 simulations of all remaining
              74 league matches. Playoff % = fraction of sims where team finishes top 4.
              Rank probabilities show finish-position distributions across all simulations.
              NRR used as tiebreaker in each sim.
            </p>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-[#2a2d3a] flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="text-xs text-gray-600">
            IPL 2026 Forecast · TATA IPL 19th Edition · Inspired by FiveThirtyEight
          </div>
          <div className="flex items-center gap-4 text-xs text-gray-600">
            <a
              href="https://cricsheet.org"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-[#FFD700] transition-colors flex items-center gap-1"
            >
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              Data: Cricsheet
            </a>
            <span>·</span>
            <span>React · Recharts · Tailwind CSS</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
