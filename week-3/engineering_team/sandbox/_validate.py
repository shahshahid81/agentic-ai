from app import build_app


def main():
    app = build_app()
    assert app is not None
    print(type(app).__name__)


if __name__ == "__main__":
    main()
