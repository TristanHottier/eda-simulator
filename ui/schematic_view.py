# ui/schematic_view.py
import json
from typing import List, Dict, Tuple, Optional, Any
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QFileDialog
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QColor, QWheelEvent

from core.component import Component
from ui.component_item import ComponentItem
from ui.junction_item import JunctionItem
from ui.pin_item import PinItem
from ui.wire_segment_item import WireSegmentItem
from ui.undo_commands import UndoStack, CreateWireCommand, DeleteItemsCommand
from ui.grid import GridItem


class SchematicView(QGraphicsView):
    GRID_SIZE = 10

    def __init__(self):
        super().__init__()

        # --- Scene & View Configuration ---
        self._scene = QGraphicsScene()
        self.setScene(self._scene)
        self.setSceneRect(-5000, -5000, 10000, 10000)

        self.setBackgroundBrush(QColor(20, 20, 20))
        self.setMouseTracking(True)
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)

        # Ensures zoom centers on the mouse cursor
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        # --- Initialize Background Grid ---
        self.grid_item = GridItem(self.GRID_SIZE)
        self._scene.addItem(self.grid_item)

        # --- Navigation State ---
        self.zoom_step = 1.2
        self.panning = False
        self.last_pan_point: Optional[QPointF] = None

        # --- Circuit Data & State ---
        self.components: List[Component] = []
        self.undo_stack = UndoStack()
        self.mode = "component"

        self.next_net_id = 1
        self.point_to_net: Dict[Tuple[float, float], int] = {}
        self.net_to_wires: Dict[int, List[WireSegmentItem]] = {}
        self.junctions: List[JunctionItem] = []

        self.drawing_wire = False
        self.wire_start_pos: Optional[QPointF] = None
        self.preview_wire: Optional[WireSegmentItem] = None

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handles zooming via the mouse scroll wheel."""
        if event.angleDelta().y() > 0:
            factor = self.zoom_step
        else:
            factor = 1 / self.zoom_step

        # Apply the scaling transformation
        self.scale(factor, factor)

    def _snap_point(self, pt: QPointF) -> QPointF:
        """
        Calculates the snapping target.
        Prioritizes pins, then falls back to the 25px wire grid.
        """
        # 1. Check for nearby pins (Proximity Snap)
        snap_radius = 10
        search_area = QRectF(pt.x() - snap_radius, pt.y() - snap_radius,
                             snap_radius * 2, snap_radius * 2)

        for item in self._scene.items(search_area):
            if hasattr(item, "scene_connection_point"):
                return item.scene_connection_point()

        # 2. Fallback to updated 25px Wire Grid Snap
        x = round(pt.x() / self.GRID_SIZE) * self.GRID_SIZE
        y = round(pt.y() / self.GRID_SIZE) * self.GRID_SIZE
        return QPointF(x, y)

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        snapped_pos = self._snap_point(scene_pos)

        if event.button() == Qt.MiddleButton or (
                event.button() == Qt.LeftButton and event.modifiers() == Qt.AltModifier):
            self.panning = True
            self.last_pan_point = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            return

        if self.mode == "wire" and event.button() == Qt.LeftButton:
            self._handle_wire_click(snapped_pos)
            return

        super().mousePressEvent(event)

    def _handle_wire_click(self, pos: QPointF):
        """Logic for starting or extending a wire path."""
        if not self.drawing_wire:
            # Check if we are starting a wire on top of an existing one
            self._check_and_split_wire(pos)

            self.drawing_wire = True
            self.wire_start_pos = pos
            self.preview_wire = WireSegmentItem(pos.x(), pos.y(), pos.x(), pos.y(), preview=True)
            self._scene.addItem(self.preview_wire)
        else:
            self._finalize_wire(pos)

    def _finalize_wire(self, end_pos: QPointF):
        """Creates a permanent segment, checking for intersections."""
        if self.wire_start_pos == end_pos:
            return

        # Check if the endpoint lands on an existing wire to create a junction
        self._check_and_split_wire(end_pos)

        new_wire = WireSegmentItem(self.wire_start_pos.x(), self.wire_start_pos.y(), end_pos.x(), end_pos.y())
        self.register_wire_connection(new_wire)
        self.undo_stack.push(CreateWireCommand(self, new_wire))

        self.wire_start_pos = end_pos
        if self.preview_wire:
            self.preview_wire.setLine(self.wire_start_pos.x(), self.wire_start_pos.y(), end_pos.x(), end_pos.y())

    def _check_and_split_wire(self, pos: QPointF):
        """Detects if a point intersects a wire body and splits it to allow a junction."""
        for item in self.scene().items(pos):
            if isinstance(item, WireSegmentItem) and not item.preview:
                line = item.line()
                p1, p2 = line.p1(), line.p2()

                # If the point is already an endpoint, no split needed
                if pos == p1 or pos == p2:
                    continue

                # Remove old wire endpoints
                old_p1 = (p1.x(), p1.y())
                old_p2 = (p2.x(), p2.y())
                if old_p1 in self.point_to_net: del self.point_to_net[old_p1]
                if old_p2 in self.point_to_net: del self.point_to_net[old_p2]

                # Split the wire into two segments meeting at 'pos'
                self._scene.removeItem(item)

                # Remove from net tracking before splitting
                # (Simple approach: cleanup_junctions will fix the visuals)
                w1 = WireSegmentItem(p1.x(), p1.y(), pos.x(), pos.y())
                w2 = WireSegmentItem(pos.x(), pos.y(), p2.x(), p2.y())

                self._scene.addItem(w1)
                self._scene.addItem(w2)

                self.register_wire_connection(w1)
                self.register_wire_connection(w2)
                break

    def register_wire_connection(self, wire: WireSegmentItem):
        """Registers endpoints and ensures junction items exist at both ends."""
        p1 = (wire.line().x1(), wire.line().y1())
        p2 = (wire.line().x2(), wire.line().y2())

        # Logic for Net assignment
        net1 = self.point_to_net.get(p1)
        net2 = self.point_to_net.get(p2)

        if net1 and net2 and net1 != net2:
            self._merge_nets(net1, net2)
            target_net = net1
        else:
            target_net = net1 or net2 or self.next_net_id
            if target_net == self.next_net_id:
                self.next_net_id += 1

        wire.net_id = target_net

        # Register the points in the mapping
        self.point_to_net[p1] = target_net
        self.point_to_net[p2] = target_net

        # Update net tracking
        if target_net not in self.net_to_wires:
            self.net_to_wires[target_net] = []
        if wire not in self.net_to_wires[target_net]:
            self.net_to_wires[target_net].append(wire)

        # Refresh visual junction dots
        self.cleanup_junctions()

    def _stretch_wires_at(self, old_pos: QPointF, new_pos: QPointF):
        """
        Updates wires visually during a drag.
        Fix: Updates permanent wire geometry and anchors the preview wire.
        """
        old_pt = (old_pos.x(), old_pos.y())
        new_pt = (new_pos.x(), new_pos.y())

        for item in self._scene.items():
            if isinstance(item, WireSegmentItem) and not item.preview:
                line = item.line()
                p1 = line.p1()
                p2 = line.p2()
                changed = False

                # 1. Update permanent wire geometry (Erase old / Draw new)
                if p1 == old_pos:
                    p1 = new_pos
                    changed = True
                if p2 == old_pos:
                    p2 = new_pos
                    changed = True

                if changed:
                    # This call triggers the visual update/erase of the old line
                    item.setLine(p1.x(), p1.y(), p2.x(), p2.y())

                    # Update logical net mapping
                    if old_pt in self.point_to_net:
                        net_id = self.point_to_net.get(old_pt)
                        # We use setdefault or simple assignment to ensure the new point is mapped
                        self.point_to_net[new_pt] = net_id

        # 2. Update the preview wire anchor (The wire being currently drawn)
        if self.drawing_wire and self.preview_wire:
            if self.wire_start_pos == old_pos:
                self.wire_start_pos = new_pos

            current_line = self.preview_wire.line()
            # Anchor (p1) follows the junction, head (p2) stays at current mouse snap
            self.preview_wire.setLine(
                self.wire_start_pos.x(),
                self.wire_start_pos.y(),
                current_line.x2(),
                current_line.y2()
            )

    def cleanup_junctions(self):
        """
        Ensures exactly one JunctionItem exists at every wire endpoint coordinate.
        """
        # 1. Clear existing junctions from the scene
        for j in self.junctions:
            if j.scene():
                self._scene.removeItem(j)
        self.junctions.clear()

        # 2. Identify all unique endpoints currently in use by wires
        active_points = set()
        for item in self._scene.items():
            if isinstance(item, WireSegmentItem) and not item.preview:
                line = item.line()
                active_points.add((line.x1(), line.y1()))
                active_points.add((line.x2(), line.y2()))

        # 3. Create one junction dot per unique coordinate
        # This naturally handles "sharing" because a set only stores unique values
        for pt in active_points:
            j = JunctionItem(pt[0], pt[1])
            self.junctions.append(j)
            self._scene.addItem(j)

    def _merge_nets(self, net_keep: int, net_remove: int):
        """Unifies two nets into one when they are connected by a new wire."""
        wires_to_move = self.net_to_wires.pop(net_remove, [])
        for w in wires_to_move:
            w.net_id = net_keep
            self.net_to_wires[net_keep].append(w)
            # Update all endpoint mappings for moved wires
            self.point_to_net[(w.line().x1(), w.line().y1())] = net_keep
            self.point_to_net[(w.line().x2(), w.line().y2())] = net_keep

    def mouseMoveEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        if self.panning and self.last_pan_point:
            delta = event.pos() - self.last_pan_point
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self.last_pan_point = event.pos()
            return
        if self.mode == "wire" and self.drawing_wire and self.preview_wire:
            snapped = self._snap_point(scene_pos)
            self.preview_wire.setLine(self.wire_start_pos.x(), self.wire_start_pos.y(), snapped.x(), snapped.y())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.panning:
            self.panning = False
            self.setCursor(Qt.ArrowCursor if self.mode == "component" else Qt.CrossCursor)
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:
        """
        Handles keyboard shortcuts.
        Esc: Cancels the current wire drawing chain.
        Del : Deletes the selected item
        """
        if event.key() == Qt.Key_Escape:
            if self.drawing_wire:
                self._cancel_wire_drawing()
            else:
                # If not currently drawing, allow standard behavior (like deselecting)
                super().keyPressEvent(event)
        elif event.key() == Qt.Key_Delete:
            # Retrieve selected items
            selected_items = self.scene().selectedItems()

            if selected_items:
                # Create and execute a DeleteItemsCommand
                delete_command = DeleteItemsCommand(self, selected_items)
                self.undo_stack.push(delete_command)
        else:
            # Propagate other keys (like R for rotation) to the items or window
            super().keyPressEvent(event)

    def _cancel_wire_drawing(self) -> None:
        """
        Exits the wire creation state and removes temporary UI elements.
        """
        if self.preview_wire:
            # Remove the dashed 'rubber-band' line from the scene
            if self.preview_wire.scene():
                self._scene.removeItem(self.preview_wire)
            self.preview_wire = None

        # Reset state variables
        self.drawing_wire = False
        self.wire_start_pos = None

        # Optional: update the viewport to ensure the preview is cleared immediately
        self.viewport().update()

    def get_snapping_grid_size(self):
        """
        Determines the snapping grid size based on the selection.
        Returns:
            int: The grid size (10px or 50px).
        """
        selected_items = self.scene().selectedItems()

        # Check if at least one component is selected
        for item in selected_items:
            if isinstance(item, ComponentItem):
                return 50  # Snap to 50px grid

        # If no components are selected, snap to 10px grid
        return 10

    def load_from_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Schematic", "", "JSON Files (*.json)")
        if not path: return
        with open(path, 'r') as f:
            data = json.load(f)
        self._scene.clear()
        self.components.clear()
        self.point_to_net.clear()
        self.net_to_wires.clear()
        self._scene.addItem(GridItem(self.GRID_SIZE))
        for c_data in data.get("components", []):
            model = Component(c_data["ref"], comp_type=c_data["comp_type"], parameters=c_data.get("parameters"))
            self.components.append(model)
            item = ComponentItem(model)
            item.setPos(c_data["x"], c_data["y"])
            item.setRotation(c_data.get("rotation", 0))
            self._scene.addItem(item)
        for w_data in data.get("wires", []):
            wire = WireSegmentItem(w_data["x1"], w_data["y1"], w_data["x2"], w_data["y2"], net_id=w_data["net_id"])
            self._scene.addItem(wire)
            self.register_wire_connection(wire)