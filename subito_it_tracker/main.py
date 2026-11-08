import argparse

from . import __version__
from .command import CommandList
from .subito import SubitoApi


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tracker for Subito.it.")
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    return parser.parse_args()


def main():
    parse_arguments()

    api = SubitoApi()
    commands = CommandList(api)

    while True:
        try:
            user_input = input("tracker> ")
        except KeyboardInterrupt:
            print()
            break

        commands.run_command(user_input)


if __name__ == "__main__":
    main()
