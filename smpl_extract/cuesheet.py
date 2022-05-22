import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))

from dataclasses import dataclass
from dataclasses import field
import re
from typing import List
from typing import Optional
from typing import Protocol
from typing import Tuple
from typing import TypeVar


class BadCueSheet(Exception): pass


def get_nonempty_entry(lines: List[str]) -> Tuple[str, List[str]]:
    text = ""
    while len(lines):
        text = lines.pop(0).strip()
        if len(text):
            break
    return text, lines


T = TypeVar("T", covariant=True)
class CueItemAdapter(Protocol[T]):
    def parse(self, lines: List[str]) -> T: ...


_AUDIO_FRAMES_PER_SECOND = 75
@dataclass
class CueSheetIndex:
    number: int = 0
    n_minutes: int = 0
    n_seconds: int = 0
    n_frames: int = 0

    def get_total_audio_frames(self) -> int:
        total_seconds = 60*self.n_minutes + self.n_seconds
        total_frames = _AUDIO_FRAMES_PER_SECOND*total_seconds + \
            self.n_frames
        return total_frames


@dataclass
class CueSheetTrack:
    number: int = 0
    mode: str = ""
    title: Optional[str] = None
    indices: List[CueSheetIndex] = field(default_factory=list)
    unparsed: List = field(default_factory=list)


_TRACK_LINE_REGEX = re.compile(r"\s*TRACK\s+(\d+)\s+([A-z\d\/]+)", flags=re.I)
_TITLE_LINE_REGEX = re.compile(r"\s*TITLE\s+\"(.*?)\"", flags=re.I)
_INDEX_LINE_REGEX = re.compile(r"\s*INDEX\s+(\d+)\s+(\d+):(\d+):(\d+)", flags=re.I)
class CueSheetTrackAdapter:
    @classmethod
    def parse(cls, lines: List[str]):
        text, lines = get_nonempty_entry(lines)
        if len(text) <= 0:
            raise BadCueSheet
        result = _TRACK_LINE_REGEX.match(text)
        if not result:
            raise BadCueSheet
        track_number = int(result.groups()[0])
        track_mode = result.groups()[1]
        track = CueSheetTrack(
            track_number,
            track_mode
        )

        while len(lines):
            text, lines = get_nonempty_entry(lines)
            if len(text) <= 0:
                break

            # Check if next track began
            result = _TRACK_LINE_REGEX.match(text)
            if result:
                lines = [text] + lines
                break

            # check known properties
            result = _INDEX_LINE_REGEX.match(text)
            if result:
                index_number = int(result.groups()[0])
                n_minutes = int(result.groups()[1])
                n_seconds = int(result.groups()[2])
                n_frames = int(result.groups()[3])
                index = CueSheetIndex(
                    index_number,
                    n_minutes,
                    n_seconds,
                    n_frames
                )
                track.indices.append(index)
                continue

            result = _TITLE_LINE_REGEX.match(text)
            if result:
                title = result.groups()[0]
                track.title = title
                continue

            track.unparsed.append(text)

        return track, lines


@dataclass
class CueSheetFile:
    bin_file_name: str
    tracks: List[CueSheetTrack] = field(default_factory=list)


_FILE_LINE_REGEX = re.compile(r"\s*FILE\s+\"(.*?)\"\s+BINARY", flags=re.I)
class CueSheetFileAdapter:


    @classmethod
    def parse(cls, lines: List[str]):
        text, lines = get_nonempty_entry(lines)
        if len(text) <= 0:
            raise BadCueSheet
        result = _FILE_LINE_REGEX.match(text)
        if not result:
            raise BadCueSheet
        
        bin_file_name = result.groups()[0]
        cue_sheet = CueSheetFile(bin_file_name)
        while len(lines):
            text, lines = get_nonempty_entry(lines)
            if len(text) <= 0:
                break
            lines = [text] + lines
            track, lines = CueSheetTrackAdapter.parse(lines)
            if track:
                cue_sheet.tracks.append(track)

        return cue_sheet, lines


def parse_cue_sheet(lines: List[str]) -> CueSheetFile:
    cue_sheet_files = []
    while len(lines):
        text, lines = get_nonempty_entry(lines)
        match_result = _FILE_LINE_REGEX.match(text)
        if match_result:
            lines = [text] + lines
            cue_sheet_file, lines = CueSheetFileAdapter.parse(lines)
            cue_sheet_files.append(cue_sheet_file)
    
    if len(cue_sheet_files) <= 0:
        raise BadCueSheet("No FILE entry")
    
    result = cue_sheet_files[0]
    return result

