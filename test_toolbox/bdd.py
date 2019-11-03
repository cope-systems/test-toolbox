from functools import partial

from test_toolbox.output import DefaultOutputFunctions, wrap_text_cleanly


class BDD(object):
    PASS = "pass"
    IGNORE = "ignore"
    WARNING = "warning"
    FAIL = "fail"
    UNKNOWN = "unknown"

    _bdd_names = {'given', 'when', 'then', 'also', 'and_', 'but'}

    class _Clause(object):
        def __init__(self, clause_name, parent, children=None, output_functions=DefaultOutputFunctions):
            self.clause_name = clause_name.replace("_", " ").capitalize().strip()
            self.parent = parent
            self.children = children or []
            self.text_description = ""
            self.warn_exceptions = []
            self.ignore_exceptions = []
            self.cleanup_func = lambda: True
            self.state = BDD.UNKNOWN
            self.state_data = None
            self.active = False
            self.output_functions = output_functions

        def __call__(self, text_description, warn_exceptions=None, ignore_exceptions=None, cleanup_func=lambda: True):
            self.text_description = text_description
            self.warn_exceptions = warn_exceptions or self.warn_exceptions
            self.ignore_exceptions = ignore_exceptions or self.ignore_exceptions
            self.cleanup_func = cleanup_func
            return self
            
        def decide_fate(self, exc_type, exc_val, exc_tb):
            can_continue = True
            if self.children:
                for i, child in enumerate(self.children):
                    if (i + 1) == len(self.children) and not child.active and child.state == BDD.UNKNOWN:
                        can_continue = child.decide_fate(exc_type, exc_val, exc_tb)
                    elif not child.active and child.state == BDD.UNKNOWN:
                        child.decide_fate(None, None, None)
            if not exc_type:
                self.state = BDD.PASS
                return True and can_continue
            elif exc_type in self.ignore_exceptions:
                self.state = BDD.IGNORE
                self.state_data = (exc_type, exc_val, exc_tb)
                return True and can_continue
            elif exc_type in self.warn_exceptions:
                self.state = BDD.WARNING
                self.state_data = (exc_type, exc_val, exc_tb)
                return True and can_continue
            else:
                self.state = BDD.FAIL
                self.state_data = (exc_type, exc_val, exc_tb)
                return False
            
        def generate_report(self, indent, current_ident_level, bullet, max_width=120):
            wrap_text = partial(wrap_text_cleanly, width=max_width)
            clause_indent =  indent*current_ident_level
            clause_str = "{0}{1} {2} {3}".format(clause_indent, bullet, self.clause_name, self.text_description)
            if self.state == BDD.PASS:
                self.output_functions.pass_(wrap_text(clause_str))
            elif self.state == BDD.IGNORE:
                strs = (clause_str, "(Ignored Exception: {0})".format(repr(self.state_data[1])))
                entry, exception_data = map(wrap_text, strs)
                formatted_str = "{0}\n\t\t{1}".format(entry, exception_data)
                self.output_functions.ignore(formatted_str)
            elif self.state == BDD.WARNING:
                strs = ("{0}  **WARNING**".format(clause_str), "(Exception: {0})".format(repr(self.state_data[1])))
                entry, exception_data = map(wrap_text, strs)
                formatted_str = "{0}\n\t\t{1}".format(entry, exception_data)
                self.output_functions.warn(formatted_str)
            elif self.state == BDD.FAIL:
                strs = ("{0} **FAIL**".format(clause_str), "(Exception: {0})".format(repr(self.state_data[1])))
                entry, exception_data = map(wrap_text, strs)
                formatted_str = "{0}\n\t\t{1}".format(entry, exception_data)
                self.output_functions.fail(formatted_str)
            elif self.state == BDD.UNKNOWN:
                self.output_functions.warn(wrap_text("{0} **UNKNOWN**".format(clause_str)))
            else:
                assert False, "Should never be here."
            for child_clause in self.children:
                child_clause.generate_report(indent, current_ident_level + 1, bullet, max_width=max_width)

        def __getattr__(self, name):
            if name in BDD._bdd_names and not self.active:
                raise AttributeError("Child BDD clauses may only be created if used with a with statement.")
            elif name in BDD._bdd_names:
                # Assume the last child must be done, and no exceptions will be thrown for that child.
                if self.children and not self.children[-1].active and self.children[-1].state == BDD.UNKNOWN:
                    self.children[-1].decide_fate(None, None, None)
                new_child = BDD._Clause(name, self, output_functions=self.output_functions)
                self.children.append(new_child)
                return new_child
            else:
                raise AttributeError("No such attribute {0}".format(name))

        def __enter__(self):
            self.active = True
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.cleanup_func()
            return self.decide_fate(exc_type, exc_val, exc_tb)

    def __init__(self, description=None, level_bullet="->", max_width=120,
                 indent_str="  ", output_functions=DefaultOutputFunctions):
        self.description = description
        self.level_bullet = level_bullet
        self.max_width = max_width
        self.indent_str = indent_str
        self.output_functions = output_functions
        self.clauses = []
        self.active = False

    @classmethod
    def scenario(cls, scenario_description, level_bullet="->", max_width=120,
                 indent_str="  ", output_functions=DefaultOutputFunctions):
        return cls(
            "Scenario: {0}".format(scenario_description),
            level_bullet=level_bullet,
            max_width=max_width,
            indent_str=indent_str,
            output_functions=output_functions
        )

    def __getattr__(self, name):
        if name in self._bdd_names and not self.active:
            raise AttributeError("Child BDD clauses may only be created if used with a with statement.")
        elif name in self._bdd_names:
            child = self._Clause(name, self, output_functions=self.output_functions)
            self.clauses.append(child)
            return child
        else:
            raise AttributeError("No such attribute {0}".format(name))
        
    def __enter__(self):
        self.active = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.clauses:
            for i, clause in enumerate(self.clauses):
                if (i + 1) == len(self.clauses) and not clause.active and clause.state == BDD.UNKNOWN:
                    clause.decide_fate(exc_type, exc_val, exc_tb)
                elif not clause.active and clause.state == BDD.UNKNOWN:
                    clause.decide_fate(None, None, None)
        self.generate_report()

    def generate_report(self):
        if self.description:
            self.output_functions.info(self.description)
        for clause in self.clauses:
            clause.generate_report(indent=self.indent_str, current_ident_level=0,
                                   bullet=self.level_bullet, max_width=self.max_width)
