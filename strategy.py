import state
import random
import copy
import time
import math
from operator import itemgetter


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


class MotionOffense(Strategy):
    def __init__(self):
        super().__init__()
        self.p_screen = 0.2  # prob that defense_agent could catch up
        self.p_unscreen = 0.8  # prob that defense_agent could catch up under screen

    def next_move(self, state, time_step, search_depth, n_beam):
        """
        The action flow would be:
            1) pass or not
            2) two agent small group or not
            3) left agent go or not
        This method will return the move dict and score log_p
        Parameters
        ---------
        time_step: int
            search_time_depth (left time step in real problem)
        search_depth: int
            search_dfs_depth
        n_beam: int
            # of beam search
        Returns
        ------
        moves: list(move structure), len=n_beam
            move that could lead to smallest log_p
        """
        def get_best_log_p(state, t, cur_baseline=None):
            if t == 0:
                return state.log_p
            if cur_baseline is not None and t == 1:
                if state.log_p + len(state.run_one) * math.log(self.p_screen) + (int(state.n_agent / 2) - 1 - len(state.run_one)) * math.log(self.p_unscreen) > cur_baseline:
                    return state.log_p
            moves = self.get_step_1_moves(state)
            moves = self.refine_possible_moves(state, moves)
            best_move = None
            best_log_p = None
            for move in moves:
                new_state = self.get_successor_state(state, move)
                final_log_p = get_best_log_p(new_state, t - 1)
                if best_move is None or final_log_p < best_log_p:
                    best_move = move
                    best_log_p = final_log_p
            return best_log_p

        moves = self.get_step_1_moves(state)
        moves = self.refine_possible_moves(state, moves)
        print("len(moves)", len(moves))
        cands = []
        cur_baseline = None
        for move in moves:
            new_state = self.get_successor_state(state, move)
            new_log_p = get_best_log_p(new_state, min(time_step - 1, search_depth - 1), cur_baseline)
            if len(cands) < n_beam:
                cands.append((move, new_log_p))
            else:
                if new_log_p < cands[-1][1]:
                    cands[-1] = (move, new_log_p)
                cands = sorted(cands, key=itemgetter(1))
                cur_baseline = cands[-1][1]
        cands = sorted(cands, key=itemgetter(1))
        cands_moves = [x[0] for x in cands]
        cands_future_log_p = [x[1] for x in cands]
        return cands_moves[:n_beam], cands_future_log_p[:n_beam]

    def get_step_1_moves(self, state):
        """
        Returns
        -------
        ret: list of dict
            list of possible move
        """
        ret = []
        move = {}
        move["pass"] = {}
        move["screen"] = {}
        move["go"] = {}

        # build white list that could move freely
        white_list = set()
        for agent_id in range(int(state.n_agent / 2)):
            if agent_id == state.ball_agent_id:
                continue
            if agent_id in state.screen_one:
                continue
            white_list.add(agent_id)

        # build occupy_list and screen_list
        occupy_list = set()

        # case 1: not pass
        #new_move = copy.deepcopy(move)
        #new_white_list = copy.deepcopy(white_list)
        ball_agent_id = state.ball_agent_id
        v1 = state.get_agent_virtual_pos(ball_agent_id)
        new_occupy_list = copy.deepcopy(occupy_list)
        new_occupy_list.add(str(v1))
        ret.extend(self.get_step_2_moves(state, move, white_list, set(), new_occupy_list))
        # case 2: find if someone could pass
        ball_agent_id = state.ball_agent_id
        v1 = state.get_agent_virtual_pos(ball_agent_id)
        for agent_id in white_list:
            if agent_id in state.run_one:  # screen_one need to run
                continue
            v2 = state.get_agent_virtual_pos(agent_id)
            if v2 in state.stand_place_link[str(v1)]:
                new_move = copy.deepcopy(move)
                new_move["pass"][ball_agent_id] = agent_id
                new_white_list = copy.deepcopy(white_list)
                new_white_list.add(ball_agent_id)
                new_white_list.remove(agent_id)
                new_occupy_list = copy.deepcopy(occupy_list)
                new_occupy_list.add(str(v2))
                ret.extend(self.get_step_2_moves(state, new_move, new_white_list, set(), new_occupy_list))
        return ret

    def get_step_2_moves(self, state, move, white_list, pass_list, occupy_list):
        ret = []
        further_search = False
        # case 1: find one agent to screen
        for agent_id_1 in white_list:
            if agent_id_1 in pass_list:
                continue
            # case 1.1 agent_id_1 choose to pass this round
            #new_move = copy.deepcopy(move)
            #new_white_list = copy.deepcopy(white_list)
            new_pass_list = copy.deepcopy(pass_list)
            new_pass_list.add(agent_id_1)
            ret.extend(self.get_step_2_moves(state, move, white_list, new_pass_list, occupy_list))
            further_search = True
            # case 1.2 agent_id_1 screen for someone
            for agent_id_2 in white_list:
                if agent_id_2 == agent_id_1:
                    continue
                v1 = state.get_agent_virtual_pos(agent_id_1)
                v2 = state.get_agent_virtual_pos(agent_id_2)
                if v2 not in state.stand_place_link[str(v1)]:
                    continue
                if str(v2) in occupy_list:
                    continue
                new_move = copy.deepcopy(move)
                new_move["screen"][agent_id_1] = agent_id_2
                new_white_list = copy.deepcopy(white_list)
                new_white_list.remove(agent_id_1)
                new_white_list.remove(agent_id_2)
                #new_pass_list = copy.deepcopy(pass_list)
                new_occupy_list = copy.deepcopy(occupy_list)
                new_occupy_list.add(str(v2))
                ret.extend(self.get_step_2_moves(state, new_move, new_white_list, pass_list, new_occupy_list))
                further_search = True
            # state.screen_one could also be agent_id_2
            for agent_id_2 in state.screen_one:
                if agent_id_2 in white_list:  # already process above
                    continue
                if agent_id_2 == agent_id_1:
                    continue
                v1 = state.get_agent_virtual_pos(agent_id_1)
                v2 = state.get_agent_virtual_pos(agent_id_2)
                if v2 not in state.stand_place_link[str(v1)]:
                    continue
                if str(v2) in occupy_list:
                    continue
                new_move = copy.deepcopy(move)
                new_move["screen"][agent_id_1] = agent_id_2
                new_white_list = copy.deepcopy(white_list)
                new_white_list.remove(agent_id_1)
                #new_pass_list = copy.deepcopy(pass_list)
                new_occupy_list = copy.deepcopy(occupy_list)
                new_occupy_list.add(str(v2))
                ret.extend(self.get_step_2_moves(state, new_move, new_white_list, pass_list, new_occupy_list))
                further_search = True
            break
        if further_search:
            return ret
        else:
            #new_move = copy.deepcopy(move)
            #new_white_list = copy.deepcopy(white_list)
            return self.get_step_3_moves(state, move, white_list, set(), occupy_list)

    def get_step_3_moves(self, state, move, white_list, pass_list, occupy_list):
        ret = []
        further_search = False
        # casee 1: find one agent to go
        for agent_id_1 in range(int(state.n_agent / 2)):
            if agent_id_1 not in white_list and agent_id_1 not in state.screen_one:
                continue
            if agent_id_1 in pass_list:
                continue
            if agent_id_1 in state.screen_one and agent_id_1 in move["go"]:
                continue
            # case 1.1 agent_id_1 choose to pass this round
            #new_move = copy.deepcopy(move)
            #new_white_list = copy.deepcopy(white_list)
            new_pass_list = copy.deepcopy(pass_list)
            new_pass_list.add(agent_id_1)
            ret.extend(self.get_step_3_moves(state, move, white_list, new_pass_list, occupy_list))
            further_search = True
            # case 1.2 agent_id_1 choose to run
            v1 = state.get_agent_virtual_pos(agent_id_1)
            for v2 in state.stand_place_link[str(v1)]:
                if str(v2) in occupy_list:
                    continue
                new_move = copy.deepcopy(move)
                new_move["go"][agent_id_1] = v2
                new_white_list = copy.deepcopy(white_list)
                if agent_id_1 in new_white_list:
                    new_white_list.remove(agent_id_1)
                #new_pass_list = copy.deepcopy(pass_list)
                new_occupy_list = copy.deepcopy(occupy_list)
                new_occupy_list.add(str(v2))
                ret.extend(self.get_step_3_moves(state, new_move, new_white_list, pass_list, new_occupy_list))
                further_search = True
            break
        if further_search:
            return ret
        else:
            new_move = copy.deepcopy(move)
            return [new_move]

    def refine_possible_moves(self, state, moves):
        """remove those move that would result two agent run into same place"""
        new_moves = []
        for move in moves:
            ok = True
            # can't two agent screen for same agent
            same_screen_agent = set()
            same_place = set()
            for agent_id_1 in move["screen"]:
                agent_id_2 = move["screen"][agent_id_1]
                if agent_id_2 in same_screen_agent:
                    ok = False
                same_screen_agent.add(agent_id_2)
            # can't two agent be at same place, except screen_one
            for agent_id in range(int(state.n_agent / 2)):
                if agent_id in move["screen"]:
                    continue
                if agent_id not in move["go"]:
                    vpos = state.get_agent_virtual_pos(agent_id)
                else:
                    vpos = move["go"][agent_id]
                if str(vpos) in same_place:
                    ok = False
                same_place.add(str(vpos))
            if ok:
                new_moves.append(move)
        return new_moves

    def get_reward(self, state, move):
        log_p = 0
        ball_agent_id = state.ball_agent_id
        if len(move["pass"]) > 0:
            for x in move["pass"]:  # only one x
                ball_agent_id = move["pass"][x]
        v1 = state.get_agent_virtual_pos(ball_agent_id)
        for agent_id in move["go"]:
            v2 = move["go"][agent_id]
            if v2 in state.stand_place_link[str(v1)]:
                if agent_id in state.run_one:
                    log_p += math.log(self.p_screen)
                else:
                    log_p += math.log(self.p_unscreen)
        return log_p

    def get_successor_state(self, state, move):
        new_state = copy.copy(state)
        new_state.my_deep_copy()
        """
        self.agents = copy.deepcopy(self.agents)
        self.screen_one = copy.deepcopy(self.screen_one)
        self.run_one = copy.deepcopy(self.run_one)
        """
        if len(move["pass"]) > 0:
            for x in move["pass"]:  # only one x
                new_state.ball_agent_id = move["pass"][x]
        new_state.screen_one = []
        new_state.run_one = []
        for agent_id_1, agent_id_2 in move["screen"].items():
            new_state.screen_one.append(agent_id_1)
            new_state.run_one.append(agent_id_2)
            vpos = state.get_agent_virtual_pos(agent_id_2)
            new_state.move_agent_to(agent_id_1, vpos)
        for agent_id_1, vpos in move["go"].items():
            new_state.move_agent_to(agent_id_1, vpos)
        new_state.log_p += self.get_reward(state, move)
        return new_state

    """
    def get_successor_state(self, agent_id, move):
        agent = self.agents[agent_id]
        virtual_pos = agent.get_virtual_pos()
        new_virtual_pos = [sum(x) for x in zip(virtual_pos, move)]

        check = True
        if not self.virtual_pos_is_null(agent_id, new_virtual_pos):
            check = False
        if not self.position.virtual_is_in(new_virtual_pos):
            check = False

        #new_state = copy.deepcopy(self)
        new_state = copy.copy(self)
        new_state.my_hard_copy()
        #new_state.agents = copy.deepcopy(self.agents)
        if check:
            new_state.agents[agent_id].move(move)
        return new_state
    """


class MotionDefense(Strategy):
    def __init__(self):
        super().__init__()

    def next_state(self, state, depth=1):
        pass
