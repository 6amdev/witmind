import { Link } from 'react-router-dom'
import { Rocket, Bell, Settings } from 'lucide-react'

export default function Header() {
  return (
    <header className="h-14 bg-bg-secondary border-b border-border-default px-4 flex items-center justify-between sticky top-0 z-50">
      {/* Logo */}
      <Link to="/" className="flex items-center gap-2">
        <Rocket className="w-6 h-6 text-accent-blue" />
        <span className="font-semibold text-lg">
          MISSION CONTROL
          <span className="text-text-muted text-sm ml-2">v2</span>
        </span>
      </Link>

      {/* Status indicators */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm">
          <span className="w-2 h-2 rounded-full bg-accent-green animate-pulse" />
          <span className="text-text-secondary">System Online</span>
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-2">
        <button className="btn-ghost p-2">
          <Bell className="w-5 h-5" />
        </button>
        <button className="btn-ghost p-2">
          <Settings className="w-5 h-5" />
        </button>
        <div className="w-8 h-8 rounded-full bg-accent-blue flex items-center justify-center text-white font-medium">
          U
        </div>
      </div>
    </header>
  )
}
