
from functools import wraps
from io import BufferedReader
import os
from typing import Callable
from typing import Dict 
from typing import List
from typing import Union

from smpl_extract.akai.image import AkaiImageParser
from smpl_extract.alcohol.mdf import is_mdf_image
from smpl_extract.alcohol.mdf import MdfStream
from smpl_extract.alcohol.mdx import is_mdx_image
from smpl_extract.alcohol.mdx import MdxStream
from smpl_extract.cdda.image import CompactDiskAudioImageAdapter
from smpl_extract.cuesheet import BadCueSheet
from smpl_extract.cuesheet import parse_cue_sheet
from smpl_extract.roland.s7xx.image import RolandSxxImageParser
from smpl_extract.roland.s7xx.image import is_roland_s7xx_image
from smpl_extract.structural import ErrorInvalidPath
from smpl_extract.structural import ExportManager
from smpl_extract.structural import Image
from smpl_extract.structural import T_ROUTINE
from smpl_extract.structural import T_SAMPLE_ROUTINE


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

    routines: Dict[str, T_ROUTINE] = {
        "make_safe_names": image.make_safe_names_routine,
        "make_export_names": image.make_export_names_routine
    }

    image.set_routines(routines)

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

    routines: Dict[str, T_ROUTINE] = {
        "make_safe_names": image.make_safe_names_routine,
        "make_export_names": image.make_export_names_routine
    }
    sample_routines: Dict[str, T_SAMPLE_ROUTINE] = {
        "combine_stereo": image.combine_stereo_routine
    }

    image.set_routines(routines)
    export_manager = ExportManager(base_dir, sample_routines)
    image.export_samples(export_manager)
    return

