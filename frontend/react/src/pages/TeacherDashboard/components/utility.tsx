export const badgeClasses = (value: string) => {
  switch (value) {
    case "Submitted":
    case "Successful":
      return "bg-emerald-500/15 text-emerald-300 ring-1 ring-inset ring-emerald-400/30";
    case "Late":
    case "Warnings":
    case "Pending Review":
      return "bg-amber-500/15 text-amber-300 ring-1 ring-inset ring-amber-400/30";
    case "Failed":
      return "bg-rose-500/15 text-rose-300 ring-1 ring-inset ring-rose-400/30";
    default:
      return "bg-white/10 text-slate-200 ring-1 ring-inset ring-white/10";
  }
}