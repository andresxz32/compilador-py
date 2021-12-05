# definición de Estructuras de datos
from collections import deque
from dataclasses import dataclass, field
from multimethod import multimeta
from typing import Any, List, Callable


# Entrada a la tabla de simbol
@dataclass
class Symbol:
	name: str
	type: str()             # VAR, BLTIN, UNDEF
	val : float = 0.0
	ptr : Callable = None
	defn: int = 0           # FUNCTION, PROCEDURE
	str : str = None        # STRING
	
	
#----------------------------------------
# Patron Visitor
class Visitor(metaclass=multimeta):
	pass
	
#----------------------------------------
# Estructura AST
@dataclass
class Node:
	def accept(self, visitor: Visitor, *args, **kwargs):
		return visitor.visit(self, *args, **kwargs)
		
@dataclass
class Statement(Node):
	pass
	
@dataclass
class Expression(Node):
	pass
	
@dataclass
class Program(Statement):
	stmts : List[Statement] = field(default_factory=list)
	
@dataclass
class Function(Statement):
	sym    : Symbol
	formal : List[Statement] = field(default_factory=list)
	body   : List[Statement] = field(default_factory=list)

@dataclass
class Procedure(Statement):
	sym    : Symbol
	formal : List[Statement] = field(default_factory=list)
	body   : List[Statement] = field(default_factory=list)

@dataclass
class Assignment(Statement):
	op   : str
	var  : Expression
	expr : Expression
	
@dataclass
class Print(Statement):
	exprs : List[Expression]
	
@dataclass
class While(Statement):
	cond : Expression
	body : List[Statement] = field(default_factory=list)
	
@dataclass
class If(Statement):
	cond  : Expression
	stmt  : List[Statement] = field(default_factory=list)
	stmt1 : List[Statement] = field(default_factory=list)
	
@dataclass
class Literal(Expression):
	sym : Symbol
	
@dataclass
class Variable(Expression):
	sym : Symbol
	
@dataclass
class String(Expression):
	sym : Symbol
	
@dataclass
class Binop(Expression):
	op   : str
	left : Expression
	right: Expression
	
@dataclass
class Unaryop(Expression):
	op   : str
	expr : Expression
	
@dataclass
class Bltin(Expression):
	sym  : Symbol
	expr : Expression
	
@dataclass
class Preinc(Expression):
	sym : Symbol
	
@dataclass
class Predec(Expression):
	sym : Symbol
	
@dataclass
class Postinc(Expression):
	sym : Symbol
	
@dataclass
class Postdec(Expression):
	sym : Symbol
	
#----------------------------------------
# Data Structures
class Stack(deque):
	push = deque.append
	
	def peek(self):
		return self[-1]
		
#----------------------------------------
# Tabla de Simbolos (Patron Iterator)
@dataclass
class LinkedListIterator:
	current : Symbol
	
	def __iter__(self):
		return self
		
	def __next__(self):
		if not self.current:
			raise StopIteration
		sym, self.current = self.current, self.current.next
		return sym
		
@dataclass
class LinkedList:
	sym : Symbol = None
	
	def __iter__(self):
		return LinkedListIterator(self.sym)
		
	def add(self, sym):
		sym.next = self.sym
		self.sym = sym

