import re, os
from typing import List

# ----------------------------------------------------------------------
# Parameters

# the @ is for intern purposes
add_profile_function_pattern = re.compile(r"\/\/ @?profile\s+function\s*\+\s*\r?\n")
remove_profile_function_pattern = re.compile(r"\/\/ @?profile\s+function\s*-\s*\r?\n")
add_profile_line_pattern = re.compile(r"\/\/ @?profile\s+line\s*\+\s*\r?\n")
remove_profile_line_pattern = re.compile(r"\/\/ @?profile\s+line\s*-\s*\r?\n")

profile_namespace = "Profiled"
line_class_name = Line.__name__
single_line_class_name = SingleLine.__name__
function_line_class_name = FunctionLine.__name__
function_class_name = Function.__name__
file_class_name = File.__name__
# lines to ignore
ignore_function_line_patterns = [
	re.compile(r"^\s*[{}]+\s*$") # ignore only brackets
	re.compile(r"^\s*//(?:a|[^a])*$") # ignore single line comments
	re.compile(r"^\s*return;\s*$") # ignore empty returns
]
start_chrono_macro_name = "START_CHRONO"
top_chrono_macro_name = "TOP_CHRONO"
nb_space_line_prefix = 10
nb_space_line_suffix = 10
tab_width = 4

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
		file_class_name=file_class_name
	)
	with open("generated/profile.hpp", "w") as f:
		f.write(formated)

def generate_profile_cpp(file):
	content = ""
	with open("templates/profile.cpp", "r") as f:
		content = f.read()
	formated = content.format(
		profile_namespace=profile_namespace,
		ignore_function_line_patterns_array=',\n\t'.join(f'std::regex("{pattern.replace("\\", "\\\\")}")' for pattern in ignore_function_line_patterns),
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
		lines_array=", ".join(f'std::make_unique<{"single_line_t" if isinstance(line, SingleLine) else "function_line_t"}>({line.line_number}, "{line.base_txt}")' for line in file.lines)
	)
	with open(f"generated/profile_{file.filename}.cpp", "w") as f:
		f.write(formated)

# Generate C++ files
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# Classes responsible for C++ code manipulation

class Line:
	def __init__(self, line_number, txt):
		self.line_number = line_number
		self.txt = txt.replace("\t", " " * tab_width)
		self.base_txt = self.txt

	def set_profiling(self):
		self.txt = f"{self.prefix}{self.base_txt}{self.suffix}"

	def __repr__(self):
		return self.txt

	def __len__(self):
		return len(self.__repr__())

class SingleLine(Line):
	def __init__(self, line_number, txt):
		super().__init__(line_number, txt)
		self.prefix = f"{start_chrono_macro_name}({line_number}){" " * nb_space_line_prefix}"
		self.suffix = f"{" " * nb_space_line_suffix}{top_chrono_macro_name}({line_number})"

class FunctionLine(Line):
	def __init__(self, line_number, txt):
		super().__init__(line_number, txt)
		self.prefix = None
		self.suffix = None
		self.ignore = any(pattern.match(self.base_txt) for pattern in ignore_function_line_patterns)

class Function:
	def __init__(self, first_line_number, last_line_number, longest_line_number):
		self.first_line_number = first_line_number
		self.last_line_number = last_line_number
		self.longest_line_number = longest_line_number

class File:
	def __init__(self, filename: str, lines: List[Line], functions: List[Function]):
		self.filename = filename
		self.lines = lines
		self.functions = functions

	def set_profiling(self):
		pass

	def write_to(self, path):
		pass

# Classes responsible for C++ code manipulation
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# Input C++ file(s) handling (scan and add/remove profiling macros)

def handle_file_path(file_path):
	content = ""
	with open(file_path, "r", encoding="utf-8") as file: content = file.read()
	
	add_profile_functions = list(add_profile_function_pattern.finditer(content))
	remove_profile_functions = list(remove_profile_function_pattern.finditer(content))
	add_profile_lines = list(add_profile_line_pattern.finditer(content))
	remove_profile_lines = list(remove_profile_line_pattern.finditer(content))

	n_add_profile_functions = len(add_profile_functions)
	n_remove_profile_functions = len(remove_profile_functions)
	n_add_profile_lines = len(add_profile_lines)
	n_remove_profile_lines = len(remove_profile_lines)
	
	functions, lines = [], []
	
	positive_string = lambda n, s: f"found {n} {s}{'s' if n > 1 else ''} to add profiling to in {file_path}"
	negative_string = lambda s: f"no {s} to add profiling to found in {file_path}"

	if n_add_profile_functions > 0:
		print(positive_string(n_add_profile_functions, "function"))
		functions.extend(handle_add_profile_functions(add_profile_functions, content))
	else:
		print(negative_string("function"))
	
	if n_remove_profile_functions > 0:
		print(positive_string(n_remove_profile_functions, "function"))
		functions.extend(handle_remove_profile_functions(remove_profile_functions, content))
	else:
		print(negative_string("function"))
	
	if n_add_profile_lines > 0:
		print(positive_string(n_add_profile_lines, "line"))
		lines.extend(handle_add_profile_lines(add_profile_lines, content))
	else:
		print(negative_string("line"))
	
	if n_remove_profile_lines > 0:
		print(positive_string(n_remove_profile_lines, "line"))
		lines.extend(handle_n_add_profile_functions(add_profile_functions, content))
	else:
		print(negative_string("line"))
		if n_add_profile_functions == 0 and n_remove_profile_functions == 0 and n_add_profile_lines == 0:
			return

	filename = os.path.splitext(os.path.basename(file_path))[0]
	file = File(filename, content, functions, lines)
	file.set_profiling()
	file.write_to(os.path.join(os.path.dirname(file_path), f"{filename}_profiled.cpp"))

# Input C++ file(s) handling (scan and add/remove profiling macros)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# CLI

def main():
	if not os.path.exists("generated"): os.mkdir("generated")

	file = File("mla", [SingleLine(2, " al lo "), FunctionLine(3, "aluile")], [Function(1, 2, 3), Function(1, 2, 3)])
	generate_profile_hpp(file)
	generate_profile_cpp(file)
	generate_profile_filename_cpp(file)
	
	return

	if len(sys.argv) < 2:
		print("provide cpp files")
		return

	for file_path in sys.argv[1:]:
		handle_file_path(file_path)

# CLI
# ----------------------------------------------------------------------

if __name__ == "__main__":
	main()
