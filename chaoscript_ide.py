import os
import re
from typing import List, Dict, Tuple, Optional, Any, Set
import json
import queue
import random
import tkinter as tk
from tkinter import messagebox
from chaoscript_engine import (
    ChaoLexer, ChaoParser, ChaoTokenType,
    ChaoPlantDehydrationError, ChaoLexicalError, ChaoSyntaxError,
    check_system_hydration
)
from chaoscript_interpreter import ChaoInterpreter, ChaoRuntimeError

# ==============================================================================
# CYBERPUNK COLOR CODES
# ==============================================================================
BG_DARK = "#000000"
BG_CHARCOAL = "#121212"
BG_PANEL = "#0b0b0b"
BG_CONSOLE = "#050505"

FG_GREEN = "#00ff00"
FG_MAGENTA = "#ff00ff"
FG_CYAN = "#00ffff"
FG_AMBER = "#ffaa00"
FG_YELLOW = "#ffff00"
FG_RED = "#ff0000"
FG_GREY = "#555555"

# ==============================================================================
# KEVIN'S DIALECT DATABASE
# ==============================================================================
KEVIN_CRITIQUES = [
    "🌱 Code lacks abstract structural daemon watch variables. The Spaghetti Daemon is unamused.",
    "🌱 Analysis: 0% daemon optimization. Code is too linear. Kevin recommends more chaos.",
    "🌱 Kevin's review: Why are you writing clean code? This is an esoteric language. Inject some DAEMONS!",
    "🌱 Review warning: No daemons detected. Who is going to watch the memory leak stacks? Unacceptable.",
    "🌱 Monotone report: Garden complexity rating: 1/10. Needs a background daemon loop to corrupt pointers.",
    "🌱 Sarcastic review: Looks like standard junior Python code. Where are the vines? Where is the spaghetti? Add a DAEMON."
]

KEVIN_DAEMON_OK = [
    "🌱 Review: Daemon watch variables detected. The Spaghetti Daemon nods in silent compliance.",
    "🌱 Review: Code contains daemons. Kevin is slightly less disappointed today.",
    "🌱 Analysis: Daemon threads active. Memory leak safeguards online. Nominal matrix.",
    "🌱 Monotone report: Daemons confirmed. Cyber-spaghetti levels are sufficient. Proceed."
]


# ==============================================================================
# THE INTEGRATED DEVELOPMENT ENVIRONMENT FRAME
# ==============================================================================

class ChaoScriptModule(tk.Frame):
    def __init__(self, parent_frame, app_ref=None):
        super().__init__(parent_frame, bg=BG_DARK)
        self.app_ref = app_ref
        
        self.interpreter = None
        self.execution_queue = None
        
        # Build layout viewport split frames
        self.build_ui()
        
        # Pre-bind syntax highlighter to KeyRelease event
        self.editor.bind("<KeyRelease>", self.highlight_syntax)
        
        # Pre-load a default demo garden script
        self.load_default_script()

    def build_ui(self) -> None:
        """Assembles the cyberpunk-themed panels and scrolling controls."""
        # 1. TOOLBAR PANEL
        self.toolbar = tk.Frame(self, bg=BG_PANEL, highlightthickness=1, highlightbackground=FG_CYAN)
        self.toolbar.pack(fill="x", side="top", padx=5, pady=(5, 10))

        # Neon buttons
        self.btn_run = self.create_neon_btn("RUN GARDEN", self.run_garden, FG_GREEN)
        self.btn_run.pack(side="left", padx=10, pady=8)

        self.btn_compile = self.create_neon_btn("THE SUN", self.run_compile_check, FG_YELLOW)
        self.btn_compile.pack(side="left", padx=10, pady=8)

        self.btn_clear = self.create_neon_btn("CLEAR FEED", self.clear_feed, FG_CYAN)
        self.btn_clear.pack(side="left", padx=10, pady=8)

        self.btn_review = self.create_neon_btn("DAEMON REVIEW", self.daemon_review, FG_MAGENTA)
        self.btn_review.pack(side="left", padx=10, pady=8)

        # 2. MIDDLE SPLIT PANE (GARDEN BED & SOIL MONITOR)
        self.mid_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg=BG_DARK, bd=0, sashwidth=5, sashpad=2)
        self.mid_pane.pack(fill="both", expand=True, padx=5, pady=5)

        # Garden Bed (Editor surface) Frame
        self.editor_frame = tk.Frame(self.mid_pane, bg=BG_DARK, highlightthickness=1, highlightbackground=FG_MAGENTA)
        
        editor_title = tk.Label(self.editor_frame, text="// THE GARDEN BED (Editor Surface)", fg=FG_MAGENTA, bg=BG_DARK, font=("Courier", 10, "bold"))
        editor_title.pack(anchor="w", padx=5, pady=2)

        self.editor = tk.Text(
            self.editor_frame, bg=BG_CHARCOAL, fg="#ffffff", insertbackground=FG_RED,
            font=("Consolas", 11), wrap="none", undo=True, bd=0
        )
        
        # Scrollbars
        self.editor_ysb = tk.Scrollbar(self.editor_frame, command=self.editor.yview)
        self.editor_xsb = tk.Scrollbar(self.editor_frame, orient=tk.HORIZONTAL, command=self.editor.xview)
        self.editor.config(yscrollcommand=self.editor_ysb.set, xscrollcommand=self.editor_xsb.set)

        self.editor_ysb.pack(side="right", fill="y")
        self.editor_xsb.pack(side="bottom", fill="x")
        self.editor.pack(fill="both", expand=True, padx=5, pady=5)

        # Soil Monitor (Variable stack sidebar) Frame
        self.monitor_frame = tk.Frame(self.mid_pane, bg=BG_DARK, highlightthickness=1, highlightbackground=FG_AMBER, width=220)
        self.monitor_frame.pack_propagate(False)

        monitor_title = tk.Label(self.monitor_frame, text="// THE SOIL MONITOR", fg=FG_AMBER, bg=BG_DARK, font=("Courier", 10, "bold"))
        monitor_title.pack(anchor="w", padx=5, pady=2)

        self.vars_listbox = tk.Listbox(
            self.monitor_frame, bg=BG_CONSOLE, fg=FG_GREEN, bd=0,
            highlightthickness=0, font=("Consolas", 10)
        )
        self.vars_ysb = tk.Scrollbar(self.monitor_frame, command=self.vars_listbox.yview)
        self.vars_listbox.config(yscrollcommand=self.vars_ysb.set)

        self.vars_ysb.pack(side="right", fill="y")
        self.vars_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # Add to horizontal split pane
        self.mid_pane.add(self.editor_frame, minsize=400)
        self.mid_pane.add(self.monitor_frame, minsize=200)

        # 3. BOTTOM PANEL (THE FEED CHUTE)
        self.console_frame = tk.Frame(self, bg=BG_DARK, highlightthickness=1, highlightbackground=FG_GREEN)
        self.console_frame.pack(fill="x", side="bottom", padx=5, pady=5)

        console_title = tk.Label(self.console_frame, text="// THE FEED CHUTE (Terminal Console Output)", fg=FG_GREEN, bg=BG_DARK, font=("Courier", 10, "bold"))
        console_title.pack(anchor="w", padx=5, pady=2)

        self.console = tk.Text(
            self.console_frame, bg=BG_CONSOLE, fg=FG_GREEN, height=8,
            font=("Consolas", 10), wrap="word", state=tk.DISABLED, bd=0
        )
        self.console_ysb = tk.Scrollbar(self.console_frame, command=self.console.yview)
        self.console.config(yscrollcommand=self.console_ysb.set)

        self.console_ysb.pack(side="right", fill="y")
        self.console.pack(fill="x", expand=True, padx=5, pady=5)

        # Register syntax tags
        self.editor.tag_config("def_keywords", foreground=FG_AMBER, font=("Consolas", 11, "bold"))
        self.editor.tag_config("flow_labels", foreground=FG_MAGENTA, font=("Consolas", 11, "bold"))
        self.editor.tag_config("literals", foreground=FG_CYAN)
        self.editor.tag_config("glitch", foreground=FG_RED, font=("Consolas", 11, "bold"))
        self.editor.tag_config("comments", foreground=FG_GREY)

        # Register widgets with GlitchManager if available
        if self.app_ref and hasattr(self.app_ref, "glitch_manager") and self.app_ref.glitch_manager:
            try:
                self.app_ref.glitch_manager.register_widget(self.btn_run, magnitude=0.18)
                self.app_ref.glitch_manager.register_widget(self.btn_compile, magnitude=0.15)
                self.app_ref.glitch_manager.register_widget(self.btn_clear, magnitude=0.15)
                self.app_ref.glitch_manager.register_widget(self.btn_review, magnitude=0.2)
                self.app_ref.glitch_manager.register_widget(self.editor, hover=False, click=False, temporal=True, magnitude=0.08)
                self.app_ref.glitch_manager.register_widget(self.vars_listbox, hover=False, click=False, temporal=True, magnitude=0.1)
                self.app_ref.glitch_manager.register_widget(self.console, hover=False, click=False, temporal=True, magnitude=0.08)
            except Exception:
                pass

    def create_neon_btn(self, text: str, command: Any, hover_color: str) -> tk.Button:
        """Helper to create high-contrast retro arcade style buttons."""
        btn = tk.Button(
            self.toolbar, text=text, command=command,
            bg=BG_DARK, fg=FG_GREEN, activebackground=FG_GREEN, activeforeground=BG_DARK,
            font=("Courier", 10, "bold"), bd=1, highlightthickness=1, highlightbackground=FG_GREEN
        )
        
        # Hover effect bindings
        def on_enter(e):
            if btn["state"] != tk.DISABLED:
                btn.config(fg=hover_color, highlightbackground=hover_color)
        def on_leave(e):
            if btn["state"] != tk.DISABLED:
                btn.config(fg=FG_GREEN, highlightbackground=FG_GREEN)
                
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def load_default_script(self) -> None:
        """Pre-loads a comprehensive ChaoScript demo showing off language structures."""
        demo_code = """// Welcome to ChaoScript IDE
IMPORT plant
IMPORT glitch

PLANT diagnostics_garden
    SEED iterations = 5
    SEED val = 10
    
    // We declare a function stalk to check values
    STALK evaluate_val(curr)
        IF curr > 50
            RETURN TRUE
        ELSE
            RETURN FALSE
        END IF
    END STALK

    WATER "Starting hydration is:"
    WATER plant.hydration

    WATER "Injecting water into cyberplant..."
    plant.water()

    WATER "Running mutation loops..."
    GROW iterations TIMES
        WATER val
        SOIL val = ~~~val
        GROW
    END GROW

    WATER "Final glitched val:"
    WATER val

    SOIL check = evaluate_val(val)
    IF check == TRUE
        WATER "Spaghetti Daemon threshold exceeded!"
        glitch.random()
    ELSE
        WATER "Garden metrics stable."
    END IF

    DAEMON scanner = NOTHING
END PLANT

SPROUT diagnostics_garden
"""
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", demo_code.strip())
        self.highlight_syntax()

    # --------------------------------------------------------------------------
    # SYNTAX HIGHLIGHTER (THE PRETTIER RAIN)
    # --------------------------------------------------------------------------
    def highlight_syntax(self, event=None) -> None:
        """Dynamic tokenizer scanning the editor buffer and applying tags."""
        content = self.editor.get("1.0", tk.END)
        
        # Remove old tags
        for tag in ["def_keywords", "flow_labels", "literals", "glitch", "comments"]:
            self.editor.tag_remove(tag, "1.0", tk.END)

        # 1. Highlight Comments first so keywords inside comments don't get colorized
        for m in re.finditer(r"//.*", content):
            self.editor.tag_add("comments", f"1.0 + {m.start()} chars", f"1.0 + {m.end()} chars")

        # Helper to search words avoiding comment overlaps
        def tag_matches(pattern, tag_name):
            for m in re.finditer(pattern, content):
                start = m.start()
                end = m.end()
                # Check if it overlaps with comments
                comment_ranges = self.editor.tag_ranges("comments")
                is_commented = False
                # tag_ranges returns pairs of index objects, but we can search index positions
                for i in range(0, len(comment_ranges), 2):
                    c_start = self.editor.index(comment_ranges[i])
                    c_end = self.editor.index(comment_ranges[i+1])
                    m_start = self.editor.index(f"1.0 + {start} chars")
                    if self.editor.compare(m_start, ">=", c_start) and self.editor.compare(m_start, "<", c_end):
                        is_commented = True
                        break
                if not is_commented:
                    self.editor.tag_add(tag_name, f"1.0 + {start} chars", f"1.0 + {end} chars")

        # 2. Definition Keywords
        tag_matches(r"\b(PLANT|END PLANT|SEED|SPROUT|STALK|END STALK|IMPORT)\b", "def_keywords")

        # 3. Flow Labels
        tag_matches(r"\b(IF|ELSE|ELSE IF|END IF|GROW|TIMES|END GROW|WHILE|END WHILE|INFINITE|END INFINITE|RETURN)\b", "flow_labels")

        # 4. Glitch Operator
        tag_matches(r"~~~", "glitch")

        # 5. Literals (Strings & Numbers & Nothing)
        tag_matches(r'"[^"\\]*(?:\\.[^"\\]*)*"', "literals")
        tag_matches(r"\b\d+(\.\d+)?\b", "literals")
        tag_matches(r"\b(TRUE|FALSE|NOTHING)\b", "literals")

    # --------------------------------------------------------------------------
    # FEED LOGGING HELPER
    # --------------------------------------------------------------------------
    def log_message(self, text: str) -> None:
        """Appends log information to the terminal feed pane."""
        self.console.config(state=tk.NORMAL)
        self.console.insert(tk.END, f"{text}\n")
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)

    def clear_feed(self) -> None:
        """Clears terminal console feed."""
        self.console.config(state=tk.NORMAL)
        self.console.delete("1.0", tk.END)
        self.console.config(state=tk.DISABLED)

    # --------------------------------------------------------------------------
    # COMPILER & RUNTIME MANAGEMENT
    # --------------------------------------------------------------------------
    def _disable_buttons(self) -> None:
        self.btn_run.config(state=tk.DISABLED, fg=FG_GREY, highlightbackground=FG_GREY)
        self.btn_compile.config(state=tk.DISABLED, fg=FG_GREY, highlightbackground=FG_GREY)

    def _enable_buttons(self) -> None:
        self.btn_run.config(state=tk.NORMAL, fg=FG_GREEN, highlightbackground=FG_GREEN)
        self.btn_compile.config(state=tk.NORMAL, fg=FG_GREEN, highlightbackground=FG_GREEN)

    def run_compile_check(self) -> bool:
        """Compiles the editor code and reports lexical/syntactic errors."""
        source = self.editor.get("1.0", tk.END)
        
        self.log_message("[COMPILER] Initiating syntax verification...")
        try:
            # Enforce hydration check
            check_system_hydration()
            
            lexer = ChaoLexer(source)
            tokens = lexer.tokenize()
            parser = ChaoParser(tokens)
            ast = parser.parse()
            
            self.log_message("[COMPILER SUCCESS] Program syntax is nominal. AST generated.")
            return True
        except ChaoPlantDehydrationError as e:
            self.log_message(f"[ERROR] COMPILATION BLOCKED: Virtual system plant is dehydrated!\n{str(e)}")
            return False
        except ChaoLexicalError as e:
            self.log_message(f"[ERROR] Lexical Error at line {e.line}, column {e.column}:\n{str(e)}")
            return False
        except ChaoSyntaxError as e:
            self.log_message(f"[ERROR] Syntax Error at line {e.line}, column {e.column}:\n{str(e)}")
            return False
        except Exception as e:
            self.log_message(f"[ERROR] General Compilation Error: {str(e)}")
            return False

    def run_garden(self) -> None:
        """Executes the ChaoScript compiler and kicks off the background interpreter thread."""
        source = self.editor.get("1.0", tk.END)
        
        # Compile check first
        if not self.run_compile_check():
            self.log_message("[ERROR] Run aborted due to compilation failures.")
            return

        # Setup interpreter
        try:
            lexer = ChaoLexer(source)
            tokens = lexer.tokenize()
            parser = ChaoParser(tokens)
            ast_root = parser.parse()

            self.execution_queue = queue.Queue()
            self.interpreter = ChaoInterpreter(ast_root, app_ref=self.app_ref, output_queue=self.execution_queue)
            
            self._disable_buttons()
            self.log_message("[START] Sprouting background execution loop thread...")
            self.interpreter.run_in_background()
            
            # Start queue consumer polling loop
            self.after(50, self.poll_interpreter_queue)
        except Exception as e:
            self.log_message(f"[ERROR] Failed initializing interpreter: {str(e)}")
            self._enable_buttons()

    def poll_interpreter_queue(self) -> None:
        """Periodically polls stdout and glitch commands from the thread queue."""
        if not self.interpreter or not self.execution_queue:
            return

        processed = 0
        while processed < 15:
            try:
                item = self.execution_queue.get_nowait()
                processed += 1
                
                if item is None:
                    # Sentinel detected - execution finished
                    self.log_message("\n[GARDEN SUCCESS] Background execution terminated nominal.")
                    self.interpreter = None
                    self.execution_queue = None
                    self._enable_buttons()
                    return

                if isinstance(item, dict) and item.get("type") == "GLITCH":
                    # Pushed glitch token
                    d = item.get("duration", 300)
                    m = item.get("magnitude", 0.5)
                    self.log_message(f"[TRIGGER exploit] glitch.random() executed. Tearing screen: {d}ms...")
                    
                    if self.app_ref and hasattr(self.app_ref, "glitch_manager"):
                        # Safe scheduled call on main Tkinter thread
                        self.app_ref.root.after(
                            0, 
                            lambda: self.app_ref.glitch_manager.trigger_global_glitch(duration=d, magnitude=m)
                        )
                    continue

                if isinstance(item, str):
                    self.log_message(item)

            except queue.Empty:
                break

        # Dynamically refresh Soil Monitor sidebar with live scope stack
        self.update_soil_monitor()

        # Reschedule next polling tick
        self.after(50, self.poll_interpreter_queue)

    def update_soil_monitor(self) -> None:
        """Extracts environmental values from the runtime engine in real-time."""
        if not self.interpreter:
            return
        
        try:
            self.vars_listbox.delete(0, tk.END)
            
            # 1. Fetch real-time system plant hydration
            hydration = self.interpreter.global_env.get("plant.hydration")
            self.vars_listbox.insert(tk.END, f"H2O: {hydration}%")
            self.vars_listbox.insert(tk.END, "-" * 22)
            
            # 2. Iterate memory vars
            for var_name, var_val in self.interpreter.global_env.vars.items():
                if var_name in {"TRUE", "FALSE", "NOTHING"}:
                    continue # Skip constants
                
                if isinstance(var_val, tuple) and len(var_val) == 2 and isinstance(var_val[0], list):
                    # Stalk Function parameters
                    self.vars_listbox.insert(tk.END, f"stalk {var_name}({', '.join(var_val[0])})")
                else:
                    self.vars_listbox.insert(tk.END, f"seed {var_name} = {var_val}")
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # DAEMON REVIEW EASTER EGG INJECTOR
    # --------------------------------------------------------------------------
    def daemon_review(self) -> None:
        """Easter egg scanning for DAEMON keywords and printing sarcastic critiques."""
        content = self.editor.get("1.0", tk.END)
        self.log_message("\n--- DAEMON REVIEW BY KEVIN ---")
        
        if "DAEMON" not in content:
            critique = random.choice(KEVIN_CRITIQUES)
        else:
            critique = random.choice(KEVIN_DAEMON_OK)
            
        self.log_message(critique)
        self.log_message("------------------------------\n")


# ==============================================================================
# V. STANDALONE RUNNER SYSTEM
# ==============================================================================

if __name__ == "__main__":
    # Initialize main window frame shell
    root = tk.Tk()
    root.title("ChaoScript IDE Explorer Workspace")
    root.geometry("850x650")
    root.config(bg=BG_DARK)

    # Simple Header title
    title_frame = tk.Frame(root, bg=BG_PANEL, highlightthickness=1, highlightbackground=FG_GREEN)
    title_frame.pack(fill="x", padx=5, pady=5)
    tk.Label(
        title_frame, text="CHAO_SCRIPT COMPILER & RUNTIME EXPLORER v1.2", 
        fg=FG_GREEN, bg=BG_PANEL, font=("Courier", 12, "bold")
    ).pack(pady=8)

    # Spawn ChaoScriptModule
    ide_module = ChaoScriptModule(root)
    ide_module.pack(fill="both", expand=True, padx=5, pady=5)

    root.mainloop()
