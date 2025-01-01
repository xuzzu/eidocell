import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from numpy.distutils.fcompiler import pg
from qfluentwidgets import PrimaryPushButton

from UI.dialogs.custom_info_bar import CustomInfoBar, InfoBarPosition
from UI.dialogs.plot_view_widget import PlotViewerWidget
from UI.navigation_interface.workspace.views.analysis.analysis_card import AnalysisCard
from UI.navigation_interface.workspace.views.analysis.chart_creation_dialog import ChartCreationDialog
from UI.utils.flow_gallery import FlowGallery
from backend.plot_generator import PlotGenerator

class AnalysisViewWidget(QWidget):
    """Widget for the analysis view, displaying charts and segmentation results."""

    def __init__(self, main_window_reference, parent=None):
        super().__init__(parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.buttonLayout = QHBoxLayout()
        self.createChartButton = PrimaryPushButton("Create Chart", self)
        self.runSegmentationButton = PrimaryPushButton("Run Segmentation", self)
        self.gallery = FlowGallery(self)

        # link to the main window
        self.main_window_reference = main_window_reference
        self.analysis_presenter = None
        self.plot_generator = None

        self.__initWidget()

    def __initWidget(self):
        """Initialize the layout and appearance of the analysis view."""
        self.vBoxLayout.setContentsMargins(30, 20, 30, 30)  # Adjust margins as needed
        self.vBoxLayout.addLayout(self.buttonLayout)
        self.vBoxLayout.addWidget(self.gallery)

        self.buttonLayout.addWidget(self.createChartButton)
        self.buttonLayout.addWidget(self.runSegmentationButton)
        self.buttonLayout.setAlignment(Qt.AlignHCenter)

        # Connect buttons to placeholder functions
        self.createChartButton.clicked.connect(self.openChartCreationDialog)
        self.runSegmentationButton.clicked.connect(self.runSegmentation)

    def set_presenter(self, analysis_presenter):
        self.analysis_presenter = analysis_presenter
        self.plot_generator = PlotGenerator(self.analysis_presenter.data_manager)
        # self.analysis_presenter.layout_updater_thread.card_added.connect(self.add_card_to_layout)

    def openChartCreationDialog(self):
        """Open the chart creation dialog."""
        if not all([image.mask_id is not None for image in self.analysis_presenter.data_manager.samples.values()]):
            CustomInfoBar.error(
                title='Masks required',
                content=f"Please extract masks for all images before creating charts.",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=1500,
                parent=self.main_window_reference
            )
            return

        dialog = ChartCreationDialog(self.analysis_presenter.data_manager, self.main_window_reference)
        if dialog.exec():
            # Handle chart creation here based on the dialog's selections
            print("Chart creation dialog accepted!")
            selected_chart_type = dialog.chartTypeSelector.currentRouteKey()
            print(f"Selected Chart Type: {selected_chart_type}")
            self.create_analysis_card(dialog)

    def runSegmentation(self):
        """Placeholder function for running image segmentation."""
        print("Run Segmentation button clicked!")

    def create_analysis_card(self, dialog: ChartCreationDialog):
        """Creates an AnalysisCard with embedded QWebEngineView."""
        selected_chart_type = dialog.chartTypeSelector.currentRouteKey()
        parameters = dialog.get_chart_parameters(selected_chart_type)

        if parameters is None:
            return

        plot_name = parameters.x_variable
        plot_png_path, plot_html_path = self.plot_generator.generate_plot(selected_chart_type, parameters, plot_name) # Pass the plot name

        if plot_html_path:
            card = AnalysisCard(plot_html_path, self)  # Pass HTML file path to the card
            self.gallery.flow_layout.addWidget(card)
            card.doubleClicked.connect(self.open_plot_viewer) # Correct signal connection
            card.deleteRequested.connect(lambda: self.delete_analysis_card(card))

    def open_plot_viewer(self, html_file_path):
        """Opens the PlotViewerWidget."""
        absolute_html_path = os.path.abspath(html_file_path)  # Get the absolute path
        self.plot_viewer = PlotViewerWidget(absolute_html_path, self)  # Use the absolute path
        self.plot_viewer.show()

    def delete_analysis_card(self, card: AnalysisCard):
        """Removes the specified AnalysisCard from the layout."""
        self.gallery.flow_layout.removeWidget(card)
        card.deleteLater()
