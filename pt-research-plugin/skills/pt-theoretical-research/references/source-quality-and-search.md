# Source quality, search, and evidence integrity

## Quality tiers

| Tier | Suitable sources | Permitted use |
|---|---|---|
| A | Peer-reviewed primary research; authoritative monographs/textbooks; official standards; direct experimental or modeling papers | Central mechanism, equations, applicability, validation |
| B | Strong reviews; theses/dissertations; proceedings with adequate methods | Synthesis, vocabulary, indirect support, reference chasing |
| C | Manufacturer application notes; institutional reports; reputable educational notes | Apparatus mechanisms, parameters, practical context; corroborate central claims |
| D | General sites, forums, videos, unsourced summaries | Leads and vocabulary only; never sole support for selection |

Tier is not the same as directness. A rigorous general-theory textbook may be Tier A but indirect to the apparatus. Record both.

## Complementary channels

Choose channels based on field and availability: Crossref or OpenAlex for metadata; Semantic Scholar for cross-disciplinary discovery and citation graphs; arXiv for preprints; publisher and society sites; university repositories and theses; discipline indexes; standards bodies; books; and official manufacturer notes. Google Scholar may broaden discovery when available. Report access limits and API/tool failures.

## Search log columns

Use exactly these columns in `search_log.csv`:

```text
search_id,date,database_or_site,layer,query,filters,result_count,retained_ids,decision_or_refinement,status
```

Allowed status examples: `completed`, `empty`, `blocked`, `tool_failure`, `superseded`. Quote CSV fields containing commas.

## Screening and deduplication

Deduplicate in this order:

1. normalized DOI;
2. arXiv, ISBN, standard, report, thesis, or other stable ID;
3. normalized title plus year;
4. manual comparison for preprint/published-version pairs.

Prefer the version with the clearest provenance and fullest methods. Link alternate versions instead of counting them twice.

Record an inclusion reason tied to a causal link or decision. Record exclusions; do not discard a source merely because it contradicts the initial mechanism.

## Citation verification

Before citing, verify title, authors, year, venue, and DOI/stable identifier against the source or a reliable metadata service. A DOI-shaped string is not proof that a work exists. Follow DOI redirects only to confirm identity; do not infer inaccessible full-text content.

Label evidence access as `full_text`, `partial_text`, `abstract_only`, `metadata_only`, or `blocked`. For equations and central claims record page, section, equation, figure, table, or another exact location whenever accessible.

## Claim and equation labels

Classify claim handling as:

- `direct_quote`: short exact text with location;
- `paraphrase`: source meaning in original words;
- `derived_result`: new consequence with assumptions and steps;
- `working_hypothesis`: unverified proposal.

Classify equation provenance as:

- `verbatim_source_equation`;
- `adapted_source_equation`;
- `derived_from_cited_principles`;
- `original_derivation`;
- `empirical_fit_from_data`;
- `assumed_placeholder_pending_measurement`.

Never reconstruct missing equations, limitations, or parameter values from an abstract. Represent disagreement explicitly and preserve the source-specific regime.

For each retrieved full-text equation, verify and record the most granular available locator. A
homepage, landing page, or abstract is not enough. If the locator remains unavailable after
primary/canonical alternative searches, record the searches, `not_retrieved` or `not_available`,
and the exact support limit.

## Evidence coverage matrix

For each source, mark which links it covers, whether coverage is direct or analogous, and whether it supports, contradicts, bounds, or merely motivates a candidate. A review summary is not direct primary evidence when the cited primary paper is accessible.

## Graceful fallback

When network, PDF extraction, APIs, or parallel workers are unavailable:

1. search accessible channels sequentially;
2. log the unavailable channel and error;
3. retain metadata-only records only as leads;
4. mark unsupported links unresolved;
5. select `insufficient_evidence_to_select` when central verification is impossible;
6. never substitute invented references or padded sources.
