import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))

from gettext import gettext
from argparse import ArgumentParser

from actions import ls_action
from actions import export_samples_to_wav


PACKAGE_NAME = "smpl_extract"


def parse_file_string(str_in: str)->str:
        if not os.path.exists(str_in):
            raise FileNotFoundError(f"Could not find {str_in}.")
        if not os.path.isfile(str_in):
            raise OSError(f"Entity {str_in} is not a file.")
        return str_in


def construct_common_parser(
        cmd_name: str = ""
    )->ArgumentParser:
    arg_parser = ArgumentParser(
        add_help=True, 
        prog=f"{PACKAGE_NAME} {cmd_name}".strip()
    )
    arg_parser.add_argument(
        "image_file",       
        type=parse_file_string,
        help=(
                "The path to the file containing the disc "
                "image on your operating system - either "
                "absolute or relative to the current working "
                "directory."
        )
    )
    return arg_parser


def ls_parse_args(argv):
    arg_parser = construct_common_parser("ls")
    arg_parser.add_argument(
        "internal_path", 
        type = str, 
        default="", 
        nargs="?",
        help=(
                "The path within the disc image. "
                "This path has the form \"<dir1>/<dir2>/<file>\". "
                "If this path is a file (i.e., a sample, "
                "patch, etc.), the information available for "
                "that file will be displayed as plain-text. "
                "If this path is a directory (e.g., "
                "partitions/volumes in an AKAI image, etc.), "
                "the contents of that directory will be listed. "
                "If this path is empty, the root entries of the disk "
                "(e.g., the tracks of a CDDA bin/cue) will be listed."
        )
    )

    args_namespace = arg_parser.parse_args(argv)
    result = ls_action(
        args_namespace.image_file, 
        args_namespace.internal_path
    )
    return result


def export_parse_args(argv):

    export_formats = {
        "wav": export_samples_to_wav
    }

    # arg parser
    arg_parser = construct_common_parser("export")
    arg_parser.add_argument(
        "-f", 
        "--format",
        choices=export_formats.keys(),
        default="wav",
        help=(
                "The output format of the extracted samples. "
                "Currently only accepts wav. " 
                "The default output format is wav."
        )
    )
    arg_parser.add_argument(
        "-d", 
        "--destination",
        type = str, 
        default=".",
        help=(
            "The samples will be exported in "
            "a directory structure which mirrors the structure "
            "of the disc image. The default is the current "
            "working directory."
        )
    )
    args_namespace = arg_parser.parse_args(argv)
    
    export_func = export_formats.get(
        args_namespace.format,
        export_samples_to_wav
    )
    
    result = export_func(
        args_namespace.image_file,
        args_namespace.destination
    )
    return result



def main(argv):
    if argv is None:
        argv = sys.argv[1:]

    # Print help on error
    class ArgumentParserMod(ArgumentParser):
        def error(self, message: str):
            self.print_help()
            args = {'prog': self.prog, 'message': message}
            self.exit(2, gettext('%(prog)s: error: %(message)s\n') % args)

    arg_parser = ArgumentParserMod(
        add_help=False,
        prog=PACKAGE_NAME
    )

    # define commands
    cmd_funcs = {
        "ls": ls_parse_args,
        "export": export_parse_args
    }
    arg_parser.add_argument(
        "command", 
        choices=cmd_funcs.keys(),
        help="The command to execute."
    )

    # init optional arg list
    arg_parser.add_argument(
        "args", 
        default="", 
        nargs="*",
        help="The arguments passed to the command."
    )

    # determine command
    args_namespace, unparsed_args = arg_parser.parse_known_args(argv)
    cmd_func = cmd_funcs.get(
        args_namespace.command,
        lambda x: arg_parser.print_help()
    )

    # determine args
    cmd_args = args_namespace.args
    if isinstance(cmd_args, str):
        if len(cmd_args) > 1:
            cmd_args = [cmd_args]
        else:
            cmd_args = []
    cmd_args = cmd_args + unparsed_args

    return cmd_func(cmd_args)


if __name__ == "__main__":
    PROFILE = False
    profiler = None

    if PROFILE:
        import cProfile
        profiler = cProfile.Profile()
        profiler.enable()

    argv = sys.argv[1:]
    main(argv)

    if PROFILE and profiler:
        import pstats
        profiler.disable()
        stats = pstats.Stats(profiler).sort_stats('tottime')
        stats.strip_dirs()
        stats.print_stats()

    pass

