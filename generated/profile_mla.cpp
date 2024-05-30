#include "profile.hpp"

namespace Profiled {

namespace mla {

	// lines[0] is a dummy since line numbers start at 1
	// all lines that were not profiled will have an empty base_txt and a line_number of 0
	lines_t lines{ std::make_unique<single_line_t>(0, ""), std::make_unique<single_line_t>(407, "    int max_value = 0;") };
	functions_t functions{  };
	files[mla] = file_t{lines, functions};

}

}