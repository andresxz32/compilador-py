# Maquina virtual
from dataclasses import dataclass
from errors import execerror
from math import fmod
from model import *

DEBUG = False
STOP  = None

NSTACK = 256
stack  = []    # the stack (pop, push)

NPROG  = 2000
prog   = []    # the machine
pc     = 0     # program counter 

progbase  = len(prog)
returning = False       # True if return stmt seen
indef = False           # True if parsing a func or proc

# Tipos de Instrucciones en la pila/prog
@dataclass
class Datum:
    val: float  = 0.0
    sym: Symbol = None

# proc/func call stack frame
@dataclass
class Frame:
    sp    : Symbol = None   # symbol table entry
    retpc : int = 0         # where to resume after return
    argn  : Datum = 0       # n-th argument on stack
    nargs : int	= 0         # number of arguments

NFRAME = 100
frame  = Stack()

# initialize for code generation
def initcode():
    global stack, prog, frame, returning
    stack = []
    prog  = []
    frame = Stack()
    returning = False

# push d onto stack
def push(d : Datum):
    if len(stack) >= NSTACK:
        execerror('desbordamiento de la pila')
    stack.append(d)

# pop and return top elem from stack
def pop() -> Datum:
    if len(stack) == 0:
        execerror('desbordamiento de la pila')
    return stack.pop()

# for when no value is wanted
def xpop():
    if len(stack) == 0:
        execerror('desbordamiento de la pila')
    stack.pop()

# push constant onto stack
def constpush():
    global pc
    d = Datum(val=prog[pc].val); pc += 1
    push(d)

# push variable onto stack
def varpush():
    global pc
    d = Datum(sym=prog[pc]); pc += 1
    push(d)

def whilecode():
    global pc
    savepc = pc                 # loop body

    execute(savepc+2)           # condition
    d = pop()
    while d.val:
        execute(savepc)         # body
        if returning: break
        execute(savepc+2)
        d = pop()

    if not returning:
        pc = prog[savepc+1]     # next statement

def forcode():
    global pc
    savepc = pc

    execute(savepc+4)           # precharge
    pop()
    execute(savepc)             # condiction
    d = pop()
    while d.val:
        execute(savepc+2)       # body
        if returning: break
        execute(savepc+1)       # post loop
        pop()
        execute(savepc)         # condiction
        d = pop()

    if not returning:
        pc = prog[savepc+3]     # next statement

def ifcode():
    global pc
    savepc = pc                 # then part

    execute(savepc+3)           # condition
    d = pop()
    if d.val:
        execute(savepc)
    elif prog[savepc+1]:        # else part?
        execute(savepc+1)

    if not returning:
        pc = prog[savepc+2]     # next statement

# put func/proc in symbol table
def define(sp: Symbol):
    global progbase
    sp.defn  = progbase         # start of code
    progbase = len(prog)        # next code starts here

# call a function
def call():
    global returning
    sp = prog[pc]               # symbol table entry for function
    if len(frame) >= NFRAME:
        execerror(f"{sp.name} call nested too deeply")
    fp = Frame()
    fp.sp = sp
    fp.nargs = prog[pc+1]
    fp.retpc = pc + 2
    fp.argn  = len(stack) - 1   # last argument
    frame.push(fp)
    execute(sp.defn)
    returning = False

# common return from func/proc
def ret():
    global returning, pc
    fp = frame.pop()
    for _ in range(fp.nargs):
        pop()                   # pop arguments
    pc = fp.retpc
    returning = False

# return from a function
def funcret():
    fp = frame.peek()
    if fp.sp.type == 'PROCEDURE':
        execerror(f"{fp.sp.name} (proc) returns value")
    d = pop()                   # preserve function return value
    ret()
    push(d)

# return from a procedure
def procret():
    fp = frame.peek()
    if fp.sp.type == 'FUNCTION':
        execerror(f"{fp.sp.name} (func) returns no value")
    ret()

# return pointer to argument
def getarg() -> int:
    global pc
    fp = frame.peek()
    nargs = prog[pc]; pc += 1
    if nargs > fp.nargs:
        execerror(f"{fp.sp.name} no hay suficientes argumentos")
    return fp.argn + nargs - fp.nargs

# push argument onto stack
def arg():
    d = Datum()
    d.val = stack[getarg()].val
    push(d)

# store top of stack in argument
def argassign():
    d = pop()
    push(d)                     # leave value on stack
    stack[getarg()].val = d.val

# evaluate built-in on top of stack
def bltin():
    global pc
    d = pop()
    d.val = prog[pc].ptr(d.val); pc += 1
    push(d)

# evaluate variable on stack
def eval():
    d = pop()
    verify(d.sym)
    d.val = d.sym.val
    push(d)

# add top two elems on stack
def add():
    d2 = pop()
    d1 = pop()
    d1.val += d2.val
    push(d1)

# subtract top of stack from next
def sub():
    d2 = pop()
    d1 = pop()
    d1.val -= d2.val
    push(d1)

def mul():
    d2 = pop()
    d1 = pop()
    d1.val *= d2.val
    push(d1)

def div():
    d2 = pop()
    if d2.val == 0.0:
        execerror('division por cero')
    d1 = pop()
    d1.val /= d2.val
    push(d1)

def idiv():
    d2 = pop()
    if d2.val == 0.0:
        execerror('division por cero')
    d1 = pop()
    d1.val //= d2.val
    push(d1)

def mod():
    d2 = pop()
    if d2.val == 0.0:
        execerror('division por cero')
    d1 = pop()
    #d1.val %= d2.val
    d1.val = fmod(d1.val, d2.val)
    push(d1)

def negate():
    d = pop()
    d.val = -d.val
    push(d)

def verify(s : Symbol):
    if s.type != 'VAR' and s.type != 'UNDEF':
        execerror(f"intento de evaluar una no variable '{s.name}'")
    if s.type == 'UNDEF':
        execerror(f"variable no definida '{s.name}'")

def preinc():
    global pc
    d = Datum(sym=prog[pc]); pc += 1
    verify(d.sym)
    d.sym.val += 1.0
    d.val = d.sym.val
    push(d)

def predec():
    global pc
    d = Datum(sym=prog[pc]); pc += 1
    verify(d.sym)
    d.sym.val -= 1.0
    d.val = d.sym.val
    push(d)

def postinc():
    global pc
    d = Datum(sym=prog[pc]); pc += 1
    verify(d.sym)
    v = d.sym.val
    d.sym.val += 1.0
    d.val = v
    push(d)

def postdec():
    global pc
    d = Datum(sym=prog[pc]); pc += 1
    verify(d.sym)
    v = d.sym.val
    d.sym.val -= 1.0
    d.val = v
    push(d)

def gt():
    d2 = pop()
    d1 = pop()
    d1.val = float(d1.val > d2.val)
    push(d1)

def lt():
    d2 = pop()
    d1 = pop()
    d1.val = float(d1.val < d2.val)
    push(d1)

def ge():
    d2 = pop()
    d1 = pop();
    d1.val = float(d1.val >= d2.val)
    push(d1)

def le():
    d2 = pop()
    d1 = pop()
    d1.val = float(d1.val <= d2.val)
    push(d1)

def eq():
    d2 = pop()
    d1 = pop()
    d1.val = float(d1.val == d2.val)
    push(d1)

def ne():
    d2 = pop()
    d1 = pop()
    d1.val = float(d1.val != d2.val)
    push(d1)

def and_():
    d2 = pop()
    d1 = pop()
    d1.val = float(d1.val != 0.0 and d2.val != 0.0)
    push(d1)

def or_():
    d2 = pop()
    d1 = pop()
    d1.val = float(d1.val != 0.0 or d2.val != 0.0)
    push(d1)

def not_():
    d = pop();
    d.val = float(d.val == 0.0)
    push(d)

def power():
    d2 = pop()
    d1 = pop()
    d1.val = pow(d1.val, d2.val)
    push(d1)

# assign top value to next value
def assign():
    d1 = pop()
    d2 = pop()
    if d1.sym.type != 'VAR' and d1.sym.type != 'UNDEF':
        execerror(f'asignacion a no variable {d1.sym.name}')
    d1.sym.val  = d2.val
    d1.sym.type = 'VAR'
    push(d2)

def addeq():
    d1 = pop()
    d2 = pop()
    if d1.sym.type != 'VAR' and d1.sym.type != 'UNDEF':
        execerror(f'asignacion a no variable {d1.sym.name}')
    d1.sym.val += d2.val
    d2.val = d1.sym.val
    d1.sym.type = 'VAR'
    push(d2)

def subeq():
    d1 = pop()
    d2 = pop()
    if d1.sym.type != 'VAR' and d1.sym.type != 'UNDEF':
        execerror(f'asignacion a no variable {d1.sym.name}')
    d1.sym.val -= d2.val
    d2.val = d1.sym.val
    d1.sym.type = 'VAR'
    push(d2)

def muleq():
    d1 = pop()
    d2 = pop()
    if d1.sym.type != 'VAR' and d1.sym.type != 'UNDEF':
        execerror(f'asignacion a no variable {d1.sym.name}')
    d1.sym.val *= d2.val
    d2.val = d1.sym.val
    d1.sym.type = 'VAR'
    push(d2)

def diveq():
    d1 = pop()
    d2 = pop()
    if d1.sym.type != 'VAR' and d1.sym.type != 'UNDEF':
        execerror(f'asignacion a no variable {d1.sym.name}')
    d1.sym.val /= d2.val
    d2.val = d1.sym.val
    d1.sym.type = 'VAR'
    push(d2)

def modeq():
    d1 = pop()
    d2 = pop()
    if d1.sym.type != 'VAR' and d1.sym.type != 'UNDEF':
        execerror(f'asignacion a no variable {d1.sym.name}')
    d1.sym.val %= d2.val
    d2.val = d1.sym.val
    d1.sym.type = 'VAR'
    push(d2)

# pop top value from stack, print it
def printtop():
    global s # last value computed
    if not s in globals():
        s = install('_', 'VAR', 0.0)
    d = pop()
    print('\t%.12g' % d.val)
    s.val = d.val

# print numeric value
def prexpr():
    d = pop()
    print('%.12g ' % d.val, end='')

# print string value
def prstr():
    global pc
    s = prog[pc].replace('\\n', '\n'); pc += 1
    print(f"{s}", end='')

# read into variable
def varread():
    global pc
    d = Datum()
    var = prog[pc]; pc += 1
    try:
        var.val = float(input('$ '))
    except EOFError:
        d.val = var.val = 0.0
    except ValueError:
        execerror(f"no número leido en {var.name}")
    finally:
        d.val = 1.0
    var.type = 'VAR'
    push(d)

# run the machine
def execute(p: int=0):
    global pc
    pc = p
    while prog[pc] is not STOP:
        if isinstance(prog[pc], int): pc = prog[pc]
        instr = prog[pc]; pc += 1
        instr()

def pprint(line, instr):
    if instr is None:
        cmd = 'STOP'
    elif isinstance(instr, Symbol):
        if instr.type == 'NUMBER':
            cmd = f'{instr.val} -> NUMBER'
        elif instr.type == 'STRING':
            cmd = instr.str
        else:
            cmd = instr.name
    elif isinstance(instr, (int, str)):
        cmd = instr
    else:
        cmd = instr.__name__
    print(line, '\t', cmd)

# install one instruction or operand
def code(f):
    if len(prog) >= NPROG:
        execerror('programa muy grande')
    prog.append(f)
    return len(prog) - 1

def code2(c1, c2):
    ret = code(c1); code(c2)
    return ret

def code3(c1, c2, c3): 
    ret = code(c1); code(c2); code(c3)
    return ret

