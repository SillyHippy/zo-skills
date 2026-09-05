#!/usr/bin/env python3
"""Generate Declaration of Service PDF from case data.

Document title: DECLARATION OF SERVICE (or AMENDED DECLARATION OF SERVICE).
No notary block. Oklahoma perjury declaration format.

USAGE:
    python fill_proof.py --plaintiff "..." --defendant "..." \\
        --person-served "..." --address "..." --case-number "..." \\
        --documents "..." --service-type personal \\
        --service-date "06/29/2026" --service-time "7:28 AM" \\
        --today "06/29/2026" --comments "..." \\
        --output proof_of_service.pdf
"""

import argparse
import os
import subprocess
import sys
import tempfile

try:
    import fitz  # PyMuPDF, used only for post-generation verification
except ImportError:
    fitz = None

SERVICE_TYPE_MAP = {
    "personal": "Personal Service",
    "substituted-residence": "Substituted at Residence",
    "substituted-business": "Substituted at Business",
    "posting": "Posting",
    "non-service": "Non-Service",
    "unknown": "Unknown at address",
    "moved": "Moved left no forwarding",
    "canceled": "Service canceled by litigant",
    "untimely": "Unable to serve in a timely fashion",
    "no-address": "Address does not exist",
    "other": "Other",
}

COURT = "DISTRICT COURT, TULSA COUNTY, STATE OF OKLAHOMA"
SERVER = "Joseph Iannazzi"
SERVER_ID = "PSL-2026-2"


def _escape_tex(s: str) -> str:
    return s.replace("#", r"\#").replace("'", "''")


def build_latex(
    plaintiff,
    defendant,
    person_served,
    address,
    case_number,
    documents,
    service_type,
    service_date,
    service_time,
    today,
    comments="",
    narrative="",
    hearing_date=None,
    amended=False,
    original_date="",
    wrong_name="",
    court=COURT,
):
    is_service = service_type not in (
        "non-service", "unknown", "moved", "canceled",
        "untimely", "no-address", "other",
    )

    if amended:
        title = "AMENDED DECLARATION OF SERVICE"
        doc_title = "AMENDED DECLARATION OF SERVICE OF"
    elif is_service:
        title = "DECLARATION OF SERVICE"
        doc_title = "DECLARATION OF SERVICE OF"
    else:
        title = "PROOF OF NON-SERVICE"
        doc_title = "PROOF OF NON-SERVICE OF"

    if not narrative:
        if service_type == "personal":
            narrative = (
                f"personal service was effected on the above-named party at "
                f"\\textbf{{{_escape_tex(address)}}}."
            )
        elif service_type == "substituted-residence":
            narrative = (
                f"I made successful substitute service at the abode. "
                f"I delivered the documents to a household member who stated "
                f"they were a co-resident of the premises."
            )
        elif service_type == "posting":
            narrative = (
                f"I posted a true and correct copy in a conspicuous place on "
                f"the premises located at \\textbf{{{_escape_tex(address)}}}."
            )
        else:
            narrative = SERVICE_TYPE_MAP.get(service_type, service_type) + "."

    if hearing_date:
        hearing_cell = f"Hearing Date: \\textbf{{{_escape_tex(hearing_date)}}} \\\\[0.5em]"
    else:
        hearing_cell = "\\\\[1em]"

    correction = ""
    if amended and original_date and wrong_name:
        correction = (
            f"This amended proof of service corrects the recipient name on the "
            f"Proof of Service dated {_escape_tex(original_date)}, which incorrectly "
            f"identified {_escape_tex(wrong_name)} as the person served. The person "
            f"actually served was {_escape_tex(person_served)}. All other facts of "
            f"service remain unchanged.\n\n\\vspace{{0.5em}}\n\n"
        )

    comments_block = ""
    if comments:
        comments_block = (
            f"\\textbf{{{_escape_tex(service_date)} {_escape_tex(service_time)}}}: "
            f"{_escape_tex(comments)}\n\n"
        )

    served_verb = "SERVED" if is_service else "attempted service upon"

    tex = rf"""\documentclass[11pt, letterpaper]{{article}}
\usepackage[top=1in, bottom=1in, left=1in, right=1in]{{geometry}}
\usepackage{{fontspec}}
\usepackage[english, bidi=basic, provide=*]{{babel}}
\babelprovide[import, onchar=ids fonts]{{english}}
\babelfont{{rm}}{{Noto Sans}}
\usepackage{{tabularx}}
\usepackage{{array}}
\usepackage{{ragged2e}}

\setlength{{\parindent}}{{0pt}}
\setlength{{\parskip}}{{1em}}

\begin{{document}}
\thispagestyle{{empty}}

\begin{{center}}
{{\large \textbf{{{title}}}}}
\vspace{{0.3em}}

{court}
\end{{center}}

\vspace{{0.5em}}

\noindent
\begin{{tabular}}{{@{{}} p{{0.46\textwidth}} | @{{\hspace{{0.03\textwidth}}}} p{{0.46\textwidth}} @{{}}}}
\textbf{{{_escape_tex(plaintiff)}}} & Case No.: \textbf{{{_escape_tex(case_number)}}} \\[0.5em]
\hfill Plaintiff/Petitioner & {hearing_cell}
vs. & \\\\[1em]
\textbf{{{_escape_tex(defendant)}}} & {doc_title} \\
& \textbf{{{_escape_tex(documents)}}} \\
\hfill Defendant/Respondent & \\
\end{{tabular}}

\vspace{{1em}}

{correction}Received by \textbf{{{SERVER}}} to be served upon \textbf{{{_escape_tex(person_served)}}} at \textbf{{{_escape_tex(address)}}}.

On \textbf{{{_escape_tex(service_date)}}} at \textbf{{{_escape_tex(service_time)}}}, I, \textbf{{{SERVER}}}, attended the premises at \textbf{{{_escape_tex(address)}}} for the purpose of serving \textbf{{{_escape_tex(person_served)}}}.

\textbf{{SERVICE}} after due search, careful inquiry and diligent attempts at \textbf{{{_escape_tex(address)}}}, {narrative}

{comments_block}I am over the age of eighteen, not a party to nor interested in the above entitled action, and have the proper authority in the jurisdiction in which this service was made. Under penalties of perjury, I declare that I have read the foregoing document and that the facts stated in it are true and accurate.

\vspace{{2em}}

\noindent
\begin{{tabular}}{{@{{}} l @{{\hspace{{1.5cm}}}} c @{{\hspace{{1.5cm}}}} c @{{}}}}
NAME: \begin{{tabular}}[t]{{@{{}}c@{{}}}}\rule{{6.5cm}}{{0.5pt}} \\[0.5em] {SERVER}\end{{tabular}} &
\begin{{tabular}}[t]{{@{{}}c@{{}}}}{SERVER_ID} \\[0.5em] Server ID \#\end{{tabular}} &
\begin{{tabular}}[t]{{@{{}}c@{{}}}}{_escape_tex(today)} \\[0.5em] Date\end{{tabular}}
\end{{tabular}}

\vspace{{1em}}

Executed in Tulsa County, State of Oklahoma.

\end{{document}}
"""
    return tex


def compile_latex(tex_content, output_path):
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_file = os.path.join(tmpdir, "proof_of_service.tex")
        with open(tex_file, "w") as f:
            f.write(tex_content)

        result = subprocess.run(
            ["lualatex", "-interaction=nonstopmode", "-output-directory", tmpdir, tex_file],
            capture_output=True,
            text=True,
            timeout=60,
        )

        pdf_file = os.path.join(tmpdir, "proof_of_service.pdf")
        if not os.path.exists(pdf_file):
            print(f"LATEX ERROR:\n{result.stdout}\n{result.stderr}", file=sys.stderr)
            return False

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        subprocess.run(["cp", pdf_file, output_path], check=True)
        return True


def main():
    parser = argparse.ArgumentParser(description="Generate Proof of Service PDF")
    parser.add_argument("--court", default=COURT)
    parser.add_argument("--plaintiff", required=True)
    parser.add_argument("--defendant", required=True)
    parser.add_argument("--person-served", required=True,
                        help="Person actually served (may differ from defendant)")
    parser.add_argument("--address", required=True)
    parser.add_argument("--case-number", required=True)
    parser.add_argument("--documents", required=True)
    parser.add_argument("--service-type", required=True, choices=list(SERVICE_TYPE_MAP.keys()))
    parser.add_argument("--service-date", required=True)
    parser.add_argument("--service-time", required=True)
    parser.add_argument("--today", required=True)
    parser.add_argument("--hearing-date", default=None)
    parser.add_argument("--comments", default="")
    parser.add_argument("--narrative", default="")
    parser.add_argument("--amended", action="store_true")
    parser.add_argument("--original-date", default="")
    parser.add_argument("--wrong-name", default="")
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    tex = build_latex(
        plaintiff=args.plaintiff,
        defendant=args.defendant,
        person_served=args.person_served,
        address=args.address,
        case_number=args.case_number,
        documents=args.documents,
        service_type=args.service_type,
        service_date=args.service_date,
        service_time=args.service_time,
        today=args.today,
        comments=args.comments,
        narrative=args.narrative,
        hearing_date=args.hearing_date,
        amended=args.amended,
        original_date=args.original_date,
        wrong_name=args.wrong_name,
        court=args.court,
    )

    if compile_latex(tex, args.output):
        if not os.path.exists(args.output) or os.path.getsize(args.output) == 0:
            print(f"ERROR: output missing or empty after compilation: {args.output}", file=sys.stderr)
            sys.exit(1)
        if fitz is not None:
            try:
                doc = fitz.open(args.output)
                text = "\\n".join(page.get_text() for page in doc)
                pages = len(doc)
                doc.close()
            except Exception as exc:
                print(f"ERROR: could not reopen declaration PDF: {exc}", file=sys.stderr)
                sys.exit(1)
            if pages == 0 or "DECLARATION OF SERVICE" not in text:
                print("ERROR: declaration PDF verification failed: missing expected title", file=sys.stderr)
                sys.exit(1)
            print(f"Verified: {args.output} ({pages} page(s))")
        else:
            print(f"Verified: {args.output} ({os.path.getsize(args.output)} bytes)")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
