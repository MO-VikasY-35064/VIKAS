"""
Data Automation Agent
=====================
An intelligent agent that orchestrates DataProcessor, PivotTableGenerator,
and ExcelExporter to automate end-to-end data reporting workflows.

Usage:
    Interactive mode:   python agent.py
    Workflow mode:      python agent.py --workflow workflow_config.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False

from loguru import logger

from data_processor import DataProcessor
from agent_tools import detect_file_type, parse_command, validate_workflow_config, format_summary_table

# Configure logger to file
logger.add("agent.log", rotation="1 MB", retention="7 days", level="DEBUG")


def _color(text: str, color: str) -> str:
    """Apply terminal color if colorama is available."""
    if not HAS_COLOR:
        return text
    colors = {
        "green": Fore.GREEN,
        "red": Fore.RED,
        "yellow": Fore.YELLOW,
        "cyan": Fore.CYAN,
        "bold": Style.BRIGHT,
    }
    return f"{colors.get(color, '')}{text}{Style.RESET_ALL}"


class DataAutomationAgent:
    """
    Intelligent agent for automating data processing, pivot table generation,
    and Excel reporting workflows.

    Attributes:
        processor (DataProcessor): Active DataProcessor instance.
        pivot_gen: Active PivotTableGenerator instance (lazy import).
        exporter: Active ExcelExporter instance (lazy import).
        session (dict): Current session state.
    """

    HELP_TEXT = """
╔══════════════════════════════════════════════════════════════╗
║              Data Automation Agent — Commands                ║
╠══════════════════════════════════════════════════════════════╣
║  load <filepath>              Load a CSV or Excel file       ║
║  clean [options]              Clean loaded data              ║
║    --drop-dupes               Drop duplicate rows            ║
║    --missing <strategy>       drop|mean|ffill|bfill          ║
║  summary                      Show data statistics           ║
║  pivot <index> <values>       Create a pivot table           ║
║    [--aggfunc <func>]         sum|mean|count|min|max|std     ║
║    [--name <pivot_name>]      Name to store the pivot        ║
║  export <output_path>         Export data/pivot to Excel     ║
║    [--pivot <name>]           Export a specific pivot        ║
║  workflow <config.json>       Run automated workflow         ║
║  status                       Show current session state     ║
║  help                         Show this help message         ║
║  exit                         Exit the agent                 ║
╚══════════════════════════════════════════════════════════════╝
"""

    def __init__(self):
        """Initialise the agent with a clean session."""
        self.processor = DataProcessor()
        self.pivot_gen = None
        self.exporter = None
        self.session = {
            "loaded_file": None,
            "data_shape": None,
            "cleaned": False,
            "pivots": [],
            "exports": [],
        }
        logger.info("DataAutomationAgent initialised.")

    # ------------------------------------------------------------------ #
    #  Lazy-load optional modules so the agent starts even if they are    #
    #  missing (e.g., first install before pip install -r requirements)   #
    # ------------------------------------------------------------------ #

    def _get_pivot_gen(self):
        """Lazy-load PivotTableGenerator."""
        if self.pivot_gen is None:
            try:
                from pivot_table_generator import PivotTableGenerator
                self.pivot_gen = PivotTableGenerator()
            except ImportError:
                print(_color("[ERROR] pivot_table_generator module not found.", "red"))
                return None
        return self.pivot_gen

    def _get_exporter(self):
        """Lazy-load ExcelExporter."""
        if self.exporter is None:
            try:
                from excel_exporter import ExcelExporter
                self.exporter = ExcelExporter()
            except ImportError:
                print(_color("[ERROR] excel_exporter module not found.", "red"))
                return None
        return self.exporter

    # ------------------------------------------------------------------ #
    #  Command handlers                                                    #
    # ------------------------------------------------------------------ #

    def cmd_load(self, filepath: str) -> bool:
        """
        Load a CSV or Excel file into the processor.

        Args:
            filepath: Path to the data file.

        Returns:
            True on success, False on failure.
        """
        filepath = filepath.strip('"').strip("'")
        if not os.path.exists(filepath):
            print(_color(f"[ERROR] File not found: {filepath}", "red"))
            logger.error(f"File not found: {filepath}")
            return False

        file_type = detect_file_type(filepath)
        try:
            if file_type == "csv":
                data = self.processor.read_csv(filepath)
            elif file_type == "excel":
                data = self.processor.read_excel(filepath)
            else:
                print(_color(f"[ERROR] Unsupported file type: {filepath}", "red"))
                return False

            self.session["loaded_file"] = filepath
            self.session["data_shape"] = data.shape
            self.session["cleaned"] = False
            print(_color(f"[OK] Loaded '{filepath}' — {data.shape[0]} rows × {data.shape[1]} columns", "green"))
            logger.info(f"Loaded file: {filepath}, shape: {data.shape}")
            return True
        except Exception as exc:
            print(_color(f"[ERROR] Failed to load file: {exc}", "red"))
            logger.exception(f"Load failed for {filepath}")
            return False

    def cmd_clean(self, drop_dupes: bool = True, handle_missing: str = "drop") -> bool:
        """
        Clean the currently loaded dataset.

        Args:
            drop_dupes: Whether to drop duplicate rows.
            handle_missing: Strategy — 'drop', 'mean', 'ffill', 'bfill'.

        Returns:
            True on success, False on failure.
        """
        if not self.session["loaded_file"]:
            print(_color("[WARN] No data loaded. Run: load <filepath>", "yellow"))
            return False
        try:
            self.processor.clean_data(
                drop_duplicates=drop_dupes,
                handle_missing=handle_missing,
            )
            self.session["cleaned"] = True
            print(_color(f"[OK] Data cleaned (drop_dupes={drop_dupes}, missing='{handle_missing}').", "green"))
            logger.info(f"Data cleaned: drop_dupes={drop_dupes}, handle_missing={handle_missing}")
            return True
        except Exception as exc:
            print(_color(f"[ERROR] Clean failed: {exc}", "red"))
            logger.exception("Clean step failed")
            return False

    def cmd_summary(self) -> bool:
        """
        Print statistical summary of the loaded data.

        Returns:
            True on success, False on failure.
        """
        if not self.session["loaded_file"]:
            print(_color("[WARN] No data loaded. Run: load <filepath>", "yellow"))
            return False
        try:
            summary = self.processor.get_summary()
            print("\n" + _color("=== Data Summary ===", "cyan"))
            print(format_summary_table(summary))
            return True
        except Exception as exc:
            print(_color(f"[ERROR] Summary failed: {exc}", "red"))
            logger.exception("Summary step failed")
            return False

    def cmd_pivot(
        self,
        index: list,
        values: list,
        aggfunc: str = "sum",
        pivot_name: str = None,
    ) -> bool:
        """
        Create a pivot table from the loaded data.

        Args:
            index: List of column names to use as pivot index.
            values: List of column names to aggregate.
            aggfunc: Aggregation function name.
            pivot_name: Optional name to store this pivot.

        Returns:
            True on success, False on failure.
        """
        if not self.session["loaded_file"]:
            print(_color("[WARN] No data loaded. Run: load <filepath>", "yellow"))
            return False

        gen = self._get_pivot_gen()
        if gen is None:
            return False

        try:
            data = self.processor.data
            name = pivot_name or f"pivot_{len(self.session['pivots']) + 1}"
            pivot = gen.create_pivot(
                data=data,
                index=index,
                values=values,
                aggfunc=aggfunc,
                pivot_name=name,
            )
            self.session["pivots"].append(name)
            print(_color(f"[OK] Pivot '{name}' created — {pivot.shape[0]} rows × {pivot.shape[1]} columns", "green"))
            logger.info(f"Pivot created: name={name}, shape={pivot.shape}")
            return True
        except Exception as exc:
            print(_color(f"[ERROR] Pivot creation failed: {exc}", "red"))
            logger.exception("Pivot step failed")
            return False

    def cmd_export(self, output_path: str, pivot_name: str = None) -> bool:
        """
        Export data or a named pivot to an Excel file.

        Args:
            output_path: Destination .xlsx file path.
            pivot_name: If set, export this specific pivot instead of raw data.

        Returns:
            True on success, False on failure.
        """
        if not self.session["loaded_file"]:
            print(_color("[WARN] No data loaded. Run: load <filepath>", "yellow"))
            return False

        exp = self._get_exporter()
        if exp is None:
            return False

        # Ensure output directory exists
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        try:
            if pivot_name:
                gen = self._get_pivot_gen()
                pivot_data = gen.get_pivot(pivot_name) if gen else None
                if pivot_data is None:
                    print(_color(f"[ERROR] Pivot '{pivot_name}' not found.", "red"))
                    return False
                exp.export_dataframe(
                    data=pivot_data,
                    file_path=output_path,
                    sheet_name=pivot_name,
                    apply_formatting=True,
                )
            else:
                exp.export_dataframe(
                    data=self.processor.data,
                    file_path=output_path,
                    apply_formatting=True,
                )

            self.session["exports"].append(output_path)
            print(_color(f"[OK] Exported to '{output_path}'", "green"))
            logger.info(f"Export complete: {output_path}")
            return True
        except Exception as exc:
            print(_color(f"[ERROR] Export failed: {exc}", "red"))
            logger.exception("Export step failed")
            return False

    def cmd_status(self):
        """Print the current session state."""
        print("\n" + _color("=== Agent Session Status ===", "cyan"))
        rows = [
            ["Loaded File", self.session["loaded_file"] or "—"],
            ["Data Shape", str(self.session["data_shape"]) if self.session["data_shape"] else "—"],
            ["Data Cleaned", "Yes" if self.session["cleaned"] else "No"],
            ["Pivots Created", ", ".join(self.session["pivots"]) or "—"],
            ["Files Exported", ", ".join(self.session["exports"]) or "—"],
        ]
        if HAS_TABULATE:
            print(tabulate(rows, headers=["Property", "Value"], tablefmt="rounded_outline"))
        else:
            for row in rows:
                print(f"  {row[0]:<20}: {row[1]}")
        print()

    # ------------------------------------------------------------------ #
    #  Workflow runner                                                     #
    # ------------------------------------------------------------------ #

    def run_workflow(self, config_path: str) -> bool:
        """
        Execute an automated multi-step workflow from a JSON config file.

        Args:
            config_path: Path to the workflow JSON config file.

        Returns:
            True if all steps succeeded, False otherwise.
        """
        if not os.path.exists(config_path):
            print(_color(f"[ERROR] Config file not found: {config_path}", "red"))
            return False

        try:
            with open(config_path, "r") as fh:
                config = json.load(fh)
        except json.JSONDecodeError as exc:
            print(_color(f"[ERROR] Invalid JSON in config: {exc}", "red"))
            return False

        errors = validate_workflow_config(config)
        if errors:
            for err in errors:
                print(_color(f"[ERROR] Config validation: {err}", "red"))
            return False

        wf_name = config.get("workflow_name", "Unnamed Workflow")
        steps = config.get("steps", [])
        print(_color(f"\n[WORKFLOW] Starting: '{wf_name}' ({len(steps)} steps)", "cyan"))
        logger.info(f"Workflow start: {wf_name}")

        for i, step in enumerate(steps, 1):
            action = step.get("action", "").lower()
            print(_color(f"  Step {i}/{len(steps)}: {action}", "yellow"), end=" ")

            if action == "load":
                ok = self.cmd_load(step.get("filepath", ""))
            elif action == "clean":
                ok = self.cmd_clean(
                    drop_dupes=step.get("drop_duplicates", True),
                    handle_missing=step.get("handle_missing", "drop"),
                )
            elif action == "summary":
                ok = self.cmd_summary()
            elif action == "pivot":
                ok = self.cmd_pivot(
                    index=step.get("index", []),
                    values=step.get("values", []),
                    aggfunc=step.get("aggfunc", "sum"),
                    pivot_name=step.get("name"),
                )
            elif action == "export":
                ok = self.cmd_export(
                    output_path=step.get("output", "output.xlsx"),
                    pivot_name=step.get("pivot"),
                )
            else:
                print(_color(f"[WARN] Unknown action '{action}' — skipping.", "yellow"))
                ok = True  # Non-fatal unknown step

            if not ok:
                print(_color(f"\n[WORKFLOW] Failed at step {i}. Aborting.", "red"))
                logger.error(f"Workflow '{wf_name}' failed at step {i}: {action}")
                return False

        print(_color(f"\n[WORKFLOW] '{wf_name}' completed successfully!", "green"))
        logger.info(f"Workflow complete: {wf_name}")
        return True

    # ------------------------------------------------------------------ #
    #  Interactive CLI                                                     #
    # ------------------------------------------------------------------ #

    def run(self):
        """Start the interactive agent CLI loop."""
        print(_color("""
╔══════════════════════════════════════════════╗
║        Data Automation Agent v1.0            ║
║  Type 'help' for commands, 'exit' to quit.   ║
╚══════════════════════════════════════════════╝""", "cyan"))

        while True:
            try:
                raw = input(_color("agent> ", "bold")).strip()
            except (EOFError, KeyboardInterrupt):
                print("\nBye!")
                break

            if not raw:
                continue

            action, args = parse_command(raw)

            if action == "exit":
                print(_color("Goodbye! 👋", "green"))
                break

            elif action == "help":
                print(self.HELP_TEXT)

            elif action == "status":
                self.cmd_status()

            elif action == "load":
                if not args:
                    print(_color("[WARN] Usage: load <filepath>", "yellow"))
                else:
                    self.cmd_load(args[0])

            elif action == "clean":
                drop_dupes = "--drop-dupes" in args
                try:
                    mi = args.index("--missing")
                    handle_missing = args[mi + 1]
                except (ValueError, IndexError):
                    handle_missing = "drop"
                self.cmd_clean(drop_dupes=drop_dupes, handle_missing=handle_missing)

            elif action == "summary":
                self.cmd_summary()

            elif action == "pivot":
                # pivot Region,Product Sales,Profit --aggfunc sum --name my_pivot
                if len(args) < 2:
                    print(_color("[WARN] Usage: pivot <index_cols> <value_cols> [--aggfunc func] [--name name]", "yellow"))
                else:
                    index = args[0].split(",")
                    values = args[1].split(",")
                    try:
                        af_i = args.index("--aggfunc")
                        aggfunc = args[af_i + 1]
                    except (ValueError, IndexError):
                        aggfunc = "sum"
                    try:
                        n_i = args.index("--name")
                        pivot_name = args[n_i + 1]
                    except (ValueError, IndexError):
                        pivot_name = None
                    self.cmd_pivot(index, values, aggfunc, pivot_name)

            elif action == "export":
                if not args:
                    print(_color("[WARN] Usage: export <output.xlsx> [--pivot <name>]", "yellow"))
                else:
                    output_path = args[0]
                    try:
                        p_i = args.index("--pivot")
                        pivot_name = args[p_i + 1]
                    except (ValueError, IndexError):
                        pivot_name = None
                    self.cmd_export(output_path, pivot_name)

            elif action == "workflow":
                if not args:
                    print(_color("[WARN] Usage: workflow <config.json>", "yellow"))
                else:
                    self.run_workflow(args[0])

            else:
                print(_color(f"[WARN] Unknown command '{action}'. Type 'help' for available commands.", "yellow"))


# ------------------------------------------------------------------ #
#  Entry point                                                         #
# ------------------------------------------------------------------ #

def main():
    """Parse CLI arguments and start the agent."""
    parser = argparse.ArgumentParser(
        description="Data Automation Agent — orchestrates data processing, pivot tables, and Excel exports."
    )
    parser.add_argument(
        "--workflow",
        metavar="CONFIG",
        help="Path to a workflow JSON config file to run automatically.",
    )
    args = parser.parse_args()

    agent = DataAutomationAgent()

    if args.workflow:
        success = agent.run_workflow(args.workflow)
        sys.exit(0 if success else 1)
    else:
        agent.run()


if __name__ == "__main__":
    main()
