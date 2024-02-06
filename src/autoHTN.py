import pyhop
import json

def check_enough (state, ID, item, num):
	if getattr(state,item)[ID] >= num: return []
	return False

def produce_enough (state, ID, item, num):
	return [('produce', ID, item), ('have_enough', ID, item, num)]

pyhop.declare_methods ('have_enough', check_enough, produce_enough)

def produce (state, ID, item):
	return [('produce_{}'.format(item), ID)]

pyhop.declare_methods ('produce', produce)

def make_method (name, rule):
	def method (state, ID):
		order = ['bench', 'furnace', 'ingot', 'ore', 'coal', 'cobble', 'stick', 'plank', 'wood', 'iron_axe', 'stone_axe', 'wooden_axe',
				'iron_pickaxe', 'wooden_pickaxe', 'stone_pickaxe']
		needs = rule.get('Requires', {}) | rule.get('Consumes', {})
		m = []
		items = sorted(needs.items(), key=lambda x: order.index(x[0]))
		for item, amount in items:
			m.append(('have_enough', ID, item, amount))
		m.append((("op_" + name).replace(' ', '_'), ID))
		return m
	return method

def declare_methods (data):
	# some recipes are faster than others for the same product even though they might require extra tools
	# sort the recipes so that faster recipes go first

	# your code here
	# hint: call make_method, then declare the method to pyhop using pyhop.declare_methods('foo', m1, m2, ..., mk)
	methods = {}
	for r, info in data['Recipes'].items():
		cur_time = info['Time']
		m = make_method(r, info)
		m.__name__ = r.replace(' ', '_')
		cur_m = ("produce_" + list(info['Produces'].keys())[0]).replace(' ', '_')
		if cur_m not in methods:
			methods[cur_m] = [(m, cur_time)]
		else:
			methods[cur_m].append((m, cur_time))
	for m, info in methods.items():
		methods[m] = sorted(info, key=lambda x: x[1])
		pyhop.declare_methods(m, *[method[0] for method in methods[m]])
	

def make_operator (rule):
	def operator (state, ID):
		if state.time[ID] >= rule['Time']:
			if 'Requires' in rule:
				for item, amount in rule['Requires'].items():
					cur_val = getattr(state, item)
					if cur_val[ID] < amount:
						return False
			if 'Consumes' in rule:
				for item, amount in rule['Consumes'].items():
					cur_val = getattr(state, item)
					if cur_val[ID] < amount:
						return False
				for item, amount in rule['Consumes'].items():
					setattr(state, item, {ID: cur_val[ID] - amount})
			state.time[ID] -= rule['Time']
			for item, amount in rule['Produces'].items():
				cur_val = getattr(state, item)
				setattr(state, item, {ID: cur_val[ID] + amount})
			return state
		return False
	return operator

def declare_operators (data):
	# your code here
	# hint: call make_operator, then declare the operator to pyhop using pyhop.declare_operators(o1, o2, ..., ok)
	ops = []
	for r, info in data['Recipes'].items():
		op = make_operator(info)
		op.__name__ = ("op_" + r).replace(' ', '_')
		ops.append(op)
	pyhop.declare_operators(*ops)

def add_heuristic (data, ID):
	def start_heuristic(state, curr_task, tasks, plan, depth, calling_stack):
		if len(tasks) <= 2:
			return False

	def time_heuristic(state, curr_task, tasks, plan, depth, calling_stack):
		# Prune the branch if the time taken exceeds a certain threshold
		if state.time[ID] <= 0:
			return True

	def depth_heuristic(state, curr_task, tasks, plan, depth, calling_stack):
		if depth > 500:
			return True

	def tool_dupe_heuristic(state, curr_task, tasks, plan, depth, calling_stack):
		if curr_task[0] == 'produce' and curr_task[2] in data['Tools']:
			# check state if current tool already made
			if getattr(state, curr_task[2])[ID] > 0:
				return True

	def wood_hueristic(state, curr_task, tasks, plan, depth, calling_stack):
		wood = sum([task[3] for task in tasks if task[0] == 'have_enough' and task[2] == 'wood'])
		if curr_task[0] in ['produce_wooden_axe'] and wood < 5 and 'wooden_axe' not in data['Goal']:
			return True
		elif curr_task[0] in ['produce_stone_axe'] and wood < 10 and 'rail' not in data['Goal'] and 'stone_axe' not in data['Goal']:
			return True

	def mine_heuristic(state, curr_task, tasks, plan, depth, calling_stack):
		mined_actions_cobble = ['op_{}_for_cobble'.format(x) for x in ['wooden_pickaxe', 'stone_pickaxe', 'iron_pickaxe']]
		mined_actions_ore = ['op_{}_for_ore'.format(x) for x in ['wooden_pickaxe', 'stone_pickaxe', 'iron_pickaxe']]
		mined_actions_coal = ['op_{}_for_coal'.format(x) for x in ['wooden_pickaxe', 'stone_pickaxe', 'iron_pickaxe']]
		mined_actions = mined_actions_cobble + mined_actions_ore + mined_actions_coal

		total_mine = 0
		total_ores = 0
		total_coals = 0
		# get total mined resources
		for action in plan:
			if action[0] in mined_actions:
				total_mine += 1
			if action[0] in mined_actions_ore:
				total_ores += 1
			if action[0] in mined_actions_coal:
				total_coals += 1

		total_mined = sum([task[3] for task in tasks if len(task) > 3 and task[2] in ['cobble', 'coal', 'ore']])
		total_ore = sum([task[3] for task in tasks if len(task) > 3 and task[2] == 'ore'])

		if curr_task[0] in ['produce_stone_pickaxe'] and (total_mined < 5 and total_ore == 0) and 'stone_pickaxe' not in data['Goal']:
			return True
		if curr_task[0] in ['produce_iron_pickaxe'] and total_mined != 2 and 'iron_pickaxe' not in data['Goal']:
			return True
		
	def iron_axe_heuristic(state, curr_task, tasks, plan, depth, calling_stack):
		if curr_task == ('have_enough', ID, 'iron_axe', 1):	
			if curr_task[2] in ['iron_axe'] and curr_task != tasks[len(tasks)-1] and 'iron_axe' not in data['Goal']: 
				return True
		
	def cyclical_heuristic(state, curr_task, tasks, plan, depth, calling_stack):
		min_tools = [('have_enough', ID, item, 1) for item in data['Tools']]
		if curr_task in min_tools:	
			if tasks.count(curr_task) > 1:
				return True
	
	def end_heuristic(state, curr_task, tasks, plan, depth, calling_stack):
		return False

	def resource_avalible_heuristic(state, curr_task, tasks, plan, depth, calling_stack):
		if curr_task[0] == 'produce':
			item = curr_task[2]
			if item not in data['Goal'] and item in data["Items"]:
				if item == 'ore' or item == 'coal' or item == 'wood':
					if getattr(state, item)[ID] > 1:
						return True
				elif item == 'plank':
					if(getattr(state, item)[ID] > 4):
						return True
				elif item == 'stick':
					if(getattr(state, item)[ID] > 2):
						return True
				elif item == 'cobble':
					if getattr(state, item)[ID] > 8:
						return True
				elif item == 'ingot':
					if getattr(state, item)[ID] > 6:
						return True
		
	pyhop.add_check(start_heuristic)
	pyhop.add_check(iron_axe_heuristic)
	pyhop.add_check(cyclical_heuristic)
	# pyhop.add_check(time_heuristic)
	# pyhop.add_check(depth_heuristic)
	pyhop.add_check(tool_dupe_heuristic)
	pyhop.add_check(wood_hueristic)
	pyhop.add_check(mine_heuristic)
	# pyhop.add_check(resource_avalible_heuristic)
	pyhop.add_check(end_heuristic)


def set_up_state (data, ID, time=0):
	state = pyhop.State('state')
	state.time = {ID: time}

	for item in data['Items']:
		setattr(state, item, {ID: 0})

	for item in data['Tools']:
		setattr(state, item, {ID: 0})

	for item, num in data['Initial'].items():
		setattr(state, item, {ID: num})

	return state

def set_up_goals (data, ID):
	goals = []
	for item, num in data['Goal'].items():
		goals.append(('have_enough', ID, item, num))

	return goals

if __name__ == '__main__':
	rules_filename = 'crafting.json'

	with open(rules_filename) as f:
		data = json.load(f)

	state = set_up_state(data, 'agent', time=250) # allot time here
	goals = set_up_goals(data, 'agent')

	declare_operators(data)
	declare_methods(data)
	add_heuristic(data, 'agent')

	pyhop.print_operators()
	pyhop.print_methods()

	# Hint: verbose output can take a long time even if the solution is correct; 
	# try verbose=1 if it is taking too long
	pyhop.pyhop(state, goals, verbose=1)
	# pyhop.pyhop(state, [('have_enough', 'agent', 'cart', 1),('have_enough', 'agent', 'rail', 20)], verbose=1)
