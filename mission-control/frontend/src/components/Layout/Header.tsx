import { Link, useNavigate } from 'react-router-dom'
import { Rocket, Bell, Settings, LogOut } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

export default function Header() {
  const { logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

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
        <button
          onClick={handleLogout}
          className="btn-ghost p-2 text-text-muted hover:text-accent-red"
          title="Logout"
        >
          <LogOut className="w-5 h-5" />
        </button>
      </div>
    </header>
  )
}
