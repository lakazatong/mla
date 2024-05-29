#ifndef PROFILE_{common_filename}_HPP
#define PROFILE_{common_filename}_HPP
namespace {namespace_name} {{

#include <vector>
#include <regex>
#include <string>

std::vector<std::regex> ignore_patterns {{
	{',\n'.join(ignore_patterns)}
}};

bool anyMatch(const std::string& txt, const std::vector<std::regex>& patterns);

}}
#endif /* PROFILE_{common_filename}_HPP */