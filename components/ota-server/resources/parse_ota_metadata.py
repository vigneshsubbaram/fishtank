#!/usr/bin/env python3

"""Print OTA payload metadata."""

import argparse
import binascii
import logging
import struct
import sys
from typing import Literal
import zipfile


class AndroidOTAPackage(object):
  """Android update payload using the .zip format."""

  OTA_PAYLOAD_BIN = 'payload.bin'
  OTA_PAYLOAD_PROPERTIES_TXT = 'payload_properties.txt'
  SECONDARY_OTA_PAYLOAD_BIN = 'secondary/payload.bin'
  SECONDARY_OTA_PAYLOAD_PROPERTIES_TXT = 'secondary/payload_properties.txt'
  PAYLOAD_MAGIC_HEADER = b'CrAU'

  def __init__(self, otafilename, secondary_payload=False) -> None:
    self.otafilename = otafilename

    otazip = zipfile.ZipFile(otafilename, 'r')
    payload_entry = (self.SECONDARY_OTA_PAYLOAD_BIN if secondary_payload else
                     self.OTA_PAYLOAD_BIN)
    payload_info = otazip.getinfo(payload_entry)

    if payload_info.compress_type != 0:
      logging.error(
          "Expected payload to be uncompressed, got compression method %d",
          payload_info.compress_type)

    with open(otafilename, "rb") as fp:
      fp.seek(payload_info.header_offset)
      data = fp.read(zipfile.sizeFileHeader)
      fheader = struct.unpack(zipfile.structFileHeader, data)
      filename_len = fheader[-2]
      extra_len = fheader[-1]
      self.offset = payload_info.header_offset
      self.offset += zipfile.sizeFileHeader
      self.offset += filename_len + extra_len
      self.size = payload_info.file_size
      fp.seek(self.offset)
      payload_header = fp.read(4)
      if payload_header != self.PAYLOAD_MAGIC_HEADER:
        logging.warning(
            "Invalid header, expected %s, got %s. "
            "Either the offset is not correct, or payload is corrupted",
            binascii.hexlify(self.PAYLOAD_MAGIC_HEADER),
            binascii.hexlify(payload_header))

    property_entry = (self.SECONDARY_OTA_PAYLOAD_PROPERTIES_TXT if
                      secondary_payload else self.OTA_PAYLOAD_PROPERTIES_TXT)
    self.properties = otazip.read(property_entry)


def main() -> Literal[0]:
  parser = argparse.ArgumentParser(description='Print OTA payload metadata.')
  parser.add_argument('otafile', metavar='PAYLOAD', type=str,
                      help='the OTA package file (a .zip file)')
  parser.add_argument('--secondary', action='store_true',
                      help='Extract from the secondary payload in the package.')
  parser.add_argument('--extra-headers', type=str, default='',
                      help='Extra headers to include.')

  args = parser.parse_args()

  ota = AndroidOTAPackage(args.otafile, args.secondary)
  headers = ota.properties
  headers += args.extra_headers.encode()
  print(f"{ota.offset},{ota.size},{headers}")
  return 0


if __name__ == '__main__':
  sys.exit(main())
