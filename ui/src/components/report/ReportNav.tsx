import { useState, useEffect } from "react";
import {
  BarChart3, TrendingUp, Heart, CheckCircle2, ShoppingCart,
  MapPin, ArrowLeftRight, Building, Trophy, FileCheck, Star, Menu, X
} from "lucide-react";

const sections = [
  { id: "summary", label: "Summary", icon: BarChart3 },
  { id: "price-trend", label: "Price Trend", icon: TrendingUp },
  { id: "liveability", label: "Liveability", icon: Heart },
  { id: "highlights", label: "Highlights", icon: CheckCircle2 },
  { id: "market", label: "Market", icon: ShoppingCart },
  { id: "nearby", label: "Nearby", icon: MapPin },
  { id: "demand-supply", label: "Demand/Supply", icon: ArrowLeftRight },
  { id: "property-rates", label: "Rates", icon: Building },
  { id: "top-projects", label: "Projects", icon: Trophy },
  { id: "registration", label: "Registration", icon: FileCheck },
  { id: "reviews", label: "Reviews", icon: Star },
];

const ReportNav = () => {
  const [activeId, setActiveId] = useState("summary");
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (visible.length > 0) {
          setActiveId(visible[0].target.id);
        }
      },
      { rootMargin: "-80px 0px -60% 0px", threshold: 0.1 }
    );

    sections.forEach(({ id }) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
      setActiveId(id);
      setMobileOpen(false);
    }
  };

  return (
    <>
      {/* Desktop sidebar nav */}
      <nav className="hidden lg:block fixed left-0 top-0 h-screen w-52 bg-card border-r border-border z-40 overflow-y-auto">
        <div className="p-4 border-b border-border">
          <div className="sy-gradient rounded-lg px-3 py-2">
            <span className="text-xs font-bold text-primary-foreground tracking-wide">SQUARE YARDS</span>
          </div>
        </div>
        <div className="py-3 px-2 space-y-0.5">
          {sections.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => scrollTo(id)}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-left text-sm transition-all ${
                activeId === id
                  ? "bg-sy-orange-light text-primary font-semibold"
                  : "text-muted-foreground hover:bg-secondary hover:text-foreground"
              }`}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span className="truncate">{label}</span>
            </button>
          ))}
        </div>
      </nav>

      {/* Mobile top bar */}
      <nav className="lg:hidden fixed top-0 left-0 right-0 z-40 bg-card/95 backdrop-blur-md border-b border-border">
        <div className="flex items-center justify-between px-4 h-12">
          <div className="sy-gradient rounded-md px-2.5 py-1">
            <span className="text-[10px] font-bold text-primary-foreground tracking-wide">SQUARE YARDS</span>
          </div>
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="p-1.5 rounded-lg hover:bg-secondary text-foreground"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {/* Horizontal scroll nav (always visible) */}
        <div className="flex overflow-x-auto gap-1 px-3 pb-2 scrollbar-hide">
          {sections.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => scrollTo(id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all shrink-0 ${
                activeId === id
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-muted-foreground"
              }`}
            >
              <Icon className="h-3 w-3" />
              {label}
            </button>
          ))}
        </div>

        {/* Full menu dropdown */}
        {mobileOpen && (
          <div className="absolute top-full left-0 right-0 bg-card border-b border-border shadow-lg py-2 px-3 grid grid-cols-2 gap-1 max-h-[60vh] overflow-y-auto">
            {sections.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => scrollTo(id)}
                className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm transition-all ${
                  activeId === id
                    ? "bg-sy-orange-light text-primary font-semibold"
                    : "text-muted-foreground hover:bg-secondary"
                }`}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {label}
              </button>
            ))}
          </div>
        )}
      </nav>
    </>
  );
};

export default ReportNav;
