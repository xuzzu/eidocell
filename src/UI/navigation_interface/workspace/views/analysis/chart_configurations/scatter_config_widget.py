from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QComboBox, QLabel,
    QGroupBox, QRadioButton, QButtonGroup
)
from UI.navigation_interface.workspace.views.analysis.chart_configurations.parameter_holders import ScatterParameters


class ScatterConfigWidget(QWidget):
    parametersChanged = Signal(ScatterParameters)
    params_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.properties = [  # List of properties for selection
            "area", "perimeter", "eccentricity", "solidity",
            "aspect_ratio", "circularity", "major_axis_length",
            "minor_axis_length", "mean_intensity", "std_intensity",
            "compactness", "convexity", "curl", "volume"
        ]
        self.params = ScatterParameters(
            x_variable=self.properties[0],
            y_variable=self.properties[1],
            size_variable=None,  # Initial size is uniform
            color_variable=None,
            trendline="global",
            marginal_x="box",
            marginal_y="violin"
        )
        # Create UI elements
        self.create_variable_selectors()
        self.create_size_selector()
        self.create_color_selector()
        self.create_trendline_selector()
        self.create_marginal_selectors()

        # Arrange layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.variables_group)
        main_layout.addWidget(self.size_group)
        main_layout.addWidget(self.color_group)
        main_layout.addWidget(self.trendline_group)
        main_layout.addWidget(self.marginals_group)

        main_layout.addStretch()
        self.setLayout(main_layout)

        # Connections
        self.x_variable.currentTextChanged.connect(self.emit_parameters_changed)
        self.y_variable.currentTextChanged.connect(self.emit_parameters_changed)
        self.size_variable.currentTextChanged.connect(self.emit_parameters_changed)
        self.color_variable.currentTextChanged.connect(self.emit_parameters_changed)
        self.trendline_type.buttonClicked.connect(self.emit_parameters_changed)
        self.marginal_x.currentTextChanged.connect(self.emit_parameters_changed)
        self.marginal_y.currentTextChanged.connect(self.emit_parameters_changed)

    def create_variable_selectors(self):
        self.variables_group = QGroupBox("Select Variables")
        layout = QGridLayout()
        self.x_variable = QComboBox()
        self.x_variable.addItems(self.properties)
        self.y_variable = QComboBox()
        self.y_variable.addItems(self.properties)
        layout.addWidget(QLabel("X Variable:"), 0, 0)
        layout.addWidget(self.x_variable, 0, 1)
        layout.addWidget(QLabel("Y Variable:"), 1, 0)
        layout.addWidget(self.y_variable, 1, 1)
        self.variables_group.setLayout(layout)

    def create_size_selector(self):
        self.size_group = QGroupBox("Marker Sizing")
        layout = QHBoxLayout()
        self.size_variable = QComboBox()
        self.size_variable.addItem("Uniform")  # For uniform marker size
        self.size_variable.addItems(self.properties)
        layout.addWidget(QLabel("Size Variable"), 0)
        layout.addWidget(self.size_variable, 1)
        self.size_group.setLayout(layout)

    def create_color_selector(self):
        self.color_group = QGroupBox("Coloring")
        layout = QHBoxLayout()
        self.color_variable = QComboBox()
        self.color_variable.addItem("None")  # For no coloring
        self.color_variable.addItems(["Class", "Cluster"])  # For coloring based on groups
        layout.addWidget(QLabel("Color Variable:"), 0)
        layout.addWidget(self.color_variable, 1)

        self.color_group.setLayout(layout)

    def create_trendline_selector(self):
        self.trendline_group = QGroupBox("Trendline")
        layout = QHBoxLayout()

        self.none_radio = QRadioButton("None")
        self.global_radio = QRadioButton("Global")
        self.group_radio = QRadioButton("Per Group")  # Include option for grouped trends

        self.trendline_type = QButtonGroup()
        self.trendline_type.addButton(self.none_radio)
        self.trendline_type.addButton(self.global_radio)
        self.trendline_type.addButton(self.group_radio)

        layout.addWidget(self.none_radio)
        layout.addWidget(self.global_radio)
        layout.addWidget(self.group_radio)  # Add the grouped trend option
        self.trendline_group.setLayout(layout)

    def create_marginal_selectors(self):
        self.marginals_group = QGroupBox("Marginal Distributions")
        layout = QGridLayout()
        self.marginal_x = QComboBox()
        self.marginal_x.addItems(["None", "rug", "box", "violin", "histogram"])
        self.marginal_y = QComboBox()
        self.marginal_y.addItems(["None", "rug", "box", "violin", "histogram"])
        layout.addWidget(QLabel("X Marginal:"), 0, 0)
        layout.addWidget(self.marginal_x, 0, 1)
        layout.addWidget(QLabel("Y Marginal:"), 1, 0)
        layout.addWidget(self.marginal_y, 1, 1)
        self.marginals_group.setLayout(layout)

    def emit_parameters_changed(self):
        """Emits the parametersChanged signal with current settings."""
        self.params.x_variable = self.x_variable.currentText()
        self.params.y_variable = self.y_variable.currentText()

        selected_size = self.size_variable.currentText()
        self.params.size_variable = selected_size if selected_size != "Uniform" else None

        selected_color = self.color_variable.currentText()
        self.params.color_variable = selected_color if selected_color != "None" else None

        checked_button = self.trendline_type.checkedButton()
        self.params.trendline = checked_button.text().lower() if checked_button else None  # None for no trendline
        # Handle the grouped trendline type

        self.params.marginal_x = self.marginal_x.currentText().lower() if self.marginal_x.currentText() != 'None' else None
        self.params.marginal_y = self.marginal_y.currentText().lower() if self.marginal_y.currentText() != 'None' else None

        self.params_changed.emit()

    def get_parameters(self):
        """Returns the current parameters."""
        return self.params