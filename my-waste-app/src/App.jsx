import React, { useState, useEffect } from 'react';
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
  Cpu
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = "http://localhost:8000";

const App = () => {
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState({ arduino: false, camera: false });
  const [data, setData] = useState({
    baseWeight: 0,
    capturedImage: null,
    classification: null,
    wasteType: null,
    result: null
  });
  const [error, setError] = useState(null);

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const checkStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/status`);
      const d = await res.json();
      setStatus({ arduino: d.arduino_connected, camera: d.camera_available });
    } catch (e) {
      setStatus({ arduino: false, camera: false });
    }
  };

  const handleAction = async (endpoint, nextStep, dataKey) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/${endpoint}`, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: step === 3 ? JSON.stringify({ type: data.wasteType }) : undefined
      });
      if (!res.ok) throw new Error(await res.text());
      const result = await res.json();
      
      if (dataKey === 'all') {
        setData(prev => ({ ...prev, ...result }));
      } else if (dataKey === 'classification') {
        setData(prev => ({ ...prev, classification: result.category, wasteType: result.type }));
      } else {
        setData(prev => ({ ...prev, [dataKey]: result.weight || result.image }));
      }
      
      setStep(nextStep);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setStep(0);
    setData({ baseWeight: 0, capturedImage: null, classification: null, wasteType: null, result: null });
  };

  const StepCard = ({ title, icon: Icon, children, active }) => (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className={`p-6 rounded-2xl border ${active ? 'bg-white/10 border-blue-500 shadow-lg shadow-blue-500/20' : 'bg-white/5 border-white/10 opacity-50'}`}
    >
      <div className="flex items-center gap-4 mb-4">
        <div className={`p-3 rounded-xl ${active ? 'bg-blue-500 text-white' : 'bg-white/10 text-gray-400'}`}>
          <Icon size={24} />
        </div>
        <h3 className="text-xl font-semibold text-white">{title}</h3>
      </div>
      {active && children}
    </motion.div>
  );

  return (
    <div className="min-h-screen bg-[#0a0a0c] text-slate-200 font-sans selection:bg-blue-500/30">
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
        
        <div className="flex gap-4">
          <StatusBadge icon={Cpu} label="Hardware" online={status.arduino} />
          <StatusBadge icon={Database} label="Cloud" online={true} />
        </div>
      </nav>

      <main className="relative z-10 max-w-5xl mx-auto px-6 py-12">
        {error && (
          <motion.div 
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            className="mb-8 p-4 bg-red-500/10 border border-red-500/50 rounded-xl flex items-center gap-3 text-red-400"
          >
            <AlertCircle size={20} />
            <span className="text-sm font-medium">{error}</span>
          </motion.div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="space-y-6">
            <StepCard title="Step 1: Calibration" icon={Scale} active={step === 0}>
              <p className="text-slate-400 mb-6">Resetting scale to zero to ensure accurate measurement.</p>
              <button 
                onClick={() => handleAction('measure-base', 1, 'baseWeight')}
                disabled={loading || !status.arduino}
                className="w-full py-4 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 rounded-xl font-bold flex items-center justify-center gap-2 transition-all"
              >
                {loading ? <Loader2 className="animate-spin" /> : 'Calibrate Scale'}
                <ChevronRight size={18} />
              </button>
            </StepCard>

            <StepCard title="Step 2: Analysis" icon={Camera} active={step === 1}>
              <p className="text-slate-400 mb-6">Analyzing the waste item using Gemini Pro Vision.</p>
              <button 
                onClick={() => handleAction('capture', 2, 'capturedImage')}
                disabled={loading}
                className="w-full py-4 bg-white text-black hover:bg-gray-200 rounded-xl font-bold flex items-center justify-center gap-2 transition-all"
              >
                {loading ? <Loader2 className="animate-spin" /> : 'Capture & Identify'}
              </button>
            </StepCard>

            <StepCard title="Step 3: Sorting" icon={Recycle} active={step === 2 || step === 3}>
              {step === 2 ? (
                <>
                  <div className="mb-4 p-4 bg-blue-500/10 rounded-xl border border-blue-500/20">
                    <span className="text-xs uppercase tracking-widest text-blue-400 font-bold">Classification</span>
                    <p className="text-xl font-medium text-white capitalize">{data.classification || 'Detecting...'}</p>
                  </div>
                  <button 
                    onClick={() => handleAction('classify', 3, 'classification')}
                    disabled={loading}
                    className="w-full py-4 bg-emerald-600 hover:bg-emerald-500 rounded-xl font-bold flex items-center justify-center gap-2 transition-all"
                  >
                    {loading ? <Loader2 className="animate-spin" /> : 'Confirm Classification'}
                  </button>
                </>
              ) : (
                <button 
                   onClick={() => handleAction('process-waste', 4, 'result')}
                   disabled={loading}
                   className="w-full py-4 bg-indigo-600 hover:bg-indigo-500 rounded-xl font-bold flex items-center justify-center gap-2 transition-all"
                >
                  {loading ? <Loader2 className="animate-spin" /> : 'Execute Sorting'}
                </button>
              )}
            </StepCard>
          </div>

          <div className="sticky top-12">
            <AnimatePresence mode="wait">
              {step < 4 ? (
                <motion.div 
                  key="preview"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className="aspect-square rounded-3xl overflow-hidden bg-white/5 border border-white/10 flex items-center justify-center relative group"
                >
                  {data.capturedImage ? (
                    <img src={`data:image/jpeg;base64,${data.capturedImage}`} className="w-full h-full object-cover" alt="Captured" />
                  ) : (
                    <div className="text-center text-slate-500 group-hover:text-blue-400 transition-colors">
                      <Camera size={64} className="mx-auto mb-4 opacity-20" />
                      <p className="font-medium">Live Feed Waiting...</p>
                    </div>
                  )}
                  {loading && (
                    <div className="absolute inset-0 bg-black/60 backdrop-blur-sm flex flex-col items-center justify-center">
                      <Loader2 className="animate-spin text-blue-500 mb-2" size={32} />
                      <p className="text-sm font-bold tracking-widest text-blue-500 uppercase">Processing</p>
                    </div>
                  )}
                </motion.div>
              ) : (
                <motion.div 
                  key="result"
                  initial={{ opacity: 0, x: 50 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="bg-gradient-to-br from-emerald-500/10 to-blue-500/10 border border-white/10 rounded-3xl p-8 text-center"
                >
                  <div className="w-20 h-20 bg-emerald-500 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg shadow-emerald-500/30">
                    <CheckCircle2 size={40} className="text-white" />
                  </div>
                  <h2 className="text-3xl font-bold text-white mb-2">Success!</h2>
                  <p className="text-slate-400 mb-8">Waste sorted and reward generated.</p>
                  
                  <div className="grid grid-cols-2 gap-4 mb-8">
                    <div className="bg-white/5 p-4 rounded-2xl border border-white/10">
                      <p className="text-slate-500 text-xs uppercase font-bold mb-1">Weight</p>
                      <p className="text-2xl font-bold text-white">{data.result?.weight}g</p>
                    </div>
                    <div className="bg-white/5 p-4 rounded-2xl border border-white/10">
                      <p className="text-slate-500 text-xs uppercase font-bold mb-1">Reward</p>
                      <p className="text-2xl font-bold text-emerald-400">₹{data.result?.amount}</p>
                    </div>
                  </div>

                  <div className="bg-white p-4 rounded-2xl inline-block mb-8">
                    {data.result?.qr_code && (
                      <img src={`data:image/png;base64,${data.result.qr_code}`} alt="QR" className="w-40 h-40" />
                    )}
                    <p className="text-black text-[10px] font-mono mt-2 font-bold">{data.result?.id}</p>
                  </div>

                  <button 
                    onClick={reset}
                    className="w-full py-4 bg-white/10 hover:bg-white/20 rounded-xl font-bold text-white transition-all"
                  >
                    Start New Process
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
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