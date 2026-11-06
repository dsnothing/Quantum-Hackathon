# Submission checklist

Official sources checked November 6, 2026, starting around **03:36 EST in Waterloo** (08:36 UTC): [event](https://uwquantum.com/qiskit-fall-fest), [registration](https://uwquantum.com/fall-fest-signup).

## Verified public requirements

| Requirement | Package evidence |
|---|---|
| Python notebook bridging quantum and another field | `Quantum_2048.ipynb`, shared `quantum2048.py`, game development bridge |
| Explanatory slides | `output/Quantum_2048_Five_Minute.pptx`, matching viewing PDF and detailed speaker notes |
| Judges use simulator; hardware optional | Everything runs locally, no credentials; only simulator outputs claimed |
| Individual registration | Human action for every team member |
| Live presentation for chance at physical certificate | Human action |

The event page lists November 6 **18:30–21:00**, DC 1351. Registration lists **17:30–20:30**. These conflict. Neither establishes a submission cutoff.

## Unresolved organizer requirements

- [ ] Confirm exact cutoff and upload destination. Neither appears on accessible public pages.
- [ ] Confirm talk duration. Current deck targets five minutes for slides 1–6; slides 7–10 are optional appendix.
- [ ] Confirm accepted file extensions. Notebook/slides are verified; PPTX and PDF are chosen deliverable formats, not confirmed requirements.
- [ ] Confirm AI assistance and pre-existing/reused work rules. AI use is disclosed. No earlier game source or assets copied.
- [ ] Resolve presentation time conflict from organizer communications.
- [ ] Add team identity where appropriate, review outputs and rehearse.
- [ ] Register each member and attend the live presentation if seeking certificate eligibility.
- [ ] Upload the notebook, slides and necessary source/dependencies by the actual organizer instructions. GitHub publication alone is not submission.

## Engineering evidence

| Check | Evidence |
|---|---|
| Slide/merge order, all directions, no double merge | `tests/test_core.py`, 10 passing core tests |
| Normalized states, partial and repeated measurement | Qiskit validity checks, Bell conditional marginal assertions |
| Exact independent 50% / linked 100% | notebook section 2, analytical assertions |
| Committed sampling | 198/400 independent, 400/400 linked in executed notebook |
| Preview purity, RNG preservation, branch agreement | tests comparing cloned live states and committed outcomes |
| Linked identities after movement/merge | distant collapse and consumed-ID checks |
| Spawn cap, restart, win/loss | core tests and 160-move invariant run |
| Clean notebook | `execute_notebook.py`, fresh-kernel execution, no error cells |
| JavaScript syntax | `node --check web/app.js` |
| Browser desktop/mobile | real interface exercises and screenshots under `evidence/`; details in `VERIFICATION.md` |
| Slides | latest rendered previews in `output/Quantum_2048_Five_Minute_Previews/`, package validation in build record |

No organizer submission or registration is automated. Repository push was separately authorized by the user. Usability study, physical touch-device testing, physical hardware execution, formal strategic balance evaluation and learning efficacy measurement remain undone and are not claimed.
