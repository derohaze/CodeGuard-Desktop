import { createRoot } from "react-dom/client";
import { AppProviders } from "./providers/AppProviders";
import { AppRouter } from "./router/AppRouter";

export function renderApp() {
  createRoot(document.getElementById("root")!).render(
    <AppProviders>
      <AppRouter />
    </AppProviders>,
  );
}
