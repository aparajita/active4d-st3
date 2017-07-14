import os
import os.path
import re
import shutil
import sublime
import sublime_plugin

LANGUAGE_RE = re.compile(r'^.+/(?:HTML \(Active4D\)|Active4D Library)\.sublime-syntax')


def usingActive4DSyntax(view):
    return LANGUAGE_RE.match(view.settings().get("syntax")) is not None


# class NewCircuitCommand(sublime_plugin.TextCommand):
#     def is_enabled(self):
#         return usingActive4DSyntax(self.view)

#     def run(self, edit):
#         path = os.path.dirname(self.view.file_name())

#         if path:
#             self.view.window().show_input_panel('Circuit name:', '', self.make_circuit, None, None)

#     def make_circuit(self, circuitName):
#         if circuitName:
#             circuitPath = os.path.join(os.path.dirname(os.path.abspath(self.view.file_name())), circuitName)

#             if not os.path.exists(circuitPath):
#                 src = os.path.join(sublime.packages_path(), 'Active4D', 'Support', 'circuit')
#                 shutil.copytree(src, circuitPath)
#             else:
#                 sublime.message_dialog('A file or directory already exists at %s' % circuitPath)


class BuildQueryCommand(sublime_plugin.TextCommand):
    QUERY_RE = re.compile(r'^(\s*)(query(?: selection)?\s*)\(\[([^\]]+)\]', re.IGNORECASE)
    ASTERISK_RE = re.compile(r'(^.*);\s*\*\s*\)\s*(`.*|//.*|.*)$')
    ADD_ASTERISK_RE = re.compile(r'(^.*)(\s*\))(\s*(`.*|//.*|.*)$)')

    def is_enabled(self):
        return usingActive4DSyntax(self.view)

    def run(self, edit):
        line_region = self.view.line(self.view.sel()[0])
        line_start = line_region.a
        line = self.view.substr(line_region)

        # See if the current line is a query. If it is, process it.
        m = self.QUERY_RE.match(line)

        if m:
            ws = m.group(1)
            command = m.group(2)
            table = m.group(3)

            # See if ;* has been added to the end of the query. If not, add it.
            if not self.ASTERISK_RE.match(line):
                m = self.ADD_ASTERISK_RE.match(line)
                line = '%s; *%s%s\n' % (m.group(1), m.group(2), m.group(3))
            else:
                line = line + '\n'

            self.view.replace(edit, line_region, line)

            # Go to the beginning of the next line
            line_region = self.view.line(sublime.Region(line_start, line_start))
            self.view.sel().clear()
            self.view.sel().add(sublime.Region(line_region.b + 1, line_region.b + 1))

            self.view.run_command('insert_snippet', {'contents': '%s%s([${1:%s}]; ${2:conjunction}; [$1]${3:field})' % (ws, command, table)})


class OpenIncludeCommand(sublime_plugin.TextCommand):
    QUOTE_RE = re.compile(r'[\'"]')

    def is_enabled(self):
        return usingActive4DSyntax(self.view)

    def run(self, edit):
        sel_region = self.view.sel()[0]
        line_region = self.view.line(sel_region)
        line = self.view.substr(line_region)
        col = self.view.rowcol(sel_region.begin())[1]

        # Search backward until we find a quote or line start
        first = col - 1

        for first in range(first, -1, -1):
            if self.QUOTE_RE.match(line[first]):
                # The start should be one past the first nonvalid character
                first += 1
                break

        # Search forward until we find a quote or line start
        last = col

        for last in range(last, len(line)):
            if self.QUOTE_RE.match(line[last]):
                break

        if last - first == 0:
            return

        directory = os.path.dirname(os.path.abspath(self.view.file_name()))
        path = os.path.join(directory, line[first:last])

        if os.path.isfile(path):
            self.view.window().open_file(path)
