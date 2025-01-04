# backend/objects/mask.py


class Mask:
    def __init__(self, id, image_id, path, attributes=None, masked_image_path=None, masked_image=None):
        self.id = id
        self.image_id = image_id
        self.path = path
        self.attributes = attributes if attributes else {}
        self.masked_image_path = masked_image_path
        self.masked_image = masked_image

    def to_dict(self):
        return {
            "id": self.id,
            "image_id": self.image_id,
            "path": self.path,
            "attributes": self.attributes,
            "masked_image_path": self.masked_image_path
        }

    @staticmethod
    def from_dict(data):
        return Mask(
            id=data["id"],
            image_id=data["image_id"],
            path=data["path"],
            attributes=data.get("attributes", {}),
            masked_image_path=data.get("masked_image_path")
        )
