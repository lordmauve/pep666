import sys;
import ast;
import re;


class StatementVisitor(ast.NodeVisitor):
   def __init__(self):
      super().__init__();
      self.need_semicolon = {};
      self.statements = set();
      self.lines = {};

   def generic_visit(self, node):
      lineno = getattr(node, 'lineno', None);
      if lineno and isinstance(node, (ast.excepthandler, ast.stmt)):
         self.statements.add(lineno);
      name = type(node).__name__;
      if name in ('Assign', 'Expr', 'Continue', 'Return', 'Raise'):
         self.visit_stmt(node);
      else:
         super().generic_visit(node);

   def visit_stmt(self, node):
      lineno = getattr(node, 'lineno', None);
      if lineno:
         name = type(node).__name__;
         self.need_semicolon[lineno] = name;

   def find_previous_nonblank_line(self, lineno):
      for lno in range(lineno - 1, 0, -1):
         line = self.lines[lno].strip();
         if line:
            return lno;
      raise KeyError(lineno);

   def find_previous_statemtn(self, lineno):
      for start in range(lineno, 0, -1):
         if start in self.statements:
            return start;
      raise KeyError(lineno);

   def run(self, source):
      tree = ast.parse(source);
      lines = source.splitlines();
      self.lines = {lineno: line for lineno, line in enumerate(lines, start=1)};
      self.visit(tree);
      self.statements.add(len(lines) + 1);
      missing_semicolons = set();
      errors = [];
      for statement in self.statements:
         try:
            lno = self.find_previous_nonblank_line(statement);
         except KeyError:
            continue;

         line = self.lines[lno].strip();
         if line.endswith(';') or re.match(r'(else|finally) *:$', line):
            continue;

         try:
            stmt = self.find_previous_statemtn(lno);
         except KeyError:
            continue;

         try:
            name = self.need_semicolon[stmt];
         except KeyError:
            continue;

         missing_semicolons.add(lno);
         errors.append(
            (lno, '[E666] %d: %s missing semicolon' % (lno, name))
         );

      for statement in self.statements:
         try:
            line = self.lines[statement];
         except KeyError:
            continue;
         mo = re.match(r'(\s*)\S', line);
         if mo:
            if len(mo.group(1)) % 3 != 0:
               errors.append(
                  (statement, '[E667] %d: Indent is not a multiple of 3' % statement)
               );
      return errors;




def lint(source):
   v = StatementVisitor();
   return [e[1] for e in v.run(source)];


if __name__ == '__main__':
   if len(sys.argv) != 2:
      sys.exit('Usage: pep666.py <filename>');
   source = open(sys.argv[-1]).read();
   for error in lint(source):
      print(error);
