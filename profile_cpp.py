import re, os, sys
from typing import List

# TODO:
# add meta data (longest profiled line number present in the file to align line number of all single line)
# define chronos after the #include "profile.hpp"
# make // profile line + and - work in place with profile.hpp included
# single line reports

# ----------------------------------------------------------------------
# Parameters

# python does not support \h as far as I'm aware
hspace_pat = r"[^\S\r\n]"
add_profile_function_pattern = re.compile(rf"\/\/{hspace_pat}*profile{hspace_pat}+function{hspace_pat}*(\+){hspace_pat}*\n")
remove_profile_function_pattern = re.compile(rf"\/\/{hspace_pat}*profile{hspace_pat}+function{hspace_pat}*(-){hspace_pat}*\n")
add_profile_line_pattern = re.compile(rf"\/\/{hspace_pat}*profile{hspace_pat}+line{hspace_pat}*(\+){hspace_pat}*\n")
remove_profile_line_pattern = re.compile(rf"\/\/{hspace_pat}*profile{hspace_pat}+line{hspace_pat}*(-){hspace_pat}*\n")
include_profile_hpp_pattern = re.compile(rf"#include{hspace_pat}*\"generated\/profile\.hpp\"{hspace_pat}*")

profile_namespace = "Profiled"
line_class_name = "Line"
single_line_class_name = "SingleLine"
function_line_class_name = "FunctionLine"
function_class_name = "Function"
file_class_name = "File"
# lines to ignore
ignore_function_line_patterns = [
	re.compile(r"^\s*[{}]+\s*$"), # ignore only brackets
	re.compile(r"^\s*//(?:a|[^a])*$"), # ignore single line comments
	re.compile(r"^\s*return;\s*$") # ignore empty returns
]
nb_space_line_prefix = 10
nb_space_line_suffix = 10
tab_width = 4
define_chrono_macro_name = "DEFINE_CHRONO"
start_chrono_macro_name = "START_CHRONO"
top_chrono_macro_name = "TOP_CHRONO"

# these are deduced and are not meant to be changed

profile_line_prefix_pattern = re.compile(rf"{start_chrono_macro_name}\(\s*\d+\s*\){" " * nb_space_line_prefix}")
profile_line_suffix_pattern = re.compile(rf"{" " * nb_space_line_suffix}{top_chrono_macro_name}\(\s*\d+\s*\)")

# Parameters
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# Generate C++ files

def generate_profile_hpp(file):
	content = ""
	with open("templates/profile.hpp", "r") as f:
		content = f.read()
	formated = content.format(
		profile_namespace=profile_namespace,
		line_class_name=line_class_name,
		single_line_class_name=single_line_class_name,
		function_line_class_name=function_line_class_name,
		function_class_name=function_class_name,
		file_class_name=file_class_name,
		define_chrono_macro_name=define_chrono_macro_name,
		start_chrono_macro_name=start_chrono_macro_name,
		top_chrono_macro_name=top_chrono_macro_name
	)
	with open("generated/profile.hpp", "w") as f:
		f.write(formated)

def generate_profile_cpp(file):
	content = ""
	with open("templates/profile.cpp", "r") as f:
		content = f.read()
	formated = content.format(
		profile_namespace=profile_namespace,
		start_chrono_macro_name=start_chrono_macro_name,
		start_chrono_macro_name_length=len(start_chrono_macro_name),
		top_chrono_macro_name=top_chrono_macro_name,
		nb_space_line_prefix=nb_space_line_prefix,
		nb_space_line_suffix=nb_space_line_suffix,
		tab_width=tab_width
	)
	with open("generated/profile.cpp", "w") as f:
		f.write(formated)

def generate_profile_filename_cpp(file):
	content = ""
	with open("templates/profile_filename.cpp", "r") as f:
		content = f.read()
	formated = content.format(
		profile_namespace=profile_namespace,
		file=file,
		functions_array=", ".join(f"function_t({function.first_line_number}, {function.last_line_number}, {function.longest_line_number})" for function in file.functions),
		lines_array=", ".join(f'std::make_unique<{"single_line_t" if isinstance(line, SingleLine) else "function_line_t"}>({line.line_number}, "{line.txt.replace(" " * tab_width, "\t")}")' for line in file.lines)
	)
	with open(f"generated/profile_{file.filename}.cpp", "w") as f:
		f.write(formated)

# Generate C++ files
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# Classes responsible for C++ code manipulation

class Line:
	def __init__(self, line_number, txt, start_index, end_index):
		self.line_number = line_number
		self.raw_txt = txt
		self.txt = txt.replace("\t", " " * tab_width)
		self.profiled_txt = self.txt
		self.start_index = start_index
		self.end_index = end_index
		self.prefix = ""
		self.suffix = ""

	def set_profiling(self):
		self.prefix = f"{start_chrono_macro_name}({self.line_number}){" " * nb_space_line_prefix}"
		self.suffix = f"{" " * nb_space_line_suffix}{top_chrono_macro_name}({self.line_number})"

	def unset_profiling(self):
		self.prefix = ""
		self.suffix = ""

	def undo_profiling(self):
		# self.base_txt is already the result of add_profiling + set_profiling
		# undo that
		self.txt = profile_line_suffix_pattern.sub("", profile_line_prefix_pattern.sub("", self.raw_txt)).replace("\t", " " * tab_width)

	def apply_profiling(self):
		self.profiled_txt = f"{self.prefix}{self.txt}{self.suffix}"

	def __repr__(self):
		return self.profiled_txt

	def __len__(self):
		return len(self.__repr__())

class SingleLine(Line):
	def __init__(self, line_number, txt, start_index, end_index):
		super().__init__(line_number, txt, start_index, end_index)

class FunctionLine(Line):
	def __init__(self, line_number, txt, start_index, end_index):
		super().__init__(line_number, txt, start_index, end_index)
		self.ignore = any(pattern.match(self.base_txt) for pattern in ignore_function_line_patterns)

class Function:
	def __init__(self, first_line_number, last_line_number, longest_line_number):
		self.first_line_number = first_line_number
		self.last_line_number = last_line_number
		self.longest_line_number = longest_line_number
		# self.ignore_line_prefix = " " * (len(start_chrono_macro_name) + 1 + self.max_line_number_length + 1 + nb_space_line_prefix)
		# self.ignore_line_suffix = ""

	def set_profiling(self):
		return
		for line in self.lines:
			line.set_profiling()

	def __repr__(self):
		return "\n...function...\n"
		return f"{self.opening}\n{"\n".join(str(line) for line in self.lines)}\n{self.closing}"

	def __len__(self):
		return len(self.__repr__())

class File:
	def __init__(self, filename: str, content: str, lines: List[Line], functions: List[Function]):
		self.filename = filename
		self.content = content
		self.lines = lines
		self.functions = functions
		self.preamble = ""

	def set_profiling(self):
		for line in self.lines:
			line.set_profiling()
		for function in self.functions:
			function.set_profiling()

	def unset_profiling(self):
		for line in self.lines:
			line.unset_profiling()
		for function in self.functions:
			function.unset_profiling()
	
	def undo_profiling(self):
		for line in self.lines:
			line.undo_profiling()
		for function in self.functions:
			function.undo_profiling()

	def apply_profiling(self):
		# doing it this way makes the function's profiling take priority over single line profiling
		for line in self.lines:
			line.apply_profiling()
		for function in self.functions:
			function.apply_profiling()

	def write_to(self, path):
		with open(path, "w", encoding="utf-8") as f:
			f.write(str(self))

	def __repr__(self):
		r = self.preamble
		last_index = 0
		for line in sorted(self.lines, key=lambda line: line.line_number):
			r += f"{self.content[last_index:line.start_index]}{line}\n"
			last_index = line.end_index + 1
		r += self.content[last_index:]
		return r

# Classes responsible for C++ code manipulation
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# Input C++ file.s handling (scan and add/remove profiling macros)

def handle_add_profile_functions(matches, content):
	return []

def handle_remove_profile_functions(matches, content):
	return []

def handle_add_profile_lines(matches, content):
	r = []
	for m, offset in matches:
		# right on the first character of the line we are interested in
		start_index = m.end() - offset + 1
		before_line = content[:start_index]
		# the next non empty line number after the match
		line_number = before_line.count("\n") + 1
		end_index = len(before_line) + content[start_index:].find("\n")
		line_str = content[start_index:end_index]
		sl = SingleLine(line_number, line_str, start_index, end_index)
		sl.set_profiling()
		r.append(sl)
	return r

def handle_remove_profile_lines(matches, content):
	r = []
	for m, offset in matches:
		# right on the first character of the line we are interested in
		start_index = m.end() - offset + 1
		before_line = content[:start_index]
		# the next non empty line number after the match
		line_number = before_line.count("\n") + 1
		end_index = len(before_line) + content[start_index:].find("\n")
		line_str = content[start_index:end_index]
		sl = SingleLine(line_number, line_str, start_index, end_index)
		sl.undo_profiling()
		r.append(sl)
	return r

def handle_file_path(file_path):
	content = ""
	with open(file_path, "r", encoding="utf-8") as file: content = file.read()
	
	add_profile_functions_matches = []
	remove_profile_functions_matches = []
	add_profile_lines_matches = []
	remove_profile_lines_matches = []

	offset = 0
	def replace_and_capture(match, L, trailing_regex):
		nonlocal offset
		s = match.group(0)
		r, _ = re.subn(trailing_regex, "", s)
		offset += len(s) - 1 - len(r)
		L.append((match, offset))
		return r + "\n"

	trailing_plus = re.compile(r"[+\s]*$")
	trailing_minus = re.compile(r"[-\s]*$")
	original_content = content
	content = add_profile_function_pattern.sub(lambda match: replace_and_capture(match, add_profile_functions_matches, trailing_plus), content)
	content = remove_profile_function_pattern.sub(lambda match: replace_and_capture(match, remove_profile_functions_matches, trailing_minus), content)
	content = add_profile_line_pattern.sub(lambda match: replace_and_capture(match, add_profile_lines_matches, trailing_plus), content,)
	content = remove_profile_line_pattern.sub(lambda match: replace_and_capture(match, remove_profile_lines_matches, trailing_minus), content)

	n_add_profile_functions = len(add_profile_functions_matches)
	n_remove_profile_functions = len(remove_profile_functions_matches)
	n_add_profile_lines = len(add_profile_lines_matches)
	n_remove_profile_lines = len(remove_profile_lines_matches)
	
	functions, lines = [], []

	if n_add_profile_functions > 0:
		print(f"found {n_add_profile_functions} function{'s' if n_add_profile_functions > 1 else ''} to add profiling to in {file_path}")
		functions.extend(handle_add_profile_functions(add_profile_functions_matches, content))
	# else:
		# print(f"no function to add profiling to found in {file_path}")
	
	if n_remove_profile_functions > 0:
		print(f"found {n_remove_profile_functions} function{'s' if n_remove_profile_functions > 1 else ''} to remove profiling from in {file_path}")
		functions.extend(handle_remove_profile_functions(remove_profile_functions_matches, content))
	# else:
		# print(f"no function to remove profiling from found in {file_path}")
	
	if n_add_profile_lines > 0:
		print(f"found {n_add_profile_lines} line{'s' if n_add_profile_lines > 1 else ''} to add profiling to in {file_path}")
		lines.extend(handle_add_profile_lines(add_profile_lines_matches, content))
	# else:
		# print(f"no line to add profiling to found in {file_path}")
	
	if n_remove_profile_lines > 0:
		print(f"found {n_remove_profile_lines} {s}{'s' if n_remove_profile_lines > 1 else ''} to remove profiling from in {file_path}")
		lines.extend(handle_remove_profile_lines(remove_profile_lines_matches, content))
	else:
		# print(f"no line to remove profiling from found in {file_path}")
		if n_add_profile_functions == 0 and n_remove_profile_functions == 0 and n_add_profile_lines == 0:
			print(f"{file_path} done")
			return

	filename = os.path.splitext(os.path.basename(file_path))[0]
	file = File(filename, content, lines, functions)
	file.apply_profiling()
	generate_profile_hpp(file)
	generate_profile_cpp(file)
	generate_profile_filename_cpp(file)
	# file.write_to(os.path.join(os.path.dirname(file_path), f"{filename}_profiled.cpp"))
	print(f"{file_path} done")

# Input C++ file.s handling (scan and add/remove profiling macros)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# CLI

def main():
	if not os.path.exists("generated"): os.mkdir("generated")

	# test file
	# file = File("mla", [SingleLine(2, " al lo "), FunctionLine(3, "aluile")], [Function(1, 2, 3), Function(1, 2, 3)])
	# return

	if len(sys.argv) < 2:
		print("provide cpp files")
		return

	for file_path in sys.argv[1:]:
		handle_file_path(file_path)

# CLI
# ----------------------------------------------------------------------

if __name__ == "__main__":
	main()
