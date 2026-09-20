export default function AboutPage() {
  return (
    <div className="max-w-4xl mx-auto p-8 space-y-8 animate-fadeIn">
      <div className="bg-gradient-to-r from-teal-500/10 to-blue-500/10 border border-teal-100 rounded-3xl p-8 shadow-sm">
        <span className="text-xs font-bold uppercase tracking-wider text-teal-600 bg-teal-50 px-3 py-1 rounded-full border border-teal-200">
          Project Nimit
        </span>
        <h1 className="text-4xl font-extrabold text-slate-800 mt-4 tracking-tight">
          Grounding Weather in Real-World Impact
        </h1>
        <p className="text-slate-600 mt-3 text-lg leading-relaxed">
          Weather apps give you numbers, but not the real consequences. Nimit bridges live IMD rainfall forecasts and NOAA heat index data with official advisory documents — providing safe, verified guidance for Traffic in Maharashtra and Karnataka, Health in Delhi, and Agriculture in Punjab (Ludhiana, Amritsar), grounded in published thresholds and mechanically verified citations, not LLM guesswork.
        </p>
      </div>

      {/* Coverage Section */}
      <div className="grid md:grid-cols-3 gap-4">
        <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center font-bold">Traffic</div>
          <h3 className="font-bold text-slate-800 text-sm mt-2">Traffic & Urban Mobility</h3>
          <p className="text-slate-600 text-xs">Maharashtra (Mumbai, Pune)</p>
        </div>
        <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center font-bold">Health</div>
          <h3 className="font-bold text-slate-800 text-sm mt-2">Public Health & Heatwave Safety</h3>
          <p className="text-slate-600 text-xs">Delhi</p>
        </div>
        <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center font-bold">Agriculture</div>
          <h3 className="font-bold text-slate-800 text-sm mt-2">Agriculture</h3>
          <p className="text-slate-600 text-xs">Punjab (Ludhiana, Amritsar)</p>
        </div>
      </div>

      {/* How It Works Section */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center font-bold">1</div>
          <h3 className="font-bold text-slate-800 text-lg">Live Forecast</h3>
          <p className="text-slate-600 text-sm">
            Real-time weather forecast data (IMD/O-Meteo) is fetched and validated.
          </p>
        </div>
        <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center font-bold">2</div>
          <h3 className="font-bold text-slate-800 text-lg">Deterministic Risk Rules</h3>
          <p className="text-slate-600 text-sm">
            IMD rainfall categories and NOAA heat index formula are evaluated through pure logic — no LLM guesswork for risk classification.
          </p>
        </div>
        <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center font-bold">3</div>
          <h3 className="font-bold text-slate-800 text-lg">Verified Advisory Retrieval</h3>
          <p className="text-slate-600 text-sm">
            RAG retrieves real advisory documents (government guidelines, municipal reports, agri bulletins) matched by sector/state/city.
          </p>
        </div>
        <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center font-bold">4</div>
          <h3 className="font-bold text-slate-800 text-lg">Cited Answer</h3>
          <p className="text-slate-600 text-sm">
            LLM synthesizes the answer using only retrieved evidence, with citations mechanically verified against source documents.
          </p>
        </div>
      </div>

      {/* Built Responsibly Section */}
      <div className="mt-8 p-6 bg-white border border-slate-100 rounded-2xl shadow-sm">
        <p className="text-slate-600 text-sm">
          This project does not compete with official meteorological sources — it uses published IMD and NOAA thresholds. Every citation is mechanically checked against retrieved evidence; unsupported claims are stripped rather than trusted blindly from the LLM.
        </p>
      </div>
    </div>
  );
}