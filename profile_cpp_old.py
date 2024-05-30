import sys, re, shutil, unicodedata
from typing import List

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

line_count_label = "Line"
hits_label = "Hits"
time_label = "Time"
per_hit_label = "Per Hit"
time_percentage_label = "% Time"

line_count_spacing = 0
hits_spacing = 1
time_spacing = 1
per_hit_spacing = 1
time_percentage_spacing = 1

per_hit_precision = 4
time_precision = 2
time_percentage_precision = 2

# see https://en.cppreference.com/w/cpp/io/manip/fixed
# "" for "default" or "automatic" (C++ adapts depending on the magnitude of the number)
line_count_format = "std::fixed"
hits_format = "std::fixed"
time_format = "std::fixed"
perhit_format = "std::fixed"
percentage_time_format = "std::fixed"
total_time_modifiers = "std::fixed"
call_count_modifiers = "std::fixed"

# string to put before functions / lines to add profiling to
profile_function_pattern = re.compile(r"\/\/ @profile\s+function\s*\r?\n")
profile_line_pattern = re.compile(r"\/\/ @profile\s+line\s*\r?\n")
# lines to ignore
ignore_patterns = [
	re.compile(r"^\s*[{}]+\s*$") # ignore only brackets
	re.compile(r"^\s*//(?:a|[^a])*$") # ignore single line comments
	re.compile(r"^\s*return;\s*$") # ignore empty returns
]
# line reports
report_line_pattern = re.compile(rf"\/\/ {report_line_macro_name}\((\d+)\)")
# function reports (any character is captured, the function name check will be performed after)
report_function_pattern = re.compile(rf"\/\/ {report_function_macro_name}\(((?:a|[^a])+?)\)")
# chrono include
# a = re.compile(r"#include <chrono>")

# parameters
# ----------------------------------------------------------------------

min_line_number = None
max_line_number = None

line_number_to_line = []
function_name_to_function = {}
error_occured = False

# https://stackoverflow.com/a/49332214
is_other_id_start = lambda c: bool(re.match(r'[\u1885-\u1886\u2118\u212E\u309B-\u309C]', c))
is_other_id_continue = lambda c: bool(re.match(r'[\u00B7\u0387\u1369-\u1371\u19DA]', c))
is_xid_start = lambda c: unicodedata.category(c) in {'Lu', 'Ll', 'Lt', 'Lm', 'Lo', 'Nl'} or is_other_id_start(c)
is_xid_continue = lambda c: is_xid_start(c) or unicodedata.category(c) in {'Mn', 'Mc', 'Nd', 'Pc'} or is_other_id_continue(c)
def is_valid_identifier(name: str) -> bool:
	name = unicodedata.normalize('NFKC', name)
	return all(is_xid_continue(char) for char in name[1:]) if is_xid_start(name[0]) or name[0] == '_' else False

hits_var_name = lambda line_count: f"{total_elapsed_string}{line_count}_hits"
time_var_name = lambda line_count: f"{total_elapsed_string}{line_count}"
per_hit_var_name = lambda line_count: f"{total_elapsed_string}{line_count}_per_hit"

class File:
	def __init__(self, content, functions, lines):
		# functions and lines are already sorted by line_number
		self.content = content
		self.functions = functions
		self.lines = functions
		self.preamble = ""

	def set_line_stats(self):
		line_count_modifiers = f"std::right << std::setw(function_name##_line_count_max_digits) << {line_count_format}"
		line_count_value = "line_number"

		hits_modifiers = f"std::right << std::setw(function_name##_hits_max_digits) << {hits_format}"
		hits_value = f"{total_elapsed_string}##line_number##_hits"
		
		time_modifiers = f"std::right << std::setw(function_name##_time_max_digits) << {time_format} << std::setprecision({time_precision})"
		time_value = f"{total_elapsed_string}##line_number"

		per_hit_modifiers = f"std::right << std::setw(function_name##_perhit_max_digits) << {perhit_format} << std::setprecision({per_hit_precision})"
		per_hit_value = f"{total_elapsed_string}##line_number / (double)({total_elapsed_string}##line_number##_hits)"

		percentage_time_spacing = time_percentage_max_digits - len(time_percentage_label) + 1
		percentage_time_modifiers = f"std::right << std::setw(function_name##_time_percentage_max_digits) << {percentage_time_format} << std::setprecision({time_percentage_precision})"
		time_percentage_value = f"{total_elapsed_string}##line_number * 100 / function_name##_total_time"

		self.line_stats = [
			(line_count_spacing, line_count_label, line_count_modifiers, line_count_value),
			(hits_spacing, hits_label, hits_modifiers, hits_value),
			(time_spacing, time_label, time_modifiers, time_value),
			(per_hit_spacing, per_hit_label, per_hit_modifiers, per_hit_value),
			(percentage_time_spacing, time_percentage_label, percentage_time_modifiers, time_percentage_value)
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

		self.preamble += f"""
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

template<typename... Args>
auto variadic_max(Args... args) {{
    return (std::max)({{args...}});
}}

struct lineStats {{
	long line_number;
	long hits;
	double time;
	double per_hit;
}}

struct functionLineStats : public lineStats {{
	double time_percentage;
}}

class Line {{
	
}}

long min_line_number = {min_line_number};
long max_line_number = {max_line_number};
std::vector<lineStats> lines_info(max_line_number - min_line_number + 1);

int line_count_label_length = std::string("{line_count_label}").length();
int hits_label_length = std::string("{hits_label}").length();
int time_label_length = std::string("{time_label}").length();
int per_hit_label_length = std::string("{per_hit_label}").length();
int time_percentage_label_length = std::string("{time_percentage_label}").length();

std::string line_count_str;
std::string hits_str;
std::string time_str;
std::string per_hit_str;
std::string time_percentage_str;

int line_value_width = 0;
int hits_value_width = 0;
int time_value_width = 0;
int per_hit_value_width = 0;
int time_percentage_value_width = 0;

int line_count_label_width = 0;
int hits_label_width = 0;
int time_label_width = 0;
int per_hit_label_width = 0;
int time_percentage_label_width = 0;

void update_line_labels_info(long line_count, long hits, double time, doube per_hit) {{
	line_count_str = std::to_string(line_count);
	hits_str = std::to_string(hits);
	time_str = std::to_string(round(time, {time_precision}));
	per_hit_str = std::to_string(round(per_hit, {per_hit_precision}));

	line_value_width = line_count_str.length();
	hits_value_width = hits_str.length();
	time_value_width = time_str.length();
	per_hit_value_width = per_hit_str.length();

	line_count_label_width = std::max(line_count_label_length, line_value_width);
	hits_label_width = std::max(hits_label_length, hits_value_width);
	time_label_width = std::max(time_label_length, time_value_width);
	per_hit_label_width = std::max(per_hit_label_length, per_hit_value_width);
}}

void update_function_line_labels_info(long line_count, long hits, double time, doube per_hit, double time_percentage) {{
	update_line_labels_info(line_count, hits, time, per_hit);
	time_percentage_str = std::to_string(round(time_percentage, {time_percentage_precision}));
	time_percentage_value_width = time_percentage_str.length();
	time_percentage_label_width = std::max(time_percentage_label_length, time_percentage_value_width);
}}

std::string line_header_labels_string() {{
	return std::string({line_count_spacing} + line_count_label_width - line_count_label_length, ' ') + "{line_count_label}" +
		   std::string({hits_spacing} + hits_label_width - hits_label_length, ' ') + "{hits_label}" +
		   std::string({time_spacing} + time_label_width - time_label_length, ' ') + "{time_label}" +
		   std::string({per_hit_spacing} + per_hit_label_width - per_hit_label_length, ' ') + "{per_hit_label}";
}}

std::string function_header_labels_string() {{
	return line_header_labels_string() +
		std::string({time_percentage_spacing} + time_percentage_label_width - time_percentage_label_length, ' ') + "{time_percentage_label}";
}}

std::string line_header_separator_string() {{
	int line_header_length = {line_count_spacing} + line_count_label_width +
							 {hits_spacing} + hits_label_width +
							 {time_spacing} + time_label_width +
							 {per_hit_spacing} + per_hit_label_width;
	return std::string(line_header_length, '=');
}}

std::string function_header_separator_string() {{
	return line_header_separator_string() + std::string({time_percentage_spacing} + time_percentage_label_width, '=');
}}

void report_line(long line_count, long hits, double time, double per_hit, std::string txt) {{
	update_line_labels_info(line_count, hits, time, per_hit);
	std::cout << line_header_labels_string() << "\\n" << line_header_separator_string() << " " << txt;
}}

void report_function(std::string function_name, long total_time, long call_count) {{
	std::cout << 
}}

void report_function_line(long line_count, long hits, double time, double per_hit, double time_percentage, std::string txt) {{
	
	std::cout << line_header_labels_string() << "\\n" << line_header_separator_string() << " " << txt;
}}

#include <chrono>

#define {define_chrono_macro_name}(line_number) std::chrono::time_point<std::chrono::high_resolution_clock> {start_time_string}##line_number; double {total_elapsed_string}##line_number = 0; long {total_elapsed_string}##line_number##_hits = 0; std::chrono::time_point<std::chrono::high_resolution_clock> {top_chrono_name}##line_number;
#define {start_chrono_macro_name}(line_number) {start_time_string}##line_number = std::chrono::high_resolution_clock::now();
#define {top_chrono_macro_name}(line_number) {top_chrono_name}##line_number = std::chrono::high_resolution_clock::now(); std::chrono::duration<double, std::milli> elapsed##line_number = {top_chrono_name}##line_number - {start_time_string}##line_number; {total_elapsed_string}##line_number += elapsed##line_number.count(); {total_elapsed_string}##line_number##_hits++; {start_time_string}##line_number = {top_chrono_name}##line_number;

#define {report_function_macro_name}(function_name, total_time) \\\\
	long function_name##_total_time = total_time; \\\\
	long function_name##_line_count_max_digits = 0; \\\\
	long function_name##_hits_max_digits = 0; \\\\
	long function_name##_perhit_max_digits = 0; \\\\
	long function_name##_time_max_digits = 0; \\\\
	long function_name##_time_percentage_max_digits = 0; \\\\
	std::cout << std::endl << "Function name: " << #function_name << std::endl << {rep_function_stats} << std::endl;
#define {report_function_header_macro_name}(function_name) std::cout << std::endl << "{rep_function_header_top}" << std::endl << std::string(function_name##_function_delimiter_bar_length, '=') << std::endl;
#define {report_function_line_macro_name}(line_number, line_txt, function_name) std::cout << {rep_function_line_stats} << line_txt << std::endl;
#define {report_empty_function_line_macro_name}(line_number, line_txt) std::cout << {rep_empty_function_line_stats} << line_txt << std::endl;

#define {report_line_header_macro_name} std::cout << std::endl << "{rep_header_top}" << std::endl << std::string(function_name##_line_delimiter_bar_length, '=') << std::endl;
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
		# individual line report
		n = line.line_number
		return f"update_line_labels_info({n}, {hits_var_name(n)}, {time_var_name(n)}, {per_hit_var_name(n)}); report_line()"
		return f"{report_line_header_macro_name}() {report_line_macro_name}({line_number}, \"{line.base_txt}\")"

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

class Function:
	def __init__(self, opening, lines: List[FunctionLine], longest_line_index, start_index, end_index, first_body_line_number, function_name):
		global function_name_to_function
		self.opening = opening
		self.base_opening = opening
		self.closing = "}"
		self.base_closing = self.closing
		
		self.first_body_line_number = first_body_line_number
		self.last_body_line_number = first_body_line_number + max(0, len(lines) - 1)
		self.max_line_number_length = len(str(self.last_body_line_number))
		self.max_line_length = len(self.lines[longest_line_index])

		# set line numbers and prefix / suffix in the generated code to its lines
		self.ignore_line_prefix = " " * (len(start_chrono_macro_name) + 1 + self.max_line_number_length + 1 + nb_space_line_prefix)
		self.ignore_line_suffix = ""
		line_number = first_body_line_number
		for line in lines:
			line.line_number = line_number
			aligned_line_number = f"{line_number:>{self.max_line_number_length}}"
			line_prefix = f"{start_chrono_macro_name}({aligned_line_number}){" " * nb_space_line_prefix}"
			line.prefix = self.ignore_line_prefix if line.ignore else line_prefix
			line_suffix = f"{" " * (self.max_line_length - len(line.base_txt) + nb_space_line_suffix)}{top_chrono_macro_name}({aligned_line_number})"
			line.suffix = self.ignore_line_suffix if line.ignore else line_suffix
			line_number += 1

		self.lines = lines
		# in original file, correspond to the very next character after the profile_function_pattern match
		# and the last } index
		self.start_index, self.end_index = start_index, end_index
		self.function_name = function_name

		function_name_to_function[function_name] = self
		self.total_time = "+".join(f"{total_elapsed_string}{line.line_number}" for line in lines if not line.ignore)
		self.line_count_max_digits = f"std::string(variadic_max({", ".join(line.line_number for line in lines)})).length()"
		self.hits_max_digits = f"std::string(variadic_max({", ".join(hits_var_name(line.line_number) for line in lines if not line.ignore)})).length()"
		self.perhit_max_digits = f"std::string(variadic_max({", ".join(f"std::round({per_hit_var_name(line.line_number)}, {per_hit_precision})" for line in lines if not line.ignore)})).length()"
		self.time_max_digits = f"std::string(variadic_max({", ".join(f"std::round({time_var_name(line.line_number)}, {per_hit_precision})" for line in lines if not line.ignore)})).length()"
		self.time_percentage_max_digits = f"std::string(variadic_max({", ".join(f"std::round({percentag(line.line_number)}, {per_hit_precision})" for line in lines if not line.ignore)})).length()"

	def set_profiling(self):
		self.opening = f"""{self.ignore_line_prefix}{self.base_opening}
{self.function_name}_calls++;"""
		# max_line_width = max(len(f"{get_line_prefix(line.line_number)}{line.txt}") for line in self.lines)
		for line in self.lines:
			line.set_profiling()
		self.closing = f"""{self.ignore_line_prefix}{self.base_closing}"""

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
		return f"{self.opening}\n{"\n".join(str(line) for line in self.lines)}\n{self.closing}"

	def __len__(self):
		return len(self.__repr__())

class Line:
	def __init__(self, txt):
		self.txt = txt.replace("\t", " " * tab_width)
		self.base_txt = self.txt
		self.hits, self.time, self.per_hit = None, None, None

	def set_profiling(self):
		self.txt = f"{self.prefix}{self.base_txt}{self.suffix}"

	def set_line_stats(self, line_number):
		self.hits = f"{}"
		self.time = 0
		self.per_hit = 0

	def __repr__(self):
		return self.txt

	def __len__(self):
		return len(self.__repr__())

class SingleLine(Line):
	def __init__(self, txt, line_number):
		super().__init__(txt)
		self.line_number = line_number
		self.prefix = f"{start_chrono_macro_name}({line_number}){" " * nb_space_line_prefix}"
		self.suffix = f"{" " * nb_space_line_suffix}{top_chrono_macro_name}({line_number})"

class FunctionLine(Line):
	def __init__(self, txt, ignore):
		super().__init__(txt)
		# the following 4 shall be set by their Function
		self.line_number = 0
		self.prefix = None
		self.suffix = None
		self.ignore = ignore

	def set_line_stats(self, line_number):
		self.hits = f""
		self.time = 0
		self.per_hit = 0
		self.time_percentage

def handle_function_match(m, content):
	def lines_from_body(text_body):
		lines = [
			FunctionLine(line_txt, any(pattern.match(line_txt) for pattern in ignore_patterns))
			for line_txt in text_body.replace('\r\n', '\n').split('\n')[1:-1]
		]

	start_index, end_index = m.end(), 0
	function = None
	# N = number of currently opened left bracket that are yet to be closed
	# K = first character's index after the opening left bracket
	N, K, function_name = 0, 0, ""
	for i in range(start_index, len(content)):
		if content[i] == '{':
			if N == 0: K = i + 1
			N += 1
		elif content[i] == '}':
			N -= 1
			if N == 0:
				# this excludes the K'th character
				opening = content[start_index:K]
				lines, longest_line_index = lines_from_body(content[K:i])
				end_index = i
				first_body_line_number = content[:start_index].count('\n') + 2
				function = Function(opening, lines, longest_line_index, start_index, end_index, first_body_line_number, function_name)
				break
		elif content[i] == '(' and N == 0:
			j = i - 1
			while content[j] != ' ': j -= 1
			function_name = content[j+1:i]
	if function == None: raise ValueError("Mismatched brackets")
	return function

def handle_function_matches(function_matches, content):
	global min_line_number, max_line_number
	functions = [handle_function_match(m, content) for m in function_matches]
	min_line_number = functions[0].first_body_line_number
	max_line_number = functions[-1].last_body_line_number
	return functions

def handle_line_matches(line_matches, content):
	return []

def handle_file_path(original_file_path, working_file_path):
	shutil.copyfile(original_file_path, working_file_path)
	content = ""
	with open(working_file_path, 'r', encoding='utf-8') as file: content = file.read()
	function_matches = [match for match in profile_function_pattern.finditer(content)]
	line_matches = [match for match in profile_line_pattern.finditer(content)]
	n_function_matches = len(function_matches)
	n_line_matches = len(function_matches)
	functions, lines = None, None
	if n_function_matches > 0:
		print(f"found {n_function_matches} function{'s' if n_function_matches > 1 else ''} to profile in {original_file_path}")
		functions = handle_function_matches(function_matches, content)
	else:
		print(f"no function to profile found in {original_file_path}")
	
	if n_line_matches > 0:
		print(f"found {n_line_matches} line{'s' if n_line_matches > 1 else ''} to profile in {original_file_path}")
		lines = handle_line_matches(line_matches, content)
	else:
		f"no line to profile found in {original_file_path}"
		if n_function_matches == 0: return
	
	file = File(content, functions, lines)
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
