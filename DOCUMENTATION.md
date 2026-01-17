# PyEDA-Sim

## Python-Based Electronic Circuit & MCU Simulator

> A comprehensive schematic capture and simulation environment for designing, wiring, and testing electronic circuits with analog components, digital logic, and microcontroller firmware — all in Python. 

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Design Philosophy](#design-philosophy)
3. [Technology Stack](#technology-stack)
4. [Architecture Overview](#architecture-overview)
5. [Current Implementation Status](#current-implementation-status)
6. [Phase 0:  Foundations & Technical Baseline](#phase-0-foundations--technical-baseline)
7. [Phase 1: Schematic Editor MVP](#phase-1-schematic-editor-mvp)
8. [Phase 2:  Analog Simulation (SPICE Integration)](#phase-2-analog-simulation-spice-integration)
9. [Phase 3: Digital Logic & Sensor Models](#phase-3-digital-logic--sensor-models)
10. [Phase 4: Microcontroller Simulation](#phase-4-microcontroller-simulation)
11. [Phase 5: Real Component Libraries](#phase-5-real-component-libraries)
12. [Data Models & File Formats](#data-models--file-formats)
13. [User Guide](#user-guide)
14. [Development Guidelines](#development-guidelines)

---

## Project Overview

### What Is PyEDA-Sim?

PyEDA-Sim is an **integrated electronic design and simulation environment** built entirely in Python. It provides a unified workspace where users can: 

- **Design circuits visually** using a grid-based schematic editor inspired by EasyEDA
- **Simulate analog behavior** with industry-standard SPICE engines
- **Model digital components** with event-driven logic simulation
- **Run real firmware** on emulated microcontrollers connected to the virtual circuit
- **Use real-world components** with datasheet-accurate specifications

### Target Audience

| User Type | Use Case |
|-----------|----------|
| **Students** | Learn electronics through interactive simulation without physical hardware |
| **Hobbyists** | Prototype Arduino/embedded projects before building |
| **Engineers** | Validate circuit designs and test firmware logic |
| **Educators** | Create interactive demonstrations and lab exercises |

### Project Scope

#### ✅ In Scope

- Grid-based schematic capture (EasyEDA-style interface)
- Analog circuit simulation via SPICE (DC, AC, transient analysis)
- Digital and mixed-signal component simulation
- Microcontroller emulation (Arduino Uno, Teensy, potentially ARM)
- Sensor behavioral models (I2C/SPI accelerometers, temperature sensors, etc.)
- Real component libraries with exact part specifications
- JSON-based project files for easy version control

#### ❌ Out of Scope

- **PCB layout and fabrication** — This is a simulation tool, not a PCB design tool
- **Full Linux emulation** — Raspberry Pi with full OS is not planned
- **High-speed signal integrity analysis** — Focus is on functional behavior
- **3D visualization** — Schematic-only interface

---

## Design Philosophy

PyEDA-Sim is built on five core architectural principles that guide all development decisions:

### 1. Python as the Orchestration Layer

Python handles all high-level logic:  UI rendering, data models, state management, and engine coordination.  Computationally intensive operations (SPICE simulation, MCU execution) are delegated to specialized external engines.

```
┌─────────────────────────────────────────────────────────┐
│                    Python Layer                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │   UI    │  │  Core   │  │ Circuit │  │ Project │   │
│  │ (Qt)    │  │ Models  │  │  Graph  │  │  I/O    │   │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘   │
│       │            │            │            │         │
│       └────────────┴─────┬──────┴────────────┘         │
│                          │                              │
│                   Orchestration                         │
└──────────────────────────┬──────────────────────────────┘
                           │
        ┌──────────────────��──────────────────┐
        ▼                  ▼                  ▼
   ┌─────────┐       ┌─────────┐       ┌─────────┐
   │ ngspice │       │ simavr  │       │  QEMU   │
   │ (Analog)│       │  (AVR)  │       │  (ARM)  │
   └─────────┘       └─────────┘       └─────────┘
```

### 2. Strict Separation of Concerns

Each subsystem operates independently with well-defined interfaces: 

| Subsystem | Responsibility | Location |
|-----------|----------------|----------|
| **UI Layer** | Rendering, user input, visual feedback | `ui/` |
| **Core Models** | Component, Pin, Net data structures | `core/` |
| **Application** | Window management, tool coordination | `app/` |
| **Simulation** | Engine interfaces, result parsing | `simulation/` |

**Key Rule:** UI components never contain circuit logic. Circuit models never contain rendering code.

### 3. Reuse Proven Engines

Rather than reimplementing complex simulation algorithms, PyEDA-Sim integrates battle-tested external engines:

| Domain | Engine | Integration |
|--------|--------|-------------|
| Analog circuits | ngspice | via PySpice Python bindings |
| Digital logic | Custom | Event-driven Python engine |
| AVR microcontrollers | simavr | C library with Python bindings |
| ARM microcontrollers | QEMU | Process-based communication |

### 4. Schematic-First Workflow

The user experience centers on the schematic editor.  All other features (simulation, firmware loading) originate from the schematic view: 

```
User draws schematic
        │
        ▼
┌───────────────────┐
│  Visual Canvas    │ ← Drag components, draw wires, set parameters
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Circuit Model    │ ← Graph of components, pins, and nets
└────────┬──────────┘
         │
    ┌────┴────┬─────────────┐
    ▼         ▼             ▼
 SPICE     Digital       MCU
Netlist   Event Sim    Firmware
```

### 5. Real-World Fidelity

Where possible, simulation uses datasheet-accurate models:

- Component parameters derived from manufacturer specifications
- SPICE models from vendor-provided files
- Exact part numbers, not just generic "resistor" or "capacitor"
- Firmware runs unmodified (same binary as real hardware)

---

## Technology Stack

All technology choices are **locked** after Phase 0 to prevent mid-project rewrites:

| Layer | Technology | Version | Rationale |
|-------|------------|---------|-----------|
| **Language** | Python | 3.11+ | Modern typing, pattern matching, performance |
| **GUI Framework** | PySide6 | 6.x | Official Qt bindings, LGPL license |
| **Graphics System** | QGraphicsView | — | Optimized for interactive 2D graphics with zoom/pan |
| **Analog Simulation** | ngspice via PySpice | — | Industry-standard SPICE, Python-native interface |
| **Digital Simulation** | Custom event-driven | — | Lightweight, integrated with circuit model |
| **MCU Emulation (AVR)** | simavr | — | Cycle-accurate AVR emulation |
| **MCU Emulation (ARM)** | QEMU | — | Full system emulation (future phase) |
| **Data Serialization** | JSON | — | Human-readable, version-control friendly |
| **Testing** | unittest | — | Standard library, no external dependencies |

---

## Architecture Overview

### Project Structure

```
eda-simulator/
├── main.py                      # Application entry point
│
├── app/                         # Application layer (window, tools, panels)
│   ├── __init__. py
│   ├── app_window.py            # Main window, coordinates all panels
│   ├── component_palette.py     # Left/right panel for tool/component selection
│   ├── parameter_dialog.py      # Modal dialog for editing component parameters
│   └── parameter_inspector.py   # Side panel showing selected component properties
│
├── core/                        # Domain models (circuit logic)
│   ├── __init__.py
│   ├── component.py             # Component class with pins and parameters
│   ├── pin.py                   # Pin class with direction and net reference
│   └── net.py                   # Net class connecting multiple pins
│
├── ui/                          # Visual/graphics layer (Qt items)
│   ├── __init__. py
│   ├── schematic_view.py        # Main canvas (QGraphicsView subclass)
│   ├── grid. py                  # Background grid rendering
│   ├── component_item.py        # Visual representation of components
│   ├── pin_item.py              # Visual representation of pins
│   ├── wire_segment_item.py     # Wire segment graphics with selection/hover
│   ├── junction_item.py         # Junction dots at wire intersections
│   └── undo_commands.py         # Command pattern for undo/redo
│
├── simulation/                  # Simulation engine interfaces (future)
│   └── __init__.py
│
├── tests/                       # Unit tests
│   ├── __init__. py
│   └── test_circuit_model.py    # Tests for core data models
│
└── . gitignore
```

### Layer Responsibilities

```
┌─────────────────────────────────────────────────────────────────┐
│                        app/ (Application)                       │
│  • Window lifecycle management                                  │
│  • Tool state (select mode vs. wire mode)                       │
│  • Panel coordination (palette ↔ inspector ↔ canvas)            │
│  • Keyboard shortcuts (Ctrl+S, Ctrl+Z, etc.)                    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        ui/ (Presentation)                        │
│  • QGraphicsView/Scene management                               │
│  • Visual item rendering (components, wires, junctions)         │
│  • Mouse/keyboard event handling                                │
│  • Snap-to-grid logic                                           │
│  • Undo/redo command execution                                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        core/ (Domain)                            │
│  • Component, Pin, Net data structures                          │
│  • Parameter storage and validation                             │
│  • Serialization (to_dict)                                      │
│  • No Qt dependencies — pure Python                             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    simulation/ (Engine Adapters)                 │
│  • Netlist generation                                           │
│  • Engine process management                                    │
│  • Result parsing                                               │
│  • Waveform data structures                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Current Implementation Status

### Summary

| Phase | Name | Status | Completion |
|-------|------|--------|------------|
| 0 | Foundations & Technical Baseline | ✅ Complete | 100% |
| 1 | Schematic Editor MVP | ✅ Complete | 100% |
| 2 | Analog Simulation (SPICE) | 🚧 In Progress | 0% |
| 3 | Digital Logic & Sensors | ⏳ Not Started | 0% |
| 4 | Microcontroller Simulation | ⏳ Not Started | 0% |
| 5 | Real Component Libraries | ⏳ Not Started | 0% |

### Detailed Phase 2 Progress

| Feature | Status | Implementation Details |
|---------|--------|------------------------|
| Netlist generator | 🔲 Pending | `simulation/netlist_generator.py` — Convert circuit model to SPICE netlist |
| SPICE runner | 🔲 Pending | `simulation/spice_runner.py` — PySpice/ngspice execution manager |
| Waveform data structures | 🔲 Pending | `simulation/waveform_data.py` — Simulation result containers |
| Waveform viewer | 🔲 Pending | `ui/waveform_viewer.py` — PyQtGraph-based plot widget |
| Simulate button | 🔲 Pending | Toolbar button to trigger simulation |
| Analysis type selector | 🔲 Pending | Dropdown for Transient, DC, AC analysis |
| Probe tool | 🔲 Pending | Select nets to plot in waveform viewer |
| Ground component | 🔲 Pending | Add ground symbol to component palette |
| Voltage source component | 🔲 Pending | DC and AC voltage sources |
| Current source component | 🔲 Pending | DC current source |
| Operating point analysis | 🔲 Pending | `.op` — DC voltages at all nodes |
| DC sweep analysis | 🔲 Pending | `.dc` — Sweep source, measure response |
| AC analysis | 🔲 Pending | `.ac` — Frequency response |
| Transient analysis | 🔲 Pending | `.tran` — Time-domain simulation |
| Error detection | 🔲 Pending | Missing ground, floating nodes, invalid values |
| Error reporting UI | 🔲 Pending | Clear error messages in status bar or dialog |

### Phase 2 Definition of Done

- [ ] Can simulate a simple RC low-pass filter
- [ ] Transient analysis matches hand-calculated time constant
- [ ] Waveform viewer shows voltage vs.  time
- [ ] Changing R or C value and re-simulating shows different curve
- [ ] Error messages displayed for missing ground
- [ ] Simulation results match ngspice command-line output

---

## Phase 0:  Foundations & Technical Baseline

### Purpose

Establish the technical foundation for the entire project.  Decisions made in this phase are **locked** to prevent destabilizing rewrites in later phases.

### Goals

| Goal | Description | Deliverable |
|------|-------------|-------------|
| **Validate GUI framework** | Confirm PySide6/Qt can handle schematic graphics | Hello-world Qt window |
| **Prove graphics system** | Test QGraphicsView for zoom, pan, grid rendering | Zoomable/pannable grid prototype |
| **Define circuit model** | Design graph-based data structures for netlists | `Component`, `Pin`, `Net` classes |
| **Establish project structure** | Create modular directory layout | Folder structure with `__init__.py` files |
| **Document architecture** | Record design decisions and rationale | Architecture README |

### Non-Goals

- ❌ No complete UI — only proof-of-concept windows
- ❌ No simulation — only data structures
- ❌ No component libraries — only hardcoded test components
- ❌ No microcontroller support

### Technical Decisions Locked

| Decision | Choice | Alternatives Rejected |
|----------|--------|----------------------|
| GUI framework | PySide6 (Qt) | Tkinter (limited graphics), PyGame (game-focused), Kivy (mobile-focused) |
| Graphics widget | QGraphicsView/Scene | Custom OpenGL (overkill), Matplotlib (not interactive) |
| Circuit data model | Graph-based (Component→Pin→Net) | Flat list, hierarchical XML |
| Analog simulation engine | ngspice via PySpice | LTspice (Windows-only), custom solver (too complex) |
| Project file format | JSON | XML (verbose), binary (not human-readable) |

### Deliverables Completed

1. **Qt Application Window**
   - `main.py` creates `QApplication` and shows `AppWindow`
   - Window resizes, closes, and handles events correctly

2. **QGraphicsView Prototype**
   - `SchematicView` extends `QGraphicsView`
   - Mouse wheel zooms (centered on cursor)
   - Middle-click or Alt+drag pans the view
   - Scene rect set to 10,000×10,000 pixels

3. **Background Grid**
   - `GridItem` renders infinite grid at 10px spacing
   - Grid scales appropriately during zoom

4. **Core Data Model**
   ```python
   # core/pin.py
   class PinDirection(Enum):
       INPUT = auto()
       OUTPUT = auto()
       BIDIRECTIONAL = auto()

   class Pin: 
       name: str                    # "1", "2", "A", "B"
       direction: PinDirection
       net: Optional[Net]           # Which net this pin connects to
       rel_x: float                 # Relative X position on component
       rel_y: float                 # Relative Y position on component
   ```

   ```python
   # core/net.py
   class Net: 
       name: str                    # "NET1", "VCC", "GND"
       pins:  List[Pin]              # All pins connected to this net

       def connect(pin: Pin):       # Adds pin and sets pin.net = self
   ```

   ```python
   # core/component.py
   class Component: 
       ref: str                     # "R1", "C2", "U3"
       type: str                    # "resistor", "capacitor", "led"
       pins: List[Pin]              # Connection points
       parameters: Dict[str, Any]   # {"resistance": 1000, "type": "resistor"}

       DEFAULT_PARAMS = {           # Per-type defaults
           "resistor": {"resistance": 1000},
           "capacitor": {"capacitance": 1},
           ... 
       }
   ```

5. **Project Repository Structure**
   - Modular layout with `app/`, `core/`, `ui/`, `simulation/`, `tests/`
   - Each package has `__init__.py` with exports
   - Clean separation between layers

### Definition of Done ✅

- [x] Can open a Qt window with dark background
- [x] Can see a scalable grid that zooms and pans
- [x] Can instantiate `Component`, `Pin`, `Net` objects in memory
- [x] Can connect pins to nets programmatically
- [x] Unit tests pass for circuit model (`test_circuit_model.py`)
- [x] No coupling between UI and simulation layers

---

## Phase 1: Schematic Editor MVP

### Purpose

Create a fully functional schematic editor that allows users to design circuits visually.  This phase focuses entirely on the **capture** workflow — no simulation yet.

### Goals

| Goal | Description | Success Criteria |
|------|-------------|------------------|
| **Component placement** | Drag components from palette to canvas | Components appear at cursor, snap to grid |
| **Component manipulation** | Move, rotate, select components | Rubber-band selection, R key rotates |
| **Wire routing** | Draw orthogonal wires between pins | Wires snap to pins and grid |
| **Net management** | Track which wires belong to which net | Clicking connected wires highlights entire net |
| **Property editing** | View and modify component parameters | Inspector panel shows selected component |
| **Undo/redo** | Revert and replay all editing actions | Ctrl+Z/Ctrl+Y work for all operations |
| **File I/O** | Save and load schematics | JSON format preserves exact layout |

### Non-Goals

- ❌ No simulation — editor only
- ❌ No PCB view — schematic only
- ❌ No auto-routing — manual wiring only
- ❌ No real component libraries — only generic types

### UI Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           AppWindow                                  │
├─────────────────────────────────────────┬───────────────────────────┤
│                                         │                           │
│                                         │    ComponentPalette       │
│                                         │    ┌─────────────────┐    │
│                                         │    │ Tools           │    │
│           SchematicView                 │    │ [Select/Move]   │    │
│           (QGraphicsView)               │    │ [Wire Tool]     │    │
│                                         │    ├─────────────────┤    │
│     ┌─────────────────────────────┐     │    │ Components      │    │
│     │                             │     │    │ [Resistor]      │    │
│     │   ┌───┐      ┌───┐         │     │    │ [Capacitor]     │    │
│     │   │R1 │──────│C1 │         │     │    │ [LED]           │    │
│     │   └───┘      └───┘         │     │    │ [Inductor]      │    │
│     │                             │     │    └─────────────────┘    │
│     └─────────────────────────────┘     │                           │
│                                         │    ParameterInspector     │
│                                         │    ┌─────────────────┐    │
│                                         │    │ Reference:  R1   │    │
│                                         │    │ Type: Resistor  │    │
│                                         │    │ Resistance: [___]│   │
│                                         │    └─────────────────┘    │
└─────────────────────────────────────────┴───────────────────────────┘
```

### Component System

#### Visual Component (`ui/component_item.py`)

```python
class ComponentItem(QGraphicsRectItem):
    GRID_SIZE = 50                        # Component snaps to 50px grid

    model: Component                       # Reference to core model
    ref: str                               # Display reference (e.g., "R1")
    label: QGraphicsTextItem               # Text above component
    pin_items: List[PinItem]               # Visual pin representations

    # Visual properties
    - Yellow fill (#ffeeaa)
    - Black border
    - Label shows ref + primary value (e.g., "R1 1000Ω")

    # Behavior
    - Selectable, movable, focusable
    - Snaps to 50px grid during movement
    - Rotation around center point
    - Press 'R' to rotate 90°
```

#### Logical Component (`core/component.py`)

```python
class Component:
    DEFAULT_PARAMS = {
        "resistor":    {"resistance": 1000, "type": "resistor"},
        "capacitor":  {"capacitance": 1, "type": "capacitor"},
        "led":        {"voltage_drop": 2. 0, "type":  "led"},
        "inductor":   {"inductance": 100, "type": "inductor"},
        "generic":    {"type": "generic"}
    }

    # Auto-generates 2 pins if none provided: 
    # Pin 1: Left edge (x=0, y=25)    - INPUT
    # Pin 2: Right edge (x=100, y=25) - OUTPUT
```

### Wire Routing System

#### Wire Modes

| Mode | Trigger | Cursor | Behavior |
|------|---------|--------|----------|
| **Select** | Click "Select/Move" button | Arrow | Drag to move components |
| **Wire** | Click "Wire Tool" button | Crosshair | Click-to-click wire drawing |

#### Wire Drawing Flow

```
1. User clicks "Wire Tool" button
   └─► SchematicView.mode = "wire"
       └─► Cursor changes to crosshair

2. User clicks on canvas (first click)
   └─► Snap click position to nearest pin or 10px grid
   └─► Create preview wire (dashed line)
   └─► Store wire_start_pos

3. User moves mouse
   └─► Update preview wire endpoint in real-time
   └─► Endpoint snaps to pins or grid

4. User clicks again (second click)
   └─► Check if endpoint is on existing wire → split wire
   └─► Create permanent WireSegmentItem
   └─► Register wire in net tracking
   └─► Update junction dots
   └─► Move wire_start_pos to current endpoint
   └─► Continue drawing next segment

5. User presses Escape
   └─► Remove preview wire
   └─► Exit wire drawing mode
```

#### Net Tracking

```python
# SchematicView maintains these data structures: 

point_to_net: Dict[Tuple[float, float], int]
# Maps every wire endpoint coordinate to its net ID
# Example: {(100, 200): 1, (200, 200): 1, (300, 300): 2}

net_to_wires: Dict[int, List[WireSegmentItem]]
# Maps net ID to all wire segments in that net
# Example: {1: [wire1, wire2, wire3], 2: [wire4]}

next_net_id:  int
# Counter for assigning new net IDs (starts at 1)
```

#### Net Merging

When a new wire connects two existing nets: 

```
Before:            After:
NET1: A──B        NET1: A──B──C──D
NET2: C──D        (NET2 absorbed into NET1)

Algorithm:
1. Detect net_id of both endpoints
2. If different: merge all wires from net2 into net1
3. Update point_to_net for all affected points
```

### Junction System

Junctions are visual dots that appear at wire endpoints: 

```python
class JunctionItem(QGraphicsEllipseItem):
    # 10px diameter black dot
    # Centered on wire endpoint coordinate
    # Z-order above wires (setZValue(5))
    # Draggable — connected wires stretch
```

#### Junction Cleanup

After any wire operation, `cleanup_junctions()` runs:

```python
def cleanup_junctions():
    1. Remove all existing junction items
    2. Collect all unique wire endpoint coordinates
    3. Create exactly one JunctionItem per unique coordinate
```

### Undo/Redo System

PyEDA-Sim implements a custom `UndoStack` following the Command pattern:

```python
class UndoStack:
    stack: List[Command]     # All commands
    index: int               # Points to last executed command

    push(command):           # Truncate future, append, execute redo()
    undo():                  # Execute stack[index]. undo(), decrement index
    redo():                  # Increment index, execute stack[index].redo()
```

#### Implemented Commands

| Command | Trigger | Undo | Redo |
|---------|---------|------|------|
| `MoveComponentCommand` | Drag component | Move to old position | Move to new position |
| `RotateComponentCommand` | Press 'R' key | Set old rotation | Set new rotation |
| `CreateWireCommand` | Complete wire segment | Remove from scene | Add to scene |
| `MoveJunctionCommand` | Drag junction | Move junction + stretch wires back | Move junction + stretch wires |
| `ParameterChangeCommand` | Edit in inspector | Restore old value | Apply new value |
| `DeleteItemsCommand` | Delete key (future) | Restore all items | Remove all items |

### File Format

Schematics are saved as JSON with version compatibility in mind:

```json
{
  "version": "0.1",
  "components":  [
    {
      "ref": "R1",
      "comp_type": "resistor",
      "x": 100,
      "y": 200,
      "rotation": 0,
      "parameters": {
        "resistance": 1000,
        "type":  "resistor"
      }
    },
    {
      "ref": "C1",
      "comp_type": "capacitor",
      "x": 250,
      "y": 200,
      "rotation": 90,
      "parameters": {
        "capacitance": 10,
        "type": "capacitor"
      }
    }
  ],
  "wires": [
    {
      "x1": 200,
      "y1": 225,
      "x2": 250,
      "y2": 225,
      "net_id": 1
    }
  ]
}
```

### Remaining Work

| Feature | Priority | Effort | Notes |
|---------|----------|--------|-------|
| Wire color customization | Medium | Low | Add color property to `WireSegmentItem` |
| Component flipping | Medium | Low | Mirror along X or Y axis |
| Copy/paste | Medium | Medium | Serialize selection, offset on paste |
| Multi-segment wire preview | Low | Medium | Show complete path before committing |
| Wire deletion | High | Low | Delete key removes selected wires |
| Component deletion | High | Low | Delete key removes selected components |

### Definition of Done

- [x] Can place resistors, capacitors, LEDs, inductors on canvas
- [x] Components snap to 50px grid
- [x] Can draw wires that snap to component pins
- [x] Wires are orthogonal (horizontal/vertical only)
- [x] Junction dots appear at all wire endpoints
- [x] Can drag junctions and connected wires stretch
- [x] Hovering over a wire highlights the entire net
- [x] Can edit component parameters via inspector
- [x] All actions support undo/redo
- [x] Can save schematic to JSON file
- [x] Can load schematic from JSON file
- [x] Reloading preserves exact layout and net connectivity
- [ ] Can delete components and wires
- [ ] Can customize wire colors

---

## Phase 2: Analog Simulation (SPICE Integration)

### Purpose

Transform the static schematic into a functional analog circuit simulator by integrating SPICE (via ngspice/PySpice).

### Goals

| Goal | Description | Success Criteria |
|------|-------------|------------------|
| **Netlist generation** | Convert schematic → SPICE netlist | Valid netlist for simple RC circuits |
| **Simulation execution** | Run DC, AC, and transient analysis | ngspice returns valid results |
| **Waveform display** | Plot voltage/current over time | Interactive waveform viewer |
| **Error handling** | Report SPICE errors clearly | Floating nodes, missing ground identified |

### Non-Goals

- ❌ No digital logic — pure analog only
- ❌ No microcontrollers — circuit primitives only
- ❌ No complex IC models — basic RLC and sources only

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SchematicView                                │
│                    (Circuit Model)                              │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│               SPICE Netlist Generator                            │
│                                                                  │
│   Input:  List of Components + Net connectivity                 │
│   Output:  SPICE-format text file                                │
│                                                                  │
│   Example output:                                                │
│   * PyEDA-Sim Generated Netlist                                  │
│   R1 net1 net2 1k                                                │
│   C1 net2 0 10u                                                  │
│   V1 net1 0 DC 5                                                 │
│   . tran 1ms 100ms                                                │
│   .end                                                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PySpice Interface                             │
│                                                                  │
│   - Creates ngspice simulator instance                          │
│   - Loads netlist                                                │
│   - Runs simulation                                              │
│   - Returns waveform data                                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Waveform Viewer                                │
│                                                                  │
│   - Time-domain plots (transient analysis)                      │
│   - Frequency-domain plots (AC analysis)                        │
│   - Cursor for reading values                                   │
│   - Multiple traces on same axes                                │
└─────────────────────────────────────────────────────────────────┘
```

### Supported Components (Phase 2)

| Component | SPICE Element | Example |
|-----------|---------------|---------|
| Resistor | R | `R1 net1 net2 1k` |
| Capacitor | C | `C1 net1 net2 10u` |
| Inductor | L | `L1 net1 net2 100m` |
| Voltage Source (DC) | V | `V1 net1 0 DC 5` |
| Voltage Source (AC) | V | `V1 net1 0 AC 1 SIN(0 5 1k)` |
| Current Source | I | `I1 net1 net2 1m` |
| Ground | — | Net name `0` or `GND` |

### Analysis Types

| Type | Command | Description |
|------|---------|-------------|
| **Operating Point** | `.op` | DC voltages at all nodes |
| **DC Sweep** | `.dc V1 0 10 0.1` | Sweep source, measure response |
| **AC Analysis** | `.ac dec 10 1 1Meg` | Frequency response |
| **Transient** | `.tran 1us 10ms` | Time-domain simulation |

### UI Integration

```
┌─────────────────────────────────────────────────────────────────┐
│  [Simulate ▼]  Analysis:  [Transient ▼]  Stop:  [10ms]  Step: [1us]│
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                    Schematic View                                │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                    Waveform Viewer                               │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │     ^                                                     │  │
│   │   5V│    ────────────────                                │  │
│   │     │   /                                                 │  │
│   │     │  /                                                  │  │
│   │   0V│─/────────────────────────────────────────────► t   │  │
│   │     0ms              5ms               10ms              │  │
│   └──────────────────────────────────────────────────────────┘  │
│   Traces:  [x] V(net1)  [x] V(net2)  [ ] I(R1)                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Error Detection

| Error | Detection | User Message |
|-------|-----------|--------------|
| No ground | No net named `0` or `GND` | "Circuit has no ground reference.  Add a ground symbol." |
| Floating node | ngspice warning | "Node 'netX' is not connected to ground through any DC path." |
| Missing simulation command | No `.tran` / `.ac` / `.dc` | "Select an analysis type before simulating." |
| Invalid component value | Parse error | "Invalid resistance value for R1: 'abc'" |

### Deliverables

- [ ] `simulation/netlist_generator.py` — Converts circuit model to SPICE netlist
- [ ] `simulation/spice_runner.py` — Manages PySpice/ngspice execution
- [ ] `simulation/waveform_data.py` — Data structures for simulation results
- [ ] `ui/waveform_viewer. py` — PyQtGraph-based plot widget
- [ ] "Simulate" button in toolbar
- [ ] Analysis type selector (Transient, DC, AC)
- [ ] Probe tool for selecting nets to plot

### Definition of Done

- [ ] Can simulate a simple RC low-pass filter
- [ ] Transient analysis matches hand-calculated time constant
- [ ] Waveform viewer shows voltage vs.  time
- [ ] Changing R or C value and re-simulating shows different curve
- [ ] Error messages displayed for missing ground
- [ ] Simulation results match ngspice command-line output

---

## Phase 3: Digital Logic & Sensor Models

### Purpose

Extend simulation capabilities to include digital components and virtual sensors, enabling mixed-signal simulation. 

### Goals

| Goal | Description | Success Criteria |
|------|-------------|------------------|
| **Digital pins** | Model HIGH/LOW/Z states | Logic gates produce correct outputs |
| **Event simulation** | Propagate state changes | Clock edge triggers flip-flop |
| **Logic thresholds** | Convert analog ↔ digital | ADC reads voltage as digital value |
| **Sensor models** | Virtual I2C/SPI devices | Read accelerometer value from register |

### Non-Goals

- ❌ No real firmware execution — behavior models only
- ❌ No MCU instruction emulation — only pin-level interface
- ❌ No high-speed timing — event-based, not cycle-accurate

### Digital Signal Model

```python
class DigitalState(Enum):
    LOW = 0       # 0V (below threshold)
    HIGH = 1      # VCC (above threshold)
    Z = 2         # High impedance (tri-state)
    X = 3         # Unknown/undefined

class DigitalPin:
    state:  DigitalState
    threshold_low: float   # Below this = LOW (default 0.8V)
    threshold_high: float  # Above this = HIGH (default 2.0V)
    pull:  Optional[str]    # "up", "down", or None
```

### Event-Driven Simulation

```python
class Event:
    time: float            # Simulation time in seconds
    target:  DigitalPin     # Which pin changes
    new_state: DigitalState

class EventQueue:
    events:  PriorityQueue[Event]  # Sorted by time

    def schedule(event: Event): ...
    def process_next(): ...       # Update pin, schedule dependent events
```

### Supported Digital Components (Phase 3)

| Component | Behavior |
|-----------|----------|
| Logic Gates | AND, OR, NOT, NAND, NOR, XOR — combinational logic |
| Buffer | Delay element, signal conditioning |
| Flip-Flop | D flip-flop, edge-triggered |
| Counter | Binary counter with clock input |
| Shift Register | Serial-in, parallel-out |
| MUX/DEMUX | Input selection |

### Sensor Model Architecture

```python
class Sensor(ABC):
    interface:  Literal["I2C", "SPI"]
    address: int                          # I2C address or SPI CS
    registers: Dict[int, int]             # Register map
    
    @abstractmethod
    def update(self, dt: float): ...      # Called each simulation step
    
    @abstractmethod
    def read_register(self, addr: int) -> int: ...
    
    @abstractmethod
    def write_register(self, addr: int, value: int): ...
```

### Example Sensors

| Sensor | Interface | Registers | Output |
|--------|-----------|-----------|--------|
| Push Button | GPIO | — | HIGH when pressed |
| Accelerometer | I2C | 0x32-0x37 (X,Y,Z) | ±2g range, 10-bit |
| Temperature | I2C | 0x00-0x01 | 12-bit, 0.0625°C/LSB |
| Barometer | SPI | 0xF7-0xFC | Pressure + temp |

### Mixed-Signal Interface

```
Analog Domain                   Digital Domain
     │                               │
     │    ┌─────────────────┐        │
     ├───►│  Comparator/ADC │────────┤
     │    └─────────────────┘        │
     │                               │
     │    ┌─────────────────┐        │
     ◄────│    DAC/Driver   │◄───────┤
     │    └─────────────────┘        │
     │                               │
     
Analog voltages converted to digital states at threshold boundaries
Digital states drive analog sources (0V or VCC)
```

### Deliverables

- [ ] `core/digital_pin.py` — Digital state model
- [ ] `simulation/event_queue.py` — Event-driven simulation engine
- [ ] `simulation/logic_gates.py` — Built-in gate models
- [ ] `simulation/sensors/` — Sensor behavioral models
- [ ] `simulation/i2c_bus.py` — I2C bus simulation
- [ ] `simulation/spi_bus.py` — SPI bus simulation
- [ ] Digital component library in palette
- [ ] Sensor configuration dialog

### Definition of Done

- [ ] AND gate produces correct output for all input combinations
- [ ] D flip-flop captures input on rising clock edge
- [ ] Virtual accelerometer returns X,Y,Z values via I2C read
- [ ] Analog voltage crossing threshold triggers digital event
- [ ] Mixed circuit (analog + digital) simulates correctly

---

## Phase 4: Microcontroller Simulation

### Purpose

Enable users to run real, compiled firmware on simulated microcontrollers connected to the circuit.

### Goals

| Goal | Description | Success Criteria |
|------|-------------|------------------|
| **AVR emulation** | Run Arduino sketches | Blink LED in simulation |
| **GPIO mapping** | Connect MCU pins to circuit nets | digitalWrite() changes net voltage |
| **Firmware loading** | Upload HEX/ELF files | Load compiled Arduino sketch |
| **UART console** | Display serial output | See Serial. println() in terminal |
| **Peripheral simulation** | ADC, PWM, timers | analogRead() returns circuit voltage |

### Non-Goals

- ❌ Full Raspberry Pi with Linux — only bare-metal MCUs
- ❌ Debugging/step-through — run-only mode
- ❌ High-speed USB, Ethernet — low-speed peripherals only

### Supported MCUs (Phase 4)

| MCU | Emulator | Boards |
|-----|----------|--------|
| ATmega328P | simavr | Arduino Uno, Nano |
| ATmega2560 | simavr | Arduino Mega |
| ATmega32U4 | simavr | Arduino Leonardo |

(Future: ARM Cortex-M via QEMU)

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      User Workflow                               │
│                                                                  │
│   1. Draw schematic with MCU component                          │
│   2. Load compiled . hex file                                    │
│   3. Map MCU pins to circuit nets                               │
│   4. Click "Run Firmware"                                       │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MCU Simulation Manager                        │
│                                                                  │
│   - Spawns simavr process                                       │
│   - Loads firmware binary                                       │
│   - Provides GPIO callback interface                            │
│   - Handles UART I/O                                            │
└───────────────────────────────┬─────────────────────────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
         ┌─────────┐      ┌─────────┐      ┌─────────┐
         │  GPIO   │      │   ADC   │      │  UART   │
         │ Bridge  │      │ Bridge  │      │ Bridge  │
         └────┬────┘      └────┬────┘      └────┬────┘
              │                │                │
              ▼                ▼                ▼
         ┌───────────────────────────────────────────┐
         │              Circuit Model                 │
         │         (Voltages on nets)                │
         └───────────────────────────────────────────┘
```

### Pin Mapping UI

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCU Pin Configuration                         │
├────────────────────────────────┬────────────────────────────────┤
│  MCU Pin      │  Direction   │  Connected Net                  │
├────────────────────────────────┼────────────────────────────────┤
│  D2 (PD2)     │  OUTPUT      │  [NET_LED1        ▼]            │
│  D3 (PD3)     │  INPUT       │  [NET_BUTTON1     ▼]            │
│  A0 (PC0)     │  ANALOG IN   │  [NET_SENSOR1     ▼]            │
│  TX (PD1)     │  UART TX     │  (Console)                      │
│  RX (PD0)     │  UART RX     │  (Console)                      │
├────────────────────────────────┴────────────────────────────────┤
│                    [Load Firmware]  [Start]  [Stop]              │
└─────────────────────────────────────────────────────────────────┘
```

### Serial Monitor

```
┌─────────────────────────────────────────────────────────────────┐
│  Serial Monitor                              [Clear] [Autoscroll]│
├─────────────────────────────────────────────────────────────────┤
│  > Hello from Arduino!                                            │
│  > LED ON                                                        │
│  > Button pressed!                                                │
│  > Sensor value: 512                                             │
│  > LED OFF                                                       │
│  >                                                               │
├─────────────────────────────────────────────────────────────────┤
│  Send:  [____________________________] [Send]  Baud: [9600 ▼]    │
└─────────────────────────────────────────────────────────────────┘
```

### Deliverables

- [ ] `simulation/mcu/avr_runner.py` — simavr process management
- [ ] `simulation/mcu/gpio_bridge.py` — MCU↔circuit GPIO interface
- [ ] `simulation/mcu/adc_bridge.py` — Analog input sampling
- [ ] `simulation/mcu/uart_bridge.py` — Serial communication
- [ ] `ui/mcu_config_dialog.py` — Pin mapping interface
- [ ] `ui/serial_monitor.py` — UART console widget
- [ ] Arduino Uno component in palette
- [ ] Firmware loader (HEX file selection)

### Definition of Done

- [ ] Can load Arduino blink sketch onto simulated Uno
- [ ] GPIO output changes LED component state in schematic
- [ ] GPIO input reads button component state
- [ ] analogRead() returns proportional value for circuit voltage
- [ ] Serial. println() appears in serial monitor
- [ ] Can send text to simulated Serial. read()

---

## Phase 5: Real Component Libraries

### Purpose

Replace generic component placeholders with real-world parts that have accurate electrical models.

### Goals

| Goal | Description | Success Criteria |
|------|-------------|------------------|
| **KiCad import** | Load symbols from KiCad libraries | Symbol renders correctly |
| **SPICE linking** | Attach vendor SPICE models | Op-amp simulates correctly |
| **Part browser** | Search and filter components | Find "LM358" by name |
| **User-defined** | Create custom component packages | Import new part for project |

### Non-Goals

- ❌ Footprints/PCB symbols — schematic symbols only
- ❌ Real-time parametric search — local database only
- ❌ Automatic SPICE model download — manual addition

### Component Package Structure

```
components/
├── library_index.json         # Master index of all libraries
│
├── generic/                   # Built-in generic components
│   ├── resistor/
│   │   ├── symbol.svg
│   │   ├── model.spice
│   │   └── metadata.yaml
│   ├── capacitor/
│   └── ... 
│
├── manufacturer/              # Real-world parts
│   ├── texas_instruments/
│   │   ├── lm358/
│   │   │   ├── symbol. svg
│   │   │   ├── model.spice    # From TI website
│   │   │   └── metadata.yaml
│   │   └── ... 
│   ├── microchip/
│   └── ... 
│
└── user/                      # User-created parts
    └── custom_sensor/
        ├── symbol.svg
        ├── metadata.yaml
        └── behavior.py        # Custom behavioral model
```

### Metadata Format

```yaml
# metadata.yaml
name: LM358
description:  Dual Operational Amplifier
manufacturer: Texas Instruments
part_number: LM358N
datasheet: https://www.ti.com/lit/ds/symlink/lm358.pdf

category:  Amplifier
subcategory: Op-Amp

pins:
  - name: "1OUT"
    number: 1
    type: output
  - name: "1IN-"
    number: 2
    type:  input
  - name: "1IN+"
    number:  3
    type: input
  - name: "VCC"
    number: 8
    type: power
  - name:  "GND"
    number: 4
    type: ground
  # ... etc

spice_model: model.spice
spice_subcircuit: LM358

parameters:
  - name: supply_voltage
    default: 5
    unit: V
    min: 3
    max: 32
```

### Part Browser UI

```
┌─────────────────────────────────────────────────────────────────┐
│  Component Browser                                               │
├──────────────┬──────────────────────────────────────────────────┤
│ Categories   │  Search:  [lm358___________] [🔍]                  │
│              │                                                   │
│ ▼ Passives   │  ┌────────────────────────────────────────────┐  │
│   Resistors  │  │ [Symbol]  LM358                             │  │
│   Capacitors │  │           Dual Op-Amp                       │  │
│   Inductors  │  │           Texas Instruments                 │  │
│              │  │           VCC:  3-32V                        │  │
│ ▼ Active     │  │           [Add to Schematic]                │  │
│   Diodes     │  ├────────────────────────────────────────────┤  │
│   Transistors│  │ [Symbol]  LM324                             │  │
│   ▶ Op-Amps  │  │           Quad Op-Amp                       │  │
│   ICs        │  │           ...                                │  │
│              │  └────────────────────────────────────────────┘  │
│ ▼ Sensors    │                                                   │
│ ▼ MCUs       │                                                   │
└──────────────┴──────────────────────────────────────────────────┘
```

### Deliverables

- [ ] `core/component_library.py` — Library loading and indexing
- [ ] `core/kicad_importer.py` — KiCad symbol parser
- [ ] `core/spice_model_linker.py` — Attach SPICE subcircuits
- [ ] `ui/part_browser.py` — Searchable component browser
- [ ] `ui/component_creator.py` — User-defined part wizard
- [ ] Default library with common parts
- [ ] Documentation for adding new parts

### Definition of Done

- [ ] Can browse built-in component library
- [ ] Can search for parts by name and category
- [ ] Can import KiCad symbol file
- [ ] Imported symbol renders correctly on canvas
- [ ] Can attach SPICE model to component
- [ ] Simulation uses attached SPICE model
- [ ] Can create and save user-defined component

---

## Data Models & File Formats

### Core Data Model (UML)

```
┌─────────────────────┐         ┌─────────────────────┐
│      Component      │         │        Net          │
├─────────────────────┤         ├─────────────────────┤
│ ref: str            │         │ name: str           │
│ type: str           │         │ pins: List[Pin]     │
│ parameters: dict    │         │                     │
│ pins: List[Pin]     │         │ + connect(pin)      │
├─────────────────────┤         └──────────┬──────────┘
│ + to_dict()         │                    │
│ + get_parameter()   │                    │ 0..*
│ + update_parameter()│                    │
└──────────┬──────────┘         ┌──────────┴──────────┐
           │                    │        Pin          │
           │ 1. .*               ├─────────────────────┤
           │                    │ name: str           │
           ▼                    │ direction:  Enum     │
    ┌─────────────────────┐     │ net:  Net | None     │
    │        Pin          │◄────┤ rel_x: float        │
    └─────────────────────┘     │ rel_y:  float        │
                                └─────────────────────┘
```

### JSON Schema (Project File)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "version": { "type": "string" },
    "components": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["ref", "comp_type", "x", "y"],
        "properties":  {
          "ref": { "type":  "string" },
          "comp_type": { "type":  "string" },
          "x": { "type": "number" },
          "y": { "type": "number" },
          "rotation": { "type":  "number", "default": 0 },
          "parameters": { "type":  "object" }
        }
      }
    },
    "wires": {
      "type": "array",
      "items":  {
        "type": "object",
        "required": ["x1", "y1", "x2", "y2", "net_id"],
        "properties": {
          "x1": { "type": "number" },
          "y1": { "type": "number" },
          "x2": { "type":  "number" },
          "y2":  { "type": "number" },
          "net_id":  { "type": "integer" }
        }
      }
    }
  }
}
```

---

## User Guide

### Keyboard Shortcuts

| Action | Shortcut | Context |
|--------|----------|---------|
| Undo | `Ctrl+Z` | Global |
| Redo | `Ctrl+Y` | Global |
| Save | `Ctrl+S` | Global |
| Open | `Ctrl+O` | Global |
| Rotate component | `R` | Component selected |
| Cancel wire | `Escape` | Wire tool active |
| Delete | `Delete` | Item selected |
| Pan view | `Middle-click + drag` or `Alt + drag` | Canvas |
| Zoom | `Scroll wheel` | Canvas |

### Getting Started

```bash
# 1. Clone the repository
git clone https://github.com/TristanHottier/eda-simulator.git
cd eda-simulator

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 3. Install dependencies
pip install PySide6

# 4. Run the application
python main.py
```

### Creating Your First Circuit

1. **Launch the application** — You'll see an empty canvas with a component palette on the right
2. **Add a resistor** — Click "Resistor" in the palette; it appears at the center of the view
3. **Add a capacitor** — Click "Capacitor" in the palette
4. **Move components** — Drag them to desired positions (they snap to the 50px grid)
5. **Connect with wires** — Click "Wire Tool", then click on a component pin, then click on another pin
6. **Edit values** — Click a component to select it, then modify values in the inspector panel
7. **Save your work** — Press `Ctrl+S` and choose a location

---

## Development Guidelines

### Code Style

- Follow PEP 8 with 100-character line limit
- Use type hints for all function signatures
- Docstrings for all public classes and methods
- Import order: standard library, third-party, local

### Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_circuit_model.py

# Run with coverage
python -m pytest --cov=core --cov=ui tests/
```

### Adding a New Component Type

1. Add default parameters in `core/component. py`:
   ```python
   DEFAULT_PARAMS = {
       ... 
       "new_type": {"param1": value, "type": "new_type"},
   }
   ```

2. Add unit mapping in `ui/component_item.py`:
   ```python
   UNIT_MAP = {
       ... 
       "param1": "unit_symbol",
   }
   ```

3. Add button in `app/component_palette.py`:
   ```python
   component_types = ["Resistor", "Capacitor", "LED", "Inductor", "NewType"]
   ```

### Phase Transition Checklist

Before moving to the next phase: 

- [ ] All deliverables completed
- [ ] Unit tests passing
- [ ] Manual testing of all features
- [ ] Documentation updated
- [ ] No known critical bugs
- [ ] Definition of Done criteria met
