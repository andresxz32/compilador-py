from model import *
import math

keywords = {
	'proc':   'PROC',
	'func':   'FUNC',
	'return': 'RETURN',
	'if':     'IF',
	'else':   'ELSE',
	'while':  'WHILE',
	'for':    'FOR',
	'read':   'READ',
	'print':  'PRINT',
}

consts = {
	'PI':    3.14159265358979323846,
	'E':     2.71828182845904523536,
	'GAMMA': 0.57721566490153286060,  # Euler
	'DEG':  57.29577951308232087680,  # deg/radian
	'PHI':   1.61803398874989484820,  # golden ratio
}

builtins = {
	'sin':   math.sin,
	'cos':   math.cos,
	'atan':  math.atan,
	'asin':  math.asin,  # checks argument
	'acos':  math.acos,  # checks argument
	'sinh':  math.sinh,  # checks argument
	'cosh':  math.cosh,  # checks argument
	'tanh':  math.tanh,
	'log':   math.log,   # checks argument
	'log10': math.log10, # checks argument
	'exp':   math.exp,   # checks argument
	'sqrt':  math.sqrt,  # checks argument
	'int':   int,
	'abs':   math.fabs,
}

# Inicialización Tabla de Simbolos
symlist = LinkedList()

def lookup(s):
	for sp in symlist:
		if sp.name == s:
			return sp
	return None
	
def install(s,t,d=0.0):
	sp = Symbol(name=s,type=t,val=d)
	symlist.add(sp)
	return sp
	
def init():
	for name, kval in keywords.items():
		install(name, kval)
	for name, cval in consts.items():
		install(name, 'VAR', cval)
	for name, func in builtins.items():
		s = install(name, 'BLTIN')
		s.ptr = func

# inicialización tabla de simbolos
init()
