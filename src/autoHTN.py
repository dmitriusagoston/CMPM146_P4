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
		m = []
		if 'Requires' in rule:
			for item, amount in rule['Requires'].items():
				m.append(('have_enough', ID, item, amount))
		if 'Consumes' in rule:
			for item, amount in rule['Consumes'].items():
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
	for r, info in data['Recipes'].items():
		op = make_operator(info)
		op.__name__ = ("op_" + r).replace(' ', '_')
		pyhop.declare_operators(op)

def add_heuristic (data, ID):
	# prune search branch if heuristic() returns True
	# do not change parameters to heuristic(), but can add more heuristic functions with the same parameters: 
	# e.g. def heuristic2(...); pyhop.add_check(heuristic2)

	def heuristic(state, curr_task, tasks, plan, depth, calling_stack):
		if curr_task[0] == 'produce':
			item = curr_task[-1]
			for recipe, info in data['Recipes'].items():
				if item in info['Produces']:
					if 'Requires' in info:
						required_items = info['Requires']
						if all(getattr(state, required_item)[ID] >= amount for required_item, amount in required_items.items()):
							return True
		return False
	def depth_heuristic(state, curr_task, tasks, plan, depth, calling_stack):
		if depth > 50:
			return True
		return False

	def cost_heuristic(state, curr_task, tasks, plan, depth, calling_stack):
		# Estimate the cost based on the number of tasks remaining
		cost = len(tasks)

		# Increase the cost if the current task requires a resource that is not available
		if curr_task[0] == 'produce' and getattr(state, curr_task[2])[ID] == 0:
			cost += 1

		# Prune the branch if the cost exceeds a certain threshold
		return cost > 15
	#pyhop.add_check(heuristic)
	pyhop.add_check(depth_heuristic)
	pyhop.add_check(cost_heuristic)


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

	state = set_up_state(data, 'agent', time=300) # allot time here
	goals = set_up_goals(data, 'agent')

	declare_operators(data)
	declare_methods(data)
	add_heuristic(data, 'agent')

	# pyhop.print_operators()
	# pyhop.print_methods()

	# Hint: verbose output can take a long time even if the solution is correct; 
	# try verbose=1 if it is taking too long
	pyhop.pyhop(state, goals, verbose=3)
	# pyhop.pyhop(state, [('have_enough', 'agent', 'cart', 1),('have_enough', 'agent', 'rail', 20)], verbose=1)
