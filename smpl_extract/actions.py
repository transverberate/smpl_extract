
import os, sys

from smpl_extract.base import ElementTypes
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))

from functools import wraps
from io import BufferedReader
import re
from typing import Callable 
from typing import cast
from typing import List
from typing import Union

from akai.sample import Sample
from akai.image import AkaiImage
from alcohol.mdf import is_mdf_image
from alcohol.mdf import MdfStream
from alcohol.mdx import is_mdx_image
from alcohol.mdx import MdxStream
from cdda.cdda import CompactDiskAudioImage
from cdda.cdda import CompactDiskAudioImageAdapter
from cuesheet import BadCueSheet
from cuesheet import parse_cue_sheet
from elements import ErrorInvalidPath
from elements import Traversable
from wav.akai import WavAkaiSampleStruct
from wav.cdda import WavCddaSampleStruct


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
    cue_sheet_file = parse_cue_sheet(lines)
    binary_track = next(
        (x for x in cue_sheet_file.tracks if x.mode.lower() != "audio"),
        None
    )
    if binary_track:
        bin_file_path = os.path.join(directory, cue_sheet_file.bin_file_name)
        bin_file_stream = open(bin_file_path, "rb")
        bin_image = determine_image_type(bin_file_stream)
        return bin_image
    
    if all((x.mode.lower() == "audio" for x in cue_sheet_file.tracks)):
        bin_file_path = os.path.join(directory, cue_sheet_file.bin_file_name)
        bin_file_stream = open(bin_file_path, "rb")
        image = CompactDiskAudioImageAdapter.from_bin_cue(
            bin_file_stream,
            cue_sheet_file
        )
        return image
    
    raise BadCueSheet


def _wrap_filestream(func: Callable):
    @wraps(func)
    def inner(file: Union[str, Traversable], *args, **kwargs):
        if isinstance(file, str):
            result = determine_image_type(file)
        else:
            result = file
        func(result, *args, **kwargs)
    return inner


@_wrap_filestream
def ls_action(image: Traversable, path: str):
    try:
        item = image.parse_path(path)
    except ErrorInvalidPath as e:
        print(e)
        return

    info = item.get_info()
    result_str = info.to_string()
    print(result_str)


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
        result = name.replace(":", "")
        match = _SAFE_ENDING.match(result)
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
def export_samples_to_wav(image: Traversable, base_dir: str):

    if isinstance(image, CompactDiskAudioImage):
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        for track in image.tracks:
            file_name = track.title + ".wav"
            file_path = os.path.join(base_dir, file_name)
            with open(file_path, "wb") as export_stream:
                WavCddaSampleStruct.build_stream(track, export_stream)
            print(f"Exported {file_name}")
        return

    kv_partition = {x.name: x for x in image.children}
    for partition_name, partition in kv_partition.items():
        partition = cast(Traversable, partition)
        kv_volume = {x.name: x for x in partition.children}
        
        for volume_name, volume in kv_volume.items():
            volume = cast(Traversable, volume)
            kv_files = {x.name: x for x in volume.children}
            neighboring_filenames = kv_files.keys()
            channel_pairs: List[str] = []
            for file_element_name, file_element in kv_files.items():

                if file_element.type_id == ElementTypes.SampleEntry:

                    alternate_sample = None
                    export_name = file_element_name
                    match = _STEREO_FILENAME.match(file_element_name)
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
                            alternate_sample = kv_files[alternate_name]
                            alternate_sample = cast(Sample, alternate_sample)
                            export_name = match.group(1)
                            channel_pairs.append(export_name)
                    
                    if file_element is not None:
                        file_element = cast(Sample, file_element)
                        channels = [file_element]
                        if alternate_sample is not None:
                            channels.append(alternate_sample)
                        
                        entry = ExportEntry(partition_name, volume_name, export_name, channels)
                        entry.export_file(image, base_dir)
                        path_levels = entry.get_file_path_levels()
                        path_levels[0] += ":"
                        full_path = "/".join(path_levels) + ".wav"
                        print(f"Exported {full_path}")

    return

