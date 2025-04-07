# MIT License
#
# Copyright (C) 2024 The Little Hackers.  All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from io import BytesIO
from pathlib import Path
from typing import Any

import exifread

EXIF_TAG_EXPOSURE_TIME = 0x829A
EXIF_TAG_F_NUMBER = 0x829D
EXIF_TAG_FOCAL_LENGTH = 0x920A
EXIF_TAG_ISO_SPEED_RATINGS = 0x8827
EXIF_TAG_ORIENTATION = 0x0112


# def __search_exif_tag_value(
#         exif_tags,
#         tag_subname,
#         optional=False,
#         default_value=None
# ):
#     for tag_name, tag_value in exif_tags.items():
#         offset = tag_name.find(tag_subname)
#         if offset == -1 or \
#            (offset > 0 and tag_name[offset - 1] != ' ') or \
#            (offset + len(tag_subname) < len(tag_name) and tag_name[offset + len(tag_subname)] != ' '):
#             continue
#
#         return tag_value
#
#     if not optional:
#         raise KeyError('Undefined key with subname "%s"' % tag_subname)
#
#     return default_value


def __extract_exif_tags(file: BytesIO | Path) -> dict[str, Any]:
    """
    Extract Exif metadata tags from an image file.


    :param file: A file-like object or a file path representing the image
        file.


    :return: A dictionary mapping Exif tag names to their corresponding
        values.


    :raise ValueError: If `file` is neither a `BytesIO` nor a `Path`
        object.
    """
    if isinstance(file, Path):
        with open(file, 'rb') as handle:
            exif_tags = exifread.process_file(handle)
    elif isinstance(file, BytesIO):
        file.seek(0)
        exif_tags = exifread.process_file(file)
    else:
        raise ValueError(
            "Invalid file type: expected a file-like object (`BytesIO`) or a file "
            f"path (`Path`), but received {type(file).__name__}."
        )

    return exif_tags


def get_photo_capture_time(
        file: BytesIO | Path,
        strict: bool = True
) -> datetime | None:
    """
    Retrieve the capture time of a photo from its Exif metadata.


    :param file: A file-like object (e.g., an in-memory bytes buffer)
        representing the photo's image file.

    :param strict: If `True`, raises a `ValueError` when the capture time
        is missing from the Exif metadata.

    :return: The capture time of the photo if defined in the Exif metadata
        of the photo.  If the Exif tag representing the time difference
        from Universal Time Coordinated is present, the capture time will
        be timezone-aware; otherwise, it remains naive.  Returns `None` if
        the capture time is unavailable.


    :raise ValueError: If the capture time is missing, while the argument
        `strict` is `True`, or improperly formatted in the Exif metadata.
    """
    exif_tags = __extract_exif_tags(file)

    # Extract the date and time when the photo was captured.  Some cameras
    # may include the Exif `OffsetTimeOriginal` tag, which specifies the
    # time zone offset (e.g., `+07:00` or `-05:00`).
    exif_datetime = exif_tags.get('EXIF DateTimeOriginal')
    exif_offset = exif_tags.get('EXIF OffsetTimeOriginal')

    if exif_datetime:
        try:
            # Convert the Exif date string to a naive datetime object.
            capture_time = datetime.strptime(str(exif_datetime), "%Y:%m:%d %H:%M:%S")

            if exif_offset:
                # Convert the Exif offset string to a timezone-aware datetime.
                offset_str = str(exif_offset).strip()
                sign = 1 if offset_str.startswith("+") else -1
                hours, minutes = map(int, offset_str[1:].split(":"))
                tz_offset = timedelta(hours=hours, minutes=minutes) * sign
                capture_time = capture_time.replace(tzinfo=timezone(tz_offset))
        except ValueError:
            raise ValueError("Invalid date format in Exif metadata")
    else:
        if strict:
            raise ValueError("The photo does not contain capture date and time information")
        capture_time = None

    return capture_time


# def get_photo_location(file: BytesIO | Path):
#     """
#     Parse out the GPS coordinates from the Exif tags of a photo file.
#
#
#     @param file: Path and file name of a photo's image, or an object
#         `BytesIO` (in-memory bytes buffer) of the photo's image file, to
#         retrieve the GPS coordinates of the location where the photo has
#         been captured.
#
#
#     @return: An object `GeoPoint` representing the geographical location
#         where the photo has been captured, or `None` if the photo's image
#         file doesn't contain an Exif tag that indicates where the photo
#         has been captured.
#     """
#     exif_tags = __extract_exif_tags(file)
#
#     try:
#         lat_dms = __search_exif_tag_value(exif_tags, 'GPSLatitude').values  # GPS GPSLatitude
#         latitude = GeoPoint.convert_dms_to_dd(
#             lat_dms[0].num, lat_dms[0].den,
#             lat_dms[1].num, lat_dms[1].den,
#             lat_dms[2].num, lat_dms[2].den)
#         if __search_exif_tag_value(exif_tags, 'GPSLatitudeRef').printable == 'S':
#             latitude *= -1
#
#         long_dms = __search_exif_tag_value(exif_tags, 'GPSLongitude').values  # GPS GPSLongitude
#         longitude = GeoPoint.convert_dms_to_dd(
#                 long_dms[0].num, long_dms[0].den,
#                 long_dms[1].num, long_dms[1].den,
#                 long_dms[2].num, long_dms[2].den)
#         if __search_exif_tag_value(exif_tags, 'GPSLongitudeRef').printable == 'W':
#             longitude *= -1
#     except KeyError:
#         return None
#
#     try:
#         acc = __search_exif_tag_value(exif_tags, 'GPSHPositioningError').values[0]
#         accuracy = float(acc.num) / acc.den
#     except KeyError:
#         accuracy = None
#
#     # Retrieve the altitude of the location where this photo has been
#     # taken, if defined.
#     try:
#         alt = __search_exif_tag_value(exif_tags, 'GPSAltitude').values[0]
#         altitude = float(alt.num) / alt.den
#         if __search_exif_tag_value(exif_tags, 'GPS GPSAltitudeRef') == 1:
#             altitude *= -1
#     except KeyError:
#         altitude = None
#
#     # Retrieve the angle of the direction that the camera points to,
#     # either from the EXIF GPS tag ``GPSDestBearing``, or the tag
#     # ``GPSImgDirection``, in this preference order, when available.
#     try:
#         _bearing_tag = __search_exif_tag_value(exif_tags, 'GPSDestBearing', optional=True)
#         if _bearing_tag:
#             _bearing_ = _bearing_tag.values[0]
#             bearing = float(_bearing_.num) / _bearing_.den
#         else:
#             _bearing_ = __search_exif_tag_value(exif_tags, 'GPSImgDirection').values[0]
#             bearing = float(_bearing_.num) / _bearing_.den
#             if __search_exif_tag_value(exif_tags, 'GPSImgDirectionRef').printable == 'T':
#                 bearing += 180
#     except KeyError:
#         bearing = None
#
#     # Retrieve the date and the time of the location fix.
#     try:
#         _date_ = __search_exif_tag_value(exif_tags, 'GPSDate').values.replace(':', '-')
#         _time_ = __search_exif_tag_value(exif_tags, 'GPSTimeStamp').values
#
#         _date_time_ = '%sT%02d:%02d:%02d+00' % \
#                 (_date_, _time_[0].num, _time_[1].num, float(_time_[2].num) / _time_[2].den)
#
#         fix_time = cast.string_to_timestamp(_date_time_)
#     except KeyError:
#         fix_time = None
#
#     # Build a geo-point with the information collected.
#     return GeoPoint(
#         latitude,
#         longitude,
#         accuracy=accuracy,
#         altitude=altitude,
#         bearing=bearing,
#         fix_time=fix_time
#     )
