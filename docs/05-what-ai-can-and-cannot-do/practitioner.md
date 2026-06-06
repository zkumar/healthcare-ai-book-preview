# Practitioner Depth — Chapter 5 — What AI Can and Cannot Do

*Decision-framework tools that operationalize the chapter's mental model. Written for strategy leads, AI architects, governance professionals, and operational leaders deciding where to deploy AI and how to govern it.*

## Data Snapshots

## Tool 1 — AI Category Classification Checklist

Before labeling any system "AI" in your organization, answer these questions. They determine which category the system actually belongs to — and therefore which performance expectations, governance requirements, and regulatory obligations apply.

| # | Diagnostic Question | If Yes → Category | Governance Regime That Applies |
|---|---|---|---|
| **Q1** | Does the system execute logic that was explicitly written by a human? | Rule-Based Automation | Automation governance, not AI governance |
| **Q2** | Does the system learn patterns from historical labeled data and produce a fixed-form output (score, classification, prediction)? | Classical Machine Learning | ML validation requirements — training/validation/test splits, performance metrics on holdout set, distribution-shift monitoring |
| **Q3** | Does the system synthesize across sources, generate language, reason through novel problems, or operate across multiple task types without retraining? | Generative AI | GenAI governance — hallucination risk management, HITL design, intended-use specification, PCCP if regulated |
| **Q4** | Does the system's output directly influence a clinical decision, a regulatory submission, or a financial determination? | Regulated AI (overlay) | Regardless of category, add regulated-AI obligations on top of the applicable framework above |

### How to use

1. Answer Q1–Q3 in order. The first **Yes** locates the system's primary category.
2. Always answer Q4 separately — it determines whether regulated-AI overlay obligations apply.
3. Document the answer set in the system's intended-use file. Re-evaluate whenever the system's intended use, training data, or output channel changes.

> **Expert Note — Category Drift**
>
> A system can move categories without anyone noticing. A rules engine that gets a learned-model add-on becomes Classical ML. A Classical ML model that is replaced with a foundation-model wrapper becomes GenAI. A non-regulated analytics tool whose output starts feeding a coverage-decision workflow becomes Regulated AI. Run this checklist at every material change.

## Tool 3 — Pre-Deployment Readiness Assessment

Before any healthcare AI system goes live, all items in this checklist must be confirmed. Items marked **REGULATORY** are required for regulated deployments — SaMD, payer AI used in coverage decisions, or any system deployed in EU markets.

| Domain | Required Items | Regulatory Anchor |
|---|---|---|
| **Data Foundation** | Training data quality assessed and documented · missingness patterns characterized · demographic representation audited against deployment population · vocabulary version tagged | **REGULATORY** for FDA SaMD and EU AI Act conformity |
| **Governance Infrastructure** | Consent framework in place for all data sources · audit trail system operational · data lineage tracking active · role-based access controls implemented and tested | — |
| **Hallucination Risk** | Hallucination failure modes identified and documented · RAG or grounding architecture implemented where applicable · human review gates defined for all clinically significant outputs | **REGULATORY** — ISO 14971 risk register entry required |
| **Human Oversight Design** | HITL checkpoints defined and tested in workflow · override mechanism available and documented · accountability assignment documented for each AI-influenced decision | **REGULATORY** — FDA SaMD and EU AI Act Article 14 requirement |
| **Intended Use Statement** | Intended use documented and scoped to advisory function · clinical decision-replacement language explicitly excluded · regulatory classification determination documented and signed off | **REGULATORY** — mandatory for any FDA or EU regulatory pathway |
| **Performance Monitoring** | Baseline performance metrics established on validation cohort · drift detection mechanism in place · performance review cadence defined · retraining trigger criteria documented | — |
| **PCCP (if applicable)** | Predetermined Change Control Plan drafted if system is continuously learning or foundation-model-based · permissible change types, performance bounds, and validation methodology specified | **REGULATORY** — required for FDA AI/ML SaMD submissions |

### How to use

- Walk every domain before go-live. Every required item must be **confirmed**, not **planned**.
- Items left at "planned" become production debt the day the system goes live; the cost of clearing them post-launch is always higher than the cost of clearing them pre-launch.
- For non-regulated deployments, the **REGULATORY** items are still recommended — they are the cheapest insurance against a future scope change that pulls the system into regulated use.

> **Expert Note — The Pre-Launch Audit**
>
> Treat the readiness assessment as an internal audit: an independent reviewer (not the build team) walks every item and signs off. The build team will reliably overestimate readiness; the independent reviewer is the cheapest mechanism to surface that gap before production exposes it.

## Tool 2 — Problem-First Diagnostic Worksheet

Use this worksheet before any AI initiative kickoff. Complete it with operational leaders, not technology teams. The answers locate the genuine AI opportunity before technology selection begins.

| Step | Prompt | What to Capture |
|---|---|---|
| **1. Effort inventory** | List the top five workflows in your organization where human effort per decision is highest relative to decision volume. | For each workflow: nature of human effort — judgment, synthesis, generation, or physical action |
| **2. Synthesis bottlenecks** | For each synthesis or generation workflow from Step 1: what information sources are humans currently consulting to make this decision? | Whether sources are available in structured form; whether a system that synthesized all of them simultaneously would beat human synthesis under time pressure |
| **3. Underused data** | Identify the three largest data assets currently underutilized in operational decisions. | For each: is the gap between data availability and decision quality a function of human bandwidth, human access, or genuine analytical uncertainty? |
| **4. Adjacent-workflow scan** | List your current AI investments. | For each: original problem solved · adjacent problems the same platform could address with marginal additional investment · ratio of point-solution cost to platform cost for the adjacent problems |
| **5. Roadmap rank** | Rank the identified opportunities by value (clinical impact × financial impact × feasibility). | Top three become the platform AI roadmap. Build them sequentially on a shared governance and data foundation, not as separate initiatives. |

### How to use

- Run this in a 90-minute session with operational leaders before any vendor briefing.
- One scribe captures answers in a shared document. No technology vendors in the room.
- Steps 1–3 surface candidate problems. Step 4 prevents fragmenting the AI portfolio into point solutions. Step 5 sequences the work.
- Re-run annually, or whenever a new foundation-model capability tier becomes available.

> **Expert Note — Beware the Demo-Driven Roadmap**
>
> If the worksheet was preceded by a vendor demo, the answers will reverse-engineer a problem to fit the demo. Run Steps 1–3 *before* any vendor contact to keep the diagnosis honest.

## Workshop Tools (Excel)

_Fillable templates with dropdowns, formula-driven verdicts, and conditional formatting._ Open in Excel, Numbers, or Google Sheets and run with your team.

| Template | Download |
|---|---|
| **AI Category Checklist** | [⬇ `ai-category-checklist.xlsx`](../files/ai-category-checklist.xlsx) |
| **Pre Deployment Readiness** | [⬇ `pre-deployment-readiness.xlsx`](../files/pre-deployment-readiness.xlsx) |
| **Problem First Worksheet** | [⬇ `problem-first-worksheet.xlsx`](../files/problem-first-worksheet.xlsx) |
