from google.appengine.api import images
from google.appengine.ext import blobstore
from google.appengine.ext import db


class Image(db.Model):
    """A "triangulized" image. Stores a reference to the image data in the
    blobstore and metadata about the image.
    """
    blob_key = blobstore.BlobReferenceProperty()
    source_url = db.LinkProperty()
    width = db.IntegerProperty()
    height = db.IntegerProperty()
    tile_size = db.IntegerProperty()

    created_at = db.DateTimeProperty(auto_now_add=True)
    updated_at = db.DateTimeProperty(auto_now=True)

    @property
    def url(self):
        return images.get_serving_url(self.blob_key)
