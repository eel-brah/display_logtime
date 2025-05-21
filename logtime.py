import argparse
import sys
import time
import tkinter as tk
from datetime import datetime, timedelta

import ttkbootstrap as ttk
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn

UID = "u-s4t2ud-29991113c05adf4f3bfcccaeec2ee454c26836788f9f0a2a3e84329627c4a496"
SECRET = "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"

TIMEZONE = "Africa/Casablanca"
API_BASE_URL = "https://api.intra.42.fr/v2"
MAX_HOURS = 120


def fetch_logtime(login, begin_at, end_at):
    client = BackendApplicationClient(client_id=UID)
    oauth = OAuth2Session(client=client)
    token = oauth.fetch_token(
        token_url=f"{API_BASE_URL}/oauth/token", client_id=UID, client_secret=SECRET
    )

    begin_str = begin_at.isoformat() + "Z"
    end_at = end_at + timedelta(days=1)
    end_str = end_at.isoformat() + "Z"

    user_url = f"https://api.intra.42.fr/v2/users/{login}"
    user_resp = oauth.get(user_url)
    if user_resp.status_code != 200:
        print(f"Invalid user {login}")
        sys.exit(1)

    try:
        stats_url = f"{API_BASE_URL}/users/{login}/locations_stats"
        params = {"begin_at": begin_str, "end_at": end_str, "time_zone": TIMEZONE}
        stats_resp = oauth.get(stats_url, params=params)
        return stats_resp.json()
    except Exception as e:
        print(f"API request failed: {str(e)}")
        sys.exit(1)


def get_date(begin, end):
    try:
        now = datetime.utcnow()

        if now.day >= 28 and not begin:
            begin = datetime(now.year, now.month, 28)

        if not begin:
            prev_month = now.month - 1 if now.month > 1 else 12
            prev_year = now.year if now.month > 1 else now.year - 1
            begin = datetime(prev_year, prev_month, 28)
        else:
            begin = datetime.fromisoformat(begin)

        if not end:
            end = now
        else:
            end = datetime.fromisoformat(end)

    except ValueError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

    if begin > now:
        print("Error: Invalid begin date")
        sys.exit(1)
    if end.strftime("%Y-%m-%d") < begin.strftime("%Y-%m-%d"):
        print("Error: End date must be after begin date")
        sys.exit(1)

    return begin, end


def display_progress(total_hours, begin, end):
    console = Console()
    console.print(
        f"[bold cyan]From: {begin.strftime('%Y-%m-%d')}  -  To: {end.strftime('%Y-%m-%d')}[/]"
    )

    with Progress(
        TextColumn("[bold cyan]Total Hours:[/]"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn(f"[bold green]{total_hours:.2f}h"),
        transient=False,
        console=console,
    ) as progress:
        task = progress.add_task("[green]Progress toward 120h...", total=MAX_HOURS)
        step = 0.5
        current = 0.0
        while current < total_hours and current < MAX_HOURS:
            progress.update(task, advance=step)
            current += step
            time.sleep(0.01)


def calc_hours(time_data):
    total_time = timedelta()

    for time_str in time_data.values():
        h, m, s = time_str.split(":")
        sec, micro = s.split(".")
        duration = timedelta(
            hours=int(h), minutes=int(m), seconds=int(sec), microseconds=int(micro)
        )
        total_time += duration

    return total_time.total_seconds() / 3600


def display_gui(login, begin, end, total_hours):
    root = ttk.Window(themename="darkly")
    root.title("Logtime")
    root.geometry("450x250")
    root.resizable(False, False)

    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    main_frame = ttk.Frame(root, padding=20)
    main_frame.grid(row=0, column=0, sticky="nsew")

    main_frame.columnconfigure(0, weight=1)
    for i in range(5):
        main_frame.rowconfigure(i, weight=1)

    title_label = ttk.Label(
        main_frame,
        text=f"{login}",
        font=("Helvetica", 16, "bold"),
        foreground="#5bc0de",
    )
    title_label.grid(row=0, column=0, sticky="n", pady=(0, 10))

    date_text = f"{begin.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"
    date_value = ttk.Label(
        main_frame, text=date_text, font=("Helvetica", 15), foreground="#64b5f6"
    )
    date_value.grid(row=1, column=0, pady=8)

    hours_value = ttk.Label(
        main_frame,
        text=f"{total_hours:.2f}",
        font=("Helvetica", 32, "bold"),
        foreground="#4caf50",
    )
    hours_value.grid(row=2, column=0, pady=(10, 15))

    progress_frame = ttk.Frame(main_frame)
    progress_frame.grid(row=4, column=0, sticky="nsew", pady=10)
    progress_frame.columnconfigure(0, weight=1)

    inner_progress_frame = ttk.Frame(progress_frame)
    inner_progress_frame.grid(row=0, column=0)

    percent = min((total_hours / MAX_HOURS) * 100, 100)

    style = ttk.Style()
    style.configure(
        "custom.Horizontal.TProgressbar", troughcolor="#424242", background="#4caf50"
    )

    progress = ttk.Progressbar(
        inner_progress_frame,
        style="custom.Horizontal.TProgressbar",
        value=f"{percent:.1f}",
        maximum=MAX_HOURS,
        length=300,
        mode="determinate",
    )
    progress.grid(row=0, column=0, pady=5)

    percent_label = ttk.Label(
        inner_progress_frame,
        text=f"{percent:.1f}%",
        font=("Helvetica", 12, "bold"),
        foreground="#4caf50",
    )
    percent_label.grid(row=1, column=0)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        root.destroy()
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch and display log time for a user",
        usage="%(prog)s <login> [begin_date] [end_date] [-g]",
    )
    parser.add_argument("login", help="User login (required)")
    parser.add_argument(
        "begin_date",
        nargs="?",
        default=None,
        help="Start date in YYYY-MM-DD format (optional)",
    )
    parser.add_argument(
        "end_date",
        nargs="?",
        default=None,
        help="End date in YYYY-MM-DD format (optional)",
    )
    parser.add_argument("-g", action="store_true", help="Display logtime in gui")
    args = parser.parse_args()

    begin, end = get_date(args.begin_date, args.end_date)
    time_data = fetch_logtime(args.login, begin, end)

    total_hours = calc_hours(time_data)
    if args.g:
        display_gui(args.login, begin, end, total_hours)
    else:
        display_progress(total_hours, begin, end)


if __name__ == "__main__":
    main()
