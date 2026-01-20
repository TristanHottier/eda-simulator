# ui/component_item.py
from typing import Optional, Any, List
from PySide6.QtWidgets import (
    QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem,
    QGraphicsPolygonItem, QGraphicsEllipseItem, QGraphicsLineItem,
    QGraphicsPathItem
)
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QBrush, QColor, QPolygonF, QPen, QFont, QPainterPath
from ui.undo_commands import MoveComponentCommand, RotateComponentCommand
from ui.pin_item import PinItem


class ComponentItem(QGraphicsRectItem):
    GRID_SIZE = 50
    UNIT_MAP = {
        "resistance": "Ω",
        "capacitance": "nF",
        "voltage_drop": "V",
        "inductance": "mH",
        "voltage":  "V",
        "frequency": "Hz",
        "current": "A"
    }

    def __init__(self, component_model, width: int = 100, height: int = 50):
        # Ground component has different dimensions
        if component_model.type == "ground":
            width = 50
            height = 30
        # Voltage and current sources:  2x1 grid (50x100)
        elif component_model.type in ("dc_voltage_source", "ac_voltage_source", "dc_current_source"):
            width = 50
            height = 100

        super().__init__(0, 0, width, height)
        self.model = component_model
        self.ref:  str = self.model.ref
        self.old_pos: Optional[QPointF] = None
        self._is_being_moved_by_master = False

        # --- Theme State ---
        self._dark_mode = True  # Default to dark mode (white components)
        self._stroke_color = QColor("white")

        # --- Flags ---
        self.setFlags(
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemIsFocusable |
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemSendsScenePositionChanges |
            QGraphicsItem.ItemSendsGeometryChanges
        )

        # Set origin to center for clean rotation
        self.setTransformOriginPoint(width / 2, height / 2)
        self.setAcceptedMouseButtons(Qt.LeftButton)

        # --- Visuals:  Transparent bounding box for all components ---
        self.setBrush(QBrush(Qt.transparent))
        self.setPen(QPen(Qt.NoPen))

        # Create appropriate symbol based on component type
        self._create_symbol(width, height)

        # --- Label ---
        self.label = QGraphicsTextItem("", self)
        self.refresh_label()

        # --- Pins ---
        self.pin_items: List[PinItem] = []
        for pin_logic in self.model.pins:
            p_item = PinItem(pin_logic, pin_logic.rel_x, pin_logic.rel_y, self)
            self.pin_items.append(p_item)

    def set_dark_mode(self, dark:  bool) -> None:
        """Updates the component colors based on theme."""
        self._dark_mode = dark
        self._stroke_color = QColor("white") if dark else QColor("black")

        # Update all visual elements
        self._update_symbol_colors()

        # Update label color
        self.label.setDefaultTextColor(self._stroke_color)

        # Update pins
        for pin_item in self.pin_items:
            pin_item.set_dark_mode(dark)

    def _update_symbol_colors(self) -> None:
        """Updates all symbol elements to match current theme."""
        pen = QPen(self._stroke_color, 2)
        thick_pen = QPen(self._stroke_color, 3)
        thin_pen = QPen(self._stroke_color, 1.5)

        comp_type = self.model.type

        if comp_type == "resistor":
            self.resistor_lead_left.setPen(pen)
            self.resistor_zigzag.setPen(pen)
            self.resistor_lead_right.setPen(pen)

        elif comp_type == "capacitor":
            self.cap_lead_left.setPen(pen)
            self.cap_plate_left.setPen(thick_pen)
            self.cap_plate_right.setPen(thick_pen)
            self.cap_lead_right.setPen(pen)

        elif comp_type == "inductor":
            self.inductor_lead_left.setPen(pen)
            self.inductor_coils.setPen(pen)
            self.inductor_lead_right.setPen(pen)

        elif comp_type == "led":
            self.led_lead_left.setPen(pen)
            self.led_triangle.setPen(pen)
            # LED keeps yellow fill regardless of theme
            self.led_bar.setPen(thick_pen)
            self.led_lead_right.setPen(pen)
            self.led_arrow1_line.setPen(thin_pen)
            self.led_arrow1_head.setPen(thin_pen)
            self.led_arrow1_head.setBrush(QBrush(self._stroke_color))
            self.led_arrow2_line.setPen(thin_pen)
            self.led_arrow2_head.setPen(thin_pen)
            self.led_arrow2_head.setBrush(QBrush(self._stroke_color))

        elif comp_type == "diode":
            diode_type = self.model.parameters.get("diode_type", "silicon")
            self.diode_lead_left.setPen(pen)
            self.diode_triangle.setPen(pen)
            self.diode_bar.setPen(thick_pen)
            self.diode_lead_right.setPen(pen)
            if diode_type == "zener":
                self.zener_bend1.setPen(pen)
                self.zener_bend2.setPen(pen)
            elif diode_type == "schottky":
                self.schottky_label.setDefaultTextColor(self._stroke_color)

        elif comp_type == "ground":
            self.gnd_vertical.setPen(pen)
            for i, bar in enumerate(self.gnd_bars):
                bar.setPen(QPen(self._stroke_color, 3 - i))

        elif comp_type in ("dc_voltage_source", "ac_voltage_source"):
            self.vs_lead_top.setPen(pen)
            self.voltage_circle.setPen(pen)
            # Circle fill:  dark gray in dark mode, white in light mode
            if self._dark_mode:
                self.voltage_circle.setBrush(QBrush(QColor(40, 40, 40)))
            else:
                self.voltage_circle.setBrush(QBrush(Qt.white))
            self.vs_lead_bottom.setPen(pen)
            self.plus_label.setDefaultTextColor(self._stroke_color)
            self.minus_label.setDefaultTextColor(self._stroke_color)
            if comp_type == "ac_voltage_source":
                self.ac_wave.setPen(pen)
            else:
                self.dc_line1.setPen(pen)
                self.dc_line2.setPen(pen)

        elif comp_type == "dc_current_source":
            self.cs_lead_top.setPen(pen)
            self.current_circle.setPen(pen)
            if self._dark_mode:
                self.current_circle.setBrush(QBrush(QColor(40, 40, 40)))
            else:
                self.current_circle.setBrush(QBrush(Qt.white))
            self.cs_lead_bottom.setPen(pen)
            self.arrow_shaft.setPen(pen)
            self.arrow_head_item.setBrush(QBrush(self._stroke_color))

        elif hasattr(self, 'generic_rect'):
            self.generic_rect.setPen(pen)
            if self._dark_mode:
                self.generic_rect.setBrush(QBrush(QColor(40, 40, 40)))
            else:
                self.generic_rect.setBrush(QBrush(QColor("#eeeeee")))
            self.generic_lead_left.setPen(pen)
            self.generic_lead_right.setPen(pen)

    def _create_symbol(self, width:  int, height: int) -> None:
        comp_type = self.model.type

        if comp_type == "resistor":
            self._create_resistor_symbol(width, height)
        elif comp_type == "capacitor":
            self._create_capacitor_symbol(width, height)
        elif comp_type == "inductor":
            self._create_inductor_symbol(width, height)
        elif comp_type == "led":
            self._create_led_symbol(width, height)
        elif comp_type == "diode":
            # Check which diode type to draw (silicon, schottky, zener) via parameter 'diode_type'
            diode_type = self.model.parameters.get("diode_type", "silicon")
            self._create_diode_symbol(width, height, diode_type)
        elif comp_type == "ground":
            self._create_ground_symbol(width, height)
        elif comp_type in ("dc_voltage_source", "ac_voltage_source"):
            self._create_voltage_source_symbol(width, height)
        elif comp_type == "dc_current_source":
            self._create_current_source_symbol(width, height)
        else:
            self._create_generic_symbol(width, height)

    def _create_resistor_symbol(self, width: int, height:  int) -> None:
        """Creates a proper zigzag resistor symbol (US style)."""
        pen = QPen(self._stroke_color, 2)
        center_y = height / 2

        # Lead-in line (left side)
        lead_length = 15
        self.resistor_lead_left = QGraphicsLineItem(0, center_y, lead_length, center_y, self)
        self.resistor_lead_left.setPen(pen)

        # Zigzag pattern:  center -> up -> down -> up -> down -> up -> down -> center
        zigzag_start = lead_length
        zigzag_end = width - lead_length
        zigzag_width = zigzag_end - zigzag_start
        peak_height = 10

        num_half_segments = 12
        half_segment_width = zigzag_width / num_half_segments

        path = QPainterPath()
        path.moveTo(zigzag_start, center_y)

        # Half segment:  center to first peak (up)
        path.lineTo(zigzag_start + half_segment_width, center_y - peak_height)

        # Full segments: peak to peak
        current_x = zigzag_start + half_segment_width
        going_down = True

        for i in range(5):
            current_x += 2 * half_segment_width
            if going_down:
                path.lineTo(current_x, center_y + peak_height)
            else:
                path.lineTo(current_x, center_y - peak_height)
            going_down = not going_down

        # Half segment: last peak back to center
        path.lineTo(zigzag_end, center_y)

        self.resistor_zigzag = QGraphicsPathItem(path, self)
        self.resistor_zigzag.setPen(pen)
        self.resistor_zigzag.setBrush(QBrush(Qt.NoBrush))

        # Lead-out line (right side)
        self.resistor_lead_right = QGraphicsLineItem(zigzag_end, center_y, width, center_y, self)
        self.resistor_lead_right.setPen(pen)

    def _create_capacitor_symbol(self, width: int, height: int) -> None:
        """Creates a capacitor symbol with two parallel plates."""
        pen = QPen(self._stroke_color, 2)
        center_x = width / 2
        center_y = height / 2
        plate_gap = 8
        plate_height = 30

        # Left lead
        self.cap_lead_left = QGraphicsLineItem(0, center_y, center_x - plate_gap, center_y, self)
        self.cap_lead_left.setPen(pen)

        # Left plate
        self.cap_plate_left = QGraphicsLineItem(
            center_x - plate_gap, center_y - plate_height / 2,
            center_x - plate_gap, center_y + plate_height / 2,
            self
        )
        self.cap_plate_left.setPen(QPen(self._stroke_color, 3))

        # Right plate
        self.cap_plate_right = QGraphicsLineItem(
            center_x + plate_gap, center_y - plate_height / 2,
            center_x + plate_gap, center_y + plate_height / 2,
            self
        )
        self.cap_plate_right.setPen(QPen(self._stroke_color, 3))

        # Right lead
        self.cap_lead_right = QGraphicsLineItem(center_x + plate_gap, center_y, width, center_y, self)
        self.cap_lead_right.setPen(pen)

    def _create_inductor_symbol(self, width: int, height: int) -> None:
        """Creates an inductor symbol with semicircular coils."""
        pen = QPen(self._stroke_color, 2)
        center_y = height / 2

        # Lead-in line
        lead_length = 15
        self.inductor_lead_left = QGraphicsLineItem(0, center_y, lead_length, center_y, self)
        self.inductor_lead_left.setPen(pen)

        # Coils (4 humps)
        coil_start = lead_length
        coil_end = width - lead_length
        coil_width = coil_end - coil_start
        num_coils = 4
        coil_diameter = coil_width / num_coils

        path = QPainterPath()
        path.moveTo(coil_start, center_y)

        for i in range(num_coils):
            arc_start_x = coil_start + i * coil_diameter
            path.arcTo(
                arc_start_x, center_y - coil_diameter / 2,
                coil_diameter, coil_diameter,
                180, -180
            )

        self.inductor_coils = QGraphicsPathItem(path, self)
        self.inductor_coils.setPen(pen)
        self.inductor_coils.setBrush(QBrush(Qt.NoBrush))

        # Lead-out line
        self.inductor_lead_right = QGraphicsLineItem(coil_end, center_y, width, center_y, self)
        self.inductor_lead_right.setPen(pen)

    def _create_led_symbol(self, width: int, height:  int) -> None:
        """Creates an LED symbol (diode with arrows indicating light emission)."""
        pen = QPen(self._stroke_color, 2)
        center_x = width / 2
        center_y = height / 2
        triangle_size = 20

        # Left lead
        self.led_lead_left = QGraphicsLineItem(0, center_y, center_x - triangle_size / 2, center_y, self)
        self.led_lead_left.setPen(pen)

        # Triangle (pointing right)
        triangle = QPolygonF([
            QPointF(center_x - triangle_size / 2, center_y - triangle_size / 2),
            QPointF(center_x - triangle_size / 2, center_y + triangle_size / 2),
            QPointF(center_x + triangle_size / 2, center_y)
        ])
        self.led_triangle = QGraphicsPolygonItem(triangle, self)
        self.led_triangle.setPen(pen)
        self.led_triangle.setBrush(QBrush(QColor("#ffdd44")))  # Yellow fill for LED

        # Vertical bar (cathode)
        self.led_bar = QGraphicsLineItem(
            center_x + triangle_size / 2, center_y - triangle_size / 2,
            center_x + triangle_size / 2, center_y + triangle_size / 2,
            self
        )
        self.led_bar.setPen(QPen(self._stroke_color, 3))

        # Right lead
        self.led_lead_right = QGraphicsLineItem(center_x + triangle_size / 2, center_y, width, center_y, self)
        self.led_lead_right.setPen(pen)

        # Light emission arrows
        arrow_pen = QPen(self._stroke_color, 1.5)

        # Arrow 1
        arrow1_start_x = center_x
        arrow1_start_y = center_y - triangle_size / 2 - 2
        arrow1_end_x = arrow1_start_x + 15
        arrow1_end_y = arrow1_start_y - 12

        self.led_arrow1_line = QGraphicsLineItem(
            arrow1_start_x, arrow1_start_y,
            arrow1_end_x, arrow1_end_y,
            self
        )
        self.led_arrow1_line.setPen(arrow_pen)

        arrow1_head = QPolygonF([
            QPointF(arrow1_end_x, arrow1_end_y),
            QPointF(arrow1_end_x - 6, arrow1_end_y + 2),
            QPointF(arrow1_end_x - 2, arrow1_end_y + 6)
        ])
        self.led_arrow1_head = QGraphicsPolygonItem(arrow1_head, self)
        self.led_arrow1_head.setPen(arrow_pen)
        self.led_arrow1_head.setBrush(QBrush(self._stroke_color))

        # Arrow 2
        arrow2_start_x = arrow1_start_x + 8
        arrow2_start_y = arrow1_start_y + 2
        arrow2_end_x = arrow2_start_x + 15
        arrow2_end_y = arrow2_start_y - 12

        self.led_arrow2_line = QGraphicsLineItem(
            arrow2_start_x, arrow2_start_y,
            arrow2_end_x, arrow2_end_y,
            self
        )
        self.led_arrow2_line.setPen(arrow_pen)

        arrow2_head = QPolygonF([
            QPointF(arrow2_end_x, arrow2_end_y),
            QPointF(arrow2_end_x - 6, arrow2_end_y + 2),
            QPointF(arrow2_end_x - 2, arrow2_end_y + 6)
        ])
        self.led_arrow2_head = QGraphicsPolygonItem(arrow2_head, self)
        self.led_arrow2_head.setPen(arrow_pen)
        self.led_arrow2_head.setBrush(QBrush(self._stroke_color))

    def _create_diode_symbol(self, width: int, height: int, diode_type: str) -> None:
        # 1. CLEANUP: Remove any existing diode parts to avoid ghosting/overlaps
        for attr in ["diode_lead_left", "diode_triangle", "diode_bar",
                     "zener_bend1", "zener_bend2", "schottky_label", "diode_lead_right"]:
            if hasattr(self, attr):
                item = getattr(self, attr)
                if item and item.scene():
                    item.setParentItem(None)
                    self.scene().removeItem(item)
                setattr(self, attr, None)

        pen = QPen(self._stroke_color, 2)
        center_x = width / 2
        center_y = height / 2
        triangle_size = 20

        # --- Draw Base (Shared by all) ---
        # Left lead
        self.diode_lead_left = QGraphicsLineItem(0, center_y, center_x - triangle_size / 2, center_y, self)
        self.diode_lead_left.setPen(pen)

        # Triangle (Anode)
        triangle = QPolygonF([
            QPointF(center_x - triangle_size / 2, center_y - triangle_size / 2),
            QPointF(center_x - triangle_size / 2, center_y + triangle_size / 2),
            QPointF(center_x + triangle_size / 2, center_y)
        ])
        self.diode_triangle = QGraphicsPolygonItem(triangle, self)
        self.diode_triangle.setPen(pen)

        # Main Bar (Cathode)
        self.diode_bar = QGraphicsLineItem(
            center_x + triangle_size / 2, center_y - triangle_size / 2,
            center_x + triangle_size / 2, center_y + triangle_size / 2,
            self
        )
        self.diode_bar.setPen(QPen(self._stroke_color, 3))

        # --- Type Specific Logic ---
        if diode_type == "zener":
            line_len = 6
            y1 = center_y - triangle_size / 2
            y2 = center_y + triangle_size / 2
            # Classic Zener "Z" bends
            self.zener_bend1 = QGraphicsLineItem(center_x + triangle_size / 2, y1,
                                                 center_x + triangle_size / 2 + line_len, y1 - line_len / 2, self)
            self.zener_bend2 = QGraphicsLineItem(center_x + triangle_size / 2 - line_len, y2 + line_len / 2,
                                                 center_x + triangle_size / 2, y2, self)
            self.zener_bend1.setPen(pen)
            self.zener_bend2.setPen(pen)

        elif diode_type == "schottky":
            # Schottky "S" hooks on the bar
            hook_len = 5
            y1 = center_y - triangle_size / 2
            y2 = center_y + triangle_size / 2
            self.zener_bend1 = QGraphicsLineItem(center_x + triangle_size / 2 - hook_len, y1,
                                                 center_x + triangle_size / 2, y1, self)
            self.zener_bend2 = QGraphicsLineItem(center_x + triangle_size / 2, y2,
                                                 center_x + triangle_size / 2 + hook_len, y2, self)
            # Note: Standard Schottky symbols have little L-shaped ticks on the bar
            self.zener_bend1.setPen(pen)
            self.zener_bend2.setPen(pen)

        # Right lead
        self.diode_lead_right = QGraphicsLineItem(center_x + triangle_size / 2, center_y, width, center_y, self)
        self.diode_lead_right.setPen(pen)

    def _create_ground_symbol(self, width: int, height: int) -> None:
        """Creates the ground symbol with horizontal lines."""
        pen = QPen(self._stroke_color, 2)
        center_x = width / 2

        # Vertical line from pin to first bar
        self.gnd_vertical = QGraphicsLineItem(center_x, 0, center_x, 8, self)
        self.gnd_vertical.setPen(pen)

        # Three horizontal lines of decreasing width
        bar_widths = [30, 20, 10]
        bar_y_positions = [8, 16, 24]

        self.gnd_bars = []
        for i, (bar_width, bar_y) in enumerate(zip(bar_widths, bar_y_positions)):
            bar = QGraphicsLineItem(
                center_x - bar_width / 2, bar_y,
                center_x + bar_width / 2, bar_y,
                self
            )
            bar.setPen(QPen(self._stroke_color, 3 - i))
            self.gnd_bars.append(bar)

    def _create_voltage_source_symbol(self, width: int, height: int) -> None:
        """Creates the voltage source symbol as a circle with +/- and indicator separated."""
        pen = QPen(self._stroke_color, 2)

        circle_diameter = 40
        circle_x = (width - circle_diameter) / 2
        circle_y = (height - circle_diameter) / 2

        # Vertical line from top pin to circle
        self.vs_lead_top = QGraphicsLineItem(
            width / 2, 0,
            width / 2, circle_y,
            self
        )
        self.vs_lead_top.setPen(pen)

        # Circle
        self.voltage_circle = QGraphicsEllipseItem(circle_x, circle_y, circle_diameter, circle_diameter, self)
        self.voltage_circle.setPen(pen)
        self.voltage_circle.setBrush(QBrush(QColor(40, 40, 40)))  # Dark fill for dark mode

        # Vertical line from circle to bottom pin
        self.vs_lead_bottom = QGraphicsLineItem(
            width / 2, circle_y + circle_diameter,
            width / 2, height,
            self
        )
        self.vs_lead_bottom.setPen(pen)

        # + symbol at top of circle (outside, near the lead)
        plus_font = QFont()
        plus_font.setPointSize(10)
        plus_font.setBold(True)
        self.plus_label = QGraphicsTextItem("+", self)
        self.plus_label.setFont(plus_font)
        self.plus_label.setDefaultTextColor(self._stroke_color)
        self.plus_label.setPos(width / 2 + 8, circle_y - 15)

        # - symbol at bottom of circle (outside, near the lead)
        self.minus_label = QGraphicsTextItem("−", self)
        self.minus_label.setFont(plus_font)
        self.minus_label.setDefaultTextColor(self._stroke_color)
        minus_rect = self.minus_label.boundingRect()
        self.minus_label.setPos(width / 2 + 8, circle_y + circle_diameter - minus_rect.height() + 15)

        # AC or DC indicator in the CENTER of the circle
        if self.model.type == "ac_voltage_source":
            self._draw_ac_symbol(width, height, circle_y, circle_diameter)
        else:
            self._draw_dc_symbol(width, height, circle_y, circle_diameter)

    def _create_current_source_symbol(self, width: int, height: int) -> None:
        """Creates the current source symbol as a circle with an arrow."""
        pen = QPen(self._stroke_color, 2)

        circle_diameter = 40
        circle_x = (width - circle_diameter) / 2
        circle_y = (height - circle_diameter) / 2

        # Vertical line from top pin to circle
        self.cs_lead_top = QGraphicsLineItem(
            width / 2, 0,
            width / 2, circle_y,
            self
        )
        self.cs_lead_top.setPen(pen)

        # Circle
        self.current_circle = QGraphicsEllipseItem(circle_x, circle_y, circle_diameter, circle_diameter, self)
        self.current_circle.setPen(pen)
        self.current_circle.setBrush(QBrush(QColor(40, 40, 40)))  # Dark fill for dark mode

        # Vertical line from circle to bottom pin
        self.cs_lead_bottom = QGraphicsLineItem(
            width / 2, circle_y + circle_diameter,
            width / 2, height,
            self
        )
        self.cs_lead_bottom.setPen(pen)

        # Arrow inside circle pointing up
        self._draw_current_arrow(width, height, circle_y, circle_diameter)

    def _draw_current_arrow(self, width: int, height: int, circle_y: float, circle_diameter: float) -> None:
        """Draws an upward-pointing arrow inside the current source circle."""
        center_x = width / 2
        center_y_circle = circle_y + circle_diameter / 2
        pen = QPen(self._stroke_color, 2)

        arrow_length = 24
        arrow_head_size = 10

        arrow_start_y = center_y_circle + arrow_length / 2
        arrow_end_y = center_y_circle - arrow_length / 2

        # Arrow shaft
        self.arrow_shaft = QGraphicsLineItem(
            center_x, arrow_start_y,
            center_x, arrow_end_y,
            self
        )
        self.arrow_shaft.setPen(pen)

        # Arrow head
        arrow_head = QPolygonF([
            QPointF(center_x, arrow_end_y),
            QPointF(center_x - arrow_head_size / 2, arrow_end_y + arrow_head_size),
            QPointF(center_x + arrow_head_size / 2, arrow_end_y + arrow_head_size)
        ])
        self.arrow_head_item = QGraphicsPolygonItem(arrow_head, self)
        self.arrow_head_item.setBrush(QBrush(self._stroke_color))
        self.arrow_head_item.setPen(QPen(Qt.NoPen))

    def _draw_ac_symbol(self, width: int, height: int, circle_y: float, circle_diameter:  float) -> None:
        """Draws a sine wave symbol in the CENTER of the voltage source circle."""
        center_x = width / 2
        center_y = circle_y + circle_diameter / 2

        path = QPainterPath()
        wave_width = 20
        wave_height = 8

        path.moveTo(center_x - wave_width / 2, center_y)
        path.cubicTo(
            center_x - wave_width / 4, center_y - wave_height * 1.5,
            center_x - wave_width / 8, center_y - wave_height * 1.5,
            center_x, center_y
        )
        path.cubicTo(
            center_x + wave_width / 8, center_y + wave_height * 1.5,
            center_x + wave_width / 4, center_y + wave_height * 1.5,
            center_x + wave_width / 2, center_y
        )

        self.ac_wave = QGraphicsPathItem(path, self)
        self.ac_wave.setPen(QPen(self._stroke_color, 2))
        self.ac_wave.setBrush(QBrush(Qt.NoBrush))

    def _draw_dc_symbol(self, width:  int, height: int, circle_y:  float, circle_diameter: float) -> None:
        """Draws DC indicator lines in the CENTER of the voltage source circle."""
        center_x = width / 2
        center_y = circle_y + circle_diameter / 2
        line_width = 16

        # Long line (positive bar)
        self.dc_line1 = QGraphicsLineItem(
            center_x - line_width / 2, center_y - 5,
            center_x + line_width / 2, center_y - 5,
            self
        )
        self.dc_line1.setPen(QPen(self._stroke_color, 2))

        # Short line (negative bar)
        self.dc_line2 = QGraphicsLineItem(
            center_x - line_width / 3, center_y + 5,
            center_x + line_width / 3, center_y + 5,
            self
        )
        self.dc_line2.setPen(QPen(self._stroke_color, 2))

    def _create_generic_symbol(self, width:  int, height: int) -> None:
        """Creates a generic rectangular component symbol."""
        pen = QPen(self._stroke_color, 2)

        # Simple rectangle
        rect_margin = 15
        self.generic_rect = QGraphicsRectItem(
            rect_margin, 5,
            width - 2 * rect_margin, height - 10,
            self
        )
        self.generic_rect.setPen(pen)
        self.generic_rect.setBrush(QBrush(QColor(40, 40, 40)))

        # Lead lines
        center_y = height / 2
        self.generic_lead_left = QGraphicsLineItem(0, center_y, rect_margin, center_y, self)
        self.generic_lead_left.setPen(pen)

        self.generic_lead_right = QGraphicsLineItem(width - rect_margin, center_y, width, center_y, self)
        self.generic_lead_right.setPen(pen)

    def update_symbol(self) -> None:
        """
        Public method to refresh the visual appearance of the component
        based on current model parameters.
        """
        # Get dimensions from the current bounding box
        # Usually defined by constants like width=100, height=40
        rect = self.boundingRect()
        w, h = int(rect.width()), int(rect.height())

        if self.model.type == "diode":
            dtype = self.model.parameters.get("diode_type", "silicon")
            self._create_diode_symbol(w, h, dtype)

        self.update()  # Force Qt to repaint the item

    def refresh_label(self) -> None:
        """Updates the text label based on current model parameters."""
        if self.model.type == "ground":
            text = self.ref
        elif self.model.type == "dc_voltage_source":
            voltage = self.model.parameters.get("voltage", 5.0)
            text = f"{self.ref}\n{voltage}V DC"
        elif self.model.type == "ac_voltage_source":
            voltage = self.model.parameters.get("voltage", 5.0)
            freq = self.model.parameters.get("frequency", 1000)
            text = f"{self.ref}\n{voltage}V {freq}Hz"
        elif self.model.type == "dc_current_source":
            current = self.model.parameters.get("current", 0.001)
            if current < 1:
                text = f"{self.ref}\n{current * 1000}mA"
            else:
                text = f"{self.ref}\n{current}A"
        elif self.model.type == "diode":
            diode_type = self.model.parameters.get("diode_type", "silicon")
            text = self.ref
            if diode_type == "zener":
                text += " Zener"
            elif diode_type == "schottky":
                text += " Schottky"
        else:
            main_key = next(
                (k for k in self.UNIT_MAP.keys() if k in self.model.parameters),
                None
            )
            if main_key:
                val = self.model.parameters[main_key]
                unit = self.UNIT_MAP.get(main_key, "")
                text = f"{self.ref} {val}{unit}"
            else:
                text = self.ref

        self.label.setPlainText(text)
        self.label.setDefaultTextColor(self._stroke_color)
        self.update_label_position()

    def update_label_position(self) -> None:
        """Centers the label above or beside the component."""
        rect = self.rect()
        label_rect = self.label.boundingRect()

        if self.model.type == "ground":
            self.label.setPos(
                (rect.width() - label_rect.width()) / 2,
                rect.height() + 5
            )
        elif self.model.type in ("dc_voltage_source", "ac_voltage_source", "dc_current_source"):
            self.label.setPos(
                rect.width() + 5,
                (rect.height() - label_rect.height()) / 2
            )
        else:
            self.label.setPos(
                (rect.width() - label_rect.width()) / 2,
                -label_rect.height() - 5
            )

    def _snap_to_grid(self, pos: QPointF) -> QPointF:
        """Calculates the nearest grid intersection for a given position."""
        x = round(pos.x() / self.GRID_SIZE) * self.GRID_SIZE
        y = round(pos.y() / self.GRID_SIZE) * self.GRID_SIZE
        return QPointF(x, y)

    def _is_master_component(self) -> bool:
        """Check if this component is the 'master' (first ComponentItem in selection)."""
        if not self.scene():
            return False

        for item in self.scene().selectedItems():
            if isinstance(item, ComponentItem):
                return item is self
        return False

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        """Forces the item to snap to the grid in real-time during movement."""
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            if self._is_being_moved_by_master:
                return value

            old_pos = self.pos()
            new_pos = self._snap_to_grid(value)
            delta = new_pos - old_pos

            if (delta.x() != 0 or delta.y() != 0) and self._is_master_component():
                self._move_selected_junctions_proportionally(delta)

            return new_pos
        return super().itemChange(change, value)

    def _move_selected_junctions_proportionally(self, component_delta: QPointF) -> None:
        """Move selected junctions by the same delta to maintain relative spacing."""
        from ui.junction_item import JunctionItem

        if not self.scene():
            return

        selected_items = self.scene().selectedItems()

        for item in selected_items:
            if isinstance(item, JunctionItem):
                item._is_being_moved_by_master = True
                item.setPos(item.pos() + component_delta)
                item._is_being_moved_by_master = False

    def mousePressEvent(self, event) -> None:
        self.old_pos = self.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        new_pos = self.pos()
        if self.old_pos and self.old_pos != new_pos:
            view = self.scene().views()[0]
            if hasattr(view, "undo_stack"):
                view.undo_stack.push(MoveComponentCommand(self, self.old_pos, new_pos))

        super().mouseReleaseEvent(event)

    def update_label_after_dialog(self, comp_model) -> None:
        """Public API to trigger a label refresh after model edits."""
        self.model = comp_model
        self.refresh_label()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_R:
            old_rot = self.rotation()
            new_rot = (old_rot + 90) % 360

            view = self.scene().views()[0]
            if hasattr(view, "undo_stack"):
                view.undo_stack.push(RotateComponentCommand(self, old_rot, new_rot))
            else:
                self.setRotation(new_rot)
        else:
            super().keyPressEvent(event)