# UI/navigation_interface/workspace/views/analysis/chart_configurations/histogram_config_widget.py

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLabel,
    QGroupBox, QSpinBox, QCheckBox, QRadioButton, QButtonGroup
)
from UI.navigation_interface.workspace.views.analysis.chart_configurations.parameter_holders import HistogramParameters


class HistogramConfigWidget(QWidget):
    params_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Store properties
        self.properties = [
            "area",
            "perimeter",
            "eccentricity",
            "solidity",
            "aspect_ratio",
            "circularity",
            "major_axis_length",
            "minor_axis_length",
            "mean_intensity",
            "std_intensity",
            "compactness",
            "convexity",
            "curl",
            "volume"
        ]
        self.default_params = HistogramParameters(
            x_variable=self.properties[0],
            num_bins=10,
            show_mean=True,
            relative_frequency=False,
            layered=False
        )

        # Create UI elements
        self.create_x_variable_selector()
        self.create_num_bins_selector()
        self.create_show_mean_checkbox()
        self.create_relative_freq_checkbox()
        self.create_plot_type_selector()
        self.create_group_by_selector()

        # Arrange layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.x_variable_group)
        main_layout.addWidget(self.num_bins_group)
        main_layout.addWidget(self.show_mean_checkbox)
        main_layout.addWidget(self.relative_freq_checkbox)
        main_layout.addWidget(self.plot_type_group)
        main_layout.addWidget(self.group_by_group)
        main_layout.addStretch()

        self.setLayout(main_layout)

        # Connect signals to handlers
        self.x_variable_combobox.currentTextChanged.connect(self.on_x_variable_changed)
        self.num_bins_spinbox.valueChanged.connect(self.on_num_bins_changed)
        self.show_mean_checkbox.stateChanged.connect(self.on_show_mean_changed)
        self.relative_freq_checkbox.stateChanged.connect(self.on_relative_freq_changed)
        self.plot_type_buttons.buttonClicked.connect(self.on_plot_type_changed)
        self.group_by_combobox.currentTextChanged.connect(self.on_group_by_changed)

        # Initialize group_by selector state
        self.update_group_by_visibility()

    def create_x_variable_selector(self):
        self.x_variable_group = QGroupBox("Select X Variable")
        layout = QHBoxLayout()
        self.x_variable_combobox = QComboBox()
        self.x_variable_combobox.addItems(self.properties)
        self.x_variable_combobox.setCurrentText(self.default_params.x_variable)
        layout.addWidget(QLabel("X-axis:"))
        layout.addWidget(self.x_variable_combobox)
        self.x_variable_group.setLayout(layout)

    def create_num_bins_selector(self):
        self.num_bins_group = QGroupBox("Number of Bins")
        layout = QHBoxLayout()
        self.num_bins_spinbox = QSpinBox()
        self.num_bins_spinbox.setRange(10, 1000)
        layout.addWidget(QLabel("Bins:"))
        layout.addWidget(self.num_bins_spinbox)
        self.num_bins_group.setLayout(layout)

    def create_show_mean_checkbox(self):
        self.show_mean_checkbox = QCheckBox("Show Global Mean")
        self.show_mean_checkbox.setChecked(self.default_params.show_mean)

    def create_relative_freq_checkbox(self):
        self.relative_freq_checkbox = QCheckBox("Relative Frequency")
        self.relative_freq_checkbox.setChecked(self.default_params.relative_frequency)

    def create_plot_type_selector(self):
        self.plot_type_group = QGroupBox("Plot Type")
        layout = QHBoxLayout()
        self.simple_radio = QRadioButton("Simple")
        self.layered_radio = QRadioButton("Layered")
        self.simple_radio.setChecked(not self.default_params.layered)
        self.layered_radio.setChecked(self.default_params.layered)

        # Group the radio buttons to ensure only one can be selected
        self.plot_type_buttons = QButtonGroup()
        self.plot_type_buttons.addButton(self.simple_radio)
        self.plot_type_buttons.addButton(self.layered_radio)

        layout.addWidget(self.simple_radio)
        layout.addWidget(self.layered_radio)
        self.plot_type_group.setLayout(layout)

    def create_group_by_selector(self):
        self.group_by_group = QGroupBox("Group By")
        layout = QHBoxLayout()
        self.group_by_combobox = QComboBox()
        self.group_by_combobox.addItems(["class", "cluster"])
        self.group_by_combobox.setCurrentIndex(-1)  # No selection by default
        layout.addWidget(QLabel("Group by:"))
        layout.addWidget(self.group_by_combobox)
        self.group_by_group.setLayout(layout)

    def on_x_variable_changed(self, text):
        self.default_params.x_variable = text
        self.emit_parameters_changed()

    def on_num_bins_changed(self, value):
        self.default_params.num_bins = value
        self.emit_parameters_changed()

    def on_show_mean_changed(self, state):
        self.default_params.show_mean = (state == Qt.Checked)
        self.emit_parameters_changed()

    def on_relative_freq_changed(self, state):
        self.default_params.relative_frequency = (state == Qt.Checked)
        self.emit_parameters_changed()

    def on_plot_type_changed(self, button):
        if button == self.layered_radio:
            self.default_params.layered = True
        else:
            self.default_params.layered = False
            self.default_params.group_by = None  # Reset group_by when not layered
            self.group_by_combobox.setCurrentIndex(-1)
        self.update_group_by_visibility()
        self.emit_parameters_changed()

    def on_group_by_changed(self, text):
        self.default_params.group_by = text if self.default_params.layered else None
        self.emit_parameters_changed()

    def update_group_by_visibility(self):
        if self.default_params.layered:
            self.group_by_group.setEnabled(True)
            if not self.default_params.group_by:
                self.group_by_combobox.setCurrentIndex(-1)  # Reset selection
        else:
            self.group_by_group.setEnabled(False)

    def emit_parameters_changed(self):
        self.params_changed.emit()

    def get_parameters(self):
        """Returns the current parameter settings for the histogram."""
        return HistogramParameters(
            x_variable=self.x_variable_combobox.currentText(),
            num_bins=self.num_bins_spinbox.value(),
            show_mean=self.show_mean_checkbox.isChecked(),
            relative_frequency=self.relative_freq_checkbox.isChecked(),
            layered=self.layered_radio.isChecked(),
            group_by=self.group_by_combobox.currentText() if self.layered_radio.isChecked() else None
        )