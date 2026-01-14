from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QPainterPath
from ui.component_item import ComponentItem
from ui.pin_item import PinItem
from ui.wire_segment_item import WireSegmentItem
from ui.undo_commands import UndoStack
import json
from PySide6.QtWidgets import QFileDialog


class SchematicView(QGraphicsView):
    GRID_SIZE = 50

    def __init__(self):
        super().__init__()

        # --- Scene ---
        self.setMouseTracking(True)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setSceneRect(-5000, -5000, 10000, 10000)

        # --- Grid ---
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)

        # --- Zoom ---
        self.zoom_step = 1.2

        # --- Pan ---
        self.panning = False
        self.last_pan_point = None

        # --- Components & wires ---
        self.components = []
        self.wires = []
        self.drawing_wire = False
        self.wire_start = None
        self.current_wire = None
        self.junctions = []
        self.preview_wire = []

        # --- Nets managing ---
        self.net_counter = 1
        self.net_map = {}  # net_id -> set[(x, y)]
        self.point_to_net = {}  # maps (x, y) -> net_id
        self.net_to_wires = {}  # maps net_id -> list of WireSegmentItem
        self.next_net_id = 1

        # --- Mode ---
        self.mode = "component"  # "component" or "wire"

        # --- Undo stack ---
        self.undo_stack = UndoStack()

    # -------------------
    # GRID
    # -------------------
    def grid_key(self, point):
        return int(point.x()), int(point.y())

    def drawBackground(self, painter: QPainter, rect):
        color = QColor(180, 180, 180)
        pen = QPen(color)
        pen.setWidth(0)
        painter.setPen(pen)

        left = int(rect.left()) - (int(rect.left()) % self.GRID_SIZE)
        top = int(rect.top()) - (int(rect.top()) % self.GRID_SIZE)
        right = int(rect.right())
        bottom = int(rect.bottom())

        x = left
        while x <= right:
            painter.drawLine(x, top, x, bottom)
            x += self.GRID_SIZE

        y = top
        while y <= bottom:
            painter.drawLine(left, y, right, y)
            y += self.GRID_SIZE

    # -------------------
    # ZOOM
    # -------------------
    def wheelEvent(self, event):
        factor = self.zoom_step if event.angleDelta().y() > 0 else 1 / self.zoom_step
        self.scale(factor, factor)

    # -------------------
    # PAN & MOUSE
    # -------------------
    def mousePressEvent(self, event):
        pos = self.mapToScene(event.pos())
        grid_pos = self.snap_to_grid(pos)

        # Middle-button pan
        if event.button() == Qt.MiddleButton:
            self.panning = True
            self.last_pan_point = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            return

        # Wire mode
        if self.mode == "wire":
            # Don't start wire on a component
            if any(isinstance(item, ComponentItem) for item in self.scene.items(pos)):
                return

            if not self.drawing_wire:
                # Start wire
                self.drawing_wire = True
                self.wire_start = grid_pos
            else:
                # End wire
                self.create_orthogonal_wire(self.wire_start, grid_pos)
                self.drawing_wire = False
                self.wire_start = None

                # Remove preview lines
                if self.preview_wire:
                    for line in self.preview_wire:
                        self.scene.removeItem(line)
                    self.preview_wire = None
            return

        # Component mode
        item = self.itemAt(event.pos())
        if isinstance(item, ComponentItem):
            item.setFocus()  # Ensure the item has focus to receive key events
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = self.mapToScene(event.pos())
        grid_pos = self.snap_to_grid(pos)

        # ----------------------
        # Middle-button panning
        # ----------------------
        if self.panning and self.last_pan_point:
            delta = event.pos() - self.last_pan_point
            self.last_pan_point = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            return

        # ----------------------
        # Wire preview (live)
        # ----------------------
        if self.mode == "wire" and self.drawing_wire:
            start = self.wire_start

            # Remove previous preview
            if self.preview_wire:
                for line in self.preview_wire:
                    self.scene.removeItem(line)

            self.preview_wire = []

            # Orthogonal preview
            line1 = WireSegmentItem(
                start.x(), start.y(),
                grid_pos.x(), start.y(),
                preview=True
            )
            line2 = WireSegmentItem(
                grid_pos.x(), start.y(),
                grid_pos.x(), grid_pos.y(),
                preview=True
            )

            self.scene.addItem(line1)
            self.scene.addItem(line2)

            self.preview_wire.extend([line1, line2])
            return

        # ----------------------
        # Component moving & normal behavior
        # ----------------------
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.panning = False
            self.setCursor(Qt.ArrowCursor)
            return

        super().mouseReleaseEvent(event)

    # -------------------
    # COMPONENTS
    # -------------------
    def add_component(self, ref, comp_type="generic"):
        from core.component import Component
        from core.pin import Pin, PinDirection

        # 1. Create the logical pins first
        # Example: default 2 pins for a generic component
        pins = [
            Pin("1", PinDirection.BIDIRECTIONAL),
            Pin("2", PinDirection.BIDIRECTIONAL)
        ]

        # 2. Create the logical component model
        comp_model = Component(ref=ref, pins=pins, comp_type=comp_type)
        self.components.append(comp_model)

        # 3. Create the visual item, passing the model
        item = ComponentItem(comp_model)
        self.scene.addItem(item)

        return item

    def snap_to_grid(self, pos: QPointF) -> QPointF:
        # 1. Check for Component Pins (High priority)
        items = self.scene.items(pos, Qt.IntersectsItemShape)
        for item in items:
            if isinstance(item, PinItem):
                return item.scene_connection_point()

        # 2. Check for Wire Junctions (acting as pins)
        for junction in self.junctions:
            # If mouse is within 15 pixels of a junction, snap to it
            if (junction.scenePos() - pos).manhattanLength() < 15:
                return junction.scenePos()

        # 3. Standard Grid Snapping
        x = round(pos.x() / self.GRID_SIZE) * self.GRID_SIZE
        y = round(pos.y() / self.GRID_SIZE) * self.GRID_SIZE
        return QPointF(x, y)

    # -------------------
    # WIRE HELPERS
    # -------------------
    def update_current_wire(self, end_pos: QPointF):
        if not self.current_wire or not self.wire_start:
            return
        path = QPainterPath()
        path.moveTo(self.wire_start)
        path.lineTo(end_pos.x(), self.wire_start.y())
        path.lineTo(end_pos)
        self.current_wire.setPath(path)

    def create_orthogonal_wire(self, start: QPointF, end: QPointF):
        """Create a two-segment orthogonal wire and handle net merging"""

        # Snap to grid just in case
        start = self.snap_to_grid(start)
        end = self.snap_to_grid(end)

        self.create_junction(start)
        self.create_junction(end)

        # 1️⃣ Find all nets touched by start or end points
        nets_touched = set()
        for point, net_id in self.point_to_net.items():
            if point == (start.x(), start.y()) or point == (end.x(), end.y()):
                nets_touched.add(net_id)

        # 2️⃣ Decide net ID
        if nets_touched:
            # merge all touched nets into one
            net_id = min(nets_touched)  # keep smallest ID
            for old_net in nets_touched - {net_id}:
                # move all wires and points from old_net to net_id
                for wire in self.net_to_wires.get(old_net, []):
                    wire.net_id = net_id
                    self.net_to_wires.setdefault(net_id, []).append(wire)
                for pt, nid in list(self.point_to_net.items()):
                    if nid == old_net:
                        self.point_to_net[pt] = net_id
                del self.net_to_wires[old_net]
        else:
            # new net
            net_id = self.next_net_id
            self.next_net_id += 1
            self.net_to_wires[net_id] = []

        # 4️⃣ Create wire segments (horizontal then vertical)
        seg1 = WireSegmentItem(start.x(), start.y(), end.x(), start.y())
        seg1.net_id = net_id
        self.scene.addItem(seg1)

        seg2 = WireSegmentItem(end.x(), start.y(), end.x(), end.y())
        seg2.net_id = net_id
        self.scene.addItem(seg2)

        self.net_to_wires[net_id].extend([seg1, seg2])

        # 5️⃣ Register all points of the wire in point_to_net
        for x, y in [(start.x(), start.y()), (end.x(), start.y()), (end.x(), end.y())]:
            self.point_to_net[(x, y)] = net_id

    def create_junction(self, pos: QPointF, radius=6):
        dot = QGraphicsEllipseItem(pos.x() - radius / 2, pos.y() - radius / 2, radius, radius)
        dot.setBrush(QColor(0, 0, 0))
        dot.setZValue(0.6)
        self.scene.addItem(dot)
        self.junctions.append(dot)

    def highlight_net(self, net_id):
        for wire in self.net_map.get(net_id, []):
            wire.set_glow(True)

    def clear_highlight(self, net_id):
        for wire in self.net_map.get(net_id, []):
            wire.set_glow(False)

    def get_or_create_net(self, points):
        """
        Given a list of grid points, return a net_id.
        Merge nets if multiple nets are touched.
        """
        touched_nets = set()

        for p in points:
            if p in self.point_to_net:
                touched_nets.add(self.point_to_net[p])

        # No existing net → create one
        if not touched_nets:
            net_id = self.net_counter
            self.net_counter += 1
            self.net_map[net_id] = set(points)
        else:
            # Use the smallest net id
            net_id = min(touched_nets)

            # Merge other nets
            for other in touched_nets:
                if other == net_id:
                    continue
                for pt in self.net_map[other]:
                    self.point_to_net[pt] = net_id
                    self.net_map[net_id].add(pt)
                del self.net_map[other]

            # Add new points
            self.net_map[net_id].update(points)

        # Register points
        for p in points:
            self.point_to_net[p] = net_id

        return net_id

    # -------------------
    # MODE SWITCH
    # -------------------
    def set_mode(self, mode: str):
        if mode in ("component", "wire"):
            self.mode = mode

    def save_to_json(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Schematic", "", "JSON Files (*.json)")
        if not filename:
            return

        data = {
            "components": [],
            "wires": []
        }

        # 1. Serialize Components
        # We find the UI item for each logical component to get its position/rotation
        for comp_model in self.components:
            # Find the corresponding UI item in the scene
            ui_item = next((item for item in self.scene.items()
                            if isinstance(item, ComponentItem) and item.ref == comp_model.ref), None)

            if ui_item:
                comp_data = comp_model.to_dict()
                comp_data.update({
                    "x": ui_item.x(),
                    "y": ui_item.y(),
                    "rotation": ui_item.rotation()
                })
                data["components"].append(comp_data)

        # 2. Serialize Wires
        # Since wires are segments, we save their start/end points and Net ID
        for wire in self.scene.items():
            if isinstance(wire, WireSegmentItem) and not wire.preview:
                line = wire.line()
                data["wires"].append({
                    "x1": line.x1(), "y1": line.y1(),
                    "x2": line.x2(), "y2": line.y2(),
                    "net_id": wire.net_id
                })

        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    def load_from_json(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Schematic", "", "JSON Files (*.json)")
        if not filename:
            return

        with open(filename, 'r') as f:
            data = json.load(f)

        # 1. Clear current state
        self.scene.clear()
        self.components = []
        self.junctions = []
        self.point_to_net = {}
        self.net_to_wires = {}
        self.undo_stack = UndoStack()  # Reset undo history on load

        # 2. Reconstruct Components
        from core.component import Component
        from core.pin import Pin, PinDirection

        for comp_data in data.get("components", []):
            # Recreate logical pins (assuming 2 for generic components)
            pins = [Pin("1", PinDirection.BIDIRECTIONAL), Pin("2", PinDirection.BIDIRECTIONAL)]

            # Create logic model
            comp_model = Component(
                ref=comp_data["ref"],
                pins=pins,
                comp_type=comp_data["comp_type"]
            )
            comp_model.parameters = comp_data.get("parameters", {})
            self.components.append(comp_model)

            # Create visual item
            ui_item = ComponentItem(comp_model)
            ui_item.setPos(comp_data["x"], comp_data["y"])
            ui_item.setRotation(comp_data.get("rotation", 0))
            self.scene.addItem(ui_item)

        # 3. Reconstruct Wires
        for wire_data in data.get("wires", []):
            wire = WireSegmentItem(
                wire_data["x1"], wire_data["y1"],
                wire_data["x2"], wire_data["y2"]
            )
            wire.net_id = wire_data["net_id"]
            self.scene.addItem(wire)

            # Re-register wire points for net management
            pts = [(wire_data["x1"], wire_data["y1"]), (wire_data["x2"], wire_data["y2"])]
            for pt in pts:
                self.point_to_net[pt] = wire.net_id

            # Restore net_to_wires map
            if wire.net_id not in self.net_to_wires:
                self.net_to_wires[wire.net_id] = []
            self.net_to_wires[wire.net_id].append(wire)

            # Re-create junctions at endpoints
            self.create_junction(QPointF(wire_data["x1"], wire_data["y1"]))
            self.create_junction(QPointF(wire_data["x2"], wire_data["y2"]))



