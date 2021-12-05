from model import *
from vm import *

class CodeGenerator(Visitor):

    _assign_instr = {
        '='  : assign,
        '+=' : addeq,
        '-=' : subeq,
        '*=' : muleq,
        '/=' : diveq,
        '%/' : modeq,
    }
    _binop_instr = {
        '+'  : add,
        '-'  : sub,
        '*'  : mul,
        '/'  : div,
        '%'  : mod,
        '^'  : power,
        '<'  : lt,
        '<=' : le,
        '>'  : gt,
        '>=' : ge,
        '==' : eq,
        '!=' : ne,
        '&&' : and_,
        '||' : or_,
    }
    _unaryop_instr = {
        '-' : negate,
        '!' : not_,
    }

    @classmethod
    def generate(cls, model):
        generator = cls()
        model.accept(generator)

    def visit(self, node: Program):
        '''
        program : list
        code(STOP)
        '''
        for stmt in node.stmts:
            self.visit(stmt)
        code(STOP)
        
    def visit(self, node: Assignment):
        '''
        asg : VAR '=' expr
        code3(varpush, p.VAR, assign)
        return p.expr
        '''
        pc = self.visit(node.expr)
        code3(varpush, node.var.sym, self._assign_instr[node.op])
        code(pop)
        return pc
        
    def visit(self, node: Print):
        '''
        stmt : PRINT prlist
        code(printf)
        '''
        pc = 0
        for expr in node.exprs:
            if isinstance(expr, String):
                ret = code2(prstr, expr.sym.str)
            else:
                ret = self.visit(expr)
                code(prexpr)
            if pc == 0: pc = ret
        return pc

    def visit(self, node: While):
        pc = code3(whilecode, STOP, STOP)
        self.visit(node.cond)
        code(STOP)
        pstmt = 0
        for stmt in node.body:
            ret = self.visit(stmt)
            if pstmt == 0: pstmt = ret
        pend = code(STOP) + 1
        prog[pc+1] = pstmt
        prog[pc+2] = pend
        return pc

    def visit(self, node: If):
        pc = code(ifcode)
        code3(STOP, STOP, STOP)
        self.visit(node.cond)
        code(STOP)
        pthen = STOP
        for s in node.stmt:
            ret = self.visit(s)
            if pthen is STOP: pthen = ret
        code(STOP)
        pelse = STOP
        for s in node.stmt1:
            ret = self.visit(s)
            if pelse is STOP: pelse = ret
        pend = code(STOP) + 1
        prog[pc+1] = pthen
        prog[pc+2] = pelse
        prog[pc+3] = pend
        return pc

    def visit(self, node: Literal):
        '''
        expr : NUMBER
        code2(constpush, p.NUMBER)
        '''
        return code2(constpush, node.sym)

    def visit(self, node: Variable):
        print('var',node.sym)
        '''
        expr : VAR
        code3(varpush, p.VAR, eval)
        '''
        verify(node.sym)
        return code3(varpush, node.sym, eval)

    def visit(self, node: Bltin):
        '''
        expr : BLTIN '(' expr ')'
        code2(bltin, p.BLTIN)
        return p.expr
        '''
        pc = self.visit(node.expr)
        code2(bltin, node.sym)
        return pc

    def visit(self, node: Binop):
        '''
        expr : expr binop expr
        code(add)
        '''
        pc = self.visit(node.left)
        self.visit(node.right)
        code(self._binop_instr[node.op])
        return pc

    def visit(self, node: Unaryop):
        '''
        expr : unaryop expr
        code(add)
        '''
        pc = self.visit(node.expr)
        code(self._unaryop_instr[node.op])
        return pc

    def visit(self, node: Preinc):
        return code2(preinc, node.sym)

    def visit(self, node: Predec):
        return code2(predec, node.sym)

    def visit(self, node: Postinc):
        return code2(postinc, node.sym)

    def visit(self, node: Postdec):
        return code2(postdec, node.sym)

    def verify(s : Symbol):
        if s.type != 'VAR' and s.type != 'UNDEF':
            execerror(f"intento de evaluar una no variable '{s.name}'")
        if s.type == 'UNDEF':
            execerror(f"variable no definida '{s.name}'")
