import os
import json
import glob
from datetime import datetime
from reporting.formatters import (
    format_replacement_report,
    format_health_audit_report,
    format_duplicate_report,
    format_decision_report,
    Colors,
)

class ReportTUI:
    def __init__(self):
        self.running = True
        self.current_report = None
        self.reports_cache = {}

    def clear_screen(self):
        os.system('clear' if os.name == 'posix' else 'cls')

    def header(self, title):
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}{Colors.RESET}\n")

    def footer(self):
        print(f"\n{Colors.YELLOW}[Q]uit  [B]ack  [C]lear  [R]efresh{Colors.RESET}")

    def find_reports(self):
        """Scan workspace for report files"""
        reports = {
            "replacement": [],
            "health_audit": [],
            "duplicate": [],
            "decision": [],
        }

        # Find replacement reports
        for f in glob.glob("*replacement*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    if "manual_review" in data or "removed" in data:
                        reports["replacement"].append(f)
            except:
                pass

        # Find audit reports
        for f in glob.glob("*audit*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    if "dead" in data or "ok" in data:
                        reports["health_audit"].append(f)
            except:
                pass

        # Find duplicate/decision reports
        for f in glob.glob("*report*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    if "duplicates" in data:
                        if "decisions" in str(f).lower():
                            reports["decision"].append(f)
                        else:
                            reports["duplicate"].append(f)
            except:
                pass

        return reports

    def load_report(self, filepath):
        """Load report from file"""
        if filepath in self.reports_cache:
            return self.reports_cache[filepath]

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.reports_cache[filepath] = data
                return data
        except Exception as e:
            print(f"{Colors.RED}Error loading report: {e}{Colors.RESET}")
            return None

    def display_replacement_report(self, filepath):
        """Display replacement report"""
        self.clear_screen()
        self.header(f"Replacement Report: {filepath}")

        data = self.load_report(filepath)
        if not data:
            return

        print(format_replacement_report(data))

        manual_review = data.get("manual_review", [])
        if manual_review:
            print(f"\n{Colors.YELLOW}Manual Review Candidates: {len(manual_review)}{Colors.RESET}")
            for i, item in enumerate(manual_review[:5], 1):
                orig = item.get("original", {})
                cand = item.get("candidate", {})
                print(f"\n{i}. {orig.get('name')} -> {cand.get('name')} (score: {item.get('score', 0):.2f})")
            
            if len(manual_review) > 5:
                print(f"\n... and {len(manual_review) - 5} more candidates")

        self.footer()

    def display_health_audit_report(self, filepath):
        """Display health audit report"""
        self.clear_screen()
        self.header(f"Health Audit Report: {filepath}")

        data = self.load_report(filepath)
        if not data:
            return

        print(format_health_audit_report(data))
        self.footer()

    def display_duplicate_report(self, filepath):
        """Display duplicate report"""
        self.clear_screen()
        self.header(f"Duplicate Report: {filepath}")

        data = self.load_report(filepath)
        if not data:
            return

        print(format_duplicate_report(data))
        self.footer()

    def display_decision_report(self, filepath):
        """Display decision report"""
        self.clear_screen()
        self.header(f"Decision Report: {filepath}")

        data = self.load_report(filepath)
        if not data:
            return

        print(format_decision_report(data))
        self.footer()

    def show_report_menu(self):
        """Show list of available reports by type"""
        self.clear_screen()
        self.header("Available Reports")

        reports = self.find_reports()
        choices = {}
        idx = 1

        print(f"{Colors.GREEN}Replacement Reports:{Colors.RESET}")
        for f in reports["replacement"]:
            print(f"  [{idx}] {f}")
            choices[str(idx)] = ("replacement", f)
            idx += 1

        print(f"\n{Colors.GREEN}Health Audit Reports:{Colors.RESET}")
        for f in reports["health_audit"]:
            print(f"  [{idx}] {f}")
            choices[str(idx)] = ("health_audit", f)
            idx += 1

        print(f"\n{Colors.GREEN}Duplicate Reports:{Colors.RESET}")
        for f in reports["duplicate"]:
            print(f"  [{idx}] {f}")
            choices[str(idx)] = ("duplicate", f)
            idx += 1

        print(f"\n{Colors.GREEN}Decision Reports:{Colors.RESET}")
        for f in reports["decision"]:
            print(f"  [{idx}] {f}")
            choices[str(idx)] = ("decision", f)
            idx += 1

        if not choices:
            print(f"{Colors.YELLOW}No reports found.{Colors.RESET}")
            input("Press Enter to continue...")
            return

        print(f"\n{Colors.YELLOW}[Q]uit{Colors.RESET}")
        choice = input(f"\n{Colors.CYAN}Select report to view (number): {Colors.RESET}").strip().lower()

        if choice == 'q':
            self.running = False
        elif choice in choices:
            report_type, filepath = choices[choice]
            self.show_report(report_type, filepath)

    def show_report(self, report_type, filepath):
        """Display specific report and handle navigation"""
        while True:
            if report_type == "replacement":
                self.display_replacement_report(filepath)
            elif report_type == "health_audit":
                self.display_health_audit_report(filepath)
            elif report_type == "duplicate":
                self.display_duplicate_report(filepath)
            elif report_type == "decision":
                self.display_decision_report(filepath)

            choice = input(f"\n{Colors.CYAN}Command: {Colors.RESET}").strip().lower()

            if choice == 'q':
                self.running = False
                break
            elif choice == 'b':
                break
            elif choice == 'c':
                self.clear_screen()
            elif choice == 'r':
                self.reports_cache.pop(filepath, None)

    def run(self):
        """Main TUI loop"""
        while self.running:
            self.show_report_menu()


def start_tui():
    """Start the report TUI"""
    tui = ReportTUI()
    tui.run()
    print(f"\n{Colors.GREEN}Goodbye!{Colors.RESET}")
