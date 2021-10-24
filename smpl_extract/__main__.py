import os, sys
_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, "."))
from argparse import ArgumentParser

from actions import ls_action, export_samples_to_wav


def show_help_cmd(arg_parser: ArgumentParser, argv):
    arg_parser.print_help()


def ls_command(image_file, argv):
    arg_parser = ArgumentParser()
    arg_parser.add_argument("internal_path", type = str, default="", nargs="?")
    args_namespace = arg_parser.parse_args(argv)
    return ls_action(image_file, args_namespace.internal_path)


def export_wave_command(image_file, argv):
    arg_parser = ArgumentParser()
    arg_parser.add_argument("--output_directory", type = str, default=".")
    args_namespace = arg_parser.parse_args(argv)
    return export_samples_to_wav(image_file, args_namespace.output_directory)


def main(argv):
    arg_parser = ArgumentParser(add_help=False)
    arg_parser.add_argument("image_file", type = str)
    arg_parser.add_argument("command", default="")
    args_namespace, unparsed_args = arg_parser.parse_known_args(argv)

    cmd_funcs = {
        "ls": ls_command,
        "export_wav": export_wave_command
    }

    cmd_func = cmd_funcs.get(args_namespace.command, 
        lambda imag, args: show_help_cmd(arg_parser, args)
    )
    return cmd_func(args_namespace.image_file, unparsed_args)


if __name__ == "__main__":
    argv = sys.argv[1:]
    main(argv)
    pass