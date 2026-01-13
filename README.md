# PyEDA-Sim

**Python Electronic Circuit & MCU Simulator**

---

## Overview

PyEDA-Sim is a **Python-based electronic engineering simulation tool** designed for students, hobbyists, and engineers.  

The project allows you to **design, wire, and simulate circuits**, combining **analog, digital, and microcontroller components** in a single, unified environment.

The interface is inspired by tools like EasyEDA and Simulink, providing a **grid-based schematic editor** with drag-and-drop components and configurable parameters.

---

## Core Goals

- **Schematic Editor**
  - Grid-based design with snap-to-grid wiring
  - Color-coded wires for clarity
  - Drag-and-drop components: resistors, capacitors, inductors, batteries, headers, and more

- **Analog Circuit Simulation**
  - SPICE-based simulation of circuits
  - Voltage, current, and transient analysis
  - Supports basic RC, RL, and RLC circuits

- **Digital Components and Sensors**
  - Event-driven simulation of logic gates and flip-flops
  - Sensor models: accelerometers, barometers, and other I2C/SPI devices
  - Ability to read virtual sensor outputs in real-time

- **Microcontroller Support**
  - Simulate Arduino, Teensy, and Raspberry Pi microcontrollers
  - Run uploaded firmware or scripts
  - Interface with sensors and outputs for testing code

- **Realistic Component Libraries**
  - Configure generic components with custom values
  - Integrate real-world component libraries for accurate simulations
  - Allows testing with actual part specifications

---

## Vision

PyEDA-Sim aims to **bridge the gap between conceptual circuit design and practical testing**, enabling users to:

- Quickly prototype and simulate circuits before building them
- Test microcontroller code with virtual sensors and components
- Create complex systems combining analog, digital, and software components
- Keep designs clear and organized with a grid-based schematic view

---

## Project Scope

**In scope:**

- Circuit schematic editor
- Analog simulation via SPICE
- Digital component simulation
- Microcontroller simulation for common boards
- Sensor simulation and virtual I/O

**Out of scope (initially):**

- PCB layout and fabrication
- Full microcontroller emulation beyond common MCUs
- Advanced 3D visualization

---

PyEDA-Sim is designed to be **extensible**, so future phases will expand component libraries, support more microcontrollers, and enhance simulation accuracy.
