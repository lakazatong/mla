#include "profile.hpp"

namespace {profile_namespace} {{

namespace {filename} {{

	// lines[0] is a dummy since line numbers start at 1
	// all lines that were not profiled will have an empty base_txt and a line_number of 0
	lines_t lines{{ std::make_unique<{single_line_class_name}>("", 0), {", ".join(f"std::make_unique<{single_line_class_name}>({line.base_txt}, {line.line_number})" if isinstance(line, SingleLine) else f"std::make_unique<{function_line_class_name}>({line.base_txt})" for line in file.lines)} }};
	functions_t functions{{ {", ".join(f"function_t({function.first_line_number}, {function.last_line_number})" for function in file.functions)} }};
	file_t file{lines, functions};
	files[{filename}] = file;

}}

}}