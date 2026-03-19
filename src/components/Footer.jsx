export default function Footer() {
  return (
    <footer className="border-t border-[#2a2d3a] bg-[#0f1117] mt-8">
      <div className="max-w-7xl mx-auto px-4 py-10">
        <div className="grid md:grid-cols-3 gap-8">
          <div>
            <h3 className="text-sm font-semibold text-white mb-3">Methodology</h3>
            <p className="text-xs text-gray-500 leading-relaxed">
              Playoff probabilities are derived from 10,000 Monte Carlo simulations of the
              IPL 2026 season (74 league matches). Pre-season win probabilities are estimated
              using ELO ratings seeded from IPL 2025 final standings, adjusted for squad changes
              from the December 2025 mini-auction and home advantage (+4%).
            </p>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white mb-3">Season at a Glance</h3>
            <ul className="text-xs text-gray-500 space-y-1">
              <li>📅 <span className="text-gray-400">Start:</span> March 28, 2026</li>
              <li>🏁 <span className="text-gray-400">Final:</span> May 31, 2026</li>
              <li>🏟 <span className="text-gray-400">Matches:</span> 84 total (74 league + 4 playoffs)</li>
              <li>🏆 <span className="text-gray-400">Defending Champions:</span> Royal Challengers Bengaluru</li>
              <li>🎯 <span className="text-gray-400">Opening Match:</span> RCB vs SRH, Bengaluru</li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white mb-3">Assumptions & Limitations</h3>
            <p className="text-xs text-gray-500 leading-relaxed">
              Pre-season forecasts carry high uncertainty — form, injuries, pitch conditions,
              and weather are not yet modeled. The Scenario Explorer uses a simplified linear
              model for illustration. Data is for educational purposes only and not suitable
              for betting decisions.
            </p>
          </div>
        </div>
        <div className="mt-8 pt-6 border-t border-[#2a2d3a] flex flex-col sm:flex-row items-center justify-between gap-2">
          <span className="text-xs text-gray-600">
            IPL 2026 Forecast · TATA IPL 19th Edition · Inspired by FiveThirtyEight
          </span>
          <span className="text-xs text-gray-600">
            Built with React · Recharts · Tailwind CSS
          </span>
        </div>
      </div>
    </footer>
  )
}
