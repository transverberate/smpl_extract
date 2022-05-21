
import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))

from dataclasses import dataclass
from functools import wraps
from io import BufferedReader
import re
from typing import Callable
from typing import List
from typing import Mapping
from typing import Tuple
from typing import Union
from typing import Sequence

from akai.partition import Partition
from akai.file_entry import FileEntry
from akai.sample import Sample
from akai.image import AkaiImage
from akai.image import InvalidPathStr
from akai.data_types import FileType
from alcohol.mdf import is_mdf_image
from alcohol.mdf import MdfStream
from alcohol.mdx import is_mdx_image
from alcohol.mdx import MdxStream
from cuesheet import BadCueSheet
from cuesheet import parse_cue_sheet
from util.dataclass import ItemT
from wav.akai import WavAkaiSampleStruct


class BadTextFile(Exception): pass


def parse_text_file(filename: str):
    with open(filename, "r", encoding="ascii") as file:
        try:
            text = file.readlines()
        except (UnicodeDecodeError) as e:
            raise BadTextFile from e
        return text


def determine_image_type(file: Union[str, BufferedReader]):
    if isinstance(file, str):
        is_textfile = True
        lines = []
        try:
            lines = parse_text_file(file)
        except BadTextFile:
            is_textfile = False

        if is_textfile:
            parent_directory = os.path.dirname(file)
            try: 
                result = attempt_parse_cue_sheet(lines, parent_directory)
                return result
            except BadCueSheet:
                pass

        file_stream = open(file, "rb")
    else:
        file_stream = file

    if is_mdf_image(file_stream):
        file_stream = MdfStream(file_stream)
    elif is_mdx_image(file_stream):
        file_stream = MdxStream(file_stream)

    result = AkaiImage(file_stream)
    return result


def attempt_parse_cue_sheet(lines: List[str], directory = ""):
    cue_sheet = parse_cue_sheet(lines)
    binary_track = next(
        (x for x in cue_sheet.tracks if x.mode.lower() != "audio"),
        None
    )
    if binary_track:
        bin_file_path = os.path.join(directory, cue_sheet.bin_file_name)
        bin_file_stream = open(bin_file_path, "rb")
        bin_image = determine_image_type(bin_file_stream)
        return bin_image
    
    raise BadCueSheet


def _wrap_filestream(func: Callable):
    @wraps(func)
    def inner(file: Union[str, AkaiImage], *args, **kwargs):
        if isinstance(file, str):
            result = determine_image_type(file)
        else:
            result = file
        func(result, *args, **kwargs)
    return inner


@_wrap_filestream
def ls_action(image: AkaiImage, path: str):
    try:
        item = image.get_node_from_path(path)
    except InvalidPathStr as e:
        print(e)
        return

    if isinstance(item, FileEntry):
        file = item.file
        if hasattr(file, "itemize"):
            result = file.itemize()
            print_tree((item.name, " "*2, item.type), result)
            return  # exit

    entries: Sequence[Tuple[str, ...]] = []
    
    if hasattr(item, "children"):
        for child in item.children.values():
            name = child.name
            if isinstance(child, Partition):
                name = name + ":"
            entries.append((name, child.type))

    if len(entries) < 1:
        print("(*empty*)")
        return  # exit

    # print table
    print_table(("Item", "Type"), entries)
    return


_TABLE_COLUMN_WIDTH = 20
_TABLE_COLUMN_DELIMITER = " "
def print_table(header: Tuple[str, ...], items: Sequence[Tuple[str, ...]]):
    # calc total number of columns and the widths of each
    num_columns = 0
    column_widths: Mapping[int, int] = {}
    for row in items:
        for i, column_value in enumerate(row):
            # total number of cols
            if i + 1 > num_columns:
                num_columns = i + 1
            # width of ith column
            width = len(column_value)
            if i not in column_widths.keys():
                column_widths[i] = max(width, _TABLE_COLUMN_WIDTH)
            elif width > column_widths[i]:
                column_widths[i] = width
    
    # total width is sum of column widths and the number of delimiters
    total_width = sum(column_widths.values()) + num_columns - 1
    
    def make_line(
            row: Tuple[str, ...], 
            column_widths: Mapping[int, int] = column_widths
    )->str:
        result = _TABLE_COLUMN_DELIMITER.join(map(
            lambda i: row[i].ljust(column_widths[i]), 
            range(len(row))
        ))
        return result

    # print the table
    print(make_line(header))  # header
    print("-" * total_width)  # divider
    for row in items:
        print(make_line(row))
    print()
    return


_TREE_TOTAL_WIDTH   = 80
_TREE_DELIMITER     = " "
_TREE_MAX_ROWS      = 300
def print_tree(header: Tuple[str, ...], items: ItemT):


    @dataclass
    class RowEntry:
        content: Tuple[str, ...] = ("", )
        depth: int = 0
        is_divider: bool = False


    row_entries: Sequence[RowEntry] = []


    def build_inner(item, depth=0, prev_key="", row_entries=row_entries):

        if isinstance(item, Sequence) or isinstance(item, Mapping):

            if isinstance(item, Sequence):
                kv_pair = (
                    ("".join((prev_key, f"[{str(i)}]")), value)
                    for i,value in enumerate(item)
                )
            else:
                kv_pair = item.items()

            for key, value in kv_pair:
                    content = [f"{key}:"]
                    if isinstance(value, str):
                        content.append(str(value))
                    elif len(value) == 0:
                        content.append("None")
                    row_entries.append(RowEntry(tuple(content), depth))
                    # expand value
                    if not isinstance(value, str):
                        build_inner(
                            value, 
                            depth=(depth + 1), 
                            prev_key=key, 
                            row_entries=row_entries
                        )


    row_entries.append(RowEntry(tuple(header)))
    row_entries.append(RowEntry(is_divider=True))  # divider
    build_inner(items)  # fill row_entries

    # print tree
    for i, row in enumerate(row_entries):
        if i > _TREE_MAX_ROWS:
            print()
            print(f"(...) exceeded {_TREE_MAX_ROWS} lines")
            break
        if row.is_divider:
            result = "-" * _TREE_TOTAL_WIDTH
            print(result)
            continue
        
        column_values = ((' ', ) * row.depth) + row.content 
        result = _TREE_DELIMITER.join(column_values)
        if len(result) > _TREE_TOTAL_WIDTH:
            result = result[0:_TREE_TOTAL_WIDTH-3] + "..." 
        print(result)
    print()
    
    return


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

