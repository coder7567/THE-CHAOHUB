import os
import re
import json
import random
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Any, Set

# ==============================================================================
# I. CUSTOM EXCEPTIONS FOR THE GARDEN
# ==============================================================================

class ChaoCompilationError(Exception):
    """Base exception class for all ChaoScript compilation and syntax issues."""
    pass

class ChaoPlantDehydrationError(ChaoCompilationError):
    """Raised when the virtual system plant hydration is 0 or deceased."""
    pass

class ChaoLexicalError(ChaoCompilationError):
    """Raised when tokenization fails due to invalid characters."""
    def __init__(self, message: str, line: int, column: int):
        super().__init__(message)
        self.line = line
        self.column = column

class ChaoSyntaxError(ChaoCompilationError):
    """Raised when parsing fails due to syntax or block mismatch errors."""
    def __init__(self, message: str, line: int, column: int):
        super().__init__(message)
        self.line = line
        self.column = column


# ==============================================================================
# II. VIRTUAL PLANT HYDRATION SENSORS
# ==============================================================================

def check_system_hydration() -> float:
    """
    Checks the local system plant hydration state from 'cyberplant_state.json'.
    If hydration hits 0, compilation fails immediately.
    """
    state_files = [
        "cyberplant_state.json",
        os.path.join(os.path.dirname(__file__), "cyberplant_state.json")
    ]
    hydration = 50.0
    alive = True
    found_file = False

    for path in state_files:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    hydration = float(data.get("hydration", 50.0))
                    alive = bool(data.get("alive", True))
                    found_file = True
                    break
            except Exception:
                pass # Try next fallback path

    if not alive or hydration <= 0.0:
        raise ChaoPlantDehydrationError(
            f"[ERROR] compilation failed: The virtual system plant is deceased or dehydrated.\n"
            f"   [ Hydration Level: {hydration}% | Vital Status: {'ALIVE' if alive else 'DEAD'} ]\n"
            f"   Please inject H2O into your cyberplant state immediately."
        )
    return hydration


# ==============================================================================
# III. THE LEXER (THE RAIN)
# ==============================================================================

class ChaoTokenType(Enum):
    # Program Boundaries
    PLANT = auto()
    END_PLANT = auto()
    SPROUT = auto()  # Used as SPROUT [float type] and SPROUT [module name]

    # Type Identifiers
    SEED = auto()    # Integer
    WATER = auto()   # String / Print operator
    SOIL = auto()    # Boolean / Reassignment prefix
    BED = auto()     # Collection/Array
    DAEMON = auto()  # Null type identifier

    # Function Blocks
    STALK = auto()
    RETURN = auto()
    END_STALK = auto()

    # Control Flow
    IF = auto()
    ELSE_IF = auto()
    ELSE = auto()
    END_IF = auto()

    # The Patience Mechanic & Vines Loops
    GROW = auto()
    TIMES = auto()
    END_GROW = auto()
    WHILE = auto()
    END_WHILE = auto()
    INFINITE = auto()
    END_INFINITE = auto()

    # Literals
    IDENTIFIER = auto()
    INT_LIT = auto()
    FLOAT_LIT = auto()
    STRING_LIT = auto()
    TRUE = auto()
    FALSE = auto()
    NOTHING = auto() # Null value literal

    # Mathematical Operators
    PLUS = auto()
    MINUS = auto()
    MULT = auto()
    DIV = auto()
    MOD = auto()
    ASSIGN = auto()
    GLITCH = auto()  # '~~~' Mutation operator

    # Comparisons
    EQ = auto()
    NE = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()

    # Punctuation
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()

    # Stream Bounds
    EOF = auto()


@dataclass
class ChaoToken:
    type: ChaoTokenType
    value: str
    line_number: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, '{self.value}', L:{self.line_number}:C:{self.column})"


class ChaoLexer:
    def __init__(self, source_code: str, comment_bypass_chance: float = 0.001):
        self.source_code = source_code
        self.comment_bypass_chance = comment_bypass_chance
        self.tokens: List[ChaoToken] = []
        
        # Compile token matching patterns in order of priority
        self.rules = [
            (ChaoTokenType.END_PLANT, r"END\s+PLANT\b"),
            (ChaoTokenType.END_STALK, r"END\s+STALK\b"),
            (ChaoTokenType.END_GROW, r"END\s+GROW\b"),
            (ChaoTokenType.END_WHILE, r"END\s+WHILE\b"),
            (ChaoTokenType.END_INFINITE, r"END\s+INFINITE\b"),
            (ChaoTokenType.END_IF, r"END\s+IF\b"),
            (ChaoTokenType.ELSE_IF, r"ELSE\s+IF\b"),

            (ChaoTokenType.PLANT, r"PLANT\b"),
            (ChaoTokenType.SPROUT, r"SPROUT\b"),
            (ChaoTokenType.SEED, r"SEED\b"),
            (ChaoTokenType.WATER, r"WATER\b"),
            (ChaoTokenType.SOIL, r"SOIL\b"),
            (ChaoTokenType.BED, r"BED\b"),
            (ChaoTokenType.DAEMON, r"DAEMON\b"),
            (ChaoTokenType.NOTHING, r"NOTHING\b"),
            (ChaoTokenType.STALK, r"STALK\b"),
            (ChaoTokenType.RETURN, r"RETURN\b"),
            (ChaoTokenType.IF, r"IF\b"),
            (ChaoTokenType.ELSE, r"ELSE\b"),
            (ChaoTokenType.GROW, r"GROW\b"),
            (ChaoTokenType.TIMES, r"TIMES\b"),
            (ChaoTokenType.WHILE, r"WHILE\b"),
            (ChaoTokenType.INFINITE, r"INFINITE\b"),
            (ChaoTokenType.TRUE, r"TRUE\b"),
            (ChaoTokenType.FALSE, r"FALSE\b"),

            (ChaoTokenType.FLOAT_LIT, r"\d+\.\d+"),
            (ChaoTokenType.INT_LIT, r"\d+"),
            (ChaoTokenType.STRING_LIT, r'"[^"\\]*(?:\\.[^"\\]*)*"'),

            (ChaoTokenType.GLITCH, r"~~~"),
            (ChaoTokenType.EQ, r"=="),
            (ChaoTokenType.NE, r"!="),
            (ChaoTokenType.LE, r"<="),
            (ChaoTokenType.GE, r">="),
            (ChaoTokenType.LT, r"<"),
            (ChaoTokenType.GT, r">"),
            (ChaoTokenType.ASSIGN, r"="),
            (ChaoTokenType.PLUS, r"\+"),
            (ChaoTokenType.MINUS, r"-"),
            (ChaoTokenType.MULT, r"\*"),
            (ChaoTokenType.DIV, r"/"),
            (ChaoTokenType.MOD, r"%"),

            (ChaoTokenType.LPAREN, r"\("),
            (ChaoTokenType.RPAREN, r"\)"),
            (ChaoTokenType.LBRACKET, r"\["),
            (ChaoTokenType.RBRACKET, r"\]"),
            (ChaoTokenType.COMMA, r","),

            (ChaoTokenType.IDENTIFIER, r"[a-zA-Z_][a-zA-Z0-9_]*"),
        ]

    def _lex_line(self, line_text: str, line_num: int, start_col: int) -> List[ChaoToken]:
        tokens = []
        index = 0
        n = len(line_text)

        while index < n:
            # Skip spaces & tabs
            whitespace_match = re.match(r"[ \t\r]+", line_text[index:])
            if whitespace_match:
                index += len(whitespace_match.group(0))
                continue

            if index >= n:
                break

            # Handle Comments & Kevin's 0.1% execute-comment bug
            if line_text[index:].startswith("//"):
                comment_content = line_text[index + 2:]
                has_keywords = "WATER" in comment_content or "GLITCH" in comment_content
                
                # Check for comment bypass mutation
                if has_keywords and (random.random() < self.comment_bypass_chance):
                    # Bypassed! Bypassed text is scanned recursively as code on the same line
                    bypass_tokens = self._lex_line(comment_content, line_num, start_col + index + 2)
                    tokens.extend(bypass_tokens)
                break  # Standard comment ignores the rest of the line

            # Match character slice against token rules
            matched = False
            for token_type, pattern in self.rules:
                match = re.match(pattern, line_text[index:])
                if match:
                    value = match.group(0)
                    col = start_col + index
                    tokens.append(ChaoToken(type=token_type, value=value, line_number=line_num, column=col))
                    index += len(value)
                    matched = True
                    break

            if not matched:
                col = start_col + index
                raise ChaoLexicalError(
                    f"Unexpected character '{line_text[index]}' during garden tokenization",
                    line_num, col
                )

        return tokens

    def tokenize(self) -> List[ChaoToken]:
        """Runs lexical scans over all lines, adding an EOF token at completion."""
        # Enforce plant hydration dead-switch logic
        check_system_hydration()

        lines = self.source_code.splitlines()
        for i, line in enumerate(lines):
            line_num = i + 1
            self.tokens.extend(self._lex_line(line, line_num, 1))

        # Build absolute end-of-file offsets
        if self.tokens:
            last = self.tokens[-1]
            eof_line = last.line_number
            eof_col = last.column + len(last.value)
        else:
            eof_line = 1
            eof_col = 1

        self.tokens.append(ChaoToken(type=ChaoTokenType.EOF, value="", line_number=eof_line, column=eof_col))
        return self.tokens


# ==============================================================================
# IV. THE ABSTRACT SYNTAX TREE (THE SOIL LAYOUT)
# ==============================================================================

class ASTNode:
    def to_dict(self) -> dict:
        raise NotImplementedError()


@dataclass
class ProgramNode(ASTNode):
    statements: List[ASTNode]

    def get_daemon_references(self) -> List[str]:
        """Background tracker to scan AST variables bound to NOTHING/DAEMON paths."""
        references = []
        def walk(node):
            if isinstance(node, VariableDeclNode):
                if node.var_type == "DAEMON" or (isinstance(node.expression, LiteralNode) and node.expression.value is None):
                    references.append(f"Declared: {node.identifier}")
                walk(node.expression)
            elif isinstance(node, AssignmentNode):
                if isinstance(node.expression, LiteralNode) and node.expression.value is None:
                    references.append(f"Assigned to NOTHING: {node.identifier}")
                walk(node.expression)
            elif isinstance(node, FunctionDeclNode):
                for stmt in node.body:
                    walk(stmt)
            elif isinstance(node, IfStatementNode):
                walk(node.condition)
                for stmt in node.then_branch:
                    walk(stmt)
                for cond, branch in node.else_if_branches:
                    walk(cond)
                    for stmt in branch:
                        walk(stmt)
                if node.else_branch:
                    for stmt in node.else_branch:
                        walk(stmt)
            elif isinstance(node, WhileLoopNode):
                walk(node.condition)
                for stmt in node.body:
                    walk(stmt)
            elif isinstance(node, GrowLoopNode):
                walk(node.count_expr)
                for stmt in node.body:
                    walk(stmt)
            elif isinstance(node, InfiniteLoopNode):
                for stmt in node.body:
                    walk(stmt)
            elif isinstance(node, PrintNode):
                walk(node.expression)
            elif isinstance(node, GlitchOpNode):
                walk(node.expression)
            elif isinstance(node, ReturnNode):
                if node.expression:
                    walk(node.expression)
            elif isinstance(node, BinOpNode):
                walk(node.left)
                walk(node.right)
            elif isinstance(node, ArrayNode):
                for el in node.elements:
                    walk(el)
            elif isinstance(node, FunctionCallNode):
                for arg in node.args:
                    walk(arg)

        for stmt in self.statements:
            walk(stmt)
        return references

    def to_dict(self) -> dict:
        return {
            "type": "ProgramNode",
            "statements": [s.to_dict() for s in self.statements],
            "spaghetti_daemon_tracker": {
                "active_daemons": self.get_daemon_references()
            }
        }


@dataclass
class VariableDeclNode(ASTNode):
    var_type: str
    identifier: str
    expression: ASTNode

    def to_dict(self) -> dict:
        return {
            "type": "VariableDeclNode",
            "var_type": self.var_type,
            "identifier": self.identifier,
            "expression": self.expression.to_dict()
        }


@dataclass
class AssignmentNode(ASTNode):
    identifier: str
    expression: ASTNode

    def to_dict(self) -> dict:
        return {
            "type": "AssignmentNode",
            "identifier": self.identifier,
            "expression": self.expression.to_dict()
        }


@dataclass
class FunctionDeclNode(ASTNode):
    name: str
    params: List[str]
    body: List[ASTNode]

    def to_dict(self) -> dict:
        return {
            "type": "FunctionDeclNode",
            "name": self.name,
            "params": self.params,
            "body": [s.to_dict() for s in self.body]
        }


@dataclass
class IfStatementNode(ASTNode):
    condition: ASTNode
    then_branch: List[ASTNode]
    else_if_branches: List[Tuple[ASTNode, List[ASTNode]]]
    else_branch: Optional[List[ASTNode]]

    def to_dict(self) -> dict:
        return {
            "type": "IfStatementNode",
            "condition": self.condition.to_dict(),
            "then_branch": [s.to_dict() for s in self.then_branch],
            "else_if_branches": [(c.to_dict(), [s.to_dict() for s in b]) for c, b in self.else_if_branches],
            "else_branch": [s.to_dict() for s in self.else_branch] if self.else_branch else None
        }


@dataclass
class WhileLoopNode(ASTNode):
    condition: ASTNode
    body: List[ASTNode]

    def to_dict(self) -> dict:
        return {
            "type": "WhileLoopNode",
            "condition": self.condition.to_dict(),
            "body": [s.to_dict() for s in self.body]
        }


@dataclass
class GrowLoopNode(ASTNode):
    count_expr: ASTNode
    body: List[ASTNode]

    def to_dict(self) -> dict:
        return {
            "type": "GrowLoopNode",
            "count_expr": self.count_expr.to_dict(),
            "body": [s.to_dict() for s in self.body]
        }


@dataclass
class InfiniteLoopNode(ASTNode):
    body: List[ASTNode]

    def to_dict(self) -> dict:
        return {
            "type": "InfiniteLoopNode",
            "body": [s.to_dict() for s in self.body]
        }


@dataclass
class PrintNode(ASTNode):
    expression: ASTNode

    def to_dict(self) -> dict:
        return {
            "type": "PrintNode",
            "expression": self.expression.to_dict()
        }


@dataclass
class GlitchOpNode(ASTNode):
    expression: ASTNode

    def to_dict(self) -> dict:
        return {
            "type": "GlitchOpNode",
            "expression": self.expression.to_dict()
        }


@dataclass
class ReturnNode(ASTNode):
    expression: Optional[ASTNode]

    def to_dict(self) -> dict:
        return {
            "type": "ReturnNode",
            "expression": self.expression.to_dict() if self.expression else None
        }


@dataclass
class GrowStatementNode(ASTNode):
    def to_dict(self) -> dict:
        return {"type": "GrowStatementNode"}


@dataclass
class SproutStatementNode(ASTNode):
    name: str

    def to_dict(self) -> dict:
        return {
            "type": "SproutStatementNode",
            "name": self.name
        }


@dataclass
class BinOpNode(ASTNode):
    left: ASTNode
    op: str
    right: ASTNode

    def to_dict(self) -> dict:
        return {
            "type": "BinOpNode",
            "left": self.left.to_dict(),
            "op": self.op,
            "right": self.right.to_dict()
        }


@dataclass
class LiteralNode(ASTNode):
    value: Any

    def to_dict(self) -> dict:
        return {
            "type": "LiteralNode",
            "value": self.value
        }


@dataclass
class IdentifierNode(ASTNode):
    name: str

    def to_dict(self) -> dict:
        return {
            "type": "IdentifierNode",
            "name": self.name
        }


@dataclass
class ArrayNode(ASTNode):
    elements: List[ASTNode]

    def to_dict(self) -> dict:
        return {
            "type": "ArrayNode",
            "elements": [e.to_dict() for e in self.elements]
        }


@dataclass
class FunctionCallNode(ASTNode):
    name: str
    args: List[ASTNode]

    def to_dict(self) -> dict:
        return {
            "type": "FunctionCallNode",
            "name": self.name,
            "args": [a.to_dict() for a in self.args]
        }


# ==============================================================================
# V. THE PARSER (THE SOIL ENGINE)
# ==============================================================================

class ChaoParser:
    def __init__(self, tokens: List[ChaoToken]):
        self.tokens = tokens
        self.current_index = 0
        self.symbol_table: Set[str] = set()

    # --------------------------------------------------------------------------
    # CURSOR HELPERS
    # --------------------------------------------------------------------------
    def current_token(self) -> ChaoToken:
        if self.current_index < len(self.tokens):
            return self.tokens[self.current_index]
        return self.tokens[-1]

    def previous_token(self) -> ChaoToken:
        if self.current_index > 0:
            return self.tokens[self.current_index - 1]
        return self.tokens[0]

    def peek_token(self, offset: int) -> ChaoToken:
        idx = self.current_index + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]

    def match_token(self, token_type: ChaoTokenType) -> bool:
        if self.current_token().type == token_type:
            self.current_index += 1
            return True
        return False

    def match_any(self, *token_types: ChaoTokenType) -> bool:
        if self.current_token().type in token_types:
            self.current_index += 1
            return True
        return False

    def match_any_no_consume(self, *token_types: ChaoTokenType) -> bool:
        return self.current_token().type in token_types

    def consume(self, token_type: ChaoTokenType, err_msg: str) -> ChaoToken:
        tok = self.current_token()
        if tok.type == token_type:
            self.current_index += 1
            return tok
        raise ChaoSyntaxError(
            f"Expected {token_type.name} - {err_msg} at line {tok.line_number}, col {tok.column} (got '{tok.value}')",
            tok.line_number, tok.column
        )

    def consume_any(self, token_types: Set[ChaoTokenType], err_msg: str) -> ChaoToken:
        tok = self.current_token()
        if tok.type in token_types:
            self.current_index += 1
            return tok
        types_str = ", ".join(t.name for t in token_types)
        raise ChaoSyntaxError(
            f"Expected one of [{types_str}] - {err_msg} at line {tok.line_number}, col {tok.column} (got '{tok.value}')",
            tok.line_number, tok.column
        )

    def is_expression_starter(self, token: ChaoToken) -> bool:
        return token.type in {
            ChaoTokenType.INT_LIT,
            ChaoTokenType.FLOAT_LIT,
            ChaoTokenType.STRING_LIT,
            ChaoTokenType.TRUE,
            ChaoTokenType.FALSE,
            ChaoTokenType.NOTHING,
            ChaoTokenType.IDENTIFIER,
            ChaoTokenType.LPAREN,
            ChaoTokenType.LBRACKET,
            ChaoTokenType.GLITCH,
            ChaoTokenType.MINUS
        }

    def is_grow_loop(self) -> bool:
        """Determines if a GROW token starts a loop or is a standalone execution pause."""
        idx = self.current_index + 1
        n = len(self.tokens)
        while idx < n:
            tok = self.tokens[idx]
            if tok.type == ChaoTokenType.TIMES:
                return True
            # Stop scanner early if we hit declaration keywords or structural boundaries
            if tok.type in {
                ChaoTokenType.PLANT, ChaoTokenType.END_PLANT, ChaoTokenType.STALK, ChaoTokenType.END_STALK,
                ChaoTokenType.SEED, ChaoTokenType.SPROUT, ChaoTokenType.WATER, ChaoTokenType.SOIL,
                ChaoTokenType.BED, ChaoTokenType.DAEMON, ChaoTokenType.IF, ChaoTokenType.END_IF,
                ChaoTokenType.WHILE, ChaoTokenType.END_WHILE, ChaoTokenType.INFINITE, ChaoTokenType.END_INFINITE,
                ChaoTokenType.GROW, ChaoTokenType.END_GROW, ChaoTokenType.EOF
            }:
                return False
            idx += 1
        return False

    # --------------------------------------------------------------------------
    # COMPONENT PARSERS
    # --------------------------------------------------------------------------
    def parse(self) -> ProgramNode:
        """Entry point of the parser engine."""
        if not self.tokens or (len(self.tokens) == 1 and self.tokens[0].type == ChaoTokenType.EOF):
            return ProgramNode(statements=[])

        statements = []
        while self.current_token().type != ChaoTokenType.EOF:
            tok = self.current_token()
            if tok.type in {
                ChaoTokenType.END_PLANT, ChaoTokenType.END_STALK, ChaoTokenType.END_IF,
                ChaoTokenType.END_GROW, ChaoTokenType.END_WHILE, ChaoTokenType.END_INFINITE,
                ChaoTokenType.ELSE_IF, ChaoTokenType.ELSE
            }:
                raise ChaoSyntaxError(
                    f"Orphan block termination flag '{tok.value}' without matching opening statement block",
                    tok.line_number, tok.column
                )
            statements.append(self.parse_statement())

        return ProgramNode(statements=statements)

    def parse_statement(self) -> ASTNode:
        tok = self.current_token()

        if tok.type == ChaoTokenType.PLANT:
            return self.parse_plant_decl()

        elif tok.type == ChaoTokenType.SPROUT:
            # Check if declaration e.g. "SPROUT pi = 3.14" or execution "SPROUT my_garden"
            next_t = self.peek_token(1)
            next_next_t = self.peek_token(2)
            if next_t.type == ChaoTokenType.IDENTIFIER and next_next_t.type == ChaoTokenType.ASSIGN:
                return self.parse_var_decl()
            return self.parse_sprout_statement()

        elif tok.type in {ChaoTokenType.SEED, ChaoTokenType.BED, ChaoTokenType.DAEMON}:
            return self.parse_var_decl()

        elif tok.type == ChaoTokenType.SOIL:
            # SOIL serves both as boolean variable declaration AND as reassignment keyword
            # We separate them by checking if the identifier is already in our symbol table
            next_t = self.peek_token(1)
            if next_t.type == ChaoTokenType.IDENTIFIER:
                if next_t.value in self.symbol_table:
                    return self.parse_reassignment()
                return self.parse_var_decl()
            raise ChaoSyntaxError(
                f"Expected identifier after 'SOIL' reassignment/declaration marker",
                tok.line_number, tok.column
            )

        elif tok.type == ChaoTokenType.WATER:
            # WATER is the string type identifier AND the printing command.
            # If followed by 'identifier = ', it is string variable declaration. Otherwise, print statement.
            next_t = self.peek_token(1)
            next_next_t = self.peek_token(2)
            if next_t.type == ChaoTokenType.IDENTIFIER and next_next_t.type == ChaoTokenType.ASSIGN:
                return self.parse_var_decl()
            return self.parse_print_statement()

        elif tok.type == ChaoTokenType.STALK:
            return self.parse_function_decl()

        elif tok.type == ChaoTokenType.RETURN:
            return self.parse_return_statement()

        elif tok.type == ChaoTokenType.IF:
            return self.parse_if_statement()

        elif tok.type == ChaoTokenType.WHILE:
            return self.parse_while_loop()

        elif tok.type == ChaoTokenType.INFINITE:
            return self.parse_infinite_loop()

        elif tok.type == ChaoTokenType.GROW:
            if self.is_grow_loop():
                return self.parse_grow_loop()
            return self.parse_grow_statement()

        else:
            # Fallback to standalone expression evaluation
            return self.parse_expression()

    # --------------------------------------------------------------------------
    # SUB-PARSING HANDLERS
    # --------------------------------------------------------------------------
    def parse_block(self, terminators: Set[ChaoTokenType], block_name: str, start_token: ChaoToken) -> List[ASTNode]:
        """Utility to parse sequences of statements inside loops, branches, or modules with boundary verification."""
        statements = []
        while not self.match_any_no_consume(*terminators):
            curr = self.current_token()
            if curr.type == ChaoTokenType.EOF:
                raise ChaoSyntaxError(
                    f"Reached EOF with unclosed '{block_name}' block started at line {start_token.line_number}, col {start_token.column}",
                    curr.line_number, curr.column
                )
            # Prevent illegal/unaligned nested terminations
            if curr.type in {
                ChaoTokenType.END_PLANT, ChaoTokenType.END_STALK, ChaoTokenType.END_IF,
                ChaoTokenType.END_GROW, ChaoTokenType.END_WHILE, ChaoTokenType.END_INFINITE
            }:
                raise ChaoSyntaxError(
                    f"Mismatched termination boundary '{curr.value}' inside active '{block_name}' block starting at L:{start_token.line_number}:C:{start_token.column}",
                    curr.line_number, curr.column
                )
            statements.append(self.parse_statement())
        return statements

    def parse_plant_decl(self) -> ProgramNode:
        plant_tok = self.consume(ChaoTokenType.PLANT, "initiating plant boundary declaration")
        name_tok = self.consume(ChaoTokenType.IDENTIFIER, "naming the garden node")
        
        # Isolate variable scope inside the garden
        old_table = set(self.symbol_table)
        
        body = self.parse_block({ChaoTokenType.END_PLANT}, "PLANT", plant_tok)
        self.consume(ChaoTokenType.END_PLANT, "closing plant boundary")
        
        self.symbol_table = old_table
        return ProgramNode(statements=body)

    def parse_var_decl(self) -> VariableDeclNode:
        type_tok = self.consume_any(
            {ChaoTokenType.SEED, ChaoTokenType.SPROUT, ChaoTokenType.WATER, ChaoTokenType.SOIL, ChaoTokenType.BED, ChaoTokenType.DAEMON},
            "extracting type declaration identifier"
        )
        ident_tok = self.consume(ChaoTokenType.IDENTIFIER, "extracting variable name")
        self.consume(ChaoTokenType.ASSIGN, "binding assignment value to variable")
        expr = self.parse_expression()

        # Track variable in scope table
        self.symbol_table.add(ident_tok.value)
        return VariableDeclNode(var_type=type_tok.value, identifier=ident_tok.value, expression=expr)

    def parse_reassignment(self) -> AssignmentNode:
        self.consume(ChaoTokenType.SOIL, "matching soil reassignment identifier")
        ident_tok = self.consume(ChaoTokenType.IDENTIFIER, "identifying reassignment variable target")
        self.consume(ChaoTokenType.ASSIGN, "matching assignment bind operator")
        expr = self.parse_expression()
        return AssignmentNode(identifier=ident_tok.value, expression=expr)

    def parse_sprout_statement(self) -> SproutStatementNode:
        self.consume(ChaoTokenType.SPROUT, "matching sprout execution keyword")
        name_tok = self.consume(ChaoTokenType.IDENTIFIER, "extracting module identifier to sprout")
        return SproutStatementNode(name=name_tok.value)

    def parse_print_statement(self) -> PrintNode:
        self.consume(ChaoTokenType.WATER, "matching water printing keyword")
        expr = self.parse_expression()
        return PrintNode(expression=expr)

    def parse_function_decl(self) -> FunctionDeclNode:
        stalk_tok = self.consume(ChaoTokenType.STALK, "matching stalk function block declaration")
        name_tok = self.consume(ChaoTokenType.IDENTIFIER, "extracting function name identifier")
        
        self.consume(ChaoTokenType.LPAREN, "opening function parameter bindings")
        params = []
        if not self.match_token(ChaoTokenType.RPAREN):
            p = self.consume(ChaoTokenType.IDENTIFIER, "matching function parameter identifier")
            params.append(p.value)
            while self.match_token(ChaoTokenType.COMMA):
                next_p = self.consume(ChaoTokenType.IDENTIFIER, "matching parameter separator comma")
                params.append(next_p.value)
            self.consume(ChaoTokenType.RPAREN, "closing function parameters binding list")

        # Isolate variable scope inside function stalk
        old_table = set(self.symbol_table)
        for p in params:
            self.symbol_table.add(p)

        body = self.parse_block({ChaoTokenType.END_STALK}, "STALK", stalk_tok)
        self.consume(ChaoTokenType.END_STALK, "closing stalk function definition block")
        
        self.symbol_table = old_table
        return FunctionDeclNode(name=name_tok.value, params=params, body=body)

    def parse_return_statement(self) -> ReturnNode:
        self.consume(ChaoTokenType.RETURN, "matching return output marker")
        if self.is_expression_starter(self.current_token()):
            return ReturnNode(expression=self.parse_expression())
        return ReturnNode(expression=None)

    def parse_grow_statement(self) -> GrowStatementNode:
        self.consume(ChaoTokenType.GROW, "matching standalone grow keyword")
        return GrowStatementNode()

    def parse_if_statement(self) -> IfStatementNode:
        if_tok = self.consume(ChaoTokenType.IF, "opening IF logical evaluation branch")
        condition = self.parse_expression()
        
        then_branch = self.parse_block({ChaoTokenType.ELSE_IF, ChaoTokenType.ELSE, ChaoTokenType.END_IF}, "IF", if_tok)
        
        else_if_branches = []
        while self.match_token(ChaoTokenType.ELSE_IF):
            elif_tok = self.previous_token()
            elif_cond = self.parse_expression()
            elif_body = self.parse_block({ChaoTokenType.ELSE_IF, ChaoTokenType.ELSE, ChaoTokenType.END_IF}, "ELSE IF", elif_tok)
            else_if_branches.append((elif_cond, elif_body))

        else_branch = None
        if self.match_token(ChaoTokenType.ELSE):
            else_tok = self.previous_token()
            else_branch = self.parse_block({ChaoTokenType.END_IF}, "ELSE", else_tok)

        self.consume(ChaoTokenType.END_IF, "closing IF conditional block pathways")
        return IfStatementNode(condition=condition, then_branch=then_branch, else_if_branches=else_if_branches, else_branch=else_branch)

    def parse_while_loop(self) -> WhileLoopNode:
        while_tok = self.consume(ChaoTokenType.WHILE, "opening WHILE vine loop construct")
        condition = self.parse_expression()
        
        body = self.parse_block({ChaoTokenType.END_WHILE}, "WHILE", while_tok)
        self.consume(ChaoTokenType.END_WHILE, "closing while loops block")
        return WhileLoopNode(condition=condition, body=body)

    def parse_grow_loop(self) -> GrowLoopNode:
        grow_tok = self.consume(ChaoTokenType.GROW, "opening grow loop block")
        count_expr = self.parse_expression()
        self.consume(ChaoTokenType.TIMES, "matching grow iterations loop marker")
        
        body = self.parse_block({ChaoTokenType.END_GROW}, "GROW LOOP", grow_tok)
        self.consume(ChaoTokenType.END_GROW, "closing grow loop block")
        return GrowLoopNode(count_expr=count_expr, body=body)

    def parse_infinite_loop(self) -> InfiniteLoopNode:
        inf_tok = self.consume(ChaoTokenType.INFINITE, "opening infinite loop process")
        body = self.parse_block({ChaoTokenType.END_INFINITE}, "INFINITE", inf_tok)
        self.consume(ChaoTokenType.END_INFINITE, "closing infinite loop block")
        return InfiniteLoopNode(body=body)

    # --------------------------------------------------------------------------
    # EXPRESSION PRECEDENCE LAYER (THE PRECEDENCE CLIMBING)
    # --------------------------------------------------------------------------
    def parse_expression(self) -> ASTNode:
        return self.parse_comparison()

    def parse_comparison(self) -> ASTNode:
        expr = self.parse_additive()
        while self.match_any(ChaoTokenType.EQ, ChaoTokenType.NE, ChaoTokenType.LT, ChaoTokenType.LE, ChaoTokenType.GT, ChaoTokenType.GE):
            op = self.previous_token().value
            right = self.parse_additive()
            expr = BinOpNode(left=expr, op=op, right=right)
        return expr

    def parse_additive(self) -> ASTNode:
        expr = self.parse_multiplicative()
        while self.match_any(ChaoTokenType.PLUS, ChaoTokenType.MINUS):
            op = self.previous_token().value
            right = self.parse_multiplicative()
            expr = BinOpNode(left=expr, op=op, right=right)
        return expr

    def parse_multiplicative(self) -> ASTNode:
        expr = self.parse_unary()
        while self.match_any(ChaoTokenType.MULT, ChaoTokenType.DIV, ChaoTokenType.MOD):
            op = self.previous_token().value
            right = self.parse_unary()
            expr = BinOpNode(left=expr, op=op, right=right)
        return expr

    def parse_unary(self) -> ASTNode:
        if self.match_token(ChaoTokenType.GLITCH):
            return GlitchOpNode(expression=self.parse_unary())
        elif self.match_token(ChaoTokenType.MINUS):
            # Represent unary subtraction relative to seed literal 0
            return BinOpNode(left=LiteralNode(0), op="-", right=self.parse_unary())
        return self.parse_primary()

    def parse_primary(self) -> ASTNode:
        tok = self.current_token()

        if self.match_token(ChaoTokenType.INT_LIT):
            return LiteralNode(value=int(self.previous_token().value))

        elif self.match_token(ChaoTokenType.FLOAT_LIT):
            return LiteralNode(value=float(self.previous_token().value))

        elif self.match_token(ChaoTokenType.STRING_LIT):
            val = self.previous_token().value
            if len(val) >= 2 and val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            return LiteralNode(value=val)

        elif self.match_token(ChaoTokenType.TRUE):
            return LiteralNode(value=True)

        elif self.match_token(ChaoTokenType.FALSE):
            return LiteralNode(value=False)

        elif self.match_token(ChaoTokenType.NOTHING):
            return LiteralNode(value=None)

        elif self.match_token(ChaoTokenType.IDENTIFIER):
            name = self.previous_token().value
            # Check for function call invokes
            if self.match_token(ChaoTokenType.LPAREN):
                args = []
                if not self.match_token(ChaoTokenType.RPAREN):
                    args.append(self.parse_expression())
                    while self.match_token(ChaoTokenType.COMMA):
                        args.append(self.parse_expression())
                    self.consume(ChaoTokenType.RPAREN, "closing function args signature")
                return FunctionCallNode(name=name, args=args)
            return IdentifierNode(name=name)

        elif self.match_token(ChaoTokenType.LPAREN):
            expr = self.parse_expression()
            self.consume(ChaoTokenType.RPAREN, "closing parenthesis grouping")
            return expr

        elif self.match_token(ChaoTokenType.LBRACKET):
            # Collection bed array parser
            elements = []
            if not self.match_token(ChaoTokenType.RBRACKET):
                elements.append(self.parse_expression())
                while self.match_token(ChaoTokenType.COMMA):
                    elements.append(self.parse_expression())
                self.consume(ChaoTokenType.RBRACKET, "closing bed array bounds")
            return ArrayNode(elements=elements)

        else:
            raise ChaoSyntaxError(
                f"Unexpected syntax element '{tok.value}' matched inside expression tree parser",
                tok.line_number, tok.column
            )


# ==============================================================================
# VI. DIAGNOSTIC PRINTING VISUALIZER
# ==============================================================================

def print_chao_ast(node: ASTNode, indent: int = 0) -> None:
    """Recursively formats and prints the ChaoScript AST structures visually using ASCII characters."""
    prefix = "|   " * indent
    connector = "|-- " if indent > 0 else ""
    spacing = f"{prefix}{connector}"

    if isinstance(node, ProgramNode):
        print(f"{spacing}ProgramNode:")
        daemons = node.get_daemon_references()
        print(f"{prefix}+-- [ Spaghetti Daemon Active References: {len(daemons)} ]")
        for ref in daemons:
            print(f"{prefix}    [DAEMON] Tracked Daemon: {ref}")
        for stmt in node.statements:
            print_chao_ast(stmt, indent + 1)

    elif isinstance(node, VariableDeclNode):
        print(f"{spacing}VariableDeclNode (Type: {node.var_type}, Name: '{node.identifier}')")
        print_chao_ast(node.expression, indent + 1)

    elif isinstance(node, AssignmentNode):
        print(f"{spacing}AssignmentNode (Name: '{node.identifier}')")
        print_chao_ast(node.expression, indent + 1)

    elif isinstance(node, FunctionDeclNode):
        print(f"{spacing}FunctionDeclNode (Name: '{node.name}', Params: {node.params})")
        for stmt in node.body:
            print_chao_ast(stmt, indent + 1)

    elif isinstance(node, IfStatementNode):
        print(f"{spacing}IfStatementNode:")
        print(f"{prefix}    |-- Condition:")
        print_chao_ast(node.condition, indent + 2)
        print(f"{prefix}    |-- Then Branch:")
        for stmt in node.then_branch:
            print_chao_ast(stmt, indent + 2)
        for cond, branch in node.else_if_branches:
            print(f"{prefix}    |-- Else-If Condition:")
            print_chao_ast(cond, indent + 2)
            print(f"{prefix}    |-- Else-If Body:")
            for stmt in branch:
                print_chao_ast(stmt, indent + 2)
        if node.else_branch:
            print(f"{prefix}    +-- Else Body:")
            for stmt in node.else_branch:
                print_chao_ast(stmt, indent + 2)

    elif isinstance(node, WhileLoopNode):
        print(f"{spacing}WhileLoopNode:")
        print(f"{prefix}    |-- Condition:")
        print_chao_ast(node.condition, indent + 2)
        print(f"{prefix}    +-- Body:")
        for stmt in node.body:
            print_chao_ast(stmt, indent + 2)

    elif isinstance(node, GrowLoopNode):
        print(f"{spacing}GrowLoopNode:")
        print(f"{prefix}    |-- Loops count expression:")
        print_chao_ast(node.count_expr, indent + 2)
        print(f"{prefix}    +-- Body:")
        for stmt in node.body:
            print_chao_ast(stmt, indent + 2)

    elif isinstance(node, InfiniteLoopNode):
        print(f"{spacing}InfiniteLoopNode:")
        print(f"{prefix}    +-- Body:")
        for stmt in node.body:
            print_chao_ast(stmt, indent + 1)

    elif isinstance(node, PrintNode):
        print(f"{spacing}PrintNode (WATER):")
        print_chao_ast(node.expression, indent + 1)

    elif isinstance(node, GlitchOpNode):
        print(f"{spacing}GlitchOpNode (~~~ Mutation):")
        print_chao_ast(node.expression, indent + 1)

    elif isinstance(node, ReturnNode):
        print(f"{spacing}ReturnNode:")
        if node.expression:
            print_chao_ast(node.expression, indent + 1)
        else:
            print(f"{prefix}    +-- [ Empty Return ]")

    elif isinstance(node, GrowStatementNode):
        print(f"{spacing}GrowStatementNode (GROW)")

    elif isinstance(node, SproutStatementNode):
        print(f"{spacing}SproutStatementNode (SPROUT Garden: '{node.name}')")

    elif isinstance(node, BinOpNode):
        print(f"{spacing}BinOpNode (Operator: '{node.op}')")
        print_chao_ast(node.left, indent + 1)
        print_chao_ast(node.right, indent + 1)

    elif isinstance(node, LiteralNode):
        val_str = f'"{node.value}"' if isinstance(node.value, str) else str(node.value)
        print(f"{spacing}LiteralNode (Value: {val_str})")

    elif isinstance(node, IdentifierNode):
        print(f"{spacing}IdentifierNode (Name: '{node.name}')")

    elif isinstance(node, ArrayNode):
        print(f"{spacing}ArrayNode (BED):")
        for el in node.elements:
            print_chao_ast(el, indent + 1)

    elif isinstance(node, FunctionCallNode):
        print(f"{spacing}FunctionCallNode (Function: '{node.name}')")
        for arg in node.args:
            print_chao_ast(arg, indent + 1)


# ==============================================================================
# VII. DIAGNOSTIC EXECUTION RITUAL
# ==============================================================================

if __name__ == "__main__":
    print("==============================================================================")
    print("[GARDEN] CHAOSCRIPT COMPILER CORE DIAGNOSTIC RITUAL - PHASE 1")
    print("==============================================================================")

    # 1. Check virtual plant system hydration levels first
    try:
        hyd = check_system_hydration()
        print(f"[OK] Hydration telemetry verification: OK ({hyd}% moisture detected).")
    except ChaoPlantDehydrationError as e:
        print(f"[ERROR] COMPILATION BLOCKED BY DEHYDRATION SAFEGUARD:")
        print(e)
        exit(1)

    # 2. Compile target ChaoScript source showcasing all spec constraints
    mock_source = """// Welcome to the ChaoScript Garden
PLANT fizzbuzz_garden
    SEED limit = 15
    SEED i = 1
    
    // We declare a function stalk to check divisibility
    STALK is_divisible(n, div)
        SEED rem = n % div
        IF rem == 0
            RETURN TRUE
        ELSE
            RETURN FALSE
        END IF
    END STALK

    // Let's run a while vines loop
    WHILE i <= limit
        SOIL is_fizz = is_divisible(i, 3)
        SOIL is_buzz = is_divisible(i, 5)
        
        IF is_fizz == TRUE
            IF is_buzz == TRUE
                WATER "FizzBuzz"
            ELSE
                WATER "Fizz"
            END IF
        ELSE IF is_buzz == TRUE
            WATER "Buzz"
        ELSE
            // Output index value
            WATER i
        END IF
        
        // Advance iteration using soil keyword
        SOIL i = i + 1
        GROW // Standalone patience mechanic
    END WHILE

    // A collection bed declaration
    BED logs = ["completed", "nominal"]

    // A daemon declaration
    DAEMON ghost = NOTHING

    // A glitch operation mutation demo
    SEED original = 42
    SEED glitched_val = ~~~original

    // Comment bypass check: 0.1% chance of executing on standard run.
    // WATER "This statement bypassed deletion and executed!"
END PLANT

SPROUT fizzbuzz_garden
"""

    print("\n--- Raw Input ChaoScript Source Code ---")
    print(mock_source.strip())
    print("-----------------------------------------")

    print("\n[STEP 1] Running Lexical Analysis (ChaoLexer)...")
    lexer = ChaoLexer(mock_source)
    try:
        tokens = lexer.tokenize()
        print(f"Successfully generated {len(tokens)} tokens.")
        print("\nSequential Token Stream Array:")
        for idx, token in enumerate(tokens):
            print(f"  [{idx:03d}] {token}")
    except ChaoLexicalError as e:
        print(f"\n[ERROR] Lexical Error at line {e.line}, column {e.column}: {e}")
        exit(1)

    print("\n[STEP 2] Running Syntactic Analysis (ChaoParser)...")
    parser = ChaoParser(tokens)
    try:
        ast_root = parser.parse()
        print("Garden parsed successfully into Unified AST layout.")
        
        print("\nIndented Structural AST Output:")
        print_chao_ast(ast_root)
    except ChaoSyntaxError as e:
        print(f"\n[ERROR] Syntax Error at line {e.line}, column {e.column}: {e}")
        exit(1)

    # 3. Explicitly demonstrate Kevin's Comment-Bypass execution bug
    print("\n==============================================================================")
    print("[BUG] DEMONSTRATING KEVIN'S COMMENT-BYPASS EXE BUG (Chance forced to 100%)")
    print("==============================================================================")
    bug_source = """// Welcome to the Glitch Garden
PLANT glitch_garden
    SEED x = 100
    // WATER "[GARDEN] [BUG TEST] Comment bypass active! x = "
    // WATER x
END PLANT
SPROUT glitch_garden
"""
    print("Bug source code:")
    print(bug_source.strip())
    print("\nRunning Lexer with comment_bypass_chance = 1.0 (100% force)...")
    bug_lexer = ChaoLexer(bug_source, comment_bypass_chance=1.0)
    bug_tokens = bug_lexer.tokenize()
    
    print("Generated token stream with comment bypass active:")
    for token in bug_tokens:
        if token.type != ChaoTokenType.EOF:
            print(f"  {token}")
            
    print("\nParsing Glitch Garden AST...")
    bug_parser = ChaoParser(bug_tokens)
    bug_ast = bug_parser.parse()
    print_chao_ast(bug_ast)

    print("\n==============================================================================")
    print("[OK] DIAGNOSTICS COMPLETED SUCCESSFULLY")
    print("==============================================================================")
