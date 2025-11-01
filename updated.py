# =====================================================
# Quantum Territory Wars — Pygame Edition (Fuzzy + Minimax + A*)
# UI v9.1 - EDGE CASES FIXED
# - Title page: Manual overlay with 3 pages (Left/Right to navigate), 1/2/3 to select modes, Exit quits
# - In-game ESC: confirm overlay to return Home
# - Human Expand: click a highlighted hex to claim (E or button)
# - AI: Minimax (alpha-beta) with fuzzy evaluation
# - Map: random each run, EXACTLY 5 Quantum Nodes, randomized well-spaced starts
# =====================================================

import math, random, heapq, copy, sys
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple, Optional

import pygame

# ---------------------------- Globals (updated at runtime) ----------------------------
WIN_W, WIN_H = 1550, 800
MARGIN = 20
RIGHT_PANEL_W = 380
FOOTER_H = 145
TOPBAR_H = 80
HEX_SIZE = 28  # recalculated after window created

BG_TOP = (18, 20, 27)
BG_BOT = (10, 12, 16)

WHITE=(250,250,252); GRAY1=(210,212,218); GRAY2=(160,165,176); GRAY3=(110,115,130)
PANEL_BG=(28,30,38); PANEL_STROKE=(70,76,92)
FOCUS=(255,235,120)
DISABLED=(55,58,70)
SUCCESS=(106, 212, 125)

OWNER_COLORS = {
    0: (90,170,255),   # EXPANSION_EMPIRE (blue)
    1: (255,110,110),  # TECH_COLLECTIVE (red)
    2: (125,220,140),  # ADAPTIVE_ALLIANCE (green)
    3: (95,100,115)    # NEUTRAL (slate)
}
TERRAIN_FILL = {
    "plains": (196,210,178),
    "forest": (86,143,105),
    "mountain": (145,138,133),
    "desert": (233,206,144),
    "water": (102,136,220),
    "quantum_node": (198,168,240),
}
TERRAIN_NAMES = {
    "plains": "Plains",
    "forest": "Forest",
    "mountain": "Mountain",
    "desert": "Desert",
    "water": "Water",
    "quantum_node": "Quantum Node",
}

# fonts (updated by compute_fonts / recalc_layout)
font_small=font=font_mid=font_big=font_title=None

# layout rects (updated by recalc_layout)
footer_rect=right_rect=None
MAP_ORIGIN=(0,0)

# will be created in run()
btns=[]
minimap=None

# ---------------------------- Enums & Data ----------------------------
class TerrainType(Enum):
    PLAINS="plains"; FOREST="forest"; MOUNTAIN="mountain"; DESERT="desert"; WATER="water"; QUANTUM_NODE="quantum_node"
class FactionType(Enum):
    EXPANSION_EMPIRE=0; TECH_COLLECTIVE=1; ADAPTIVE_ALLIANCE=2; NEUTRAL=3
class UnitType(Enum):
    SCOUT="scout"; WARRIOR="warrior"; ENGINEER="engineer"; QUANTUM_SPECIALIST="quantum_specialist"
# Add this RIGHT HERE (after the enum definitions):
TERRAIN_ECONOMY = {
    TerrainType.PLAINS: 1.0,        # Easy terrain = normal gain
    TerrainType.FOREST: 1.3,        # Moderate = 30% bonus
    TerrainType.DESERT: 1.4,        # Harder = 40% bonus
    TerrainType.MOUNTAIN: 1.8,      # Toughest = 80% bonus
    TerrainType.WATER: 1.6,         # Hard to traverse = 60% bonus
    TerrainType.QUANTUM_NODE: 2.0,  # Strategic = 100% bonus (double)
}

@dataclass(frozen=True)
class Position:
    q:int; r:int
    def neighbors(self):
        for dq,dr in [(1,0),(1,-1),(0,-1),(-1,0),(-1,1),(0,1)]:
            yield Position(self.q+dq, self.r+dr)

@dataclass
class Unit:
    unit_type:UnitType; faction:FactionType; position:Position
    health:int; movement_points:int; max_movement:int
    def __post_init__(self):
        if self.health<=0: self.health=self.get_max_health()
        if self.movement_points<=0: self.movement_points=self.max_movement
    def get_max_health(self):
        return {UnitType.SCOUT:50, UnitType.WARRIOR:100, UnitType.ENGINEER:75, UnitType.QUANTUM_SPECIALIST:60}[self.unit_type]

@dataclass
class Hex:
    position:Position; terrain:TerrainType; owner:FactionType; units:List[Unit]; resources:int; quantum_charge:int=0
    def __post_init__(self):
        if self.units is None: self.units=[]

@dataclass
class Player:
    faction:FactionType; resources:int=100; territories_controlled:int=0
    quantum_nodes_controlled:int=0; units:List[Unit]=None; is_ai:bool=True
    economy_uses:int=0  # <-- ADD THIS LINE
    build_uses:int=0  # <-- ADD THIS NEW LINE
    def __post_init__(self):
        if self.units is None: self.units=[]

# ---------------------------- A* Pathfinding ----------------------------
class AStar:
    def __init__(self, board): self.board=board
    def dist(self,a:Position,b:Position):
        # hex distance (axial)
        return max(abs(a.q-b.q), abs((a.q+a.r)-(b.q+b.r)), abs(a.r-b.r))
    def valid(self,p:Position): return p in self.board.hexes
    def neighbors(self,p:Position):
        for n in p.neighbors():
            if self.valid(n): yield n
    def cost(self, frm:Position, to:Position, unit:Unit):
        if not self.valid(to): return 9e9
        h=self.board.hexes[to]
        base={
            TerrainType.PLAINS:1.0, TerrainType.FOREST:1.5, TerrainType.MOUNTAIN:2.0,
            TerrainType.DESERT:1.3, TerrainType.WATER:3.0, TerrainType.QUANTUM_NODE:1.0
        }[h.terrain]
        if unit.unit_type==UnitType.SCOUT: base*=0.8
        if unit.unit_type==UnitType.ENGINEER and h.terrain==TerrainType.MOUNTAIN: base*=0.7
        if h.owner not in (FactionType.NEUTRAL, unit.faction): base*=1.5
        return base
    def path(self,start:Position,goal:Position,unit:Unit):
        if start==goal: return [start]
        cnt=0; openh=[(0,cnt,start,[start])]; g={start:0.0}; closed=set()
        while openh:
            _,_,cur,pth=heapq.heappop(openh)
            if cur in closed: continue
            if cur==goal: return pth
            closed.add(cur)
            for nb in self.neighbors(cur):
                if nb in closed: continue
                tg=g[cur]+self.cost(cur,nb,unit)
                if nb not in g or tg<g[nb]:
                    g[nb]=tg; cnt+=1
                    heapq.heappush(openh,(tg+self.dist(nb,goal),cnt,nb,pth+[nb]))
        return []

# ---------------------------- Game Board ----------------------------
class GameBoard:
    def __init__(self,size=11):
        self.size=size; self.hexes:Dict[Position,Hex]={}; self.astar=AStar(self); self.qnodes=[]
        self._gen()

    def _gen(self):
        # Step 1: create non-quantum terrain randomly
        for q in range(self.size):
            for r in range(self.size-q):
                pos=Position(q,r)
                terr=self._random_basic_terrain()
                hx=Hex(pos,terr,FactionType.NEUTRAL,[],random.randint(5,25))
                self.hexes[pos]=hx

        # Step 2: place EXACTLY 5 Quantum Nodes on non-water hexes, spread-ish
        candidates=[p for p,h in self.hexes.items() if h.terrain!=TerrainType.WATER]
        
        # EDGE CASE FIX: Ensure we have enough candidates
        if len(candidates) < 5:
            # If not enough non-water hexes, convert some water to plains
            water_hexes = [p for p,h in self.hexes.items() if h.terrain==TerrainType.WATER]
            for p in water_hexes[:5-len(candidates)]:
                self.hexes[p].terrain = TerrainType.PLAINS
                candidates.append(p)
        
        random.shuffle(candidates)
        chosen=[]
        def hex_dist(a:Position,b:Position):
            return max(abs(a.q-b.q), abs((a.q+a.r)-(b.q+b.r)), abs(a.r-b.r))
        min_sep = 3
        for p in candidates:
            if len(chosen)>=5: break
            if all(hex_dist(p,c)>=min_sep for c in chosen):
                chosen.append(p)
        # If we didn't get 5 due to spacing, fill remaining greedily
        if len(chosen)<5:
            for p in candidates:
                if p not in chosen:
                    chosen.append(p)
                    if len(chosen)==5: break
        
        # EDGE CASE FIX: Ensure we always have exactly 5 nodes
        while len(chosen) < 5 and candidates:
            for p in candidates:
                if p not in chosen:
                    chosen.append(p)
                    if len(chosen)==5: break
        
        for p in chosen:
            self.hexes[p].terrain=TerrainType.QUANTUM_NODE
            self.qnodes.append(p)

    def _random_basic_terrain(self):
        # stochastic terrain; keeps WATER relatively rare
        p=random.random()
        if p<0.42: return TerrainType.PLAINS
        if p<0.62: return TerrainType.FOREST
        if p<0.78: return TerrainType.MOUNTAIN
        if p<0.92: return TerrainType.DESERT
        return TerrainType.WATER

# ---------------------------- Game ----------------------------
class Game:
    def __init__(self, player_types):
        # EDGE CASE FIX: Ensure we have at least one player
        if not player_types or len(player_types) == 0:
            player_types = [False, True, True]  # Default to 1 human, 2 AI
        
        self.board=GameBoard(size=11)
        self.players:List[Player]=[]
        self.idx=0; self.turn=1
        self.game_over=False; self.winner=None
        self.ai={}
        facs=[FactionType.EXPANSION_EMPIRE, FactionType.TECH_COLLECTIVE, FactionType.ADAPTIVE_ALLIANCE]
        for i,is_ai in enumerate(player_types):
            p=Player(faction=facs[i], is_ai=is_ai); self.players.append(p)
        # Create AI after players exist
        for p in self.players:
            if p.is_ai:
                self.ai[p.faction]=MinimaxAI(p.faction,depth=2)

        self._setup_random_spaced_starts()
        self.log:List[str]=[]
        self.last_action_feedback=None  # (center_xy, ttl)

    def _setup_random_spaced_starts(self):
        """Pick 3 non-water, non-quantum starts with min spacing; fallback if needed."""
        all_positions=[pos for pos,h in self.board.hexes.items()
                       if h.terrain not in (TerrainType.WATER,)]
        random.shuffle(all_positions)

        def dist(a:Position,b:Position):
            return self.board.astar.dist(a,b)

        chosen=[]
        min_sep=6
        for p in all_positions:
            if len(chosen)>=len(self.players): break
            if self.board.hexes[p].terrain==TerrainType.QUANTUM_NODE:
                continue
            if all(dist(p,c)>=min_sep for c in chosen):
                chosen.append(p)

        # fallback to relax constraints if not enough
        if len(chosen)<len(self.players):
            for p in all_positions:
                # EDGE CASE FIX: Check if already chosen
                if p not in chosen and self.board.hexes[p].terrain!=TerrainType.QUANTUM_NODE:
                    chosen.append(p)
                    if len(chosen)==len(self.players): break

        # EDGE CASE FIX: Final fallback - use any non-water hex if still not enough
        if len(chosen)<len(self.players):
            for p in all_positions:
                if p not in chosen:
                    chosen.append(p)
                    if len(chosen)==len(self.players): break

        # apply
        for i, player in enumerate(self.players):
            if i < len(chosen):
                pos=chosen[i]
            else:
                # EDGE CASE FIX: Absolute fallback - use first available position
                pos=chosen[0] if chosen else next(iter(self.board.hexes))
            
            self.board.hexes[pos].owner=player.faction
            player.territories_controlled+=1
            u=Unit(UnitType.SCOUT, player.faction, pos, 50, 3, 3)
            player.units.append(u); self.board.hexes[pos].units.append(u)

    def post(self, msg:str):
        self.log.append(f"[T{self.turn}] {msg}")
        if len(self.log)>10: self.log=self.log[-10:]

    def affordable(self,cost): 
        return self.players[self.idx].resources>=cost if self.players else False

    def income_tick(self):
        for p in self.players: 
            # EDGE CASE FIX: Ensure values don't go negative
            p.resources = max(0, p.resources + 10 + max(0, p.territories_controlled)*2)

    def check_victory(self):
        for p in self.players:
            if p.territories_controlled>=18: 
                self.game_over=True; self.winner=p.faction
                self.post(f"{p.faction.name} wins (Territory)!"); return
            if p.quantum_nodes_controlled>=5: 
                self.game_over=True; self.winner=p.faction
                self.post(f"{p.faction.name} wins (Quantum)!"); return
            if p.resources>=600: 
                self.game_over=True; self.winner=p.faction
                self.post(f"{p.faction.name} wins (Economy)!"); return

    def available(self):
        p=self.players[self.idx]; opts=[]
        if p.resources>=30: opts.append(("Expand", "expand",30))
        if p.resources>=40: opts.append(("Build", "build",40))
        if p.resources>=25 and p.economy_uses<3: opts.append(("Economy","economy",25))  # <-- CHECK LIMIT
        opts.append(("End Turn","end",0))
        return opts

    # --- Human targeted expand ---
    def expand_candidates(self, faction: FactionType):
        cand=set()
        for hx in self.board.hexes.values():
            if hx.owner==faction:
                for nb in hx.position.neighbors():
                    if nb in self.board.hexes and self.board.hexes[nb].owner==FactionType.NEUTRAL:
                        cand.add(nb)
        return cand
    
    def build_candidates(self, faction: FactionType):
        """Returns all owned hexes where a warrior can be built"""
        cand = set()
        for hx in self.board.hexes.values():
            if hx.owner == faction:
                cand.add(hx.position)
        return cand

    def apply_expand_to(self, faction: FactionType, pos: Position, cost=30):
        p=self.players[self.idx]
        if p.faction!=faction: return False
        if p.resources<cost: return False
        if pos not in self.board.hexes: return False
        hx=self.board.hexes[pos]
        if hx.owner!=FactionType.NEUTRAL: return False
        # must be adjacent to any owned tile
        ok=False
        for nb in pos.neighbors():
            if nb in self.board.hexes and self.board.hexes[nb].owner==faction:
                ok=True; break
        if not ok: return False

        # commit
        p.resources-=cost
        hx.owner=faction
        p.territories_controlled+=1
        p.resources += hx.resources  # <-- ADD THIS LINE
        # EDGE CASE FIX: Only count actual quantum nodes
        if hx.terrain==TerrainType.QUANTUM_NODE:
            p.quantum_nodes_controlled+=1
        self.post(f"{p.faction.name}: Expand to ({pos.q},{pos.r})")
        return True
    
    def apply_build_to(self, faction: FactionType, pos: Position, cost=40):
        p = self.players[self.idx]
        if p.faction != faction: return False
        if p.resources < cost: return False
        if p.build_uses >= 1: return False  # <-- ADD THIS CHECK
        if pos not in self.board.hexes: return False
        hx = self.board.hexes[pos]
        if hx.owner != faction: return False
        
        # Commit build
        p.resources -= cost
        p.build_uses += 1  # <-- ADD THIS LINE
        u = Unit(UnitType.WARRIOR, faction, pos, 100, 2, 2)
        p.units.append(u)
        hx.units.append(u)
        
        # Add adjacent resources
        adjacent_resources = 0
        for nb in pos.neighbors():
            if nb in self.board.hexes:
                adjacent_resources += self.board.hexes[nb].resources
        
        p.resources += adjacent_resources
        
        self.post(f"{p.faction.name}: Build at ({pos.q},{pos.r}), gained {adjacent_resources} from adjacents")
        return True

    # --- Generic apply (AI + other actions) ---
    def apply(self, act:str, cost:int, selected:Optional[Position]=None):
        p=self.players[self.idx]
        if act=="expand" and p.resources>=cost:
            p.resources-=cost
            owned=[h for h in self.board.hexes.values() if h.owner==p.faction]
            if not owned:
                self.post(f"{p.faction.name}: Expand failed (no owned hexes)")
                return None
            random.shuffle(owned)
            claimed=None
            for oh in owned:
                for nb in oh.position.neighbors():
                    if nb in self.board.hexes and self.board.hexes[nb].owner==FactionType.NEUTRAL:
                        self.board.hexes[nb].owner=p.faction 
                        p.territories_controlled+=1
                        p.resources += self.board.hexes[nb].resources  # <-- ADD THIS LINE
                        # EDGE CASE FIX: Only count actual quantum nodes
                        if self.board.hexes[nb].terrain==TerrainType.QUANTUM_NODE:
                            p.quantum_nodes_controlled+=1
                        claimed=nb; break
                if claimed: break
            if claimed:
                self.post(f"{p.faction.name}: Expand to ({claimed.q},{claimed.r})")
            else:
                self.post(f"{p.faction.name}: Expand failed (no valid hexes)")
            return claimed
        elif act=="build" and p.resources>=cost and p.build_uses<1:
            p.resources-=cost
            p.build_uses += 1
            
            # AI SMART BUILD: Choose hex with MAXIMUM adjacent resources
            best_pos = None
            best_adjacent_resources = -1
            
            for h in self.board.hexes.values():
                if h.owner == p.faction:
                    # Calculate adjacent resources for this hex
                    adjacent_resources = 0
                    for nb in h.position.neighbors():
                        if nb in self.board.hexes:
                            adjacent_resources += self.board.hexes[nb].resources
                    
                    # Pick the hex with most adjacent resources
                    if adjacent_resources > best_adjacent_resources:
                        best_adjacent_resources = adjacent_resources
                        best_pos = h.position
            
            if best_pos is None:
                self.post(f"{p.faction.name}: Build failed (no owned hexes)")
                return None
            
            # Build the warrior
            u = Unit(UnitType.WARRIOR, p.faction, best_pos, 100, 2, 2)
            p.units.append(u)
            self.board.hexes[best_pos].units.append(u)
            
            # Add the adjacent resources to economy
            p.resources += best_adjacent_resources
            
            self.post(f"{p.faction.name}: Build at ({best_pos.q},{best_pos.r}), gained {best_adjacent_resources} from adjacents")
            return best_pos
        elif act=="economy" and p.resources>=cost and p.economy_uses<3:
            p.resources-=cost
            p.economy_uses += 1  # <-- INCREMENT COUNTER
            
            # Calculate bonus based on selected hex terrain
            base_gain = 40
            if selected and selected in self.board.hexes:
                terrain_multiplier = TERRAIN_ECONOMY[self.board.hexes[selected].terrain]
                actual_gain = int(base_gain * terrain_multiplier)
            else:
                actual_gain = base_gain
            
            p.resources += actual_gain
            remaining = 3 - p.economy_uses  # <-- CALCULATE REMAINING
            self.post(f"{p.faction.name}: Economy +{actual_gain}")
            return None
        elif act=="end":
            self.post(f"{p.faction.name}: End Turn")
            return None
        return None

    def next_turn(self):
        # EDGE CASE FIX: Prevent division by zero
        if len(self.players) == 0:
            return
        
        # Switch to next player FIRST
        self.idx=(self.idx+1)%len(self.players)
        
        if self.idx==0:
            self.turn+=1
            self.income_tick()

# ---------------------------- Fuzzy Logic ----------------------------
def tri(x, a, b, c):
    if x<=a or x>=c: return 0.0
    if x==b: return 1.0
    if x<a: return 0.0
    if x<b: return (x-a)/(b-a)
    return (c-x)/(c-b)

def trap(x, a, b, c, d):
    if x<=a or x>=d: return 0.0
    if b<=x<=c: return 1.0
    if a<x<b: return (x-a)/(b-a)
    return (d-x)/(d-c)

class FuzzyEvaluator:
    def __init__(self):
        self.RES_MAX=600
        self.TERR_MAX=18
        self.QN_MAX=5
        self.UNIT_MAX=20
        self.out_scores = {
            "Poor": 150.0,
            "Fair": 400.0,
            "Good": 700.0,
            "Excellent": 950.0,
        }

    def fuzzify(self, resources:int, territories:int, qnodes:int, units:int):
        r = max(0, min(self.RES_MAX, resources))
        t = max(0, min(self.TERR_MAX, territories))
        q = max(0, min(self.QN_MAX, qnodes))
        u = max(0, min(self.UNIT_MAX, units))

        res = {
            "Low":     trap(r, 0, 0, 120, 240),
            "Medium":  tri(r, 160, 300, 440),
            "High":    trap(r, 360, 480, 600, 600),
        }
        ter = {
            "Few":       trap(t, 0, 0, 4, 7),
            "Moderate":  tri(t, 5, 9, 13),
            "Many":      trap(t, 11, 14, 18, 18),
        }
        qn = {
            "None":  trap(q, 0, 0, 1, 2),
            "Some":  tri(q, 1, 2.5, 4),
            "Many":  trap(q, 3, 4, 5, 5),
        }
        un = {
            "Weak":     trap(u, 0, 0, 4, 7),
            "Balanced": tri(u, 5, 8.5, 12),
            "Strong":   trap(u, 10, 13, 20, 20),
        }
        return res, ter, qn, un

    def infer(self, resources:int, territories:int, qnodes:int, units:int) -> float:
        res, ter, qn, un = self.fuzzify(resources, territories, qnodes, units)
        out_strengths = {k:0.0 for k in self.out_scores.keys()}

        def add(rule_strength, label):
            out_strengths[label] = max(out_strengths[label], rule_strength)

        # Priority on QN
        add(qn["Many"], "Excellent")
        add(min(qn["Some"], ter["Many"]), "Good")

        # Resources × Territories synergy
        add(min(res["High"], ter["Many"]), "Excellent")
        add(min(res["High"], ter["Moderate"]), "Good")
        add(min(res["Medium"], ter["Many"]), "Good")
        add(min(res["Medium"], ter["Moderate"]), "Fair")
        add(min(res["Low"], ter["Few"]), "Poor")

        # Units impact
        add(un["Strong"], "Good")
        add(min(un["Balanced"], ter["Moderate"]), "Good")
        add(min(un["Balanced"], res["High"]), "Good")  # NEW: Units + Resources
        add(un["Weak"], "Fair")
        
        # Resource advantage rules (ECONOMY boosts this)
        add(min(res["High"], un["Strong"]), "Excellent")  # NEW: Rich + Strong Army
        add(min(res["Medium"], un["Balanced"]), "Good")   # NEW: Balanced economy

        # Fallbacks
        add(res["Low"], "Fair")
        add(res["High"], "Good")
        add(ter["Few"], "Fair")
        add(ter["Many"], "Good")

        num = 0.0; den = 0.0
        for label, w in out_strengths.items():
            s = self.out_scores[label]
            num += w * s
            den += w
        return (num / den) if den>1e-9 else 0.0

# ---------------------------- Minimax AI ----------------------------
class GameState:
    def __init__(self,board,players,idx,turn):
        self.board=board; self.players=players; self.idx=idx; self.turn=turn
    def copy(self): return GameState(copy.deepcopy(self.board), copy.deepcopy(self.players), self.idx, self.turn)

class MinimaxAI:
    def __init__(self,faction,depth=2):
        self.faction=faction; self.depth=depth
        self.fuzzy = FuzzyEvaluator()

    def eval_player(self, p:Player) -> float:
        return self.fuzzy.infer(p.resources, p.territories_controlled,
                                p.quantum_nodes_controlled, len(p.units))

    def eval(self, st:GameState):
        me=next((p for p in st.players if p.faction==self.faction),None)
        if not me: return -1e6
        opp=[p for p in st.players if p.faction!=self.faction]
        my_score = self.eval_player(me)
        opp_score = (sum(self.eval_player(p) for p in opp)/len(opp)) if opp else 0.0
        crisp_bonus = (
            (50 if me.territories_controlled>=15 else 0) +
            (80 if me.quantum_nodes_controlled>=4 else 0) +
            (40 if me.resources>=450 else 0) +
            (30 if len(me.units)>=8 else 0) +        # NEW: Bonus for strong army
            (20 if me.resources>=250 else 0)          # NEW: Bonus for good economy
        )
        return (my_score - opp_score) + crisp_bonus

    def moves(self,st):
        p=st.players[st.idx]; m=[]
        if p.resources>=30: m.append(("expand",30))
        if p.resources>=40 and p.build_uses<1: m.append(("build",40))
        if p.resources>=25 and p.economy_uses<3: m.append(("economy",25))
        if not m: m.append(("end",0))
        return m

    def apply(self,st,mv):
        ns=st.copy(); p=ns.players[ns.idx]; act,cost=mv
        if act=="expand" and p.resources>=cost:
            p.resources-=cost
            owned=[h for h in ns.board.hexes.values() if h.owner==p.faction]
            if not owned:
                return ns
            random.shuffle(owned)
            claimed=False
            for oh in owned:
                for nb in oh.position.neighbors():
                    if nb in ns.board.hexes and ns.board.hexes[nb].owner==FactionType.NEUTRAL:
                        ns.board.hexes[nb].owner=p.faction
                        p.territories_controlled+=1
                        p.resources += ns.board.hexes[nb].resources  # <-- ADD THIS LINE
                        # EDGE CASE FIX: Only count actual quantum nodes
                        if ns.board.hexes[nb].terrain==TerrainType.QUANTUM_NODE:
                            p.quantum_nodes_controlled+=1
                        claimed=True; break
                if claimed: break
        elif act=="build" and p.resources>=cost and p.build_uses<1:
            p.resources-=cost
            p.build_uses += 1  # <-- INCREMENT COUNTER
            
            # AI SMART BUILD: Choose hex with MAXIMUM adjacent resources
            best_pos = None
            best_adjacent_resources = -1
            
            for h in ns.board.hexes.values():
                if h.owner == p.faction:
                    # Calculate adjacent resources for this hex
                    adjacent_resources = 0
                    for nb in h.position.neighbors():
                        if nb in ns.board.hexes:
                            adjacent_resources += ns.board.hexes[nb].resources
                    
                    # Pick the hex with most adjacent resources
                    if adjacent_resources > best_adjacent_resources:
                        best_adjacent_resources = adjacent_resources
                        best_pos = h.position
            
            if best_pos is not None:
                u = Unit(UnitType.WARRIOR, p.faction, best_pos, 100, 2, 2)
                p.units.append(u)
                ns.board.hexes[best_pos].units.append(u)
                
                # Add the adjacent resources to AI's economy
                p.resources += best_adjacent_resources
        elif act=="economy" and p.resources>=cost and p.economy_uses<3:
            p.resources-=cost
            p.economy_uses += 1  # <-- INCREMENT COUNTER
            p.resources+=40
        return ns

    def minimax(self, st:GameState, depth:int, alpha:float, beta:float, maxing:bool):
        if depth==0:
            return self.eval(st), None

        actions = self.moves(st)
        best_move=None

        if maxing:
            value = -1e18
            for mv in actions:
                ns = self.apply(st, mv)
                # EDGE CASE FIX: Check for valid players before indexing
                if not ns.players:
                    continue
                ns.idx = (ns.idx+1)%len(ns.players)
                v,_ = self.minimax(ns, depth-1, alpha, beta,
                                   maxing=(ns.players[ns.idx].faction==self.faction))
                if v>value:
                    value=v; best_move=mv
                alpha=max(alpha, value)
                if beta<=alpha: break
            return value, best_move
        else:
            value = 1e18
            for mv in actions:
                ns = self.apply(st, mv)
                # EDGE CASE FIX: Check for valid players before indexing
                if not ns.players:
                    continue
                ns.idx = (ns.idx+1)%len(ns.players)
                v,_ = self.minimax(ns, depth-1, alpha, beta,
                                   maxing=(ns.players[ns.idx].faction==self.faction))
                if v<value:
                    value=v; best_move=mv
                beta=min(beta, value)
                if beta<=alpha: break
            return value, best_move

    def best(self,st):
        _,mv=self.minimax(st,self.depth,-1e18,1e18,True)
        return mv or ("end",0)

# ---------------------------- UI Helpers ----------------------------
def compute_fonts(h):
    scale = max(0.75, min(1.0, h / 900.0))
    f_small = pygame.font.SysFont("consolas", int(14*scale))
    f = pygame.font.SysFont("consolas", int(16*scale))
    f_mid = pygame.font.SysFont("consolas", int(18*scale), bold=True)
    f_big = pygame.font.SysFont("consolas", int(32*scale), bold=True)
    f_title = pygame.font.SysFont("consolas", int(20*scale), bold=True)
    return f_small, f, f_mid, f_big, f_title

def fit_hex_size_dynamic(win_w, win_h, right_w, footer_h, top_h, margin, tri_size=11):
    usable_w = win_w - right_w - margin*3 - 220
    usable_h = win_h - footer_h - top_h - margin*3
    base = min(usable_w / (math.sqrt(3)*(tri_size+4)), usable_h / (1.6*(tri_size+3)))
    return max(20, int(base))

def axial_to_pixel(q,r, origin):
    x = HEX_SIZE*(math.sqrt(3)*q + math.sqrt(3)/2*r)
    y = HEX_SIZE*(1.5*r)
    return int(origin[0]+x), int(origin[1]+y)

def hex_corners(center):
    cx,cy=center; pts=[]
    for i in range(6):
        ang=math.radians(60*i-30)
        pts.append((int(cx+HEX_SIZE*math.cos(ang)), int(cy+HEX_SIZE*math.sin(ang))))
    return pts

def point_in_poly(pt,poly):
    x,y=pt; inside=False; j=len(poly)-1
    for i in range(len(poly)):
        xi,yi=poly[i]; xj,yj=poly[j]
        if ((yi>y)!=(yj>y)) and (x < (xj-xi)*(y-yi)/(yj-yi+1e-9)+xi): inside=not inside
        j=i
    return inside

def draw_gradient_bg(surf, top_color, bot_color):
    h = surf.get_height()
    grad = pygame.Surface((1, h))
    for y in range(h):
        t = y/(h-1) if h > 1 else 0  # EDGE CASE FIX: Prevent division by zero
        r = int(top_color[0]*(1-t) + bot_color[0]*t)
        g = int(top_color[1]*(1-t) + bot_color[1]*t)
        b = int(top_color[2]*(1-t) + bot_color[2]*t)
        grad.set_at((0, y), (r,g,b))
    grad = pygame.transform.smoothscale(grad, (surf.get_width(), h))
    surf.blit(grad, (0,0))

def draw_shadow(surf, rect, radius=12, spread=8, alpha=70):
    shadow = pygame.Surface((rect.w+spread*2, rect.h+spread*2), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0,0,0,alpha), shadow.get_rect(), border_radius=radius+spread//2)
    surf.blit(shadow, (rect.x-spread, rect.y-spread))

def text_with_shadow(surf, font, text, color, pos, shadow=(0,2)):
    x,y = pos
    sh = font.render(text, True, (0,0,0))
    surf.blit(sh, (x+shadow[0], y+shadow[1]))
    lbl = font.render(text, True, color)
    surf.blit(lbl, (x,y))
    return lbl.get_rect(topleft=(x,y))

def progress_bar(surf, rect, value01, fg=(120,200,255), bg=(45,48,58)):
    pygame.draw.rect(surf, bg, rect, border_radius=8)
    fill_w = int(rect.w*max(0.0, min(1.0, value01)))
    if fill_w>0:
        pygame.draw.rect(surf, fg, pygame.Rect(rect.x, rect.y, fill_w, rect.h), border_radius=8)
    pygame.draw.rect(surf, (90,96,112), rect, 2, border_radius=8)

class Button:
    def __init__(self, rect, label, hotkey:str, action:str, cost:int):
        self.r=pygame.Rect(rect); self.label=label; self.hotkey=hotkey
        self.action=action; self.cost=cost; self.enabled=True
        self.hover=False; self.pressed=False
    def draw(self,surf,font):
        base=(40,45,58)
        col = DISABLED if not self.enabled else tuple(min(255, c + (10 if self.hover else 0) + (18 if self.pressed else 0)) for c in base)
        draw_shadow(surf, self.r, radius=12, spread=6, alpha=60 if self.enabled else 30)
        pygame.draw.rect(surf,col,self.r,border_radius=12)
        pygame.draw.rect(surf,(92,100,118),self.r,2,border_radius=12)
        t = f"{self.label} [{self.hotkey}]"
        if self.cost>0: t+=f"  -{self.cost}"
        color = WHITE if self.enabled else GRAY3
        text_with_shadow(surf, font, t, color, (self.r.x+14, self.r.y+14))
    def hit(self,pos): return self.enabled and self.r.collidepoint(pos)
    def update_hover(self,mouse_pos):
        self.hover = self.r.collidepoint(mouse_pos) if self.enabled else False

class Minimap:
    def __init__(self, rect_tuple, board):
        self.rect = pygame.Rect(rect_tuple)
        self.board = board
    def draw(self, surf):
        r = self.rect
        draw_shadow(surf, r, spread=6, alpha=70)
        pygame.draw.rect(surf, (32,34,44), r, border_radius=10)
        pygame.draw.rect(surf, (88,94,112), r, 2, border_radius=10)
        text_with_shadow(surf, font_title, "MAP", WHITE, (r.x+10, r.y+6))
        padx, pady = 12, 28
        w = r.w - 2*padx
        h = r.h - pady - 10
        
        # EDGE CASE FIX: Handle empty board
        if not self.board.hexes:
            return
        
        maxq = max(p.position.q for p in self.board.hexes.values())
        maxr = max(p.position.r for p in self.board.hexes.values())
        max_r = maxr + 0.01  # Prevent division by zero
        
        for pos, hx in self.board.hexes.items():
            nx = (pos.q + pos.r*0.5) / (maxq + maxr*0.5 + 0.01)
            ny = pos.r / max_r
            cx = r.x + padx + int(nx * w)
            cy = r.y + pady + int(ny * h)
            col = OWNER_COLORS[hx.owner.value]
            pygame.draw.circle(surf, col, (cx,cy), 2)
            if hx.terrain == TerrainType.QUANTUM_NODE:
                pygame.draw.circle(surf, (198,168,240), (cx,cy), 3, 1)

# --------- Hover tooltip helpers ---------
def movement_costs_for_hex(hx: Hex, viewer_faction: FactionType):
    base_map = {
        TerrainType.PLAINS: 1.0,
        TerrainType.FOREST: 1.5,
        TerrainType.MOUNTAIN: 2.0,
        TerrainType.DESERT: 1.3,
        TerrainType.WATER: 3.0,
        TerrainType.QUANTUM_NODE: 1.0,
    }
    def cost_for(ut: UnitType):
        c = base_map[hx.terrain]
        if ut == UnitType.SCOUT:
            c *= 0.8
        if ut == UnitType.ENGINEER and hx.terrain == TerrainType.MOUNTAIN:
            c *= 0.7
        if hx.owner not in (FactionType.NEUTRAL, viewer_faction):
            c *= 1.5
        return c
    return {
        "Scout": round(cost_for(UnitType.SCOUT), 2),
        "Warrior": round(cost_for(UnitType.WARRIOR), 2),
        "Engineer": round(cost_for(UnitType.ENGINEER), 2),
        "Q.Specialist": round(cost_for(UnitType.QUANTUM_SPECIALIST), 2),
    }

def draw_hex_tooltip(screen, game, hp, mx, my):
    hx = game.board.hexes[hp]
    owner_name = hx.owner.name
    terr_name = TERRAIN_NAMES[hx.terrain.value]
    unit_count = len(hx.units)
    costs = movement_costs_for_hex(hx, game.players[game.idx].faction)

    lines_left = [
        "Terrain:", "Owner:", "Resources:", "Units:", "Quantum:", "Coords:",
        "", "Move Cost", "  • Scout", "  • Warrior", "  • Engineer", "  • Q.Specialist",
    ]
    lines_right = [
        terr_name, owner_name, str(hx.resources), str(unit_count),
        str(getattr(hx, 'quantum_charge', 0)), f"q={hp.q}, r={hp.r}",
        "", "(lower is better)", f"{costs['Scout']}", f"{costs['Warrior']}",
        f"{costs['Engineer']}", f"{costs['Q.Specialist']}",
    ]

    pad_x, pad_y, gap = 12, 10, 8
    col_gap = 16
    l_surfs = [font.render(t, True, GRAY1) for t in lines_left]
    r_surfs = [font.render(t, True, WHITE) for t in lines_right]
    col1_w = max(s.get_width() for s in l_surfs)
    col2_w = max(s.get_width() for s in r_surfs)
    total_w = pad_x*2 + col1_w + col_gap + col2_w + 6
    total_h = pad_y*2 + sum(max(l_surfs[i].get_height(), r_surfs[i].get_height()) for i in range(len(l_surfs))) + (len(l_surfs)-1)*2

    tx = min(mx + 18, WIN_W - total_w - 6)
    max_h = WIN_H - FOOTER_H - 6
    ty = min(my + 18, max_h - total_h)

    box = pygame.Rect(tx, ty, total_w, total_h)
    draw_shadow(screen, box, spread=6, alpha=90)
    pygame.draw.rect(screen, (32, 34, 44), box, border_radius=10)
    pygame.draw.rect(screen, (88, 94, 112), box, 2, border_radius=10)

    stripe_col = OWNER_COLORS[hx.owner.value]
    pygame.draw.rect(screen, stripe_col, pygame.Rect(box.x, box.y, 6, box.h), border_radius=10)

    cx1 = box.x + pad_x + 6
    cx2 = box.x + pad_x + col1_w + col_gap + 6
    cy = box.y + pad_y
    for i in range(len(l_surfs)):
        lh = max(l_surfs[i].get_height(), r_surfs[i].get_height())
        screen.blit(l_surfs[i], (cx1, cy))
        screen.blit(r_surfs[i], (cx2, cy))
        cy += lh + 2

# --------- Generic Confirm overlay ---------
def draw_confirm_overlay(screen, title, subtitle, f_big, f_mid, f_norm):
    dim = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
    dim.fill((0, 0, 0, 150))
    screen.blit(dim, (0, 0))

    mw = max(460, int(WIN_W * 0.45))
    mh = 230
    mx = WIN_W // 2 - mw // 2
    my = WIN_H // 2 - mh // 2
    box = pygame.Rect(mx, my, mw, mh)
    draw_shadow(screen, box, spread=12, alpha=100)
    pygame.draw.rect(screen, (32, 34, 44), box, border_radius=16)
    pygame.draw.rect(screen, (90, 96, 112), box, 2, border_radius=16)

    text_with_shadow(screen, f_big, title, FOCUS, (box.x + 24, box.y + 22))
    text_with_shadow(screen, f_norm, subtitle, GRAY1, (box.x + 24, box.y + 70))

    btn_w, btn_h, gap = 180, 52, 22
    bx = box.centerx - (btn_w * 2 + gap) // 2
    by = box.bottom - btn_h - 24
    yes = pygame.Rect(bx, by, btn_w, btn_h)
    no  = pygame.Rect(bx + btn_w + gap, by, btn_w, btn_h)

    draw_shadow(screen, yes, spread=8, alpha=80)
    pygame.draw.rect(screen, (40, 120, 70), yes, border_radius=12)
    pygame.draw.rect(screen, (95, 160, 120), yes, 2, border_radius=12)
    text_with_shadow(screen, f_mid, "Return Home", WHITE, (yes.x + 14, yes.y + 12))

    draw_shadow(screen, no, spread=8, alpha=80)
    pygame.draw.rect(screen, (75, 40, 44), no, border_radius=12)
    pygame.draw.rect(screen, (140, 88, 92), no, 2, border_radius=12)
    text_with_shadow(screen, f_mid, "Cancel", WHITE, (no.x + 44, no.y + 12))

    return {"yes": yes, "no": no}

# --------- Game Over overlay ---------
def draw_game_over_overlay(screen, winner_faction):
    dim = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
    dim.fill((0, 0, 0, 150))
    screen.blit(dim, (0, 0))

    title = f"WINNER: {winner_faction.name}" if winner_faction else "DRAW"
    mw = max(460, int(WIN_W * 0.45))
    mh = 260
    mx = WIN_W // 2 - mw // 2
    my = WIN_H // 2 - mh // 2
    box = pygame.Rect(mx, my, mw, mh)
    draw_shadow(screen, box, spread=12, alpha=100)
    pygame.draw.rect(screen, (32, 34, 44), box, border_radius=16)
    pygame.draw.rect(screen, (90, 96, 112), box, 2, border_radius=16)

    text_with_shadow(screen, font_big, title, FOCUS, (box.x + 24, box.y + 24))
    text_with_shadow(screen, font, "Press  R  to play again   •   Press  Esc  to return home", GRAY1, (box.x + 24, box.y + 74))

    btn_w, btn_h, gap = 180, 58, 22
    bx = box.centerx - (btn_w * 2 + gap) // 2
    by = box.bottom - btn_h - 28
    restart = pygame.Rect(bx, by, btn_w, btn_h)
    exitb   = pygame.Rect(bx + btn_w + gap, by, btn_w, btn_h)

    draw_shadow(screen, restart, spread=8, alpha=80)
    pygame.draw.rect(screen, (40, 120, 70), restart, border_radius=12)
    pygame.draw.rect(screen, (95, 160, 120), restart, 2, border_radius=12)
    text_with_shadow(screen, font_mid, "Play Again", WHITE, (restart.x + 28, restart.y + 14))

    draw_shadow(screen, exitb, spread=8, alpha=80)
    pygame.draw.rect(screen, (75, 40, 44), exitb, border_radius=12)
    pygame.draw.rect(screen, (140, 88, 92), exitb, 2, border_radius=12)
    text_with_shadow(screen, font_mid, "Home", WHITE, (exitb.x + 62, exitb.y + 14))

    return {"restart": restart, "exit": exitb}

# ------------- Layout recalculation -------------
def recalc_layout(win_w, win_h):
    global WIN_W, WIN_H, RIGHT_PANEL_W, FOOTER_H, TOPBAR_H, MARGIN, HEX_SIZE
    global footer_rect, right_rect, MAP_ORIGIN, btns, minimap
    global font_small, font, font_mid, font_big, font_title

    WIN_W, WIN_H = win_w, win_h

    # RIGHT PANEL: Always 50% of screen width
    RIGHT_PANEL_W = int(WIN_W * 0.4)
    
    compact = WIN_H <= 800
    MARGIN = 16 if compact else 20
    TOPBAR_H = 56 if compact else 70
    FOOTER_H = 90 if compact else 110

    # Calculate available space for map (LEFT side - 50% of screen)
    map_area_width = WIN_W - RIGHT_PANEL_W - MARGIN * 3  # Left 50% minus margins
    map_area_height = WIN_H - FOOTER_H - TOPBAR_H - MARGIN * 2
    
    # Calculate HEX_SIZE to use 95% of available space
    HEX_SIZE = fit_hex_size_dynamic(WIN_W, WIN_H, RIGHT_PANEL_W, FOOTER_H, TOPBAR_H, MARGIN)
    HEX_SIZE = int(HEX_SIZE * 1.0)  # Scale to 95% for visibility
    
    font_small, font, font_mid, font_big, font_title = compute_fonts(WIN_H)

    # Calculate map bounds to center it in the LEFT 50% area
    # Assuming 11x11 hex grid
    max_hex_width = HEX_SIZE * math.sqrt(3) * 12
    max_hex_height = HEX_SIZE * 1.5 * 12
    
    # Center the map horizontally and vertically in the left area
    map_x_offset = MARGIN + (map_area_width - max_hex_width) / 2
    map_y_offset = TOPBAR_H + MARGIN + (map_area_height - max_hex_height) / 2
    
    MAP_ORIGIN = (int(map_x_offset), int(map_y_offset))
    
    # Footer spans full width
    footer_rect = pygame.Rect(0, WIN_H-FOOTER_H, WIN_W, FOOTER_H)
    
    # Right panel: 50% of screen, starting from middle
    right_rect = pygame.Rect(WIN_W - RIGHT_PANEL_W - MARGIN, 
                             TOPBAR_H + MARGIN,
                             RIGHT_PANEL_W, 
                             WIN_H - FOOTER_H - TOPBAR_H - 2*MARGIN)

    # Minimap: Make it BIGGER - 25% of LEFT side width
    map_area_width_actual = WIN_W - RIGHT_PANEL_W
    mini_w = int(map_area_width_actual * 0.25)  # 25% of left area
    mini_w = max(180, min(mini_w, 300))  # Clamp between 180-300px
    mini_h = int(mini_w * 0.9)  # Slightly taller ratio
    
    mini_x = MARGIN
    mini_y = WIN_H - FOOTER_H - mini_h - MARGIN - 10
    if minimap:
        minimap.rect = pygame.Rect(mini_x, mini_y, mini_w, mini_h)

    # Footer buttons span full width
    footer_usable_width = WIN_W - MARGIN*2
    btn_gap = 12 if compact else 14
    btn_w = (footer_usable_width - btn_gap*3) // 4
    btn_h = 60 if compact else 76
    btn_y = WIN_H - FOOTER_H + (18 if compact else 36)

    labels = ["Expand","Build","Economy","End Turn"]
    hotkeys = ["E","B","C","SPACE"]
    actions = ["expand","build","economy","end"]
    costs   = [30,40,25,0]

    if btns:
        old = [(b.hover,b.pressed,b.enabled) for b in btns]
        btns.clear()
        for i in range(4):
            btns.append(Button((MARGIN + (btn_w+btn_gap)*i, btn_y, btn_w, btn_h),
                               labels[i], hotkeys[i], actions[i], costs[i]))
        for b, st in zip(btns, old):
            b.hover, b.pressed, b.enabled = st
    else:
        for i in range(4):
            btns.append(Button((MARGIN + (btn_w+btn_gap)*i, btn_y, btn_w, btn_h),
                               labels[i], hotkeys[i], actions[i], costs[i]))

# ---------------------------- Menu ----------------------------
def choose_mode(screen, font_big_local, font_mid_local, font_small_local):
    """
    Home screen:
      - 1/2/3 keys select modes
      - Manual / How-to opens overlay with 3 pages (Left/Right to navigate)
      - Exit only via the red button (Esc does NOTHING here)
    """
    manual_open = False
    manual_page = 0  # 0..2

    # ----- Manual content: 3 pages -----
    manual_pages: List[List[str]] = [
        [   # Page 1 — Overview & Goals
            "HOW TO PLAY — Quantum Territory Wars",
            "",
            " Goal",
            "Win by any ONE of the following:",
            " • Territorial Victory — Control 18 hexes.",
            " • Quantum Victory — Control all 5 Quantum Nodes.",
            " • Economic Victory — Reach 600 resources.",
            "",
            " Setup",
            "• Random hex map each game with 5 Quantum Nodes.",
            "• Factions: Expansion Empire (Blue), Tech Collective (Red), Adaptive Alliance (Green).",
            "• Starts and terrain are randomized every match.",
            "",
            " Mode Select on Home",
            "• Press 1 = Human vs 2 AI",
            "• Press 2 = 2 Humans vs 1 AI",
            "• Press 3 = 3 Humans",
        ],
        [   # Page 2 — Movement, AI, Economy
            " Terrain & Movement (A* Pathfinding)",
            "• Plains: easy | Forest: slower | Mountains: very slow",
            "• Desert: moderate cost | Water: hard to cross",
            "• Quantum Node (purple): strategic objective",
            "• Units move using A*; borders/ownership affect cost.",
            "",
            " AI (Minimax + Fuzzy Evaluation)",
            "• Alpha–beta minimax evaluates actions per turn.",
            "• Fuzzy score balances Resources, Territories, Quantum Nodes, Units.",
            "• Bonus for near-victory states.",
            "",
            " Income",
            "• After each full round: +10 base +2 per owned territory.",
            "",
            " Interface",
            "• Top Bar: Turn info & hints.",
            "• Right Panel: Player cards (Res, Terr, Units, QN) + Turn Log.",
            "• Bottom Bar: Action buttons + hotkeys.",
            "• Minimap: Bottom-left overview.",
        ],
        [   # Page 3 — Actions & Controls
            " Actions (per turn)",
            "• Expand  [E / Button] — Cost 30 → Enter target mode; click a glowing neutral hex to claim.",
            "• Build   [B / Button] — Cost 40 → Train a Warrior on one of your owned hexes.",
            "• Economy [C / Button] — Cost 25 → Quick trade: +40 resources.",
            "• End Turn [Space / Button] → Pass to next player.",
            "",
            " Tips",
            "• Expand early for income.",
            "• Guard Quantum Nodes—they swing games.",
            "• Balance Economy and Build.",
            "",
            " Controls",
            "• E/B/C/Space → Actions   • Esc (in match) → Return Home confirm",
            "• R (Game Over) → Restart",
            "",
            " Manual Navigation",
            "• Left / Right Arrow → Prev / Next page",
            "• Esc → Close Manual",
        ],
    ]

    def draw_manual_overlay(page_idx: int):
        overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        mw = max(720, int(WIN_W * 0.66))
        mh = min(600, int(WIN_H * 0.80))
        box = pygame.Rect(WIN_W // 2 - mw // 2, WIN_H // 2 - mh // 2, mw, mh)

        pygame.draw.rect(screen, (32, 34, 44), box, border_radius=16)
        pygame.draw.rect(screen, (90, 96, 112), box, 2, border_radius=16)

        # Header
        title = "MANUAL — Page {}/3".format(page_idx+1)
        text_with_shadow(screen, font_big_local, title, FOCUS, (box.x + 24, box.y + 20))

        # Body text
        x = box.x + 26
        y = box.y + 72
        max_w = box.w - 52
        line_gap = 4

        def blit_wrapped(text, color, y_pos, font_obj):
            words = text.split(" ")
            cur = ""
            ypos = y_pos
            for w in words:
                test = (cur + " " + w).strip()
                if font_obj.size(test)[0] > max_w:
                    screen.blit(font_obj.render(cur, True, color), (x, ypos))
                    ypos += font_obj.get_height() + line_gap
                    cur = w
                else:
                    cur = test
            if cur:
                screen.blit(font_obj.render(cur, True, color), (x, ypos))
                ypos += font_obj.get_height() + line_gap
            return ypos

        for ln in manual_pages[page_idx]:
            if not ln:
                y += 6
                continue
            # headings (emoji or all caps words at line start)
            if ln.startswith(("🎯","🕹️","🌍","🧠","💼","💰","🖥️","🧩","⌨️","📖")) or ln.isupper():
                y = blit_wrapped(ln, FOCUS, y, font_mid_local)
            elif ln.startswith(("•"," -","• ")):
                y = blit_wrapped(ln, WHITE, y, font_small_local)
            else:
                y = blit_wrapped(ln, WHITE, y, font_small_local)
            if y > box.bottom - 80:
                break

        # Footer controls
        footer_text = "← Prev     → Next     Esc Close"
        ft = font_small_local.render(footer_text, True, GRAY2)
        screen.blit(ft, (box.centerx - ft.get_width()//2, box.bottom - ft.get_height() - 12))

        # Prev / Next buttons
        btn_w, btn_h = 120, 44
        prev_rect = pygame.Rect(box.x + 18, box.bottom - btn_h - 14, btn_w, btn_h)
        next_rect = pygame.Rect(box.right - btn_w - 18, box.bottom - btn_h - 14, btn_w, btn_h)

        # Prev
        draw_shadow(screen, prev_rect, spread=6, alpha=70)
        pygame.draw.rect(screen, (38, 42, 55), prev_rect, border_radius=12)
        pygame.draw.rect(screen, (92, 100, 118), prev_rect, 2, border_radius=12)
        text_with_shadow(screen, font_mid_local, "Prev", WHITE, (prev_rect.x + 34, prev_rect.y + 8))

        # Next
        draw_shadow(screen, next_rect, spread=6, alpha=70)
        pygame.draw.rect(screen, (38, 42, 55), next_rect, border_radius=12)
        pygame.draw.rect(screen, (92, 100, 118), next_rect, 2, border_radius=12)
        text_with_shadow(screen, font_mid_local, "Next", WHITE, (next_rect.x + 34, next_rect.y + 8))

        return box, prev_rect, next_rect

    def draw_menu():
        draw_gradient_bg(screen, BG_TOP, BG_BOT)

        title_text = "QUANTUM TERRITORY WARS"
        title_surf = font_big_local.render(title_text, True, FOCUS)
        title_x = (WIN_W - title_surf.get_width()) // 2
        title_y = 60
        screen.blit(title_surf, (title_x, title_y))

        subtitle_text = "Select Game Mode"
        subtitle_surf = font_mid_local.render(subtitle_text, True, WHITE)
        subtitle_x = (WIN_W - subtitle_surf.get_width()) // 2
        subtitle_y = title_y + title_surf.get_height() + 8
        screen.blit(subtitle_surf, (subtitle_x, subtitle_y))

        underline_w = max(subtitle_surf.get_width(), 280)
        ux = (WIN_W - underline_w) // 2
        uy = subtitle_y + subtitle_surf.get_height() + 6
        pygame.draw.line(screen, (90, 96, 112), (ux, uy), (ux + underline_w, uy), 2)

        col_w = min(560, WIN_W - 2 * MARGIN - 80)
        x = WIN_W // 2 - col_w // 2
        y = uy + 40

        opts = [
            ("1 Human vs 2 AI", "Strategic Challenge", [False, True, True]),
            ("2 Humans vs 1 AI", "Cooperative Play",   [False, False, True]),
            ("3 Humans",         "Pure Strategy",      [False, False, False]),
        ]
        rects = []
        for title, sub, mode in opts:
            r = pygame.Rect(x, y, col_w, 80)
            draw_shadow(screen, r, spread=8, alpha=80)
            pygame.draw.rect(screen, (38, 42, 55), r, border_radius=12)
            pygame.draw.rect(screen, (92, 100, 118), r, 2, border_radius=12)
            text_with_shadow(screen, font_mid_local, title, WHITE, (r.x + 18, r.y + 16))
            text_with_shadow(screen, font_small_local, sub, GRAY2, (r.x + 18, r.y + 46))
            rects.append((r, mode))
            y += 98

        # Manual button
        manual_rect = pygame.Rect(x, y + 8, col_w, 70)
        draw_shadow(screen, manual_rect, spread=8, alpha=80)
        pygame.draw.rect(screen, (40, 70, 110), manual_rect, border_radius=12)
        pygame.draw.rect(screen, (100, 130, 170), manual_rect, 2, border_radius=12)
        text_with_shadow(screen, font_mid_local, "Manual / How to Play", WHITE, (manual_rect.x + 18, manual_rect.y + 14))
        text_with_shadow(screen, font_small_local, "Click to open", GRAY1, (manual_rect.x + 18, manual_rect.y + 40))

        # Exit button
        exit_rect = pygame.Rect(x, y + 98, col_w, 70)
        draw_shadow(screen, exit_rect, spread=8, alpha=80)
        pygame.draw.rect(screen, (60, 36, 40), exit_rect, border_radius=12)
        pygame.draw.rect(screen, (150, 90, 96), exit_rect, 2, border_radius=12)
        text_with_shadow(screen, font_mid_local, "Exit Game", WHITE, (exit_rect.x + 18, exit_rect.y + 14))
        text_with_shadow(screen, font_small_local, "Close the application", GRAY1, (exit_rect.x + 18, exit_rect.y + 40))

        return rects, manual_rect, exit_rect

    rects, manual_rect, exit_rect = draw_menu()
    manual_box=None
    prev_btn=None
    next_btn=None
    pygame.display.flip()

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)

            if manual_open:
                # Navigation inside manual
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        manual_open=False
                    elif e.key == pygame.K_RIGHT:
                        manual_page = min(2, manual_page+1)
                    elif e.key == pygame.K_LEFT:
                        manual_page = max(0, manual_page-1)
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    # click buttons
                    if prev_btn and prev_btn.collidepoint(e.pos):
                        manual_page = max(0, manual_page-1)
                    elif next_btn and next_btn.collidepoint(e.pos):
                        manual_page = min(2, manual_page+1)
                    else:
                        # click outside the panel closes
                        if manual_box and not manual_box.collidepoint(e.pos):
                            manual_open=False

                # Redraw while manual open
                rects, manual_rect, exit_rect = draw_menu()
                manual_box, prev_btn, next_btn = draw_manual_overlay(manual_page)
                pygame.display.flip()
                continue

            # --- Title page interactions ---
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for r, m in rects:
                    if r.collidepoint(e.pos):
                        return m
                if manual_rect.collidepoint(e.pos):
                    manual_open=True
                    manual_page=0
                    rects, manual_rect, exit_rect = draw_menu()
                    manual_box, prev_btn, next_btn = draw_manual_overlay(manual_page)
                    pygame.display.flip()
                    continue
                if exit_rect.collidepoint(e.pos):
                    pygame.quit(); sys.exit(0)

            if e.type == pygame.KEYDOWN:
                # ESC does nothing on title page (per your rule)
                if e.key in (pygame.K_1, pygame.K_KP1): return [False, True, True]
                if e.key in (pygame.K_2, pygame.K_KP2): return [False, False, True]
                if e.key in (pygame.K_3, pygame.K_KP3): return [False, False, False]

        rects, manual_rect, exit_rect = draw_menu()
        if manual_open:
            manual_box, prev_btn, next_btn = draw_manual_overlay(manual_page)
        pygame.display.flip()

# ---------------------------- Game Loop (single match) ----------------------------
def play_match(screen, initial_mode) -> bool:
    """
    Runs one match. Returns:
      True  -> user chose 'Return Home' (go back to menu)
      False -> window closed (caller should quit app)
    """
    clock=pygame.time.Clock()

    # create game
    game=Game(initial_mode)

    global minimap
    minimap = Minimap((MARGIN, WIN_H-FOOTER_H-170, 165, 150), game.board)

    # layout & precompute
    recalc_layout(WIN_W, WIN_H)
    hex_centers={pos:axial_to_pixel(pos.q,pos.r,MAP_ORIGIN) for pos in game.board.hexes}

    selected:Optional[Position]=None
    sel_pulse_t = 0.0
    go_buttons = None
    confirm_open = False
    confirm_buttons = None
    return_home = False

    # --- targeted expand state ---
    targeting_expand = False
    expand_candidates: set[Position] = set()
    
    targeting_build = False
    build_candidates: set[Position] = set()

    def hex_at(pos):
        for p,ctr in hex_centers.items():
            if point_in_poly(pos, hex_corners(ctr)):
                return p
        return None

    def draw_topbar():
        bar = pygame.Rect(0, 0, WIN_W, TOPBAR_H)
        
        # Gradient background for modern look
        pygame.draw.rect(screen, (20, 22, 30), bar)
        pygame.draw.line(screen, (55, 58, 70), (0, TOPBAR_H - 1), (WIN_W, TOPBAR_H - 1), 2)
        
        # Left side: Game title
        title = "Quantum Territory Wars"
        title_x = MARGIN + 10
        title_y = TOPBAR_H // 2 - font_big.get_height() // 2
        text_with_shadow(screen, font_big, title, FOCUS, (title_x, title_y))
        
        # Center: Turn counter (prominent)
        turn_text = f"TURN {game.turn}"
        turn_surf = font_title.render(turn_text, True, WHITE)
        turn_x = (WIN_W - turn_surf.get_width()) // 2
        turn_y = TOPBAR_H // 2 - turn_surf.get_height() // 2
        
        # Turn counter background badge
        badge_padding = 12
        badge_rect = pygame.Rect(
            turn_x - badge_padding, 
            turn_y - 6, 
            turn_surf.get_width() + badge_padding * 2, 
            turn_surf.get_height() + 12
        )
        pygame.draw.rect(screen, (40, 45, 58), badge_rect, border_radius=8)
        pygame.draw.rect(screen, (90, 96, 112), badge_rect, 2, border_radius=8)
        text_with_shadow(screen, font_title, turn_text, WHITE, (turn_x, turn_y))
        
        # Right side: Current player info
        cur_player = game.players[game.idx]
        player_text = f"{cur_player.faction.name}"
        player_color = OWNER_COLORS[cur_player.faction.value]
        
        # Calculate position (right-aligned with margin)
        player_surf = font_mid.render(player_text, True, player_color)
        player_x = WIN_W - MARGIN - player_surf.get_width() - 10
        player_y = TOPBAR_H // 2 - player_surf.get_height() // 2
        
        # Player indicator badge
        player_badge_rect = pygame.Rect(
            player_x - 10, 
            player_y - 6, 
            player_surf.get_width() + 20, 
            player_surf.get_height() + 12
        )
        pygame.draw.rect(screen, (40, 45, 58), player_badge_rect, border_radius=8)
        pygame.draw.rect(screen, player_color, player_badge_rect, 2, border_radius=8)
        text_with_shadow(screen, font_mid, player_text, player_color, (player_x, player_y))
        
        # Action hints (below main bar, if targeting)
        if targeting_expand or targeting_build:
            hint_y = TOPBAR_H - 28
            
            if targeting_expand:
                msg = "Click a highlighted hex to Expand  •  Press ESC to cancel"
                msg_color = FOCUS
            else:  # targeting_build
                msg = "Click a highlighted hex to Build Warrior  •  Press ESC to cancel"
                msg_color = (120, 200, 255)
            
            # Center the hint message
            msg_surf = font.render(msg, True, msg_color)
            msg_x = (WIN_W - msg_surf.get_width()) // 2
            
            # Hint background (subtle)
            hint_bg_rect = pygame.Rect(msg_x - 10, hint_y - 4, msg_surf.get_width() + 20, msg_surf.get_height() + 8)
            pygame.draw.rect(screen, (30, 32, 40, 180), hint_bg_rect, border_radius=6)
            
            text_with_shadow(screen, font, msg, msg_color, (msg_x, hint_y))

    def draw_map(dt):
        nonlocal sel_pulse_t
        for pos,hx in game.board.hexes.items():
            c=hex_centers[pos]; pts=hex_corners((c[0]+2,c[1]+2))
            pygame.draw.polygon(screen,(0,0,0,22),pts)

        for pos,hx in game.board.hexes.items():
            c=hex_centers[pos]; pts=hex_corners(c)
            fill=TERRAIN_FILL[hx.terrain.value]
            pygame.draw.polygon(screen, fill, pts)
            rim=OWNER_COLORS[hx.owner.value]
            pygame.draw.polygon(screen, rim, pts, 3)
            pygame.draw.polygon(screen, (255,255,255,12), pts, 1)

            if hx.terrain==TerrainType.QUANTUM_NODE:
                glow_r = 12
                s=pygame.Surface((glow_r*4, glow_r*4), pygame.SRCALPHA)
                pygame.draw.circle(s,(180,140,255,55),(2*glow_r,2*glow_r), 2*glow_r)
                screen.blit(s,(c[0]-2*glow_r, c[1]-2*glow_r))
                pygame.draw.circle(screen,(250,236,255),c,6)
                pygame.draw.circle(screen,(120,85,180),c,6,2)

        for p in game.players:
            uc=OWNER_COLORS[p.faction.value]
            hex_groups: Dict[Tuple[int,int], List[Unit]]={}
            for u in p.units:
                hex_groups.setdefault((u.position.q,u.position.r), []).append(u)
            for (q,r), units in hex_groups.items():
                c=hex_centers[Position(q,r)]
                pygame.draw.circle(screen, uc, c, 10)
                pygame.draw.circle(screen, (30,30,32), c, 10, 2)
                u0 = units[0]
                maxh = u0.get_max_health()
                frac = max(0.0, min(1.0, u0.health/maxh))
                arc_rect = pygame.Rect(c[0]-12, c[1]-12, 24, 24)
                pygame.draw.arc(screen, (255,255,255), arc_rect, -math.pi/2, -math.pi/2 + 2*math.pi*frac, 3)
                if len(units)>1:
                    badge = pygame.Rect(c[0]+8, c[1]-14, 20, 18)
                    pygame.draw.rect(screen, (28,30,38), badge, border_radius=6)
                    pygame.draw.rect(screen, (90,96,112), badge, 1, border_radius=6)
                    screen.blit(font.render(str(len(units)), True, WHITE), (badge.x+6, badge.y+1))

        if selected and selected in hex_centers:
            sel_pulse_t = (sel_pulse_t + dt*0.004) % 1.0
            c = hex_centers[selected]
            pygame.draw.polygon(screen, FOCUS, hex_corners(c), 2)
            radius = int(14 + 6*math.sin(sel_pulse_t*2*math.pi))
            s=pygame.Surface((radius*2+4, radius*2+4), pygame.SRCALPHA)
            pygame.draw.circle(s,(255,240,150,90),(radius+2,radius+2),radius,2)
            screen.blit(s,(c[0]-radius-2, c[1]-radius-2))

        if game.last_action_feedback:
            (cx,cy),ttl=game.last_action_feedback
            r=int(14 + (1-ttl/0.5)*10)
            s=pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
            pygame.draw.circle(s,(255,240,150,120),(r+2,r+2),r,2)
            screen.blit(s,(cx-r-2, cy-r-2))
            ttl-=dt/1000.0
            if ttl<=0: game.last_action_feedback=None
            else: game.last_action_feedback=((cx,cy),ttl)

        if targeting_expand:
            surf = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
            for pos in expand_candidates:
                c = hex_centers[pos]
                pygame.draw.polygon(surf, (255,235,120,90), hex_corners(c), 0)
                pygame.draw.polygon(surf, (255,255,255,180), hex_corners(c), 2)
            screen.blit(surf, (0,0))
            
        if targeting_build:
            surf = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
            for pos in build_candidates:
                c = hex_centers[pos]
                pygame.draw.polygon(surf, (120,200,255,90), hex_corners(c), 0)
                pygame.draw.polygon(surf, (255,255,255,180), hex_corners(c), 2)
            screen.blit(surf, (0,0))

    def draw_right():
        draw_shadow(screen, right_rect, spread=10, alpha=80)
        pygame.draw.rect(screen, PANEL_BG, right_rect, border_radius=12)
        pygame.draw.rect(screen, PANEL_STROKE, right_rect, 2, border_radius=12)
        
        # Responsive padding based on panel width
        pad = int(right_rect.w * 0.05)  # 5% padding
        x = right_rect.x + pad
        y = right_rect.y + pad

        text_with_shadow(screen, font_title, "PLAYERS", WHITE, (x, y))
        y += 36

        for i, p in enumerate(game.players):
            is_now = (i == game.idx)
            
            # BIGGER CARDS - Taller and wider with responsive sizing
            card_w = right_rect.w - (pad * 2)
            card_h = 140  # Increased from 96 to 140 for more space
            card = pygame.Rect(x, y, card_w, card_h)
            
            draw_shadow(screen, card, spread=8, alpha=70 if is_now else 40)
            pygame.draw.rect(screen, (34, 36, 46), card, border_radius=12)
            pygame.draw.rect(screen, (90, 96, 112), card, 2, border_radius=12)

            # Faction name - truncate if needed
            name = p.faction.name
            if card.w < 350:  # Abbreviate on narrow screens
                name = name[:15] + "..." if len(name) > 15 else name
            full_name = f"{name}  [{'AI' if p.is_ai else 'HUMAN'}]"
            text_with_shadow(screen, font_mid, full_name, OWNER_COLORS[p.faction.value], (card.x + pad, card.y + 10))

            # Split stats into TWO lines for better readability
            line1 = f"Resources: {p.resources}  |  Territories: {p.territories_controlled}"
            line2 = f"Units: {len(p.units)}  |  Quantum: {p.quantum_nodes_controlled}  |  Econ: {p.economy_uses}/3  |  Build: {p.build_uses}/1"
            
            # Render stats on two lines
            screen.blit(font_small.render(line1, True, GRAY1), (card.x + pad, card.y + 35))
            screen.blit(font_small.render(line2, True, GRAY1), (card.x + pad, card.y + 52))

            # Progress bars - bigger and better positioned
            bar_w = card.w - (pad * 2)
            bar_h = 14  # Slightly taller bars
            bar_y_start = card.y + 75
            
            # Resources bar
            progress_bar(screen, pygame.Rect(card.x + pad, bar_y_start, bar_w, bar_h),
                        min(1.0, p.resources / 600.0), fg=(120, 200, 255))
            
            # Territories bar
            progress_bar(screen, pygame.Rect(card.x + pad, bar_y_start + 20, bar_w, bar_h),
                        min(1.0, p.territories_controlled / 18.0), fg=SUCCESS)
            
            # Quantum nodes bar
            progress_bar(screen, pygame.Rect(card.x + pad, bar_y_start + 40, bar_w, bar_h),
                        min(1.0, p.quantum_nodes_controlled / 5.0), fg=(198, 168, 240))

            # Current player glow effect
            if is_now:
                glow = pygame.Surface((card.w, card.h), pygame.SRCALPHA)
                pygame.draw.rect(glow, (255, 235, 140, 40), glow.get_rect(), border_radius=12)
                screen.blit(glow, (card.x, card.y))
            
            y += card.h + 16  # More spacing between cards

        # Turn Log section
        y += 10
        text_with_shadow(screen, font_title, "TURN LOG", WHITE, (x, y))
        y += 32
        log_bottom = right_rect.bottom - pad
        
        # Calculate max characters based on panel width
        max_chars = int(card_w / 7)  # Roughly 7 pixels per character
        
        for m in game.log[::-1]:
            if y + 22 > log_bottom:
                break
            # Truncate log messages to fit width
            truncated = ("• " + m)[:max_chars]
            screen.blit(font_small.render(truncated, True, GRAY2), (x, y))
            y += 22
        
    def draw_footer(mouse_pos):
        draw_shadow(screen, footer_rect, spread=10, alpha=80)
        pygame.draw.rect(screen,(22,24,30),footer_rect)
        pygame.draw.rect(screen,(78,86,104),footer_rect,2)

        cur=game.players[game.idx]
        is_human=not cur.is_ai and not game.game_over
        for b in btns:
            b.update_hover(mouse_pos)
            if not is_human or targeting_expand or targeting_build:
                b.enabled=False
            else:
                if b.action=="end": b.enabled=True
                elif b.action=="expand": b.enabled=game.affordable(30)
                elif b.action=="build": b.enabled=game.affordable(40) and cur.build_uses<1
                elif b.action=="economy": b.enabled=game.affordable(25) and cur.economy_uses<3
            b.draw(screen,font_mid)

    # Removed status text - info is already in the right panel

    # ----------- Main loop -----------
    AI_DELAY = 260
    last_ai_time = 0
    running=True
    while running:
        dt=clock.tick(60)
        mouse_pos = pygame.mouse.get_pos()
        for e in pygame.event.get():
            if e.type==pygame.QUIT:
                return False

            if confirm_open:
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and confirm_buttons:
                    if confirm_buttons["yes"].collidepoint(e.pos):
                        return_home = True
                        running = False
                        continue
                    if confirm_buttons["no"].collidepoint(e.pos):
                        confirm_open=False; confirm_buttons=None
                        continue
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_y, pygame.K_RETURN):
                        return_home = True; running=False; continue
                    if e.key in (pygame.K_n, pygame.K_ESCAPE):
                        confirm_open=False; confirm_buttons=None; continue
                continue

            if game.game_over:
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and go_buttons:
                    if go_buttons["restart"].collidepoint(e.pos):
                        return play_match(screen, initial_mode)
                    if go_buttons["exit"].collidepoint(e.pos):
                        return_home = True
                        running = False
                        continue

                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_ESCAPE, pygame.K_q):
                        return_home = True
                        running = False
                        continue
                    if e.key == pygame.K_r:
                        return play_match(screen, initial_mode)

            elif e.type == pygame.VIDEORESIZE:
                new_w = max(1024, e.w)
                new_h = max(720,  e.h)
                screen = pygame.display.set_mode((new_w, new_h), pygame.RESIZABLE)
                recalc_layout(new_w, new_h)
                hex_centers = {pos:axial_to_pixel(pos.q,pos.r,MAP_ORIGIN) for pos in game.board.hexes}

            elif e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                mx,my=e.pos

                if targeting_expand and my < WIN_H-FOOTER_H:
                    hp=hex_at((mx,my))
                    if hp and hp in expand_candidates:
                        if game.apply_expand_to(game.players[game.idx].faction, hp, cost=30):
                            if hp in hex_centers:
                                game.last_action_feedback=(hex_centers[hp],0.5)
                            game.check_victory()
                            targeting_expand=False
                            expand_candidates.clear()
                            if not game.game_over:
                                game.next_turn()
                        continue
                    
                if targeting_build and my < WIN_H-FOOTER_H:
                    hp=hex_at((mx,my))
                    if hp and hp in build_candidates:
                        if game.apply_build_to(game.players[game.idx].faction, hp, cost=40):
                            if hp in hex_centers:
                                game.last_action_feedback=(hex_centers[hp],0.5)
                            game.check_victory()
                            targeting_build=False
                            build_candidates.clear()
                            if not game.game_over:
                                game.next_turn()
                        continue

                if my < WIN_H-FOOTER_H:
                    hp=hex_at((mx,my))
                    if hp: selected=hp

                if footer_rect.collidepoint((mx,my)):
                    cur=game.players[game.idx]
                    if not cur.is_ai and not game.game_over and not targeting_expand:
                        for b in btns:
                            if b.hit((mx,my)):
                                if b.action=="expand":
                                    targeting_expand=True
                                    expand_candidates = game.expand_candidates(cur.faction)
                                elif b.action=="build":
                                    targeting_build=True
                                    build_candidates = game.build_candidates(cur.faction)
                                else:
                                    pos=game.apply(b.action,b.cost, selected)
                                    if pos and pos in hex_centers:
                                        game.last_action_feedback=(hex_centers[pos],0.5)
                                    game.check_victory()
                                    if not game.game_over:
                                        game.next_turn()
                                break

            elif e.type==pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    if targeting_expand:
                        targeting_expand=False
                        expand_candidates.clear()
                    elif targeting_build:
                        targeting_build=False
                        build_candidates.clear()
                    else:
                        confirm_open = True
                    continue

                if not game.game_over:
                    cur=game.players[game.idx]
                    if not cur.is_ai:
                        if not targeting_expand and not targeting_build:
                            if e.key==pygame.K_e:
                                targeting_expand=True
                                expand_candidates = game.expand_candidates(cur.faction)
                            elif e.key==pygame.K_b:
                                targeting_build=True
                                build_candidates = game.build_candidates(cur.faction)
                            elif e.key==pygame.K_c:
                                game.apply("economy",25, selected)
                                game.check_victory()
                                if not game.game_over: game.next_turn()
                            elif e.key==pygame.K_SPACE:
                                game.apply("end",0, selected)
                                game.check_victory()
                                if not game.game_over: game.next_turn()

        if not game.game_over and not confirm_open and not targeting_expand and not targeting_build and game.players[game.idx].is_ai:
            if pygame.time.get_ticks() - last_ai_time > AI_DELAY:
                p=game.players[game.idx]
                st=GameState(game.board, game.players, game.idx, game.turn)
                mv=game.ai[p.faction].best(st)
                pos=game.apply(mv[0], mv[1])
                if pos and pos in hex_centers: game.last_action_feedback=(hex_centers[pos],0.5)
                game.check_victory()
                if not game.game_over: game.next_turn()
                last_ai_time = pygame.time.get_ticks()

        draw_gradient_bg(screen, BG_TOP, BG_BOT)
        draw_topbar()
        draw_map(dt)
        minimap.draw(screen)
        draw_right()
        draw_footer(mouse_pos)

        if game.game_over:
            go_buttons = draw_game_over_overlay(screen, game.winner)
        else:
            go_buttons = None

        if confirm_open:
            confirm_buttons = draw_confirm_overlay(
                screen, "Return to Home?", "Your current match will be abandoned.", font_big, font_mid, font
            )

        pygame.display.flip()

    return True if return_home else False

# ---------------------------- App Runner ----------------------------
def run():
    pygame.init()
    flags = pygame.RESIZABLE
    screen=pygame.display.set_mode((WIN_W,WIN_H), flags)
    pygame.display.set_caption("Quantum Territory Wars — UI v9.1 (EDGE CASES FIXED)")

    font_small_temp, _, font_mid_temp, font_big_temp, _ = compute_fonts(WIN_H)

    while True:
        mode = choose_mode(screen, font_big_temp, font_mid_temp, font_small_temp)
        go_home = play_match(screen, mode)
        if not go_home:
            break

    pygame.quit()

if __name__=="__main__":
    run()