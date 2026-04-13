import { Link } from "react-router-dom";

const footerLinks = {
  Product: [
    { label: "Features", to: "/features" },
    { label: "Workflow", to: "/workflow" },
    { label: "Security Review", to: "/security-review" },
    { label: "Download", to: "/download" },
  ],
  Resources: [
    { label: "FAQ", to: "/faq-contact" },
    { label: "Documentation", to: "/faq-contact" },
    { label: "Release Notes", to: "/faq-contact" },
  ],
  Support: [
    { label: "Contact", to: "/faq-contact" },
    { label: "Help Center", to: "/faq-contact" },
  ],
};

export function Footer() {
  return (
    <footer className="border-t border-border-soft bg-surface-sidebar">
      <div className="max-w-content mx-auto px-6 py-16">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-10">
          <div className="col-span-2 md:col-span-1">
            <Link to="/" className="flex items-center gap-2.5 mb-4">
              <div className="w-7 h-7 rounded-md bg-primary flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-xs">SS</span>
              </div>
              <span className="font-semibold text-foreground tracking-tight text-sm">SecureScan Studio</span>
            </Link>
            <p className="text-text-secondary text-sm leading-relaxed">
              A focused desktop workspace for security analysis and remediation.
            </p>
          </div>

          {Object.entries(footerLinks).map(([group, links]) => (
            <div key={group}>
              <h4 className="font-medium text-foreground text-sm mb-4">{group}</h4>
              <ul className="space-y-2.5">
                {links.map((link) => (
                  <li key={link.label}>
                    <Link
                      to={link.to}
                      className="text-text-secondary text-sm hover:text-foreground transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-14 pt-6 border-t border-border-soft flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-text-tertiary text-xs">
            © {new Date().getFullYear()} SecureScan Studio. All rights reserved.
          </p>
          <div className="flex items-center gap-5">
            <span className="text-text-tertiary text-xs hover:text-text-secondary cursor-pointer transition-colors">Privacy</span>
            <span className="text-text-tertiary text-xs hover:text-text-secondary cursor-pointer transition-colors">Terms</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
