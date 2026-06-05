import os
import re
import json
import time
import queue
import random
import threading
from typing import List, Dict, Tuple, Optional, Any, Set
from chaoscript_engine import (
    ASTNode, ProgramNode, VariableDeclNode, AssignmentNode, FunctionDeclNode,
    IfStatementNode, WhileLoopNode, GrowLoopNode, InfiniteLoopNode, PrintNode,
    GlitchOpNode, ReturnNode, GrowStatementNode, SproutStatementNode, BinOpNode,
    LiteralNode, IdentifierNode, ArrayNode, FunctionCallNode, ImportNode,
    ChaoLexer, ChaoParser, check_system_hydration, ChaoPlantDehydrationError,
    ChaoCompilationError
)

# ==============================================================================
# I. RUNTIME SIGNALS & EXCEPTIONS
# ==============================================================================

class ChaoRuntimeError(ChaoCompilationError):
    """Raised when evaluation fails during runtime execution."""
    pass

class ChaoReturnSignal(Exception):
    """Special signal used to unwind the visitor stack for functions."""
    def __init__(self, value: Any):
        self.value = value


# ==============================================================================
# II. SCROLLING VARIABLE MEMORY ENVIRONMENT (SOIL MEMORY MATRIX)
# ==============================================================================

class ChaoEnvironment:
    def __init__(self, parent: Optional["ChaoEnvironment"] = None):
        self.parent = parent
        self.vars: Dict[str, Any] = {}

    def declare(self, name: str, value: Any) -> None:
        """Binds a new variable name in the local environment context."""
        self.vars[name] = value

    def get(self, name: str) -> Any:
        """
        Retrieves a variable value from the local environment.
        Supports standard library bindings dynamically.
        """
        # Dynamic Standard Library bindings
        if name == "plant.hydration":
            return self._read_plant_hydration()
            
        if name in self.vars:
            return self.vars[name]
            
        if self.parent:
            return self.parent.get(name)
            
        raise ChaoRuntimeError(f"NameError: Identifier '{name}' is not defined in any active garden scope.")

    def assign(self, name: str, value: Any) -> None:
        """Updates the value of an existing variable, traversing up parent scopes."""
        if name in self.vars:
            self.vars[name] = value
            return
            
        if self.parent:
            self.parent.assign(name, value)
            return
            
        raise ChaoRuntimeError(f"NameError: Cannot reassign undeclared variable '{name}'. Prefix with SOIL to declare.")

    def _read_plant_hydration(self) -> float:
        """Loads system plant hydration value directly from cyberplant_state.json."""
        state_files = [
            "cyberplant_state.json",
            os.path.join(os.path.dirname(__file__), "cyberplant_state.json")
        ]
        for path in state_files:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        return float(data.get("hydration", 50.0))
                except Exception:
                    pass
        return 50.0


# ==============================================================================
# III. THE INTERPRETER VISITOR CORE (THE RAIN ENGINE)
# ==============================================================================

class ChaoInterpreter:
    def __init__(self, program: ProgramNode, app_ref: Optional[Any] = None, output_queue: Optional[queue.Queue] = None):
        self.program = program
        self.app_ref = app_ref
        self.output_queue = output_queue
        
        # Build global environment with language keywords
        self.global_env = ChaoEnvironment()
        self.global_env.declare("NOTHING", None)
        self.global_env.declare("TRUE", True)
        self.global_env.declare("FALSE", False)
        
        self.thread: Optional[threading.Thread] = None

    def run_in_background(self) -> None:
        """Instantiates and launches execution wrapper in isolated background worker."""
        self.thread = threading.Thread(target=self._execute, name="ChaoScript_Interpreter_Worker", daemon=True)
        self.thread.start()

    def _execute(self) -> None:
        """Asynchronous execution loop target processing statements."""
        try:
            # Recheck system hydration at execution startup
            check_system_hydration()
            
            # Initiate AST visitor
            self.visit(self.program, self.global_env)
        except Exception as e:
            if self.output_queue:
                self.output_queue.put(f"[ERROR] Runtime Panic: {str(e)}")
        finally:
            if self.output_queue:
                # Push execution completion sentinel
                self.output_queue.put(None)

    def visit(self, node: ASTNode, env: ChaoEnvironment) -> Any:
        """Dynamic double-dispatch visitor router."""
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, env)

    def generic_visit(self, node: ASTNode, env: ChaoEnvironment) -> Any:
        raise ChaoRuntimeError(f"Interpreter Panic: No visitor defined for node '{type(node).__name__}'")

    # --------------------------------------------------------------------------
    # STATEMENT VISITORS
    # --------------------------------------------------------------------------
    def visit_ProgramNode(self, node: ProgramNode, env: ChaoEnvironment) -> Any:
        if hasattr(node, "name"):
            # This is a plant boundary module declaration. Save it for sprouting later.
            env.declare(node.name, node)
            return None
            
        for stmt in node.statements:
            self.visit(stmt, env)
        return None

    def visit_VariableDeclNode(self, node: VariableDeclNode, env: ChaoEnvironment) -> Any:
        val = self.visit(node.expression, env)
        env.declare(node.identifier, val)
        return val

    def visit_AssignmentNode(self, node: AssignmentNode, env: ChaoEnvironment) -> Any:
        val = self.visit(node.expression, env)
        env.assign(node.identifier, val)
        return val

    def visit_FunctionDeclNode(self, node: FunctionDeclNode, env: ChaoEnvironment) -> Any:
        env.declare(node.name, (node.params, node.body))
        return None

    def visit_ImportNode(self, node: ImportNode, env: ChaoEnvironment) -> Any:
        if node.module_name not in {"plant", "glitch"}:
            raise ChaoRuntimeError(
                f"ImportError: Unknown module '{node.module_name}'. Available: [plant, glitch]"
            )
        return None

    def visit_SproutStatementNode(self, node: SproutStatementNode, env: ChaoEnvironment) -> Any:
        # Resolves garden module boundary and sprouts it
        plant_node = env.get(node.name)
        if not isinstance(plant_node, ProgramNode):
            raise ChaoRuntimeError(f"TypeError: Identifier '{node.name}' is not a valid plant module.")
            
        # Isolate variables inside sprouted garden
        sprout_env = ChaoEnvironment(parent=env)
        for stmt in plant_node.statements:
            self.visit(stmt, sprout_env)
        return None

    def visit_PrintNode(self, node: PrintNode, env: ChaoEnvironment) -> Any:
        val = self.visit(node.expression, env)
        msg = f"🌱 {val}"
        if self.output_queue:
            self.output_queue.put(msg)
        else:
            try:
                print(msg)
            except UnicodeEncodeError:
                print(f"[PLANT] {val}")
        return None

    def visit_ReturnNode(self, node: ReturnNode, env: ChaoEnvironment) -> Any:
        val = self.visit(node.expression, env) if node.expression else None
        raise ChaoReturnSignal(val)

    def visit_GrowStatementNode(self, node: GrowStatementNode, env: ChaoEnvironment) -> Any:
        # Pause background thread dynamically for 100ms
        time.sleep(0.1)
        return None

    # --------------------------------------------------------------------------
    # CONTROL FLOW VISITORS
    # --------------------------------------------------------------------------
    def visit_IfStatementNode(self, node: IfStatementNode, env: ChaoEnvironment) -> Any:
        cond_val = self.visit(node.condition, env)
        if cond_val:
            for stmt in node.then_branch:
                self.visit(stmt, env)
            return None
            
        for elif_cond, elif_body in node.else_if_branches:
            if self.visit(elif_cond, env):
                for stmt in elif_body:
                    self.visit(stmt, env)
                return None
                
        if node.else_branch:
            for stmt in node.else_branch:
                self.visit(stmt, env)
        return None

    def visit_WhileLoopNode(self, node: WhileLoopNode, env: ChaoEnvironment) -> Any:
        while self.visit(node.condition, env):
            for stmt in node.body:
                self.visit(stmt, env)
        return None

    def visit_GrowLoopNode(self, node: GrowLoopNode, env: ChaoEnvironment) -> Any:
        count = self.visit(node.count_expr, env)
        if not isinstance(count, int):
            raise ChaoRuntimeError(
                f"TypeError: GROW loop iteration count must resolve to SEED integer, got {type(count).__name__}."
            )
        for _ in range(count):
            for stmt in node.body:
                self.visit(stmt, env)
        return None

    def visit_InfiniteLoopNode(self, node: InfiniteLoopNode, env: ChaoEnvironment) -> Any:
        while True:
            for stmt in node.body:
                self.visit(stmt, env)

    # --------------------------------------------------------------------------
    # EXPRESSION EVALUATOR VISITORS
    # --------------------------------------------------------------------------
    def visit_BinOpNode(self, node: BinOpNode, env: ChaoEnvironment) -> Any:
        left = self.visit(node.left, env)
        right = self.visit(node.right, env)
        op = node.op

        try:
            if op == "+":
                return left + right
            elif op == "-":
                return left - right
            elif op == "*":
                return left * right
            elif op == "/":
                if right == 0 or right == 0.0:
                    raise ChaoRuntimeError("DivisionByZeroError: Dehydration panic! Division by zero.")
                return left / right
            elif op == "%":
                if right == 0 or right == 0.0:
                    raise ChaoRuntimeError("DivisionByZeroError: Dehydration panic! Modulo division by zero.")
                return left % right
            elif op == "==":
                return left == right
            elif op == "!=":
                return left != right
            elif op == "<":
                return left < right
            elif op == "<=":
                return left <= right
            elif op == ">":
                return left > right
            elif op == ">=":
                return left >= right
            else:
                raise ChaoRuntimeError(f"Unsupported binary operator '{op}'")
        except TypeError as e:
            raise ChaoRuntimeError(
                f"TypeError: Invalid operation '{left} {op} {right}' (types: {type(left).__name__}, {type(right).__name__}): {e}"
            )

    def visit_GlitchOpNode(self, node: GlitchOpNode, env: ChaoEnvironment) -> Any:
        """The Glitch Operator Mutation Layer (~ ~ ~)"""
        val = self.visit(node.expression, env)

        if isinstance(val, (int, float)):
            # 15% chance of replacing with massive index integer block
            if random.random() < 0.15:
                return random.randint(100000, 99999999)
            
            # Otherwise, apply a random mathematical drift variance between -100% and +100%
            drift = random.uniform(-1.0, 1.0)
            mutated = val * (1.0 + drift)
            if isinstance(val, int):
                return int(mutated)
            return mutated

        elif isinstance(val, str):
            # Corrupt vowels with raw Unicode glitches, ANSI static blocks, and leetspeak
            mutated_chars = []
            glitch_pool = ["3", "1", "0", "☠", "€", "☣", "█", "░", "▒", "▓", "⚡", "👽", "👾", "Æ"]
            for char in val:
                if char.lower() in "aeiouy":
                    mutated_chars.append(random.choice(glitch_pool))
                else:
                    if random.random() < 0.1: # 10% chance to corrupt non-vowels
                        mutated_chars.append(random.choice(["☠", "⚡", "☣", "3", "1", "0"]))
                    else:
                        mutated_chars.append(char)
            return "".join(mutated_chars)

        elif isinstance(val, bool):
            # Mutate boolean values by random inversion
            return random.choice([True, False])

        return val

    def visit_LiteralNode(self, node: LiteralNode, env: ChaoEnvironment) -> Any:
        return node.value

    def visit_IdentifierNode(self, node: IdentifierNode, env: ChaoEnvironment) -> Any:
        return env.get(node.name)

    def visit_ArrayNode(self, node: ArrayNode, env: ChaoEnvironment) -> Any:
        return [self.visit(el, env) for el in node.elements]

    def visit_FunctionCallNode(self, node: FunctionCallNode, env: ChaoEnvironment) -> Any:
        # Check Standard Library bindings
        if node.name == "plant.water":
            self._water_plant()
            return None
        elif node.name == "glitch.random":
            self._trigger_glitch_tear()
            return None

        # Custom function stalk evaluation
        func_meta = env.get(node.name)
        if not isinstance(func_meta, tuple) or len(func_meta) != 2:
            raise ChaoRuntimeError(f"TypeError: Identifier '{node.name}' is not a callable stalk.")

        params, body = func_meta
        if len(node.args) != len(params):
            raise ChaoRuntimeError(
                f"TypeError: Stalk '{node.name}' expects {len(params)} arguments, got {len(node.args)}."
            )

        # Build function scope and bind arguments (functions resolve in global lexical scope)
        func_env = ChaoEnvironment(parent=self.global_env)
        for param, arg in zip(params, node.args):
            func_env.declare(param, self.visit(arg, env))

        # Evaluate body, capturing return signal exception
        try:
            for stmt in body:
                self.visit(stmt, func_env)
        except ChaoReturnSignal as signal:
            return signal.value
            
        return None

    # --------------------------------------------------------------------------
    # STANDARD LIBRARY ROUTINES
    # --------------------------------------------------------------------------
    def _water_plant(self) -> None:
        """Invokes ChaoHub's inject_h2o telemetry or updates state file directly."""
        if self.app_ref and hasattr(self.app_ref, "cyber_plant") and hasattr(self.app_ref.cyber_plant, "inject_h2o"):
            # Tkinter safe invocation from background worker thread
            self.app_ref.root.after(0, self.app_ref.cyber_plant.inject_h2o)
            if self.output_queue:
                self.output_queue.put("[SYSTEM] plant.water() triggered local UI water injection.")
        else:
            # Direct file-writing fallback for standalone run
            state_file = "cyberplant_state.json"
            state_data = {"growth_points": 0.0, "hydration": 50.0, "radiation_level": 0.0, "alive": True}
            if os.path.exists(state_file):
                try:
                    with open(state_file, "r", encoding="utf-8") as f:
                        state_data = json.load(f)
                except Exception:
                    pass
            
            prev_hyd = float(state_data.get("hydration", 50.0))
            new_hyd = min(100.0, prev_hyd + 15.0)
            state_data["hydration"] = new_hyd
            state_data["alive"] = True
            
            try:
                with open(state_file, "w", encoding="utf-8") as f:
                    json.dump(state_data, f, indent=4)
                if self.output_queue:
                    self.output_queue.put(
                        f"[SYSTEM] plant.water() fallback: H2O injected (hydration {prev_hyd}% -> {new_hyd}%)."
                    )
            except Exception as e:
                if self.output_queue:
                    self.output_queue.put(f"[ERROR] Failed writing hydration update to disk: {e}")

    def _trigger_glitch_tear(self) -> None:
        """Invokes ChaoHub's GlitchManager screen tear or pushes structured queue commands."""
        if self.app_ref and hasattr(self.app_ref, "glitch_manager") and hasattr(self.app_ref.glitch_manager, "trigger_global_glitch"):
            # Tkinter thread-safe dispatch on main GUI loop
            self.app_ref.root.after(
                0, 
                lambda: self.app_ref.glitch_manager.trigger_global_glitch(duration=300, magnitude=0.5)
            )
            if self.output_queue:
                self.output_queue.put("[SYSTEM] glitch.random() triggered active GUI screen tear exploit.")
        else:
            # Standalone fallback: push command packet to queue for processing
            if self.output_queue:
                self.output_queue.put({"type": "GLITCH", "duration": 300, "magnitude": 0.5})
                self.output_queue.put("[SYSTEM] glitch.random() pushed command token to output queue.")


# ==============================================================================
# IV. INTEGRATED RUNTIME DIAGNOSTIC SIMULATION
# ==============================================================================

if __name__ == "__main__":
    print("==============================================================================")
    print("[GARDEN] CHAOSCRIPT RUNTIME INTERPRETER DIAGNOSTIC - PHASE 2")
    print("==============================================================================")

    # 1. Setup dummy plant state if missing
    dummy_file = "cyberplant_state.json"
    had_state = os.path.exists(dummy_file)
    if not had_state:
        print("Writing default mock plant state file to disk...")
        with open(dummy_file, "w", encoding="utf-8") as f:
            json.dump({"growth_points": 25.0, "hydration": 40.0, "radiation_level": 10.0, "alive": True}, f, indent=4)

    # 2. Mock source containing loops, math, GROW timer and Glitch mutation operator
    diagnostic_source = """// Diagnostic Garden Script
IMPORT plant
IMPORT glitch

PLANT diagnostic_garden
    SEED x = 100
    WATER "Starting hydration is:"
    WATER plant.hydration

    WATER "Beginning mutation loop..."
    GROW 5 TIMES
        WATER x
        SOIL x = ~~~x
        GROW // Pause loop slightly
    END GROW

    WATER "Final glitched value of x is:"
    WATER x
    
    // Trigger standard library modules
    plant.water()
    glitch.random()
END PLANT

SPROUT diagnostic_garden
"""

    print("\nParsing diagnostic program source...")
    lexer = ChaoLexer(diagnostic_source)
    tokens = lexer.tokenize()
    parser = ChaoParser(tokens)
    program_ast = parser.parse()
    print("AST generated successfully.")

    # Create thread-safe communication queue
    comm_queue = queue.Queue()

    print("\n[START] Launching interpreter on background worker thread...")
    interpreter = ChaoInterpreter(program_ast, output_queue=comm_queue)
    interpreter.run_in_background()

    # Poll communication queue live
    print("\n--- Live Runtime Console Feed ---")
    while True:
        try:
            # Wait for output packet
            item = comm_queue.get(timeout=3.0)
            if item is None:
                # Finished executing
                break
            
            # Print item safely
            if isinstance(item, dict):
                print(f"[CMD] [COMMAND PACKET] {item}")
            else:
                try:
                    print(item)
                except UnicodeEncodeError:
                    # ASCII fallback
                    print(item.replace("🌱", "[PLANT]"))
        except queue.Empty:
            print("[WARN] Worker thread timeout - no packet received.")
            break

    print("---------------------------------")
    print("[FINISHED] Interpreter execution worker terminated.")

    # Print out final environment variable memory stack
    print("\nFinal Environment Variable memory stack:")
    for var_name, var_val in interpreter.global_env.vars.items():
        print(f"  {var_name} = {var_val}")

    # Cleanup mock plant state file if we created it
    if not had_state and os.path.exists(dummy_file):
        try:
            os.remove(dummy_file)
            print("\nRemoved dummy mock plant state file.")
        except Exception:
            pass

    print("\n==============================================================================")
    print("[OK] DIAGNOSTICS COMPLETED SUCCESSFULLY")
    print("==============================================================================")
