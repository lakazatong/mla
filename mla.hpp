#pragma once

#include <vector>
#include <set>

using namespace std;

class Cart;

class Item {
public:
	int category, rarity, base_value, value, width, height, id;
	vector<int> shape;
	vector<int> possible_positions;
	vector<int> adjacent_items;
	int size;
	int item_type;

	Item(int category, int rarity, int value, const vector<int>& shape, int width);

	void set_adjacent_items(const vector<int>& cells, int k);

	template<typename T>
	static void create(int category, int rarity, int value, const vector<int>& shape, int width);

	virtual void apply_effect(Cart& cart) = 0;

	friend std::ostream& operator<<(std::ostream& os, const Item& item);
};

class Cart {
public:
	int value;
	vector<int> cells;
	vector<int> items;
	vector<int> items_coords;
	set<int> items_set;
	uint32_t cells_as_number;
	vector<int> canonical_form;

	Cart();

	bool full() const;
	void add_item(const Item& item, int k);
	int set_value();
	void compress_attributes();
	void set_canonical_form();
	string to_string() const;
};
