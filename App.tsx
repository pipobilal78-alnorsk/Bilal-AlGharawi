
import React, { useState, useEffect } from 'react';
import { 
  Home, 
  MapPin, 
  Image as ImageIcon, 
  MessageSquare, 
  Menu, 
  X, 
  Search,
  ChevronLeft,
  TrendingUp,
  History,
  Palmtree,
  Sparkles,
  Download
} from 'lucide-react';
import { LANDMARKS, ECONOMIC_DATA } from './constants';
import { geminiService } from './services/geminiService';
import { ChatMessage } from './types';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const SplashScreen: React.FC<{ onComplete: () => void }> = ({ onComplete }) => {
  useEffect(() => {
    const timer = setTimeout(() => onComplete(), 3300);
    return () => clearTimeout(timer);
  }, [onComplete]);

  return (
    <div className="fixed inset-0 z-[100] bg-emerald-900 flex flex-col items-center justify-center splash-fade-out">
      <div className="relative">
        <div className="absolute inset-0 bg-white/20 blur-3xl rounded-full scale-150 animate-pulse"></div>
        <Palmtree className="text-white relative z-10 animate-bounce" size={80} />
      </div>
      <h1 className="text-white text-4xl md:text-5xl font-black mt-8 tracking-widest glow-text animate-pulse">
        Pipo Al-Gharawi
      </h1>
      <div className="mt-4 flex items-center gap-2 text-emerald-200/80 tracking-[0.3em] font-light">
        <Sparkles size={16} />
        <span>KUWAIT EXPLORER</span>
        <Sparkles size={16} />
      </div>
      <div className="absolute bottom-12 w-48 h-1 bg-white/10 rounded-full overflow-hidden">
        <div className="h-full bg-emerald-400 w-full animate-[shimmer_3s_infinite] origin-left scale-x-0 group-hover:scale-x-100 transition-transform" 
             style={{ animation: 'loading 3s ease-in-out forwards' }}></div>
      </div>
      <style>{`
        @keyframes loading {
          0% { transform: scaleX(0); }
          100% { transform: scaleX(1); }
        }
      `}</style>
    </div>
  );
};

const App: React.FC = () => {
  const [showSplash, setShowSplash] = useState(true);
  const [activeTab, setActiveTab] = useState<'home' | 'landmarks' | 'gallery' | 'chat'>('home');
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [generatedImages, setGeneratedImages] = useState<string[]>([]);
  const [userLocation, setUserLocation] = useState<{ lat: number, lng: number } | null>(null);

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setUserLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        () => console.log("Geolocation blocked")
      );
    }
    
    setChatMessages([{
      role: 'model',
      text: 'مرحباً بك في دليل الكويت الشامل! أنا مساعدك الذكي المطور بواسطة Pipo Al-Gharawi. كيف أخدمك اليوم؟'
    }]);
  }, []);

  const handleSendMessage = async () => {
    if (!chatInput.trim()) return;
    const userMsg = chatInput;
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setIsLoading(true);
    try {
      const response = await geminiService.askAboutKuwait(userMsg, userLocation ? { latitude: userLocation.lat, longitude: userLocation.lng } : undefined);
      setChatMessages(prev => [...prev, { role: 'model', text: response.text || 'عذراً، حدث خطأ ما.' }]);
    } catch (error) {
      setChatMessages(prev => [...prev, { role: 'model', text: 'حدث خطأ في الاتصال. حاول مرة أخرى.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateImage = async (prompt: string) => {
    setIsLoading(true);
    try {
      const img = await geminiService.generateKuwaitImage(prompt);
      if (img) setGeneratedImages(prev => [img, ...prev]);
    } catch (error) {
      alert("فشل إنشاء الصورة");
    } finally {
      setIsLoading(false);
    }
  };

  if (showSplash) {
    return <SplashScreen onComplete={() => setShowSplash(false)} />;
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 animate-in fade-in duration-1000">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 glass-effect border-b border-slate-200 px-4 py-3">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="bg-emerald-600 p-2 rounded-lg shadow-lg">
              <Palmtree className="text-white" size={24} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-800 leading-none">الكويت <span className="text-emerald-600">Explore</span></h1>
              <span className="text-[10px] text-slate-400 font-medium">By Pipo Al-Gharawi</span>
            </div>
          </div>

          <div className="hidden md:flex gap-6">
            <button onClick={() => setActiveTab('home')} className={`flex items-center gap-2 px-3 py-2 rounded-lg transition ${activeTab === 'home' ? 'bg-emerald-50 text-emerald-700' : 'text-slate-600 hover:bg-slate-100'}`}>
              <Home size={20} /> الرئيسية
            </button>
            <button onClick={() => setActiveTab('landmarks')} className={`flex items-center gap-2 px-3 py-2 rounded-lg transition ${activeTab === 'landmarks' ? 'bg-emerald-50 text-emerald-700' : 'text-slate-600 hover:bg-slate-100'}`}>
              <MapPin size={20} /> المعالم
            </button>
            <button onClick={() => setActiveTab('gallery')} className={`flex items-center gap-2 px-3 py-2 rounded-lg transition ${activeTab === 'gallery' ? 'bg-emerald-50 text-emerald-700' : 'text-slate-600 hover:bg-slate-100'}`}>
              <ImageIcon size={20} /> المعرض
            </button>
            <button onClick={() => setActiveTab('chat')} className={`flex items-center gap-2 px-3 py-2 rounded-lg transition ${activeTab === 'chat' ? 'bg-emerald-50 text-emerald-700' : 'text-slate-600 hover:bg-slate-100'}`}>
              <MessageSquare size={20} /> المساعد الذكي
            </button>
          </div>

          <div className="flex items-center gap-4">
             <button className="hidden lg:flex items-center gap-2 text-xs font-bold text-slate-500 hover:text-emerald-600 transition">
               <Download size={16} /> تثبيت التطبيق
             </button>
            <button className="md:hidden text-slate-600" onClick={() => setIsMenuOpen(!isMenuOpen)}>
              {isMenuOpen ? <X size={28} /> : <Menu size={28} />}
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="md:hidden fixed inset-0 z-40 bg-white pt-20 px-6 flex flex-col gap-4">
          <button onClick={() => { setActiveTab('home'); setIsMenuOpen(false); }} className="text-lg font-medium p-4 border-b border-slate-100 flex items-center gap-3"><Home /> الرئيسية</button>
          <button onClick={() => { setActiveTab('landmarks'); setIsMenuOpen(false); }} className="text-lg font-medium p-4 border-b border-slate-100 flex items-center gap-3"><MapPin /> المعالم السياحية</button>
          <button onClick={() => { setActiveTab('gallery'); setIsMenuOpen(false); }} className="text-lg font-medium p-4 border-b border-slate-100 flex items-center gap-3"><ImageIcon /> معرض الصور</button>
          <button onClick={() => { setActiveTab('chat'); setIsMenuOpen(false); }} className="text-lg font-medium p-4 border-b border-slate-100 flex items-center gap-3"><MessageSquare /> المساعد الذكي</button>
        </div>
      )}

      {/* Main Content Areas (Same as previous but with better transitions) */}
      <main className="flex-grow max-w-7xl mx-auto w-full px-4 py-8">
        {activeTab === 'home' && (
          <div className="space-y-12 animate-in fade-in slide-in-from-top-4 duration-700">
            {/* Hero */}
            <section className="relative h-[450px] rounded-[2rem] overflow-hidden shadow-2xl flex items-center justify-center text-center">
              <img src="https://images.unsplash.com/photo-1549488344-1f9b8d2bd1f3?q=80&w=2000&auto=format&fit=crop" className="absolute inset-0 w-full h-full object-cover" alt="Kuwait City" />
              <div className="absolute inset-0 bg-gradient-to-t from-emerald-950/90 via-black/40 to-transparent" />
              <div className="relative z-10 px-6 max-w-3xl">
                <div className="inline-flex items-center gap-2 bg-emerald-500/20 backdrop-blur-md px-4 py-1 rounded-full text-emerald-300 text-sm font-bold mb-6 border border-emerald-500/30">
                  <Sparkles size={14} /> مطور بواسطة Pipo Al-Gharawi
                </div>
                <h2 className="text-4xl md:text-7xl font-black text-white mb-6 leading-tight">لؤلؤة الخليج <br/> بلمسة ذكاء اصطناعي</h2>
                <p className="text-lg md:text-xl text-slate-200 mb-8 font-medium">استكشف الكويت كما لم تراها من قبل عبر شاشة تطبيقك.</p>
                <div className="flex flex-wrap justify-center gap-4">
                  <button onClick={() => setActiveTab('landmarks')} className="bg-white text-emerald-900 hover:bg-emerald-50 px-10 py-4 rounded-2xl font-black shadow-xl transition transform hover:scale-105">اكتشف الآن</button>
                  <button onClick={() => setActiveTab('chat')} className="bg-emerald-600/20 hover:bg-emerald-600/40 text-white backdrop-blur-md px-10 py-4 rounded-2xl font-black border border-white/20 transition transform hover:scale-105">اسأل Pipo AI</button>
                </div>
              </div>
            </section>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                { icon: <History />, title: "تاريخ عريق", desc: "حضارة دلمون إلى العصر الحديث", color: "amber" },
                { icon: <TrendingUp />, title: "اقتصاد متصدر", desc: "أقوى عملة في العالم (KWD)", color: "blue" },
                { icon: <MapPin />, title: "وجهة سياحية", desc: "مزيج بين الحداثة والأصالة", color: "emerald" }
              ].map((stat, i) => (
                <div key={i} className="bg-white p-8 rounded-[2rem] shadow-sm border border-slate-100 hover:shadow-md transition group">
                  <div className={`bg-${stat.color}-100 w-16 h-16 rounded-2xl flex items-center justify-center text-${stat.color}-600 mb-6 group-hover:scale-110 transition`}>
                    {React.cloneElement(stat.icon as React.ReactElement, { size: 32 })}
                  </div>
                  <h3 className="font-bold text-slate-800 text-xl mb-2">{stat.title}</h3>
                  <p className="text-slate-500 text-sm leading-relaxed">{stat.desc}</p>
                </div>
              ))}
            </div>

            {/* Economic Chart */}
            <section className="bg-white p-8 md:p-12 rounded-[2.5rem] shadow-sm border border-slate-100">
              <div className="flex flex-col md:flex-row md:items-center justify-between mb-10 gap-4">
                <div>
                  <h3 className="text-2xl font-bold text-slate-800">قوة الاقتصاد الكويتي</h3>
                  <p className="text-slate-500 mt-1">الناتج المحلي الإجمالي بالمليارات (بيانات تقديرية)</p>
                </div>
                <div className="bg-emerald-50 px-4 py-2 rounded-xl text-emerald-700 font-bold text-sm flex items-center gap-2">
                  <TrendingUp size={18}/> نمو مستدام
                </div>
              </div>
              <div className="h-[350px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={ECONOMIC_DATA}>
                    <defs>
                      <linearGradient id="colorGdp" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#059669" stopOpacity={0.15}/>
                        <stop offset="95%" stopColor="#059669" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="year" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} dy={10} />
                    <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} dx={-10} />
                    <Tooltip 
                      contentStyle={{borderRadius: '20px', border: 'none', boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1)'}} 
                      itemStyle={{color: '#059669', fontWeight: 'bold'}}
                    />
                    <Area type="monotone" dataKey="gdp" stroke="#059669" strokeWidth={4} fillOpacity={1} fill="url(#colorGdp)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </section>
          </div>
        )}

        {/* Landmarks Tab */}
        {activeTab === 'landmarks' && (
          <div className="space-y-8 animate-in slide-in-from-bottom-8 duration-700">
            <div className="text-center max-w-2xl mx-auto mb-12">
              <h2 className="text-4xl font-black text-slate-800 mb-4">أهم الوجهات السياحية</h2>
              <p className="text-slate-500">أماكن يجب عليك زيارتها عند قدومك إلى دولة الكويت</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {LANDMARKS.map(landmark => (
                <div key={landmark.id} className="group bg-white rounded-[2rem] overflow-hidden shadow-sm hover:shadow-2xl transition-all duration-500 border border-slate-100 flex flex-col">
                  <div className="relative h-72 overflow-hidden">
                    <img src={landmark.imageUrl} alt={landmark.name} className="w-full h-full object-cover group-hover:scale-110 transition duration-700" />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                    <div className="absolute top-6 right-6 bg-white/95 backdrop-blur px-4 py-1.5 rounded-full text-xs font-black text-emerald-800 shadow-lg">{landmark.category}</div>
                  </div>
                  <div className="p-8 flex-grow flex flex-col">
                    <h3 className="text-2xl font-bold text-slate-800 mb-3">{landmark.name}</h3>
                    <p className="text-slate-500 mb-6 text-sm leading-relaxed flex-grow">{landmark.description}</p>
                    <button className="bg-slate-50 text-slate-700 font-bold py-3 rounded-xl hover:bg-emerald-600 hover:text-white transition-all flex items-center justify-center gap-2">
                      عرض الموقع <ChevronLeft size={18} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Gallery Tab */}
        {activeTab === 'gallery' && (
          <div className="space-y-10 animate-in fade-in duration-700">
            <div className="bg-emerald-900 rounded-[2.5rem] p-10 text-white flex flex-col md:flex-row items-center justify-between gap-8 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/10 blur-[100px] rounded-full"></div>
              <div className="relative z-10">
                <h2 className="text-3xl font-black mb-3">مولد الصور الذكي</h2>
                <p className="text-emerald-200/80 max-w-md">اطلب من الذكاء الاصطناعي رسم أي مشهد في مدينة الكويت وسيقوم بإنشائه لك فوراً.</p>
              </div>
              <button 
                onClick={() => handleGenerateImage("Futuristic Kuwait City towers with flying cars and neon lights, hyperrealistic")}
                disabled={isLoading}
                className="bg-white text-emerald-900 px-8 py-4 rounded-2xl font-black hover:bg-emerald-50 disabled:opacity-50 transition shadow-xl shrink-0 flex items-center gap-3"
              >
                {isLoading ? 'جاري الرسم...' : <><Sparkles size={20}/> ابهرني بصورة!</>}
              </button>
            </div>

            <div className="columns-1 sm:columns-2 lg:columns-3 gap-6 space-y-6">
              {generatedImages.map((img, idx) => (
                <div key={`gen-${idx}`} className="break-inside-avoid rounded-3xl overflow-hidden shadow-2xl border-4 border-emerald-500/10 group relative">
                  <img src={img} className="w-full h-auto" alt="AI Generated" />
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <button className="bg-white text-slate-800 p-3 rounded-full shadow-lg"><Download size={20}/></button>
                  </div>
                </div>
              ))}
              {[1,2,3,4,5,6].map(i => (
                <img key={i} src={`https://picsum.photos/seed/kwt${i}/800/${600 + (i%3)*100}`} className="w-full rounded-3xl shadow-sm break-inside-avoid hover:scale-[1.02] transition cursor-zoom-in" alt="Gallery" />
              ))}
            </div>
          </div>
        )}

        {/* Chat Tab */}
        {activeTab === 'chat' && (
          <div className="max-w-5xl mx-auto h-[650px] flex flex-col bg-white rounded-[2.5rem] shadow-2xl overflow-hidden border border-slate-100 animate-in zoom-in-95 duration-500">
            <div className="bg-emerald-900 p-6 text-white flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="bg-emerald-500 p-3 rounded-2xl shadow-lg">
                  <MessageSquare size={24} />
                </div>
                <div>
                  <h3 className="font-bold text-lg leading-tight">مساعد Pipo الذكي</h3>
                  <p className="text-xs text-emerald-300/80 uppercase tracking-widest mt-1">Kuwait Intelligence Agency</p>
                </div>
              </div>
              <div className="flex -space-x-2">
                {[1,2,3].map(i => <div key={i} className="w-8 h-8 rounded-full border-2 border-emerald-900 bg-emerald-600"></div>)}
              </div>
            </div>

            <div className="flex-grow overflow-y-auto p-8 space-y-6 bg-slate-50/50">
              {chatMessages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === 'user' ? 'justify-start' : 'justify-end'}`}>
                  <div className={`max-w-[85%] p-5 rounded-3xl shadow-sm ${
                    msg.role === 'user' 
                      ? 'bg-emerald-600 text-white rounded-tr-none' 
                      : 'bg-white text-slate-800 rounded-tl-none border border-slate-100'
                  }`}>
                    <p className="text-[15px] leading-relaxed whitespace-pre-wrap font-medium">{msg.text}</p>
                    <span className="text-[10px] mt-2 block opacity-50 uppercase tracking-tighter">
                      {msg.role === 'user' ? 'You' : 'Pipo AI'} • {new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </span>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-end">
                  <div className="bg-white p-5 rounded-3xl border border-slate-100 shadow-sm flex items-center gap-3">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce [animation-delay:0.2s]"></div>
                      <div className="w-2 h-2 bg-emerald-600 rounded-full animate-bounce [animation-delay:0.4s]"></div>
                    </div>
                    <span className="text-slate-400 text-xs font-bold">جاري تحليل البيانات...</span>
                  </div>
                </div>
              )}
            </div>

            <div className="p-6 bg-white border-t border-slate-100 flex gap-3 items-center">
              <input 
                type="text" 
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="اسأل Pipo عن التاريخ، الاقتصاد، أو المطاعم..." 
                className="flex-grow bg-slate-100 border-none rounded-2xl px-6 py-4 focus:ring-2 focus:ring-emerald-500 outline-none transition font-medium"
              />
              <button 
                onClick={handleSendMessage}
                disabled={isLoading}
                className="bg-emerald-600 hover:bg-emerald-700 text-white w-14 h-14 rounded-2xl shadow-xl transition disabled:opacity-50 flex items-center justify-center shrink-0"
              >
                <ChevronLeft size={28} />
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-slate-950 text-slate-500 py-16 px-4">
        <div className="max-w-7xl mx-auto flex flex-col items-center text-center gap-10">
          <div className="flex flex-col items-center gap-4">
            <div className="bg-emerald-600 p-3 rounded-2xl shadow-2xl shadow-emerald-600/20">
              <Palmtree className="text-white" size={32} />
            </div>
            <div>
              <h1 className="text-2xl font-black text-white">Pipo Kuwait Explorer</h1>
              <p className="text-emerald-500 font-bold text-xs tracking-widest uppercase mt-1">Premium Digital Experience</p>
            </div>
          </div>
          
          <div className="flex flex-wrap justify-center gap-8 text-sm font-bold">
            <button onClick={() => setActiveTab('home')} className="text-slate-400 hover:text-white transition">الرئيسية</button>
            <button onClick={() => setActiveTab('landmarks')} className="text-slate-400 hover:text-white transition">المعالم</button>
            <button onClick={() => setActiveTab('gallery')} className="text-slate-400 hover:text-white transition">المعرض</button>
            <button onClick={() => setActiveTab('chat')} className="text-slate-400 hover:text-white transition">المساعد الذكي</button>
          </div>

          <div className="max-w-md text-slate-600 text-sm leading-relaxed">
            هذا المشروع تم تطويره ليكون المرجع الرقمي الأول لكل من يبحث عن عراقة وجمال دولة الكويت، مدمجاً بأحدث تقنيات الذكاء الاصطناعي العالمية.
          </div>

          <div className="border-t border-slate-900 w-full pt-10 flex flex-col md:flex-row items-center justify-between gap-4">
            <span className="text-xs uppercase tracking-widest font-black text-slate-700">© {new Date().getFullYear()} Designed & Engineered by Pipo Al-Gharawi</span>
            <div className="flex gap-4">
              <div className="w-8 h-8 rounded-full bg-slate-900 border border-slate-800"></div>
              <div className="w-8 h-8 rounded-full bg-slate-900 border border-slate-800"></div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
