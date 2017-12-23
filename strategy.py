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

    def next_state(self, agent_id, state):
        moves = state.get_legal_moves()
        move = random.sample(moves, 1)[0]
        new_state = state.get_successor_state(agent_id, move)
        return new_state

