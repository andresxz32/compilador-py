from dataclasses import fields
from graphviz import Digraph
from model import *

from rich.text import Text
from rich.tree import Tree


class DotRender(Visitor):

    _node_defaults = {
        'shape' : 'box',
        'color' : 'lightblue2',
        'style' : 'filled',
    }
    _edge_defaults = {
        'arrowhead' : 'none',
    }

    def __init__(self):
        self.dot = Digraph('AST')
        self.dot.attr('node', **self._node_defaults)
        self.dot.attr('edge', **self._edge_defaults)
        self.seq = 0

    def __repr__(self):
        return self.dot.source

    def __str__(self):
        return self.dot.source

    @classmethod
    def render(cls, model):
        dot = cls()
        model.accept(dot)
        return dot.dot

    def name(self):
        self.seq += 1
        return 'n%02d' % self.seq

    def visit(self, node: Program):
        name = self.name()
        self.dot.node(name, label='Program')
        for stmt in node.stmts:
            self.dot.edge(name, self.visit(stmt))
        return name
        
    def visit(self, node: Print):
        name = self.name()
        self.dot.node(name, label='Print')
        for expr in node.exprs:
            self.dot.edge(name, self.visit(expr))
        return name

    def visit(self, node: While):
        name = self.name()
        self.dot.node(name, label='While')
        self.dot.edge(name, self.visit(node.cond), label='cond')
        for stmt in node.body:
            self.dot.edge(name, self.visit(stmt))
        return name

    def visit(self, node: If):
        name = self.name()
        self.dot.node(name, label='If')
        self.dot.edge(name, self.visit(node.cond), label='cond')
        for s in node.stmt:
            self.dot.edge(name, self.visit(s))
        for s in node.stmt1:
            self.dot.edge(name, self.visit(s))
        return name
        
    def visit(self, node: Assignment):
        name = self.name()
        label = 'Assign' if node.op == '=' else node.op
        self.dot.node(name, label=label)
        self.dot.edge(name, self.visit(node.var))
        self.dot.edge(name, self.visit(node.expr))
        return name
        
    def visit(self, node: Literal):
        name = self.name()
        self.dot.node(name, label='%.8g' % node.sym.val)
        return name

    def visit(self, node: String):
        name = self.name()
        self.dot.node(name, label=node.sym.str)
        return name

    def visit(self, node: Variable):
        name = self.name()
        self.dot.node(name, label=node.sym.name)
        return name
        
    def visit(self, node: Bltin):
        name = self.name()
        self.dot.node(name, label=node.sym.name)
        self.dot.edge(name, self.visit(node.expr))
        return name
        
    def visit(self, node: Binop):
        name  = self.name()
        self.dot.node(name, label=node.op)
        self.dot.edge(name, self.visit(node.left))
        self.dot.edge(name, self.visit(node.right))
        return name
        
    def visit(self, node: Unaryop):
        name  = self.name()
        self.dot.node(name, label=node.op)
        self.dot.edge(name, self.visit(node.expr))
        return name
        
    def visit(self, node: Preinc):
        name  = self.name()
        self.dot.node(name, label='++'+node.sym.name)
        return name
        
    def visit(self, node: Predec):
        name  = self.name()
        self.dot.node(name, label='--'+node.sym.name)
        return name
        
    def visit(self, node: Postinc):
        name  = self.name()
        self.dot.node(name, label=node.sym.name+'++')
        return name
        
    def visit(self, node: Postdec):
        name  = self.name()
        self.dot.node(name, label=node.sym.name+'--')
        return name
        
'''
Aplana todo el árbol de sintaxis en una lista con el propósito
de depurar y probar. Esto devuelve una lista de tuplas de la
forma (profundidad, nodo) donde la profundidad es un número
entero que representa la profundidad del árbol de análisis y
el nodo es el nodo AST asociado.
'''
class Flattener(Visitor):

    def __init__(self):
        self.depth = 0
        self.nodes = []
        
    @classmethod
    def render(cls, model):
        d = cls()
        tree = Tree()
        model.accept(d)
        return d.nodes
        
    def visit(self, node: Program):
        self.nodes.append((self.depth, 'Program'))
        self.depth += 1
        for stmt in node.stmts:
            self.visit(stmt)
        self.depth -= 1
        
    def visit(self, node: Assignment):
        self.nodes.append((self.depth, 'Assign'))
        self.depth += 1
        self.visit(node.var)
        self.visit(node.expr)
        self.depth -= 1
        
    def visit(self, node: Print):
        self.nodes.append((self.depth, 'Print'))
        self.depth += 1
        for expr in node.prlist:
            self.visit(expr)
        self.depth -=1

