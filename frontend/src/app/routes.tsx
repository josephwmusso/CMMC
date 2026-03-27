import { createBrowserRouter } from "react-router";
import { Root } from "./Root";
import { Overview } from "./pages/Overview";
import { SSP } from "./pages/SSP";
import { Evidence } from "./pages/Evidence";
import { POAM } from "./pages/POAM";
import { SetupWizard } from "./pages/SetupWizard";
import { Settings } from "./pages/Settings";

export const router = createBrowserRouter([
  {
    path: "/",
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