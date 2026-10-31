import React from "react";

// Inline Button Component
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "secondary" | "ghost" | "gradient" | "medical";
  size?: "default" | "sm" | "lg";
  children: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "default", size = "default", className = "", children, ...props }, ref) => {
    const baseStyles =
      "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50";

    const variants = {
      default: "bg-sky-500 text-white hover:bg-sky-600 shadow-md shadow-sky-500/25",
      secondary: "bg-slate-800 text-slate-100 hover:bg-slate-700 border border-slate-700/60",
      ghost: "hover:bg-sky-950/40 text-slate-200 hover:text-sky-300",
      gradient:
        "bg-gradient-to-r from-sky-500 via-cyan-400 to-teal-400 text-slate-950 font-semibold shadow-lg shadow-cyan-500/30 hover:scale-[1.02] active:scale-[0.98]",
      medical:
        "bg-gradient-to-r from-sky-600 to-cyan-600 text-white font-semibold shadow-lg shadow-sky-600/30 hover:bg-sky-500 hover:scale-[1.02] active:scale-[0.98]",
    };

    const sizes = {
      default: "h-10 px-4 py-2 text-sm",
      sm: "h-9 px-4 text-xs font-semibold rounded-md",
      lg: "h-12 px-8 text-base font-semibold rounded-lg",
    };

    return (
      <button
        ref={ref}
        className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";

// Icons
const ArrowRight = ({ className = "", size = 16 }: { className?: string; size?: number }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M5 12h14" />
    <path d="m12 5 7 7-7 7" />
  </svg>
);

const Activity = ({ className = "", size = 20 }: { className?: string; size?: number }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
  </svg>
);

const ShieldCheck = ({ className = "", size = 16 }: { className?: string; size?: number }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" />
    <path d="m9 12 2 2 4-4" />
  </svg>
);

const Sparkles = ({ className = "", size = 16 }: { className?: string; size?: number }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
  </svg>
);

const Menu = ({ className = "", size = 24 }: { className?: string; size?: number }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <line x1="4" x2="20" y1="12" y2="12" />
    <line x1="4" x2="20" y1="6" y2="6" />
    <line x1="4" x2="20" y1="18" y2="18" />
  </svg>
);

const X = ({ className = "", size = 24 }: { className?: string; size?: number }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M18 6 6 18" />
    <path d="m6 6 12 12" />
  </svg>
);

// Navigation Component
export const Navigation = React.memo(() => {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  return (
    <header className="fixed top-0 w-full z-50 border-b border-slate-800/80 bg-[#080d1a]/80 backdrop-blur-xl">
      <nav className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Brand Logo */}
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-sky-600 via-cyan-500 to-teal-400 p-[1px] shadow-lg shadow-cyan-500/20">
              <div className="h-full w-full rounded-[7px] bg-[#090e1c] flex items-center justify-center text-cyan-400">
                <Activity size={20} />
              </div>
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-bold text-white tracking-tight leading-none flex items-center gap-1.5">
                Health<span className="text-cyan-400">Copilot</span>
                <span className="text-[10px] font-semibold bg-sky-500/20 text-sky-400 border border-sky-500/30 px-1.5 py-0.5 rounded-full">
                  ABDM
                </span>
              </span>
              <span className="text-[10px] text-slate-400 tracking-wider uppercase font-medium mt-0.5">
                Personal AI Healthcare
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center justify-center gap-8 absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
            <a
              href="#ingestion"
              className="text-sm font-medium text-slate-300 hover:text-cyan-400 transition-colors"
            >
              Smart Ingestion
            </a>
            <a
              href="#copilot-chat"
              className="text-sm font-medium text-slate-300 hover:text-cyan-400 transition-colors"
            >
              GPT-6-Luna Chat
            </a>
            <a
              href="#timeline"
              className="text-sm font-medium text-slate-300 hover:text-cyan-400 transition-colors"
            >
              Health Timeline
            </a>
            <a
              href="#abdm-vault"
              className="text-sm font-medium text-slate-300 hover:text-cyan-400 transition-colors"
            >
              3-Tier S3 Vault
            </a>
          </div>

          {/* Header Action Buttons */}
          <div className="hidden md:flex items-center gap-3">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => window.open("http://3.27.249.44:8000/", "_blank")}
            >
              Backend API
            </Button>
            <Button
              type="button"
              variant="gradient"
              size="sm"
              onClick={() => {
                const el = document.getElementById("dashboard-preview");
                el?.scrollIntoView({ behavior: "smooth" });
              }}
            >
              Launch Dashboard
            </Button>
          </div>

          {/* Mobile Menu Toggle */}
          <button
            type="button"
            className="md:hidden text-slate-300 hover:text-white"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </nav>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-[#080d1a]/95 backdrop-blur-xl border-t border-slate-800 animate-slideDown">
          <div className="px-6 py-5 flex flex-col gap-4">
            <a
              href="#ingestion"
              className="text-sm font-medium text-slate-300 hover:text-cyan-400 py-1"
              onClick={() => setMobileMenuOpen(false)}
            >
              Smart Ingestion
            </a>
            <a
              href="#copilot-chat"
              className="text-sm font-medium text-slate-300 hover:text-cyan-400 py-1"
              onClick={() => setMobileMenuOpen(false)}
            >
              GPT-6-Luna Chat
            </a>
            <a
              href="#timeline"
              className="text-sm font-medium text-slate-300 hover:text-cyan-400 py-1"
              onClick={() => setMobileMenuOpen(false)}
            >
              Health Timeline
            </a>
            <a
              href="#abdm-vault"
              className="text-sm font-medium text-slate-300 hover:text-cyan-400 py-1"
              onClick={() => setMobileMenuOpen(false)}
            >
              3-Tier S3 Vault
            </a>
            <div className="flex flex-col gap-2 pt-4 border-t border-slate-800">
              <Button
                type="button"
                variant="gradient"
                size="sm"
                onClick={() => setMobileMenuOpen(false)}
              >
                Launch Dashboard
              </Button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
});

Navigation.displayName = "Navigation";

// Hero Component
export const Hero = React.memo(() => {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-start px-6 pt-28 pb-20 md:pt-36 md:pb-28 overflow-hidden">
      {/* Background Ambient Glows (Medical Cyan & Teal) */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[450px] bg-gradient-to-tr from-sky-500/20 via-cyan-400/15 to-teal-400/10 blur-[130px] pointer-events-none rounded-full" />
      <div className="absolute top-1/3 left-1/4 w-[350px] h-[350px] bg-blue-600/10 blur-[100px] pointer-events-none rounded-full" />

      {/* Badge Notification */}
      <aside className="mb-8 inline-flex items-center justify-center gap-2 px-4 py-1.5 rounded-full border border-cyan-500/30 bg-cyan-950/30 backdrop-blur-md shadow-inner shadow-cyan-500/10 hover:border-cyan-400/50 transition-colors">
        <span className="flex h-2 w-2 rounded-full bg-cyan-400 animate-ping" />
        <span className="text-xs font-medium text-cyan-300 flex items-center gap-1.5">
          <Sparkles size={13} className="text-cyan-400" />
          ABDM & FHIR R4 Ready &bull; Powered by GPT-6-Luna
        </span>
        <a
          href="#features"
          className="flex items-center gap-1 text-xs text-slate-400 hover:text-cyan-200 transition-colors pl-1"
        >
          Explore Architecture
          <ArrowRight size={12} />
        </a>
      </aside>

      {/* Main Hero Headline */}
      <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold text-center max-w-4xl px-4 tracking-tight leading-[1.1] mb-6">
        AI-Powered Personal{" "}
        <span className="bg-gradient-to-r from-sky-400 via-cyan-300 to-teal-300 bg-clip-text text-transparent">
          Health Copilot
        </span>
      </h1>

      {/* Subhead with Clinical Problem Solving Value Proposition */}
      <p className="text-base md:text-lg text-center max-w-2xl px-4 text-slate-300 leading-relaxed mb-10 font-normal">
        Transform complex prescriptions, lab reports, and code-mixed{" "}
        <span className="text-cyan-300 font-medium">Telugu & Hindi records</span> into
        meaningful, plain-language insights, unified longitudinal timelines, and safe clinical guidance.
      </p>

      {/* CTA Buttons */}
      <div className="flex flex-wrap items-center justify-center gap-4 relative z-10 mb-16">
        <Button
          type="button"
          variant="gradient"
          size="lg"
          className="rounded-xl flex items-center justify-center gap-2 text-slate-950"
          onClick={() => {
            const el = document.getElementById("dashboard-preview");
            el?.scrollIntoView({ behavior: "smooth" });
          }}
        >
          <span>Get Started Free</span>
          <ArrowRight size={18} />
        </Button>
        <Button
          type="button"
          variant="secondary"
          size="lg"
          className="rounded-xl text-slate-200 hover:text-white"
          onClick={() => window.open("http://3.27.249.44:8000/", "_blank")}
        >
          <Activity size={18} className="text-cyan-400" />
          <span>Live EC2 Instance</span>
        </Button>
      </div>

      {/* Live Value Prop Pillars */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl w-full mb-16 px-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm text-center">
          <div className="text-cyan-400 font-bold text-xl md:text-2xl">PP-OCRv6</div>
          <div className="text-xs text-slate-400 mt-1">Multilingual Indic OCR (Telugu, Hindi, English)</div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm text-center">
          <div className="text-emerald-400 font-bold text-xl md:text-2xl">GPT-6-Luna</div>
          <div className="text-xs text-slate-400 mt-1">Autonomous Clinical Ingestion & Triage</div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm text-center">
          <div className="text-sky-400 font-bold text-xl md:text-2xl">3-Tier S3</div>
          <div className="text-xs text-slate-400 mt-1">Raw, Artifacts & FHIR R4 Vaults</div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm text-center">
          <div className="text-amber-400 font-bold text-xl md:text-2xl">100% ACID</div>
          <div className="text-xs text-slate-400 mt-1">Relational SQLite / MySQL Schema</div>
        </div>
      </div>

      {/* Dashboard Preview Graphic Card */}
      <div id="dashboard-preview" className="w-full max-w-5xl relative pb-16 px-2">
        {/* Glow Behind the Card */}
        <div
          className="absolute left-1/2 -top-12 w-[85%] h-[60%] bg-gradient-to-b from-sky-500/25 to-teal-500/5 blur-3xl rounded-full pointer-events-none -translate-x-1/2"
          aria-hidden="true"
        />

        {/* Clinical Interface Mockup Container */}
        <div className="relative z-10 rounded-2xl border border-slate-700/80 bg-gradient-to-b from-slate-900 via-[#0c1322] to-[#080d1a] p-3 sm:p-5 shadow-2xl shadow-cyan-950/50 backdrop-blur-md">
          {/* Mock Browser Header Bar */}
          <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4 px-2">
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-rose-500/80" />
              <div className="h-3 w-3 rounded-full bg-amber-500/80" />
              <div className="h-3 w-3 rounded-full bg-emerald-500/80" />
              <span className="text-xs text-slate-400 ml-2 font-mono hidden sm:inline">
                https://copilot.health.abdm/patient/PAT-91443288912011
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-medium text-emerald-400 bg-emerald-950/60 border border-emerald-800 px-2 py-0.5 rounded-full flex items-center gap-1">
                <ShieldCheck size={12} /> Live Encrypted Vault
              </span>
            </div>
          </div>

          {/* Mockup Dashboard Content Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Left: Patient Profile & Vitals */}
            <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-4 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="text-xs uppercase font-semibold text-slate-400">Patient Identity</div>
                  <span className="text-[10px] font-mono bg-sky-950 text-sky-400 border border-sky-800 px-1.5 py-0.5 rounded">
                    ABDM Linked
                  </span>
                </div>
                <div className="text-lg font-bold text-white">Ramesh Rao</div>
                <div className="text-xs text-slate-400">ABHA: 91-4432-8891-2011 &bull; 52y / Male</div>
                
                <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-slate-800">
                  <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                    <div className="text-[10px] text-slate-400">Blood Pressure</div>
                    <div className="text-sm font-bold text-amber-300">140/90 mmHg</div>
                  </div>
                  <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                    <div className="text-[10px] text-slate-400">Pulse</div>
                    <div className="text-sm font-bold text-slate-200">76 bpm</div>
                  </div>
                  <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                    <div className="text-[10px] text-slate-400">Fasting Sugar</div>
                    <div className="text-sm font-bold text-rose-400">162 mg/dL HIGH</div>
                  </div>
                  <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                    <div className="text-[10px] text-slate-400">HbA1c</div>
                    <div className="text-sm font-bold text-rose-400">7.8% HIGH</div>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
                <span>Next Visit: 27-Oct-2026</span>
                <span className="text-cyan-400 font-medium">Dr. K. Srinivas</span>
              </div>
            </div>

            {/* Middle: Bilingual Prescriptions & Regimen */}
            <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="text-xs uppercase font-semibold text-slate-400">Active Regimen</div>
                <span className="text-[10px] font-medium bg-emerald-950 text-emerald-400 border border-emerald-800 px-1.5 py-0.5 rounded">
                  4 Active Prescriptions
                </span>
              </div>

              <div className="space-y-2.5">
                <div className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-xs text-white">Metformin 500mg</span>
                    <span className="text-[10px] font-mono text-cyan-300 bg-cyan-950 px-1 rounded">1-0-1</span>
                  </div>
                  <div className="text-[11px] text-cyan-400 font-telugu mt-0.5">
                    మోతాదు: రోజుకు రెండుసార్లు భోజనం తర్వాత తీసుకోండి
                  </div>
                  <div className="text-[10px] text-slate-400">Twice daily after meals</div>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-xs text-white">Telmisartan 40mg</span>
                    <span className="text-[10px] font-mono text-cyan-300 bg-cyan-950 px-1 rounded">1-0-0</span>
                  </div>
                  <div className="text-[11px] text-cyan-400 font-telugu mt-0.5">
                    మోతాదు: ఉదయం ఖాళీ కడుపుతో ఒకసారి వేసుకోండి
                  </div>
                  <div className="text-[10px] text-slate-400">Once daily in morning on empty stomach</div>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-xs text-white">Glimepiride 1mg</span>
                    <span className="text-[10px] font-mono text-amber-300 bg-amber-950/60 px-1 rounded">1-0-0</span>
                  </div>
                  <div className="text-[11px] text-cyan-400 font-telugu mt-0.5">
                    మోతాదు: ఉదయం అల్పాహారానికి 15 నిమిషాల ముందు
                  </div>
                  <div className="text-[10px] text-slate-400">15 minutes before breakfast</div>
                </div>
              </div>
            </div>

            {/* Right: Downstream Copilot Chat (GPT-6-Luna) */}
            <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-4 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="text-xs uppercase font-semibold text-slate-400 flex items-center gap-1.5">
                    <Sparkles size={12} className="text-cyan-400" />
                    GPT-6-Luna Copilot
                  </div>
                  <span className="text-[10px] font-mono text-teal-400 bg-teal-950 px-1.5 py-0.5 rounded border border-teal-800">
                    Live
                  </span>
                </div>

                {/* Simulated Chat Bubbles */}
                <div className="space-y-2 text-xs">
                  <div className="bg-sky-600/30 text-sky-200 border border-sky-500/40 p-2.5 rounded-xl rounded-tr-sm">
                    <b>You:</b> నా మందుల షెడ్యూల్ మరియు ల్యాబ్ పరీక్షల ఫలితాలు వివరించండి.
                  </div>
                  <div className="bg-slate-900 border border-slate-800 p-2.5 rounded-xl rounded-tl-sm text-slate-200 space-y-1">
                    <div className="text-cyan-300 font-medium font-telugu">
                      రమేష్ గారు, అపోలో క్లినిక్ డా. కె. శ్రీనివాస్ గారి రికార్డుల ప్రకారం:
                    </div>
                    <div className="text-[11px] text-slate-300 font-telugu">
                      &bull; ఉదయం ఖాళీ కడుపుతో Telmisartan వేసుకోండి.
                    </div>
                    <div className="text-[11px] text-slate-300 font-telugu">
                      &bull; టిఫిన్ కంటే 15 నిమిషాల ముందు Glimepiride తీసుకోండి.
                    </div>
                    <div className="text-[11px] text-amber-300 font-telugu">
                      &bull; FBS 162 mg/dL మరియు HbA1c 7.8% ఎక్కువగా ఉన్నాయి; అక్టోబర్ 27న ఫాలో-అప్ ఉంది.
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Chip */}
              <div className="mt-3 pt-2.5 border-t border-slate-800 flex items-center justify-between">
                <span className="text-[10px] text-slate-400">Invoked: 3 relational tools</span>
                <span className="text-[10px] text-emerald-400 font-medium bg-emerald-950/80 px-2 py-0.5 rounded">
                  Safe with Monitoring
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
});

Hero.displayName = "Hero";

// Main Component
export default function Component() {
  return (
    <main className="min-h-screen bg-[#080d1a] text-slate-100 selection:bg-cyan-500/30 selection:text-cyan-200">
      <Navigation />
      <Hero />
    </main>
  );
}
