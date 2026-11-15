# Results index

Start with these folders. The numerical experiment evidence has been preserved.

| Folder | Meaning |
|---|---|
| `single-channel-comparison/` | Controlled fixed single-channel versus WDM/Pareto comparison, including equal total pulses |
| `normal-comparison/` | New healthy reference matched to the Pareto grid's seeds, pulse count and duration |
| `pareto/` | 2,480-run Pareto follow-up; seven alignment settings and eighteen standard scenarios |
| `hybrid/` | Original 2,160-run combined-policy study; includes correlated-drift failure |
| `ml/` | Random Forest evaluation against the analytical teacher |
| `protocol/` | Ideal single-photon authenticated participant demonstration |
| `decoy-finite/` | Separate conditional decoy finite-key length bounds |
| `sdn/` | Windows dry-run commands; not Linux packet validation |
| `pareto-aer-smoke/`, `hybrid-aer-smoke/` | Separate circuit-based smoke checks |

The other folders retain earlier studies, notebook runs, sensitivity checks and
revalidation records. They use different seeds, durations and sometimes model
versions. Do not combine their totals into a single detection rate or compare
their raw bit counts without matching the experiment settings.

`summary.csv` usually has one row per scenario/policy. `runs.csv` contains
individual seeds. Example traces contain one row per wavelength and interval.
For the latest interpretation, read `reports/PROFESSOR_BRIEF.md` and
`normal-comparison/COMPARISON_REPORT.md` from the project root.
