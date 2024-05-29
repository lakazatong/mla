

f"""
std::vector<{line_class_name}> lines = {{ std::make_unique<{single_line_class_name}>("", 0), {", ".join(f"std::make_unique<{single_line_class_name}>({line.base_txt}, {line.line_number})" if isinstance(line, SingleLine) else f"std::make_unique<{function_line_class_name}>({line.base_txt})" for line in lines)} }};
"""