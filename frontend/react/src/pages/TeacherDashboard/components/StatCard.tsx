
type StatCardProps = {
  icon: React.ElementType;
  label: string;
  value: string | number;
};

const StatCard = ({ icon: Icon, label, value }: StatCardProps) => {
  return (
    <div className="p-6 bg-white border shadow-sm rounded-2xl border-slate-200">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-slate-500">{label}</p>
          <p className="mt-2 text-2xl font-semibold text-slate-500">{value}</p>
        </div>
        <div className="p-3 rounded-2xl bg-slate-100 text-slate-500">
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
};

export default StatCard;