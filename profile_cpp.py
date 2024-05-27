import sys, re, shutil, unicodedata

# mimics how kernprof works in python but for C++

# LIMITATIONS
# // @profile must be on the line just above the function declaration
# function declarations must be one line only
# one line must equal one statement

# MUST:
# TODO: let C++ handle the whole parts of max_digits for Hits, Per Hit, Time and % Time (+ 1 + its precision or 0 i the case of Hits)
# example with max time at 152.87... then C++ will compute 3 to which we add 1 for the . and its precision
# example with max hits at 14 then C++ will compute 2 to which we add nothing because Hits is an integer

# ASAP:
# TODO: fix the bug around one_less_available_items.erase(one_less_available_items.begin() + i);

# GOOD TO HAVE:
# TODO: removing the limitations lol
# TODO: put / move the chrono include at the very top

# ----------------------------------------------------------------------
# parameters (those marked with an ### are not meant to be used directly)
nb_space_line_prefix = 10
nb_space_line_suffix = 30
tab_width = 4
preamble_spacing = 2
top_chrono_name = "top_chrono"

define_chrono_macro_name = "DEF_CHRONO" ###
start_chrono_macro_name = "START_CHRONO"
top_chrono_macro_name = "TOP_CHRONO"

report_function_macro_name = "REP_FUNC"
report_function_header_macro_name = "REP_FUNC_HEADER" ###
report_function_line_macro_name = "REP_FUNC_LINE" ###
report_empty_function_line_macro_name = "REPE_FUNC_LINE" ###

report_line_header_macro_name = "REP_LINE_HEADER" ###
report_line_macro_name = "REP_LINE"

start_time_string = "st"
total_elapsed_string = start_time_string + "et" # et for end_time, making "stet" (simple enough to write and pronounce lol)

per_hit_precision = 4
time_precision = 2
percentage_time_precision = 2

# see https://en.cppreference.com/w/cpp/io/manip/fixed
# "" for "default" or "automatic" (C++ adapts depending on the magnitude of the number)
line_count_format = "std::fixed"
hits_format = "std::fixed"
time_format = "std::fixed"
perhit_format = "std::fixed"
percentage_time_format = "std::fixed"
total_time_modifiers = "std::fixed"
call_count_modifiers = "std::fixed"

# string to put before functions to add profiling to
profile_pattern = re.compile(r"\/\/ @profile\s*\r?\n")
# lines to ignore
ignore_bracket_line_pattern = re.compile(r"^\s*[{}]+\s*$")
ignore_comment_line_pattern = re.compile(r"^\s*//(?:a|[^a])*$")
ignore_empty_return_line_pattern = re.compile(r"^\s*return;\s*$")
# line reports
report_line_pattern = re.compile(rf"\/\/ {report_line_macro_name}\((\d+)\)")
# function reports (any character is captured, the function name check will be performed after)
report_function_pattern = re.compile(rf"\/\/ {report_function_macro_name}\(((?:a|[^a])+?)\)")
# chrono include
# a = re.compile(r"#include <chrono>")

# parameters
# ----------------------------------------------------------------------

line_count_max_digits = 0
hits_max_digits = 0
perhit_max_digits = 0
time_max_digits = 0
percentage_time_max_digits = 0

max_line_number = 0
max_line_width = 0

line_number_to_line = []
function_name_to_function = {}
error_occured = False

def to_tabs(s):
	return s

	# messes up the right bit
	# try 1
	return s.replace(' ' * tab_width, '\t')
	# try 2
	lines = s.split('\n')
	converted_lines = []

	for line in lines:
		new_line = ""
		space_count = 0

		for char in line:
			if char == ' ':
				space_count += 1
				if space_count == tab_width:
					new_line += '\t'
					space_count = 0
			else:
				if space_count > 0:
					new_line += ' ' * space_count
					space_count = 0
				new_line += char

		if space_count > 0:
			new_line += ' ' * space_count

		converted_lines.append(new_line)

	return '\n'.join(converted_lines)

# https://stackoverflow.com/a/49332214
is_other_id_start = lambda c: bool(re.match(r'[\u1885-\u1886\u2118\u212E\u309B-\u309C]', c))
is_other_id_continue = lambda c: bool(re.match(r'[\u00B7\u0387\u1369-\u1371\u19DA]', c))
is_xid_start = lambda c: unicodedata.category(c) in {'Lu', 'Ll', 'Lt', 'Lm', 'Lo', 'Nl'} or is_other_id_start(c)
is_xid_continue = lambda c: is_xid_start(c) or unicodedata.category(c) in {'Mn', 'Mc', 'Nd', 'Pc'} or is_other_id_continue(c)
def is_valid_identifier(name: str) -> bool:
	name = unicodedata.normalize('NFKC', name)
	return all(is_xid_continue(char) for char in name[1:]) if is_xid_start(name[0]) or name[0] == '_' else False

class File:
	def __init__(self, content, functions):
		self.content = content
		self.functions = functions
		self.preamble = ""

	def set_line_stats(self):
		global line_count_max_digits
		line_count_label = "Line #"
		
		tmp = max(len(line_count_label), len(str(max_line_number)))
		if line_count_max_digits != 0 and line_count_max_digits == tmp: return
		line_count_max_digits = tmp

		line_count_spacing = 0
		line_count_modifiers = f"std::right << std::setw({line_count_max_digits}) << {line_count_format}"
		line_count_value = "line_number"

		hits_label = "Hits"
		hits_spacing = hits_max_digits - len(hits_label) + 1
		hits_modifiers = f"std::right << std::setw({hits_max_digits}) << {hits_format}"
		hits_value = f"{total_elapsed_string}##line_number##_hits"
		
		time_label = "Time"
		time_spacing = time_max_digits - len(time_label) + 1
		time_modifiers = f"std::right << std::setw({time_max_digits}) << {time_format} << std::setprecision({time_precision})"
		time_value = f"{total_elapsed_string}##line_number"

		per_hit_label = "Per Hit"
		per_hit_spacing = perhit_max_digits - len(per_hit_label) + 1
		per_hit_modifiers = f"std::right << std::setw({perhit_max_digits}) << {perhit_format} << std::setprecision({per_hit_precision})"
		per_hit_value = f"{total_elapsed_string}##line_number / (double)({total_elapsed_string}##line_number##_hits)"

		percentage_time_label = "% Time"
		percentage_time_spacing = percentage_time_max_digits - len(percentage_time_label) + 1
		percentage_time_modifiers = f"std::right << std::setw({percentage_time_max_digits}) << {percentage_time_format} << std::setprecision({percentage_time_precision})"
		percentage_time_value = f"{total_elapsed_string}##line_number * 100 / function_name##_total_time"

		self.line_stats = [
			(line_count_spacing, line_count_label, line_count_modifiers, line_count_value),
			(hits_spacing, hits_label, hits_modifiers, hits_value),
			(time_spacing, time_label, time_modifiers, time_value),
			(per_hit_spacing, per_hit_label, per_hit_modifiers, per_hit_value),
			(percentage_time_spacing, percentage_time_label, percentage_time_modifiers, percentage_time_value)
		]

	def set_profiling(self):
		self.set_line_stats()
		rep_header_top = "".join(f"{" " * spacing}{label}" for spacing, label, modifiers, value in self.line_stats[:-1])
		line_delimiter_bar_length = len(rep_header_top)

		rep_function_header_top = f"{rep_header_top}{" " * self.line_stats[-1][0]}{self.line_stats[-1][1]}"
		function_delimiter_bar_length = len(rep_function_header_top)
		
		rep_line_stats = " << ".join(f'{modifiers} << {value} << " "' for spacing, label, modifiers, value in self.line_stats[:-1])
		
		rep_function_stats = f'"Total Time: " << {total_time_modifiers} << function_name##_total_time << std::endl << "Call #: " << {call_count_modifiers} << function_name##_calls'
		rep_function_line_stats = f'{rep_line_stats} << {self.line_stats[-1][2]} << {self.line_stats[-1][3]} << " "'
		rep_empty_function_line_stats = f'{self.line_stats[0][2]} << {self.line_stats[0][3]} << "{" " * (function_delimiter_bar_length - line_count_max_digits)}" << " "'

		self.preamble = f"""
// THIS FILE IS AUTO GENERATED, EVERYTHING WRITTEN HERE WILL BE OVERWRITTEN

// # chat gpt

#include <iostream>
#include <locale>

struct custom_thousand_sep : std::numpunct<char> {{
    char sep;
    custom_thousand_sep(char s) : sep(s) {{}}
protected:
    virtual char do_thousands_sep() const override {{ return sep; }}
    virtual std::string do_grouping() const override {{ return "\\3"; }}
}};

struct thousand_separator {{
    char sep;
    thousand_separator(char s) : sep(s) {{}}
}};

std::ostream& operator<<(std::ostream& os, const thousand_separator& ts) {{
    os.imbue(std::locale(os.getloc(), new custom_thousand_sep(ts.sep)));
    return os;
}}

#include <chrono>

#define {define_chrono_macro_name}(line_number) std::chrono::time_point<std::chrono::high_resolution_clock> {start_time_string}##line_number; double {total_elapsed_string}##line_number = 0; long {total_elapsed_string}##line_number##_hits = 0; std::chrono::time_point<std::chrono::high_resolution_clock> {top_chrono_name}##line_number;
#define {start_chrono_macro_name}(line_number) {start_time_string}##line_number = std::chrono::high_resolution_clock::now();
#define {top_chrono_macro_name}(line_number) {top_chrono_name}##line_number = std::chrono::high_resolution_clock::now(); std::chrono::duration<double, std::milli> elapsed##line_number = {top_chrono_name}##line_number - {start_time_string}##line_number; {total_elapsed_string}##line_number += elapsed##line_number.count(); {total_elapsed_string}##line_number##_hits++; {start_time_string}##line_number = {top_chrono_name}##line_number;

#define {report_function_macro_name}(function_name, total_time) long function_name##_total_time = total_time; std::cout << std::endl << "Function name: " << #function_name << std::endl << {rep_function_stats} << std::endl;
#define {report_function_header_macro_name} std::cout << std::endl << "{rep_function_header_top}" << std::endl << "{"=" * function_delimiter_bar_length}" << std::endl;
#define {report_function_line_macro_name}(line_number, line_txt, function_name) std::cout << {rep_function_line_stats} << line_txt << std::endl;
#define {report_empty_function_line_macro_name}(line_number, line_txt) std::cout << {rep_empty_function_line_stats} << line_txt << std::endl;

#define {report_line_header_macro_name} std::cout << std::endl << "{rep_header_top}" << std::endl << "{"=" * line_delimiter_bar_length}" << std::endl;
#define {report_line_macro_name}(line_number, line_txt) std::cout << {rep_line_stats} << " " << line_txt << std::endl;
"""
		# done this way instead of considering it's the first function's line Hit count because it could be a loop
		# in which case it would corresponds to the number of loops, not function calls
		self.preamble += """
""".join(f"long {f.function_name}_calls = 0;" for f in self.functions) + """
"""
		# line_number_offset = self.preamble.count("\n") + len(self.functions) + preamble_spacing
		for f in self.functions:
			# f.update_line_numbers(line_number_offset)
			f.update_line_number_to_line()
			self.preamble += f"\n{" ".join(f"{define_chrono_macro_name}({line.line_number})" for line in f.lines if not line.ignore)}"
		self.preamble += "\n" * preamble_spacing
		for f in self.functions: f.set_profiling()

	def write_to(self, path):
		with open(path, "w", encoding="utf-8") as f:
			f.write(str(self))

	def try_replace_report_line(self, m):
		global error_occured
		line_number, line = int(m.group(1)), None
		try:
			line = line_number_to_line[line_number]
			if line == None: raise IndexError
			if line.ignore:
				print(f"line number {line_number} can not be profiled")
				error_occured = True
				return ""
		except IndexError:
			print(f"line number {line_number} is not profiled")
			error_occured = True
			return ""
		return f"{report_line_header_macro_name} {report_line_macro_name}({line_number}, \"{line.base_txt}\")"

	def __repr__(self, only_functions=False):
		global error_occured
		if only_functions: return '\n'.join(str(f) for f in sorted(self.functions, key=lambda f: f.start_index))
		
		r = self.preamble
		last_index = 0
		for f in sorted(self.functions, key=lambda f: f.start_index):
			r += f"{self.content[last_index:f.start_index]}{f}"
			last_index = f.end_index + 1
		# the \ufeff is obscure
		r = (r + self.content[last_index:]).replace(u"\ufeff", "")

		if len(line_number_to_line) == 0:
			# no line was added to line_number_to_line => self.set_profiling was not called
			return r

		# now replace commented macros
		r = report_line_pattern.sub(self.try_replace_report_line, r)
		if error_occured: exit(1)

		report_functions_matches = list(report_function_pattern.finditer(r))
		for m in report_functions_matches:
			name = m.group(1)
			if name in function_name_to_function:
				f = function_name_to_function[name]
				macro_replacement = f"{report_function_macro_name}({f.function_name}, {f.total_time}) {report_function_header_macro_name} {" ".join(f"{report_empty_function_line_macro_name}({line.line_number}, \"{line.base_txt}\")" if line.ignore else f"{report_function_line_macro_name}({line.line_number}, \"{line.base_txt}\", {f.function_name})" for line in f.lines)}"
				r = f"{r[:m.start()]}{macro_replacement}{r[m.end():]}"
			else:
				print(f"function name {name} does not exists / is not profiled")
				error_occured = True
		if error_occured: exit(1)

		return r

get_line_prefix = lambda given_line_number = None: f"{start_chrono_macro_name}({(max_line_number if given_line_number == None else given_line_number):>{len(str(max_line_number))}}){" " * nb_space_line_prefix}" 

class Function:
	def __init__(self, decl, lines, start_index, end_index, first_body_line_number, function_name):
		global function_name_to_function
		self.base_decl = decl
		self.decl = decl
		# self.first_body_line_number = first_body_line_number
		line_number = first_body_line_number
		for line in lines:
			line.set_line_number(line_number)
			line_number += 1
		self.lines = lines
		# in original file, correspond to the very next character after the profile_pattern match
		# and the last } index
		self.start_index, self.end_index = start_index, end_index
		self.closing = "\n}"
		self.function_name = function_name
		function_name_to_function[function_name] = self
		self.total_time = "+".join(f"{total_elapsed_string}{line.line_number}" for line in lines if not line.ignore)

	def set_profiling(self):
		self.decl = f"{" " * len(get_line_prefix())}{self.base_decl}\n{self.function_name}_calls++;\n"
		# max_line_width = max(len(f"{get_line_prefix(line.line_number)}{line.txt}") for line in self.lines)
		for line in self.lines:
			line.set_profiling()
		self.closing = f"\n{" " * len(get_line_prefix())}" + "}"

	# def update_line_numbers(self, line_number_offset):
	def update_line_number_to_line(self):
		global line_number_to_line
		for line in self.lines:
			# line.line_number += line_number_offset
			n = line.line_number
			# add line to line_number_to_line
			if n >= len(line_number_to_line):
				line_number_to_line.extend([None] * (n - len(line_number_to_line) + 1))
			line_number_to_line[n] = line

	def __repr__(self):
		return f"{to_tabs(self.decl)}{"\n".join(str(line) for line in self.lines)}{to_tabs(self.closing)}"

	def __len__(self):
		return len(self.__repr__())

class Line:
	def __init__(self, ignore, txt):
		self.ignore = ignore
		self.txt = txt.replace("\t", " " * tab_width)
		self.base_txt = self.txt
		self.line_number = 0

	def set_line_number(self, line_number):
		global max_line_number, max_line_width
		self.line_number = line_number
		if line_number > max_line_number:
			max_line_number = line_number
		n = len(f"{get_line_prefix(self.line_number)}{self.txt}")
		if n > max_line_width:
			max_line_width = n

	def set_profiling(self):
		self.txt = f"{" " * len(get_line_prefix())}{self.base_txt}" if self.ignore else f"{get_line_prefix(self.line_number)}{self.base_txt}{" " * (max_line_width - (len(f"{get_line_prefix(self.line_number)}{self.base_txt}")) + nb_space_line_suffix)}{top_chrono_macro_name}({self.line_number})"

	def __repr__(self):
		return to_tabs(self.txt)

	def __len__(self):
		return len(self.__repr__())

def function_body_to_lines(function_body):
	return [
		Line((
				ignore_bracket_line_pattern.match(line)
				or ignore_comment_line_pattern.match(line)
				or ignore_empty_return_line_pattern.match(line)
			) != None,
			line
		)
		for line in function_body.replace('\r\n', '\n').split('\n')[1:-1]
	]

def handle_file_path(original_file_path, working_file_path):
	shutil.copyfile(original_file_path, working_file_path)
	content = ""
	with open(working_file_path, 'r', encoding='utf-8') as file: content = file.read()
	matches = [match for match in profile_pattern.finditer(content)]
	if len(matches) == 0:
		print(f"no function to profile found in {original_file_path}")
		return
	print(f"found {len(matches)} function to profile in {original_file_path}")
	functions = []
	for match in matches:
		start_index, end_index = match.end(), 0
		function = None
		N, K, function_name = 0, 0, ""
		for i in range(start_index, len(content)):
			if content[i] == '{':
				if N == 0:
					K = i + 1
				N += 1
			elif content[i] == '}':
				N -= 1
				if N == 0:
					function = Function(content[start_index:K],
										function_body_to_lines(content[K:i]),
										start_index, i, content[:start_index].count('\n') + 2,
										function_name)
					break
			elif content[i] == '(' and N == 0:
				j = i - 1
				while content[j] != ' ': j -= 1
				function_name = content[j+1:i]
		
		if function == None:
			raise ValueError("Mismatched brackets")
		functions.append(function)
		# print(function.function_name)
	file = File(content, functions)
	file.set_profiling()
	file.write_to(working_file_path)

def main():
	if len(sys.argv) < 2:
		print("provide cpp files")
		return

	for file_path in sys.argv[1:]:
		handle_file_path(file_path, file_path.split('.')[0] + '_profiled.cpp')

if __name__ == "__main__":
	main()
