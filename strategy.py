import state
import random


class Strategy:
    def __init__(self):
        pass

    def get_next_move(self, agent_id, state):
        pass


class Brownian(Strategy):
    def __init__(self):
        super().__init__()

    def next_move(self, agent_id, state):
        moves = state.get_legal_moves()
        move = random.sample(moves, 1)[0]
        return move


class Minimax(Strategy):
    def __init__(self):
        super().__init__()

    def evaluation_function(self, state):
        def cross_product(a, b):
            return a[0] * b[0] + a[1] * b[1]

        vpos_offense_agents = []
        vpos_defense_agents = []
        for i in range(state.n_agent):
            if i < state.n_agent / 2:
                vpos_offense_agents.append(state.get_agent_virtual_pos(i))
            else:
                vpos_defense_agents.append(state.get_agent_virtual_pos(i))
        vpos_basket = state.get_basket_virtual_pos()

        ret = 0
        # if offense agent far from basket
        for i in range(len(vpos_offense_agents)):
            real_three_point = 6.75
            if state.position.real_distance(vpos_offense_agents[i],
                    vpos_basket) > real_three_point + 1:
                ret -= 10000
        """
        # if offense close to basket
        for agent_id in range(int(state.n_agent / 2)):
            ret += -2 * (state.basket_distance(agent_id))
        """
        # if offense has space
        for agent_id in range(int(state.n_agent / 2)):
            if state.is_open(agent_id):
                ret += 1000
        return ret

    def next_move(self, agent_id, state, depth=3):
        def min_score(agent_id, state, depth):
            if depth == 0:
                return self.evaluation_function(state), None
            moves = state.get_legal_moves()
            ret_s = 100000000
            ret_move = None
            next_agent_id = (agent_id + 1) % state.n_agent
            for move in moves:
                next_state = state.get_successor_state(agent_id, move)
                if next_agent_id < state.n_agent / 2:
                    s, _ = max_score(next_agent_id, next_state, depth - 1)
                else:
                    s, _ = min_score(next_agent_id, next_state, depth - 1)
                if s < ret_s:
                    ret_s = s
                    ret_move = move
            return ret_s, ret_move

        def max_score(agent_id, state, depth):
            if depth == 0:
                return self.evaluation_function(state), None
            moves = state.get_legal_moves()
            ret_s = -100000000
            ret_move = None
            next_agent_id = (agent_id + 1) % state.n_agent
            for move in moves:
                next_state = state.get_successor_state(agent_id, move)
                if next_agent_id < state.n_agent / 2:
                    s, _ = max_score(next_agent_id, next_state, depth - 1)
                else:
                    s, _ = min_score(next_agent_id, next_state, depth - 1)
                if s > ret_s:
                    ret_s = s
                    ret_move = move
            return ret_s, ret_move

        if agent_id < state.n_agent / 2:
            s, m = max_score(agent_id, state, depth)
        else:
            s, m = min_score(agent_id, state, depth)

        print("next move {} score {}".format(str(m), s))
        print("defense_distance {}".format(state.defense_distance(agent_id)))
        return m


class Oneonone(Strategy):
    """
    0 <-> 5, 1 <-> 6, ...
    """
    def __inti__(self):
        super().__init__()

    def next_move(self, agent_id, state):
        vpos_basket = state.get_basket_virtual_pos()
        vpos_offense = state.get_agent_virtual_pos(agent_id - int(state.n_agent / 2))
        vpos_defense = state.get_agent_virtual_pos(agent_id)
        path_offence = state.get_shortest_path(vpos_offense, vpos_basket)
        try:
            path_defense = state.get_shortest_path(vpos_defense, path_offence[1])
        except:
            path_defense = state.get_shortest_path(vpos_defense, path_offence[0])

        try:
            dx = path_defense[1][0] - vpos_defense[0]
            dy = path_defense[1][1] - vpos_defense[1]
        except:
            dx = 0
            dy = 0
        return [dx, dy]
