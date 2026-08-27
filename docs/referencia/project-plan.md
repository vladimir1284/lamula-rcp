# **LAMULA RCP — Project Plan**

**Project:** LAMULA RCP — Radar Control Processor & Operator MMI (successor to Ravis 1.3 \+ RCP \+ Rainbow) **Goal:** Bring a Gematronik weather radar back to operational life with a fully in-house software stack, with no Gematronik dependency. The RCP controls the radar, ingests pre-computed moments from the DSP/DRX, archives the **volumetric observation** as NEXRAD **Level-II**, and feeds that base data to **ORPG** through a complete WSR-88D **RDA emulation**; all meteorological product generation is delegated to ORPG. **Duration:** 8 months (34 weeks) **Team:** 6 (4 software engineers \+ 2 product/domain experts acting as QA) **Delivery model:** AI-agent-accelerated, spec-and-test-driven development **Month-8 success criterion:** the complete system validated end-to-end against in-house simulators (and against a real or stubbed ORPG over the RDA interface); field commissioning against real hardware follows after month 8\.

---

## **Revision note (this update)**

This revision incorporates four decisions taken after the first draft. They are listed here so the change is auditable; the rest of the document reflects them throughout.

1. **The ORPG feed moves from the DSP to the RCP.** Rationale: the RCP is the node that manages the archiving of observations, and the DSP is headless (no GUI). The DSP now only delivers moments to the RCP; the RCP archives them and feeds ORPG. *Cross-project consequence:* the LAMULA DSP plan must be updated to remove its `DSP ↔ ORPG` contract and the ORPG output encoders — that responsibility now lives here.

2. **The RCP ↔ DSP link is 1 GbE.** Outside the FPGA, 1 Gb Ethernet is sufficient; the high-rate path (ADC/DDC/decimation and the 10GbE inside the DRX) stays internal to the FPGA/DRX and is out of scope for the RCP.

3. **The RCP archives only the volumetric observation** (base data: Z/V/W \+ dual-pol, by volume) — **not** derived products. The **primary archive/output format is NEXRAD Level-II.** Product generation is ORPG's responsibility.

4. **The RDA emulation is implemented in full.** The system depends 100% on ORPG for product generation, so the RCP↔ORPG (WSR-88D RDA, ICD 2620002\) interface is a complete, critical-path, Stage-1 deliverable — not a partial encoder.

---

## **1\. Executive Summary**

LAMULA RCP is a clean-sheet design and build of the radar control software stack: the Radar Control Processor (RCP) control logic and hardware routines, automated scan scheduling, archiving of the volumetric observation, the ORPG feed (RDA emulation), the LAMULA RCP web-based operator MMI (which reproduces the operationally relevant behaviour of Ravis), and a hardware-faithful radar simulator.

Because we control the entire interface, we discard the legacy RCL protocol and the legacy four-level control-mode arbitration. The system targets a single radar model, a single operator on a control-room laptop (a thin browser client), and runs on a private, air-gapped operational network — which removes the entire security-hardening workstream.

The RCP does **not** generate meteorological products. It receives pre-computed moments from the DSP (the "DRX"), persists the volumetric observation as NEXRAD Level-II, and streams that base data by radial to ORPG, which performs all product generation. This makes the `RCP ↔ ORPG` interface (a complete WSR-88D RDA emulation per ICD 2620002\) mission-critical: with no in-house product path, the system depends 100% on ORPG.

The architecture's central principle is a Hardware Abstraction Layer (HAL) with two interchangeable implementations behind one interface: a real-hardware adapter (Modbus/Profibus via an SBC) and a simulator adapter. The whole stack runs identically against either, which is exactly what makes "validate on simulators now, commission on hardware later" a sound delivery strategy and what keeps the control laptop trivially replaceable.

The plan is structured around four milestones (M1–M4) over five phases, sized for a 6-person AI-accelerated team. The two largest residual risks are **simulator fidelity** (the acceptance gate is simulator-based, so the system is only as validated as the simulator is faithful) and the **100% dependency on the external ORPG** for product generation. Both are owned by the two product experts and managed explicitly throughout.

## **2\. Context & Objectives**

The radar hardware (transmitter, analog receiver, antenna/servo and associated sensors and actuators) exists and is well understood by the team. The objective is to replace all proprietary Gematronik control software with an independent stack, so the radar can be operated, scanned, archived and delivered to ORPG without the original vendor.

Objectives, in priority order:

1. Reliably and safely power up and control the radar (the six control routines) through a clean hardware interface.

2. Execute manual and automated volume scans.

3. Ingest pre-computed moments from the DSP/DRX (over 1 GbE) and present them as live PPI / RHI / ASCOPE displays with full color management.

4. Archive the acquired **volumetric observation** as NEXRAD Level-II.

5. Feed that base data to ORPG by radial, in real time, through a complete WSR-88D RDA emulation; ORPG generates all products.

6. Provide a single-operator web MMI reproducing the operationally relevant Ravis feature set.

7. Provide a simulator faithful enough to serve as the validation and acceptance platform.

## **3\. Scope**

### **3.1 In scope (Stage 1 — this project)**

* Hardware Abstraction Layer (HAL) with real-hardware (Modbus/Profibus over SBC) and simulator adapters behind one interface.

* Radar simulator: emulates sensors/actuators at the HAL boundary and emulates the DSP/DRX moment stream, with fault injection for BITE testing.

* Control routines: general radar power-on, transmitter power-on, analog-receiver power-on, antenna-unit power-on, antenna movement, antenna positioning.

* Parameter-safety guard (low-responsibility, complementing hardware interlocks): antenna limit checks and prevention of pulse-width × PRF combinations that would damage the klystron/magnetron.

* Scan controller \+ scheduler: interactive scans (Scan Worksheet equivalent) and automated volume scans (Stage-1 must-have).

* DSP/DRX moment ingestion: subscribe to and route pre-computed moments (UZ, CZ, ZDR, V, W, I, Q) from the external DSP **over a 1 GbE link**.

* **Archive (salva):** persistence of the **volumetric observation** as **NEXRAD Level-II (primary format)**, plus scan, status and event metadata. No derived products are archived.

* **ORPG interface — complete WSR-88D RDA emulation (ICD 2620002):** Message 31 / Message 1 base-data framing; CTM and MSG headers; the RDA state machine (Standby / Startup / Operate / Offline-Operate); periodic RDA status (Message 2); loopback test (Messages 11/12); RDA control-command processing from ORPG (Message 6, including VCP change, transmission enable/disable, calibration control); clutter filter map and bypass map (Messages 15/13); VCP definitions; TCP server with login. Real-time **by-radial Level-II** stream to ORPG. (RDABackendPy is the reference implementation.)

* Gateway: REST \+ WebSocket API (FastAPI) co-located on the backend server.

* LAMULA RCP web MMI (Vue 3): Control Center, passive/active toggle, System Visualization with live subsystem status, Antenna Control, Scan Worksheet, DRX/RSP control & calibration views, PPI / RHI / ASCOPE data views with 256-level color management, BITE message window, System Information window, and an ORPG-link status view.

* Calibration (Stage 1): single-point calibration and TX power/adjustment workflows.

* Packaging: offline, air-gapped installer for the server; thin browser client.

### **3.2 Out of scope**

* Hardware re-engineering / reverse-engineering of the radar and replacement of proprietary devices with general-purpose ones — handled by the team outside this project; we assume full knowledge of and access to the hardware interface.

* DSP signal processing (I/Q → moments) — a separate component/project; we consume pre-computed moments.

* **Product generation** — performed entirely by **ORPG** (the separate LAMULA ORPG project); the RCP only delivers base data to it.

* The high-rate acquisition path (ADC/DDC/decimation, 10GbE) — internal to the FPGA/DRX; the RCP only sees the 1 GbE moment stream.

* Field commissioning on real hardware — occurs after month 8; this project delivers a system validated on simulators (and against ORPG over the RDA interface) and commissioning-ready.

* Security hardening / authentication / multi-tenant access control — air-gapped private network, single operator.

### **3.3 Stage 2 / deferred (documented, not built now)**

Additional output/distribution formats beyond Level-II — **MDV by-volume to NCAR TITAN**, and **NETCDF / HDF5** for research/archive; concurrent multi-destination distribution engine; Sun Position / Sun Track auto-alignment; email/notification messaging; an RCL-console-equivalent low-level maintenance terminal; geographic overlays and location-out-of-center; RX linearity validation, power monitor, signal-generator and ITSG control modules; multi-radar / heterogeneous support; multi-operator concurrency and control-authority arbitration; remote IoT access (HTTPS/VPN) and role-based access control.

## **4\. System Architecture**

### **4.1 Overview**

A single server on the operational network hosts the entire backend, the gateway and the RDA emulation. The control-room laptop runs only a browser pointed at that server, so replacing the laptop has no operational impact. The backend is layered; every layer above the HAL is agnostic to whether it is driving real steel or the simulator.

Data flow: the **DSP/DRX** is an external moment source the RCP subscribes to **over 1 GbE**; the RCP fans each ray out to the live displays, to the Level-II archive, and to the **ORPG interface**, which presents the RCP to ORPG as a WSR-88D RDA and streams base data by radial. **ORPG** is the downstream product generator. The simulator emulates the DSP/DRX during development and validation; ORPG (real open-source build, or a CM\_TCP stub) closes the loop on the other side.


### **4.3 Key design principles**

* **HAL swappability** — one interface, two adapters (real / simulator). Nothing above the HAL changes between simulator validation and field operation.  
* **Simulator as the acceptance oracle** — the simulator is a first-class, early, critical-path deliverable, not a test fixture afterthought. Acceptance in month 8 is defined against it.  
* **ORPG as the sole product generator** — the RCP produces no products; it archives the volumetric observation (Level-II) and feeds ORPG. The `RCP ↔ ORPG` RDA interface is therefore mission-critical.  
* **Clean, modern contracts** — `RCP↔MMI`, `RCP↔DSP/DRX` and `RCP↔HAL` are defined as explicit typed contracts (Pydantic on the backend, generated TypeScript on the front end). The fourth contract, `RCP↔ORPG`, is the fixed WSR-88D RDA/RPG ICD (2620002) rather than an in-house schema. No legacy RCL.  
* **Single operator, passive/active toggle** — the legacy four-level control arbitration collapses to one passive (monitor) / active (control) switch.  
* **Soft real-time only** — hard real-time (triggering, PRF, pulse integration) lives in hardware/DRX; the Python backend performs soft-real-time control, orchestration, archiving and the by-radial ORPG feed.

### **4.4 Component summary**

| Component | Responsibility |
| ----- | ----- |
| Gateway (FastAPI) | REST \+ WebSocket endpoints; serves the built MMI; enforces the typed contracts |
| Scan Controller & Scheduler | Sequences interactive and automated volume scans; drives the control routines |
| Control Routines | The six power-on / movement / positioning routines against the HAL |
| Parameter-Safety Guard | Rejects unsafe parameter combinations (PRF×pulse-width duty, antenna limits); status-checking, low safety responsibility |
| DSP/DRX Moment Ingestion | Receives pre-computed moments over 1 GbE; fans out to displays, Level-II archive and the ORPG interface |
| Archive (Level-II) | Persists the volumetric observation as NEXRAD Level-II; plus scan/status/event metadata |
| **ORPG Interface / RDA Emulation** | Presents the RCP to ORPG as a WSR-88D RDA per ICD 2620002: Message 31/1 base data by radial, CTM/MSG headers, RDA state machine, status (Msg 2), loopback (Msg 11/12), control commands (Msg 6), clutter/bypass maps (Msg 15/13), VCP, TCP server \+ login |
| System Status & BITE Manager | Aggregates subsystem status; manages BITE/fault messages, filtering and history; surfaces ORPG-link health |
| HAL | Single hardware interface with real and simulator adapters |
| Radar Simulator | Hardware \+ DSP/DRX-stream emulation with fault injection |
| LAMULA RCP MMI | Operator front end reproducing the Ravis feature set |

### **4.5 MMI Screen Inventory (detail)**

The bullets in §3.1 name the MMI's screens at a high level. This section pins down what each screen must actually show and do, at the level of detail a mature operator console reaches — informed by the screen/workflow structure of established radar consoles (Ravis among them), but re-specified from scratch for LAMULA RCP's own data model and reduced (single-operator, single-radar) scope.

*Sourcing note:* the Data Views and DRX/RSP Control & Calibration entries below carry added detail mined from Ravis's own Data Views, Control Windows and Calibration chapters — capabilities and interaction patterns only, never Ravis's exact labels, layout or text, per the sourcing rule in [index.md](../index.md). Both screens are **not yet built** in the `lamula-rcp` implementation, so this detail is tracked there as a *proposed* pendiente (product-expert confirmation required before it's treated as decided), not retrofitted onto the already-built screens (System Visualization, Antenna Control, Scan Worksheet, BITE window, System Information), which stay as originally specified.

* **System Visualization.** A subsystem map rather than a single status LED: separate live indicators for Transmitter, Receiver, Antenna/Servo, DSP/DRX link, RCP core, and the ORPG link, each carrying a three-state health color (normal / degraded / fault) plus a fourth "no data" state when a subsystem is unreachable. Radar-on, servo-on and radiation-on are the only three commands exposed from this screen in active mode; every other indicator is read-only. A compact event/message strip surfaces the most recent BITE entries inline, with a link into the full BITE window.
* **Antenna Control.** Two coupled panels: a step/position control (target azimuth/elevation, jog controls, current position readout) and a servo-status panel (servo enabled/faulted, torque/velocity limits, following-error indication). Movement commands are rejected client-side and server-side alike when the parameter-safety guard flags an out-of-limit target, with the rejection reason shown next to the control, not just logged.
* **Scan Worksheet.** Parameter entry for a single scan (PRF, pulse width, elevation/azimuth range, dwell, unambiguous range/velocity trade-off) plus a saved-strategy list for the automated volume-scan scheduler. Every edited field re-runs the parameter-safety guard live (duty-cycle and antenna-limit checks) so an operator sees a rejection before starting the scan, not after.
* **DRX/RSP Control & Calibration.** Six sub-views, not one grouped panel:
    1. *TX/RX adjustment* — transmit power setpoint, receiver gain/attenuation stages, per-pulse-width TX timing/sampling window, live readouts (linear power, IF frequency, channel-switch point and mode — static-threshold vs. dynamic-saturation-detect — inter-channel phase correction).
    2. *Calibration folder* — two distinct procedures, not one: **Zero Check** (noise-floor sampling), which runs automatically at boot and on a fixed background interval with no operator action; and **single-point / TX power calibration**, the manual, maintenance-staff-only, operator-guided workflow described in the Calibration & Alignment entry below. The automatic Zero Check is a standing requirement distinct from that manual workflow — it must run whether or not an operator ever opens this screen.
    3. *Trigger/timing setup* — an editable table, one row per trigger output.
    4. *DRX process monitor* — the operator-facing counterpart of the DSP/DRX Moment Ingestion component in §4.4: a live, read-only mirror of every parameter currently in effect on the acquisition pipeline (operating mode, full range/PRF/filter/threshold set) — wider than link up/down and ray-rate/dropped-ray counters alone.
    5. *DRX BiTE folder* — explicitly **pull-only, not push**: values refresh only on an explicit operator request, with a stated staleness warning (not to be relied on for real-time power-supply monitoring). This is a distinct semantic from the RCP's own System Status & BITE Manager (§4.4), which is push/event-based — the two must not be conflated in the UI or in the contract.
    6. *Misc / radar-equation constants folder* — static calibration constants (losses, wavelength, beam widths, antenna gain, atmospheric/radome loss, dual-PRF filter-init pulse count), editable under the same apply/save-as-default convention as the Data Views Color Composer (below).

    **Resolved (2026-08-27, `lamula-rcp` D-13):** calibration-writing actions — the manual single-point/TX power calibration commit and the radar-equation constants folder (sub-views 2 and 6 above) — sit behind a second explicit **maintenance-mode gate**, on top of the single passive/active toggle from §4.3, enforced client- and server-side like the parameter-safety guard. Scoped narrowly: TX/RX adjustment and trigger/timing setup stay behind active mode alone; Zero Check is exempt entirely (automatic, no operator action). This is a gate on *what action* the one active operator may take, not a reinstatement of Ravis's discarded four-level control arbitration — §4.3's single-operator principle is unchanged. A dedicated calibration activity log (distinct from the general BITE/fault log) and a restore-previous-calibration rollback action accompany it.
* **Data Views (PPI / RHI / ASCOPE).** PPI and RHI share one color-management subsystem (a 256-level color table per data type, editable via the Color Composer below) rather than two independent renderers; **ASCOPE is not color-coded** and instead needs its own per-pixel aggregation-mode toggle (max-of-bins vs. average-of-bins, for when multiple range bins map to one display pixel) and an X-axis unit toggle (distance vs. time). PPI supports pan/zoom and freeze; RHI shares the azimuth cursor with the active PPI; ASCOPE renders the raw I/Q or moment profile along the current beam for calibration and diagnostic use. Freeze/unfreeze is per-window and independent — other open views keep updating regardless. Multi-data-type switching (UZ/CZ/V/W/ZDR/…) is a single control shared across all three views, not per-view state. Every view supports a point-probe: clicking a point shows range/azimuth/elevation/intensity in the active data type's unit and keeps updating live at that same point as new rays arrive, until the operator clicks elsewhere — not a static snapshot. A variable refresh-rate divider (operator-settable "show every Nth update") and an independent display-resolution selector (coarser/finer rendering quantization, distinct from any archive bit-depth decision) trade update smoothness against rendering headroom at high antenna speed.

    *Color Composer (PPI/RHI only).* A preset matrix per data type (tabbed); a linear-RGB interpolate-between-two-selected-colors tool to build a gradient ramp instead of hand-picking every level; copy/paste of a whole preset between data types; three color-entry modes (swatches / HSB / RGB). Every edit here — and every edit in the DRX/RSP folders above — follows one MMI-wide convention: **apply** (transient, current session) is always a separate, explicit action from **save as default** (persisted), gated by a confirmation prompt.
* **BITE / Fault Window.** A filterable, timestamped fault/event log (by subsystem, by severity, by acknowledged/unacknowledged) with an extended-detail pane for the selected entry (raw fault code, affected subsystem, first/last occurrence). Acknowledging an entry is logged as an operator action, not silently cleared.
* **System Information Window.** A single read-only diagnostic surface listing software/firmware versions per subsystem, current configuration snapshot (active VCP, calibration constants in effect, network/link addresses for DSP/DRX and ORPG), and uptime/connection counters — the reference operators pull up before calling for support, so it must be exportable as a single text/JSON blob for a support ticket without needing screen captures.
* **Calibration & Alignment workflow.** Two Stage-1 workflows, both operator-guided (step list with pass/fail gates, not a single "calibrate" button): **(1) TX channel calibration** — sampling/timing adjustment followed by TX power calibration against a reference measurement; **(2) single-point receiver calibration and linearity check** — inject a known reference signal, record the receiver's response at that point, and validate that the reflectivity computed from it matches the expected value from the radar equation for the system's known constants (antenna gain, pulse width, wavelength, receiver bandwidth). The result of each step is persisted with a timestamp so calibration drift is visible over time, not just the latest value.
* **ORPG-link status view.** No Ravis precedent exists for this screen — Ravis predates ORPG/RDA entirely. It is specified from the `RCP↔ORPG` contract alone (§6): RDA state-machine state, last status exchange (Msg 2), loopback health (Msg 11/12) and connection uptime, surfaced as part of the System Status & BITE Manager's health picture (§4.4).

## **5\. Technology Stack**

All choices are mature, actively maintained, and installable offline (vendored wheels / npm cache) for the air-gapped target.

| Layer | Choice | Rationale |
| ----- | ----- | ----- |
| Backend language | Python 3.12 | Team preference; soft-real-time workload; rich ecosystem |
| Web framework | FastAPI \+ Uvicorn | First-class async, WebSocket, OpenAPI; pairs with Pydantic |
| Contracts/validation | Pydantic v2 | Typed messages; OpenAPI/JSON-Schema → TS codegen |
| Concurrency | asyncio | Soft-real-time orchestration of control \+ streaming \+ ORPG feed |
| Fieldbus client | pymodbus (Modbus TCP/RTU); Profibus via SBC gateway/cards | SBC bridges fieldbus; server speaks Modbus TCP over the LAN |
| DSP/DRX link | 1 GbE Ethernet; compact binary framing (typed arrays) over TCP/UDP | Outside the FPGA, 1 Gb suffices; the 10GbE high-rate path is internal to the DRX/FPGA |
| ORPG interface | In-house Python implementation of the WSR-88D RDA/RPG ICD 2620002 (asyncio TCP server; `struct`\-based Message 31/1, CTM/MSG headers, Msg 2/6/11/12/13/15; VCP from XML) | Standard, fixed interface to ORPG; RDABackendPy is the reference implementation |
| Numerics | NumPy / SciPy | Moment handling, Level-II encoding, simulator synthesis |
| Archive | NEXRAD Level-II files (primary) \+ SQLite for scan/status/event metadata | Standard volumetric-observation format ORPG already understands; embedded metadata store on a single box |
| Binary transport (MMI) | msgpack / raw typed arrays over WebSocket | Compact moment delivery to the browser |
| Logging | structlog / loguru | Structured logs for the BITE/event history and diagnostics |
| Frontend | Vue 3 \+ TypeScript \+ Vite | Team preference; fast HMR; strong typing |
| State / routing | Pinia \+ Vue Router | Standard, mature Vue 3 stack |
| Styling | Tailwind CSS | Team preference |
| Components | PrimeVue or shadcn-vue (Reka UI) | PrimeVue \= batteries-included; shadcn-vue \= Tailwind-native headless — *decision needed* |
| PPI / RHI render | PixiJS (WebGL) | GPU polar heatmap \+ 256-entry color LUT in shader |
| ASCOPE / plots | uPlot | Extremely fast real-time line/intensity plotting |
| Utilities | VueUse | Composables for sockets, sizing, etc. |
| Testing (backend) | pytest \+ pytest-asyncio | Unit/integration; simulator-driven; RDA-interface contract tests |
| Testing (frontend) | Vitest \+ Playwright | Unit \+ end-to-end on the laptop/CI |
| Packaging/deploy | Docker Compose (offline image bundle) on the server | One-box deploy; thin browser client; PyInstaller is the alternative |
| Dev workflow | AI coding agents \+ spec/test-first | Core to the team's strategy; see §7.2 |

## **6\. Interfaces & Contracts (defined in Phase 0\)**

Four interfaces are designed up front and frozen early, because every workstream depends on them:

* **RCP ↔ MMI** — REST for configuration/commands, WebSocket for live status, BITE and moment streams; typed via Pydantic and mirrored to generated TypeScript.  
* **RCP ↔ DSP/DRX** — the moment subscription/stream format (data types, ray metadata, scan/sweep framing) over a **1 GbE** link. External dependency; agreed with the DSP project and validated by contract tests and the simulated DSP stream.  
* **RCP ↔ HAL** — the abstract device interface (read status, command actuators, sensor model) that both the real adapter and the simulator implement identically.  
* **RCP ↔ ORPG** *(new — migrated from the DSP plan)* — the **fixed WSR-88D RDA/RPG ICD 2620002**: the RCP acts as the RDA. Base data delivered by radial as Message 31 (Message 1 legacy framing where required); CTM/MSG headers; RDA state machine and status (Msg 2); loopback (Msg 11/12); inbound RDA control commands from ORPG (Msg 6); clutter filter/bypass maps (Msg 15/13); VCP definitions. External dependency; agreed with the LAMULA ORPG project and validated by contract tests against a real ORPG build or a CM\_TCP stub.

**Moment vocabulary (canonical):** UZ (uncorrected reflectivity), CZ (corrected reflectivity), V, W, ZDR, ΦDP, KDP, LDR, ρHV; quality indices SQI, CCOR, SIG; raw I, Q — consistent with the DSP and ORPG contracts.

## **7\. Team, Roles & Delivery Model**

### **7.1 Roles**

| \# | Role | Primary ownership |
| ----- | ----- | ----- |
| 1 | Tech Lead / Backend Architect (eng) | Architecture, the four contracts, gateway, RCP core, CI |
| 2 | Backend Engineer (eng) | HAL, the six control routines, parameter-safety guard, scan controller |
| 3 | Backend Engineer — Sim & Data (eng) | Radar simulator, DSP/DRX ingestion, **Level-II archive, ORPG interface / RDA emulation** |
| 4 | Frontend Engineer / Visualization (eng) | Vue MMI, PixiJS/uPlot data views, design system, ORPG-link status view |
| 5 | Product Expert / QA Lead (domain) | Acceptance specs, calibration & pulse/PRF-safety correctness, validation strategy, **RDA/ORPG conformance** |
| 6 | Product Expert / QA (domain) | BITE/fault scenarios, operator-procedure validation, test execution, documentation |

### **7.2 AI-accelerated delivery model**

This team uses coding agents as a core capability, which is what makes the scope feasible in 8 months. The plan assumes:

* **Spec-and-test-first:** the product experts author precise acceptance scenarios; engineers turn them into executable specs (pytest, Playwright, Gherkin-style) before implementation, then agents implement against the tests.  
* **Simulator as deterministic oracle:** scripted simulator scenarios (including faults) give agents and CI a reproducible source of truth.  
* **Generated contracts:** a single Pydantic/OpenAPI source generates TypeScript types, eliminating front/back drift; the `RCP↔ORPG` ICD is captured as typed message structs with conformance tests.  
* **Repository conventions ("skills") and CI gates:** documented conventions keep agent output consistent; CI enforces type checks, tests and contract tests (including the RDA interface) on every change.

## **8\. Delivery Plan**

### **8.1 Cadence & methodology**

Two-week sprints (17 sprints across 34 weeks). Sprint demos to the product experts, who own acceptance. Continuous integration with mandatory type, test and contract-test gates (including the RDA/ORPG interface). A living Stage-2 backlog absorbs out-of-scope requests through lightweight change control.

### **8.2 Phases**

| Phase | Weeks | Focus | Exit milestone |
| ----- | ----- | ----- | ----- |
| 0 — Inception & Architecture | 1–3 | Freeze the four contracts (incl. RCP↔ORPG/ICD 2620002); repo/CI/agent-workflow setup; simulator architecture; design system; spikes: WebGL PPI render \+ Modbus path \+ **a minimal RDA↔ORPG/CM\_TCP handshake** | Architecture & contracts baselined |
| 1 — Foundations & Simulator | 4–10 | HAL interface \+ simulator (HW \+ DRX stream \+ fault injection); gateway skeleton; MMI shell (Control Center, connect, message log); first live data pipe sim→WS→PPI | M1 vertical slice |
| 2 — Control, Safety & Scanning | 11–18 | Six control routines on sim; parameter-safety guard; antenna movement/positioning; manual Scan Worksheet; automated volume-scan scheduler; System Visualization \+ BITE | M2 active control on sim |
| 3 — Data Views, Calibration, Archive & ORPG Feed | 19–27 | Full PPI/RHI/ASCOPE \+ 256-level color management \+ multi-data-type \+ freeze/zoom; DRX/RSP control \+ single-point/TX calibration; **Level-II volumetric-observation archive; complete RDA emulation \+ by-radial Level-II feed to ORPG; state machine, status, loopback, VCP and inbound control commands** | M3 full operator capability \+ ORPG feed on sim |
| 4 — Hardening & Simulator Acceptance | 28–34 | Performance, endurance/soak runs, full fault-injection/BITE coverage, simulator-based acceptance suite, **RDA/ORPG conformance against a real/stubbed ORPG**, offline installer, operator docs, commissioning dry-run plan | M4 simulator acceptance — commissioning-ready |

### **8.3 Milestones & acceptance criteria**

* **M1 — Vertical slice (end of W10).** Simulator emits status \+ a moment stream over the DRX interface; gateway relays it; the browser renders a live PPI and shows subsystem status in passive mode. Proves the end-to-end path and the HAL/contract design.  
* **M2 — Active control on sim (end of W18).** The operator powers up the radar (all six routines against the simulator), positions and moves the antenna, runs a manual scan and a scheduled automated volume scan, sees live System Visualization and BITE/fault messages. The parameter-safety guard rejects damaging PRF×pulse-width combinations and out-of-limit antenna commands.  
* **M3 — Full operator capability \+ ORPG feed on sim (end of W27).** All three data views with color management and multiple data types; single-point and TX calibration workflows; the **volumetric observation archived as Level-II**; the **RDA emulation streams base data by radial to ORPG (or a CM\_TCP stub), exchanges status (Msg 2), loopback (Msg 11/12), VCP and inbound control commands (Msg 6\)**, and ORPG generates products from the feed.  
* **M4 — Simulator acceptance (end of W34, month 8).** The full product-expert-owned acceptance suite passes on the simulator; endurance and fault-injection campaigns pass; the **RDA/ORPG interface passes conformance against a real ORPG build (or validated stub)**; the offline installer deploys cleanly on a clean air-gapped server; operator documentation and a field-commissioning dry-run plan are delivered. System is commissioning-ready.

## **9\. Work Breakdown by Workstream**

* **Architecture & Platform** — contracts (four, incl. ICD 2620002), repo, CI, agent conventions, packaging, observability.  
* **HAL & Simulator** — abstract interface, real adapter (Modbus/Profibus over SBC), simulator (hardware emulation, DSP/DRX moment stream, fault/BITE injection, scriptable scenarios).  
* **Control & Safety** — six control routines, servo/antenna positioning and movement, parameter-safety guard.  
* **Scanning** — interactive scan worksheet, automated volume-scan scheduler, scan-state management.  
* **Data Path** — DSP/DRX ingestion (1 GbE), moment fan-out, **Level-II volumetric-observation archive, ORPG interface / RDA emulation (ICD 2620002\)**.  
* **MMI** — Control Center, System Visualization, Antenna Control, Scan Worksheet UI, DRX/RSP & calibration UIs, PPI/RHI/ASCOPE rendering \+ color management, BITE window, System Information, ORPG-link status.  
* **Quality & Validation** — acceptance specs, test harnesses, **RDA/ORPG conformance**, endurance/fault campaigns, documentation.

## **10\. Quality, Testing & Validation**

* Unit & integration (pytest, Vitest) on every change; contract tests guard the four interfaces.  
* **RDA/ORPG conformance tests** — Level-II encoding, Message 31/1 framing, CTM/MSG headers, state-machine transitions, Msg 2 status, loopback (11/12), inbound control (Msg 6), clutter/bypass maps (15/13) and VCP, exercised against a real ORPG build or a CM\_TCP stub.  
* End-to-end (Playwright) drive the MMI against the simulator-backed stack.  
* Scenario/acceptance suite authored by the product experts — operator procedures, scan sequences, calibration correctness, and a safety matrix for PRF×pulse-width duty limits and antenna limits.  
* Fault-injection / BITE campaigns via the simulator's fault hooks (including ORPG-link loss/recovery).  
* Endurance/soak runs (long unattended scheduled scanning, sustained by-radial ORPG feed) in Phase 4\.  
* Simulator-fidelity register — explicitly catalogues known simulator-vs-real deltas so they convert directly into the commissioning test plan.

## **11\. Risk Register**

| Risk | L | I | Mitigation |
| ----- | ----- | ----- | ----- |
| Simulator fidelity gap (acceptance is sim-only) | Med | High | Product-expert-owned fidelity criteria; broad fault-injection; explicit sim-vs-real delta register feeding a commissioning test plan |
| **100% dependency on external ORPG for product generation** | Med | High | Freeze RCP↔ORPG (ICD 2620002\) in Phase 0; conformance-test against real/stubbed ORPG continuously; RDABackendPy as reference implementation; ORPG-link health surfaced in BITE |
| **RDA-interface conformance (ICD 2620002\) wrong/incomplete** | Med | High | Early Phase-0 handshake spike; message-level conformance suite; validate against a real ORPG build, not only a stub |
| DSP/DRX moment-interface dependency (external project) | Med | High | Freeze RCP↔DSP contract in Phase 0; simulate the DRX stream; contract tests |
| Hardware-interface assumptions wrong at commissioning (deferred) | Med | High | HAL isolation; documented assumptions; commissioning dry-run plan in Phase 4 |
| Klystron/magnetron safety-rule correctness | Low | Critical | Product-expert-owned duty-cycle/limit rules; automated guard tests; hardware interlock as independent backstop |
| **Cross-project reconciliation: DSP plan still claims the ORPG feed** | Med | Med | Update the DSP plan to drop `DSP↔ORPG`; single owner (RCP) for the ICD; shared contract work done once |
| Scope pressure ("all included") in 8 months | Med | Med | Phased milestones; Stage-2 backlog; change control |
| Soft-real-time timing edge cases | Low | Med | Hard timing kept in hardware/DRX; soak testing; backpressure handling on streams |
| Offline/air-gapped packaging friction | Low | Med | Vendored dependencies; offline installer built and tested in Phase 1, not Phase 4 |
| Team ramp on this specific radar | Low | Med | Two embedded product experts; experienced team |

## **12\. Assumptions & Dependencies**

* Full knowledge of and access to the radar hardware interface; proprietary devices already replaced by general-purpose Modbus/Profibus devices on an SBC (out of scope here).  
* The DSP/DRX delivers correct, pre-computed moments **over a 1 GbE link**, and its interface contract is agreed early. The high-rate acquisition path (ADC/DDC/decimation, 10GbE) is internal to the FPGA/DRX.  
* **ORPG is an external system** (the separate LAMULA ORPG project). The system depends 100% on ORPG for product generation; the `RCP↔ORPG` ICD 2620002 contract is agreed and frozen early, and a real or stubbed ORPG is available for in-loop testing.  
* **The DSP plan is updated in parallel** to remove its `DSP↔ORPG` contract and ORPG output encoders; that responsibility now lives in the RCP.  
* Hard real-time (triggering, PRF, pulse integration) is guaranteed by hardware/DRX, not by the Python backend.  
* Hardware interlocks (radiation inhibit, e-stop, limit switches) exist independently; RCP safety responsibility is limited to status checks and parameter validation.  
* Single radar model, single operator, air-gapped private network, no security requirements.  
* Dev/CI environment has package access (or an internal mirror); the deployment target is offline.

## **13\. Definition of Done (Month 8\)**

The system, running on a clean air-gapped server with the simulator behind the HAL, lets a single operator power up the radar, position the antenna, run manual and automated volume scans, view live PPI/RHI/ASCOPE with color management, and perform single-point and TX calibration — with the parameter-safety guard enforcing klystron/magnetron and antenna limits. The **volumetric observation is archived as NEXRAD Level-II**, and the **complete RDA emulation feeds base data by radial to ORPG** (exchanging status, loopback, VCP and inbound control commands per ICD 2620002), so that ORPG generates all products. The product-expert acceptance suite is green, the RDA/ORPG interface passes conformance against a real or stubbed ORPG, endurance and fault-injection campaigns are passed, an offline installer is validated, operator documentation is delivered, and a field-commissioning plan is ready. Real-hardware commissioning begins after month 8 by swapping the HAL's simulator adapter for the real adapter.

---

## **Appendix A — Ravis → LAMULA RCP feature mapping**

| Ravis feature | LAMULA RCP | Stage |
| ----- | ----- | ----- |
| Radar Control Center, message area | Control Center \+ live message/event log | 1 |
| Connect/Login \+ 4-level control modes | Connect \+ passive/active toggle (arbitration dropped) | 1 |
| System Visualization (subsystem status) | System Visualization with live status | 1 |
| Antenna Control (step/servo) | Antenna Control (movement/positioning) | 1 |
| Scan Worksheet | Scan Worksheet (interactive) | 1 |
| — (Rainbow scheduler) | Automated volume-scan scheduler | 1 |
| RSP/DRX Control, calibration | DRX/RSP control \+ single-point/TX calibration | 1 |
| ASCOPE / PPI / RHI \+ color management | Same, WebGL \+ uPlot, 256-level LUT | 1 |
| BITE Message Window \+ history | BITE/fault window with filter \+ history | 1 |
| System Information Window | System Information | 1 |
| — (archive) | Volumetric-observation archive (NEXRAD Level-II) | 1 |
| — (products) | **Feed to ORPG (RDA emulation, ICD 2620002); products generated by the separate LAMULA ORPG** | 1 |
| Sun Position / Sun Track | Deferred | 2 |
| Email messaging | Deferred | 2 |
| Ravis Console (RCL) | Maintenance terminal (if needed) | 2 |
| RX linearity / power monitor / sig-gen / ITSG | Deferred | 2 |
| Geographic overlays / location out of center | Deferred | 2 |
| MDV by-volume to TITAN; NETCDF/HDF5 archive | Deferred | 2 |
| Heterogeneous/multi-radar, multi-operator, remote IoT/RBAC | Deferred | 2 |

