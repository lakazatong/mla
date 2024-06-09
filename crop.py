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
padding = 3

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
			x, y, width, height = coords[i, j, :]
			
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
				items_shape.append([[1]])
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
		items_shape.append(vital_goods_shape[min_i:max_i+1,min_j:max_j+1])
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

	def explore_item(i, j, k, tmp, item_shape):
		# mark this cart space as seen as well as putting a unique id
		cart_space[i, j] = k
		item_shape[i, j] = 1
		tmp[0] = min(tmp[0], i)
		tmp[1] = max(tmp[1], i)
		tmp[2] = min(tmp[2], j)
		tmp[3] = max(tmp[3], j)
		
		top, bot, left, right = item_span_directions(cart_cells_array[i][j], i, j)

		if top and cart_space[i-1, j] == 0: explore_item(i-1, j, k, tmp, item_shape)
		if bot and cart_space[i+1, j] == 0: explore_item(i+1, j, k, tmp, item_shape)
		if left and cart_space[i, j-1] == 0: explore_item(i, j-1, k, tmp, item_shape)
		if right and cart_space[i, j+1] == 0: explore_item(i, j+1, k, tmp, item_shape)

	for i in range(cart_height):
		for j in range(cart_width):
			# already explored (attribute stone / vital goods / item) or empty
			if cart_space[i, j] != 0 or is_empty(i, j): continue
			tmp = [cart_height, -1, cart_width, -1]
			item_shape = np.full((cart_height, cart_width), 0)
			explore_item(i, j, k, tmp, item_shape)
			items_shape.append(item_shape[tmp[0]:tmp[1]+1,tmp[2]:tmp[3]+1])
			k += 1

	return items_shape, cart_space

coords = np.array([
	(508, 263, 112, 111),
	(623, 263, 111, 111),
	(737, 263, 111, 111),
	(851, 263, 111, 111),
	(965, 263, 111, 111),
	(1079, 263, 111, 111),
	(1193, 263, 112, 111),

	(508, 377, 112, 111),
	(623, 377, 111, 111),
	(737, 377, 111, 111),
	(851, 377, 111, 111),
	(965, 377, 111, 111),
	(1079, 377, 111, 111),
	(1193, 377, 112, 111),

	(508, 491, 112, 111),
	(623, 491, 111, 111),
	(737, 491, 111, 111),
	(851, 491, 111, 111),
	(965, 491, 111, 111),
	(1079, 491, 111, 111),
	(1193, 491, 112, 111),
	
	(508, 605, 112, 112),
	(623, 605, 111, 112),
	(737, 605, 111, 112),
	(851, 605, 111, 112),
	(965, 605, 111, 112),
	(1079, 605, 111, 112),
	(1193, 605, 112, 112),
	
	(508, 720, 112, 111),
	(623, 720, 111, 111),
	(737, 720, 111, 111),
	(851, 720, 111, 111),
	(965, 720, 111, 111),
	(1079, 720, 111, 111),
	(1193, 720, 112, 111)
]).reshape(cart_height, cart_width, 4)


def main():
	cart_img_path = "emotes/ss/1.png"
	cart_cells_img, cart_cells_array = cut_cart(cart_img_path, coords)
	items_shape, cart_space = scan_cart(cart_cells_array)

	# number of items found
	n = len(items_shape)
	for item_shape in items_shape:
		print(item_shape, end="\n\n")
	print(cart_space)

	save_path = "emotes/ss/1-cropped/"
	os.makedirs(save_path, exist_ok=True)
	clear_folder(save_path)
	for i in range(cart_height):
		for j in range(cart_width):
			cart_cells_img[i][j].save(f"emotes/ss/1-cropped/{i}-{j}.png")

if __name__ == "__main__":
	main()