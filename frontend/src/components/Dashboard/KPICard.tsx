interface KPICardProps {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  color: 'indigo' | 'green' | 'red' | 'blue' | 'yellow' | 'purple';
}

const colorMap = {
  indigo: 'border-indigo-700 bg-indigo-900/30 text-indigo-400',
  green: 'border-green-700 bg-green-900/30 text-green-400',
  red: 'border-red-700 bg-red-900/30 text-red-400',
  blue: 'border-blue-700 bg-blue-900/30 text-blue-400',
  yellow: 'border-yellow-700 bg-yellow-900/30 text-yellow-400',
  purple: 'border-purple-700 bg-purple-900/30 text-purple-400',
};

export default function KPICard({ title, value, icon, color }: KPICardProps) {
  return (
    <div className={`border rounded-xl p-4 ${colorMap[color]}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium uppercase tracking-wider opacity-70">{title}</span>
        {icon}
      </div>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}
