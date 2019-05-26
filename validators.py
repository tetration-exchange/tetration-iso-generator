from werkzeug.datastructures import FileStorage
from wtforms.validators import ValidationError


class FileSize(object):
    """Validates that the uploaded file is within a minimum and maximum file size (set in bytes).
    :param min_size: minimum allowed file size (in bytes). Defaults to 0 bytes.
    :param max_size: maximum allowed file size (in bytes).
    :param message: error message
    You can also use the synonym ``file_size``.
    """

    def __init__(self, max_size, min_size=0, message=None):
        self.min_size = min_size
        self.max_size = max_size
        self.message = message

    def __call__(self, form, field):
        if not (isinstance(field.data, FileStorage) and field.data):
            return

        file_size = len(field.data.read())
        field.data.seek(0)  # reset cursor position to beginning of file

        if (file_size < self.min_size) or (file_size > self.max_size):
            # the file is too small or too big => validation failure
            raise ValidationError(self.message or field.gettext('File must be between {min_size} and {max_size} bytes.'.format(min_size=self.min_size, max_size=self.max_size)))
