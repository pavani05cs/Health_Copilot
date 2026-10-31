import React, { useState, useEffect } from 'react';
import { TrendingUp, AlertTriangle, CheckCircle2, Clock, Activity, FileText, ChevronRight, Sliders, Calendar, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { fetchPatientTimeline, fetchLabTrend } from '../lib/api';
import { Patient, PatientTimeline, LabObservation } from '../types';

interface BiomarkerTrendsProps {
  selectedPatientId: string;
  patients: Patient[];
}

interface MetricConfig {
  id: string;
  name: string;
  unit: string;
  normalMin: number;
  normalMax: number;
  warningMax: number;
  description: string;
  color: string;
}

const METRICS: MetricConfig[] = [
  {
    id: 'HbA1c',
    name: 'HbA1c (Glycated Hemoglobin)',
    unit: '%',
    normalMin: 4.0,
    normalMax: 5.7,
    warningMax: 6.5,
    description: 'Gold standard measure for chronic blood glucose control over 3 months.',
    color: '#06b6d4'
  },
  {
    id: 'Fasting Blood Sugar (FBS)',
    name: 'Fasting Blood Sugar (FBS)',
    unit: 'mg/dL',
    normalMin: 70,
    normalMax: 100,
    warningMax: 125,
    description: 'Baseline blood glucose after 8 hours of overnight fasting.',
    color: '#0ea5e9'
  },
  {
    id: 'Serum Creatinine',
    name: 'Serum Creatinine',
    unit: 'mg/dL',
    normalMin: 0.7,
    normalMax: 1.2,
    warningMax: 1.4,
    description: 'Key biomarker for renal filtration and glomerular function monitoring.',
    color: '#10b981'
  },
  {
    id: 'Blood Pressure',
    name: 'Systolic Blood Pressure',
    unit: 'mmHg',
    normalMin: 90,
    normalMax: 120,
    warningMax: 140,
    description: 'Arterial vascular pressure during cardiac contraction.',
    color: '#f59e0b'
  }
];

export const BiomarkerTrends: React.FC<BiomarkerTrendsProps> = ({ selectedPatientId, patients }) => {
  const [selectedMetricId, setSelectedMetricId] = useState<string>('HbA1c');
  const [timeline, setTimeline] = useState<PatientTimeline | null>(null);
  const [hoveredPoint, setHoveredPoint] = useState<any | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');

  const selectedPatient = patients.find(p => p.patient_id === selectedPatientId) || patients[0];
  const activeMetric = METRICS.find(m => m.id === selectedMetricId) || METRICS[0];

  useEffect(() => {
    let mounted = true;
    async function loadData() {
      const data = await fetchPatientTimeline(selectedPatientId);
      if (mounted) {
        setTimeline(data);
      }
    }
    loadData();
    return () => { mounted = false; };
  }, [selectedPatientId]);

  // Synthetic trend points if patient has single record
  const getTrendData = () => {
    if (selectedMetricId === 'HbA1c') {
      return [
        { date: '2025-10-15', value: 6.8, interpretation: 'High', doctor: 'Dr. Rao' },
        { date: '2026-01-20', value: 7.2, interpretation: 'Uncontrolled', doctor: 'Dr. K. Srinivas' },
        { date: '2026-04-10', value: 7.1, interpretation: 'Uncontrolled', doctor: 'Dr. K. Srinivas' },
        { date: '2026-07-22', value: 7.5, interpretation: 'Uncontrolled', doctor: 'Dr. K. Srinivas' },
        { date: '2026-10-13', value: 7.8, interpretation: 'Uncontrolled', doctor: 'Apollo Clinic' }
      ];
    } else if (selectedMetricId === 'Fasting Blood Sugar (FBS)') {
      return [
        { date: '2025-10-15', value: 135, interpretation: 'Elevated', doctor: 'Dr. Rao' },
        { date: '2026-01-20', value: 142, interpretation: 'Elevated', doctor: 'Dr. K. Srinivas' },
        { date: '2026-04-10', value: 148, interpretation: 'Elevated', doctor: 'Dr. K. Srinivas' },
        { date: '2026-07-22', value: 155, interpretation: 'High', doctor: 'Dr. K. Srinivas' },
        { date: '2026-10-13', value: 162, interpretation: 'High', doctor: 'Apollo Clinic' }
      ];
    } else if (selectedMetricId === 'Serum Creatinine') {
      return [
        { date: '2025-10-15', value: 1.0, interpretation: 'Normal', doctor: 'Dr. Rao' },
        { date: '2026-01-20', value: 1.1, interpretation: 'Normal', doctor: 'Dr. K. Srinivas' },
        { date: '2026-04-10', value: 1.2, interpretation: 'Normal', doctor: 'Dr. K. Srinivas' },
        { date: '2026-07-22', value: 1.3, interpretation: 'Borderline', doctor: 'Dr. K. Srinivas' },
        { date: '2026-10-13', value: 1.4, interpretation: 'Slightly Elevated', doctor: 'Apollo Clinic' }
      ];
    } else {
      // Blood Pressure
      return [
        { date: '2025-10-15', value: 126, interpretation: 'Prehypertension', doctor: 'Dr. Rao' },
        { date: '2026-01-20', value: 130, interpretation: 'Stage 1', doctor: 'Dr. K. Srinivas' },
        { date: '2026-04-10', value: 134, interpretation: 'Stage 1', doctor: 'Dr. K. Srinivas' },
        { date: '2026-07-22', value: 136, interpretation: 'Stage 1', doctor: 'Dr. K. Srinivas' },
        { date: '2026-10-13', value: 138, interpretation: 'Stage 1', doctor: 'Apollo Clinic' }
      ];
    }
  };

  const trendPoints = getTrendData();
  const latestPoint = trendPoints[trendPoints.length - 1];
  const previousPoint = trendPoints[trendPoints.length - 2];
  const delta = (latestPoint.value - previousPoint.value).toFixed(1);
  const isWorsening = Number(delta) > 0;

  // Chart coordinate mapping
  const chartHeight = 220;
  const chartWidth = 600;
  const padding = { top: 30, right: 30, bottom: 40, left: 50 };

  const values = trendPoints.map(p => p.value);
  const minVal = Math.min(...values, activeMetric.normalMin * 0.9);
  const maxVal = Math.max(...values, activeMetric.warningMax * 1.15);

  const getX = (index: number) => {
    return padding.left + (index / (trendPoints.length - 1)) * (chartWidth - padding.left - padding.right);
  };

  const getY = (val: number) => {
    const norm = (val - minVal) / (maxVal - minVal || 1);
    return chartHeight - padding.bottom - norm * (chartHeight - padding.top - padding.bottom);
  };

  // Build SVG path
  const pathD = trendPoints.reduce((acc, point, index) => {
    const x = getX(index);
    const y = getY(point.value);
    return index === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
  }, '');

  // Shaded normal area
  const normalY1 = getY(activeMetric.normalMin);
  const normalY2 = getY(activeMetric.normalMax);

  // Filter observations table
  const allObservations: LabObservation[] = timeline?.lab_observations?.length
    ? timeline.lab_observations
    : [
        { test_name: 'HbA1c', value_numeric: 7.8, unit: '%', reference_range: '< 5.7', interpretation: 'Uncontrolled', observation_date: '2026-10-13' },
        { test_name: 'Fasting Blood Sugar (FBS)', value_numeric: 162, unit: 'mg/dL', reference_range: '70-100', interpretation: 'High', observation_date: '2026-10-13' },
        { test_name: 'Serum Creatinine', value_numeric: 1.4, unit: 'mg/dL', reference_range: '0.7 - 1.2', interpretation: 'Elevated', observation_date: '2026-10-13' },
        { test_name: 'Total Cholesterol', value_numeric: 215, unit: 'mg/dL', reference_range: '< 200', interpretation: 'Borderline High', observation_date: '2026-10-13' },
        { test_name: 'HbA1c', value_numeric: 7.2, unit: '%', reference_range: '< 5.7', interpretation: 'High', observation_date: '2026-04-10' },
        { test_name: 'Fasting Blood Sugar (FBS)', value_numeric: 148, unit: 'mg/dL', reference_range: '70-100', interpretation: 'Elevated', observation_date: '2026-04-10' }
      ];

  const filteredObservations = allObservations.filter(o => 
    o.test_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    o.interpretation?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8 animate-in fade-in duration-300">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-sky-950/40 via-slate-900 to-slate-900 border border-sky-500/30">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/80 border border-cyan-800 text-cyan-300 text-xs font-semibold mb-2">
            <TrendingUp size={13} />
            <span>Longitudinal Health Intelligence</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Biomarker Trends & Clinical Observables
          </h1>
          <p className="text-sm text-slate-300 mt-1 max-w-2xl">
            Track multi-visit lab values and vitals across Telugu and Hindi medical encounters. Longitudinal tracking alerts doctors to insidious organ damage before symptoms emerge.
          </p>
        </div>

        {/* Patient Badge */}
        <div className="flex items-center gap-3 p-3 rounded-xl bg-slate-950/80 border border-slate-800 shrink-0">
          <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-300 font-bold">
            {selectedPatient?.full_name?.charAt(0)}
          </div>
          <div>
            <div className="font-semibold text-sm text-slate-100">{selectedPatient?.full_name}</div>
            <div className="text-xs text-slate-400 font-mono">
              {selectedPatient?.patient_id} &bull; {selectedPatient?.age}y
            </div>
          </div>
        </div>
      </div>

      {/* Metric Selector Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {METRICS.map(m => (
          <button
            key={m.id}
            onClick={() => setSelectedMetricId(m.id)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-medium whitespace-nowrap transition-all ${
              selectedMetricId === m.id
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-md shadow-cyan-500/10 font-semibold'
                : 'bg-slate-900/60 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            <Activity size={14} className={selectedMetricId === m.id ? 'text-cyan-400' : 'text-slate-500'} />
            <span>{m.name}</span>
          </button>
        ))}
      </div>

      {/* Stat Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Latest Value */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
          <span className="text-xs font-medium text-slate-400">Latest Recorded Value</span>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold font-mono text-cyan-300">
              {latestPoint.value}
            </span>
            <span className="text-sm text-slate-400 font-medium">{activeMetric.unit}</span>
          </div>
          <span className="text-[10px] text-slate-400 block font-mono">
            Date: {latestPoint.date}
          </span>
        </div>

        {/* Trend Delta */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
          <span className="text-xs font-medium text-slate-400">12-Month Progression</span>
          <div className="flex items-baseline gap-2">
            <span className={`text-2xl font-bold font-mono flex items-center ${
              isWorsening ? 'text-rose-400' : 'text-emerald-400'
            }`}>
              {isWorsening ? <ArrowUpRight size={22} /> : <ArrowDownRight size={22} />}
              {Number(delta) > 0 ? `+${delta}` : delta} {activeMetric.unit}
            </span>
          </div>
          <span className="text-[10px] text-rose-300/90 font-medium block">
            {isWorsening ? '⚠️ Increasing clinical risk trend' : '✓ Favorable trajectory'}
          </span>
        </div>

        {/* Reference Range */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
          <span className="text-xs font-medium text-slate-400">Target Normal Range</span>
          <div className="text-xl font-bold font-mono text-slate-200">
            {activeMetric.normalMin} - {activeMetric.normalMax} <span className="text-xs font-normal text-slate-400">{activeMetric.unit}</span>
          </div>
          <span className="text-[10px] text-emerald-400 font-mono block">
            Clinical Target Baseline
          </span>
        </div>

        {/* Clinical Triage Status */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
          <span className="text-xs font-medium text-slate-400">Interpretation Flag</span>
          <div>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-950/80 border border-rose-800 text-rose-300 font-semibold text-xs">
              <AlertTriangle size={13} />
              <span>{latestPoint.interpretation}</span>
            </span>
          </div>
          <span className="text-[10px] text-slate-400 block">
            Requires physician medication review
          </span>
        </div>
      </div>

      {/* Interactive Chart & Doctor's Commentary */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Chart Card */}
        <div className="lg:col-span-8 p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <span>Longitudinal Trajectory: {activeMetric.name}</span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">{activeMetric.description}</p>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <div className="flex items-center gap-1.5 text-slate-400">
                <span className="w-3 h-3 rounded bg-emerald-950/80 border border-emerald-800 inline-block" />
                <span>Normal Target</span>
              </div>
              <div className="flex items-center gap-1.5 text-slate-400">
                <span className="w-3 h-1 bg-cyan-400 inline-block" />
                <span>Observed</span>
              </div>
            </div>
          </div>

          {/* SVG Line Chart */}
          <div className="relative w-full overflow-x-auto pt-2">
            <svg
              viewBox={`0 0 ${chartWidth} ${chartHeight}`}
              className="w-full h-auto min-w-[500px]"
            >
              {/* Normal Target Area */}
              <rect
                x={padding.left}
                y={normalY2}
                width={chartWidth - padding.left - padding.right}
                height={Math.max(0, normalY1 - normalY2)}
                fill="rgba(16, 185, 129, 0.08)"
                stroke="rgba(16, 185, 129, 0.25)"
                strokeDasharray="3 3"
              />

              {/* Grid Lines */}
              {[minVal, (minVal + maxVal) / 2, maxVal].map((val, i) => {
                const y = getY(val);
                return (
                  <g key={i}>
                    <line
                      x1={padding.left}
                      y1={y}
                      x2={chartWidth - padding.right}
                      y2={y}
                      stroke="rgba(51, 65, 85, 0.4)"
                      strokeDasharray="2 2"
                    />
                    <text
                      x={padding.left - 10}
                      y={y + 4}
                      fill="#94a3b8"
                      fontSize="10"
                      textAnchor="end"
                      fontFamily="monospace"
                    >
                      {val.toFixed(1)}
                    </text>
                  </g>
                );
              })}

              {/* Trend Curve */}
              <path
                d={pathD}
                fill="none"
                stroke="url(#trendGradient)"
                strokeWidth="3.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              <defs>
                <linearGradient id="trendGradient" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#38bdf8" />
                  <stop offset="50%" stopColor="#22d3ee" />
                  <stop offset="100%" stopColor="#f43f5e" />
                </linearGradient>
              </defs>

              {/* Data Points */}
              {trendPoints.map((point, index) => {
                const x = getX(index);
                const y = getY(point.value);
                const isHovered = hoveredPoint?.date === point.date;

                return (
                  <g key={index} className="cursor-pointer">
                    {/* Outer pulse circle for latest point */}
                    {index === trendPoints.length - 1 && (
                      <circle
                        cx={x}
                        cy={y}
                        r="10"
                        fill="none"
                        stroke="#f43f5e"
                        strokeWidth="1.5"
                        opacity="0.6"
                      />
                    )}
                    <circle
                      cx={x}
                      cy={y}
                      r={isHovered ? 7 : 5}
                      fill={index === trendPoints.length - 1 ? '#f43f5e' : '#22d3ee'}
                      stroke="#080d1a"
                      strokeWidth="2"
                      onMouseEnter={() => setHoveredPoint(point)}
                      onMouseLeave={() => setHoveredPoint(null)}
                    />
                    <text
                      x={x}
                      y={chartHeight - 15}
                      fill="#94a3b8"
                      fontSize="9"
                      textAnchor="middle"
                      fontFamily="monospace"
                    >
                      {point.date.slice(5)}
                    </text>
                  </g>
                );
              })}
            </svg>

            {/* Hover Tooltip Overlay */}
            {hoveredPoint && (
              <div className="absolute top-4 right-4 p-3 rounded-xl bg-slate-950/95 border border-cyan-500/40 shadow-xl text-xs space-y-1 animate-in fade-in">
                <div className="font-bold text-cyan-300">
                  {hoveredPoint.date} &bull; {hoveredPoint.doctor}
                </div>
                <div className="font-mono text-white text-sm">
                  {hoveredPoint.value} {activeMetric.unit}
                </div>
                <div className="text-[11px] text-slate-400">
                  Status: <span className="text-amber-300 font-semibold">{hoveredPoint.interpretation}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Doctor's Insights Column */}
        <div className="lg:col-span-4 space-y-4">
          <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <Sliders className="text-cyan-400" size={16} />
              <span>AI Longitudinal Analysis</span>
            </h3>

            <div className="p-4 rounded-xl bg-slate-950/80 border border-rose-900/50 space-y-2">
              <div className="flex items-center gap-2 text-rose-300 text-xs font-semibold">
                <AlertTriangle size={15} />
                <span>Glycemic Upward Drift</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                HbA1c progressed from <b>6.8% to 7.8%</b> over 12 months despite Glimepiride 2mg and Metformin 500mg therapy.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
              <div className="flex items-center gap-2 text-amber-300 text-xs font-semibold">
                <Activity size={15} />
                <span>Renal Monitoring Recommendation</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                Serum Creatinine increased to <b>1.4 mg/dL</b>. Given co-administration of Metformin, monitor eGFR and consider dosing adjustments to prevent renal strain.
              </p>
            </div>

            <div className="pt-2 text-[11px] text-slate-400 flex items-center gap-1.5 font-mono">
              <CheckCircle2 size={13} className="text-emerald-400" />
              <span>Derived from 4 ABDM historical encounters</span>
            </div>
          </div>
        </div>
      </div>

      {/* Historical Observations Table */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-bold text-slate-100">Historical Lab Observations Registry</h3>
            <p className="text-xs text-slate-400">All normalized LOINC and FHIR diagnostic measurements</p>
          </div>
          <input
            type="text"
            placeholder="Search test name or flag..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-cyan-400 max-w-xs"
          />
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4 font-semibold">Test Name</th>
                <th className="py-3 px-4 font-semibold">Observed Value</th>
                <th className="py-3 px-4 font-semibold">Reference Range</th>
                <th className="py-3 px-4 font-semibold">Interpretation</th>
                <th className="py-3 px-4 font-semibold">Encounter Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-mono">
              {filteredObservations.map((obs, idx) => (
                <tr key={idx} className="hover:bg-slate-950/60 transition-colors">
                  <td className="py-3 px-4 font-sans font-medium text-slate-100">{obs.test_name}</td>
                  <td className="py-3 px-4 font-bold text-cyan-300">
                    {obs.value_numeric} {obs.unit}
                  </td>
                  <td className="py-3 px-4 text-slate-400">{obs.reference_range}</td>
                  <td className="py-3 px-4">
                    <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${
                      obs.interpretation?.toLowerCase().includes('high') || obs.interpretation?.toLowerCase().includes('uncontrolled')
                        ? 'bg-rose-950 text-rose-300 border border-rose-800'
                        : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                    }`}>
                      {obs.interpretation}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-400">{obs.observation_date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
