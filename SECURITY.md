# Security Policy

Security fixes apply to the latest release on the default branch.

Do not open a public issue for a suspected vulnerability or include working secrets in a report. Use the repository owner's private security-reporting channel.

Deploy this service behind an HTTPS reverse proxy. Keep Bark port 8080 and gateway port 8787 bound to loopback, use a distinct credential for every source, and prefer native webhook signatures when available.

