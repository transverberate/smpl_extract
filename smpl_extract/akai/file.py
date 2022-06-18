import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))

from construct.core import ConstructError
from construct.core import Subconstruct
from construct.core import Switch
from construct.expr import this

from .data_types import FileType
from .data_types import InvalidCharacter
from .data_types import FileType
from .program import ProgramParser
from .sample import SampleAdapter
from .sample import SampleHeaderConstruct
from util.fat import RequestedInvalidSector


FileConstruct = Switch(
    this.type,
    {
        FileType.SAMPLE_S1000:  SampleAdapter(SampleHeaderConstruct),
        FileType.SAMPLE_S3000:  SampleAdapter(SampleHeaderConstruct),
        FileType.PROGRAM_S1000: ProgramParser,
        FileType.PROGRAM_S3000: ProgramParser
    }
)


class FileAdapter(Subconstruct):


    def __init__(self, sat, subcon):
        super().__init__(subcon)  # type: ignore
        self.sat = sat
        self.flagbuildnone = True

    
    def _parse(self, stream, context, path):
        del path  # Unused
        try:
            file = FileConstruct.parse_stream(
                stream, 
                **context
            )
        except (RequestedInvalidSector, InvalidCharacter) as e:
            raise ConstructError from e

        return file


    def _build(self, obj, stream, context, path):
        raise NotImplementedError


    # Required for encapsulating Lazy Construct 
    def _sizeof(self, context, path):
        del context, path  # Unused
        return 0

