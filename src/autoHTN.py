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
			# methods[cur_m] = sorted(methods[cur_m], key=lambda x: x.cur_time)
	for m, info in methods.items():
		methods[m] = sorted(info, key=lambda x: x[1])
		pyhop.declare_methods(m, *[method[0] for method in methods[m]])
	

def make_operator (rule):
	def operator (state, ID):
		if state.time[ID] >= rule['Time']:
			if 'Requires' in rule:
				for item, amount in rule['Requires'].items():
					if state[item][ID] < amount:
						return False
				for item, amount in rule['Requires'].items():
					state[item][ID] -= amount
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
	def heuristic (state, curr_task, tasks, plan, depth, calling_stack):
		
		if (curr_task[0] == 'produce_iron_axe' or curr_task[0] == 'produce_stone_axe' or curr_task[0] == 'produce_wooden_axe') and state.wood[ID] == 0:
			return True
		return False # if True, prune this branch

	pyhop.add_check(heuristic)


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

	state = set_up_state(data, 'agent', time=239) # allot time here
	goals = set_up_goals(data, 'agent')

	declare_operators(data)
	declare_methods(data)
	add_heuristic(data, 'agent')

	# pyhop.print_operators()
	# pyhop.print_methods()

	# Hint: verbose output can take a long time even if the solution is correct; 
	# try verbose=1 if it is taking too long
	pyhop.pyhop(state, goals, verbose=3)
	# pyhop.pyhop(state, [('have_enough', 'agent', 'cart', 1),('have_enough', 'agent', 'rail', 20)], verbose=3)
