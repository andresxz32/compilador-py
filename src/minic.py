# Fase 1: Calculadora Avanzada
from errors import CompilerError
from init import *
from model import *
from vm import *
from irgenerator import CodeGenerator
from rich import print

import argparse
import logging
import sly
import sys
	
# ---------------------------------------------------------------------
# Analizador Léxico
# ---------------------------------------------------------------------
class Lexer(sly.Lexer):

	tokens = {
		# keywords
		IF, ELSE, WHILE, PRINT, RETURN,
		FUNC, PROC, READ, FOR,
		
		INC, DEC,
		
		# Operadores de Relación
		LT, LE, GT, GE, EQ, NE, OR, AND, NOT,
		
		# Operadores de Asignacion
		ADDEQ, SUBEQ, MULEQ, DIVEQ, MODEQ,
		
		VAR, NUMBER, BLTIN,
		ARG, STRING, FUNCTION, PROCEDURE,
	}
	literals = '+-*/%^=(){},;'
	
	# ignore: white-space, comments, newline
	ignore = ' \t\r'
	
	# Comentarios C-Style
	@_(r'/\*(.|\n)*?\*/')
	def ignore_comment(self, t):
		self.lineno += t.value.count('\n')
		
	# Comentarios C++-Style
	@_(r'//.*\n')
	def ignore_cppcomment(self, t):
		self.lineno += 1
		
	# Comentarios Python-Style
	@_(r'#.*\n')
	def ignore_pycomment(self, t):
		self.lineno += 1

	@_(r'\n')
	def ignore_newline(self, t):
		self.lineno += 1
		return t

	# definición de tokens
	
	LE  = r'<='
	LT  = r'<'
	GE  = r'>='
	GT  = r'>'
	EQ  = r'=='
	NE  = r'!='
	OR  = r'\|\|'
	AND = r'&&'
	NOT = r'!'
	
	INC = r'\+\+'
	DEC = r'--'
	
	ADDEQ = r'\+='
	SUBEQ = r'-='
	MULEQ = r'\*='
	DIVEQ = r'/='
	MODEQ = r'%='
	
	@_(r'\$\d+')
	def ARG(self, t):
		n = int(t.value[1:])
		if n == 0:
			execerror(f"extraño $...{n}")
		t.value = n
		return t
		
	@_(r'[a-zA-Z_]\w*')
	def VAR(self, t):
		s = lookup(t.value)
		if s is None:
			s = install(t.value, 'UNDEF')
		t.type = 'VAR' if s.type == 'UNDEF' else s.type
		t.value = s
		return t
		
	@_(r'(\d*\.\d+|\d+\.?)([eE][-+]?\d+)?')
	def NUMBER(self, t):
		t.value = install('', 'NUMBER', float(t.value))
		return t
		
	@_(r'\"([^\\\n]|(\\.))*?\"')
	def STRING(self, t):
		s = install('', 'STRING')
		s.str = t.value[1:-1]
		t.value = s
		return t

	def error(self, t):
		print(f"Línea {t.lineno}: Error léxico, '{t.value[0]}' es ilegal")
		self.index += 1

# ---------------------------------------------------------------------
# Analizador Sintático
# ---------------------------------------------------------------------
class Parser(sly.Parser):
	log = logging.getLogger()
	log.setLevel(logging.ERROR)
	debugfile = 'minic.txt'

	tokens = Lexer.tokens

	precedence = (
		('right', '=', ADDEQ, SUBEQ, MULEQ, DIVEQ, MODEQ),
		('left', OR),
		('left', AND),
		('left', EQ, NE),
		('left', GT, GE, LT, LE),
		('left', '+', '-'),
		('left', '*', '/', '%'),
		('right', UMINUS, NOT, INC, DEC),
		('right', '^'),
	)

	def __init__(self):
		self.indef = False
		
	# warn if illegal definition
	def defnonly(self, s):
		if not self.indef:
			execerror(f"{s} utilizado fuera de la definición")
			
	# Definición de la Gramática
	
	@_("list")
	def program(self, p):
		return Program(p.list)
		
	@_("error")
	def program(self, p):
		print("Error de sintaxis")
		self.errok()
		
	@_("empty")
	def list(self, p):
		return []
		
	@_("list defn")
	def list(self, p):
		return p.list + [ p.defn ]
		
	@_("list stmt")
	def list(self, p):
		return p.list + [ p.stmt ]

	@_("VAR '='   expr",
		"VAR ADDEQ expr",
		"VAR SUBEQ expr",
		"VAR MULEQ expr",
		"VAR DIVEQ expr",
		"VAR MODEQ expr")
	def asgn(self, p):
		return Assignment(p[1], Variable(p.VAR), p.expr)
		
	@_("RETURN")
	def stmt(self, p):
		pass
		
	@_("RETURN expr")
	def stmt(self, p):
		pass
		
	@_("PROCEDURE '(' arglist ')'")
	def stmt(self, p):
		pass
		
	@_("PRINT prlist")
	def stmt(self, p):
		return Print(p.prlist)
		
	@_("WHILE '(' expr ')' stmt")
	def stmt(self, p):
		return While(p.expr, p.stmt)
		
	@_("FOR '(' expr ';' expr ';' expr ')' stmt")
	def stmt(self, p):
		pass

	@_("IF '(' expr ')' stmt ELSE stmt")
	def stmt(self, p):
		return If(p.expr, p.stmt0, p.stmt1)
		
	@_("IF '(' expr ')' stmt")
	def stmt(self, p):
		return If(p.expr, p.stmt)
		
	@_("asgn")
	def stmt(self, p):
		return p.asgn
		
	@_("expr")
	def stmt(self, p):
		return p.expr
		
	@_("'{' stmtlist '}'")
	def stmt(self, p):
		return p.stmtlist
		
	@_("empty")
	def stmtlist(self, p):
		return []
		
	@_("stmtlist stmt")
	def stmtlist(self, p):
		return p.stmtlist + [p.stmt]
		
	@_("NUMBER")
	def expr(self, p):
		return Literal(p.NUMBER)
		
	@_("VAR")
	def expr(self, p):
		return Variable(p.VAR)
		
	@_("FUNCTION '(' arglist ')'")
	def expr(self, p):
		pass
		
	@_("READ '(' VAR ')'")
	def expr(self, p):
		pass
		
	@_("BLTIN '(' expr ')'")
	def expr(self, p):
		return Bltin(p.BLTIN, p.expr)
		
	@_("'(' expr ')'")
	def expr(self, p):
		return p.expr
		
	@_("expr '+' expr",
		 "expr '-' expr",
		 "expr '*' expr",
		 "expr '/' expr",
		 "expr '%' expr",
		 "expr '^' expr")
	def expr(self, p):
		return Binop(p[1], p.expr0, p.expr1)
		
	@_("expr LT expr",
		 "expr LE expr",
		 "expr GT expr",
		 "expr GE expr",
		 "expr EQ expr",
		 "expr NE expr")
	def expr(self, p):
		return Binop(p[1], p.expr0, p.expr1)
		
	@_("expr AND expr",
		 "expr OR expr")
	def expr(self, p):
		return Binop(p[1], p.expr0, p.expr1)
		
	@_("'-' expr %prec UMINUS", "NOT expr")
	def expr(self, p):
		return Unaryop(p[0], p.expr)
		
	@_("INC VAR")
	def expr(self, p):
		return Preinc(p.VAR)
		
	@_("DEC VAR")
	def expr(self, p):
		return Predec(p.VAR)
		
	@_("VAR INC")
	def expr(self, p):
		return Postinc(p.VAR)
		
	@_("VAR DEC")
	def expr(self, p):
		return Postdec(p.VAR)
		
	@_("expr")
	def prlist(self, p):
		return [ p.expr ]
		
	@_("STRING")
	def prlist(self, p):
		return [ String(p.STRING) ]
		
	@_("prlist ',' expr")
	def prlist(self, p):
		return p.prlist + [ p.expr ]
		
	@_("prlist ',' STRING")
	def prlist(self, p):
		return p.prlist + [ String(p.STRING) ]

	@_("func_header '(' ')' stmt")
	def defn(self, p):
		code(procret)
		define(p.func_header)
		self.indef = False

	@_("FUNC procname")
	def func_header(self, p):
		p.procname.type = 'FUNCTION'
		self.indef = True
		return p.procname

	@_("PROC procname")
	def func_header(self, p):
		p.procname.type = 'PROCEDURE'
		self.indef = True
		return p.procname

	'''
	@_("empty")
	def formals(self, p):
		pass

	@_("VAR")
	def formals(self, p):
		pass

	@_("VAR ',' formals")
	def formals(self, p):
		pass
	'''

	@_("VAR", "FUNCTION", "PROCEDURE")
	def procname(self, p):
		return p[0]

	@_("empty")
	def arglist(self, p):
		return []

	@_("expr")
	def arglist(self, p):
		return [ p.expr ]

	@_("arglist ',' expr")
	def arglist(self, p):
		return p.arglist + [ p.expr ]

	@_("")
	def empty(self, p):
		pass

	def error(self, p):
		logging.error("en linea {lineno}: simbol desconocido '{value}'".format(
			lineno=p.lineno,
			value=p.value
		))
		raise CompilerError()
# ---------------------------------------------------------------------
# main
# ---------------------------------------------------------------------
def print_tokens(tokens):
	for tok in tokens:
		if isinstance(tok.value, Symbol):
			if tok.type == 'NUMBER':
				tok.value = tok.value.val
			elif tok.type == 'STRING':
				tok.value = tok.value.str
			else:
				tok.value = tok.value.name
		print(tok)
		
def print_ast(top):
	from renderer import DotRender
	from PIL import Image
	dot = DotRender.render(top)
	
	try:
		dot.format = 'png'
		dot.render()
		im = Image.open('AST.gv.png')
		im.show()
		
	except PermissionError:
		print(top)
		
def parse_args():
	parser = argparse.ArgumentParser(description="MiniC compiler")
	parser.add_argument('input')
	parser.add_argument('--output', "-o",
		help="specify output filename (default a.out)",
		default="a.out")
	parser.add_argument('--tokens', '-t',
		help='print tokens',
		dest='tokens', action='store_true')
	parser.add_argument('--ast',
		help='generate ast',
		dest='ast', action='store_true')
	return parser.parse_args()
	
def run_compiler(args):
	lexer = Lexer()
	parser = Parser()
	#analyzer = StaticAnalyzer()
	#flow_generator = FlowGraph()
	source_code = ''
	
	try:
		with open(args.input, 'r') as f:
			source_code = f.read()
	except FileNotFoundError:
		logging.error("File not found")
		exit(1)
		
	try:
		# group tokens into syntactical units using parser
		tokens = lexer.tokenize(source_code)
		if args.tokens:
			print_tokens(tokens)

			exit(0)
			
		top = parser.parse(tokens)
		print(top)
		if args.ast:
			print_ast(top)
			exit(0)
		
		# generate code
		CodeGenerator.generate(top)
		
		for line, instr in enumerate(prog):
			pprint(line, instr)
		execute()
		
		# perform semantic analyze
		#symtab, ast = analyzer.analyze(parse_tree)
		# generate flow graph
		#flow_graph = flow_generator.generate(ast)
		# generate code
		#code = code_generator.generate(flow_graph, symtab)
		
		'''
		original_stdout = sys.stdout
		with open(output_name, 'w') as f:
		sys.stdout = f
		for line, instr in enumerate(prog):
		pprint(line, instr)
		
		sys.stdout = original_stdout
		'''
	except CompilerError as e:
		if str(e):
			logging.error("COMPILER_ERROR: {0}".format(str(e)))
		exit(1)
		
def main():
	args = parse_args()
	run_compiler(args)
	
if __name__ == '__main__':
	main()

