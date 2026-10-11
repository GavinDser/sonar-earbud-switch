import sys


def main():
    argv = sys.argv[1:]
    if argv and argv[0] == "setup":
        from . import setup

        return setup.run(argv[1:])
    from . import app

    return app.run()


if __name__ == "__main__":
    sys.exit(main())
