import { Settings, User, Bell, Shield, Map } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";

export function SettingsPage() {
  return (
    <div className="animate-fade-in space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2.5">
            <Settings className="w-6 h-6 text-[#183a37]" />
            System Settings
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            Manage your account preferences, notifications, and system configurations.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Profile Settings */}
        <Card className="rounded-none border border-gray-300 shadow-none">
          <CardHeader className="border-b border-gray-200 bg-gray-50/80">
            <CardTitle className="text-sm font-bold flex items-center gap-2 text-gray-800 uppercase tracking-wide">
              <User className="w-4 h-4 text-[#D47A22]" />
              Account Profile
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Username</label>
              <input type="text" className="w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-none text-sm focus:outline-none focus:ring-1 focus:ring-brand-teal-blue" value="admin_user" disabled />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Email Address</label>
              <input type="email" className="w-full px-3 py-2 bg-white border border-gray-300 rounded-none text-sm focus:outline-none focus:ring-1 focus:ring-brand-teal-blue" defaultValue="admin@bhoomisetu.gov.in" />
            </div>
            <button className="w-full py-2 bg-[#183a37] text-white text-sm font-semibold rounded-none hover:bg-opacity-90">
              Save Changes
            </button>
          </CardContent>
        </Card>

        {/* Preferences */}
        <Card className="rounded-none border border-gray-300 shadow-none">
          <CardHeader className="border-b border-gray-200 bg-gray-50/80">
            <CardTitle className="text-sm font-bold flex items-center gap-2 text-gray-800 uppercase tracking-wide">
              <Bell className="w-4 h-4 text-[#D47A22]" />
              Notifications
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">Email Alerts</span>
              <input type="checkbox" className="w-4 h-4 text-brand-teal-blue rounded-none border-gray-300 focus:ring-brand-teal-blue" defaultChecked />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">SMS Notifications</span>
              <input type="checkbox" className="w-4 h-4 text-brand-teal-blue rounded-none border-gray-300 focus:ring-brand-teal-blue" />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">SLA Breach Warnings</span>
              <input type="checkbox" className="w-4 h-4 text-brand-teal-blue rounded-none border-gray-300 focus:ring-brand-teal-blue" defaultChecked />
            </div>
          </CardContent>
        </Card>

        {/* System Settings */}
        <Card className="rounded-none border border-gray-300 shadow-none">
          <CardHeader className="border-b border-gray-200 bg-gray-50/80">
            <CardTitle className="text-sm font-bold flex items-center gap-2 text-gray-800 uppercase tracking-wide">
              <Shield className="w-4 h-4 text-[#D47A22]" />
              Security
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 space-y-4">
            <button className="w-full py-2 bg-white border border-gray-300 text-gray-700 text-sm font-semibold rounded-none hover:bg-gray-50">
              Change Password
            </button>
            <button className="w-full py-2 bg-white border border-gray-300 text-gray-700 text-sm font-semibold rounded-none hover:bg-gray-50">
              Two-Factor Authentication
            </button>
            <button className="w-full py-2 bg-red-50 border border-red-200 text-red-700 text-sm font-semibold rounded-none hover:bg-red-100 mt-4">
              Logout All Sessions
            </button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default SettingsPage;
