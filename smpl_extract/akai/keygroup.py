import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
sys.path.append(os.path.join(_SCRIPT_PATH, ".."))
from dataclasses import dataclass
from dataclasses import field
from dataclasses import fields
from typing import List
from typing import Sequence
from construct.core import Adapter
from construct.core import Check
from construct.core import Computed
from construct.core import ConstructError
from construct.core import Default
from construct.core import Int16sl
from construct.core import Int16ul
from construct.core import Int8sl
from construct.core import Int8ul
from construct.core import Padding
from construct.core import Struct
from construct.expr import len_
from construct.expr import this
from construct.lib.containers import Container

from .akai_string import AkaiPaddedString
from .data_types import AkaiLoopType
from .data_types import AkaiMidiNote
from .data_types import AkaiTuneCents
from midi import MidiNote
from util.constructs import BoolConstruct
from util.constructs import MappingDefault
from util.constructs import PaddedGeneral
from util.constructs import sanitize_container
from util.constructs import SlicingGeneral
from util.dataclass import itemizable


# Has a *different* mapping than the loop_mode_stored in samples
def ZoneLoopTypeAdapter(subcon):
    result = MappingDefault(
        subcon,
        {
            AkaiLoopType.AS_SAMPLE:             0,
            AkaiLoopType.LOOP_IN_RELEASE:       1,
            AkaiLoopType.LOOP_UNTIL_RELEASE:    2,
            AkaiLoopType.LOOP_INACTIVE:         3,
            AkaiLoopType.PLAY_TO_SAMPLE_END:    4
        },
        (AkaiLoopType.AS_SAMPLE, 0)
    )
    return result


@dataclass
class VelocityZoneCommon:
    sample_name:            str = ""
    low_velocity:           int =  0          
    high_velocity:          int = 127   
    tune_cents:             float = 0        
    tune_semitones:         int = 0    
    loudness_offset:        int = 0   
    filter_cutoff_offset:   int = 0     
    pan_offset:             int = 0         
    loop_mode:              AkaiLoopType = AkaiLoopType.AS_SAMPLE


@dataclass
class VelocityZoneContainer(VelocityZoneCommon, Container):
    pass


VelocityZoneConstruct = Struct(
    "sample_name"           /   AkaiPaddedString(12),
    "low_velocity"          /   Int8ul,
    "high_velocity"         /   Int8ul,
    "tune_cents"            /   AkaiTuneCents(Int8sl),
    "tune_semitones"        /   Int8sl,
    "loudness_offset"       /   Int8sl,
    "filter_cutoff_offset"  /   Int8sl,
    "pan_offset"            /   Int8sl,
    "loop_mode"             /   ZoneLoopTypeAdapter(Int8ul),
    Padding(2, pattern=b"\xFF"),
    Padding(1, pattern=b"\x2C"),
    Padding(1, pattern=b"\x01")
)


@dataclass
class KeygroupCommon:
    block_id:                           int = 2
    low_key:                            MidiNote = MidiNote.from_string("C0")
    high_key:                           MidiNote = MidiNote.from_string("G8")
    tune_cents:                         float = 0
    tune_semitones:                     int = 0
    filter_cutoff:                      int = 99
    key_to_filter_cutoff:               int = 12
    velocity_to_filter_cutoff:          int = 0
    pressure_to_filter_cutoff:          int = 0
    env2_to_filter_cutoff:              int = 0
    env1_attack:                        int = 0
    env1_decay:                         int = 30
    env1_sustain:                       int = 99
    env1_release:                       int = 45
    env1_velocity_to_attack:            int = 0
    env1_velocity_to_release:           int = 0
    env1_off_velocity_to_release:       int = 0
    env1_key_to_decay_and_release:      int = 0
    env2_attack:                        int = 0
    env2_decay:                         int = 50
    env2_sustain:                       int = 99
    env2_release:                       int = 45
    env2_velocity_to_attack:            int = 0
    env2_velocity_to_release:           int = 0
    env2_off_velocity_to_release:       int = 0
    env2_key_to_decay_and_release:      int = 0
    velocity_to_env2_to_filter_cutoff:  int = 0
    env2_to_pitch:                      int = 0
    velocity_zone_crossfade:            bool = True
    beat_detune:                        int = 0
    hold_attack_until_loop:             bool = False
    velocity_to_volume_offset:          int = 0


@dataclass
class KeygroupContainer(KeygroupCommon, Container):
    num_active_velocity_zones:  int = 1
    velocity_zones:             Sequence[VelocityZoneContainer] = field(
                                    default=(VelocityZoneContainer(), )
                                )
    enable_key_tracking:        Sequence[bool]  = field(default=(True, ) * 4)
    aux_out_offset:             Sequence[int]   = field(default=(0, ) * 4)
    velocity_to_sample_start:   Sequence[int]   = field(default=(0, ) * 4)


def _next_keygroup_address(this, default=150)->int:
    try:
        num_keygroups = this._._.header.number_of_keygroups
        keygroup_size = this._._.header.first_keygroup_address
        index = this._._index
    except (KeyError, AttributeError) as e:
        return default
    if index >= num_keygroups - 1:  # is last keygroup
        pass   # (gives next address anyhow)
    result = keygroup_size * (index + 1)
    return result


KeygroupConstruct = Struct(
    "block_id"                          / Int8ul,
    "next_keygroup_address"             / Default(Int16ul, 
                                            _next_keygroup_address
                                        ),
    "low_key"                           / AkaiMidiNote(Int8ul),
    "high_key"                          / AkaiMidiNote(Int8ul),
    "tune_cents"                        / AkaiTuneCents(Int8sl),
    "tune_semitones"                    / Int8sl,
    "filter_cutoff"                     / Int8ul,
    "key_to_filter_cutoff"              / Int8ul,
    "velocity_to_filter_cutoff"         / Int8sl,
    "pressure_to_filter_cutoff"         / Int8sl,
    "env2_to_filter_cutoff"             / Int8sl,
    "env1_attack"                       / Int8ul,
    "env1_decay"                        / Int8ul,
    "env1_sustain"                      / Int8ul,
    "env1_release"                      / Int8ul,
    "env1_velocity_to_attack"           / Int8sl,
    "env1_velocity_to_release"          / Int8sl,
    "env1_off_velocity_to_release"      / Int8sl,
    "env1_key_to_decay_and_release"     / Int8sl,
    "env2_attack"                       / Int8ul,
    "env2_decay"                        / Int8ul,
    "env2_sustain"                      / Int8ul,
    "env2_release"                      / Int8ul,
    "env2_velocity_to_attack"           / Int8sl,
    "env2_velocity_to_release"          / Int8sl,
    "env2_off_velocity_to_release"      / Int8sl,
    "env2_key_to_decay_and_release"     / Int8sl,
    "velocity_to_env2_to_filter_cutoff" / Int8sl,
    "env2_to_pitch"                     / Int8sl,
    "velocity_zone_crossfade"           / BoolConstruct(Int8ul),
    "num_velocity_zones"                / Default(Int8ul, 4),
    #Check(this.num_velocity_zones <= 4),
    Padding(2, pattern=b"\xFF"),
    "velocity_zones"                    / PaddedGeneral(
                                            lambda this:
                                            this.num_velocity_zones,
                                            VelocityZoneConstruct,
                                            VelocityZoneContainer(),
                                            lambda x,y: len(x.sample_name) > 0  # type: ignore
                                        ),
    "num_active_velocity_zones"         / Computed(len_(lambda this: this.velocity_zones)),
    "beat_detune"                       / Int8sl,
    "hold_attack_until_loop"            / BoolConstruct(Int8ul),
    "enable_key_tracking"               / SlicingGeneral(
                                            BoolConstruct(Int8ul)[lambda this: this.num_velocity_zones],
                                            lambda this: this.num_velocity_zones,
                                            0,
                                            lambda this: this.num_active_velocity_zones,
                                            pattern=False
                                        ),
    "aux_out_offset"                    / SlicingGeneral(
                                            Int8ul[lambda this: this.num_velocity_zones],
                                            lambda this: this.num_velocity_zones,
                                            0,
                                            lambda this: this.num_active_velocity_zones,
                                            pattern=0
                                        ),
    "velocity_to_sample_start"          / SlicingGeneral(
                                            Int16sl[lambda this: this.num_velocity_zones],
                                            lambda this: this.num_velocity_zones,
                                            0,
                                            lambda this: this.num_active_velocity_zones,
                                            pattern=0
                                        ),
    "velocity_to_volume_offset"         / Int8sl,
    Padding(1)
)


@itemizable
@dataclass
class VelocityZone(VelocityZoneCommon):
    enable_key_tracking:        bool    = True
    aux_out_offset:             int     = 0
    velocity_to_sample_start:   int     = 0


@itemizable
@dataclass
class Keygroup(KeygroupCommon):
    velocity_zones: Sequence[VelocityZone] = field(default=(VelocityZone(), ))


class KeygroupAdapter(Adapter):


    def _decode(self, obj: KeygroupContainer, context, path)->Keygroup:
        del context  # Unused
        container = obj 
        
        num_active_velocity_zones = len(container.velocity_zones)
        zone_aux_attrib_names = (
            "enable_key_tracking",
            "aux_out_offset",
            "velocity_to_sample_start"
        )
        cond = {
            k : len(container[k]) != num_active_velocity_zones 
            for k in zone_aux_attrib_names    
        }
        if any(cond.values()):
            bad_attribs = tuple(k for k, v in cond.items() if v)
            bad_lengths = tuple(str(len(container[x])) for x in bad_attribs)
            grammar = "have lengths" if len(bad_attribs) > 1 else "has a length"
            message = (
                f"{', '.join(bad_attribs)} {grammar} of {', '.join(bad_lengths)}. "
                f"Expected {num_active_velocity_zones}."
            )
            raise ConstructError(message, path)
        
        velocity_zones: List[VelocityZone] = list()
        for i, zone_container in enumerate(container.velocity_zones):
            zone_aux_attribs = {
                k : container[k][i] for k in zone_aux_attrib_names
            }
            velocity_zone = VelocityZone(
                **sanitize_container(zone_container),
                **zone_aux_attribs
            )
            velocity_zones.append(velocity_zone)

        common_attribs = {
            k.name: container[k.name] for k in fields(KeygroupCommon)
        }

        keygroup = Keygroup(
            **common_attribs,
            velocity_zones=velocity_zones
        )

        return keygroup

