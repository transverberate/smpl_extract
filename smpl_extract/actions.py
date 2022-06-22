
import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))

from functools import wraps
from io import BufferedReader
from typing import Callable 
from typing import List
from typing import Union

from akai.image import AkaiImageParser
from alcohol.mdf import is_mdf_image
from alcohol.mdf import MdfStream
from alcohol.mdx import is_mdx_image
from alcohol.mdx import MdxStream
from cdda.image import CompactDiskAudioImageAdapter
from cuesheet import BadCueSheet
from cuesheet import parse_cue_sheet
from elements import ErrorInvalidPath
from elements import ExportManager
from elements import Image
from roland.s7xx.image import RolandSxxImageParser
from roland.s7xx.image import is_roland_s7xx_image


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

    if is_roland_s7xx_image(file_stream):
        result = RolandSxxImageParser(file_stream)
    else:
        result = AkaiImageParser(file_stream)
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
    def inner(file: Union[str, Image], *args, **kwargs):
        if isinstance(file, str):
            result = determine_image_type(file)
        else:
            result = file
        func(result, *args, **kwargs)
    return inner


@_wrap_filestream
def ls_action(image: Image, path: str):
    try:
        item = image.parse_path(path)
    except ErrorInvalidPath as e:
        print(e)
        return

    info = item.get_info()
    result_str = info.to_string()
    print(result_str)


@_wrap_filestream
def export_samples_to_wav(image: Image, base_dir: str):

    routines = {
        "combine_stereo": image.combine_stereo_routine
    }

    export_manager = ExportManager(base_dir, routines)
    image.export_samples(export_manager)
    return

