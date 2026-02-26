import argparse
import pathlib

import requests


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=pathlib.Path)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--token", default=None)
    parser.add_argument("--return-mode", default="both", choices=["both", "html_only", "json_only"])
    args = parser.parse_args()

    headers = {}
    if args.token:
        headers["Authorization"] = f"Bearer {args.token}"

    with args.pdf.open("rb") as f:
        resp = requests.post(
            f"{args.base_url}/process/pdf",
            params={"return": args.return_mode},
            files={"file": (args.pdf.name, f, "application/pdf")},
            headers=headers,
            timeout=300,
        )

    print(resp.status_code)
    print(resp.text[:1000])


if __name__ == "__main__":
    main()
