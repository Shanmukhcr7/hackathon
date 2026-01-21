import React, { useState, useEffect, useCallback } from 'react';
import { 
  Recycle, 
  Camera, 
  Scale, 
  Wallet, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  ChevronRight,
  Database,
  Cpu,
  RefreshCcw,
  Zap
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Mock API Base - In a real scenario, this would point to your local backend
const API_BASE = "http://localhost:8000";

const App = () => {
  const [step, setStep] = useState(0); // 0: Idle, 1: Calibrating, 2: Camera Timer, 3: Analysis, 4: Sorting, 5: Result
  const [countdown, setCountdown] = useState(10);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState({ arduino: true, camera: true });
  const [data, setData] = useState({
    baseWeight: 0,
    capturedImage: null,
    classification: null,
    wasteType: null,
    result: null
  });
  const [error, setError] = useState(null);

  // Status check effect
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch(`${API_BASE}/status`);
        const d = await res.json();
        setStatus({ arduino: d.arduino_connected, camera: d.camera_available });
      } catch (e) {
        // Fallback for demo purposes
        setStatus({ arduino: true, camera: true });
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  // Timer Effect for Step 2 (Camera Preparation)
  useEffect(() => {
    let timer;
    if (step === 2 && countdown > 0) {
      timer = setInterval(() => {
        setCountdown(prev => prev - 1);
      }, 1000);
    } else if (step === 2 && countdown === 0) {
      executeCapture();
    }
    return () => clearInterval(timer);
  }, [step, countdown]);

  const reset = () => {
    setStep(0);
    setCountdown(10);
    setData({ baseWeight: 0, capturedImage: null, classification: null, wasteType: null, result: null });
    setError(null);
  };

  const startProcess = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Start Calibration
      setStep(1);
      const res = await fetch(`${API_BASE}/measure-base`, { method: 'POST' });
      const result = await res.json();
      setData(prev => ({ ...prev, baseWeight: result.weight }));
      
      // 2. Start Camera Timer
      setLoading(false);
      setStep(2);
    } catch (e) {
      setError("Calibration Failed: Ensure hardware is connected.");
      setLoading(false);
      setStep(0);
    }
  };

  const executeCapture = async () => {
    setLoading(true);
    setStep(3);
    try {
      // 3. Capture and Classify
      const res = await fetch(`${API_BASE}/capture`, { method: 'POST' });
      const result = await res.json();
      setData(prev => ({ ...prev, capturedImage: result.image }));

      const classRes = await fetch(`${API_BASE}/classify`, { method: 'POST' });
      const classData = await classRes.json();
      setData(prev => ({ ...prev, classification: classData.category, wasteType: classData.type }));

      // 4. Process/Sort automatically
      setStep(4);
      const sortRes = await fetch(`${API_BASE}/process-waste`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: classData.type })
      });
      const sortResult = await sortRes.json();
      setData(prev => ({ ...prev, result: sortResult }));
      
      setStep(5);
    } catch (e) {
      setError("Processing Interrupted: " + e.message);
      setStep(0);
    } finally {
      setLoading(false);
    }
  };

  const getButtonState = () => {
    if (step === 0) return { label: "Start Recycling Process", color: "bg-blue-600 hover:bg-blue-500", icon: Zap };
    if (step === 1) return { label: "Calibrating Scale...", color: "bg-gray-700", icon: Loader2, disabled: true };
    if (step === 2) return { label: `Get Ready (${countdown}s)`, color: "bg-amber-500", icon: Camera };
    if (step === 3) return { label: "Analyzing Object...", color: "bg-indigo-600", icon: Cpu, disabled: true };
    if (step === 4) return { label: "Sorting Waste...", color: "bg-emerald-600", icon: Recycle, disabled: true };
    if (step === 5) return { label: "New Item", color: "bg-white text-black", icon: RefreshCcw };
    return { label: "Error", color: "bg-red-600", icon: AlertCircle };
  };

  const btn = getButtonState();

  return (
    <div className="min-h-screen bg-[#0a0a0c] text-slate-200 font-sans selection:bg-blue-500/30 overflow-x-hidden">
      {/* Background Decor */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/10 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-emerald-600/10 blur-[120px] rounded-full" />
      </div>

      <nav className="relative z-10 border-b border-white/5 bg-black/20 backdrop-blur-xl px-8 py-4 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="bg-gradient-to-br from-blue-500 to-emerald-500 p-2 rounded-lg">
            <Recycle className="text-white" size={24} />
          </div>
          <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-500">
            SmartRecycle AI
          </span>
        </div>
        
        <div className="hidden sm:flex gap-4">
          <StatusBadge icon={Cpu} label="Hardware" online={status.arduino} />
          <StatusBadge icon={Database} label="Cloud" online={true} />
        </div>
      </nav>

      <main className="relative z-10 max-w-4xl mx-auto px-6 py-12 flex flex-col items-center">
        {error && (
          <motion.div 
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            className="w-full mb-8 p-4 bg-red-500/10 border border-red-500/50 rounded-xl flex items-center gap-3 text-red-400"
          >
            <AlertCircle size={20} />
            <span className="text-sm font-medium">{error}</span>
          </motion.div>
        )}

        <div className="w-full grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Display Side */}
          <div className="relative group w-full aspect-square">
            <AnimatePresence mode="wait">
              {step === 5 ? (
                <motion.div 
                  key="result-pane"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="w-full h-full bg-gradient-to-br from-emerald-500/20 to-blue-500/20 border border-white/10 rounded-3xl p-8 flex flex-col items-center justify-center text-center shadow-2xl"
                >
                  <div className="w-20 h-20 bg-emerald-500 rounded-full flex items-center justify-center mb-6 shadow-lg shadow-emerald-500/30">
                    <CheckCircle2 size={40} className="text-white" />
                  </div>
                  <h2 className="text-3xl font-bold text-white mb-2">Sorted!</h2>
                  <div className="grid grid-cols-2 gap-4 w-full mt-4">
                    <div className="bg-white/5 p-4 rounded-2xl border border-white/10">
                      <p className="text-slate-500 text-[10px] uppercase font-bold mb-1">Weight</p>
                      <p className="text-xl font-bold text-white">{data.result?.weight || '0'}g</p>
                    </div>
                    <div className="bg-white/5 p-4 rounded-2xl border border-white/10">
                      <p className="text-slate-500 text-[10px] uppercase font-bold mb-1">Reward</p>
                      <p className="text-xl font-bold text-emerald-400">₹{data.result?.amount || '0'}</p>
                    </div>
                  </div>
                  {data.result?.qr_code && (
                    <div className="mt-6 bg-white p-3 rounded-2xl">
                      <img src={`data:image/png;base64,${data.result.qr_code}`} alt="QR" className="w-32 h-32" />
                    </div>
                  )}
                </motion.div>
              ) : (
                <motion.div 
                  key="viewfinder"
                  className="w-full h-full rounded-3xl overflow-hidden bg-white/5 border border-white/10 flex items-center justify-center relative shadow-2xl"
                >
                  {data.capturedImage ? (
                    <img src={`data:image/jpeg;base64,${data.capturedImage}`} className="w-full h-full object-cover" alt="Captured" />
                  ) : (
                    <div className="text-center text-slate-500">
                      <Camera size={64} className={`mx-auto mb-4 transition-all duration-700 ${step === 2 ? 'text-amber-500 scale-125' : 'opacity-20'}`} />
                      <p className="font-medium">{step === 2 ? 'Position your waste item...' : 'Waiting to start'}</p>
                    </div>
                  )}
                  
                  {step === 2 && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/40">
                      <span className="text-9xl font-black text-white drop-shadow-2xl animate-pulse">{countdown}</span>
                    </div>
                  )}

                  {loading && step !== 2 && (
                    <div className="absolute inset-0 bg-black/60 backdrop-blur-sm flex flex-col items-center justify-center">
                      <Loader2 className="animate-spin text-blue-500 mb-2" size={48} />
                      <p className="text-sm font-bold tracking-widest text-blue-500 uppercase">Processing</p>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Action Side */}
          <div className="flex flex-col gap-8">
            <div className="space-y-4">
               <h1 className="text-4xl font-extrabold text-white leading-tight">
                Recycle with <span className="text-blue-500">Intelligence.</span>
               </h1>
               <p className="text-slate-400 text-lg">
                 Place your waste item on the tray and click the button below. Our AI will handle the rest.
               </p>
            </div>

            <div className="space-y-6">
              <div className="flex flex-col gap-3">
                <div className={`flex items-center gap-4 p-4 rounded-2xl border transition-all ${step === 1 ? 'bg-blue-500/10 border-blue-500' : 'bg-white/5 border-white/5 opacity-50'}`}>
                  <Scale size={20} className={step === 1 ? 'text-blue-400' : 'text-slate-500'} />
                  <span className="font-medium text-sm">Hardware Calibration</span>
                </div>
                <div className={`flex items-center gap-4 p-4 rounded-2xl border transition-all ${step === 2 ? 'bg-amber-500/10 border-amber-500' : 'bg-white/5 border-white/5 opacity-50'}`}>
                  <Camera size={20} className={step === 2 ? 'text-amber-400' : 'text-slate-500'} />
                  <span className="font-medium text-sm">Visual Analysis (10s Prep)</span>
                </div>
                <div className={`flex items-center gap-4 p-4 rounded-2xl border transition-all ${step === 4 ? 'bg-emerald-500/10 border-emerald-500' : 'bg-white/5 border-white/5 opacity-50'}`}>
                  <Recycle size={20} className={step === 4 ? 'text-emerald-400' : 'text-slate-500'} />
                  <span className="font-medium text-sm">Automated Sorting</span>
                </div>
              </div>

              <button 
                onClick={step === 5 ? reset : startProcess}
                disabled={btn.disabled || !status.arduino}
                className={`w-full py-5 ${btn.color} rounded-2xl font-black text-xl flex items-center justify-center gap-3 shadow-xl transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed group`}
              >
                {btn.icon === Loader2 ? <Loader2 className="animate-spin" size={24} /> : <btn.icon size={24} className="group-hover:rotate-12 transition-transform" />}
                {btn.label}
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

const StatusBadge = ({ icon: Icon, label, online }) => (
  <div className="flex items-center gap-2 bg-white/5 px-3 py-1.5 rounded-full border border-white/10">
    <Icon size={14} className={online ? 'text-emerald-500' : 'text-red-500'} />
    <span className="text-xs font-medium text-slate-300">{label}</span>
    <div className={`w-1.5 h-1.5 rounded-full ${online ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-red-500'}`} />
  </div>
);

export default App;
