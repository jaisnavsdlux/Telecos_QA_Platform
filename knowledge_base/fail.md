# FAIL Knowledge Base

All rules that have returned FAIL verdict.
Auto-updated after every validation run.

---

## R002 — Drawings must be correct scale in all sheets
- **Verdict:** FAIL
- **Drawing:** M8398_DOREEN TOWNSHIP_FC_30052025 (2).pdf
- **Last seen:** 2026-03-18 15:10
- **Pages checked:** 3, 4, 5
- **Reference image:** 1-Scale.png
- **Evidence:** Sheet M8398-G2 (Overall Site Plan) uses scale 1:1500, which is classified as 'Not Preferred' per the standard drawing scale reference. Sheet M8398-G3 detail uses 1:200 (Standard/Preferred) and Sheet M8398-G3-2 uses 1:25 (Acceptable), both of which comply. The 1:1500 scale on M8398-G2 should be highlighted as it does not meet the preferred or acceptable scale standards.
- **Times seen:** 1
- **Confidence:** 0.5 🔴 Low

---

## R003 — FC stamp is correctly mentioned to all sheets?
- **Verdict:** FAIL
- **Drawing:** M8398_DOREEN TOWNSHIP_FC_30052025 (2).pdf
- **Last seen:** 2026-03-19 11:03
- **Pages checked:** 0, 1, 2
- **Reference image:** 2-Draft.png
- **Evidence:** The DRAFT stamp shown in the reference image is not present on any of the three FC drawing sheets reviewed (M8398-00, M8398-01, M8398-G1). All sheets show 'FOR CONSTRUCTION' in the title block but are missing the required DRAFT overlay stamp.
- **Times seen:** 2
- **Confidence:** 0.525 🔴 Low

---


## R005b — Child CAD template layer format
- **Verdict:** FAIL
- **Drawing:** M8398_DOREEN TOWNSHIP_FC_30052025 (2).pdf
- **Last seen:** 2026-03-18 15:10
- **Pages checked:** 3, 4, 5
- **Reference image:** 4-Child CAD template Layer format.png
- **Evidence:** In the FC drawing, proposed/new elements (e.g., 'PROPOSED EWP SET UP LOCATION', 'NEW MERCS#2 SIGNAGE', 'INSTALL NEW VODAFONE NOKIA FYGC GPS ANTENNA', 'NEW JURALCO WALKWAY/HANDRAIL') appear in the same unbold text weight as existing elements. Per the child CAD template rule, proposed/new items must use bold layers while existing items use unbold layers. The drawings do not show this distinction — both existing and new annotation text appear in uniform non-bold weight throughout all pages.
- **Times seen:** 1
- **Confidence:** 0.5 🔴 Low

---

## R007 — Work authority number is correct
- **Verdict:** FAIL
- **Drawing:** M8398_DOREEN TOWNSHIP_FC_30052025 (2).pdf
- **Last seen:** 2026-03-19 12:00
- **Pages checked:** 0, 1, 2
- **Reference image:** 2-Work Authority ID -1.png
- **Evidence:** The Work Authority Number in the FC drawing is 540268 (shown as 'OPTUS WORK AUTHORITY Nº 540268' on the cover sheets), but the reference image (Antenna System tab Scope of Works) shows WA ID 658102. The numbers do not match.
- **Times seen:** 1
- **Confidence:** 0.5 🔴 Low

---

## R012 — Service stream site only - Add  “SAED_DA/DC/L3/LO CONDITIONS” in reference documents (Refer snip 8 in next sheet for details)
- **Verdict:** FAIL
- **Drawing:** M8398_DOREEN TOWNSHIP_FC_30052025 (2).pdf
- **Last seen:** 2026-03-19 12:00
- **Pages checked:** 0, 1, 2
- **Reference image:** 9-SS-SAED.png
- **Evidence:** The FC drawing (M8398-01) Reference Documents section does not include 'SAED_DA/DC/L3/LO CONDITIONS'. This is a ServiceStream site (confirmed by ServiceStream logo and distribution entry), and the required entry is missing from the reference documents list, whereas the reference image clearly shows it should be present and highlighted.
- **Times seen:** 1
- **Confidence:** 0.5 🔴 Low

---

## R017 — Point 1 "Existing structure sections" Mention existing tower with heights, model & Owner. Like below format; EXISTING INDARA 54.76m HIGH ROAM RT84 SELF SUPPORTING LATTICE TOWER
- **Verdict:** FAIL
- **Drawing:** M8398_DOREEN TOWNSHIP_FC_30052025 (2).pdf
- **Last seen:** 2026-03-19 12:00
- **Pages checked:** 0, 1, 2
- **Reference image:** 2-Existing structure sections TITLE.png
- **Evidence:** The FC drawing (M8398-G1) section heading reads 'EXISTING INDARA ROOFTOP SITE' but does not include the required format stating the structure height, model, and owner together (e.g., 'EXISTING INDARA Xm HIGH [MODEL] ROOFTOP POLE'). The 8.65m referenced in point 1 refers to the building parapet wall height, not the structure description in the required format. The model of the mounting pole/turret is not mentioned in the existing structure section as required.
- **Times seen:** 1
- **Confidence:** 0.5 🔴 Low

---

## R021 — Is the antenna maintenance access by EWP only or access step pegs with Lad Saf?. If Lad-saf are present at existing, please check which is certified or not. (Point 5)
- **Verdict:** FAIL
- **Drawing:** M8398_DOREEN TOWNSHIP_FC_30052025 (2).pdf
- **Last seen:** 2026-03-19 12:00
- **Pages checked:** 0, 1, 2
- **Reference image:** 7-Existing structure sections.png
- **Evidence:** The FC drawing (M8398-G1, point 4 under Existing Indara Rooftop Site) states antenna maintenance access is via 'LADDER AND STEP PEGS WITH FALL ARREST SYSTEM,' and construction access notes reference a Lad-Saf cable on site. However, the drawing does not confirm whether the Lad-Saf/fall arrest system is certified or not, which is required per the rule when Lad-Saf is present at the existing site.
- **Times seen:** 1
- **Confidence:** 0.5 🔴 Low

---

## R030 — Update Corrosion Protection note on G1 page. (Only Servicestream site)
- **Verdict:** FAIL
- **Drawing:** M8398_DOREEN TOWNSHIP_FC_30052025 (2).pdf
- **Last seen:** 2026-03-19 12:00
- **Pages checked:** 0, 1, 2
- **Reference image:** 14-Corrosion protection.png
- **Evidence:** The G1 page (M8398-G1) of this ServiceStream site does not contain a CORROSION PROTECTION section. The reference image shows a required CORROSION PROTECTION note with CORROSIVITY CATEGORY AS/NZS 2312.2 and PROPOSED CORROSION PROTECTION SYSTEM fields, but no such section is present on the FC drawing's G1 page.
- **Times seen:** 1
- **Confidence:** 0.5 🔴 Low

---

## R062 — Calculate RF tail length for all RRUs - please consider horizontal & vertical distance for tail calculation
- **Verdict:** FAIL
- **Drawing:** M8398_DOREEN TOWNSHIP_FC_30052025 (2).pdf
- **Last seen:** 2026-03-19 12:00
- **Pages checked:** 5, 6, 7, 8, 9
- **Reference image:** Tail length calculation 1.png
- **Evidence:** The FC drawing does not include any RF tail length calculations for the RRUs. From the elevation drawing (M8398-G4), passive antennas are at EL 15.00m while RRUs range from EL 12.20m down to EL 9.10m, giving vertical distances of 2.8m to 5.9m. RRUs at EL 9.10m have a vertical gap of ~5.9m from the passive antenna, which already exceeds the 5m limit before adding horizontal run and bending radius. The reference image requires explicit annotation of horizontal distance + vertical distance + bending allowance = total RF tail length, and client approval notation if >5m. None of these calculations or annotations are present in the FC drawing pages (G3, G3-2, G3-3, G4).
- **Times seen:** 1
- **Confidence:** 0.5 🔴 Low

---

## R070 — AC units working conditions
- **Verdict:** FAIL
- **Drawing:** M8398_DOREEN TOWNSHIP_FC_30052025 (2).pdf
- **Last seen:** 2026-03-19 12:00
- **Pages checked:** 0, 1, 2
- **Reference image:** 6-AC issue.png
- **Evidence:** The reference image shows 2 OFF split AC units with a water leakage issue captured by the SDV Engineer. None of the FC drawing pages (M8398-00, M8398-01, M8398-G1) contain any notation or callout regarding the AC unit working conditions or the water leakage issue. This issue has not been highlighted in the DFC as required.
- **Times seen:** 1
- **Confidence:** 0.5 🔴 Low

---

## R080 — Mention PDT approved version number. Please make sure use recent PDT tools
- **Verdict:** FAIL
- **Drawing:** M8398_DOREEN TOWNSHIP_FC_30052025 (2).pdf
- **Last seen:** 2026-03-19 12:00
- **Pages checked:** 0, 1, 2
- **Reference image:** 15-PDT version number.png
- **Evidence:** No PDT approved version number is mentioned anywhere in the FC drawing pages reviewed (M8398-00, M8398-01, M8398-G1). The reference image shows that the drawing should include a statement such as 'OPTUS POWER TOOL V12.7 APPROVED' in the notes/specifications section, but this is absent from the FC drawing.
- **Times seen:** 1
- **Confidence:** 0.5 🔴 Low

---

## R081 — Ensure the exact AC power supply value is mentioned, and it must align with the PVA, power meter photos, and SLD. Also, confirm if a power upgrade is required
- **Verdict:** FAIL
- **Drawing:** M8398_DOREEN TOWNSHIP_FC_30052025 (2).pdf
- **Last seen:** 2026-03-19 12:00
- **Pages checked:** 0, 1, 2
- **Reference image:** 16-AC power supply.png
- **Evidence:** The FC drawing (M8398-G1) states the existing AC power supply is 40A 3-Phase and requires an upgrade to 63A. However, the PVA report confirms the Optus supply is 50A 3-Phase (meter SN:218038715, 50A protection/main switch rating), and the PDT AC Power Summary shows existing capacity of 50A is sufficient for the proposed upgrade with no upgrade required. The stated 40A value does not align with the PVA, and the power upgrade statement contradicts both the PVA and PDT findings.
- **Times seen:** 1
- **Confidence:** 0.5 🔴 Low

---

