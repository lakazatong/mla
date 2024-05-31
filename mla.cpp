#include <iostream>
#include <algorithm>
#include <bitset>
#include <chrono>
#include <numeric>
#include <memory>
#include <string>
#include <iomanip>

#include "generated/profile.hpp"

#include "mla.hpp"

using namespace std;

// categories
const int NONE = 0;
const int ANTIQUE = 1;
const int WEAPON = 2;
const int FOOD = 3;

// rarities
const int NORMAL_GOOD = 0;
const int RARE_GOOD = 1;
const int VITAL_GOOD = 2;
const int ATTRIBUTE_STONE = 3;

vector<unique_ptr<Item>> all_items;
int all_items_length = 0;

const int cart_width = 6;
const int cart_height = 4;
const int cart_size = cart_height * cart_width;
// const int trailing_zeros_length = 32 - cart_size;

void apply_full_cart_bonus(Cart& cart) {
	cart.value += cart_width * cart_height * 20;
}

// -------------------
// Utils

inline bool valid_pos(int index) {
	return index >= 0 && index < cart_size;
}

vector<int> get_neighbours(int index) {
	vector<int> r;
	int left = index - 1;
	int right = index + 1;
	int top = index - cart_width;
	int bottom = index + cart_width;
	if (valid_pos(left)) r.push_back(left);
	if (valid_pos(right)) r.push_back(right);
	if (valid_pos(top)) r.push_back(top);
	if (valid_pos(bottom)) r.push_back(bottom);
	return r;
}

bool has_common_element(const set<int>& set1, const set<int>& set2) {
	for (int element : set1) {
		if (set2.count(element) > 0) { return true; }
	}
	return false;
}

template <typename T>
std::ostream& operator<<(std::ostream& os, const std::vector<T>& vec) {
	os << "[";
	for (size_t i = 0; i < vec.size(); ++i) {
		os << setw(2) << setfill(' ') << vec[i];
		if (i != vec.size() - 1) {
			os << ", ";
		}
	}
	os << "]";
	return os;
}

constexpr unsigned factorial(int n) {
	unsigned result = 1;
	for (int i = 2; i <= n; ++i) {
		result *= i;
	}
	return result;
}

constexpr unsigned nChooseK(int n, int k) {
	return factorial(n) / (factorial(k) * factorial(n - k));
}

constexpr unsigned int count_ones(unsigned int n) {
	unsigned int count = 0;
	while (n) {
		n &= (n - 1);
		count++;
	}
	return count;
}

// Utils
// -------------------

// -------------------
// Item

Item::Item(int category, int rarity, int value, const vector<int>& shape, int width)
	: category(category), rarity(rarity), base_value(value), value(value),
	shape(shape), width(width), item_type(0) {
	height = ((int)shape.size()) / width;
	size = height * width;
	id = all_items_length++;
	for (int i = 0; i <= cart_height - height; i++) {
		for (int j = 0; j <= cart_width - width; j++) {
			possible_positions.push_back(i * cart_width + j);
		}
	}
}

void Item::set_adjacent_items(const vector<int>& cells, int k) {
	set<int> r;
	for (int i = 0; i < height; i++) {
		for (int j = 0; j < width; j++) {
			if (shape[i * width + j] == 0) continue;
			for (auto j : get_neighbours(k + i * cart_width + j)) {
				int neighbour_id = cells[j];
				if (neighbour_id != -1 && neighbour_id != id) { r.insert(neighbour_id); }
			}
		}
	}
	adjacent_items.assign(r.begin(), r.end());
}

template<typename T>
void Item::create(int category, int rarity, int value, const vector<int>& shape, int width) {
	static_assert(is_base_of<Item, T>::value, "T must be derived from Item");
	all_items.push_back(make_unique<T>(category, rarity, value, shape, width));
}

std::ostream& operator<<(std::ostream& os, const Item& item) {
	os << "category: " << item.category << ", rarity: " << item.rarity << ", base_value: " << item.base_value
		<< ", value: " << item.value << ", width: " << item.width << ", height: " << item.height << ", id: " << item.id
		<< ", size: " << item.size << ", item_type: " << item.item_type << std::endl;
	os << "shape: [";
	for (size_t i = 0; i < item.shape.size(); ++i) {
		os << item.shape[i];
		if (i != item.shape.size() - 1) {
			os << ", ";
		}
	}
	os << "]" << std::endl;
	os << "possible_positions: ";
	for (int pos : item.possible_positions) {
		os << pos << " ";
	}
	os << std::endl;
	os << "adjacent_items: ";
	for (int adj : item.adjacent_items) {
		os << adj << " ";
	}
	os << std::endl;
	return os;
}

// Item
// -------------------

// -------------------
// Cart

Cart::Cart() : value(0), cells(cart_size, -1), cells_as_number(0) {}

bool Cart::full() const {
	return find(cells.begin(), cells.end(), -1) == cells.end();
}

void Cart::add_item(const Item& item, int k) {
	items.push_back(item.id);
	items_coords.push_back(k);
	for (int i = 0; i < item.height; i++) {
		for (int j = 0; j < item.width; j++) {
			if (item.shape[i * item.width + j] == 1) {
				cells[k + i * cart_width + j] = item.id;
			}
		}
	}
}

int Cart::set_value() {
	for (size_t i = 0; i < items.size(); ++i) {
		Item& item = *all_items[items[i]];
		item.value = item.base_value;
		item.set_adjacent_items(cells, items_coords[i]);
	}
	for (int i : items) { all_items[i]->apply_effect(*this); }
	value = 0;
	for (int i : items) { value += all_items[i]->value; }
	if (full()) { apply_full_cart_bonus(*this); }
	return value;
}

void Cart::compress_attributes() {
	// items_set = set<int>(items.begin(), items.end());
	cells_as_number = 0;
	for (int i = cart_size - 1; i >= 0; i--) {
		cells_as_number |= ~(cells[i] >> 31U) & (1U << i);
		/*cout << cells[i] << endl;
		cout << bitset<8>(cells[i]) << endl;
		cout << bitset<8>(~(cells[i] >> 31U)) << endl;
		if (cells[i] != -1) {
			cells_as_number |= (1U << (cart_size - 1 - i));
		}*/
	}
	/*
	if (cells_as_number != cells_as_number2) {
		cout << "cells_as_number: " << cells_as_number << ", cells_as_number2: " << cells_as_number2 << endl;
		cout << cells << endl;
		cout << "[ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]" << endl;
		cout << "[23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10,  9,  8,  7,  6,  5,  4,  3,  2,  1,  0]" << endl;
		exit(1);
	}*/
	// cells_as_number <<= trailing_zeros_length;
}

void Cart::set_canonical_form() {
	canonical_form.clear();
	for (size_t i = 0; i < items.size(); ++i) {
		// hash item type and pos
		canonical_form.push_back(all_items[items[i]]->item_type * cart_size + items_coords[i]);
	}
	sort(canonical_form.begin(), canonical_form.end());
}

string Cart::to_string() const {
	const int GREY = 90, RED = 31, GREEN = 32, YELLOW = 33, BLUE = 34, PURPLE = 35, CYAN = 36, WHITE = 37;
	vector<int> colors = { GREY, RED, GREEN, YELLOW, BLUE, PURPLE, CYAN, WHITE };
	string r;

	for (int i = 0; i < cart_height; ++i) {
		string row_str = "";
		for (int j = 0; j < cart_width; ++j) {
			int cell = cells[i * cart_width + j];
			if (cell < -1 || cell >= static_cast<int>(colors.size()) - 1) {
				throw invalid_argument("Unknown cell value: " + std::to_string(cell));
			}
			row_str += "\033[" + std::to_string(colors[cell + 1]) + "m██\033[0m";
		}
		r += row_str + "\n";
	}

	return r;
}

// Cart
// -------------------

// -------------------
// Define all items

class AncientHolyGrail : public Item {
public:
	AncientHolyGrail(int category, int rarity, int value, const vector<int>& shape, int width)
		: Item(category, rarity, value, shape, width) {
		this->item_type = 0;
	}

	void apply_effect(Cart& cart) override {
		for (int adj_index : adjacent_items) {
			if (all_items[adj_index]->rarity == ATTRIBUTE_STONE) {
				cart.value += 200;
			}
		}
	}
};

// Define all items
// -------------------

// -------------------
// Algorithm

vector<vector<Cart>> all_carts;
// as many as there are items combinations
unsigned int all_carts_length;
// basically: one_item_carts_index[i] = available_items_to_index({i}) since they will be often needed
vector<unsigned int> one_item_carts_index;

/*

example with 4 items ({abcd} means "all possible carts with items of index 0 if a, 1 if b, 2 if c and 3 if d"):

1000 = ...
0100 = ...
0010 = ...
0001 = ...

0011 = {{0010 + 0001} + {0001 + 0010}}
0101 = {{0100 + 0001} + {0001 + 0100}}
1001 = {{1000 + 0001} + {0001 + 1000}}
0110 = {{0100 + 0010} + {0010 + 0100}}
1010 = {{1000 + 0010} + {0010 + 1000}}
1100 = {{1000 + 0100} + {0100 + 1000}}

0111 = {{0110 + 0001} + {0101 + 0010} + {0011 + 0100}}
1011 = {{1010 + 0001} + {1001 + 0010} + {0011 + 1000}}
1101 = {{1100 + 0001} + {1001 + 0100} + {0101 + 1000}}
1110 = {{1100 + 0010} + {1010 + 0100} + {0110 + 1000}}

1111 = {{1110 + 0001} + {1101 + 0010} + {1011 + 0100} + {0111 + 1000}}

re ordered as it will be indexed:

0001 = ...
0010 = ...
0011 = {{0010 + 0001} + {0001 + 0010}}
0100 = ...
0101 = {{0100 + 0001} + {0001 + 0100}}
0110 = {{0100 + 0010} + {0010 + 0100}}
0111 = {{0110 + 0001} + {0101 + 0010} + {0011 + 0100}}
1000 = ...
1001 = {{1000 + 0001} + {0001 + 1000}}
1010 = {{1000 + 0010} + {0010 + 1000}}
1011 = {{1010 + 0001} + {1001 + 0010} + {0011 + 1000}}
1100 = {{1000 + 0100} + {0100 + 1000}}
1101 = {{1100 + 0001} + {1001 + 0100} + {0101 + 1000}}
1110 = {{1100 + 0010} + {1010 + 0100} + {0110 + 1000}}
1111 = {{1110 + 0001} + {1101 + 0010} + {1011 + 0100} + {0111 + 1000}}

there are 2^4 - 1 = 15 unique combinations for 4 items
this algorithm only works with <= 31 items
this is reasonable because if we try as many 1x1 items as there are cells in a cart 6 * 4 = 24 we would be under 31
meaning we would need to have at least 7 duplicates of any 1x1 item to reach the limit

*/

inline void try_adding_cart(Cart& cart, int index) {
	for (const Cart& existing_cart : all_carts[index]) {
		if (cart.canonical_form == existing_cart.canonical_form) {
			return;
		}
	}
	cart.compress_attributes();
	all_carts[index].push_back(cart);
}

inline unsigned int available_items_to_index(const vector<int>& available_items) {
	unsigned int index = 0;
	for (size_t i = 0; i < available_items.size(); ++i) {
		index |= (1U << available_items[i]);
	}
	return index - 1;
}

// profile +
void generate_all_carts(const vector<int>& available_items) {
	if (available_items.size() == 1) {
		// base case
		int item_index = available_items[0];
		unsigned int index = one_item_carts_index[item_index];
		const Item& item = *all_items[item_index];
		for (int pos : item.possible_positions) {
			Cart cart;
			cart.add_item(item, pos);
			cart.set_canonical_form();
			cart.compress_attributes();
			all_carts[index].push_back(cart);
		}
		return;
	}
	unsigned int index = available_items_to_index(available_items);
	for (size_t i = 0; i < available_items.size(); i++) {
		int removed_item_index = available_items[i];
		auto one_less_available_items = available_items;
		one_less_available_items.erase(one_less_available_items.begin() + i);
		unsigned int one_less_index = index - (1U << removed_item_index);
		if (all_carts[one_less_index].empty()) {
			generate_all_carts(one_less_available_items);
		}
		for (const Cart& cart : all_carts[one_less_index]) {
			for (const Cart& one_item_cart : all_carts[one_item_carts_index[removed_item_index]]) {
				if (cart.cells_as_number & one_item_cart.cells_as_number) { continue; }
				// merge cart with one_item_cart
				Cart merged;
				for (size_t j = 0; j < cart.items.size(); j++) {
					merged.add_item(*all_items[cart.items[j]], cart.items_coords[j]);
				}
				merged.add_item(*all_items[removed_item_index], one_item_cart.items_coords[0]);
				merged.set_canonical_form();
				try_adding_cart(merged, index);
			}
		}
	}
}

// profile function+
void compute_best_carts() {
	vector<int> available_items;
	for (int i = 0; i < all_items.size(); ++i) {
		available_items.push_back(i);
	}
	// cout << available_items << endl;
	generate_all_carts(available_items);
	vector<Cart>& carts = all_carts[all_carts_length - 1];

	// profile line   + 
	int max_value = 0;
	for (auto& cart : carts) {
		if (cart.set_value() > max_value) {
			max_value = cart.value;
		}
	}

	carts.erase(remove_if(carts.begin(), carts.end(),[max_value](const auto& cart) {return cart.value != max_value;}),carts.end());
}

// Algorithm
// -------------------

void test(const vector<int>& available_items) {
	cout << available_items_to_index(available_items) << " -> " << available_items << endl;
}

int main() {
	/*
	for (int i = -1; i <= 10; i++) {
		std::cout << setw(2) << setfill(' ') << i << ": " << bitset<8>(i) << " -> " << std::bitset<8>((i & ~(i >> 31)) << 1) << std::endl;
	}
	return 0;
	
	test({ 0 });
	test({ 1 });
	test({ 0, 1 });
	test({ 2 });
	test({ 0, 2 });
	test({ 1, 2 });
	test({ 0, 1, 2 });
	test({ 3 });
	test({ 0, 3 });
	test({ 1, 3 });
	test({ 0, 1, 3 });
	test({ 2, 3 });
	test({ 0, 2, 3 });
	test({ 1, 2, 3 });
	test({ 0, 1, 2, 3 });
	return 0;
	*/
	// init
	Item::create<AncientHolyGrail>(ANTIQUE, RARE_GOOD, 180, { 1, 1 }, 1);
	Item::create<AncientHolyGrail>(ANTIQUE, RARE_GOOD, 180, { 1, 1 }, 1);
	Item::create<AncientHolyGrail>(ANTIQUE, RARE_GOOD, 180, { 1, 1 }, 1);
	Item::create<AncientHolyGrail>(ANTIQUE, RARE_GOOD, 180, { 1, 1 }, 1);
	// Item::create<AncientHolyGrail>(ANTIQUE, RARE_GOOD, 180, { 1, 1 }, 1);
	// Item::create<AncientHolyGrail>(ANTIQUE, RARE_GOOD, 180, { 1, 1 }, 1);
	// Item::create<AncientHolyGrail>(ANTIQUE, RARE_GOOD, 180, { 1, 1 }, 1);

	if (all_items_length < 1 || all_items_length > 31) {
		cout << "all_items_length must be between 1 and 31" << endl;
		exit(1);
	}

	all_carts_length = (1U << all_items_length) - 1;

	all_carts.resize(all_carts_length);
	// cout << "all_carts.size() = " << all_carts.size() << endl;
	// cout << "all_carts.capacity() = " << all_carts.capacity() << endl;
	
	for (unsigned i = 0; i < all_carts_length; i++) {
		// worst case is when n items are of shape 1x1
		// meaning the number of possible carts is factorial
		// 
		// nb possible carts =
		// cart_size! / (cart_size - n)!		if 0 <= n < cart_size
		// cart_size!							if n = cart_size
		// cart_size! * (n choose cart_size)	if n > cart_size
		// 
		// we do this to help push back
		unsigned n = count_ones(i);
		constexpr unsigned cart_size_fact = factorial(cart_size);
		all_carts[i].resize(n == cart_size ? cart_size_fact :
			n > cart_size ? cart_size_fact * nChooseK(n, cart_size) :
			cart_size_fact / factorial(cart_size - n));
	}
	
	one_item_carts_index.reserve(all_items_length);
	auto* buffer = one_item_carts_index.data();
	for (int i = 0; i < all_items_length; i++) {
		buffer[i] = available_items_to_index({ i });
	}
	one_item_carts_index.resize(all_items_length);
	compute_best_carts();
	cout << "done" << endl;
	/*
	for (const auto& cart : all_carts[all_carts_length - 1]) {
		cout << cart.to_string() << endl;
	}
	*/
	// REP_LINE(378)
	// REP_LINE(397)
	// REP_FUNC(generate_all_carts)
}
