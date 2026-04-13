Shared security scan rules:
- stay evidence-grounded and compact
- use only the supplied repository artifacts, profile, map, and code slices
- prefer real source -> processing -> sink paths over generic risk advice
- if framework evidence indicates GraphQL, treat schema, resolvers, args, variables, context user/session, and directive-based auth as first-class signals
- if framework evidence indicates Java servlet/JSP/JAX-RS, treat request parameter/header/cookie/session flows, RequestDispatcher forward/include, sendRedirect, JDBC execution, and auth/session boundaries as first-class signals
- if service edges or service-address markers are present, treat service-to-service hops as limited but real attack-surface transitions; mention them only when the supplied edges support the claim
- call out command execution, SSRF, NoSQL operator injection, auth/session misuse, and dynamic query construction only when the path is credible in the supplied evidence
