import argparse
import sys
import time
from datetime import datetime, timedelta
from tkinter import messagebox

import ttkbootstrap as ttk
from oauthlib import oauth2
from requests_oauthlib import OAuth2Session
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn

from conf import API_BASE_URL, MAX_HOURS, MINUTES_UPDATE, SECRET, TIMEZONE, UID


def fetch_logtime(login, begin_at, end_at):
    try:
        client = oauth2.BackendApplicationClient(client_id=UID)
        oauth = OAuth2Session(client=client)
        oauth.fetch_token(
            token_url=f"{API_BASE_URL}/oauth/token", client_id=UID, client_secret=SECRET
        )
    except oauth2.rfc6749.errors.InvalidClientError:
        print("OAuth2 authentication failed due to invalid client credentials")
        print("Check UID and SECRET")

    begin_str = begin_at.isoformat() + "Z"
    end_at = end_at + timedelta(days=1)
    end_str = end_at.isoformat() + "Z"

    try:
        stats_url = f"{API_BASE_URL}/users/{login}/locations_stats"
        params = {"begin_at": begin_str, "end_at": end_str, "time_zone": TIMEZONE}
        stats_resp = oauth.get(stats_url, params=params)

        if stats_resp.status_code != 200:
            print(f"Error: Invalid login '{login}'")
            return None
        return stats_resp.json()
    except Exception as e:
        print(f"API request failed: {str(e)}")
        return None


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


def display_progress(total_minutes, begin, end):
    console = Console()
    console.print(
        f"[bold cyan]From: {begin.strftime('%Y-%m-%d')}  -  To: {end.strftime('%Y-%m-%d')}[/]"
    )

    total_hours = total_minutes // 60
    minutes = total_minutes % 60
    with Progress(
        TextColumn("[bold cyan]Total Hours:[/]"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn(f"[bold green]{total_hours:02.0f}:{minutes:02.0f}"),
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

    return total_time.total_seconds() / 60


def get_message(total_hours):
    message = ""
    if total_hours >= 130 and total_hours < 150:
        message = "Touch some grass"
    elif total_hours >= 150:
        message = "Bro, have a life"
    return message

def days_to_28():
    today = datetime.today()
    year = today.year
    month = today.month

    day_28_this_month = datetime(year, month, 28)

    if today <= day_28_this_month:
        delta = day_28_this_month - today
        return delta.days
    else:
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year

        day_28_next_month = datetime(next_year, next_month, 28)
        delta = day_28_next_month - today
        return delta.days

def display_gui(login, begin, end):
    root = ttk.Window(themename="darkly")
    root.title("Logtime")
    root.geometry("450x250")
    root.maxsize(450, 250)

    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    main_frame = ttk.Frame(root, padding=20)
    main_frame.grid(row=0, column=0, sticky="nsew")

    main_frame.columnconfigure(0, weight=1)
    main_frame.rowconfigure(0, weight=1)
    main_frame.rowconfigure(1, weight=1)
    main_frame.rowconfigure(3, weight=1)
    main_frame.rowconfigure(4, weight=1)

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

    total_minutes = 0
    hours_value = ttk.Label(
        main_frame,
        text="Loading...",
        font=("Helvetica", 32, "bold"),
        foreground="#4caf50",
    )
    hours_value.grid(row=2, column=0, pady=(10, 10))

    days_left = ttk.Label(
        main_frame,
        text=f"{days_to_28()} day(s) left",
        font=("Helvetica", 12, "bold"),
        foreground="#bfaf40",
    )
    days_left.grid(row=3, column=0, pady=(0, 0))

    progress_frame = ttk.Frame(main_frame)
    progress_frame.grid(row=4, column=0, sticky="nsew", pady=5)
    progress_frame.columnconfigure(0, weight=1)

    progress = ttk.Progressbar(
        progress_frame,
        bootstyle="success-striped",
        value=0,
        maximum=100,
        length=300,
    )
    progress.grid(row=0, column=0, pady=5)

    percent_label = ttk.Label(
        progress_frame,
        text="0%",
        font=("Helvetica", 12, "bold"),
        foreground="#4caf50",
    )
    percent_label.grid(row=1, column=0)

    def update_gui_display():
        total_hours = total_minutes // 60
        minutes = total_minutes % 60
        hours_value.config(text=f"{total_hours:02.0f}:{minutes:02.0f}")
        percent = (total_minutes / (MAX_HOURS * 60)) * 100
        message = get_message(total_hours)
        progress.config(value=percent)
        percent_label.config(text=f"{percent:.1f}% {message}")

    def update_display():
        nonlocal total_minutes
        total_minutes += MINUTES_UPDATE
        update_gui_display()
        root.after(MINUTES_UPDATE * 60000, update_display)

    def get_total_minutes():
        nonlocal total_minutes
        time_data = fetch_logtime(login, begin, end)
        if time_data is None:
            messagebox.showerror("Error", f"Failed to fetch logtime data for {login}.")
            root.destroy()
            return
        total_minutes = calc_hours(time_data)
        update_gui_display()

    root.after(100, get_total_minutes)
    root.after(MINUTES_UPDATE * 60000, update_display)

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

    if args.g:
        display_gui(args.login, begin, end)
    else:
        time_data = fetch_logtime(args.login, begin, end)
        if time_data is None:
            sys.exit(1)
        total_minutes = calc_hours(time_data)
        display_progress(total_minutes, begin, end)


if __name__ == "__main__":
    main()
