import itertools, json, colorsys

# TODO: separer generate_carts et generate_carts_with_effect

# en supposont qu'on a une config d'item qui a une size <= taille du cart

# si < taille du cart:
# si aucun item a effet: renvoyer premiere config qui les fait tous rentrer
# sinon: renvoyer la config qui fait tout rentrer avec le + de bonus value

# si == taille du cart:
# si aucun item a effet: renvoyer premiere config qui est full
# sinon: renvoyer la config full avec le + de bonus value

# ( 797 - 6 * 3 ) / 7
# ( 568 - 4 * 3 ) / 5

def get_color(index, total):
	h = (index + 1) / (total + 1)
	s = 1
	v = 1
	return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(h, s, v))

class Cart:
	def __init__(self, config, items_index, items_position):
		# assumes given argument make up for a valid Cart (no overlap)
		if len(items_index) != len(items_position):
			raise ValueError("len(items_index) != len(items_position)")
		self.config = config
		self.items = config["items"]
		self.cart_width, self.cart_height = config["cart_width"], config["cart_height"]
		
		# if so the caller is responsible for assigning the following attributes
		# items_index, items_position, space
		# as well as calling set_value
		if len(items_index) == 0: return

		self.items_index = items_index
		
		self.items_position = items_position
		
		self.space = [[-1 for _ in range(self.cart_width)] for _ in range(self.cart_height)]
		for k in range(len(items_index)):
			item_index = items_index[k]
			i0, j0 = items_position[k]
			item = self.items[item_index]
			shape = item["shape"]
			for i in range(item["height"]):
				tmp = i0 + i
				for j in range(item["width"]):
					if shape[i][j] == 0: continue
					self.space[tmp][j0 + j] = item_index
		
		self.set_value()

	def full(self):
		for i in range(self.cart_height):
			for j in range(self.cart_width):
				if self.space[i][j] == -1:
					return False
		return True

	def is_valid(self, pos):
		y, x = pos
		return x >= 0 and x < self.cart_width and y >= 0 and y < self.cart_height

	def get_neighbours(self, pos):
		y, x = pos
		r = []
		left, right, top, down = (y, x-1), (y, x+1), (y-1, x), (y+1, x)
		if self.is_valid(left): r.append(left)
		if self.is_valid(right): r.append(right)
		if self.is_valid(top): r.append(top)
		if self.is_valid(down): r.append(down)
		return r

	def get_adjacent_items(self, item_index, item_position):
		item = self.items[item_index]
		shape = item["shape"]
		i0, j0 = item_position
		r = set()
		for i in range(item["height"]):
			tmp = i0 + i
			for j in range(item["width"]):
				if shape[i][j] == 0: continue
				neighbours = self.get_neighbours((j0 + j, tmp))
				for neighbour in neighbours:
					y, x = neighbour
					r.add(self.space[y][x])
		return list(r)

	def set_value(self):
		self.value = 0
		adjs = [self.get_adjacent_items(self.items_index[k], self.items_position[k]) for k in range(len(self.items_index))]
		self.added_value = 0
		# apply all effects
		for k in range(len(self.items_index)):
			item_index = self.items_index[k]
			# item_position = self.items_position[k]
			
			# all items with an effect
			# too lazy to have a class Item and have a class for all item and override an abstract "apply_effect" method
			# here effects are translated to effects to the cart value directly
			# tho we still apply all effects before adding their base value as we should
			match item_index:
				# Exorcism Ring i(Normal)
				case 2:
					for adj in adjs[k]:
						if self.items[adj].get("category", "") == "Antique":
							self.added_value += 20
				# Exorcism Ring (Rare)
				case 3:
					for adj in adjs[k]:
						if self.items[adj].get("category", "") == "Antique":
							self.added_value += 30
				# Gleaming Earrings (Normal)
				case 4:
					for adj in adjs[k]:
						if self.items[adj].get("rarity", "") == "Rare Goods":
							self.added_value += 20
				# Gleaming Earrings (Rare)
				case 5:
					for adj in adjs[k]:
						if self.items[adj].get("rarity", "") == "Rare Goods":
							self.added_value += 60
				# Ancient Holy Grail (Normal)
				case 6:
					for adj in adjs[k]:
						if self.items[adj]["name"] == "Attribute Stone":
							self.added_value += 100
				# Ancient Holy Grail (Rare)
				case 7:
					for adj in adjs[k]:
						if self.items[adj]["name"] == "Attribute Stone":
							self.added_value += 200
				# Radish (Normal)
				case 28:
					for adj in adjs[k]:
						if self.items[adj].get("category", "") == "Food":
							self.added_value += 30
				# Radish (Rare)
				case 29:
					for adj in adjs[k]:
						if self.items[adj].get("category", "") == "Food":
							self.added_value += 45
				# Demons Scythe (Normal)
				case 54:
					self.added_value += 300
				# Demons Scythe (Rare)
				case 55:
					self.added_value += 450
		self.value += sum(self.items[i]["value"] for i in self.items_index) + self.added_value
		self.is_full = self.full()
		if self.is_full:
			self.value += self.cart_width * self.cart_height * 20
		return self.value

	def __repr__(self):
		total_items = len(self.items)
		colored_space = "\n"
		for row in self.space:
			for cell in row:
				if cell == -1:
					colored_space += "\u2588\u2588\u2588"
				else:
					color = get_color(cell, total_items)
					colored_space += f"\033[38;2;{color[0]};{color[1]};{color[2]}m\u2588\u2588\u2588\033[0m"
			colored_space += "\n"
		return colored_space

class CartSolver:

	def __init__(self, config, available_items_index):
		self.config = config
		self.items = config["items"]
		self.available_items_index = available_items_index
		self.cart_width, self.cart_height = config["cart_width"], config["cart_height"]
		self.cart_size = self.cart_width * self.cart_height
		self.must_have_items_index = [i for i in available_items_index if "Non-discardable" in self.items[i].get("feature", "").split(",")]
		self.compute_items_sizes()
		self.compute_items_possible_positions()
		self.compute_interesting_carts()

	def compute_items_sizes(self):
		for item in self.items:
			shape = item["shape"]
			item["height"] = len(shape)
			item["width"] = len(shape[0])
			item["size"] = sum(sum(row) for row in shape)

	def compute_items_possible_positions(self):
		for item in self.items:
			item["possible_positions"] = [(i, j) for i in range(self.cart_height - item["height"] + 1) for j in range(self.cart_width - item["width"] + 1)]

	# @profile
	def try_put(self, item_index, position, space):
		item = self.items[item_index]
		shape = item["shape"]
		item_size = item["size"]
		checked = 0
		i0, j0 = position
		coords = []
		
		for i in range(item["height"]):
			tmpi = i0 + i
			for j in range(item["width"]):
				tmpj = j0 + j
				if space[tmpi][tmpj] != -1: return None
				if shape[i][j] == 1:
					coords.append((tmpi, tmpj))
					checked += 1
					if checked == item_size: break
		
		space_copy = [[space[i][j] for j in range(self.cart_width)] for i in range(self.cart_height)]
		for i, j in coords: space_copy[i][j] = item_index
		
		return space_copy

	# @profile
	def _best_cart_with_effects(self, i, indices, positions, space):
		if i == len(indices):
			cart = Cart(self.config, [], [])
			# shallow copies for now so that set_value can do its thing, will deepcopy if it turns out it's the best cart so far
			cart.items_index = indices
			cart.items_position = positions
			cart.space = space
			cart.set_value()
			return cart
		
		item_index = indices[i]
		item = self.items[item_index]
		
		best_cart = Cart(self.config, [], [])
		best_cart.value = -1
		for position in item["possible_positions"]:
			space_copy = self.try_put(item_index, position, space)
			if space_copy == None: continue
			
			positions[i] = position
			cart = self._best_cart_with_effects(i + 1, indices, positions, space_copy)
			
			if cart == None: continue
			
			if cart.value > best_cart.value:
				best_cart = cart
				# deep copies
				best_cart.items_index = [i for i in indices]
				best_cart.items_position = [pos for pos in positions]
				best_cart.space = [[space_copy[i][j] for j in range(self.cart_width)] for i in range(self.cart_height)]
		
		return None if best_cart.value == -1 else best_cart

	def best_cart_with_effects(self, indices):
		return self._best_cart_with_effects(0, indices, [(0, 0) for _ in indices], [[-1 for _ in range(self.cart_width)] for _ in range(self.cart_height)])

	# @profile
	def _find_cart(self, i, indices, positions, space):
		if i == len(indices):
			cart = Cart(self.config, [], [])
			# here we can straight up deep copy since the first cart found is guaranteed to be the best (no items with effect here)
			cart.items_index = [i for i in indices]
			cart.items_position = [pos for pos in positions]
			cart.space = [[space[i][j] for j in range(self.cart_width)] for i in range(self.cart_height)]
			cart.set_value()
			return cart
		
		item_index = indices[i]
		item = self.items[item_index]
		
		for position in item["possible_positions"]:
			space_copy = self.try_put(item_index, position, space)
			if space_copy == None: continue
			
			positions[i] = position
			cart = self._find_cart(i + 1, indices, positions, space_copy)
			
			if cart == None: continue
			
			return cart
		
		return None

	def find_cart(self, indices):
		return self._find_cart(0, indices, [(0, 0) for _ in indices], [[-1 for _ in range(self.cart_width)] for _ in range(self.cart_height)])

	# @profile
	def compute_interesting_carts(self):
		# will try all combinaisons of N items that have a possible cart plus the ones with one item less (just in case idk) and stop there
		self.all_interesting_carts = []
		depth = 2
		for n_items in range(len(self.available_items_index), 0, -1):
			found = False
			for indices in itertools.combinations(self.available_items_index, n_items):
				
				total_size = sum(self.items[i]["size"] for i in indices)
				if total_size > self.cart_size: continue

				if any(i not in indices for i in self.must_have_items_index): continue

				# sort by size to fill up the cart as fast as possible
				indices = sorted(list(indices), key=lambda i: -self.items[i]["size"])

				with_effects = any("effect" in self.items[i] and self.items[i]["name"] != "Attribute Stone" for i in indices)

				cart = self.best_cart_with_effects(indices) if with_effects else self.find_cart(indices)

				if cart == None: continue
				print(f"found new interesting cart with {indices = }")
				found = True
				self.all_interesting_carts.append(cart)
			
			if found:
				depth -= 1
				if depth == 0: break

	def _solve(self, min_base_price):
		best_cart = Cart(self.config, [], [])
		best_cart.value = -1
		for cart in self.all_interesting_carts:
			if cart.value >= min_base_price and cart.value > best_cart.value:
				best_cart = cart
		return best_cart

	def solve(self):
		for min_base_price in range(7000, -1, -10):
			print(f"trying with {min_base_price = }")
			r = self._solve(min_base_price)
			if r.value != -1:
				return r
		return None

def main():

	content = None

	with open("cart_config.json", "r") as f:
		content = f.read()

	config = json.loads(content)
	solver = CartSolver(config, [1, 2, 3, 4, 5])
	best_cart = solver.solve()

	print("\n" + "-" * 40 + "\n\nbest cart found:")
	print(best_cart)

if __name__ == '__main__':
	main()