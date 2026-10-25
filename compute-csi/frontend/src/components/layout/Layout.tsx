import { NavLink, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  Cpu,
  PlayCircle,
  AlertTriangle,
  Link2,
  Zap,
} from 'lucide-react';

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/workloads', label: 'Workloads', icon: Cpu },
  { to: '/runs', label: 'Runs', icon: PlayCircle },
  { to: '/incidents', label: 'Incidents', icon: AlertTriangle },
  { to: '/integrations', label: 'Integrations', icon: Link2 },
];

export function Layout() {
  return (
    <div className="flex h-screen overflow-hidden bg-csi-dark">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 bg-csi-surface border-r border-csi-border flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-csi-border">
          <div className="flex items-center gap-2 mb-1">
            <Zap className="w-6 h-6 text-csi-cyan" />
            <span className="text-lg font-bold text-white tracking-wider">COMPUTE CSI</span>
          </div>
          <p className="text-xs text-gray-500 ml-8">AI Infrastructure Forensics</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-csi-blue/20 text-csi-blue border border-csi-blue/30'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-csi-border">
          <p className="text-xs text-gray-600 text-center">v1.0.0 — Hacktoberfest</p>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
