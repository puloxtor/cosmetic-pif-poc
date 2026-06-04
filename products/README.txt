Product input files (one YAML per product) go here. See products/TEMPLATE.yaml.

Each file describes ONE product as raw materials + their supplier composition
statements (exact %, ranges -> upper bound, or "remainder"). The engine computes
the final concentrations, sums duplicate INCI names and generates the INCI list.

Run:  python3 pifgen.py products/<your_product>.yaml
Outputs (CPSR + INCI) are written to outputs/<slug>/ and are NOT committed.
