import { createBrowserRouter } from "react-router";
import { Root } from "./Root";
import { MarketingLayout } from "./layouts/MarketingLayout";
import { Overview } from "./pages/Overview";
import { SSP } from "./pages/SSP";
import { Evidence } from "./pages/Evidence";
import { POAM } from "./pages/POAM";
import { SetupWizard } from "./pages/SetupWizard";
import { Settings } from "./pages/Settings";
import { Home } from "./pages/marketing/Home";
import { Features } from "./pages/marketing/Features";
import { Pricing } from "./pages/marketing/Pricing";
import { About } from "./pages/marketing/About";
import { Contact } from "./pages/marketing/Contact";
import { Login } from "./pages/Login";

export const router = createBrowserRouter([
  // Marketing — public
  {
    Component: MarketingLayout,
    children: [
      { path: "/", Component: Home },
      { path: "/features", Component: Features },
      { path: "/pricing", Component: Pricing },
      { path: "/about", Component: About },
      { path: "/contact", Component: Contact },
      { path: "/login", Component: Login },
    ],
  },
  // Platform — protected (auth handled by Root)
  {
    path: "/app",
    Component: Root,
    children: [
      { index: true, Component: Overview },
      { path: "ssp", Component: SSP },
      { path: "evidence", Component: Evidence },
      { path: "poam", Component: POAM },
      { path: "intake", Component: SetupWizard },
      { path: "settings", Component: Settings },
    ],
  },
]);
