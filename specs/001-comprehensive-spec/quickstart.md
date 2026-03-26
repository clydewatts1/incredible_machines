# Incredible Machines: Quickstart Guide

This guide provides a baseline for operating the Incredible Machines engine in accordance with the Project Constitution v1.1.0.

## 1. Environment Setup
- **Dependencies**: Ensure `pygame-ce`, `pymunk`, `pygame-gui`, and `faker` are installed.
- **Config**: Review `config/environment.yaml` for resolution, deadzones, and control sensitivities.
- **Run**: Execute `python main.py` to launch the sandbox.

## 2. Controls (M42)
- **Mouse/Keyboard**: 
    - Left Click: Place/Select.
    - Right Click: Delete.
    - Arrows: Camera Pan.
- **Gamepad**:
    - Left Stick: Virtual Mouse.
    - Right Stick: Physical Avatar movement (PLAY mode only).
    - A/B Buttons: primary/Secondary UI actions.

## 3. Visual Programming Loop (US1)
- **Placement**: Select a machine from the palette and click on the canvas.
- **Wiring**: click an Output port (Green) and drag to an Input port (Red) to route payloads.
- **PLAY Mode**: Toggle logic execution to observe physics-based data flow.

## 4. Synthetic Data ETL (M40)
- **FakerSource**: Generates random JSON records.
- **FakerEngine**: Mutates record fields in flight.
- **FileSink**: Aggregates records and writes them to `.jsonl` files in the project workspace.

## 5. Architectural Safeguards
- **Zero Rule**: No custom trigonometry in routing; `resolve_exit_path` handles all ejections.
- **Kill Z**: Objects falling below the screen are automatically flagged for deletion.
- **Handshakes**: Machines will pause (Visual: JAMMED state) if the downstream buffer is full.
