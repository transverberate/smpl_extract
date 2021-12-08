import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
from functools import wraps
import re
from typing import Callable, List, Tuple, Union

from akai.partition import Partition
from akai.file_entry import FileEntry
from akai.sample import Sample
from akai.image import AkaiImage, InvalidPathStr
from akai.data_types import FileType
from alcohol.mdf import is_mdf_image
from alcohol.mdf import MdfStream
from wav.akai import WavAkaiSampleStruct


def _wrap_filestream(func: Callable):
    @wraps(func)
    def inner(file: Union[str, AkaiImage], *args, **kwargs):
        if isinstance(file, str):
            fstream = open(file, "rb")
            if is_mdf_image(fstream):
                fstream = MdfStream(fstream)
            result = AkaiImage(fstream)
        else:
            result = file
        func(result, *args, **kwargs)
    return inner


_PRINT_COLUMN_WIDTH = 20
@_wrap_filestream
def ls_action(image: AkaiImage, path: str):
    try:
        item = image.get_node_from_path(path)
    except InvalidPathStr as e:
        print(e)
        return

    entry_table: List[Tuple[str, str]] = []
    header = "{}{}".format(
        "Item".ljust(_PRINT_COLUMN_WIDTH), 
        "Type".ljust(_PRINT_COLUMN_WIDTH)
    )

    if hasattr(item, "children"):
        for child in item.children.values():
            name = child.name
            child.type
            if isinstance(child, Partition):
                name = name + ":"
            entry_table.append((name, child.type))
    elif isinstance(item, FileEntry):
        file = item.file
        if hasattr(file, "get_info"):
            if isinstance(file, Sample):
                header = "Sample".ljust(2 * _PRINT_COLUMN_WIDTH)
                info = file.get_info()
                for key, value in info.items():
                    entry_table.append((key, value))
    else:
        entry_table.append((item.name, item.type))
    if len(entry_table) < 1:
        print("(*empty*)")
        return
    # print table header
    print(header)
    # heading divider (spans 2 Columns)
    print("".join(["-"] * 2 * _PRINT_COLUMN_WIDTH))
    # print table entries
    for row in entry_table:
        print_entries = list(map(
            lambda i: row[i].ljust(_PRINT_COLUMN_WIDTH) if i < 2 
            else row[i].rjust(_PRINT_COLUMN_WIDTH), 
            range(len(row))
        ))
        print("".join(print_entries))


@_wrap_filestream
def write_wave_out(image: AkaiImage, file_path: str, channels: List[Sample]):
    with open(file_path, "wb") as export_stream:
        WavAkaiSampleStruct.build_stream(channels, export_stream)
    return


_SAFE_ENDING = re.compile(r"(.+?)\s*\.?\s*$")
class ExportEntry:

    def __init__(
        self,
        partition: str,
        volume: str,
        file: str,
        channels: List[Sample]
    ):
        self.partition = self.sanitize_name(partition)
        self.volume = self.sanitize_name(volume)
        self.file = self.sanitize_name(file)
        self.channels = channels

    
    def sanitize_name(self, name: str)->str:
        match = _SAFE_ENDING.match(name)
        if not match:
            raise Exception(f"Invalid name {name}")
        result = match.group(1)
        return result


    def get_file_path_levels(self)->List[str]:
        levels = [
            self.partition,
            self.volume,
            self.file
        ]
        return levels


    def ensure_directory(self, base: str, levels: List[str]):
        current_dir = base
        for i in range(max(0, len(levels)-1)):
            level = levels[i]
            current_dir = os.path.join(current_dir, level)
            if not os.path.exists(current_dir):
                os.makedirs(current_dir)

    
    def export_file(self, image_stream, base_dir: str):
        path_levels = self.get_file_path_levels()
        self.ensure_directory(base_dir, path_levels)
        file_path = os.path.join(base_dir, *path_levels)
        write_wave_out(image_stream, file_path + ".wav", self.channels)


_STEREO_FILENAME = re.compile(r"(.*?)([\s-]+)(L|R)\s*$")
@_wrap_filestream
def export_samples_to_wav(image: AkaiImage, base_dir: str):

    for partition_name, partition in image.children.items():
        for volume_name, volume in partition.children.items():
            neighboring_filenames = volume.children.keys()
            channel_pairs: List[str] = []
            for file_entry_name, file_entry in volume.children.items():

                if file_entry.file_type in (FileType.SAMPLE_S1000, FileType.SAMPLE_S3000):

                    alternate_sample = None
                    export_name = file_entry_name
                    match = _STEREO_FILENAME.match(file_entry_name)
                    if match:
                        if match.group(1) in channel_pairs:
                            continue
                        alternate_ending = "R" if match.group(3) == "L" else "L"
                        alternate_name = "".join((
                            match.group(1), 
                            match.group(2), 
                            alternate_ending
                        ))
                        if alternate_name in neighboring_filenames:
                            alternate_sample = volume.children[alternate_name].file
                            export_name = match.group(1)
                            channel_pairs.append(export_name)
                    
                    if file_entry.file is not None:
                        channels = [file_entry.file]
                        if alternate_sample is not None:
                            channels.append(alternate_sample)
                        
                        entry = ExportEntry(partition_name, volume_name, export_name, channels)
                        entry.export_file(image, base_dir)
                        path_levels = entry.get_file_path_levels()
                        path_levels[0] += ":"
                        full_path = "/".join(path_levels) + ".wav"
                        print(f"Exported {full_path}")

