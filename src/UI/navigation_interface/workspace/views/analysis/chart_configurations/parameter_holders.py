from dataclasses import dataclass
from typing import Optional


@dataclass
class HistogramParameters:
    x_variable: str
    num_bins: int
    show_mean: bool
    relative_frequency: bool
    layered: bool
    group_by: Optional[str] = None  # 'class' or 'cluster'

    def get_data(self, data_manager):
        """Retrieves data from the DataManager based on the parameters."""
        x_data = []
        group_data = []

        for image in data_manager.samples.values():
            if image.mask_id: # Check if mask exists
                try:
                    x_data.append(data_manager.masks[image.mask_id].attributes[self.x_variable])
                    if self.group_by == "class":
                        group_data.append(data_manager.classes[image.class_id].name if image.class_id else "Uncategorized")
                    elif self.group_by == "cluster":
                        cluster = next((c for c in data_manager.clusters.values() if image in c.samples), None)
                        group_data.append(cluster.id[:8] if cluster else "No Cluster")  # Shorten cluster ID
                    else: # Simple plot - group data by image id for compatibility.
                        group_data.append(image.id)
                except KeyError:
                    print(f"Warning: Property '{self.x_variable}' not found for image {image.id}. Skipping.")

        return x_data, group_data

@dataclass
class ScatterParameters:
    x_variable: str
    y_variable: str
    size_variable: Optional[str]
    color_variable: Optional[str] #None, Class, or Cluster
    trendline: Optional[str] #global, per group, or none
    marginal_x: Optional[str]
    marginal_y: Optional[str]

    def get_data(self, data_manager):
        """Retrieve data for scatter plot."""
        x_data = []
        y_data = []
        size_data = []
        color_data = []

        for image in data_manager.samples.values():
            if image.mask_id:
                try:
                    x_data.append(data_manager.masks[image.mask_id].attributes[self.x_variable])
                    y_data.append(data_manager.masks[image.mask_id].attributes[self.y_variable])

                    if self.size_variable:
                        size_data.append(data_manager.masks[image.mask_id].attributes[self.size_variable])
                    else:
                        size_data.append(1) # Uniform size


                    if self.color_variable == "Class":
                        color_data.append(data_manager.classes[image.class_id].name if image.class_id else "Uncategorized")

                    elif self.color_variable == "Cluster":
                        cluster = next((c for c in data_manager.clusters.values() if image in c.samples), None)
                        color_data.append(cluster.id[:8] if cluster else "No Cluster") # Shorten cluster ID

                    else:  # No coloring
                        color_data.append("All data")

                except KeyError as e:
                    print(f"Warning: Property '{e}' not found for image {image.id}. Skipping.")
        return x_data, y_data, size_data, color_data