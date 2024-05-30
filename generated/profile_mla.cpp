#include "profile.hpp"

namespace Profiled {

namespace mla {

	// lines[0] is a dummy since line numbers start at 1
	// all lines that were not profiled will have an empty base_txt and a line_number of 0
	lines_t lines{ std::make_unique<single_line_t>(0, ""), std::make_unique<single_line_t>(2, " al lo "), std::make_unique<function_line_t>(3, "aluile") };
	functions_t functions{ function_t(1, 2, 3), function_t(1, 2, 3) };
	files[mla] = file_t{lines, functions};

}

}