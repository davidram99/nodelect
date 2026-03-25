import argparse
from nodelect import __version__
from nodelect.core.installer import install_node_version
from nodelect.core.switcher import use_version
from nodelect.core.list import list_versions
from nodelect.core.uninstaller import uninstall_node_version
from nodelect.utils.parsers import parse_version
from nodelect.utils.logoPrinter import print_logo

def main() -> None:
    parser = argparse.ArgumentParser(prog="nodelect", description="Gestiona versiones de Node.js")
    parser.add_argument("-v", "--version", action="store_true", help="Muestra la versión de nodelect")
    
    subparsers = parser.add_subparsers(dest="command", required=False)

    parser_install = subparsers.add_parser("install", help="Instala una versión de Node.js")
    parser_install.add_argument("version", type=str, help="Versión de Node.js a instalar")

    parser_use = subparsers.add_parser("use", help="Selecciona la versión de Node.js a usar")
    parser_use.add_argument("version", type=str, help="Versión de Node.js a usar")

    parser_uninstall = subparsers.add_parser("uninstall", help="Desinstala una versión de Node.js")
    parser_uninstall.add_argument("version", type=str, help="Versión de Node.js a desinstalar")

    subparsers.add_parser("list", help="Lista las versiones de Node.js instaladas")

    args = parser.parse_args()

    if args.version and not args.command:
        print(f"nodelect version {__version__}")
        return
    elif args.command == "install":
        version = parse_version(args.version)
        install_node_version(version)
    elif args.command == "use":
        version = parse_version(args.version)
        use_version(version)
    elif args.command == "uninstall":
        version = parse_version(args.version)
        uninstall_node_version(version)
    elif args.command == "list":
        list_versions()
    else:
        print_logo()
        parser.print_help()



if __name__ == "__main__":
    main()