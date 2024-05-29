#include "profile_{common_filename}.hpp"
namespace {namespace_name} {{

bool anyMatch(const std::string& txt, const std::vector<std::regex>& patterns) {{
	for (const auto& pattern : patterns) {{
		if (std::regex_search(txt, pattern)) {{
			return true;
		}}
	}}
	return false;
}}

}}