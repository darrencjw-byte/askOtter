"use client";

import { useEffect } from "react";

export function SgdsProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Swallow re-registration errors from HMR/strict-mode re-invoking this
    // effect — customElements.define() throws if a name is already
    // registered, and the browser's custom-element registry persists
    // across hot reloads (unlike React's own component tree), so this is
    // expected during development, not a real failure to surface.
    import("@govtechsg/sgds-web-component").catch(() => {});
  }, []);

  return <>{children}</>;
}
