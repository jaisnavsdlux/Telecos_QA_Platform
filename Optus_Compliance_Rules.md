# Optus Compliance Rules Library (Raw YAML)

## R001.yaml

```yaml
id: R001
name: Correct drawing template must be used based on input watermark
type: medium

match_keywords:
  - optus
  - template
  - watermark
  - draft
  - child

validation_mode: hybrid

complexity: conditional_template_validation

required_references:
  - Input_Drawing
  - Output_Drawing

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that the correct drawing template is used in the output
  based on watermark presence in the FIRST PAGE of the input drawing.

# -----------------------------
# SCOPE
# -----------------------------
scope: |-
  - ONLY Page 1 of input drawing → watermark detection
  - All output sheets → template consistency

# -----------------------------
# DECISION LOGIC (CORE)
# -----------------------------
decision_logic: |-
  Step 1: Extract Page 1 of input drawing

  Step 2: Detect watermark on Page 1:

      Indicators:
        • Diagonal large text
        • Contains "CHILD"
        • Contains "CPS"
        • Contains "EJV"
        • Contains "DO NOT REMOVE THIS WATERMARK"

  Step 3:

      IF watermark present:
          Expected → Child CAD template

      IF watermark NOT present:
          Expected → Optus standard template

  Step 4: Validate output template across all sheets

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - Watermark correctly detected on Page 1

  AND

  - Output template matches expected:

      CASE 1: Watermark present
          → Output uses child CAD template

      CASE 2: No watermark
          → Output uses Optus standard template

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Watermark present but:
      • Output uses standard Optus template

  - No watermark but:
      • Output uses child CAD template

  - Output template inconsistent across sheets

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - Page 1 not available

  - Watermark partially visible or unreadable

  - Output template cannot be identified

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: watermark_detection
    keywords:
      - child
      - cps
      - ejv
      - watermark
      - draft
    pass_evidence: 'Watermark indicators detected: {found}'
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: watermark_classification
    description: Detect watermark on first page
    logic: |-
      Identify:
        • Diagonal overlay text
        • Large semi-transparent text
        • Keywords: CHILD, CPS, EJV

  - check: template_classification
    description: Identify output template type
    logic: |-
      Classify:
        • Child CAD template
        • Optus standard template

  - check: template_mapping
    description: Validate correct mapping
    logic: |-
      Map:
        Input (Page 1 watermark) → Expected template → Output template

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - lowercase text
  - trim spaces

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT check watermark beyond Page 1
  - Do NOT assume template based only on "OPTUS"
  - Do NOT ignore diagonal watermark patterns
  - Do NOT validate only one sheet → check all output sheets

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Watermark appears ONLY on first page

  - Example watermark:
      "CHILD 1: CPS TECH_5G (EJV)"

  - Watermark is diagonal and semi-transparent

  - Presence of watermark indicates:
      → Child CAD template required

  - Absence indicates:
      → Optus standard template required

  - This rule ensures correct template usage based on drawing lifecycle
```

---

## R002.yaml

```yaml
id: R002
name: Drawing sheets must have valid standard scale
type: low

match_keywords:
  - scale
  - drawing scale

validation_mode: auto

description: |-
  Validate that applicable drawing sheets contain a valid numeric scale ratio.
  Scale can appear ANYWHERE in the sheet (title, detail callouts, elevation labels, etc.).

  Validation must be performed PER SHEET, not globally.

scope: |-
  Apply ONLY to:
    - G2 (Overall Site Plan)
    - G3 (Site Layout)
    - G3-1 (Antenna Layout)
    - G4 (Elevation)
    - F1 (Shelter Layout)

  Do NOT validate:
    - Cover sheet
    - G1
    - A-series (A1, A2, A3)
    - P-series (P1)
    - E-series
    - Reference/OSD sheets

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  For EACH applicable sheet:

  - A valid scale is present AND
  - The scale matches a standard value

  Accepted:
    - Main scale (e.g., 1:1000, 1:500)
    - Detail scale (e.g., "DETAIL SCALE 1:20") if main scale not present

  At least ONE valid scale per sheet is required.

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  FAIL if ANY applicable sheet:

  - Has NO scale present OR
  - Uses a non-standard scale (e.g., 1:15, 1:30) OR
  - Contains invalid numeric format (e.g., 1:12345 not in standard list)

# -----------------------------
# EXPECTED PATTERNS (ROBUST)
# -----------------------------
expected_patterns:
  - '1\s*:\s*\d+'
  - 'SCALE\s*1\s*:\s*\d+'
  - 'DETAIL\s*SCALE\s*1\s*:\s*\d+'

# -----------------------------
# STANDARD SCALE LIST
# -----------------------------
standard_scales:
  - 1:1
  - 1:2
  - 1:5
  - 1:10
  - 1:20
  - 1:25
  - 1:50
  - 1:100
  - 1:200
  - 1:250
  - 1:500
  - 1:1000
  - 1:2000
  - 1:2500
  - 1:5000

# -----------------------------
# NON-STANDARD (STRICT FAIL)
# -----------------------------
non_standard_scales:
  - 1:15
  - 1:30

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - remove spaces around colon (1 : 1000 → 1:1000)
  - uppercase text
  - trim whitespace

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT check non-drawing sheets (Cover, G1, A, P, E)
  - Do NOT fail if ONLY detail scale is present (acceptable fallback)
  - Do NOT fail 1:2000 or 1:2500 (valid for large site plans)
  - Do NOT assume one sheet scale applies to all sheets

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: regex_search
    patterns:
      - '1\s*:\s*\d+'
    pass_evidence: 'Scale detected: {match}'
    fail_evidence: 'No scale pattern found'

  - check: standard_scale_validation
    logic: |-
      Extract detected scale → normalize → compare with standard_scales list
    pass_evidence: 'Valid standard scale: {match}'
    fail_evidence: 'Non-standard scale detected'
```

---

## R003.yaml

```yaml
id: R003
name: Check scale with viewport
type: high
match_keywords:
- check scale with viewport
- scale with viewport
validation_mode: cad_only
description: |-
  The displayed (annotated) scale in the drawing should match the viewport scale. When CAD access is not available, validation is limited to checking whether the visible annotated scale is present, follows standard or acceptable scale conventions, and appears consistent across the drawing or viewport labels.
pass_criteria: |-
  A clearly visible scale (e.g., 1:100, 1:200) is present in the drawing, follows standard or acceptable scale conventions, and no conflicting scale values are observed within the same view.
fail_criteria: |-
  Scale is missing, multiple conflicting scales are visible in the same view, or a non-standard scale (e.g., 1:75, 1:150, 1:300, 1:600) is used.
expected_patterns:
- '1:1'
- '1:2'
- '1:5'
- '1:10'
- '1:20'
- '1:25'
- '1:50'
- 1:75
- 1:100
- 1:125
- 1:150
- 1:200
- 1:250
- 1:300
- 1:400
- 1:500
- 1:600
- 1:800
- 1:1000
- 1:2000
- 1:5000
non_standard_patterns:
- 1:75
- 1:150
- 1:300
- 1:600
```

---

## R004.yaml

```yaml
id: R004
name: FC stamp is correctly mentioned to all sheets?
type: high
match_keywords:
- fc stamp
- draft watermark
validation_mode: auto
description: |-
  All sheets must contain a visible 'DRAFT' watermark (FC stamp). 'FOR CONSTRUCTION' stamp should not be considered for this check.
pass_criteria: The 'DRAFT' watermark is clearly visible on all sheets/pages in the
  document.
fail_criteria: The 'DRAFT' watermark is missing from one or more sheets/pages.
expected_patterns:
- DRAFT
```

---

## R005.yaml

```yaml
id: R005
name: Layer usage must follow existing vs proposed standards
type: medium

match_keywords:
  - layers correctly followed
  - layer naming
  - cad layer standards

validation_mode: cad_only

required_references:
  - As-built
  - Optus CAD Template (Model Space)

description: |-
  Validate that CAD layer usage follows telecom drafting standards:
  - Existing elements must be represented using unbold/light layers
  - Proposed/New/Modified elements must be represented using bold/high-visibility layers
  - Layer conventions must align with Optus CAD template standards and As-built references

scope: |-
  Applies to all CAD drawings including layout, elevation, and detail sheets.
  Special conditional rules apply for G1 sheet and text/callouts.

pass_criteria: |-
  - All existing elements are drawn in unbold/light layers
  - All proposed/new/relocated/removed elements are drawn in bold layers
  - Headings, notes, and structural notes are consistently in bold layers
  - Callouts follow keyword-based formatting rules
  - G1 sheet follows conditional formatting rules

fail_criteria: |-
  - Existing elements are shown in bold layers
  - Proposed/new/relocated/removed elements are shown in unbold/light layers
  - Layer usage does not match Optus CAD template conventions
  - Callout text contradicts visual layer formatting (e.g., "Existing" shown in bold)
  - Structural notes or headings are not in bold layers

layer_rules:
  existing_elements:
    expected_style: unbold
    keywords:
      - existing

  proposed_elements:
    expected_style: bold
    keywords:
      - proposed
      - new
      - relocated
      - removed
      - install
      - replace

text_and_annotations:
  headings:
    expected_style: bold

  notes:
    expected_style: bold

  structural_notes:
    expected_style: bold

callout_rules:
  - condition: contains "Existing"
    expected_style: unbold

  - condition: contains any of ["Proposed", "New", "Relocated", "Removed", "Install", "Replace"]
    expected_style: bold

g1_sheet_exceptions:
  equipment_shelter:
    heading: bold
    content: unbold
    exception: content may be bold if new cabinet or modification is proposed

  transmission:
    heading: bold
    content: unbold
    exception: content may be bold if new dish or fibre is proposed

negative_constraints:
  - Do NOT fail if G1 sheet follows its defined exceptions
  - Do NOT fail mixed styles where justified by explicit design intent (e.g., highlighting changes)
  - Do NOT rely solely on color; validate using layer properties (line weight, style)

notes: |-
  - Refer to "3-Optus FC Template Layer Format" and "4-Child CAD Template Layer Format" in Model Space
  - Validation should compare against As-built drawings to distinguish existing vs proposed elements
  - Layer validation must consider both visual style (bold/unbold) and semantic meaning (based on text/callouts)
```

---

## R006.yaml

```yaml
id: R006
name: All drafting text must be in uppercase
type: medium

match_keywords:
  - uppercase font
  - all text uppercase

validation_mode: hybrid

complexity: text_classification + formatting

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that drafting text (callouts, labels, annotations) is in uppercase.

  This rule applies ONLY to finalized drafting content in FC drawings.

  Text originating from markup layers, RLM drawings, redlines,
  or review annotations must be excluded from validation.

# -----------------------------
# SCOPE
# -----------------------------
scope: |-
  Apply ONLY to:
    - Callouts (equipment, antenna, signage, etc.)
    - Labels
    - Drawing annotations
    - Titles outside title block

  Do NOT apply to:
    - Imported/reference drawings
    - Markup/redline content
    - Narrative notes

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  PASS if:
  - All drafting text is uppercase
  - Any lowercase text appears ONLY in excluded zones or allowed exceptions
  - No lowercase text in finalized drawing callouts

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  FAIL if:
  - Lowercase or mixed-case text appears in drafting elements
  - Text is clearly part of finalized drawing (not markup/reference)

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - Unable to determine if text belongs to:
      • Drafting layer OR
      • Markup/redline/reference

  - OCR ambiguity in text extraction

# -----------------------------
# EXPECTED PATTERN
# -----------------------------
expected_patterns:
  - '^[A-Z0-9\s\W]+$'

# -----------------------------
# TEXT SOURCE CLASSIFICATION (CRITICAL)
# -----------------------------
text_source_rules:

  drafting_text:
    description: Final CAD drawing content
    validate: true

  markup_text:
    description: Redline, review comments, engineer notes
    indicators:
      - mixed_case_phrasing
      - informal language (e.g., "previous", "check", "revise")
      - clouded or arrow-linked text
    validate: false

  reference_text:
    description: Imported As-built / RLM / external references
    validate: false

# -----------------------------
# EXCLUDED ZONES
# -----------------------------
excluded_zones:

  bottom_title_block:
    description: Title block and revision area
    rule: Skip validation

  narrative_notes:
    description: Safety, WHS, hazard, general notes
    keywords:
      - hazard
      - safety
      - whs
      - warning
      - note
    rule: Skip validation

  legends_tables:
    description: Legends, tables, schedules
    rule: Skip validation

# -----------------------------
# ALLOWED EXCEPTIONS
# -----------------------------
allowed_exceptions:

  email_ids:
    pattern: '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}'

  units:
    allowed_values:
      - m
      - km
      - mm
      - kg

  program_names:
    allowed_values:
      - eJV

  proper_nouns:
    description: Brand names, company names, product codes are exempt from uppercase enforcement
    examples:
      - Civilmart
      - iDCDP
      - RLM
      - Nokia
      - Huawei
      - Ericsson
      - CommScope
    rule: Do NOT fail text that is clearly a proper noun or registered brand name

  product_codes:
    description: Manufacturer part numbers and model codes may contain mixed case
    rule: Do NOT flag model numbers, part codes, or product identifiers

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - ignore excluded zones
  - trim whitespace

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT validate markup/redline text
  - Do NOT validate imported RLM/As-built text
  - Do NOT validate narrative notes
  - Do NOT validate title block
  - Do NOT flag units or email IDs
  - Do NOT assume all visible text is drafting text
  - Do NOT over-report (limit violations)

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Drafting standard requires uppercase text for clarity and consistency

  - Source-of-truth FC drawings confirm all finalized drafting text is uppercase

  - Most false FAILs occur due to:
      • Markup/redline text
      • Imported As-built annotations
      • Narrative notes

  - This rule depends on correct text classification before validation

  - If classification is uncertain → return UNCLEAR instead of FAIL 
```

---

## R007.yaml

```yaml
id: R007
name: Detect and highlight "Prior to Installation/Fabrication" notes
type: high

match_keywords:
  - prior to installation
  - prior to fabrication
  - structural MU

validation_mode: hybrid

description: |-
  Detect whether any "PRIOR TO INSTALLATION" or "PRIOR TO FABRICATION"
  notes are present in the drawing set (especially structural sheets).
  If such notes are found, they must be clearly highlighted for DEs & SEs.

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - If notes exist -> they are clearly identified and highlighted (bold/box/callout).
  - OR if no such notes are found in the drawing set, the rule is considered PASSED (Not Applicable).

fail_criteria: |-
  - "PRIOR TO INSTALLATION" or "PRIOR TO FABRICATION" notes are present 
    but NOT identified or highlighted.

# -----------------------------
# EXPECTED PATTERNS
# -----------------------------
expected_patterns:
  - PRIOR TO INSTALLATION
  - PRIOR TO FABRICATION
  - BEFORE INSTALLATION
  - PRE[- ]FABRICATION

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: note_presence_detection
    regex_patterns:
      - 'PRIOR TO INSTALLATION'
      - 'PRIOR TO FABRICATION'
      - 'BEFORE INSTALLATION'
      - 'PRE[- ]FABRICATION'
    pass_evidence: 'Relevant note found: {match}'
    fail_verdict: NOT_APPLICABLE
    fail_evidence: 'No prior-to-installation/fabrication notes found'

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: highlight_detection
    description: |-
      If note is present, verify it is emphasized using:
        • bold text
        • boxed note
        • callout
        • separate instruction block

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT fail if notes are not present
  - Do NOT assume structural MU notes must exist
  - Do NOT restrict search only to G1/G2; include structural sheets if available

# -----------------------------
# OUTPUT LOGIC
# -----------------------------
output_logic: |-
  IF note_found = false:
      verdict = PASS
      status = NOT_APPLICABLE

  IF note_found = true:
      evaluate highlight → PASS or FAIL

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - This is a conditional detection rule, not a mandatory presence rule
  - Most projects may not contain such notes
  - Focus should be on detection accuracy first, then highlighting validation
```

---

## R008.yaml

```yaml
id: R008
name: Site identity must match RFNSA (Master Rule)
type: high

validation_mode: hybrid

required_references:
  - RFNSA

description: |-
  Master validation rule for site identity.
  Validates that core site identity in FC drawings matches RFNSA.

  Fields validated:
    - Site ID (PRIMARY KEY)
    - Site Name
    - Address (Lot / Plan / Street)
    - JV (if applicable)

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - Site ID matches RFNSA EXACTLY
  - Site Name matches (minor formatting allowed)
  - Address matches:
      • Lot number
      • Plan number
      • Street name

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Site ID mismatch (CRITICAL FAIL)
  - Address mismatch in:
      • Lot number
      • Plan number
  - Site Name mismatch (major difference)

# -----------------------------
# PRIORITY LOGIC
# -----------------------------
priority_logic: |-
  Site ID → Highest priority
  Address → Second priority
  Site Name → Supporting

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - uppercase all text
  - remove commas
  - normalize lot/plan keywords
  - trim spaces

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT duplicate validation done in R025/R026/R027
  - Do NOT fail due to formatting differences
  - If RFNSA missing → return UNCLEAR

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  This is the ONLY rule responsible for final identity validation.
  Other rules (R025, R026, R027) act as supporting checks only.
```

---

## R009.yaml

```yaml
id: R009
name: Structure owner and owner site ID must be correct
type: high

match_keywords:
  - structure owner
  - owner site id

validation_mode: hybrid

required_references:
  - RFNSA

description: |-
  Validate that the structure owner is correctly identified based on RFNSA.
  For third-party infrastructure providers (Indara, Amplitel, BAI), the owner Site ID
  must be present and valid. For Optus-owned structures, no external owner ID is required.

# -----------------------------
# SCOPE
# -----------------------------
scope: |-
  Primary location:
    - Cover sheet
    - G1 (Site Specifications)
    - Title block / structure description

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  PASS if:

  1. RFNSA owner = OPTUS:
     - Drawing shows OPTUS as owner
     - No owner Site ID required

  OR

  2. RFNSA owner in [INDARA, AMPLITEL, BAI]:
     - Owner name matches (after normalization)
     - Owner Site ID is present
     - Owner Site ID follows valid format (alphanumeric / numeric ID)

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  FAIL if:

  - RFNSA owner is third-party BUT:
      • Owner name missing in drawing
      • Owner name mismatch with RFNSA
      • Owner Site ID missing
      • Owner Site ID invalid or not identifiable

  - Incorrect owner shown (e.g., wrong company)

# -----------------------------
# EXPECTED PATTERNS
# -----------------------------
expected_patterns:
  - '(?i)indara'
  - '(?i)amplitel'
  - '(?i)bai'
  - '(?i)optus'
  - '(?i)pty\s*ltd'
  - '(?i)communications'

# -----------------------------
# OWNER ID PATTERN
# -----------------------------
owner_id_patterns:
  - '\b[A-Z0-9]{5,10}\b'   # generic alphanumeric ID
  - '\b\d{5,10}\b'         # numeric ID

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - lowercase all text
  - trim spaces
  - telstra → amplitel
  - remove "pty ltd", "communications"

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: owner_detection
    keywords:
      - indara
      - amplitel
      - bai
      - optus
    pass_evidence: 'Owner detected: {found}'
    fail_evidence: 'No recognizable structure owner found'

  - check: owner_id_detection
    regex_patterns:
      - '\b[A-Z0-9]{5,10}\b'
      - '\b\d{5,10}\b'
    pass_evidence: 'Owner Site ID detected: {match}'
    fail_evidence: 'Owner Site ID not found'

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: rfsna_owner_extraction
    description: Extract structure owner from RFNSA

  - check: fc_owner_extraction
    description: Extract structure owner from drawing

  - check: owner_normalization
    description: Normalize ownership values
    logic: |-
      TELSTRA → AMPLITEL

  - check: owner_comparison
    description: Compare RFNSA vs drawing owner after normalization

# -----------------------------
# CONDITIONAL LOGIC
# -----------------------------
conditional_logic: |-
  IF RFNSA owner = OPTUS:
      PASS (no owner site ID required)

  IF RFNSA owner in [INDARA, AMPLITEL, BAI]:
      REQUIRE:
        - owner match
        - owner site ID present

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT require owner Site ID for Optus-owned structures
  - Do NOT fail if Telstra is used instead of Amplitel (legacy naming)
  - Do NOT assume all sites are shared infrastructure
  - Do NOT accept random numeric values as owner ID without context

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - RFNSA is the source of truth for ownership
  - Telstra structures are now typically owned by Amplitel
  - Owner Site ID is required ONLY for third-party infrastructure
  - This is a conditional validation rule based on ownership type
```

---

## R010.yaml

```yaml
id: R010
name: Work authority number must be valid and consistent across documents
type: high

match_keywords:
  - work authority number
  - work authority
  - WA number

validation_mode: hybrid

required_references:
  - Form_A
  - FR

description: |-
  Validate that the Work Authority (WA) Number is correctly defined and consistent.
  The WA number is a 6-digit identifier typically found:
    - In the Cover Sheet (under upgrade / 5G(eJV) section)
    - In the Feasibility Report (FR) – Scope of Works section
    - In Form A (or file name)

# -----------------------------
# SCOPE
# -----------------------------
scope: |-
  Primary extraction:
    - Cover sheet

  Cross-reference:
    - FR (Scope of Works / Antenna System tab)
    - Form A (content or filename)

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  PASS if:

  - A 6-digit WA number is found in the cover sheet with correct context AND
  - The same WA number is found in:
      • FR (Scope of Works / Antenna System section)
      • OR Form A (content or filename)
  - All detected WA numbers match exactly

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  FAIL if:

  - WA number is missing in cover sheet
  - WA number is not 6 digits
  - WA number is found but:
      • Does not match FR or Form A
      • Multiple conflicting WA numbers exist
  - A 6-digit number is detected WITHOUT proper context (false extraction)

# -----------------------------
# EXPECTED PATTERNS (STRICT)
# -----------------------------
expected_patterns:
  - '(?i)work\s*authority\s*(number|no\.?|id)?[\s:\-]*\d{6}'
  - '(?i)\bwa\s*(number|no\.?|id)?[\s:\-]*\d{6}'

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - lowercase all text
  - remove extra spaces
  - standardize "wa", "work authority"

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: regex_search
    patterns:
      - '(?i)work\s*authority\s*(number|no\.?|id)?[\s:\-]*(\d{6})'
      - '(?i)\bwa\s*(number|no\.?|id)?[\s:\-]*(\d{6})'
    pass_evidence: 'WA number detected with context: {match}'
    fail_evidence: 'No valid WA number found with proper context'

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: cover_wa_extraction
    description: Extract WA number from cover sheet (primary source)

  - check: fr_wa_extraction
    description: Extract WA number from FR (Scope of Works / Antenna System)

  - check: forma_wa_extraction
    description: Extract WA number from Form A (content or filename)

  - check: wa_comparison
    description: Ensure all extracted WA numbers match

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT accept standalone 6-digit numbers without WA context
  - Do NOT extract WA from unrelated sections (e.g., plan numbers, drawing numbers)
  - Do NOT pass if multiple WA numbers conflict
  - Do NOT rely only on regex without context validation

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - WA number is a critical identifier across project documentation
  - FR (Feasibility Report) is usually the most reliable source
  - Form A filename often includes WA number
  - Context-based extraction is mandatory to avoid false positives
```

---

## R011.yaml

```yaml
id: R011
name: Client and Vendor logos must be correctly present (template-level validation)
type: high

validation_mode: hybrid

description: |-
  Validate that correct client and vendor logos are present in the drawing set.
  This is a TEMPLATE-LEVEL validation, not strictly per-sheet.

  IMPORTANT:
  Logos may appear as graphical elements and may not be extractable as text.
  Therefore, absence in text extraction does NOT imply absence in drawing.

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. Cover sheet (primary truth)
  2. Any FC sheet (template confirmation)
  3. Text extraction (support only)

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  PASS if ANY of the following is true:

  CASE 1: Cover Sheet Validation
    - Correct client (OPTUS) and vendor (CPS/Service Stream) logos
      are present in the cover sheet

  CASE 2: Template Consistency
    - Logos detected in at least one FC sheet
    - No evidence of incorrect/mismatched logos
    → Assume template consistency → PASS

  CASE 3: Text Confirmation (secondary)
    - Client/vendor names appear in title block text
    - No conflicting branding detected

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  FAIL ONLY if:

  - Logos are missing in BOTH:
      • Cover sheet
      • AND all FC sheets

  OR

  - Incorrect client/vendor branding is present
    (e.g., wrong telecom, wrong vendor)

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - Cover sheet not available
  - Title block not visible
  - Logo region not extractable

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT rely only on text extraction for logo detection
  - Do NOT require logos to be detected on every sheet
  - Do NOT fail based on partial OCR extraction
  - Do NOT fail if logos are visible but not text-extractable

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Telecom drawings use a consistent title block template
  - If logos are present in the cover sheet, they apply to all sheets
  - Visual presence overrides text extraction
```

---

## R012.yaml

```yaml
id: R012
name: Cover sheet drawing list must align with As-built reference and project scope
type: medium

match_keywords:
  - drawing index
  - cover sheet
  - sheet list

validation_mode: hybrid

complexity: cross_document + structural_alignment

required_references:
  - FC_Drawings

optional_references:
  - As-built

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that the drawing list in the FC (For Construction) cover sheet
  aligns with the As-built reference and reflects the current project scope.

  This includes:
  - Sheet structure (prefix + numbering)
  - Discipline naming
  - Revision usage
  - Scope-based inclusion/exclusion

# -----------------------------
# SCOPE
# -----------------------------
scope: |-
  - Cover sheet only (drawing index)
  - Section headings + sheet list

location_hint:
  region: drawing_index_section

# -----------------------------
# DECISION FLOW (CRITICAL)
# -----------------------------
decision_flow: |-
  Step 1: Extract FC drawing list

  Step 2: Check if As-built reference is available

    IF As-built NOT available:
        → Perform partial validation (structure + revision only)

    IF As-built available:
        → Perform full validation (alignment + scope + naming)

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  STEP 1: Structure Validation

  - Sheet IDs follow correct prefixes:
      • G → General
      • A → Antenna
      • P → Plumbing
      • T → Transmission
      • S → Structural
      • E → Electrical
      • F → Shelter

  ------------------------------------------------

  STEP 2: Revision Validation

  - FC sheets use revision "A"

  - As-built reference uses revision "AB" (if provided)

  ------------------------------------------------

  STEP 3: Cross-Reference Alignment (if As-built available)

  - FC sheet list aligns with As-built:
      • Prefix consistency
      • Logical sheet numbering
      • Comparable titles

  ------------------------------------------------

  STEP 4: Scope Filtering

  - Only relevant disciplines included

  - Irrelevant sheets removed OR justified

  ------------------------------------------------

  STEP 5: Naming Correction

  - Plumbing sheets must use P-series (NOT A-series)

  ------------------------------------------------

  FINAL:

  - Drawing index is structurally correct, logically aligned, and scope-consistent

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Incorrect sheet prefixes (e.g., plumbing shown as A-series)

  - FC drawings not using revision "A"

  - Major mismatch with As-built structure (if reference available)

  - Irrelevant sheets included without justification

  - Required sheets missing without scope-based reasoning

  - Inconsistent or broken numbering sequence

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - As-built reference not provided (limits full validation)

  - Sheet titles partially readable

  - Scope unclear (cannot determine relevance of sheets)

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: revision_detection
    regex_patterns:
      - '\bA\b'
    pass_evidence: 'Revision A detected in FC'
    fail_verdict: UNCLEAR

  - check: asbuilt_revision_detection
    regex_patterns:
      - '\bAB\b'
    pass_evidence: 'As-built revision detected'
    fail_verdict: UNCLEAR

  - check: sheet_id_detection
    regex_patterns:
      - '\bG\d+\b'
      - '\bA\d+\b'
      - '\bP\d+\b'
      - '\bT\d+\b'
      - '\bS\d+\b'
      - '\bE\d+\b'
      - '\bF\d+\b'
    pass_evidence: 'Sheet IDs detected'
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: fc_extraction
    description: Extract FC drawing index
    logic: |-
      Extract:
        • Sheet IDs
        • Titles
        • Revisions

  - check: asbuilt_extraction
    description: Extract As-built reference (if available)
    logic: |-
      Extract:
        • Sheet structure
        • Naming pattern

  - check: alignment_comparison
    description: Compare FC vs As-built
    logic: |-
      Compare:
        • Prefix consistency
        • Sheet numbering logic
        • Title similarity

  - check: scope_validation
    description: Validate scope-based inclusion/exclusion
    logic: |-
      Ensure:
        • Only relevant disciplines included
        • Removed sheets are logically justified

  - check: naming_validation
    description: Validate discipline naming
    logic: |-
      Ensure:
        • Plumbing uses P-series
        • Legacy naming corrected

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - uppercase text
  - trim spaces

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT require exact 1:1 match with As-built (scope may differ)
  - Do NOT fail if As-built is missing → return partial validation
  - Do NOT assume missing sheets are errors without context
  - Do NOT rely only on sheet count → validate structure

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - As-built is the baseline reference, not an exact template

  - FC must reflect:
      • Updated scope
      • Correct discipline naming
      • Proper revision usage

  - Revision rules:
      • FC → A
      • As-built → AB

  - This rule ensures:
      Structural consistency + scope correctness in drawing index
```

---

## R013.yaml

```yaml
id: R013
name: Remove R references and EME EXCLUSION ZONE from cover sheet for CPS vendor
type: medium

match_keywords:
  - eme exclusion zone
  - remove eme exclusion
  - r reference removal

validation_mode: auto

description: |-
  For CPS vendor drawings, the cover sheet must NOT include:
  - "EME EXCLUSION ZONE" section (both heading and content)
  - Any previous revision references (e.g., "R" revisions or legacy revision details)

  NOTE:
  This rule applies ONLY when the vendor is CPS.

scope: |-
  Applies ONLY to the cover sheet.

applicability_condition: |-
  Apply this rule ONLY if vendor is identified as "CPS"
  (from title block, logo, or metadata)

pass_criteria: |-
  - "EME EXCLUSION ZONE" section is completely removed (no heading, no content)
  - No previous revision references (e.g., "R") are present in the cover sheet
  - Cover sheet reflects only current project scope

fail_criteria: |-
  - "EME EXCLUSION ZONE" is present in any form (heading or content)
  - Any legacy revision references (e.g., "R") are present
  - Old or irrelevant revision details are retained

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: eme_exclusion_absent
    description: Ensure EME EXCLUSION ZONE is removed
    keywords:
      - eme exclusion zone
      - eme exclusion
    pass_evidence: EME EXCLUSION ZONE not found in cover sheet
    found_verdict: FAIL
    fail_evidence: EME EXCLUSION ZONE present — must be removed for CPS

  - check: r_reference_absent
    description: Ensure legacy revision references are removed
    regex_patterns:
      - '\bREV\s*R\b'
      - '\bR[0-9]*\b'
    pass_evidence: No R revision references found
    found_verdict: FAIL
    fail_evidence: R revision reference found — must be removed for CPS

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT apply this rule if vendor is not CPS
  - Do NOT fail if EME EXCLUSION ZONE is absent (this is expected)
  - Ignore revision references outside cover sheet

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Unlike other sections, EME EXCLUSION ZONE must be fully removed (not just content, but also heading)
  - This is a strict vendor-specific requirement for CPS
  - Vendor identification should be derived from logo, title block, or metadata
  - Ensure distinction between current revision (A) and legacy revision (R)
```

---

## R014.yaml

```yaml
id: R014
name: MERC signage must comply with Optus OSD requirements based on site type
type: medium

match_keywords:
  - merc signage
  - osd-171
  - signage legend

validation_mode: auto

required_references:
  - OSD-171-1
  - OSD-171-2

description: |-
  Validate that MERC signage in the FC pack complies with the latest Optus OSD standards 
  based on the site type (Ground / Rooftop / Water tank).

  NOTE:
  The required reference documents (OSD-171-1 and OSD-171-2) will be provided/uploaded 
  as inputs during validation. These must be used as the baseline for verification.

scope: |-
  Applies to:
  - Cover sheet (primary validation for sheet inclusion)
  - Supporting drawings and signage references

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - OSD-100 is present for all sites
  - OSD-171-3 (signage legend and notes) is present for all sites

  Based on site type:

  • Ground site:
      - OSD-171-1 must be present

  • Rooftop / Water tank site:
      - OSD-171-2 must be present

  • Rooftop / Water tank site with shelter on ground:
      - BOTH OSD-171-1 and OSD-171-2 must be present

  - Correct OSD references are listed in the cover sheet

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Missing mandatory sheets (OSD-100 or OSD-171-3)
  - Incorrect OSD sheet included for site type
  - Required OSD sheets not present
  - Mismatch between site type and OSD references
  - Cover sheet does not list required OSD sheets

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: osd_presence
    description: Detect OSD references
    regex_patterns:
      - '\bOSD[-\s]?100\b'
      - '\bOSD[-\s]?171[-\s]?1\b'
      - '\bOSD[-\s]?171[-\s]?2\b'
      - '\bOSD[-\s]?171[-\s]?3\b'
    pass_evidence: OSD references detected
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: site_type_detection
    description: Identify site type from cover sheet or drawings
    logic: |-
      - Detect keywords:
          • "rooftop", "roof", "building", "watertower" → Rooftop site
          • Otherwise → Ground site

  - check: osd_mapping_validation
    description: Validate correct OSD mapping based on site type
    logic: |-
      - Ground site → must include OSD-171-1
      - Rooftop/water tank → must include OSD-171-2
      - Rooftop with ground shelter → must include BOTH 171-1 and 171-2
      - All cases → must include OSD-171-3

  - check: cover_sheet_validation
    description: Validate OSD references listed in cover sheet
    logic: |-
      - Extract drawing list from cover sheet
      - Verify required OSD sheets are listed

  - check: optional_photo_validation
    description: Cross-check site type using site photos (if available)
    logic: |-
      - Detect rooftop vs ground visually
      - Use as supporting evidence (not mandatory)

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT fail if reference documents are not uploaded → return UNCLEAR
  - Allow minor naming variations (e.g., "OSD 171-1", "OSD-171 1")
  - Do NOT rely solely on keyword presence; must validate against site type

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - OSD-100 and OSD-171-3 are mandatory for ALL projects
  - OSD-171-1 and OSD-171-2 are conditional based on site type
  - Validation must combine:
      • Cover sheet analysis
      • Site type detection
      • Optional visual/photo confirmation
  - Reference documents (OSD-171-1, OSD-171-2) must be used for verification when provided
```

---

## R015.yaml

```yaml
id: R015
name: Program name must match FR reference
type: medium

match_keywords:
  - program name
  - project type
  - deployment type

validation_mode: auto

required_references:
  - FR

description: |-
  Validate that the program name in the drawing matches the program defined 
  in the FR (Feasibility Report).

  Program types include:
  - eJV (Joint Venture)
  - OO (Optus Only)
  - MOCN (Multi-Operator Core Network)

  NOTE:
  The FR document will be provided/uploaded as an input.
  The program name must be extracted from structured FR fields and 
  validated against the drawing (cover sheet/title block).

scope: |-
  - FR document (source of truth)
  - Drawing cover sheet / title block

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - Program name is correctly extracted from FR
  - Program name is present in the drawing
  - Program name in drawing matches FR value

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Program name not found in FR
  - Program name not found in drawing
  - Program name mismatch between FR and drawing

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: drawing_program_presence
    description: Detect program name in drawing
    regex_patterns:
      - \bejv\b
      - \bmocn\b
      - \boo\b
    pass_evidence: 'Program name found in drawing: {found}'
    fail_evidence: Program name not found in drawing
    fail_verdict: FAIL

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: fr_program_extraction
    description: Extract program name from FR structured fields
    logic: |-
      - Look for fields like:
          • Program
          • Project Type
          • Deployment Type
      - Extract value associated with these fields
      - Normalize to one of:
          • eJV
          • OO
          • MOCN

  - check: program_alignment
    description: Compare FR vs drawing
    logic: |-
      - Extract program name from FR
      - Extract program name from drawing
      - Normalize both values
      - Compare for equality
    pass_condition: Exact match
    fail_condition: Mismatch

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - 'ejv → eJV'
  - "'e j v' → eJV"
  - 'mocn → MOCN'
  - "'multi operator core network' → MOCN"
  - 'oo → OO'
  - "'optus only' → OO"

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT fail if FR is not uploaded → return UNCLEAR
  - Do NOT rely on random keyword matches; prioritize structured fields
  - Ignore program mentions in revision blocks or notes

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - FR is the source of truth for program type
  - Program name must be extracted from structured fields, not inferred
  - Drawing must reflect the same program name (usually in cover sheet)
  - This is a cross-document validation rule (FR ↔ Drawing)
```

---

## R016.yaml

```yaml
id: R016
name: Structural certificates must match cover sheet and follow correct sequence and date logic
type: medium

match_keywords:
  - structural certificate
  - pole certificate
  - foundation certificate
  - mount certificate
  - headframe

validation_mode: auto

required_references:
  - Pole_Certificate
  - Mount_Certificate
  - Foundation_Certificate

description: |-
  Validate that structural certificates (Foundation, Pole, Mount/Headframe):

  - Are correctly referenced in the FC drawing cover sheet
  - Have matching names and dates with uploaded certificates
  - Follow correct engineering sequence
  - Maintain logical chronological order
  - Align with FC issue date

  NOTE:
  Reference certificates will be uploaded and must be used as source of truth.

scope: |-
  - FC cover sheet (primary validation)
  - Foundation certificate
  - Pole certificate
  - Mount/Headframe certificate

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - All required certificates are referenced in cover sheet:
      • Foundation certificate
      • Pole certificate
      • Mount/Headframe certificate

  - Certificate names match uploaded documents

  - Certificate dates match uploaded documents

  - Correct sequence is followed:
      1. Foundation certificate
      2. Pole certificate
      3. Mount/Headframe certificate
      4. Mount/Headframe drawing

  - Dates follow logical chronological order:
      Foundation ≤ Pole ≤ Mount ≤ FC issue date

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Missing certificate reference in cover sheet
  - Name mismatch between certificate and cover sheet
  - Date mismatch between certificate and cover sheet
  - Incorrect certificate order
  - Invalid chronological order (e.g., mount before pole)
  - FC issue date earlier than certificate date

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: certificate_reference_presence
    keywords:
      - foundation cert
      - pole cert
      - mount cert
      - headframe
    pass_evidence: Certificate references found
    fail_evidence: Missing certificate references
    fail_verdict: FAIL

  - check: date_detection
    regex_patterns:
      - '\d{2}[-/]\d{2}[-/]\d{4}'
      - '\d{2}-[A-Za-z]{3}-\d{2,4}'
    pass_evidence: Dates detected
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: certificate_extraction
    logic: |-
      Extract:
        • Certificate name / ID
        • Date
        • Drawing reference (if any)

  - check: cover_sheet_extraction
    logic: |-
      Extract:
        • Certificate references
        • Dates
        • FC issue date

  - check: name_matching
    logic: |-
      Compare certificate identifiers with cover sheet

  - check: date_matching
    logic: |-
      Compare certificate dates with cover sheet values

  - check: chronological_validation
    logic: |-
      Ensure:
        Foundation ≤ Pole ≤ Mount ≤ FC

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - "'03-Sep-25' → '2025-09-03'"
  - "'02/09/2025' → '2025-09-02'"
  - "'15/10/2025' → '2025-10-15'"

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT fail if references not uploaded → return UNCLEAR
  - Allow small date gaps (expected across stages)
  - Treat equivalent naming (Headframe = Mount)

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Foundation certificate is the base dependency
  - Pole certificate builds on foundation
  - Mount certificate builds on pole
  - Dates should NOT be identical; they must follow engineering sequence
  - This is a multi-document + temporal validation rule
```

---

## R017.yaml

```yaml
id: R017
name: All required OSD is mentioned or not?
type: medium
match_keywords:
- OSD
- reference documents
- OSD-
- standard drawing
validation_mode: cad_only
description: |-
  Verify that all required Optus Standard Drawings (OSD) are included in the cover sheet based on the proposed scope. If any new steelwork or equipment (e.g., cable ladder, fencing, shelter, cable pit) is proposed, the corresponding OSD reference must be included.
pass_criteria: |-
  All required OSD references corresponding to proposed works are correctly included in the cover sheet.
fail_criteria: |-
  Required OSD references are missing, incomplete, or do not match the proposed scope.
expected_patterns:
- OSD-
```

---

## R018.yaml

```yaml
id: R018
name: ServiceStream sites must include SAED references in documents
type: medium

match_keywords:
  - saed
  - servicestream
  - service stream

validation_mode: hybrid

complexity: conditional_vendor + reference_validation

required_references:
  - FC_Drawings

optional_references:
  - Structural_Certificate

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that SAED references are included ONLY for ServiceStream vendor sites.

  If the site is not a ServiceStream project, this rule is NOT applicable.

# -----------------------------
# DECISION FLOW
# -----------------------------
decision_flow: |-
  Step 1: Detect vendor

    Priority:
      1. Title block (FC drawings)
      2. Structural certificate
      3. Other reference documents

  Step 2:

    IF vendor = ServiceStream:
        → SAED reference is REQUIRED

    IF vendor ≠ ServiceStream:
        → Rule NOT applicable → NOT_APPLICABLE

    IF vendor cannot be determined:
        → UNCLEAR

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  CASE 1: ServiceStream site

  - SAED reference present in:
      • Reference documents OR
      • FC drawing notes

  ------------------------------------------------

  CASE 2: Non-ServiceStream site

  - Rule not applicable → PASS

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Vendor is ServiceStream AND

      • SAED reference missing

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - Vendor not identifiable

  - Reference documents not available

  - SAED mention partially visible or ambiguous

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: vendor_detection
    keywords:
      - servicestream
      - service stream
    pass_evidence: 'ServiceStream vendor detected'
    fail_verdict: UNCLEAR

  - check: saed_detection
    keywords:
      - saed
      - saed_da
      - saed_dc
      - saed_l3
      - saed_lo
    pass_evidence: 'SAED reference detected'
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: vendor_classification
    description: Identify project vendor
    logic: |-
      Extract vendor from:
        • Title block (primary)
        • Structural certificate (secondary)

  - check: saed_reference_validation
    description: Validate SAED reference presence
    logic: |-
      Search for:
        • SAED conditions
        • SAED references in notes or documents

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - lowercase text
  - trim spaces

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT enforce SAED requirement for non-ServiceStream sites
  - Do NOT assume vendor from partial keywords
  - Do NOT fail if vendor cannot be determined → return UNCLEAR
  - Do NOT restrict SAED detection to one document only

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - This is a conditional rule based on vendor

  - ServiceStream → SAED mandatory
  - Others (e.g., CPS) → NOT required

  - Vendor should be primarily identified from title block

  - This rule ensures:
      Correct compliance requirements based on vendor type
```

---

## R019.yaml

```yaml
id: R019
name: Distribution list must match client, vendor, and project manager mapping
type: high

match_keywords:
  - distribution list
  - distribution
  - client
  - vendor

validation_mode: auto

description: |-
  Validate that the distribution list in the cover sheet correctly reflects:
  - Client name
  - Vendor name
  - Corresponding Project Manager (PM)

  Standard mappings:
  - Client: OPTUS → SUHAIB OBAID
  - Vendor: CPS / CPS TECH → BRETT THOMSON
  - Vendor: SERVICE STREAM → SAMINA TABASSUM

scope: |-
  Applies ONLY to the cover sheet.
  The distribution list is typically located at the bottom section of Page 1.

location_hint:
  page: 1
  region: bottom_20_percent

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - Distribution section is present in the cover sheet
  - Client name is present and correctly identified
  - Vendor name is present and correctly identified
  - Corresponding Project Manager names are present
  - Correct mapping is followed:
      • OPTUS → SUHAIB OBAID
      • CPS / CPS TECH → BRETT THOMSON
      • SERVICE STREAM → SAMINA TABASSUM

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Distribution section is missing
  - Client name missing or incorrect
  - Vendor name missing or incorrect
  - Project Manager name missing
  - Incorrect mapping between vendor/client and PM
  - Mismatch between detected vendor and listed PM

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: distribution_section_presence
    description: Detect distribution section
    keywords:
      - distribution
    pass_evidence: Distribution section detected
    fail_evidence: Distribution section not found
    fail_verdict: FAIL

  - check: entity_presence
    description: Detect client, vendor, and PM names
    keywords:
      - optus
      - cps
      - cps tech
      - service stream
      - suhaib obaid
      - brett thomson
      - samina tabassum
    pass_evidence: Required entities detected
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: client_detection
    description: Identify client from distribution section
    logic: |-
      - Extract entity labeled as client (typically OPTUS)

  - check: vendor_detection
    description: Identify vendor from distribution or title block
    logic: |-
      - Detect vendor name:
          • CPS
          • CPS TECH → normalize to CPS
          • SERVICE STREAM

  - check: pm_extraction
    description: Extract project manager names
    logic: |-
      - Extract names associated with client and vendor entries

  - check: mapping_validation
    description: Validate correct mapping between entities and PMs
    logic: |-
      IF client = OPTUS → must include SUHAIB OBAID

      IF vendor = CPS → must include BRETT THOMSON

      IF vendor = SERVICE STREAM → must include SAMINA TABASSUM

    pass_condition: All mappings are correct
    fail_condition: Any mismatch in mapping

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - cps tech → CPS
  - cps → CPS
  - service stream → SERVICE STREAM
  - optus → OPTUS
  - suhaib obaid → SUHAIB OBAID
  - brett thomson → BRETT THOMSON
  - samina tabassum → SAMINA TABASSUM

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT fail for case differences (case-insensitive matching)
  - Allow minor formatting variations (colon, spacing, alignment)
  - Do NOT rely only on keyword presence; mapping validation is mandatory
  - Ignore occurrences outside distribution section

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Distribution list is typically located at the bottom of the cover sheet (Page 1)
  - Vendor name may appear as CPS or CPS TECH; both must be treated as equivalent
  - Vendor can also be validated using logo or title block if ambiguous
  - This is a relational validation rule (entity → role → mapping), not just keyword detection
```

---

## R020.yaml

```yaml
id: R020
name: All drawing sheets must have correct revision "A" in title block
type: high

match_keywords:
  - revision
  - issue
  - title block

validation_mode: auto

description: |-
  Validate that all drawing sheets in the FC package have the correct revision 
  number ("A") in their title blocks.

  The revision must:
  - Be present in each sheet
  - Be consistent across all sheets
  - Match the FC issue standard (typically "A")

  NOTE:
  Reference/standard sheets (e.g., OSD sheets) may have different revisions 
  and must be excluded from validation.

scope: |-
  Applies to all drawing sheets in the FC package.
  Validation must be performed on title block regions of each sheet.

location_hint:
  region: title_block
  typical_position: bottom_right

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - All applicable drawing sheets contain a revision value
  - Revision value is "A" for all sheets
  - Revision is consistent across all sheets

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Revision missing in any sheet
  - Revision value not equal to "A"
  - Inconsistent revision values across sheets

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: revision_detection
    description: Detect revision value in title block
    regex_patterns:
      - '\brev\s*[:\-]?\s*a\b'
      - '\bissue\s*a\b'
    pass_evidence: Revision "A" detected in sheet
    fail_evidence: Revision "A" not found
    fail_verdict: FAIL

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: sheet_iteration
    description: Validate revision across all sheets
    logic: |-
      - Iterate through all pages in the PDF
      - Extract title block region (bottom-right area)
      - Extract revision value from each sheet

  - check: osd_exclusion
    description: Exclude reference/OSD sheets
    logic: |-
      - Identify sheets containing:
          • "OSD"
          • "STANDARD"
          • "REFERENCE"
      - Exclude these sheets from revision validation

  - check: consistency_validation
    description: Ensure all revisions are consistent
    logic: |-
      - Collect revision values from all applicable sheets
      - Verify all values are equal to "A"

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - "'rev a' → 'A'"
  - "'issue a' → 'A'"
  - "'revision a' → 'A'"

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT validate OSD/reference sheets
  - Do NOT fail if OSD sheets have non-"A" revisions
  - Allow minor formatting variations (Rev A, REV:A, Issue A)
  - Do NOT rely only on keyword presence; must extract from title block

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Title block is typically located at the bottom-right of each sheet
  - FC drawings usually start with revision "A"
  - OSD/reference sheets are external standards and may have different revisions
  - This is a multi-sheet consistency validation rule
```

---

## R021.yaml

```yaml
id: R021
name: Drawing number format and site code consistency
type: high

validation_mode: auto

required_references:
  - RFNSA

description: |-
  Validate drawing number format and ensure site code consistency.

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - Drawing number present
  - Contains RFNSA site code
  - Valid format:
      • H8097-00
      • H8097-G1
      • H8097-G3-1

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Missing drawing number
  - Invalid format
  - Site code mismatch

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Ignore spacing variations
  - Ignore OSD/reference sheets

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  This is format + consistency validation.
```

---

## R022.yaml

```yaml
id: R022
name: Drawing titles must match cover sheet mapping
type: high

match_keywords:
  - drawing title
  - title

validation_mode: auto

description: |-
  Validate that drawing titles in each sheet match the titles defined 
  in the cover sheet (drawing index).

  The cover sheet acts as the source of truth for:
  - Sheet number (Drawing No)
  - Corresponding drawing title

  Each sheet must have a title that aligns with its entry in the cover sheet.

scope: |-
  - Cover sheet (page 1)
  - All drawing sheets

location_hint:
  region: title_block_or_top_center

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - Cover sheet contains drawing list with:
      • Drawing number
      • Drawing title

  - Each sheet:
      • Has a drawing title
      • Matches the title defined in cover sheet for that drawing number

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Drawing title missing in any sheet
  - Drawing title does not match cover sheet mapping
  - Incorrect or mismatched title for given drawing number

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: title_presence
    description: Ensure title exists
    keywords:
      - plan
      - diagram
      - layout
      - specifications
    pass_evidence: Title detected
    fail_evidence: Title not found
    fail_verdict: FAIL

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: cover_sheet_mapping_extraction
    description: Extract mapping from cover sheet
    logic: |-
      - From cover sheet extract:
          Drawing No → Title
      - Example:
          H8097-G1 → SITE SPECIFICATIONS
          H8097-G2 → OVERALL SITE PLAN

  - check: sheet_title_extraction
    description: Extract title from each sheet
    logic: |-
      - Extract title from:
          • top center OR
          • title block

  - check: drawing_number_extraction
    description: Extract drawing number
    logic: |-
      - Extract from title block (e.g., H8097-G2)

  - check: mapping_validation
    description: Validate title alignment
    logic: |-
      - For each sheet:
          Find drawing number
          Lookup expected title from cover sheet
          Compare with extracted title

    pass_condition: Titles match
    fail_condition: Mismatch

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - remove extra spaces
  - uppercase comparison
  - ignore minor variations:
      • "PLAN" vs "LAYOUT PLAN"
      • "RF PLUMBING" vs "RF PLUMBING DIAGRAM"

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT rely only on keyword presence
  - Allow minor wording variations
  - Do NOT fail if cover sheet is missing → return UNCLEAR

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Cover sheet is the single source of truth
  - Titles must align with drawing number (not just exist)
  - This is a cross-page validation rule
  - Titles may appear:
      • Top center of sheet
      • Inside title block
```

---

## R023.yaml

```yaml
id: R023
name: Revision details must follow lifecycle and match cover sheet
type: high

match_keywords:
  - revision
  - rev
  - issue

validation_mode: hybrid

complexity: cross_document + lifecycle_validation

required_references:
  - FC_Drawings

optional_references:
  - As-built

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that revision details across FC sheets, cover sheet,
  and As-built reference follow correct lifecycle and are internally consistent.

  IMPORTANT:
  "Matching As-built" means correct progression, not identical values.

# -----------------------------
# SCOPE
# -----------------------------
scope: |-
  - Cover sheet (revision summary)
  - All FC sheet title blocks
  - As-built reference (if available)

# -----------------------------
# DECISION FLOW
# -----------------------------
decision_flow: |-
  Step 1: Extract revision from:
    • Cover sheet
    • All FC sheets

  Step 2: Validate internal consistency:
    → All FC sheets must match cover sheet revision

  Step 3: If As-built available:
    → Validate lifecycle progression

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  STEP 1: FC Consistency

  - All FC sheets use same revision (typically "A")
  - Cover sheet matches FC revision

  ------------------------------------------------

  STEP 2: Lifecycle Alignment (if As-built available)

  - As-built revision exists (e.g., AB)

  - For existing sheets:
      • Sheet exists in As-built
      • FC revision is updated (e.g., AB → A)

  - For new sheets:
      • Not present in As-built
      • Only revision "A" OR no history

  ------------------------------------------------

  FINAL:

  - Revision is consistent and follows correct lifecycle progression

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - FC sheets have inconsistent revisions

  - Cover sheet revision does not match FC sheets

  - FC sheet retains As-built revision (e.g., AB instead of A)

  - Existing sheet not updated from As-built revision

  - Missing revision identifier in title block

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - As-built not available (skip lifecycle check)

  - Revision not readable

  - Sheet mapping between FC and As-built unclear

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: fc_revision_detection
    regex_patterns:
      - '\bA\b'
    pass_evidence: 'FC revision A detected'
    fail_verdict: UNCLEAR

  - check: asbuilt_revision_detection
    regex_patterns:
      - '\bAB\b'
    pass_evidence: 'As-built revision AB detected'
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: cover_revision_extraction
    description: Extract revision from cover sheet

  - check: fc_revision_consistency
    description: Ensure all FC sheets match cover sheet

  - check: sheet_mapping
    description: Match FC sheets to As-built
    logic: |-
      If sheet exists in As-built → existing
      Else → new

  - check: lifecycle_validation
    description: Validate revision progression
    logic: |-
      Existing:
        AB → A (valid)

      Invalid:
        AB → AB (not updated)

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT require FC revision to equal As-built revision
  - Do NOT fail if revision history table is empty
  - Do NOT rely only on revision dates
  - Do NOT validate single sheet only

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Cover sheet is the revision authority

  - As-built provides historical baseline (AB)

  - FC represents new issue (A)

  - Revision history table may be empty for new sheets

  - This rule validates:
      • Internal consistency
      • Correct lifecycle progression
```

---

## R024.yaml

```yaml
id: R024
name: Drawing status must be "FOR CONSTRUCTION" across all sheets
type: high

match_keywords:
  - drawing status
  - for construction

validation_mode: auto

description: |-
  Validate that drawing status in each sheet:
  - Is present in the title block
  - Is set to "FOR CONSTRUCTION"
  - Is consistent across all sheets

  Drawing status is a critical field indicating approval stage.

scope: |-
  Applies to title block of all drawing sheets.

location_hint:
  region: title_block
  typical_position: bottom_right

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - Drawing status is present in each sheet
  - Drawing status is exactly "FOR CONSTRUCTION"
  - Same status is used across all sheets

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Drawing status missing in any sheet
  - Drawing status not equal to "FOR CONSTRUCTION"
  - Inconsistent status across sheets

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: status_detection
    description: Detect drawing status in title block
    keywords:
      - for construction
    pass_evidence: FOR CONSTRUCTION detected
    fail_evidence: FOR CONSTRUCTION not found
    fail_verdict: FAIL

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: status_extraction
    description: Extract drawing status from each sheet
    logic: |-
      - Extract from title block region (bottom-right)
      - Identify status text (e.g., FOR CONSTRUCTION)

  - check: per_sheet_validation
    description: Validate each sheet individually
    logic: |-
      - Iterate through all sheets
      - Ensure status is present in each

  - check: consistency_validation
    description: Ensure uniform status across document
    logic: |-
      - Collect status values from all sheets
      - Ensure all are identical

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - lowercase → uppercase
  - trim extra spaces

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT rely on keyword presence outside title block
  - Ignore watermark text (e.g., DRAFT watermark)
  - Allow minor spacing variations (FOR  CONSTRUCTION)
  - Do NOT fail if OCR noise slightly alters formatting

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Drawing status is typically located in bottom-right title block
  - "FOR CONSTRUCTION" is the required status for FC drawings
  - Other statuses (e.g., DRAFT) must NOT replace this field IN THE TITLE BLOCK
  - DRAFT watermark in the background is a REVIEW OVERLAY and is NOT a conflict with FOR CONSTRUCTION
  - A drawing can simultaneously have a DRAFT watermark AND a FOR CONSTRUCTION title block — this is NORMAL
  - Only validate the formal title block field, not background overlays
  - This is a multi-sheet consistency validation rule
```

---

## R025.yaml

```yaml
id: R025
name: Site details present in header/title block
type: medium

validation_mode: auto

description: |-
  Validate presence and basic correctness of site details in header/title block.
  This rule DOES NOT perform strict RFNSA comparison (handled in R008).

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - Site Code present
  - Site Name present
  - Address present

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Missing site code
  - Missing site name
  - Missing address

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT compare with RFNSA (handled in R008)
  - Do NOT fail due to mismatch (only presence check)

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  This is a presence/visibility rule only.
  All correctness validation is handled in R008.
```

---

## R026.yaml

```yaml
id: R026
name: G1 site details and coordinates must match RFNSA
type: high

validation_mode: hybrid

required_references:
  - RFNSA

scope: G1 only

complexity: structured_comparison + precision_validation

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that G1 site specifications match RFNSA data.

  Fields validated:
    - Coordinates (PRIMARY - strict)
    - Address (structured comparison)
    - Site number (secondary reference)

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  STEP 1: Coordinate Validation (CRITICAL)

  - Latitude & Longitude present in G1

  - Matches RFNSA within tolerance:
      ±0.0001

  ------------------------------------------------

  STEP 2: Address Validation (STRUCTURED)

  Compare components:

  - Lot / Plan → MUST match exactly

  - Street name:
      • Allow normalization (Rd = Road)
      • Must refer to same street

  - Suburb / State / Postcode → MUST match

  - Site descriptor (e.g., reserve name):
      • Preferred but not mandatory

  ------------------------------------------------

  FINAL:

  - Coordinates match
  - Address core components match

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Coordinates missing

  - Coordinate mismatch beyond tolerance

  - Lot/Plan mismatch between G1 and RFNSA

  - Suburb / State / Postcode mismatch

  - Completely different address structure

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - RFNSA data incomplete

  - Coordinates partially extracted

  - Address components not clearly identifiable

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: coordinate_detection
    regex_patterns:
      - '-?\d{1,2}\.\d+'
    pass_evidence: 'Coordinates detected'
    fail_verdict: FAIL

  - check: lot_plan_detection
    regex_patterns:
      - '(lot\s*\d+)'
      - '(plan\s*\d+)'
    pass_evidence: 'Lot/Plan detected'
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: coordinate_comparison
    description: Compare RFNSA vs G1 coordinates
    logic: |-
      Compute delta:
        lat_diff <= 0.0001
        lon_diff <= 0.0001

  - check: address_component_comparison
    description: Structured address validation
    logic: |-
      Extract and compare:
        • Lot / Plan
        • Street name (normalized)
        • Suburb
        • State
        • Postcode

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT rely on full string match for address
  - Do NOT fail for Rd vs Road differences
  - Do NOT fail if site descriptor is missing
  - Do NOT re-validate site ID (handled in R008)

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Coordinates are the primary identity check

  - Address validation is component-based:
      • Lot/Plan = critical
      • Locality = mandatory
      • Street = normalized match

  - This rule ensures:
      Physical site alignment with RFNSA data
```

---

## R027.yaml

```yaml
id: R027
name: Site number consistency across drawings
type: medium

validation_mode: auto

description: |-
  Ensure same site number is used across all sheets.

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - Same site number appears across all sheets

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Multiple different site numbers found across sheets

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT compare with RFNSA (handled in R008)
  - Only check internal consistency

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  This rule checks consistency, not correctness.
```

---

## R028.yaml

```yaml
id: R028
name: Optus site number shown correct
type: high
match_keywords:
- optus site number
validation_mode: auto
required_references:
- RFNSA
description: The Optus Site Number must match the RFNSA system.
pass_criteria: Optus Site Number matches RFNSA.
fail_criteria: Optus Site Number is missing or incorrect.
expected_patterns:
- '[A-Z]\d{4,5}'
deterministic_checks:
- check: regex_search
  patterns:
  - \b[A-Z]\d{4,5}\b
  pass_evidence: 'Optus site number found: {match}'
  fail_evidence: Optus site number not found
```

---

## R029.yaml

```yaml
id: R029
name: Site map location correct & Site location Data table
type: high
match_keywords:
- site map location
validation_mode: google_maps_crosscheck
required_references:
- Google_Maps
- RFNSA
description: Site map location must correspond to RFNSA coordinates.
pass_criteria: Map location corresponds to RFNSA coordinates.
fail_criteria: Map location does not align with RFNSA coordinates.
expected_patterns:
- RFNSA
- GDA94
- ZONE 55
- -?\d+\.\d+
deterministic_checks:
- check: regex_search
  patterns:
  - -?\d+\.\d+
  pass_evidence: 'Coordinates found in drawing: {match}'
  fail_verdict: UNCLEAR
  fail_evidence: Cannot verify map location from PDF text — visual inspection required
```

---

## R030.yaml

```yaml
id: R030
name: Existing structure details must match As-built and RFNSA
type: high

match_keywords:
  - existing structure
  - existing monopole
  - existing tower

validation_mode: hybrid

required_references:
  - As-built
  - RFNSA

input_expectation: |-
  The following reference documents will be provided at runtime:

  - As-built document
  - RFNSA document

  These documents must be used as the source of truth for validation.

  If any required reference is missing or cannot be accessed,
  return:
  → verdict: UNCLEAR

  Do NOT assume or infer values without reference documents.

description: |-
  Validate that the "Existing Structure" section in the FC drawing
  correctly reflects structure details and follows the required format.

  REQUIRED FORMAT:
  EXISTING <OWNER> <HEIGHT> <MODEL> <STRUCTURE TYPE>

  Example:
  "EXISTING INDARA 54.76m HIGH ROAM RT84 SELF SUPPORTING LATTICE TOWER"

  Validation includes:
  - Structure type
  - Height
  - Model
  - Ownership
  - Format compliance

  IMPORTANT:
  - Telstra structures must be updated to AMPLITEL
  - Ownership must align with As-built and RFNSA

scope: |-
  - G1 sheet (SITE SPECIFICATIONS)
  - Any section containing "EXISTING STRUCTURE"

location_hint:
  region: main_content

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - Structure section follows required format:
      EXISTING <OWNER> <HEIGHT> <MODEL> <TYPE>

  - Structure type matches (MONOPOLE / TOWER / ROOF etc.)

  - Height matches reference (if available)

  - Model/details match (if available)

  - Ownership is correct:
      • TELSTRA → must be converted to AMPLITEL
      • OPTUS / INDARA valid if aligned with references

  - Data matches BOTH:
      • As-built document
      • RFNSA document

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Incorrect or incomplete format
  - Missing components (owner / height / type)
  - Structure type mismatch
  - Height mismatch
  - Model mismatch
  - Ownership incorrect:
      • TELSTRA used instead of AMPLITEL
      • Wrong owner vs reference
  - Missing "EXISTING STRUCTURE" section

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: format_detection
    description: Validate required structure sentence format
    regex_patterns:
      - 'existing\s+[a-z]+\s+\d+\.?\d*\s*m.*(monopole|tower|roof)'
    pass_evidence: 'Structure format detected: {match}'
    fail_evidence: Structure format not matching required pattern
    fail_verdict: FAIL

  - check: structure_type_detection
    regex_patterns:
      - monopole
      - tower
      - roof
    pass_evidence: 'Structure type detected: {match}'
    fail_verdict: UNCLEAR

  - check: height_detection
    regex_patterns:
      - '\d+\.?\d*\s*m'
    pass_evidence: 'Structure height detected: {match}'
    fail_verdict: UNCLEAR

  - check: ownership_detection
    keywords:
      - optus
      - telstra
      - amplitel
      - indara
    pass_evidence: 'Ownership detected: {found}'
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: asbuilt_structure_extraction
    description: Extract structure details from As-built
    logic: |-
      Extract:
        • Structure type
        • Ownership
        • Height (if available)
        • Model (if available)

  - check: rfsna_structure_extraction
    description: Extract structure info from RFNSA
    logic: |-
      Extract:
        • Structure type
        • Owner (if available)

  - check: fc_structure_extraction
    description: Extract structure details from FC drawing
    logic: |-
      Locate "EXISTING STRUCTURE" section and extract:
        • Owner
        • Height
        • Model
        • Type

  - check: ownership_normalization
    description: Normalize ownership values
    logic: |-
      Apply mapping:
        TELSTRA → AMPLITEL

  - check: structure_comparison
    description: Compare FC vs references
    logic: |-
      Compare:
        • Type
        • Height (if available)
        • Model (if available)
        • Owner (after normalization)

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - uppercase all text
  - trim spaces
  - telstra → amplitel

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT fail if model not present → mark as PARTIAL
  - Do NOT assume ownership without reference
  - Do NOT skip Telstra → Amplitel normalization
  - Do NOT validate outside "Existing Structure" section
  - Do NOT fail if required references are missing → return UNCLEAR

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Format enforcement is critical for this rule
  - As-built may show legacy ownership (TELSTRA)
  - Expected output should reflect updated ownership (AMPLITEL)
  - This rule validates both:
      • Data correctness
      • Formatting compliance
```

---

## R031.yaml

```yaml
id: R031
name: Structural adequacy of pole & foundation (certificate validation)
type: high

validation_mode: hybrid

required_references:
  - Structural_Certificate

# -----------------------------
# INPUT EXPECTATION
# -----------------------------
input_expectation: |-
  Structural certificate document will be provided.

  Extract:
    - ULS loading (%)
    - Structural adequacy statement
    - Certifier name
    - Certificate date

  If certificate missing:
    → verdict = UNCLEAR

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate structural adequacy of pole/tower and foundation using the structural certificate.

  CORE LOGIC:
    - ULS loading < 100% → SAFE
    - ULS loading ≥ 100% → OVERLOADED → strengthening required

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - ULS loading < 100%

  - Structural adequacy is confirmed
    (explicit OR implicit via loading < 100%)

  - Certifier name present

  - Certificate date present

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - ULS loading ≥ 100% AND no strengthening mentioned

  - Loading not found

  - Certifier missing

  - Certificate date missing

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: loading_detection
    regex_patterns:
      - '\b\d{1,3}%\b'
    pass_evidence: 'Loading found: {match}'
    fail_evidence: 'Loading not found'
    fail_verdict: FAIL

  - check: date_detection
    regex_patterns:
      - '\d{2}[-/][A-Za-z]{3}[-/]\d{2,4}'
      - '\d{2}[/-]\d{2}[/-]\d{4}'
    pass_evidence: 'Date found: {match}'
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: uls_priority_logic
    logic: |-
      If both ULS and SLS present:
        → Use ULS only

  - check: adequacy_logic
    logic: |-
      IF loading < 100%:
        → PASS (even if wording is missing)

      IF loading ≥ 100%:
        → Check strengthening

  - check: strengthening_logic
    logic: |-
      IF loading ≥ 100%:
        Check for:
          • strengthening
          • upgrade
          • modification

  - check: certifier_extraction
    logic: |-
      Extract engineer name from signature block
      (not keyword-based)

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT depend only on "adequacy" keywords
  - Do NOT use SLS if ULS exists
  - Do NOT fail if wording differs but loading is valid
  - If certificate missing → UNCLEAR

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  Loading % is the PRIMARY decision driver.
  Text statements are secondary.
```

---

## R032.yaml

```yaml
id: R032
name: Mount type and structural reference consistency (Panel/RRU/AAU)
type: high

validation_mode: hybrid

required_references:
  - Structural_Drawings

complexity: multi_sheet_inference + cross_reference

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate mount type (Existing vs New) and ensure consistency across:
    - G3 / G3-1 (primary)
    - Elevation drawings (supporting)
    - Structural drawings (validation)

  If NEW mount is identified:
    → Structural reference MUST exist and be traceable

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. G3 / G3-1 → primary source (mount intent)
  2. Structural drawings → confirmation
  3. Elevation → supporting only

# -----------------------------
# DECISION FLOW (CRITICAL)
# -----------------------------
decision_flow: |-
  Step 1: Detect mount type from G3/G3-1

    Identify:
      • "NEW MOUNT"
      • "EXISTING MOUNT"
      • "COLLAR MOUNT"
      • "NEW COLLAR"

    If explicit not found:
      → Infer from notes (e.g., "to be installed")

  Step 2: Map equipment to mount
    → Panel / RRU / AAU association

  Step 3:

    IF mount = NEW:
        → Structural reference MUST exist

    IF mount = EXISTING:
        → Structural reference optional

  Step 4: Cross-check consistency across sheets

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - Mount type identified from G3/G3-1

  - Consistent across available drawings

  - Equipment (Panel/RRU/AAU) logically mapped

  ------------------------------------------------

  CASE 1: NEW mount

  - Structural drawing reference present

  - Reference:
      • Listed in drawing index OR
      • Mentioned in notes OR
      • Traceable to mount type

  ------------------------------------------------

  CASE 2: EXISTING mount

  - Installation consistent with drawings

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Mount type conflict across drawings

  - NEW mount detected BUT:
      • No structural drawing reference
      • OR reference not traceable

  - Structural drawing exists but unrelated to mount

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - Mount type not extractable from G3

  - G3 visibility limited (labels not readable)

  - Structural drawings not provided

  - Equipment-to-mount mapping unclear

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: mount_detection
    keywords:
      - new mount
      - existing mount
      - collar mount
      - new collar
    pass_evidence: 'Mount type detected: {found}'
    fail_verdict: UNCLEAR

  - check: structural_reference_detection
    regex_patterns:
      - 'SP\d{5}-H\d+'
      - 'SX\d+'
    pass_evidence: 'Structural reference detected'
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: mount_inference
    description: Infer mount type from G3
    logic: |-
      If antenna installation includes:
        • "NEW"
        • "INSTALL"
        → classify as NEW mount

  - check: equipment_mapping
    description: Map equipment to mount
    logic: |-
      Associate:
        • Panels
        • RRUs
        • AAUs
      with detected mount

  - check: reference_linking
    description: Validate structural reference relevance
    logic: |-
      Ensure structural drawing corresponds to:
        • Mount type (e.g., collar/headframe)
        • Listed in index or notes

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT assume mount type without evidence
  - Do NOT fail if G3 not readable → return UNCLEAR
  - Do NOT require elevation drawings if absent
  - Do NOT require strict 1:1 mapping if intent is clear

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - G3 is the primary source of truth

  - Structural drawings validate NEW mounts only

  - "Collar mount" typically implies NEW mount

  - This rule validates:
      • Mount intent
      • Structural support linkage
```

---

## R033.yaml

```yaml
id: R033
name: Structural adequacy of mount (certificate validation)
type: high

validation_mode: hybrid

required_references:
  - certificate_document

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate mount structural adequacy using certification evidence.

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - Certificate-like document identified

  - Certifier name present

  - Certificate ID present (not drawing number)

  - Date present

  - Loading < 100%
    OR explicitly adequate

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Loading ≥ 100% AND no strengthening mentioned

  - Certificate clearly invalid:
      • Wrong document type
      • Drawing used as certificate

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - No certificate document found
  - Certificate not extractable
  - Partial data only

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT fail if certificate missing → UNCLEAR
  - Do NOT rely on file names
  - Do NOT treat drawings as certificates

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  This is a conditional validation rule.
  Missing certificate ≠ FAIL.
```

---

## R034.yaml

```yaml
id: R034
name: Antenna/RRU maintenance access validation (EWP vs Ladder/Lad-Saf)
type: high

validation_mode: hybrid

required_references:
  - Site_Photos

optional_references:
  - As-built
  - FC_Drawings

complexity: access_classification + conditional_validation

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate antenna/RRU maintenance access method based on site conditions.

  Access types:
    - EWP (Elevated Work Platform)
    - Ladder / Step Pegs with Lad-Saf

  Photos are the primary source of truth.

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. Site Photos (primary – actual condition)
  2. As-built (secondary – historical)
  3. Drawings (supporting)

# -----------------------------
# DECISION FLOW (CRITICAL)
# -----------------------------
decision_flow: |-
  Step 1: Detect access method from photos

    IF ladder / step pegs / Lad-Saf detected:
        → Ladder-based access

    ELSE:
        → Check drawings / notes for EWP indication

  Step 2:

    IF ladder-based:
        → Certification validation required

    IF no ladder AND EWP indicated:
        → PASS

    IF no ladder AND no EWP indication:
        → UNCLEAR

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  CASE 1: Ladder / Lad-Saf present

  - Ladder-based access confirmed from photos

  - Certification evidence present OR
    no contradiction in provided references

  ------------------------------------------------

  CASE 2: EWP access

  - No ladder / step pegs visible in photos

  - EWP indicated in:
      • Drawings OR
      • Notes OR
      • Site layout (G3)

  ------------------------------------------------

  FINAL:

  - Access method correctly identified and validated

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Ladder / step pegs present BUT:
      • Certification missing
      • OR explicitly invalid/unsafe

  - Clear contradiction:
      • Drawings show ladder
      • Photos show no ladder

  - Incorrect access method defined

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - Photos do not clearly show access area

  - No ladder detected AND no EWP evidence

  - Certification not readable

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: photo_access_detection
    description: Detect physical access elements
    logic: |-
      Identify:
        • ladder
        • step pegs
        • Lad-Saf rail

  - check: ewp_detection
    description: Detect EWP indication
    logic: |-
      Look for:
        • "EWP"
        • "Elevated Work Platform"
        • EWP setup location in G3

  - check: certification_validation
    description: Validate ladder certification
    logic: |-
      If ladder present:
        check:
          • certification mention
          • inspection validity (if available)

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT assume EWP without supporting evidence
  - Do NOT require certification if ladder not present
  - Do NOT rely only on As-built if photos contradict
  - Do NOT fail if photos missing → return UNCLEAR

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Photos override all other references

  - Default industry trend:
      No ladder → likely EWP (but must be confirmed)

  - Ladder access requires certification validation

  - This rule ensures:
      Safe and compliant maintenance access
```

---

## R035.yaml

```yaml
id: R035
name: Equipment shelter consistency (As-built vs FC vs Photos)
type: high

validation_mode: hybrid

required_references:
  - As-built
  - Site_Photos

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate shelter configuration using As-built as baseline.

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. As-built (source of truth)
  2. FC drawing
  3. Photos (support only)

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - FC matches As-built configuration

  - No major change detected

  OR

  - Change exists AND certification provided

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Major configuration mismatch:
      • Cabinet count mismatch
      • Layout mismatch

  - New shelter introduced WITHOUT certification

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - As-built missing
  - Photos missing AND change unclear
  - Extraction incomplete

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT fail based only on photos
  - Allow minor visual differences
  - Do NOT rely on layer styling

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  Photos are secondary validation only.
```

---

## R036.yaml

```yaml
id: R036
name: Transmission type validation (Radio vs Fibre)
type: high

validation_mode: hybrid

optional_references:
  - As-built
  - Site_Photos

complexity: inference_based + cross_validation

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate transmission type (Radio or Fibre) using:
    - Dish antenna presence (primary signal)
    - As-built drawings (authoritative if available)
    - Site photos (supporting)

  Rule:
    Dish present → Radio
    No dish → Fibre

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. Dish detection (Photos / Drawings)
  2. As-built (if available)
  3. FC drawings (support)

# -----------------------------
# DECISION FLOW
# -----------------------------
decision_flow: |-
  Step 1: Detect dish antenna

    IF dish present:
        → Transmission = Radio

    ELSE:
        → Transmission = Fibre

  Step 2: Cross-check with As-built (if available)

    IF contradiction:
        → FAIL

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  CASE 1: Radio

  - Dish antenna detected in:
      • Photos OR
      • Drawings OR
      • As-built

  ------------------------------------------------

  CASE 2: Fibre

  - No dish antenna detected

  ------------------------------------------------

  FINAL:

  - Transmission type correctly inferred and consistent

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Dish present BUT classified as fibre

  - As-built indicates radio BUT no dish detected

  - Contradictory evidence across sources

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - No photos AND no drawings AND As-built not readable

  - Unable to detect dish presence/absence

# -----------------------------
# DECISION SCHEMA (FOR LLM TRACE)
# -----------------------------
decision_schema:
  - step: check_dish_presence
    description: Are there any dish, microwave, or radio antennas explicitly drawn or called out in the FC drawings or As-Built?
  - step: infer_transmission_type
    description: If dish is present → Radio. If no dish is present → Fibre.
  - step: check_asbuilt_contradiction
    description: Does the As-built (if available) explicitly contradict the inference?
  - step: reconcile_evidence
    description: Generate final structured evidence linking the inference directly to the verdict.

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT require explicit "fibre" mention
  - Do NOT require T1 sheet extraction
  - Do NOT assume radio without dish
  - Do NOT fail if As-built missing → rely on inference

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Telecom standard:
      Dish → Radio
      No dish → Fibre

  - Fibre is the default assumption

  - This is an inference-based rule
```

---

## R037.yaml

```yaml
id: R037
name: |-
  Update the construction site access - Previous AB info is mostly outdated - please check INDARA/Amplitel/BAI document for updated information.
type: medium
match_keywords:
- site access
- construction access
- access road
- Indara
- Amplitel
- BAI
- site access details
validation_mode: llm_only
required_references:
- As-built
description: |-
  Check the transmission type, either fibre or dish. The site is connected to the network via radio or fibre. Verify this through the As-Built drawings and site photos. If any active Optus dish is found, note that the site is connected via radio; otherwise, it is connected via fibre.
pass_criteria: |-
  Validate transmission type (Dish(Radio) / Fiber), Check presence of dish antenna in site photos, Cross-check transmission details in As-built drawings
fail_criteria: |-
  Verify that the transmission type is correctly identified as either Dish (Radio) or Fibre by checking both site photos and As-Built drawings. A failure occurs if there is a mismatch or insufficient evidence—such as the absence of a visible dish antenna in site photos while the transmission is marked as radio, or the presence of an active Optus dish that is not reflected in the transmission type. Additionally, if the As-Built drawings do not clearly specify the transmission method, or contradict the site photos, the validation should be marked as failed due to inconsistent or missing supporting documentation..
expected_patterns:
- access
- road
- entry
- site access
```

---

## R038.yaml

```yaml
id: R038
name: Site hazards must reflect site conditions
type: high

validation_mode: hybrid

required_references:
  - As-built
  - SDV_Photos

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that site hazards in FC drawings reflect actual site conditions.

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. SDV Photos (if available)
  2. FC Drawing (G1 hazards section)
  3. As-built (baseline only)

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - Site hazards section exists in G1

  - Hazards are reasonable and relevant

  - IF SDV photos available:
      • No major hazard is completely missing

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Critical hazard visible in photos BUT completely missing in drawings

  - Hazards section missing entirely

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - SDV photos not provided

  - Hazards cannot be reliably extracted from photos

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT fail for generic wording alone
  - Do NOT expect perfect 1:1 hazard mapping
  - Do NOT assume hazards from unclear images
  - Do NOT fail if photos missing → UNCLEAR

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  Hazards are often semi-generic.
  Only fail if a clear, critical hazard is omitted.
```

---

## R039.yaml

```yaml
id: R039
name: Site signage must comply with OSD-171, Form A/B, and SDV photos
type: high

match_keywords:
  - site signage
  - MERCS
  - OSD-171
  - signage
  - hazard sign

validation_mode: hybrid

required_references:
  - Form_A
  - Form_B
  - SDV_Photos
  - OSD_171

# -----------------------------
# DECISION PRIORITY (CRITICAL FIX)
# -----------------------------
decision_priority: |-
  1. Form A / Form B → Defines REQUIRED signage
  2. OSD-171 → Defines STANDARD
  3. FC Drawings → Implementation
  4. SDV Photos → Supporting validation only

# -----------------------------
# INPUT EXPECTATION
# -----------------------------
input_expectation: |-
  The system will be provided with:

  1. FC drawings (with signage callouts)
  2. Form A / Form B (signage requirements)
  3. SDV site photos
  4. OSD-171 standard drawings

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that required site signage is correctly specified,
  compliant with OSD-171 standards, and aligned with Form A/B.

  SDV photos are used only to support validation, not as primary failure source.

# -----------------------------
# SCOPE
# -----------------------------
scope: |-
  - G1 sheet (Site Signage section)
  - Plan / Elevation drawings

location_hint:
  region: signage_section

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - Correct OSD standard applied:
      • Ground → OSD-171-1
      • Rooftop → OSD-171-2
      • General → OSD-171-3

  - Required signage from Form A/B is present in drawings

  - Mandatory signage present:
      • KEEP OUT
      • MERCS
      • Hazard signage (HV etc.)

  - MERCS signage contains RFNSA number (if required)

# -----------------------------
# FAIL CRITERIA (CONTROLLED)
# -----------------------------
fail_criteria: |-
  - Wrong OSD standard selected

  - Mandatory signage completely missing from drawings

  - Clear mismatch between Form A/B and drawings

  - MERCS signage missing RFNSA number (when explicitly required)

# -----------------------------
# PHOTO VALIDATION (SAFE MODE)
# -----------------------------
photo_logic: |-
  Use SDV photos ONLY to:
    - Support detection of missing signage
    - Identify damaged/faded signage

  DO NOT:
    - Fail based only on photos
    - Override Form A/B or drawing data

# -----------------------------
# UNCLEAR CONDITIONS (IMPORTANT)
# -----------------------------
unclear_conditions: |-
  - Form A/B not provided

  - Site type (ground vs rooftop) cannot be determined

  - Signage cannot be reliably extracted from drawings

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: signage_keyword_detection
    keywords:
      - mercs
      - keep out
      - hazardous voltage
      - site enquiry
    pass_evidence: 'Signage keywords detected: {found}'
    fail_verdict: UNCLEAR

  - check: rfnsa_number_detection
    regex_patterns:
      - '\b\d{7}\b'
    pass_evidence: 'RFNSA number found: {match}'
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: site_type_detection
    description: Identify site type

  - check: form_signage_extraction
    description: Extract required signage from Form A/B

  - check: drawing_signage_extraction
    description: Extract signage from drawings

  - check: signage_comparison
    description: Compare Form A/B vs drawings

  - check: rfnsa_validation
    description: Validate RFNSA number presence (if applicable)

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - uppercase all text
  - trim spaces

# -----------------------------
# NEGATIVE CONSTRAINTS (FIXED)
# -----------------------------
negative_constraints:
  - Do NOT fail based only on SDV photos
  - Do NOT expect perfect placement accuracy
  - Do NOT assume signage absence from unclear images
  - Do NOT fail if Form A/B missing → return UNCLEAR
  - Do NOT over-penalize minor placement differences

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  Validation hierarchy:
    Form A/B → requirement
    OSD → standard
    Drawing → implementation
    Photos → supporting evidence only

  This is a compliance validation rule, not a visual perfection check.
```

---

## R040.yaml

```yaml
id: R040
name: Outdated or damaged signage must be identified and replaced
type: high

match_keywords:
  - signage
  - replace signage
  - faded
  - damaged
  - worn
  - MERCS
  - keep out
  - hazardous voltage

validation_mode: hybrid

required_references:
  - SDV_Photos
  - Form_A
  - Form_B

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. SDV Photos → detect signage condition (if clearly visible)
  2. FC Drawings → corrective action
  3. Form A/B → supporting reference only

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that any clearly visible damaged, faded, missing, or incorrectly placed signage
  from SDV photos is addressed with corrective actions in FC drawings.

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - If signage condition issues are clearly visible in SDV photos:
      • Corresponding corrective action exists in drawings
        (e.g., "Replace existing signage", "Install new signage")

  - If no clear issues are visible:
      • Rule passes

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Clearly visible damaged/faded/missing signage in SDV photos
    AND no corrective action mentioned in drawings

  - Critical signage missing in both photos and drawings

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - SDV photos not provided

  - Signage condition cannot be reliably determined from photos

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: replacement_keywords
    keywords:
      - replace existing
      - install new
      - new signage
    pass_evidence: 'Corrective action found: {found}'
    fail_verdict: UNCLEAR

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT fail if photo evidence is unclear
  - Do NOT require perfect 1:1 mapping
  - Do NOT assume damage without clear evidence

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  This is a CONDITION → ACTION validation rule.

  Only fail when:
    • Issue is clearly visible
    • AND not addressed in drawings
```

---

## R041.yaml

```yaml
id: R041
name: Electrical installation and site earthing must match references
type: high

validation_mode: hybrid

preconditions:
  - electrical_context_available

match_keywords:
  - electrical installation
  - site earthing
  - power supply
  - earthing

required_references:
  - RLM
  - As-built
  - Photos

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. Electrical sheets (E1/E2) → determine applicability
  2. RLM → primary electrical reference
  3. G1 → summarized design
  4. As-built → baseline validation
  5. Photos → supporting only

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate electrical installation and earthing consistency
  when electrical information is present in the drawing set.

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  CASE 1: ELECTRICAL SECTION PRESENT (E1/E2 exists)

  - Electrical section present in G1

  - Power supply defined:
      • Phase (single / 3-phase)
      • Current rating

  - Electrical details are logically consistent between:
      • G1
      • RLM
      • As-built (if available)

  - Earthing system is present

  ------------------------------------------------

  CASE 2: NO ELECTRICAL SECTION (E1/E2 absent)

  - No contradiction in G1 regarding electrical scope

  - No incomplete or partial electrical upgrade statements

  → Treat as NO ELECTRICAL UPGRADE (PASS)

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Electrical section present but:

      • Electrical data missing in G1

      • Clear contradiction between G1 and RLM

      • Earthing system completely missing

  - Partial electrical upgrade mentioned
    but not properly defined

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - Electrical section presence unclear

  - RLM not available AND electrical data ambiguous

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: sheet_detection
    regex_patterns:
      - '\bE1\b'
      - '\bE2\b'
    pass_evidence: 'Electrical sheets detected: {match}'
    fail_verdict: UNCLEAR

  - check: power_detection
    regex_patterns:
      - '\b\d{1,3}A\b'
      - '3\s*phase'
      - 'single\s*phase'
    pass_evidence: 'Power details detected: {match}'
    fail_verdict: UNCLEAR

  - check: earthing_detection
    keywords:
      - earthing
      - earth
      - grounding
    pass_evidence: 'Earthing reference found'
    fail_verdict: UNCLEAR

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT fail if electrical section is absent
  - Do NOT rely only on photos
  - Do NOT expect exact numeric match
  - Do NOT assume upgrade from partial keywords

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Presence of E1/E2 sheets indicates electrical scope exists.

  - Absence of electrical sheets implies no electrical upgrade.

  - RLM is the source of truth for electrical configuration.
```

---

## R042.yaml

```yaml
id: R042
name: Electrical upgrade validation and E-sheet inclusion
type: high

validation_mode: hybrid

complexity: conditional_validation + document_inference

required_references:
  - FC_Drawings

optional_references:
  - RLM

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate whether electrical upgrade is required and ensure
  correct inclusion or exclusion of E-sheets (E1/E2).

  Decision is based on RLM first, then validated using drawing index.

# -----------------------------
# DECISION PRIORITY (FIXED)
# -----------------------------
decision_priority: |-
  1. RLM → determines upgrade requirement (source of truth)
  2. Drawing index → validates sheet presence
  3. G3 / F1 → notes validation (supporting)

# -----------------------------
# DECISION FLOW (CRITICAL)
# -----------------------------
decision_flow: |-
  Step 1: Determine upgrade requirement from RLM

    IF RLM contains:
      • "upgrade required"
      • new supply / new cable / augmentation

        → upgrade_required = TRUE

    IF RLM contains:
      • "existing supply sufficient"
      • "no upgrade required"

        → upgrade_required = FALSE

    ELSE:
        → UNCLEAR

  Step 2: Validate sheet inclusion

    IF upgrade_required = TRUE:
        → E1 and E2 MUST be present

    IF upgrade_required = FALSE:
        → E1 and E2 MUST NOT be present

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  CASE 1: Upgrade Required

  - RLM indicates upgrade required

  - E1 and E2 sheets present in drawing index

  ------------------------------------------------

  CASE 2: No Upgrade Required

  - RLM confirms existing supply is sufficient

  - E1 and E2 sheets NOT present

  - Standard electrical notes present (G3 / F1)

  ------------------------------------------------

  FINAL:

  - Electrical scope correctly represented

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Upgrade required but E1/E2 missing

  - No upgrade required BUT:
      • E1/E2 present

  - RLM contradicts drawing index

  - Partial inclusion (E1 without E2 or vice versa)

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - RLM not available

  - Upgrade intent not extractable from RLM

  - Drawing index not readable

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: sheet_detection
    regex_patterns:
      - '\bE1\b'
      - '\bE2\b'
      - '\bE3\b'
    pass_evidence: 'E-sheets detected: {match}'
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: upgrade_detection
    description: Detect electrical upgrade requirement
    logic: |-
      Look for phrases in RLM:

      Positive (upgrade):
        • upgrade required
        • new supply
        • augmentation

      Negative (no upgrade):
        • existing supply sufficient
        • no upgrade required

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT infer upgrade from E-sheet presence
  - Do NOT treat "NEW" keyword alone as upgrade
  - Do NOT require E1/E2 if upgrade not required
  - Do NOT rely only on drawing index for decision

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - RLM is the primary decision source

  - E1/E2 presence is validation, not decision

  - Most telecom projects are upgrades without electrical changes

  - Key distinction:
      Electrical work ≠ Electrical upgrade
```

---

## R043.yaml

```yaml
id: R043
name: WHS design risk assessment note included for CPS only
type: high

validation_mode: hybrid

required_references:
  - SDV_Photos

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. Project type detection
  2. G1 → WHS note presence
  3. SDV Photos → supporting only

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate WHS risk assessment notes in G1 for CPS projects.

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - If CPS project:
      • WHS note present
      • Notes are reasonable

  - If ServiceStream:
      → NOT APPLICABLE

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - CPS project AND WHS note missing

  - Critical risk clearly visible in photos
    AND not mentioned in notes

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - Project type unclear

  - Photos not available or unclear

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT require full risk mapping
  - Do NOT fail based on minor omissions
  - Do NOT rely only on photos

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  Focus on presence + reasonable coverage, not perfection.
```

---

## R044.yaml

```yaml
id: R044
name: Corrosion protection validation (ServiceStream only)
type: high

validation_mode: hybrid

complexity: conditional_vendor + category_based_validation

required_references:
  - Structural_Certificate

optional_references:
  - FC_Drawings

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate corrosion protection notes based on corrosivity category.

  This rule applies ONLY to ServiceStream projects.

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. Vendor detection (applicability gate)
  2. Structural certificate → corrosivity category
  3. G1 sheet → corrosion note validation

# -----------------------------
# DECISION FLOW (CRITICAL)
# -----------------------------
decision_flow: |-
  Step 1: Detect vendor

    IF vendor ≠ ServiceStream:
        → NOT APPLICABLE (N/A)

    IF vendor = ServiceStream:
        → proceed

  Step 2: Extract corrosivity category (C1–CX) from structural certificate

  Step 3:

    IF category = C1–C4:
        → corrosion protection may be N/A

    IF category = C5–CX:
        → protection MUST be defined

  Step 4: Validate G1

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  CASE 1: ServiceStream + C1–C4

  - Category identified

  - Corrosion protection may be:
      • Defined OR
      • Marked as N/A

  ------------------------------------------------

  CASE 2: ServiceStream + C5–CX

  - Category identified

  - Corrosion protection note present in G1

  - Protection method defined (e.g., coating, stainless steel)

  ------------------------------------------------

  CASE 3: Non-ServiceStream

  - Rule not applicable → PASS / N/A

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - ServiceStream project AND:

      • Corrosion note missing in G1

  - Category = C5–CX AND:

      • Protection method not defined

  - Mismatch between structural certificate and G1

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - Vendor cannot be determined

  - Structural certificate not available

  - Corrosivity category not extractable

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: corrosion_keywords
    keywords:
      - corrosion
      - C1
      - C2
      - C3
      - C4
      - C5
      - CX
    pass_evidence: 'Corrosion reference found: {found}'
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: vendor_detection
    description: Identify vendor from title block or certificate

  - check: category_extraction
    description: Extract corrosivity category from certificate

  - check: g1_note_validation
    description: Validate corrosion note presence
    logic: |-
      Look for:
        • corrosion protection note
        • material specification
        • coating / galvanization reference

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT validate for non-ServiceStream sites
  - Do NOT assume category without certificate
  - Do NOT fail if certificate missing → UNCLEAR
  - Do NOT require protection definition for C1–C4

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - This is a vendor-specific rule (ServiceStream only)

  - Corrosivity categories:
      • C1–C4 → low/moderate → protection may be N/A
      • C5–CX → high → protection mandatory

  - Structural certificate is the source of truth
```

---

## R045.yaml

```yaml
id: R045
name: North located and pointed in upper direction
type: medium
match_keywords:
- north
- north symbol
- north block
- MGA north
validation_mode: cad_only
description: |-
  Verify that the north symbol (north block) is present and oriented correctly in the drawing. The north arrow must always point straight upwards without any tilt or directional deviation.
pass_criteria: North symbol is present and correctly aligned pointing straight upwards.
fail_criteria: |-
  North symbol is missing, tilted, rotated, or not pointing in the upward direction.
expected_patterns:
- N
- north
```

---

## R046.yaml

```yaml
id: R046
name: Scale must be standard and appropriate based on site coverage (G2)
type: medium

match_keywords:
  - scale
  - 1:500
  - 1:1000
  - 1:2000
  - 1:2500

validation_mode: hybrid

# -----------------------------
# INPUT EXPECTATION
# -----------------------------
input_expectation: |-
  The system will be provided with:

  1. G2 sheet (Overall Site Plan)
  2. Drawing scale annotation

  The system must:
  - Detect scale used in drawing
  - Evaluate site coverage (roads, site extent)
  - Validate whether chosen scale is appropriate

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that the drawing scale is both:
  1. A standard scale, and
  2. Appropriate for the site extent

  Preferred scales:
    • 1:500
    • 1:1000

  Larger scale (1:2000) is allowed ONLY when required to cover
  a wider area.

# -----------------------------
# SCOPE
# -----------------------------
scope: |-
  - G2 sheet (Overall Site Plan)

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  STEP 1: Scale Presence

  - Scale is clearly mentioned in drawing

  ------------------------------------------------

  STEP 2: Standard Scale Validation

  Acceptable scales:
    • 1:500
    • 1:1000
    • 1:2000

  ------------------------------------------------

  STEP 3: Coverage Validation

  - Drawing should cover:
      • At least TWO roads (primary reference)
      • Site location
      • Access route

  ------------------------------------------------

  STEP 4: Scale Selection Logic

  CASE A: Compact site

    - If 1:500 or 1:1000 can cover:
        • ≥2 roads
        • Site + access

      → PASS

  CASE B: Large / spread-out site

    - If 1:500 / 1:1000 insufficient:
        → 1:2000 allowed

  CASE C: Large scale used unnecessarily

    - If 1:2000 used but:
        • Only small area shown
        → FAIL

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Scale missing

  - Non-standard scale used:
      • e.g., 1:750, 1:1500, 1:2500

  - Coverage insufficient:
      • Less than 2 roads visible

  - Incorrect scale usage:
      • 1:2000 used when 1:1000 sufficient

  - Site or access route not clearly visible

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: scale_detection
    regex_patterns:
      - '1:\s*500'
      - '1:\s*1000'
      - '1:\s*2000'
      - '1:\s*\d+'
    pass_evidence: 'Scale detected: {match}'
    fail_verdict: FAIL
    fail_evidence: 'Scale not found'

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: road_detection
    description: Detect number of roads
    logic: |-
      Identify named roads / street labels in drawing

      If ≥2 roads present → PASS
      Else → FAIL

  - check: coverage_evaluation
    description: Evaluate site coverage vs scale
    logic: |-
      Determine if selected scale appropriately fits:

        • Site
        • Access path
        • Surrounding roads

  - check: scale_appropriateness
    description: Validate scale efficiency
    logic: |-
      If large scale (1:2000):
        Ensure justified by wide coverage

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - remove spaces in scale
  - standardize format (1:1000)

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT validate non-G2 sheets
  - Do NOT pass based on scale alone (coverage required)
  - Do NOT assume roads without labels

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Preferred working scales:
      • 1:500
      • 1:1000

  - 1:2000 is acceptable only for large sites

  - Key requirement:
      Scale must ensure visibility of at least two roads

  - Common issue:
      Using 1:2000 unnecessarily → reduces clarity

  - This rule ensures:
      Readability + contextual completeness of site plan
```

---

## R047.yaml

```yaml
id: R047
name: Street name shown is correct?
type: medium
match_keywords:
- street name
- road name
- access route
- EWP location
- site access road
validation_mode: google_maps_crosscheck
description: |-
  Verify that the street/road names shown in the drawing are correct by cross-referencing site coordinates with external sources such as Google Maps or RFNSA data. Ensure that all access roads and surrounding street labels match real-world naming.
pass_criteria: |-
  Street names in the drawing match accurately with Google Maps or RFNSA data based on site coordinates.
fail_criteria: |-
  Street names are incorrect, missing, or do not match Google Maps/RFNSA reference data.
expected_patterns: []
```

---

## R048.yaml

```yaml
id: R048
name: All existing electrical/fiber O/H or U/G services shown
type: high
match_keywords:
- overhead power
- underground cable
- fiber
- UG line
- OH line
- electrical service
validation_mode: google_maps_crosscheck
description: |-
  Verify that all existing electrical and fiber services (overhead and underground) are correctly represented. Overhead lines should be validated using Google Maps based on site coordinates, while underground services must be validated against As-Built drawings.
pass_criteria: |-
  All overhead and underground electrical/fiber services are correctly shown and match Google Maps (for O/H) and As-Built drawings (for U/G).
fail_criteria: |-
  Electrical/fiber services are missing, incorrectly shown, or inconsistent with Google Maps or As-Built references.
expected_patterns:
- power
- fiber
- cable
- UG
- OH
```

---

## R049.yaml

```yaml
id: R049
name: |-
  Surrounding buildings/parks/road/other carriers/ True north/trees and vegetation etc shown
type: medium
match_keywords:
- buildings
- parks
- roads
- trees
- vegetation
- site surroundings
validation_mode: google_maps_crosscheck
description: |-
  Verify that surrounding features such as buildings, parks, roads, vegetation, and nearby infrastructure are accurately shown in the G2 drawing by comparing with Google Maps and As-Built drawings.
pass_criteria: |-
  All major surrounding features are correctly represented and consistent with Google Maps and As-Built references.
fail_criteria: |-
  Surrounding features are missing, incomplete, or inconsistent with real-world or As-Built data.
expected_patterns: []
```

---

## R050.yaml

```yaml
id: R050
name: Surrounding features must match real-world conditions and references
type: medium

match_keywords:
  - buildings
  - parks
  - roads
  - trees
  - vegetation
  - site surroundings

validation_mode: hybrid

complexity: visual

required_references:
  - Google_Maps

optional_references:
  - As-built
  - G2_Drawing

# -----------------------------
# INPUT EXPECTATION
# -----------------------------
input_expectation: |-
  The system will be provided with:

  1. FC drawing:
     - G2 sheet (if available)

  2. Reference documents:
     - Google Maps (primary)
     - As-built drawings (optional)

  The system must:
  - Extract surrounding features from G2 drawing (if present)
  - Compare with As-built ONLY if G2 is present
  - Validate against Google Maps for real-world alignment

  If Google Maps is unavailable:
  → verdict: UNCLEAR

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that surrounding site features such as buildings, roads,
  vegetation, parks, and nearby infrastructure are correctly represented.

  Validation must ensure:
  - Drawing reflects real-world surroundings
  - Spatial alignment and orientation are correct

  Conditional logic applies based on G2 availability.

# -----------------------------
# SCOPE
# -----------------------------
scope: |-
  FC:
    - G2 sheet (site layout)

  REF:
    - Google Maps
    - As-built (if G2 present)

location_hint:
  region: site_layout

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - Major surrounding features are present in G2 (if available):
      • Roads
      • Buildings
      • Vegetation

  - Features align with Google Maps:
      • Correct placement
      • Correct orientation

  - If G2 is present:
      • Features are consistent with As-built drawings

  - True north direction is correctly indicated

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Key surrounding features missing in G2 (if available)

  - Mismatch between:
      • Drawing and Google Maps

  - If G2 is present:
      • Mismatch between drawing and As-built

  - Incorrect spatial placement or orientation

  - True north missing or incorrect

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: surroundings_keyword_detection
    keywords:
      - road
      - building
      - tree
      - vegetation
      - north
    pass_evidence: 'Surrounding elements detected: {found}'
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: g2_feature_extraction
    description: Extract surrounding features from G2
    logic: |-
      Identify:
        • Roads
        • Buildings
        • Vegetation
        • North direction

  - check: map_feature_detection
    description: Detect features from Google Maps
    logic: |-
      Identify:
        • Roads
        • Buildings
        • Vegetation / open areas

  - check: conditional_validation_logic
    description: Apply validation based on G2 availability
    logic: |-
      IF G2 sheet is present:
        • Compare features with As-built
        • Cross-check with Google Maps

      IF G2 sheet is NOT present:
        • Skip As-built comparison
        • Validate using Google Maps only

      IF Google Maps is unavailable:
        → verdict: UNCLEAR

  - check: spatial_alignment
    description: Validate placement and orientation
    logic: |-
      Ensure surrounding features align spatially
      between drawing and Google Maps

# -----------------------------
# CONFIDENCE
# -----------------------------
confidence_logic: |-
  HIGH → G2 + As-built + Maps all align
  MEDIUM → G2 + Maps align
  LOW → Maps only or partial feature visibility

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - lowercase text
  - trim spaces

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT assume features if not visible
  - Do NOT fail due to missing As-built if G2 is absent
  - Do NOT enforce As-built comparison unless G2 is present
  - Do NOT rely only on keywords → require spatial validation
  - Do NOT fail if Google Maps unavailable → return UNCLEAR

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Google Maps is the primary real-world reference

  - As-built is used ONLY when G2 sheet is present

  - G2 drawing represents planned layout of surroundings

  - Validation hierarchy:
      G2 → As-built (if G2 present) → Google Maps

  - This rule ensures:
      Drawing surroundings = Real-world surroundings
```

---

## R051.yaml

```yaml
id: R051
name: Access routes and EWP/Crane location must be clearly shown with required safety notes
type: high

match_keywords:
  - ewp
  - crane
  - access route
  - access road
  - working area

validation_mode: hybrid

complexity: cross_document

required_references:
  - SDV_Photos

optional_references:
  - As-built

# -----------------------------
# INPUT EXPECTATION
# -----------------------------
input_expectation: |-
  The system will be provided with:

  1. FC drawings:
     - G2 / site layout drawings

  2. Reference documents:
     - SDV Photos (mandatory)
     - As-built drawings (optional)

  The system must:
  - Verify access route is clearly shown
  - Verify EWP/Crane location is explicitly marked
  - Validate access using SDV photos (primary) and As-built (if available)
  - Check if required safety notes are included based on EWP placement

  If SDV photos are missing:
  → verdict: UNCLEAR

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that access routes and EWP/Crane locations are clearly
  shown in drawings and aligned with actual site conditions.

  Additionally, ensure required safety notes are included based on
  EWP positioning.

  Mandatory:
  - EWP location must be shown for ALL sites

# -----------------------------
# SCOPE
# -----------------------------
scope: |-
  FC:
    - G2 sheet / site layout

  REF:
    - SDV Photos
    - As-built (optional)

location_hint:
  region: site_layout

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - Access route clearly shown in drawings

  - EWP/Crane location is explicitly marked

  - Access route aligns with SDV photos:
      • Road/path visible
      • Entry feasible

  - If As-built available:
      • Access aligns with As-built

  - Conditional safety notes correctly applied:

      CASE 1: EWP on road / roadside
        → "Traffic and Pedestrian Management required" note present

      CASE 2: EWP near overhead power lines
        → "Tiger tails required" note present

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Access route not shown or unclear

  - EWP/Crane location missing (mandatory failure)

  - Access route does not match SDV photos

  - If As-built available:
      • Mismatch with drawing

  - Missing required safety notes:

      • EWP on road but no traffic management note

      • EWP near power lines but no tiger tails note

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: ewp_detection
    keywords:
      - ewp
      - crane
      - working area
    pass_evidence: 'EWP/Crane location detected'
    fail_evidence: 'EWP/Crane location not found'
    fail_verdict: FAIL

  - check: access_detection
    keywords:
      - access
      - road
      - path
      - entry
    pass_evidence: 'Access route detected: {found}'
    fail_verdict: UNCLEAR

  - check: safety_note_detection
    keywords:
      - traffic management
      - pedestrian management
      - tiger tails
    pass_evidence: 'Safety notes detected: {found}'
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: access_extraction
    description: Extract access route from drawing
    logic: |-
      Identify:
        • Access road/path
        • Entry point

  - check: ewp_location_extraction
    description: Extract EWP/Crane placement
    logic: |-
      Identify:
        • EWP position
        • Working radius / area (if shown)

  - check: photo_validation
    description: Validate access using SDV photos
    logic: |-
      Identify:
        • Road presence
        • Accessibility to site

  - check: asbuilt_comparison
    description: Compare with As-built (if available)
    logic: |-
      Validate access route consistency

  - check: safety_condition_evaluation
    description: Evaluate safety requirements
    logic: |-
      IF EWP located on road or roadside:
        → Traffic/Pedestrian management note required

      IF EWP near overhead power lines:
        → Tiger tails note required

# -----------------------------
# CONFIDENCE
# -----------------------------
confidence_logic: |-
  HIGH → Access + EWP + safety notes all correct
  MEDIUM → Access + EWP correct, minor note ambiguity
  LOW → Partial visibility or unclear EWP placement

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - lowercase text
  - trim spaces

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT pass if EWP location is missing (mandatory)
  - Do NOT assume EWP placement without explicit marking
  - Do NOT enforce As-built comparison if not available
  - Do NOT fail if safety condition not applicable
  - Do NOT rely only on keywords → require contextual validation

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - EWP location is mandatory for all telecom sites

  - SDV photos are primary validation for access

  - Safety notes are condition-based (not always required)

  - This rule ensures:
      Access feasibility + Safe execution planning
```

---

## R052.yaml

```yaml
id: R052
name: Standard notes and legend details must be complete and conditionally correct
type: high

match_keywords:
  - standard notes
  - legend
  - line type
  - fence
  - power line
  - underground
  - overhead

validation_mode: hybrid

complexity: cross_document

required_references:
  - FC_Drawings

optional_references:
  - SDV_Photos

# -----------------------------
# INPUT EXPECTATION
# -----------------------------
input_expectation: |-
  The system will be provided with:

  1. FC drawings:
     - G1 sheet (standard notes section)
     - G2/G3 sheets (legend section)

  2. Reference:
     - SDV Photos (optional, for contextual validation)

  The system must:
  - Validate presence of standard notes in G1
  - Validate legend completeness and correctness
  - Ensure conditional safety notes are included where applicable

  If G1 or legend section is missing:
  → verdict: UNCLEAR

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that standard notes and legend details are correctly included
  and aligned with drawing content.

  This includes:
  - Presence of standard notes
  - Inclusion of condition-based safety notes
  - Correct legend representation for line types used in drawing

# -----------------------------
# SCOPE
# -----------------------------
scope: |-
  FC:
    - G1 sheet (standard notes)
    - G2/G3 sheets (legend)

location_hint:
  region: notes_and_legend_section

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - Standard notes are present in G1 sheet

  - Required conditional notes included:

      CASE 1: EWP on road
        → Traffic & pedestrian management note present

      CASE 2: Work near overhead power lines
        → Tiger tails note present

  - Legend is present and includes correct line types used in drawing:
      • Fence
      • Overhead (O/H) power line
      • Underground (U/G) power line

  - Legend line types match actual drawing usage

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Standard notes missing in G1

  - Missing required conditional notes:

      • EWP on road but no traffic note
      • Near power lines but no tiger tails note

  - Legend missing or incomplete

  - Legend does not include required line types

  - Legend does not match drawing elements

# -----------------------------
# DECISION SCHEMA (FOR LLM TRACE)
# -----------------------------
decision_schema:
  - step: check_standard_notes_presence
    description: Are standard notes present on G1?
  - step: check_conditional_notes
    description: Are there conditions (EWP, power lines) that require specific safety notes? If so, are they present?
  - step: check_legend_presence
    description: Is the legend section present on G2/G3?
  - step: check_legend_alignment
    description: Do the line types and symbols in the legend match what is actually drawn (fence, power line, etc.)?
  - step: reconcile_evidence
    description: Combine notes and legend findings into a structured evidence output.

# -----------------------------
# CONFIDENCE
# -----------------------------
confidence_logic: |-
  HIGH → Notes + legend + conditions all satisfied
  MEDIUM → Notes present, minor legend mismatch
  LOW → Partial notes or incomplete legend

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - lowercase text
  - trim spaces

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT pass if standard notes are missing
  - Do NOT assume conditional notes unless condition is detected
  - Do NOT rely only on keyword detection → require context
  - Do NOT fail if condition not applicable
  - Do NOT assume legend correctness without matching drawing

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Standard notes are mandatory for all drawings

  - Conditional notes depend on:
      • EWP placement
      • Presence of power lines

  - Legend must reflect actual drawing elements

  - This rule ensures:
      Drawing clarity + execution safety + interpretability
```

---

## R053.yaml

```yaml
id: R053
name: North direction and site orientation must be correct and consistent
type: high

match_keywords:
  - north
  - north arrow
  - orientation
  - latitude
  - longitude
  - site layout

validation_mode: hybrid

complexity: cross_document + optional_external

required_references:
  - FC_Drawings

optional_references:
  - As-built
  - Google_Maps

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. G3 sheet → primary orientation reference
  2. G2 sheet → secondary validation
  3. G1 → latitude & longitude reference
  4. Google Maps → real-world validation (if available)
  5. As-built → supporting validation

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that the North direction is correctly represented and that
  site orientation aligns with geographic reality.

  North arrow must be straight (not rotated), and the layout should
  align with coordinates from G1 and external references if available.

# -----------------------------
# SCOPE
# -----------------------------
scope: |-
  - G3 sheet (Site Layout and Setout Plan)
  - G2 sheet (Overall Site Plan)
  - G1 sheet (Latitude / Longitude)

location_hint:
  region: north_arrow_section

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  STEP 1: North Arrow Validation

  - North arrow present in G3
  - Arrow is straight (aligned vertically upward)
  - No rotated or angled north block

  ------------------------------------------------

  STEP 2: Cross-Sheet Consistency

  - G3 orientation aligns with G2
  - No mismatch between G2 and G3

  ------------------------------------------------

  STEP 3: Coordinate Alignment (if available)

  - Latitude and Longitude present in G1

  - Site orientation logically aligns with:
      • Coordinates (G1)
      • Google Maps (if available)
      • As-built (if available)

  ------------------------------------------------

  FINAL:

  - Orientation is consistent across all available references

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - North arrow missing in G3

  - North arrow is rotated / not straight

  - Orientation mismatch between:
      • G3 and G2

  - Site layout clearly contradicts:
      • Coordinates (G1)
      • Google Maps (if available)

  - Known incorrect orientation from As-built not corrected

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - North arrow not clearly visible

  - Latitude/Longitude missing

  - Google Maps not available AND orientation cannot be inferred

  - G2 sheet missing

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: north_arrow_detection
    keywords:
      - north
      - n
    pass_evidence: 'North arrow detected'
    fail_verdict: FAIL

  - check: coordinate_detection
    regex_patterns:
      - '\b-?\d{1,3}\.\d{3,}\b'
    pass_evidence: 'Coordinates detected: {match}'
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: orientation_alignment
    description: Validate orientation consistency
    logic: |-
      Compare:
        • G3 vs G2 orientation
        • Layout direction vs north arrow

  - check: geo_alignment
    description: Validate real-world alignment
    logic: |-
      If coordinates available:
        Compare with Google Maps

      If As-built available:
        Cross-check orientation

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - lowercase text
  - trim spaces

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT rely only on Google Maps
  - Do NOT fail if Google Maps is unavailable
  - Do NOT assume correctness if north arrow exists
  - Do NOT ignore cross-sheet mismatch

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - G3 is the primary orientation sheet

  - If G3 is correct, G2 is typically aligned

  - North arrow must always be straight (no rotation)

  - Coordinates from G1 are used for geographic validation

  - Google Maps validation is optional but recommended
```

---

## R054.yaml

```yaml
id: R054
name: Drawings must reflect actual site conditions based on SDV photos
type: high

match_keywords:
  - sdv
  - photos
  - as-built
  - existing
  - site condition
  - mismatch

validation_mode: hybrid

complexity: cross_document

required_references:
  - FC_Drawings
  - SDV_Photos

optional_references:
  - As-built

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. SDV Photos → source of truth (actual site condition)
  2. G3 sheet → primary drawing validation
  3. As-built → baseline reference (not authoritative)

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that all existing site conditions shown in drawings
  accurately reflect SDV photos.

  If As-built matches SDV photos → retain existing design.

  If mismatch exists → drawings must be updated to match SDV photos.

# -----------------------------
# SCOPE
# -----------------------------
scope: |-
  - G3 sheet (Site Layout and Setout Plan)
  - SDV Photos
  - As-built drawings (if available)

location_hint:
  region: general_layout

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  STEP 1: SDV Photo Validation

  - Site features visible in SDV photos are identified:
      • Steps / retaining walls
      • Access paths
      • Structures / objects

  ------------------------------------------------

  STEP 2: Drawing Alignment

  - G3 drawing reflects actual site condition from SDV photos

  ------------------------------------------------

  STEP 3: As-built Handling

  - If As-built matches SDV → retained correctly

  - If As-built DOES NOT match SDV:
      → Drawing is updated to reflect SDV (NOT As-built)

  ------------------------------------------------

  STEP 4: Photo Quality Check

  - No duplicate SDV photos present

  ------------------------------------------------

  FINAL:

  - Drawing represents real site condition accurately

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - SDV photos show site condition not reflected in drawing

  - Drawing blindly follows As-built despite mismatch with SDV

  - Missing updates for visible site features:
      • Steps
      • Retaining wall
      • Access path
      • Structures

  - Duplicate SDV photos present

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - SDV photos missing

  - SDV photos unclear or insufficient

  - Site features cannot be reliably identified

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: photo_presence
    keywords:
      - photo
      - sdv
    pass_evidence: 'SDV photos detected'
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: photo_feature_extraction
    description: Identify site features from SDV photos
    logic: |-
      Detect:
        • Steps / retaining walls
        • Access paths
        • Structures
        • Terrain features

  - check: drawing_feature_extraction
    description: Extract features from G3 drawing
    logic: |-
      Identify:
        • Existing structures
        • Access routes
        • Site elements

  - check: feature_alignment
    description: Compare drawing vs SDV
    logic: |-
      For each feature in SDV:
        Check if represented in drawing

  - check: asbuilt_override_logic
    description: Validate correct reference priority
    logic: |-
      If As-built conflicts with SDV:
        SDV takes precedence

  - check: duplicate_photo_detection
    description: Identify duplicate SDV photos
    logic: |-
      Detect repeated or identical images

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - lowercase text
  - trim spaces

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT treat As-built as absolute truth
  - Do NOT pass if SDV and drawing mismatch
  - Do NOT assume correctness without SDV validation
  - Do NOT ignore duplicate SDV photos

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - SDV photos represent actual site condition and override As-built

  - As-built drawings may be outdated and must not be blindly trusted

  - G3 is the primary sheet for site condition validation

  - Example:
      Timber steps visible in SDV but missing in drawing → FAIL

  - This is a foundational rule affecting overall drawing accuracy
```

---

## R055.yaml

```yaml
id: R055
name: Existing and new callouts must be correctly represented without unnecessary references
type: medium

match_keywords:
  - existing
  - new
  - callout
  - reference
  - osd
  - note

validation_mode: hybrid

complexity: cross_document

required_references:
  - FC_Drawings

optional_references:
  - As-built
  - SDV_Photos

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. FC drawings → callout representation (primary)
  2. SDV Photos → confirm existing vs new condition
  3. As-built → baseline reference for existing elements

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that all existing and new elements are correctly represented
  in drawings with appropriate callouts.

  Existing elements must be shown without unnecessary references,
  while new elements must include proper references (e.g., OSD).

# -----------------------------
# SCOPE
# -----------------------------
scope: |-
  - All FC drawing sheets
  - Callouts / notes / annotations

location_hint:
  region: callout_section

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  STEP 1: Existing Elements

  - All existing elements are shown in drawings

  - Existing elements:
      • Do NOT include reference numbers (e.g., OSD)
      • Are clearly marked as existing

  ------------------------------------------------

  STEP 2: New Elements

  - All new elements are clearly identified

  - New elements:
      • Include appropriate references (e.g., OSD, detail refs)
      • Are distinguishable from existing elements

  ------------------------------------------------

  STEP 3: Validation with References

  - Existing vs new classification aligns with:
      • SDV photos
      • As-built drawings

  ------------------------------------------------

  FINAL:

  - Callouts are complete, correctly classified, and properly referenced

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Existing elements include unnecessary references (e.g., OSD numbers)

  - New elements missing required references

  - Existing elements not shown in drawings

  - Misclassification:
      • Existing marked as new
      • New marked as existing

  - Inconsistency between:
      • Drawings vs SDV photos
      • Drawings vs As-built

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - Unable to distinguish existing vs new elements

  - SDV photos and As-built both unavailable

  - Callouts unclear or partially visible

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: reference_detection
    regex_patterns:
      - '\bOSD-\d+\b'
      - '\bREF\b'
    pass_evidence: 'Reference detected: {match}'
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: classification_detection
    description: Identify existing vs new elements
    logic: |-
      Detect keywords:
        • existing
        • new
        • proposed
        • install

  - check: reference_assignment
    description: Validate reference usage
    logic: |-
      For each element:
        If NEW → must have reference
        If EXISTING → must NOT have reference

  - check: cross_validation
    description: Validate classification using SDV and As-built
    logic: |-
      Compare:
        • SDV → actual condition
        • As-built → baseline
        • Drawing → classification

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - lowercase text
  - trim spaces

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT require references for existing elements
  - Do NOT assume all elements are new
  - Do NOT ignore SDV validation
  - Do NOT pass if classification is inconsistent

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Existing elements represent current site condition and should not
    include reference standards like OSD.

  - New elements must always include proper references.

  - This rule ensures clarity between:
      Existing (no reference) vs New (with reference)

  - SDV photos are useful to confirm real site condition.
```

---

## R056.yaml

```yaml

```

---

## R057.yaml

```yaml
id: R057
name: Compound area and lease boundary must match As-built and lease references (Indara)
type: high

match_keywords:
  - compound
  - lease
  - boundary
  - dimension
  - site area

validation_mode: hybrid

complexity: cross_document

required_references:
  - FC_Drawings

optional_references:
  - As-built
  - Lease_Document
  - SDV_Photos

# -----------------------------
# APPLICABILITY
# -----------------------------
applicability: |-
  Applicable for Indara sites only.

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. Lease document → legal boundary (highest priority)
  2. As-built → baseline dimensions
  3. G2 / G3 → implementation in drawings
  4. SDV photos → visual confirmation

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that the compound area and lease boundary shown in drawings
  are accurate and consistent with lease documents, As-built drawings,
  and actual site conditions.

# -----------------------------
# SCOPE
# -----------------------------
scope: |-
  - G2 sheet (Overall Site Plan)
  - G3 sheet (Site Layout and Setout Plan)
  - Lease boundary annotations
  - Compound dimensions

location_hint:
  region: compound_boundary

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  STEP 1: Compound Representation

  - Compound area is clearly shown in drawings
  - Boundaries are properly marked

  ------------------------------------------------

  STEP 2: Dimension Validation

  - Compound dimensions match:
      • As-built drawings (if available)
      • Lease document (if available)

  ------------------------------------------------

  STEP 3: Lease Boundary Validation

  - Lease boundary clearly defined in drawings

  - Lease dimensions align with:
      • Lease document (primary)
      • As-built (secondary)

  ------------------------------------------------

  STEP 4: Photo Alignment (if available)

  - Compound layout aligns with SDV photos:
      • Fence
      • Boundary walls
      • Site enclosure

  ------------------------------------------------

  FINAL:

  - Compound and lease boundaries are accurate and consistent

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Compound area not shown in drawings

  - Missing or unclear boundary markings

  - Dimension mismatch between:
      • Drawing vs As-built
      • Drawing vs Lease document

  - Lease boundary incorrect or missing

  - Significant mismatch with SDV photos

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - Lease document not available

  - As-built not available

  - Dimensions partially visible or unreadable

  - Compound boundary not clearly identifiable

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: dimension_detection
    regex_patterns:
      - '\b\d+(\.\d+)?\s*m\b'
    pass_evidence: 'Dimensions detected: {match}'
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: compound_detection
    description: Identify compound boundary
    logic: |-
      Detect:
        • Fence lines
        • Boundary markings
        • Enclosed site area

  - check: dimension_comparison
    description: Compare dimensions across documents
    logic: |-
      Compare:
        • Drawing vs As-built
        • Drawing vs Lease document

  - check: photo_alignment
    description: Validate visual alignment with SDV
    logic: |-
      Identify:
        • Fence
        • Boundary walls
        • Site enclosure

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - lowercase text
  - trim spaces

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT rely only on drawings
  - Do NOT ignore lease document if available
  - Do NOT pass if dimensions clearly mismatch
  - Do NOT fail if references are missing → return UNCLEAR

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Lease document is the legal source of truth

  - As-built provides baseline but may be outdated

  - SDV photos confirm actual boundary condition

  - Critical for legal and site ownership validation

  - Applies only to Indara sites
```

---

## R058.yaml

```yaml
id: R058
name: Earthing notes must be included in G3 for Indara rooftop sites
type: high

match_keywords:
  - earthing
  - earth
  - grounding
  - rooftop
  - indara

validation_mode: hybrid

complexity: conditional_context

required_references:
  - FC_Drawings

# -----------------------------
# PRECONDITIONS
# -----------------------------
preconditions:
  - site_owner_indara
  - site_type_rooftop

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. Project context → site owner (Indara)
  2. Project context → site type (Rooftop)
  3. G3 sheet → earthing note presence

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that earthing notes are included in the G3 sheet
  when the site belongs to Indara and is a rooftop installation.

# -----------------------------
# SCOPE
# -----------------------------
scope: |-
  - G3 sheet (Site Layout and Setout Plan)
  - Earthing notes / annotations

location_hint:
  region: electrical_notes

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - Site owner is Indara
  - Site type is Rooftop

  AND

  - Earthing notes are clearly included in G3 sheet

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Site owner is Indara AND site is Rooftop

  BUT

  - Earthing notes missing in G3 sheet

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - Site owner not identifiable

  - Site type (rooftop vs ground) unclear

  - G3 sheet missing or unreadable

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: earthing_keyword_detection
    keywords:
      - earthing
      - earth
      - grounding
    pass_evidence: 'Earthing reference found in G3'
    fail_verdict: FAIL

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: g3_note_extraction
    description: Extract earthing-related notes from G3
    logic: |-
      Identify:
        • Earthing notes
        • Grounding instructions
        • Electrical safety notes

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - lowercase text
  - trim spaces

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT apply rule if site owner is not Indara
  - Do NOT apply rule if site is not rooftop
  - Do NOT pass if earthing note is generic but missing in G3
  - Do NOT infer rooftop without clear evidence

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - This is a conditional rule specific to Indara rooftop sites

  - Earthing notes are mandatory for rooftop installations
    due to safety and grounding requirements

  - G3 sheet is the required location for these notes

  - This rule should NOT run if preconditions are not met
    → return NOT_APPLICABLE
```

---

## R059.yaml

```yaml
id: R059
name: Other operator shelter and cable ladder must be shown and aligned with references
type: high

match_keywords:
  - operator
  - shelter
  - cable ladder
  - cable tray
  - existing equipment

validation_mode: hybrid

complexity: cross_document

required_references:
  - FC_Drawings

optional_references:
  - As-built
  - SDV_Photos

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. SDV Photos → actual site condition (primary)
  2. As-built → baseline operator infrastructure
  3. G3 / G2 → drawing representation

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that other operator infrastructure such as shelters and
  cable ladders/trays are correctly shown in the drawings and aligned
  with actual site conditions.

# -----------------------------
# SCOPE
# -----------------------------
scope: |-
  - G3 sheet (Site Layout and Setout Plan)
  - G2 sheet (Overall Site Plan)
  - Operator shelters
  - Cable ladders / trays

location_hint:
  region: operator_infrastructure

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  STEP 1: Operator Infrastructure Detection

  - Other operator shelters identified from:
      • SDV photos
      • As-built drawings

  - Cable ladders / trays identified

  ------------------------------------------------

  STEP 2: Drawing Representation

  - All identified operator shelters are shown in drawings

  - Cable ladders / trays are clearly represented

  ------------------------------------------------

  STEP 3: Cross-Validation

  - Drawing aligns with:
      • SDV photos (primary)
      • As-built (secondary)

  ------------------------------------------------

  FINAL:

  - No operator infrastructure is missing from drawings

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Operator shelter visible in SDV or As-built but missing in drawing

  - Cable ladder / tray present in site but not shown in drawings

  - Incorrect or incomplete representation of operator infrastructure

  - Significant mismatch between:
      • Drawing vs SDV photos
      • Drawing vs As-built

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - SDV photos not available

  - Operator infrastructure not clearly visible

  - As-built not available

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: keyword_detection
    keywords:
      - shelter
      - cable ladder
      - cable tray
    pass_evidence: 'Operator infrastructure keywords detected'
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: photo_infrastructure_detection
    description: Detect operator infrastructure from SDV photos
    logic: |-
      Identify:
        • Operator shelters
        • Cable ladders / trays
        • External equipment

  - check: drawing_infrastructure_extraction
    description: Extract infrastructure from drawings
    logic: |-
      Identify:
        • Shelter locations
        • Cable routing systems

  - check: alignment_validation
    description: Compare drawing vs references
    logic: |-
      Ensure:
        • All detected infrastructure exists in drawing

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - lowercase text
  - trim spaces

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT rely only on drawings
  - Do NOT assume single-operator site
  - Do NOT ignore SDV evidence
  - Do NOT pass if infrastructure is missing

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Telecom sites often have multiple operators (co-location)

  - Other operator infrastructure must always be shown for:
      • Safety
      • Space planning
      • Access clarity

  - SDV photos provide the most accurate site condition

  - As-built may be outdated but still useful for reference
```

---

## R060.yaml

```yaml
id: R060
name: Shelter callout must be present, correct, and in bold layer
type: medium

match_keywords:
  - shelter
  - callout
  - note
  - label

validation_mode: hybrid

complexity: drawing_standard

requires_visual_render: true
render_target_sheets:
  - G3

required_references:
  - FC_Drawings

optional_references:
  - As-built

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. G3 sheet → shelter callout presence (primary)
  2. As-built → shelter reference (secondary)
  3. Drawing notes → formatting and style validation

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that shelter callout is present in the G3 sheet,
  matches As-built reference, and follows drafting standards
  (bold layer / clear visibility).

# -----------------------------
# SCOPE
# -----------------------------
scope: |-
  - G3 sheet (Site Layout and Setout Plan)
  - Shelter callout / label
  - Notes section (left side)

location_hint:
  region: shelter_callout_section

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  STEP 1: Callout Presence

  - Shelter callout is present in G3 sheet

  ------------------------------------------------

  STEP 2: Reference Validation

  - Shelter callout aligns with:
      • As-built shelter reference (if available)

  ------------------------------------------------

  STEP 3: Formatting Requirement

  - Shelter callout is clearly visible

  - Callout appears in bold layer / emphasized style

  ------------------------------------------------

  STEP 4: Notes Alignment

  - Shelter callout matches relevant notes
    (e.g., "2nd point" in left-side notes of G3)

  ------------------------------------------------

  FINAL:

  - Shelter callout is correctly placed, styled, and referenced

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Shelter callout missing in G3

  - Shelter callout present but:
      • Not clearly visible
      • Not in bold/emphasized layer

  - Mismatch between:
      • G3 callout vs As-built

  - Shelter callout not aligned with notes

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - Shelter callout not clearly readable

  - As-built not available

  - Notes section not visible or unclear

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: shelter_keyword_detection
    keywords:
      - shelter
    pass_evidence: 'Shelter callout detected'
    fail_verdict: FAIL

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: callout_extraction
    description: Extract shelter callout from G3
    logic: |-
      Identify:
        • Shelter label
        • Position in layout

  - check: style_validation
    description: Validate callout visibility/style
    logic: |-
      Check:
        • Bold/emphasized appearance
        • Clear readability

  - check: reference_alignment
    description: Validate with As-built
    logic: |-
      Compare shelter reference between:
        • G3
        • As-built

  - check: note_alignment
    description: Validate with G3 notes
    logic: |-
      Match shelter callout with:
        • Notes section (left side)
        • Specific referenced point

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - lowercase text
  - trim spaces

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT assume presence if keyword exists elsewhere
  - Do NOT ignore formatting requirements
  - Do NOT fail if As-built is unavailable (use drawing only)
  - Do NOT pass if callout is unclear or poorly visible

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Shelter callout is typically a standard element

  - It must be clearly visible and emphasized (bold layer)

  - G3 is the primary sheet for validating shelter location

  - Notes section (left side) provides additional validation reference

  - This rule ensures clarity and drafting consistency
```

---

## R061.yaml

```yaml
id: R061
name: GPS antenna model and placement must match RRU vendor and references
type: high

match_keywords:
  - gps
  - gnss
  - ayge
  - antenna
  - rru

validation_mode: hybrid

complexity: cross_document + vendor_logic

required_references:
  - FC_Drawings

optional_references:
  - FR
  - RLM

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. FR (Feature Report) → RRU vendor (preferred source)
  2. RLM → equipment layout validation
  3. FC drawings → GPS model and placement

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that the GPS antenna model and placement are correct
  based on the RRU vendor (Nokia or Ericsson).

  GPS model must align with RRU manufacturer, and placement must
  be correctly represented in drawings.

# -----------------------------
# SCOPE
# -----------------------------
scope: |-
  - G3 sheet (Site Layout)
  - Equipment layout / antenna callouts
  - GPS antenna location

location_hint:
  region: gps_antenna_section

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  STEP 1: RRU Vendor Identification

  - RRU vendor identified from:
      • FR (preferred)
      • RLM (fallback)

  ------------------------------------------------

  STEP 2: GPS Model Validation

  CASE 1: Nokia RRU

  - GPS antenna model = Nokia AYGE

  ------------------------------------------------

  CASE 2: Ericsson RRU

  - GPS antenna model = GNSS GPS

  ------------------------------------------------

  STEP 3: Telecom Logic

  - Vodafone:
      • Always uses Nokia RRU
      → GPS must be AYGE

  - Optus:
      • Nokia RRU → AYGE
      • Ericsson RRU → GNSS

  ------------------------------------------------

  STEP 4: Placement Validation

  - GPS antenna is mounted on:
      • Cable ladder OR
      • Shelter wall (top)

  - Placement matches:
      • FR
      • RLM

  ------------------------------------------------

  FINAL:

  - GPS model and placement are correct and consistent

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - GPS model does not match RRU vendor

      • Nokia RRU + GNSS → FAIL
      • Ericsson RRU + AYGE → FAIL

  - Vodafone site but GPS not AYGE

  - GPS antenna missing in drawing

  - GPS placement incorrect or not aligned with:
      • FR
      • RLM

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - RRU vendor not identifiable

  - GPS model not clearly mentioned

  - FR and RLM both unavailable

  - GPS placement unclear in drawing

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: gps_model_detection
    keywords:
      - ayge
      - gnss
      - gps
    pass_evidence: 'GPS model detected: {found}'
    fail_verdict: UNCLEAR

  - check: rru_vendor_detection
    keywords:
      - nokia
      - ericsson
    pass_evidence: 'RRU vendor detected: {found}'
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: vendor_mapping
    description: Map RRU vendor to GPS model
    logic: |-
      If Nokia → AYGE
      If Ericsson → GNSS

  - check: telecom_logic
    description: Apply operator-specific rules
    logic: |-
      Vodafone → Nokia → AYGE
      Optus → depends on RRU vendor

  - check: placement_validation
    description: Validate GPS antenna location
    logic: |-
      Confirm placement on:
        • Cable ladder
        • Shelter top

  - check: cross_reference_validation
    description: Validate against FR and RLM
    logic: |-
      Ensure:
        • GPS model matches FR
        • Placement matches RLM

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - lowercase text
  - trim spaces

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT assume vendor without FR or RLM
  - Do NOT pass if GPS model is generic (not specific)
  - Do NOT ignore telecom-specific rules
  - Do NOT pass if placement is missing

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - GPS antenna model depends strictly on RRU vendor

  - Nokia → AYGE
  - Ericsson → GNSS

  - Vodafone always uses Nokia RRUs

  - Optus may use Nokia or Ericsson depending on region

  - FR is the preferred source for vendor identification

  - Placement is typically:
      • Cable ladder
      • Shelter top

  - This rule ensures vendor consistency and installation correctness
```

---

## R062.yaml

```yaml
id: R062
name: All proposed equipment must be located within lease area
type: high

match_keywords:
  - lease area
  - boundary
  - equipment
  - antenna
  - shelter
  - layout

validation_mode: hybrid

complexity: geometric_validation

required_references:
  - FC_Drawings

optional_references:
  - As-built
  - Lease_Document

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. G3 sheet → lease boundary (primary)
  2. Equipment layout → proposed equipment (bold layers)
  3. As-built / lease doc → boundary validation (optional)

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that all proposed equipment shown in the drawing
  is located within the defined lease area boundary.

  Ensure that visual representation (antenna blocks / symbols)
  accurately reflects real positioning and does not falsely
  appear compliant.

# -----------------------------
# SCOPE
# -----------------------------
scope: |-
  - G3 sheet (Site Layout and Setout Plan)
  - Lease boundary outline
  - Proposed equipment (bold layers)

location_hint:
  region: lease_area_section

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  STEP 1: Lease Boundary Detection

  - Lease area boundary is clearly defined in drawing

  ------------------------------------------------

  STEP 2: Equipment Identification

  - All proposed equipment identified:
      • Antennas
      • Shelter
      • Equipment cabinets
      • Cable ladder (if applicable)

  ------------------------------------------------

  STEP 3: Boundary Validation

  - All proposed equipment lies completely within lease boundary

  - No part of equipment extends beyond boundary

  ------------------------------------------------

  STEP 4: Block Accuracy Validation

  - Antenna blocks / symbols accurately represent real footprint

  - No visual misrepresentation:
      • Equipment appears inside but actually extends outside

  ------------------------------------------------

  FINAL:

  - All proposed equipment is correctly placed within lease area

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Any proposed equipment extends outside lease boundary

  - Antenna block overlaps or crosses boundary

  - Equipment placement visually misleading:
      • Appears inside but dimensionally incorrect

  - Lease boundary missing or unclear

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - Lease boundary not clearly visible

  - Equipment blocks unclear or unreadable

  - Scale or dimensions not sufficient to validate

  - Only partial drawing available

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: lease_keyword_detection
    keywords:
      - lease
      - boundary
      - area
    pass_evidence: 'Lease boundary reference detected'
    fail_verdict: UNCLEAR

  - check: equipment_detection
    keywords:
      - antenna
      - shelter
      - cabinet
    pass_evidence: 'Equipment elements detected'
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: boundary_extraction
    description: Identify lease boundary
    logic: |-
      Detect:
        • Boundary lines
        • Lease labels
        • Enclosed area

  - check: equipment_extraction
    description: Identify proposed equipment
    logic: |-
      Extract:
        • All bold-layer equipment
        • Antenna blocks
        • Shelter footprint

  - check: spatial_validation
    description: Validate equipment within boundary
    logic: |-
      For each equipment:
        Check if fully inside lease boundary

  - check: footprint_validation
    description: Validate block accuracy
    logic: |-
      Ensure:
        • Symbol size reflects actual footprint
        • No hidden boundary violations

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - lowercase text
  - trim spaces

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT assume equipment is inside based on visual overlap alone
  - Do NOT ignore antenna block size vs actual footprint
  - Do NOT pass if boundary is unclear
  - Do NOT validate non-proposed (existing) equipment

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - This is a critical compliance rule (lease violation risk)

  - Proposed equipment is usually shown in bold layers

  - Antenna blocks must reflect true dimensions

  - Common issue:
      • Block appears inside boundary
      • Actual footprint extends outside

  - G3 sheet is the primary validation source

  - This rule ensures:
      Design compliance with lease constraints
```

---

## R063.yaml

```yaml
id: R063
name: Removed feeders and proposed hybrid cables must be detailed and feasible within existing cable infrastructure
type: high

match_keywords:
  - feeder
  - hybrid cable
  - reuse existing
  - cable ladder
  - cable tray
  - length
  - mm2

validation_mode: hybrid

complexity: capacity_validation + cross_document

required_references:
  - FC_Drawings

optional_references:
  - RLM
  - FR

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. FR → feeder scope (primary)
  2. RLM → routing and infrastructure
  3. G3 notes → cable details and feasibility

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that removed feeder details and proposed hybrid cable details
  are clearly specified and that hybrid cables can be accommodated within
  existing cable ladder/tray/conduit infrastructure.

# -----------------------------
# SCOPE
# -----------------------------
scope: |-
  - G3 sheet (Notes section)
  - Cable ladder / tray references
  - Feeder / hybrid cable notes

location_hint:
  region: feeder_notes_section

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  STEP 1: Feeder Replacement Details

  - Notes clearly mention:
      • Reuse existing feeders OR
      • Removal of feeders

  ------------------------------------------------

  STEP 2: Hybrid Cable Details

  - Proposed hybrid cables include:
      • Cable length (e.g., 40m)
      • Cable size (e.g., 10mm²)
      • Quantity (e.g., 1 off)

  ------------------------------------------------

  STEP 3: Infrastructure Reference

  - Cable routing clearly specifies:
      • Cable ladder / tray width (e.g., 450mm)
      • Existing infrastructure usage

  ------------------------------------------------

  STEP 4: Feasibility Validation

  - Proposed cables logically fit within:
      • Existing cable ladder / tray
      • Conduit / monopole (if used)

  - Multi-operator sharing is feasible:
      • Example: Optus + Vodafone cables sharing ladder

  ------------------------------------------------

  FINAL:

  - Feeder transition is clearly defined and physically feasible

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Missing feeder replacement details

  - Hybrid cable details incomplete:
      • No length
      • No size
      • No quantity

  - No reference to cable ladder / tray

  - Cable routing unclear or missing

  - Obvious infeasibility:
      • Multiple cables in small ladder
      • No available routing path

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - Cable size or length not readable

  - Infrastructure dimensions not visible

  - FR/RLM not available for cross-check

  - Notes partially captured

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: cable_length_detection
    regex_patterns:
      - '\b\d+\s?m\b'
    pass_evidence: 'Cable length found: {match}'
    fail_verdict: UNCLEAR

  - check: cable_size_detection
    regex_patterns:
      - '\b\d+\s?mm²\b'
      - '\b\d+\s?mm2\b'
    pass_evidence: 'Cable size found: {match}'
    fail_verdict: UNCLEAR

  - check: ladder_width_detection
    regex_patterns:
      - '\b\d+\s?mm\b.*ladder'
    pass_evidence: 'Cable ladder width found: {match}'
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: feeder_transition_detection
    description: Detect feeder replacement logic
    logic: |-
      Identify:
        • "reuse existing"
        • "remove feeder"
        • "install hybrid"

  - check: cable_detail_validation
    description: Validate completeness of cable specification
    logic: |-
      Ensure:
        • Length present
        • Size present
        • Quantity present

  - check: infrastructure_mapping
    description: Identify cable routing infrastructure
    logic: |-
      Detect:
        • Cable ladder
        • Cable tray
        • Shared routing

  - check: feasibility_assessment
    description: Evaluate capacity feasibility
    logic: |-
      Validate:
        • Cable count vs ladder size
        • Multi-operator sharing feasibility

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - lowercase text
  - trim spaces

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT pass if only generic "install cable" text exists
  - Do NOT assume feasibility without infrastructure reference
  - Do NOT ignore cable size/length
  - Do NOT fail if exact math not possible → use qualitative logic

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Real drawings include:
      • Cable length (e.g., 40m)
      • Cable size (e.g., 10mm²)
      • Ladder width (e.g., 450mm)

  - Hybrid cables often replace feeders

  - Multi-operator sharing is common and must be validated

  - This rule ensures:
      Detailed documentation + physical feasibility

  - This is a semi-manual validation rule → confidence may be lower
```

---

## R064.yaml

```yaml
id: R064
name: Antenna tags (ID and azimuth) must match RLM/FR and be correctly positioned
type: high

match_keywords:
  - antenna
  - azimuth
  - tag
  - sector
  - optus
  - vodafone

validation_mode: hybrid

complexity: cross_document + spatial_annotation

required_references:
  - FC_Drawings

optional_references:
  - RLM
  - FR

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. FR → antenna configuration (primary)
  2. RLM → antenna layout and orientation
  3. G3 drawing → tag placement and azimuth display

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that antenna tags (antenna number, operator label, and azimuth)
  are correctly shown in drawings, aligned with RLM and FR, and properly
  positioned relative to antenna blocks.

# -----------------------------
# SCOPE
# -----------------------------
scope: |-
  - G3 sheet (Site Layout)
  - Antenna blocks and tag labels
  - Azimuth indicators

location_hint:
  region: antenna_tag_section

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  STEP 1: Antenna Tag Presence

  - Each antenna has:
      • Tag (ID/number)
      • Operator label (O / V)
      • Azimuth value

  ------------------------------------------------

  STEP 2: Cross-Reference Validation

  - Antenna tags match:
      • FR (preferred)
      • RLM

  - Includes:
      • Correct antenna numbering
      • Correct azimuth angles

  ------------------------------------------------

  STEP 3: Operator Identification

  - O → Optus
  - V → Vodafone

  - Tags correctly mapped to operator

  ------------------------------------------------

  STEP 4: Multi-Antenna Positioning Rule

  - If multiple antennas on same pole:

      • Higher antenna → tag placed closer to antenna block

      • Lower antenna → tag placed accordingly

  - No overlapping or ambiguous tag placement

  ------------------------------------------------

  STEP 5: Azimuth Representation

  - Azimuth direction clearly shown

  - Orientation aligns with:
      • RLM
      • FR

  ------------------------------------------------

  FINAL:

  - Antenna tags are accurate, readable, and correctly positioned

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Missing antenna tags

  - Incorrect antenna numbering

  - Azimuth mismatch with RLM or FR

  - Wrong operator labeling:
      • O/V mismatch

  - Incorrect positioning:
      • Tag not aligned with antenna
      • Higher antenna tag placed incorrectly

  - Overlapping or unclear tags

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - Tags not readable

  - RLM/FR not available

  - Multiple antennas but positioning unclear

  - Azimuth values partially visible

# -----------------------------
# DECISION SCHEMA (FOR LLM TRACE)
# -----------------------------
decision_schema:
  - step: check_antenna_tags
    description: Are antenna numbers, operator labels (O/V), and azimuths clearly visible on G3?
  - step: check_azimuth_alignment
    description: Do the azimuths on G3 match the FR/RLM reference?
  - step: check_spatial_positioning
    description: For multiple antennas on one pole, is the tag placement unambiguous?
  - step: reconcile_evidence
    description: Does the evidence fully support a PASS, or are critical elements missing?

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: antenna_tag_extraction
    description: Extract antenna tags and IDs
    logic: |-
      Identify:
        • Antenna numbers
        • Operator labels
        • Tag text

  - check: azimuth_alignment
    description: Validate azimuth against references
    logic: |-
      Compare:
        • Drawing azimuth
        • FR / RLM azimuth

  - check: operator_mapping
    description: Validate operator assignment
    logic: |-
      Map:
        O → Optus
        V → Vodafone

  - check: spatial_positioning
    description: Validate tag placement relative to antenna
    logic: |-
      For multiple antennas:
        • Higher antenna → tag closer
        • Maintain clear association

  - check: overlap_detection
    description: Detect overlapping or unclear tags
    logic: |-
      Ensure:
        • Tags do not overlap
        • Clear readability maintained

# -----------------------------
# NORMALIZATION
# -----------------------------
normalization_rules:
  - lowercase text
  - trim spaces

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT assume correctness without FR/RLM validation
  - Do NOT pass if azimuth is missing or incorrect
  - Do NOT ignore positioning rules for multiple antennas
  - Do NOT pass if tags are visually ambiguous

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Antenna tags include:
      • ID
      • Operator (O/V)
      • Azimuth

  - FR is the source of truth for antenna configuration

  - RLM validates layout and orientation

  - Multi-antenna poles require strict tag positioning logic

  - Common issue:
      • Tags not updated after design change

  - This rule ensures:
      RF accuracy + drawing clarity
```

---

## R065.yaml

```yaml
id: R065
name: EME signage must align with Form A/B, OSD-171, and site conditions
type: high

validation_mode: hybrid

required_references:
  - Form_A_B
  - OSD_171
  - Site_Photos

optional_references:
  - FC_Drawings

complexity: multi_source_validation

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate EME signage content, placement, and compliance using:
    - Form A / Form B (primary reference)
    - OSD-171 document (standard)
    - G3 drawing (placement)
    - SDV photos (site verification)

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. Form A / B → signage requirement (source of truth)
  2. OSD-171 → content standard
  3. G3 → placement validation
  4. SDV photos → real-world confirmation

# -----------------------------
# DECISION FLOW
# -----------------------------
decision_flow: |-
  Step 1: Identify signage requirement from Form A/B

  Step 2: Validate signage content against OSD-171

  Step 3: Validate signage placement in G3:
    • Leader present
    • Correct location

  Step 4: Cross-check with SDV photos

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - Signage requirement matches Form A/B

  - Signage content aligns with OSD-171

  - G3 sheet:
      • Signage shown
      • Leader correctly positioned

  - SDV photos confirm signage presence (if visible)

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Signage missing in G3 but required in Form A/B

  - Signage content contradicts OSD-171

  - Leader incorrectly placed or missing

  - Photos contradict drawing (signage missing on site)

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - Form A/B not available

  - OSD-171 reference not accessible

  - SDV photos do not show signage area

  - G3 visibility unclear

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: signage_detection
    description: Detect signage callouts in G3

  - check: leader_validation
    description: Validate leader direction and placement

  - check: content_alignment
    description: Compare signage text with OSD-171

  - check: photo_validation
    description: Confirm signage presence in SDV photos

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT rely on drawings alone (photos preferred)
  - Do NOT assume signage if not visible
  - Do NOT fail if photos unavailable → return UNCLEAR

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Form A/B defines requirement
  - OSD-171 defines content
  - G3 defines placement
  - Photos confirm reality
```

---

## R066.yaml

```yaml
id: R066
name: Roof levels must be shown and validated (Rooftop sites only)
type: high

validation_mode: hybrid

required_references:
  - As-built

optional_references:
  - Form_A_B
  - FC_Drawings

complexity: conditional_site_type + cross_reference

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that roof levels are shown in drawings for rooftop sites
  and match As-built or Form A/B references.

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. Site type detection (rooftop vs non-rooftop)
  2. G3 / elevation drawings → roof level presence
  3. As-built / Form A/B → validation reference

# -----------------------------
# DECISION FLOW
# -----------------------------
decision_flow: |-
  Step 1: Detect site type

    IF site ≠ rooftop:
        → NOT APPLICABLE (N/A)

    IF rooftop:
        → proceed

  Step 2: Detect roof level in drawing

    Look for:
      • RL (Roof Level)
      • Height markers
      • Elevation references

  Step 3: Cross-check with:
    • As-built elevation sheet
    • Form A/B

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  CASE 1: Rooftop site

  - Roof level clearly shown in:
      • G3 OR
      • Elevation drawing

  - Roof level aligns with:
      • As-built OR
      • Form A/B

  ------------------------------------------------

  CASE 2: Non-rooftop site

  - Rule not applicable → PASS / N/A

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Rooftop site BUT:
      • Roof level not shown

  - Roof level contradicts As-built / Form A/B

  - Missing elevation reference for rooftop

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - Site type cannot be determined

  - Roof level not readable in drawing

  - As-built / Form A/B not available

# -----------------------------
# DETERMINISTIC CHECKS
# -----------------------------
deterministic_checks:

  - check: roof_level_detection
    regex_patterns:
      - '\bRL\b'
      - 'roof level'
      - '\+\d+(\.\d+)?'
    pass_evidence: 'Roof level detected'
    fail_verdict: UNCLEAR

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: site_type_detection
    description: Identify rooftop vs ground site

  - check: elevation_validation
    description: Compare roof level with reference

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT validate for non-rooftop sites
  - Do NOT fail if As-built missing → return UNCLEAR
  - Do NOT require exact numeric match (allow tolerance)

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Rooftop sites require roof level reference for installation context

  - Ground-based sites do NOT require this validation

  - Typical indicators:
      • RL notation
      • Elevation markers
```

---

## R067.yaml

```yaml
id: R067
name: Walkway and step-over validation (Rooftop sites only)
type: high

validation_mode: hybrid

required_references:
  - Site_Photos

optional_references:
  - As-built
  - FC_Drawings

complexity: conditional_site + material_based_validation

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate designated walkways and step-overs for rooftop sites.

  Requirement depends on roof type:
    - Roof sheet → walkways required
    - Concrete roof → walkways optional

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. Site type detection (rooftop)
  2. Roof type detection (sheet vs concrete)
  3. Photos (actual condition)
  4. As-built / G3 (supporting)

# -----------------------------
# DECISION FLOW
# -----------------------------
decision_flow: |-
  Step 1: Detect site type

    IF site ≠ rooftop:
        → NOT APPLICABLE (N/A)

  Step 2: Detect roof type

    IF roof sheet:
        → walkway REQUIRED

    IF concrete:
        → walkway OPTIONAL

  Step 3: Validate using:
    • SDV photos (primary)
    • As-built / G3 (support)

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  CASE 1: Roof sheet

  - Walkway present in:
      • Photos OR
      • Drawings

  - Provides access to antennas

  - Step-overs present where required

  ------------------------------------------------

  CASE 2: Concrete roof

  - Walkway may be absent

  - No unsafe access condition observed

  ------------------------------------------------

  FINAL:

  - Access path is safe and logically defined

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Roof sheet AND:
      • Walkway missing

  - Unsafe access path:
      • No clear route to antennas

  - Step-overs required but missing

  - Drawings show walkway but not present in photos

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - Roof type not identifiable

  - Photos do not show roof surface

  - Walkway visibility unclear

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: roof_type_detection
    description: Identify roof material
    logic: |-
      Detect:
        • corrugated / metal → roof sheet
        • flat slab → concrete

  - check: walkway_detection
    description: Detect walkway presence
    logic: |-
      Identify:
        • walkway paths
        • grating / panels
        • marked access paths

  - check: stepover_detection
    description: Detect step-over elements
    logic: |-
      Identify:
        • step-over frames
        • cable crossings

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT require walkway for concrete roofs
  - Do NOT rely only on drawings (photos preferred)
  - Do NOT fail if photos missing → return UNCLEAR

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Roof sheet sites require walkways to prevent damage

  - Concrete roofs allow direct access

  - Step-overs are required where obstructions exist

  - Photos override drawings for actual condition
```

---

## R068.yaml

```yaml
id: R068
name: Safety handrails and anchor points validation (Rooftop sites only)
type: high

validation_mode: hybrid

required_references:
  - Site_Photos

optional_references:
  - As-built
  - FC_Drawings

complexity: conditional_site + safety_validation

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate presence and correctness of safety handrails and anchor points
  for rooftop sites using SDV photos as primary reference.

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. Site type detection (rooftop)
  2. SDV photos (actual condition – source of truth)
  3. As-built (baseline)
  4. FC drawings (support)

# -----------------------------
# DECISION FLOW
# -----------------------------
decision_flow: |-
  Step 1: Detect site type

    IF site ≠ rooftop:
        → NOT APPLICABLE (N/A)

  Step 2: Detect safety systems from photos

    Identify:
      • Handrails (edge protection)
      • Anchor points (fall arrest)

  Step 3: Cross-check with:
      • As-built
      • G3 / elevation drawings

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  CASE 1: Handrails

  - Handrails present where required (roof edges / fall zones)

  OR

  - Not present BUT:
      • Anchor-based safety system exists

  ------------------------------------------------

  CASE 2: Anchor Points

  - Anchor points present and visible in photos

  - Consistent with As-built / drawings

  ------------------------------------------------

  FINAL:

  - At least one valid fall protection system is present
  - Drawings do not contradict site condition

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - No handrails AND no anchor points present

  - Safety system shown in drawings but not present in photos

  - Clear unsafe condition (unprotected roof access)

  - Anchor/handrail contradicts As-built

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - Photos do not show roof edges

  - Safety elements not visible

  - Site type unclear

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: handrail_detection
    description: Detect rooftop handrails
    logic: |-
      Identify:
        • edge railings
        • guard rails

  - check: anchor_detection
    description: Detect anchor points
    logic: |-
      Identify:
        • anchor bolts
        • lifeline anchors
        • safety eyelets

  - check: safety_consistency
    description: Compare with drawings
    logic: |-
      Ensure no contradiction between:
        • photos
        • as-built
        • G3

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT validate for non-rooftop sites
  - Do NOT fail if only one system (handrail OR anchor) exists
  - Do NOT rely only on drawings (photos override)
  - Do NOT fail if photos missing → return UNCLEAR

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Photos are the source of truth

  - Safety can be ensured by:
      • Edge protection (handrails)
      • Fall arrest (anchor points)

  - At least one system must be present

  - This is a safety-critical rule
```

---

## R069.yaml

```yaml
id: R069
name: Trees and vegetation must be represented in drawings
type: medium
 
validation_mode: hybrid
 
required_references:
  - As-built
  - Google_Snippet_PDF
 
optional_references:
  - FC_Drawings
 
complexity: environment_detection + representation_validation
 
# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that trees and vegetation around the site are identified
  and represented in the drawings.
 
# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. Google Snippet PDF (primary – real-world reference)
  2. As-built (baseline reference)
  3. G2 / G3 drawings (representation)
 
# -----------------------------
# DECISION FLOW
# -----------------------------
decision_flow: |-
  Step 1: Detect surroundings from Google Snippet PDF / As-built
 
    • Identify vegetation:
        - trees
        - green areas
 
    • Ignore:
        - rectangular shapes (buildings)
        - hard structures
 
  Step 2:
 
    IF vegetation present:
        → Must be shown in drawings
 
    IF no vegetation:
        → No requirement
 
# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  CASE 1: Vegetation present
 
  - Vegetation visible in:
      • Google Snippet PDF OR
      • As-built
 
  - Represented in:
      • G2 OR G3 drawing
 
  ------------------------------------------------
 
  CASE 2: No vegetation
 
  - No vegetation detected in references
 
  - Drawings consistent with surroundings
 
  ------------------------------------------------
 
  FINAL:
 
  - Vegetation accurately represented
 
# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Vegetation present BUT not shown in drawings
 
  - Major trees missing from layout
 
  - Drawings contradict real-world vegetation
 
# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - Google Snippet PDF not available
 
  - As-built not available
 
  - Vegetation visibility unclear
 
# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:
 
  - check: vegetation_detection
    description: Detect trees/vegetation
    logic: |-
      Identify:
        • trees
        • green patches
        • landscaping
 
      Exclude:
        • rectangular shapes (buildings)
        • concrete areas
 
  - check: drawing_representation
    description: Validate vegetation in drawings
    logic: |-
      Look for:
        • tree symbols
        • vegetation markers
        • site surroundings
 
# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT treat rectangular shapes as vegetation (these are buildings)
  - Do NOT require exact count of trees
  - Do NOT fail for minor vegetation omissions
  - Do NOT rely only on drawings
  - Do NOT fail if references missing → return UNCLEAR
 
# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - Google Snippet PDF is the primary visual reference
 
  - Buildings are typically represented as rectangles and must be ignored
 
  - Focus only on vegetation impacting site layout
 
  - Minor shrubs can be ignored
 
```

---

## R070.yaml

```yaml
id: R070
name: Panel/AAU antenna model, dimensions, and orientation validation
type: high

validation_mode: hybrid

required_references:
  - RLM
  - FR

optional_references:
  - FC_Drawings

complexity: multi_attribute_validation

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate that panel/AAU antennas are correctly represented in drawings,
  including:
    - Antenna model and dimensions
    - Antenna presence and placement
    - Azimuth (orientation) consistency

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. RLM → primary technical specification
  2. FR → supporting reference
  3. FC drawings → implementation

# -----------------------------
# DECISION FLOW
# -----------------------------
decision_flow: |-
  Step 1: Extract antenna data from RLM/FR:
    • Model
    • Dimensions
    • Azimuth

  Step 2: Validate drawing:
    • Antenna blocks present
    • RRU blocks present (if applicable)

  Step 3: Compare:
    • Model / dimension consistency
    • Azimuth alignment

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - Antenna blocks (panel/AAU) present in drawing

  - Antenna model/dimensions match RLM/FR

  - Azimuth:
      • Shown in drawing
      • Matches RLM/FR (allow small tolerance ±2–5°)

  - Callouts correctly label:
      • Antenna number
      • Azimuth
      • Model reference

  ------------------------------------------------

  FINAL:

  - Antenna configuration is consistent across all sources

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Antenna missing in drawing

  - Model/dimension mismatch with RLM/FR

  - Azimuth:
      • Missing OR
      • Clearly incorrect

  - Callouts incorrect or inconsistent

  - Multiple antennas incorrectly labeled or ordered

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - RLM or FR not available

  - Antenna details not readable in drawing

  - Azimuth partially visible

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: antenna_detection
    description: Detect panel/AAU blocks

  - check: rru_detection
    description: Detect RRU blocks

  - check: model_extraction
    description: Extract antenna model from RLM/FR

  - check: azimuth_validation
    description: Compare azimuth values
    logic: |-
      Allow tolerance ±2–5 degrees

  - check: callout_validation
    description: Validate antenna labels and annotations

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT require exact textual match for model (allow formatting differences)
  - Do NOT fail for minor azimuth deviation (tolerance allowed)
  - Do NOT rely only on drawings (must compare with RLM/FR)

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - RLM is the source of truth for antenna configuration

  - FR supports validation if RLM unclear

  - Azimuth is critical for network alignment

  - Higher antenna tags should be placed closest to antenna blocks when multiple antennas exist
```

---

## R071.yaml

```yaml
id: R071
name: Antenna separation and clearance validation (G3-1)
type: high

validation_mode: hybrid

required_references:
  - RLM
  - FC_Drawings

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate antenna spacing and angular separation in G3-1 layout.

# -----------------------------
# DECISION FLOW
# -----------------------------
decision_flow: |-
  Step 1: Identify antennas and classify:
    • Passive antenna
    • AAU

  Step 2: Extract:
    • Position (for distance)
    • Azimuth (for angle)

  Step 3: Compute:
    • Horizontal separation
    • Angular separation

  Step 4: Check obstruction within beam

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - Horizontal separation ≥ 500 mm

  - Angular separation:
      • Passive ≥ 70°
      • AAU ≥ 60°

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Horizontal separation < 500 mm

  - Angular separation below threshold

# -----------------------------
# FLAG CONDITIONS
# -----------------------------
flag_conditions: |-
  - RRU / steel / antenna present within beam path

  → Highlight to DE / TL

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - Antenna positions not measurable

  - Azimuth not visible

  - Antenna type unclear

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - 500 mm spacing is mandatory

  - Angular separation depends on antenna type

  - Obstruction is a design risk, not a fail condition
```

---

## R072.yaml

```yaml
id: R072
name: Antenna tag, block size, and azimuth validation
type: high

validation_mode: hybrid

required_references:
  - RLM
  - FR

optional_references:
  - FC_Drawings

complexity: multi_attribute_consistency

# -----------------------------
# DESCRIPTION
# -----------------------------
description: |-
  Validate antenna tag numbering, antenna/RRU block size,
  and azimuth consistency with RLM and FR.

# -----------------------------
# DECISION PRIORITY
# -----------------------------
decision_priority: |-
  1. RLM → primary specification
  2. FR → supporting reference
  3. Drawings → implementation

# -----------------------------
# DECISION FLOW
# -----------------------------
decision_flow: |-
  Step 1: Extract from RLM/FR:
    • Antenna tags
    • Antenna model (dimension reference)
    • Azimuth

  Step 2: Validate in drawing:
    • Tag numbering
    • Antenna block size
    • RRU block presence
    • Azimuth callouts

# -----------------------------
# PASS CRITERIA
# -----------------------------
pass_criteria: |-
  - Antenna tags:
      • Present
      • Correct numbering (no mismatch/duplication)

  - Antenna block size:
      • Matches model/dimension from RLM/FR

  - RRU block:
      • Present where applicable

  - Azimuth:
      • Shown in drawing
      • Matches RLM/FR (±2–5° tolerance)

  - Callouts correctly aligned with antenna blocks

# -----------------------------
# FAIL CRITERIA
# -----------------------------
fail_criteria: |-
  - Missing or incorrect antenna tag numbers

  - Duplicate or inconsistent tagging

  - Antenna block size mismatch

  - RRU missing where required

  - Azimuth:
      • Missing OR
      • Clearly incorrect

# -----------------------------
# UNCLEAR CONDITIONS
# -----------------------------
unclear_conditions: |-
  - RLM / FR not available

  - Drawing resolution insufficient

  - Block dimensions not measurable

# -----------------------------
# SEMANTIC CHECKS
# -----------------------------
semantic_checks:

  - check: tag_detection
    description: Extract antenna tags

  - check: block_size_validation
    description: Compare antenna block vs model

  - check: rru_detection
    description: Identify RRU blocks

  - check: azimuth_validation
    description: Compare azimuth values

  - check: callout_alignment
    description: Ensure labels point to correct antenna

# -----------------------------
# NEGATIVE CONSTRAINTS
# -----------------------------
negative_constraints:
  - Do NOT require exact text match for model names
  - Do NOT fail for minor azimuth deviation (≤5°)
  - Do NOT rely only on drawings without RLM/FR

# -----------------------------
# NOTES
# -----------------------------
notes: |-
  - This rule mirrors G3 validation logic but applied to detail sheet

  - Tag consistency is critical for antenna identification

  - Azimuth accuracy directly impacts network performance
```

---

