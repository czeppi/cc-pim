import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from typing import Tuple


class Zipper:

    def __init__(self, source_dpath: Path):
        self._source_dpath = source_dpath

    def start(self):
        source_dpath = self._source_dpath
        zip_fpath = str(source_dpath) + '.zip'
        with ZipFile(zip_fpath, 'x', compression=ZIP_DEFLATED, compresslevel=6) as zip_file:
            self._zip_dir_recursive(zip_file, source_dpath, Path())
        shutil.copystat(source_dpath, zip_fpath)

    def _zip_dir_recursive(self, zip_file: ZipFile, source_dpath: Path, rel_dpath: Path):
        for path in source_dpath.iterdir():
            rel_path = rel_dpath / path.name
            if path.is_dir():
                self._zip_write_dir(zip_file, path, rel_path)
                self._zip_dir_recursive(zip_file, path, rel_path)
            else:
                self._zip_write_file(zip_file, path, rel_path)

    def _zip_write_dir(self, zip_file: ZipFile, source_dpath: Path, rel_dpath: Path):
        # print(f'{rel_dpath}...')
        dt_tuple = self._get_datetime_tuple(source_dpath)

        # zip_info = ZipInfo(str(rel_dpath) + '/', dt_tuple)
        zip_info = ZipInfo.from_file(source_dpath, arcname=str(rel_dpath) + '/')
        zip_info.compress_type = ZIP_DEFLATED
        zip_info.date_time = dt_tuple

        zip_file.writestr(zip_info, b'')

    def _zip_write_file(self, zip_file: ZipFile, source_fpath: Path, rel_fpath: Path):
        with source_fpath.open('rb') as fh:
            dt_tuple = self._get_datetime_tuple(source_fpath)
            # print(f'rel_fpath={rel_fpath}')
            zip_info = ZipInfo(str(rel_fpath), dt_tuple)
            zip_info.compress_type = ZIP_DEFLATED

            data = fh.read()
            zip_file.writestr(zip_info, data)

    @staticmethod
    def _get_datetime_tuple(path: Path) -> Tuple[int, int, int, int, int, int]:
        mtime: float = path.stat().st_mtime
        utc = datetime.utcfromtimestamp(mtime)
        return utc.year, utc.month, utc.day, utc.hour, utc.minute, utc.second


class Unzipper:

    def __init__(self, zip_fpath: Path):
        self._zip_fpath = zip_fpath

    def start(self):
        zip_fpath = self._zip_fpath
        target_dpath = zip_fpath.parent / zip_fpath.stem
        target_dpath.mkdir()
        with ZipFile(zip_fpath, 'r') as zip_file:
            zip_file.extractall(target_dpath)
            for zip_info in zip_file.infolist():
                self.adapt_mtime(target_dpath, zip_info)
        shutil.copystat(zip_fpath, target_dpath)

    @staticmethod
    def adapt_mtime(dpath: Path, zip_info: ZipInfo):
        path = dpath / zip_info.filename
        year, month, day, hour, minute, second = zip_info.date_time
        dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
        atime = mtime = dt.timestamp()
        # print(f'{path}, {hour}:{minute}:{second} {day}.{month}.{year}')
        os.utime(path, times=(atime, mtime))
