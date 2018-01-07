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
    def __init__(self, p_screen, p_unscreen):
        super().__init__()
        self.p_screen = p_screen
        self.p_unscreen = p_unscreen

    def next_move(self, state, time_step):
        """
        The action flow would be:
            1) pass or not
            2) two agent small group or not
            3) left agent go or not
        This method will return the move dict and score log_p
        Parameters
        ---------
        time_step: int
            search depth
        Returns
        ------
        move: move structure
            move that could lead to smallest log_p
        log_p: float
            log probability of successful defense
        """
        if time_step == 0:
            return None, state.log_p
        moves = self.get_step_1_moves(state)
        moves = self.refine_possible_moves(state, moves)
        cands = []
        for move in moves:
            new_state = self.get_successor_state(state, move)
            _, successor_log_p = self.next_move(new_state, time_step - 1)
            cands.append((new_state.log_p + successor_log_p, move))
            #print(move, self.get_reward(state, move))
        cands = sorted(cands, key=itemgetter(0))
        #return move, new_log_p
        return cands[0][1], cands[0][0]

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

        # case 1: not pass
        new_move = copy.deepcopy(move)
        new_white_list = copy.deepcopy(white_list)
        ret.extend(self.get_step_2_moves(state, new_move, new_white_list, set()))
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
                ret.extend(self.get_step_2_moves(state, new_move, new_white_list, set()))
        return ret

    def get_step_2_moves(self, state, move, white_list, pass_list):
        ret = []
        further_search = False
        # case 1: find one agent to screen
        for agent_id_1 in white_list:
            if agent_id_1 in pass_list:
                continue
            # case 1.1 agent_id_1 choose to pass this round
            new_move = copy.deepcopy(move)
            new_white_list = copy.deepcopy(white_list)
            new_pass_list = copy.deepcopy(pass_list)
            new_pass_list.add(agent_id_1)
            ret.extend(self.get_step_2_moves(state, new_move, new_white_list, new_pass_list))
            further_search = True
            # case 1.2 agent_id_1 screen for someone
            for agent_id_2 in white_list:
                if agent_id_2 == agent_id_1:
                    continue
                v1 = state.get_agent_virtual_pos(agent_id_1)
                v2 = state.get_agent_virtual_pos(agent_id_2)
                if v2 not in state.stand_place_link[str(v1)]:
                    continue
                new_move = copy.deepcopy(move)
                new_move["screen"][agent_id_1] = agent_id_2
                new_white_list = copy.deepcopy(white_list)
                new_white_list.remove(agent_id_1)
                new_white_list.remove(agent_id_2)
                new_pass_list = copy.deepcopy(pass_list)
                ret.extend(self.get_step_2_moves(state, new_move, new_white_list, new_pass_list))
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
                print(state.screen_one)
                print(state.run_one)
                print(new_move)
                print(new_white_list)
                print(new_pass_list)
                new_move = copy.deepcopy(move)
                new_move["screen"][agent_id_1] = agent_id_2
                new_white_list = copy.deepcopy(white_list)
                new_white_list.remove(agent_id_1)
                new_pass_list = copy.deepcopy(pass_list)
                ret.extend(self.get_step_2_moves(state, new_move, new_white_list, new_pass_list))
                further_search = True
            break
        if further_search:
            return ret
        else:
            new_move = copy.deepcopy(move)
            new_white_list = copy.deepcopy(white_list)
            return self.get_step_3_moves(state, new_move, new_white_list, set())

    def get_step_3_moves(self, state, move, white_list, pass_list):
        ret = []
        further_search = False
        # casee 1: find one agent to go
        for agent_id_1 in white_list:
            if agent_id_1 in pass_list:
                continue
            # case 1.1 agent_id_1 choose to pass this round
            new_move = copy.deepcopy(move)
            new_white_list = copy.deepcopy(white_list)
            new_pass_list = copy.deepcopy(pass_list)
            new_pass_list.add(agent_id_1)
            ret.extend(self.get_step_3_moves(state, new_move, new_white_list, new_pass_list))
            further_search = True
            # case 1.2 agent_id_1 choose to run
            v1 = state.get_agent_virtual_pos(agent_id_1)
            for v2 in state.stand_place_link[str(v1)]:
                new_move = copy.deepcopy(move)
                new_move["go"][agent_id_1] = v2
                new_white_list = copy.deepcopy(white_list)
                new_white_list.remove(agent_id_1)
                new_pass_list = copy.deepcopy(pass_list)
                ret.extend(self.get_step_3_moves(state, new_move, new_white_list, new_pass_list))
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





class MCTSMotionOffense(Strategy):
    def __init__(self, p_screen, p_unscreen, num_sims, scalar):
        """
        Parameters
        ---------
            p_screen:
            p_unscreen:
            num_sims:   the number of simulations starting from root of MCTS search;
                        the number of simulations are decreasing when searching to the deeper of the tree;
            scalar:     the scalar to control exploitation-exploration balance; 
                        it is used to compute the value of each node in searching tree;
                        larger scalar will increase exploitation, smaller will increase exploration;

        Reference
        --------
            The implementation refers to https://github.com/haroldsultan/MCTS
        """
        super().__init__()
        self.p_screen = p_screen
        self.p_unscreen = p_unscreen
        self.num_sims = num_sims
        self.scalar = scalar

    def next_move(self, state, time_step):
        """
        The action flow would be:
            1) pass or not
            2) two agent small group or not
            3) left agent go or not
        This method will return the move dict and score log_p

        In each move, run a new MCTS search correpsonding to the current time step and decide to take a move

        Parameters
        ---------
        time_step: int
            search depth
        Returns
        ------
        move: move structure
            move that could lead to smallest log_p
        log_p: float
            log probability of successful defense
        """
        if time_step == 0:
            return None, state.log_p
#        moves = self.get_step_1_moves(state)
#        moves = self.refine_possible_moves(state, moves)
#        cands = []
#        for move in moves:
#            new_state = self.get_successor_state(state, move)
#            _, successor_log_p = self.next_move(new_state, time_step - 1)
#            cands.append((new_state.log_p + successor_log_p, move))
#            #print(move, self.get_reward(state, move))
#        cands = sorted(cands, key=itemgetter(0))
#        #return move, new_log_p
        cands = []
        node = self.make_node(state)
        mcts_move = self.MCTSearch(node, int(self.num_sims/(time_step+1)), time_step)
        new_state = self.get_successor_state(state, mcts_move)
        _, successor_log_p = self.next_move(new_state, time_step - 1)
        cands.append((new_state.log_p + successor_log_p, mcts_move))
        return cands[0][1], cands[0][0]

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

        # case 1: not pass
        new_move = copy.deepcopy(move)
        new_white_list = copy.deepcopy(white_list)
        ret.extend(self.get_step_2_moves(state, new_move, new_white_list, set()))
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
                ret.extend(self.get_step_2_moves(state, new_move, new_white_list, set()))
        return ret

    def get_step_2_moves(self, state, move, white_list, pass_list):
        ret = []
        further_search = False
        # case 1: find one agent to screen
        for agent_id_1 in white_list:
            if agent_id_1 in pass_list:
                continue
            # case 1.1 agent_id_1 choose to pass this round
            new_move = copy.deepcopy(move)
            new_white_list = copy.deepcopy(white_list)
            new_pass_list = copy.deepcopy(pass_list)
            new_pass_list.add(agent_id_1)
            ret.extend(self.get_step_2_moves(state, new_move, new_white_list, new_pass_list))
            further_search = True
            # case 1.2 agent_id_1 screen for someone
            for agent_id_2 in white_list:
                if agent_id_2 == agent_id_1:
                    continue
                v1 = state.get_agent_virtual_pos(agent_id_1)
                v2 = state.get_agent_virtual_pos(agent_id_2)
                if v2 not in state.stand_place_link[str(v1)]:
                    continue
                new_move = copy.deepcopy(move)
                new_move["screen"][agent_id_1] = agent_id_2
                new_white_list = copy.deepcopy(white_list)
                new_white_list.remove(agent_id_1)
                new_white_list.remove(agent_id_2)
                new_pass_list = copy.deepcopy(pass_list)
                ret.extend(self.get_step_2_moves(state, new_move, new_white_list, new_pass_list))
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
                print(state.screen_one)
                print(state.run_one)
                print(new_move)
                print(new_white_list)
                print(new_pass_list)
                new_move = copy.deepcopy(move)
                new_move["screen"][agent_id_1] = agent_id_2
                new_white_list = copy.deepcopy(white_list)
                new_white_list.remove(agent_id_1)
                new_pass_list = copy.deepcopy(pass_list)
                ret.extend(self.get_step_2_moves(state, new_move, new_white_list, new_pass_list))
                further_search = True
            break
        if further_search:
            return ret
        else:
            new_move = copy.deepcopy(move)
            new_white_list = copy.deepcopy(white_list)
            return self.get_step_3_moves(state, new_move, new_white_list, set())

    def get_step_3_moves(self, state, move, white_list, pass_list):
        ret = []
        further_search = False
        # casee 1: find one agent to go
        for agent_id_1 in white_list:
            if agent_id_1 in pass_list:
                continue
            # case 1.1 agent_id_1 choose to pass this round
            new_move = copy.deepcopy(move)
            new_white_list = copy.deepcopy(white_list)
            new_pass_list = copy.deepcopy(pass_list)
            new_pass_list.add(agent_id_1)
            ret.extend(self.get_step_3_moves(state, new_move, new_white_list, new_pass_list))
            further_search = True
            # case 1.2 agent_id_1 choose to run
            v1 = state.get_agent_virtual_pos(agent_id_1)
            for v2 in state.stand_place_link[str(v1)]:
                new_move = copy.deepcopy(move)
                new_move["go"][agent_id_1] = v2
                new_white_list = copy.deepcopy(white_list)
                new_white_list.remove(agent_id_1)
                new_pass_list = copy.deepcopy(pass_list)
                ret.extend(self.get_step_3_moves(state, new_move, new_white_list, new_pass_list))
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

    def make_node(self, state, parent=None, depth=0):
        node = {}
        node['state'] = state
        node['parent'] = parent        
        node['successors'] = []
        node['moves'] = []        
        node['visits'] = 1
        node['value'] = 0.0
#        node['value'] = state.log_p #XXX use log_p of the state as initialized value
        node['depth'] = depth # the depth of searching tree
        node['terminal'] = False # recode if the node is in terminal state
        node['expanded'] = False # recode if the node is fully-expanded
        return node

    def MCTSearch(self, root, budget, max_depth):
        for i in range(budget):
            # selection and expansion
            front = self.selection(root, max_depth)
            # simulation
            reward = self.simulation(front, max_depth)
            # backpropagation
            self.backpropagation(front, reward)
        return self.action(root, 0)

    def selection(self, node, max_depth):
        # check terminal conditions
        while not node['terminal'] and node['depth'] < max_depth:
            if len(node['successors']) == 0:
                return self.expansion(node)
            # exploitation and exploration
            elif random.uniform(0,1) < 0.5:
                node = self.select_successors(node, self.scalar)
            else:
                if not node['expanded']:
                    return self.expansion(node)
                # if no new successors to expand, go through and select "best" successors
                node = self.select_successors(node, self.scalar)
        return node


    def expansion(self, node):
        successor_states = [successor['state'] for successor in node['successors']]
        moves = self.get_step_1_moves(node['state'])
        moves = self.refine_possible_moves(node['state'], moves)
        random.shuffle(moves)
        if len(moves) == 0:
            node['terminal'] = True
            return node
        for move in moves:
            new_state = self.get_successor_state(node['state'], move)
            if new_state not in successor_states:
                new_node = self.make_node(new_state, parent=node, depth=node['depth']+1)
                node['successors'].append(new_node)
                node['moves'].append(move)
                break
        if len(moves) == len(node['successors']):
            node['expanded'] = True
        return node['successors'][-1]
                        

    # simulation by random roll-out policy
    def simulation(self, node, max_depth):
        state = node['state']
        depth = node['depth']
        reward = state.log_p #XXX use the max log_p as the reward
        moves = self.get_step_1_moves(state)
        moves = self.refine_possible_moves(state, moves)
        while len(moves) > 0 and depth < max_depth:
            random_move = random.choice(moves)
            new_state = self.get_successor_state(state, random_move)
            new_reward = new_state.log_p
            if new_reward > reward:
                reward = new_reward
            moves = self.get_step_1_moves(new_state)
            moves = self.refine_possible_moves(new_state, moves)
            state = new_state
            depth += 1
        return reward

    def backpropagation(self, node, reward):
        while node != None:
            node['visits'] += 1
            node['value'] += reward
            node = node['parent']


    def action(self, node, scalar):
        # act the move lead to the "best" successor
        best_successor = self.select_successors(node, scalar)
        return node['moves'][node['successors'].index(best_successor)] 

    
    def select_successors(self, node, scalar):
        best_score = float('-inf')
        best_successors = []
        for succ in node['successors']:
            score = self.uct_func(succ, scalar)
            if score > best_score:
                best_score = score
                best_successors = [succ]
            elif score == best_score:
                best_successors.append(succ)
        if len(best_successors) == 0:
            print("Error: no best successor")
        return random.choice(best_successors)


    # upper confidence bounds on trees (UCT) score function
    def uct_func(self, node, scalar):
        exploit = node['value']
        explore = math.sqrt(2.0*math.log(node['parent']['visits'])/float(node['visits']))
        score = exploit + scalar * explore
        return score

