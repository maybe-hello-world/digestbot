from digestbot.core.utils import reaction_dict as rd

react_dict = react_dict
print(react_dict)


def get_react_score(reactions, react_dict):
	''' 
    Returns score of the post according to reactions weights.
	
	:reactions: list of dictionaries containing post info
	:react_dict: dictionary with weights of reactions'''
	
	react_score = 0

	for i in reactions:
		try:
			react_score += react_dict[i['name']]*i['count']
		except KeyError:
			pass
		
	return react_score
	
reactions=[{'name': 'joy', 'users': ['UNQN3Q7MX'], 'count': 1}, {'name': 'man-biking', 'users': ['UNQN3Q7MX'], 'count': 1},{'name': 'joy2', 'users': ['UNQN3Q7MX'], 'count': 1}]

# react_dict = {
# 'joy' : 5,
# 'man-biking' : 3,
# 'minus' : -5
# }

# print(get_react_score(reactions, react_dict))