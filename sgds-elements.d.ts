// Global type declarations for SGDS web components.
// This file is at the project root so TypeScript always finds it.
import "react";

declare module "react" {
  namespace JSX {
    interface IntrinsicElements {
      "sgds-masthead": DetailedHTMLProps<HTMLAttributes<HTMLElement> & { fluid?: boolean }, HTMLElement>;
      "sgds-footer": DetailedHTMLProps<HTMLAttributes<HTMLElement> & {
        contactHref?: string;
        feedbackHref?: string;
        faqHref?: string;
        privacyHref?: string;
        termsOfUseHref?: string;
        sitemapHref?: string;
        copyrightLiner?: string;
        layout?: string;
        tone?: string;
      }, HTMLElement>;
      "sgds-mainnav": DetailedHTMLProps<HTMLAttributes<HTMLElement> & { fluid?: boolean }, HTMLElement>;
      "sgds-sidebar": DetailedHTMLProps<HTMLAttributes<HTMLElement>, HTMLElement>;
      "sgds-footer-item": DetailedHTMLProps<HTMLAttributes<HTMLElement>, HTMLElement>;
      [elemName: `sgds-${string}`]: DetailedHTMLProps<HTMLAttributes<HTMLElement> & Record<string, unknown>, HTMLElement>;
    }
  }
}
