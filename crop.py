import os, math, time
from PIL import Image
import numpy as np
from colorsys import rgb_to_hsv as rgb_to_hsv_colorsys
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.widgets import Slider

def save_single_color_image(color, size, save_path):
	image = Image.new("RGB", size, color)
	image.save(save_path)

def save_float_array_as_image(array, output_path):
	scaled_array = (array * 255).astype(np.uint8)
	img = Image.fromarray(scaled_array)
	img.save(output_path)

def rgb_distance_to_hsv(color, hsv_target_color):
	h0, s0, v0 = rgb_to_hsv_colorsys(*color)
	# h, s, v = h*360, s*100, v/255*100
	h0 = round(h0 * 360)
	s0 = round(s0 * 100)
	h1, s1, v1 = hsv_target_color
	dh = min(abs(h1-h0), 360-abs(h1-h0)) / 180.0
	ds = abs(s1-s0) / 100
	dv = abs(v1-v0) / 255.0
	h_weight = 1
	s_weight = 1
	v_weight = 1
	total_weight = h_weight + s_weight + v_weight
	return max(0, min(1, math.sqrt(dh*dh*h_weight/total_weight+ds*ds*s_weight/total_weight+dv*dv*v_weight/total_weight) / math.sqrt(3)))

def image_to_distances_hsv(img, hsv_target_color):
	# hsv_target_color ranges:
	# hue in [0, 360]
	# saturation in [0, 100]
	# value in [0, 255]
	return np.apply_along_axis(lambda color: rgb_distance_to_hsv(color, hsv_target_color), -1, np.array(img))

def rgb_distance_to_rgb(color, rgb_target_color):
	r0, g0, b0 = color
	r1, g1, b1 = rgb_target_color
	dr = abs(r1-r0) / 255
	dg = abs(g1-g0) / 255
	db = abs(b1-b0) / 255
	return max(0, min(1, math.sqrt(dr*dr+dg*dg+db*db) / math.sqrt(3)))

def image_to_distances_rgb(img_array, rgb_target_color):
	# rgb_target_color ranges:
	# hue in [0, 255]
	# saturation in [0, 255]
	# value in [0, 255]
	return np.sqrt(np.sum(np.square(np.abs(img_array - np.full(img_array.shape, rgb_target_color)) / 255), axis=2)) / math.sqrt(3)
	# return np.sqrt(np.sum(np.square(np.abs(img_array - np.full(img_array.shape, rgb_target_color))), axis=2))

def compute_optimal_target_color(img_array):
	optimal_r = 0
	min_distance_sum = float('inf')
	for r in range(256):
		distances = image_to_distances_rgb(img_array, (r, 0, 0))
		distance_sum = np.sum(distances)
		if distance_sum < min_distance_sum:
			min_distance_sum = distance_sum
			optimal_r = r

	optimal_g = 0
	min_distance_sum = float('inf')
	for g in range(256):
		distances = image_to_distances_rgb(img_array, (optimal_r, g, 0))
		distance_sum = np.sum(distances)
		if distance_sum < min_distance_sum:
			min_distance_sum = distance_sum
			optimal_g = g

	optimal_b = 0
	min_distance_sum = float('inf')
	for b in range(256):
		distances = image_to_distances_rgb(img_array, (optimal_r, optimal_g, b))
		distance_sum = np.sum(distances)
		if distance_sum < min_distance_sum:
			min_distance_sum = distance_sum
			optimal_b = b

	return (optimal_r, optimal_g, optimal_b)

def compute_optimal_target_color_multithreaded(image):
	def process_range(start, end):
		min_distance_sum = np.inf
		optimal_hsv = np.zeros(3)
		for r in range(start, end):
			for g in range(256):
				for b in range(256):
					rgb_target_color = (r, g, b)
					distances = image_to_distances_rgb(image, rgb_target_color)
					distance_sum = np.sum(distances)
					if distance_sum < min_distance_sum:
						min_distance_sum = distance_sum
						optimal_hsv = rgb_target_color
		return min_distance_sum, optimal_hsv

	ranges = [(0, 64), (64, 128), (128, 192), (192, 256)]
	results = []
	with ThreadPoolExecutor() as executor:
		for start, end in ranges:
			results.append(executor.submit(process_range, start, end))

	min_distance_sum, optimal_hsv = min((result.result() for result in results), key=lambda x: x[0])
	return optimal_hsv

def proportion_of_color_hsv(img_array, hsv_target_color, threshold=0.1):
	distances = image_to_distances_hsv(img_array, hsv_target_color)
	# save_float_array_as_image(distances, "emotes/ss/1-cropped/test.png")
	return np.count_nonzero(distances <= threshold) / distances.size

def proportion_of_color_rgb(img_array, rgb_target_color, threshold=0.1):
	distances = image_to_distances_rgb(img_array, rgb_target_color)
	# save_float_array_as_image(distances, "emotes/ss/1-cropped/test.png")
	return np.count_nonzero(distances <= threshold) / distances.size

cart_width = 7
cart_height = 5
padding = 4

def clear_folder(path):
	for file in os.listdir(path):
		file_path = os.path.join(path, file)
		if os.path.isfile(file_path):
			os.unlink(file_path)

def get_average_color(image):
	np_image = np.array(image)
	w, h, d = np_image.shape
	return tuple(np_image.reshape(w * h, d).mean(axis=0).astype(int))

def cut_cart(image_path, coords):
	image = Image.open(image_path)
	# crop the image in cart cells
	cart_cells_img = [[None for _ in range(cart_width)] for _ in range(cart_height)]
	cart_cells_array = [[None for _ in range(cart_width)] for _ in range(cart_height)]
	for i in range(cart_height):
		for j in range(cart_width):
			y, x, height, width = coords[i, j, :]
			
			x -= padding
			y -= padding
			width += padding * 2
			height += padding * 2
			
			cropped_image = image.crop((x, y, x + width, y + height))
			cart_cells_img[i][j] = cropped_image
			cart_cells_array[i][j] = np.array(cropped_image)
	return cart_cells_img, cart_cells_array

def scan_cart(cart_cells_array):
	cart_background_color = (49, 36, 24)
	empty_color = (33, 24, 16)
	attribute_stone_color = (165, 81, 165)
	vital_goods_color = (82, 166, 165)
	
	cart_space = np.full((cart_height, cart_width), 0)
	items_shape = []

	def is_attribute_stone(i, j):
		img_array = cart_cells_array[i][j]
		height, width = img_array.shape[:1+1]
		horizontal_length, vertical_length = width - padding * 2, height - padding * 2
		# top = proportion_of_color_rgb(img_array[padding,padding:width-padding,:].reshape(1, horizontal_length, 3), attribute_stone_color)
		# bot = proportion_of_color_rgb(img_array[height-padding-1,padding:width-padding,:].reshape(1, horizontal_length, 3), attribute_stone_color)
		# left = proportion_of_color_rgb(img_array[padding:height-padding,padding,:].reshape(1, vertical_length, 3),  attribute_stone_color)
		# right = proportion_of_color_rgb(img_array[padding:height-padding,width-padding-1,:].reshape(1, vertical_length, 3), attribute_stone_color)
		# print(top, bot, left, right)
		return (
				proportion_of_color_rgb(img_array[padding,padding:width-padding,:].reshape(1, horizontal_length, 3), attribute_stone_color) >= 0.5
			and proportion_of_color_rgb(img_array[height-padding-1,padding:width-padding,:].reshape(1, horizontal_length, 3), attribute_stone_color) >= 0.5
			and proportion_of_color_rgb(img_array[padding:height-padding,padding,:].reshape(1, vertical_length, 3),  attribute_stone_color) >= 0.5
			and proportion_of_color_rgb(img_array[padding:height-padding,width-padding-1,:].reshape(1, vertical_length, 3), attribute_stone_color) >= 0.5
		)

	k = 1

	# first find the Attribute Stone because it spills on the edges, making item_span_directions return a false positive
	for i in range(cart_height):
		for j in range(cart_width):
			if is_attribute_stone(i, j):
				items_shape.append(([[1]], i, j))
				cart_space[i, j] = k
				k += 1
				break

	if k == 1:
		print("no Attribute stone? sus")
		exit(1)
	
	def is_vital_good(i, j):
		img_array = cart_cells_array[i][j]
		height, width = img_array.shape[:1+1]
		horizontal_length, vertical_length = width - padding * 2, height - padding * 2
		return (
				proportion_of_color_rgb(img_array[padding,padding:width-padding,:].reshape(1, horizontal_length, 3), vital_goods_color) >= 0.5
			and proportion_of_color_rgb(img_array[height-padding-1,padding:width-padding,:].reshape(1, horizontal_length, 3), vital_goods_color) >= 0.5
			and proportion_of_color_rgb(img_array[padding:height-padding,padding,:].reshape(1, vertical_length, 3),  vital_goods_color) >= 0.5
			and proportion_of_color_rgb(img_array[padding:height-padding,width-padding-1,:].reshape(1, vertical_length, 3), vital_goods_color) >= 0.5
		)

	found_vital_goods = False
	min_i, max_i, min_j, max_j = cart_height, -1, cart_width, -1
	vital_goods_shape = np.full((cart_height, cart_width), 0)
	# then find vital goods if there are because they don't spill but should be connected, making item_span_directions return false negative
	for i in range(cart_height):
		for j in range(cart_width):
			if is_vital_good(i, j):
				# print(f"vital goods at {i}, {j}")
				cart_space[i, j] = k
				vital_goods_shape[i,j] = 1
				
				found_vital_goods = True
				min_i = min(min_i, i)
				max_i = max(max_i, i)
				min_j = min(min_j, j)
				max_j = max(max_j, j)

	if found_vital_goods:
		items_shape.append((vital_goods_shape[min_i:max_i+1,min_j:max_j+1], min_i, min_j))
		k += 1

	def is_empty(i, j):
		img_array = cart_cells_array[i][j]
		height, width = img_array.shape[:1+1]
		horizontal_length, vertical_length = width - padding * 2, height - padding * 2
		return (
				proportion_of_color_rgb(img_array[padding,padding:width-padding,:].reshape(1, horizontal_length, 3), empty_color) >= 0.5
			and proportion_of_color_rgb(img_array[height-padding-1,padding:width-padding,:].reshape(1, horizontal_length, 3), empty_color) >= 0.5
			and proportion_of_color_rgb(img_array[padding:height-padding,padding,:].reshape(1, vertical_length, 3),  empty_color) >= 0.5
			and proportion_of_color_rgb(img_array[padding:height-padding,width-padding-1,:].reshape(1, vertical_length, 3), empty_color) >= 0.5
		)

	def item_span_directions(cropped_image_array, i, j):
		height, width = cropped_image_array.shape[:1+1]
		top, bot, left, right = False, False, False, False
		if i > 0:
			line = cropped_image_array[1,:,:].reshape(1, width, 3)
			top = proportion_of_color_rgb(line, cart_background_color) <= 0.96
		if i < cart_height - 1:
			line = cropped_image_array[height - 2,:,:].reshape(1, width, 3)
			bot = proportion_of_color_rgb(line, cart_background_color) <= 0.96
		if j > 0:
			line = cropped_image_array[:,1,:].reshape(1, height, 3)
			left = proportion_of_color_rgb(line, cart_background_color) <= 0.96
		if j < cart_width - 1:
			line = cropped_image_array[:,width - 2,:].reshape(1, height, 3)
			right = proportion_of_color_rgb(line, cart_background_color) <= 0.96
		return top, bot, left, right

	def explore_item(i, j, k, mins, item_shape):
		# mark this cart space as seen as well as putting a unique id
		cart_space[i, j] = k
		item_shape[i, j] = 1
		mins[0] = min(mins[0], i)
		mins[1] = max(mins[1], i)
		mins[2] = min(mins[2], j)
		mins[3] = max(mins[3], j)
		
		top, bot, left, right = item_span_directions(cart_cells_array[i][j], i, j)

		if top and cart_space[i-1, j] == 0: explore_item(i-1, j, k, mins, item_shape)
		if bot and cart_space[i+1, j] == 0: explore_item(i+1, j, k, mins, item_shape)
		if left and cart_space[i, j-1] == 0: explore_item(i, j-1, k, mins, item_shape)
		if right and cart_space[i, j+1] == 0: explore_item(i, j+1, k, mins, item_shape)

	for i in range(cart_height):
		for j in range(cart_width):
			# already explored (attribute stone / vital goods / item) or empty
			if cart_space[i, j] != 0 or is_empty(i, j): continue
			mins = [cart_height, -1, cart_width, -1]
			item_shape = np.full((cart_height, cart_width), 0)
			explore_item(i, j, k, mins, item_shape)
			items_shape.append((item_shape[mins[0]:mins[1]+1,mins[2]:mins[3]+1], mins[0], mins[2]))
			k += 1

	return items_shape, cart_space

coords = np.array([
	(271, 692, 149, 149),
	(271, 845, 149, 148),
	(271, 997, 149, 148),
	(271, 1149, 149, 148),
	(271, 1301, 149, 149),
	(271, 1454, 149, 148),
	(271, 1606, 149, 148),

	(424, 692, 148, 149),
	(424, 845, 148, 148),
	(424, 997, 148, 148),
	(424, 1149, 148, 148),
	(424, 1301, 148, 149),
	(424, 1454, 148, 148),
	(424, 1606, 148, 148),

	(576, 692, 148, 149),
	(576, 845, 148, 148),
	(576, 997, 148, 148),
	(576, 1149, 148, 148),
	(576, 1301, 148, 149),
	(576, 1454, 148, 148),
	(576, 1606, 148, 148),
	
	(728, 692, 148, 149),
	(728, 845, 148, 148),
	(728, 997, 148, 148),
	(728, 1149, 148, 148),
	(728, 1301, 148, 149),
	(728, 1454, 148, 148),
	(728, 1606, 148, 148),
	
	(880, 692, 149, 149),
	(880, 845, 149, 148),
	(880, 997, 149, 148),
	(880, 1149, 149, 148),
	(880, 1301, 149, 149),
	(880, 1454, 149, 148),
	(880, 1606, 149, 148)
]).reshape(cart_height, cart_width, 4)

def main():
	folder_path = "emotes/ss"
	for file_path in os.listdir(folder_path):
		if not file_path.endswith('.png'): continue
		cart_img_path = os.path.join(folder_path, file_path)
		cart_cells_img, cart_cells_array = cut_cart(cart_img_path, coords)
		items_shape, cart_space = scan_cart(cart_cells_array)
		
		save_path = os.path.join(folder_path, f"{os.path.splitext(os.path.basename(file_path))[0]}-cropped").replace("\\", "/")
		os.makedirs(save_path, exist_ok=True)
		clear_folder(save_path)
		
		for k in range(len(items_shape)):
			item_shape, item_i, item_j = items_shape[k]
			item_top_left_cell_i, item_top_left_cell_j = coords[item_i,item_j,:2]
			item_height, item_width = len(item_shape), len(item_shape[0])
			# we subtract some padding because the in between margins are overlapping on the final merged image
			item_image_height = sum(cart_cells_array[item_i+i][item_j].shape[0] for i in range(item_height)) - padding * (item_height - 1)
			item_image_width = sum(cart_cells_array[item_i][item_j+j].shape[1] for j in range(item_width)) - padding * (item_width - 1)
			item_image = Image.new(mode="RGBA", size=(item_image_width, item_image_height), color = (0, 0, 0, 0))
			item_id = k + 1
			image_save_path = os.path.join(save_path, f"item{item_id}.png").replace("\\", "/")
			trimmed_image_save_path = os.path.join(save_path, f"item{item_id}-trimmed.png").replace("\\", "/")
			# use cart_space as a mask over cart_cells_img
			for i in range(cart_height):
				for j in range(cart_width):
					if cart_space[i,j] != item_id: continue
					cell_i, cell_j = coords[i,j,:2]
					top_left_i, top_left_j = cell_i - item_top_left_cell_i, cell_j - item_top_left_cell_j
					Image.Image.paste(item_image, cart_cells_img[i][j], (top_left_j, top_left_i))
			item_image.save(image_save_path)
			for i in range(cart_height):
				for j in range(cart_width):
					if cart_space[i,j] == item_id: continue
					cell_i, cell_j = coords[i,j,:2]
					top_left_i, top_left_j = cell_i - item_top_left_cell_i, cell_j - item_top_left_cell_j
					transparent_img = Image.new('RGBA', cart_cells_img[i][j].size, (0, 0, 0, 0))
					Image.Image.paste(item_image, transparent_img, (top_left_j, top_left_i))
			cropped_item_image = item_image.crop((padding, padding, item_image_width - padding, item_image_height - padding))
			cropped_item_image.save(trimmed_image_save_path)

if __name__ == "__main__":
	main()