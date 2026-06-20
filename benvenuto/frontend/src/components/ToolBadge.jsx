const LABELS = {
  law_info: "🏛 Law",
  student_news: "📰 News",
  cuisine_guide: "🍝 Cuisine",
  tourism_guide: "🗺 Tourism",
  etiquette_coach: "🤝 Etiquette",
  grocery_finder: "🛒 Grocery",
  university_area: "📍 University area",
  scholarships: "🎓 Scholarships",
};

export default function ToolBadge({ name }) {
  return (
    <span className="inline-block text-xs px-2 py-0.5 mr-1 mb-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
      {LABELS[name] || name}
    </span>
  );
}
