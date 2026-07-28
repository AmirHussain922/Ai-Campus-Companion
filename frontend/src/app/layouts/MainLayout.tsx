import { useState, useEffect } from "react";
import { Outlet, NavLink, useNavigate, useLocation } from "react-router";
import { LayoutDashboard, Settings, User, Menu, X, ChevronLeft, ChevronRight, ScrollText, Users, BookOpen } from "lucide-react";
import { useStore } from "../store";
import { companionColorClasses, cn } from "../utils";
import ToastContainer from "../components/ToastContainer";
import NotificationBell from "../components/NotificationBell";

export default function MainLayout() {
  const myCompanions = useStore(state => state.myCompanions);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Close sidebar on route change
  useEffect(() => {
    setIsSidebarOpen(false);
  }, [location.pathname]);

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50 flex overflow-hidden">
      {/* Mobile Top Bar */}
      <div className="md:hidden fixed top-0 left-0 right-0 h-16 bg-zinc-950/80 backdrop-blur-xl border-b border-zinc-800 z-50 flex items-center justify-between px-4">
        <div className="flex items-center gap-3">
          <button onClick={() => setIsSidebarOpen(true)} className="p-2 -ml-2 text-zinc-400 hover:text-white">
            <Menu className="w-6 h-6" />
          </button>
          <h1 className="text-xl font-bold tracking-tighter">
            AI Campus<span className="text-zinc-500">.</span>
          </h1>
        </div>
        <div className="flex items-center gap-1">
          <NotificationBell />
          <button onClick={() => navigate(-1)} className="p-2 text-zinc-400 hover:text-white rounded-full hover:bg-zinc-800/50">
            <ChevronLeft className="w-5 h-5" />
          </button>
          <button onClick={() => navigate(1)} className="p-2 text-zinc-400 hover:text-white rounded-full hover:bg-zinc-800/50">
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Sidebar Navigation */}
      <div className={cn(
        "fixed inset-0 bg-black/50 z-40 transition-opacity md:hidden",
        isSidebarOpen ? "opacity-100" : "opacity-0 pointer-events-none"
      )} onClick={() => setIsSidebarOpen(false)} />
      
      <aside className={cn(
        "fixed md:relative top-0 left-0 z-50 h-full w-64 border-r border-zinc-800 flex flex-col p-4 bg-zinc-950/95 md:bg-zinc-950/50 backdrop-blur-xl shrink-0 transition-transform duration-300 ease-in-out md:translate-x-0",
        isSidebarOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex items-center justify-between mb-8 px-2 mt-4 md:mt-4">
          <h1 className="text-xl font-bold tracking-tighter hidden md:block">
            AI Campus<span className="text-zinc-500">.</span>
          </h1>
          <h1 className="text-xl font-bold tracking-tighter md:hidden">Menu</h1>
          <button onClick={() => setIsSidebarOpen(false)} className="md:hidden p-2 -mr-2 text-zinc-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Global Navigation Arrows (Desktop) */}
        <div className="hidden md:flex items-center justify-between gap-2 mb-6 px-2">
          <div className="flex items-center gap-2">
            <button onClick={() => navigate(-1)} className="p-1.5 text-zinc-400 hover:text-white rounded-full hover:bg-zinc-800 transition-colors" title="Go Back">
              <ChevronLeft className="w-5 h-5" />
            </button>
            <button onClick={() => navigate(1)} className="p-1.5 text-zinc-400 hover:text-white rounded-full hover:bg-zinc-800 transition-colors" title="Go Forward">
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
          <div className="flex items-center gap-2">
            <NotificationBell />
          </div>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto custom-scrollbar">
          <NavLink 
            to="/app" end
            className={({isActive}) => `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${isActive ? 'bg-zinc-800 text-white' : 'text-zinc-400 hover:text-white hover:bg-zinc-900'}`}
          >
            <LayoutDashboard className="w-4 h-4" />
            Dashboard
          </NavLink>

          {/* New Campus Features */}
          <div className="pt-6 pb-2 px-3 text-xs font-semibold text-zinc-500 uppercase tracking-wider">
            Campus
          </div>
          
          <NavLink 
            to="/app/quests"
            className={({isActive}) => `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${isActive ? 'bg-zinc-800 text-white' : 'text-zinc-400 hover:text-white hover:bg-zinc-900'}`}
          >
            <ScrollText className="w-4 h-4" />
            Quests
            <span className="ml-auto px-1.5 py-0.5 bg-amber-500/20 text-amber-400 text-xs rounded">3</span>
          </NavLink>
          
          <NavLink 
            to="/app/campus-lounge"
            className={({isActive}) => `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${isActive ? 'bg-zinc-800 text-white' : 'text-zinc-400 hover:text-white hover:bg-zinc-900'}`}
          >
            <Users className="w-4 h-4" />
            Campus Lounge
            <span className="ml-auto w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
          </NavLink>
          
          <NavLink 
            to="/app/study-room"
            className={({isActive}) => `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${isActive ? 'bg-zinc-800 text-white' : 'text-zinc-400 hover:text-white hover:bg-zinc-900'}`}
          >
            <BookOpen className="w-4 h-4" />
            Study Room
          </NavLink>

          <div className="pt-6 pb-2 px-3 text-xs font-semibold text-zinc-500 uppercase tracking-wider">
            My Companions
          </div>
          
          {myCompanions.map(comp => {
            const colors = companionColorClasses[comp.color as keyof typeof companionColorClasses];
            return (
              <NavLink 
                key={comp.id}
                to={`/app/chat/${comp.id}`}
                className={({isActive}) => `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${isActive ? 'bg-zinc-800 text-white' : 'text-zinc-400 hover:text-white hover:bg-zinc-900'}`}
              >
                <div className="relative">
                  <img src={comp.avatarUrl} alt={comp.name} className="w-6 h-6 rounded-full object-cover" />
                  <div className={cn("absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border border-zinc-950", colors.bg)} />
                </div>
                <span className="truncate">{comp.name}</span>
              </NavLink>
            );
          })}
          
          {myCompanions.length === 0 && (
            <div className="px-3 py-2 text-sm text-zinc-500">
              No companions yet.
            </div>
          )}
        </nav>

        <div className="pt-4 border-t border-zinc-800 mt-auto space-y-1">
          <NavLink 
            to="/app/me"
            className={({isActive}) => `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${isActive ? 'bg-zinc-800 text-white' : 'text-zinc-400 hover:text-white hover:bg-zinc-900'}`}
          >
            <Settings className="w-4 h-4" />
            My Profile
          </NavLink>
          <NavLink 
            to="/select"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-zinc-400 hover:text-white hover:bg-zinc-900 transition-colors"
          >
            <User className="w-4 h-4" />
            Add Companion
          </NavLink>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 relative flex flex-col pt-16 md:pt-0 h-[100dvh] md:h-[100dvh] overflow-hidden">
        <Outlet />
      </main>
      <ToastContainer />
    </div>
  );
}
