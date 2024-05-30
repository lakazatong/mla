#include "profile.hpp"

namespace {profile_namespace} {{

namespace {file.filename} {{

	// lines[0] is a dummy since line numbers start at 1
	// all lines that were not profiled will have an empty base_txt and a line_number of 0
	lines_t lines{{ std::make_unique<single_line_t>(0, ""), {lines_array} }};
	functions_t functions{{ {functions_array} }};
	files[{file.filename}] = file_t{{lines, functions}};

}}

}}