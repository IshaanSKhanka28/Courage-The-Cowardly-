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
          Weather apps tell you numbers like temperature and rainfall, but they leave you guessing the real consequences. Nimit bridges live forecasts with official advisories to provide safe, verified guidance.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">1</div>
          <h3 className="font-bold text-slate-800 text-lg">Deterministic Rules</h3>
          <p className="text-slate-600 text-sm">We use published official thresholds (IMD rainfall categories, heat indexes) evaluated through pure logic with zero LLM guesswork.</p>
        </div>
        <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center font-bold">2</div>
          <h3 className="font-bold text-slate-800 text-lg">Citation Verification</h3>
          <p className="text-slate-600 text-sm">Every response is mechanically checked against official municipal and health document corpora to prevent hallucinations.</p>
        </div>
      </div>
    </div>
  );
}