import re, os

# ----------------------------------------------------------------------
# parameters

profile_namespace = "Profiled"
single_line_class_name = SingleLine.__name__
function_line_class_name = FunctionLine.__name__
function_class_name = Function.__name__
file_class_name = File.__name__
# lines to ignore
ignore_patterns = [
	r"^\s*[{}]+\s*$", # ignore only brackets
	r"^\s*//(?:a|[^a])*$", # ignore single line comments
	r"^\s*return;\s*$" # ignore empty returns
]
start_chrono_macro_name = "START_CHRONO"
top_chrono_macro_name = "TOP_CHRONO"
nb_space_line_prefix = 10
nb_space_line_suffix = 10
tab_width = 4

# parameters
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# classes

class Line:
	def __init__(self, line_number, txt):
		self.line_number = line_number
		self.txt = txt
		self.base_txt = txt

class SingleLine(Line):
	def __init__(self, line_number, txt):
		super().__init__(line_number, txt)

class FunctionLine(Line):
	def __init__(self, line_number, txt):
		super().__init__(line_number, txt)
		self.ignore = any(pattern.match(line_txt) for pattern in ignore_patterns)

class Function:
	def __init__(self, first_line_number, last_line_number, longest_line_number):
		self.first_line_number = first_line_number
		self.last_line_number = last_line_number
		self.longest_line_number = longest_line_number

class File:
	def __init__(self, filename, lines, functions):
		self.filename = filename
		self.lines = lines
		self.functions = functions

# classes
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# profile.hpp

def generate_profile_hpp(file):
	content = ""
	with open("templates/profile.hpp", "r") as f:
		content = f.read()
	formated = content.format(
		profile_namespace=profile_namespace,
		single_line_class_name=single_line_class_name,
		function_line_class_name=function_line_class_name,
		function_class_name=function_class_name,
		file_class_name=file_class_name
	)
	with open("generated/profile.hpp", "w") as f:
		f.write(formated)

# profile.hpp
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# profile.cpp

def generate_profile_cpp(file):
	content = ""
	with open("templates/profile.cpp", "r") as f:
		content = f.read()
	formated = content.format(
		profile_namespace=profile_namespace,
		ignore_patterns_array=',\n\t'.join(f'std::regex("{pattern.replace("\\", "\\\\")}")' for pattern in ignore_patterns),
		start_chrono_macro_name=start_chrono_macro_name,
		start_chrono_macro_name_length=len(start_chrono_macro_name),
		top_chrono_macro_name=top_chrono_macro_name,
		nb_space_line_prefix=nb_space_line_prefix,
		nb_space_line_suffix=nb_space_line_suffix,
		tab_width=tab_width
	)
	with open("generated/profile.cpp", "w") as f:
		f.write(formated)

# profile.cpp
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# profile_{filename}.cpp

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

# profile_{filename}.cpp
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# given .cpp file analysis

def handle_file_path(file_path):
	content = ""
	with open(file_path, "r", encoding="utf-8") as file: content = file.read()
	function_matches = [match for match in profile_function_pattern.finditer(content)]
	line_matches = [match for match in profile_line_pattern.finditer(content)]
	n_function_matches = len(function_matches)
	n_line_matches = len(function_matches)
	functions, lines = None, None
	if n_function_matches > 0:
		print(f"found {n_function_matches} function{'s' if n_function_matches > 1 else ''} to profile in {file_path}")
		functions = handle_function_matches(function_matches, content)
	else:
		print(f"no function to profile found in {file_path}")
	
	if n_line_matches > 0:
		print(f"found {n_line_matches} line{'s' if n_line_matches > 1 else ''} to profile in {file_path}")
		lines = handle_line_matches(line_matches, content)
	else:
		f"no line to profile found in {file_path}"
		if n_function_matches == 0: return
	
	file = File(content, functions, lines)
	file.set_profiling()

# given .cpp file analysis
# ----------------------------------------------------------------------

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

if __name__ == "__main__":
	main()
