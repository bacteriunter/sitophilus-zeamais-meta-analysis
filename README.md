# Natural Control of *Sitophilus zeamais* in Stored Maize: Systematic Review and Quantitative Synthesis

## Overview

This repository contains the computational workflow, structured datasets, quality-control records, statistical analyses, and figures associated with a systematic review and quantitative synthesis of natural and non-synthetic strategies for controlling *Sitophilus zeamais* in stored maize.

The project evaluates biological responses to botanical products, natural materials, and other eligible non-synthetic interventions, with particular emphasis on insect mortality, treatment formulation, and dose-dependent responses.

The repository is intended to support methodological transparency, analytical reproducibility, and traceability from literature identification to final synthesis.

## Study scope

The systematic review focused on experimental studies evaluating natural or non-synthetic interventions against *S. zeamais* in stored maize.

Eligible interventions included botanical powders, extracts, essential oils, natural oils, ashes, mixtures of natural materials, and relevant physical or storage-based approaches.

Biological outcomes considered during evidence extraction included:

- Adult mortality
- Progeny emergence (F1)
- Grain weight loss
- Grain damage
- Seed germination

These outcomes were evaluated separately rather than combined into a single biological effect measure.

## Study selection

The literature identification and screening workflow involved database searches, deduplication, title and abstract screening, full-text retrieval, and sequential eligibility assessment.

The final systematic review included **58 experimental studies**.

A subset of **9 studies**, providing **154 mortality observations**, was incorporated into the quantitative mortality synthesis.

Studies included in the systematic review were not automatically eligible for the quantitative mortality analysis. Inclusion in the quantitative dataset depended on the availability and structure of extractable mortality data.

## Quality-control and auditing workflow

A multistage computational auditing process was implemented to improve traceability and reduce errors in study classification and data extraction.

### Experimental eligibility audit

Retrieved full texts were examined for information on the target insect species, maize context, experimental treatments, controls, replication, sample size, exposure duration, dose, environmental conditions, and quantitative outcomes.

### Scope eligibility audit

Studies were assessed for consistency with the review question, including confirmation of *S. zeamais*, relevance to maize, and the presence of eligible natural or non-synthetic interventions.

### Numerical evidence audit

Potentially extractable quantitative information was examined, including percentages, means, dispersion measures, sample sizes, and tabulated results.

Mortality, progeny, weight loss, grain damage, and germination were treated as distinct outcomes.

### Mortality-specific audit

Mortality data were assessed for treatment identification, dose, exposure time, reported mortality values, replication, measures of dispersion, control information, Abbott correction, and LC/LD reporting.

Only observations meeting the requirements of the final mortality dataset were retained for quantitative synthesis.

## Quantitative mortality synthesis

The final mortality dataset comprised 154 observations from 9 studies.

Mortality was evaluated using a hierarchical analytical framework that accounted for the nested structure of observations across studies, experiments, and treatments.

For treatment–dose combinations reported at multiple exposure times, the final reported exposure time was retained for the primary mortality synthesis. Eligible dose levels were preserved to support biological interpretation and dose–response assessment.

The analysis emphasized differences among natural materials, formulations, and dose-dependent responses.

Because the synthesis was based on reported mortality observations rather than consistently available study-specific sampling variances, it should not be interpreted as a conventional inverse-variance meta-analysis of treatment effects.

## Repository structure

| Directory | Contents |
|---|---|
| `00_protocol/` | Protocol-related documentation |
| `01_search/` | Literature search records |
| `02_deduplication/` | Deduplicated bibliographic records |
| `03_screening/` | Screening and prioritization outputs |
| `04_pdfs/` | Retrieval metadata and logs; third-party full texts are excluded |
| `05_extraction/` | Structured extraction, eligibility assessments, and audit outputs |
| `06_effect_sizes/` | Quantitative data preparation and analytical outputs |
| `07_meta_analysis/` | Statistical synthesis and biological summaries |
| `08_figures/` | Scientific figures and supporting figure data |
| `scripts/` | Computational scripts |

## Reproducibility

The workflow was developed using Python and R in a Linux environment under Windows Subsystem for Linux (WSL).

The computational analysis includes literature processing, structured evidence extraction, quantitative data preparation, hierarchical statistical modeling, and figure generation.

Scripts and available structured intermediate outputs are retained to document the analytical workflow.

Reproduction of stages requiring original full-text publications may depend on obtaining those publications independently from their respective publishers or repositories.

The final structured datasets and analysis outputs are provided where redistribution is appropriate.

## Data availability and copyright

Bibliographic metadata, derived structured datasets, audit outputs, analysis scripts, and original figures are included where permitted.

Full-text PDF, XML, and extracted-text copies of third-party scientific publications are intentionally excluded from the public repository.

The MIT License applies to the original software and documentation covered by the repository license. Third-party publications and externally sourced materials retain their respective rights and licensing conditions.

## Citation

Please cite the associated scientific publication when available.

A formal citation and persistent repository identifier will be added following publication or archival release.

## License

The original software in this repository is distributed under the MIT License. See `LICENSE` for details.
