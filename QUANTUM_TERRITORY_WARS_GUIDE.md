# Quantum Territory Wars - Complete Game Guide

## What is This Game?

**Quantum Territory Wars** is a turn-based strategy game where 3 factions compete to dominate a hexagonal map. Think of it like a mix of *Risk* and *Civilization* but faster-paced. You'll expand your territory, build armies, manage resources, and race to achieve one of three victory conditions before your opponents!

---

## Quick Start

### Game Modes (Choose on Title Screen)
- Press **1**: Play alone vs 2 AI opponents
- Press **2**: Play with a friend vs 1 AI
- Press **3**: Play with 2 friends (no AI)

---

## How to Win (3 Victory Conditions)

You can win the game in **THREE DIFFERENT WAYS** - achieve any ONE of these:

1. **Territorial Victory**: Control **18 hexes** on the map
2. **Quantum Victory**: Control all **5 Quantum Nodes** (special purple hexes)
3. **Economic Victory**: Accumulate **600 resources**

---

## The Factions (Players)

There are 3 factions competing:

| Faction | Color | Description |
|---------|-------|-------------|
| **Expansion Empire** | Blue | Player 1 - Focuses on territorial growth |
| **Tech Collective** | Red | Player 2 - Technology-focused |
| **Adaptive Alliance** | Green | Player 3 - Balanced strategy |

Each faction has the same abilities - the differences are just thematic!

---

## Understanding the Map

### Map Layout
- The map is made of **hexagonal tiles** (hexes)
- Each game generates a **random map** with different terrain
- Map size: **11x11 hexes** in a triangular grid
- **5 Quantum Nodes** are placed randomly (special strategic objectives)

### Terrain Types

Each hex has a terrain type that affects movement:

| Terrain | Color | Movement Cost | Notes |
|---------|-------|---------------|-------|
| **Plains** | Light green | 1.0 (easy) | Best for quick movement |
| **Forest** | Dark green | 1.5 (slow) | Harder to traverse |
| **Mountain** | Gray/brown | 2.0 (very slow) | Very difficult terrain |
| **Desert** | Sandy yellow | 1.3 (moderate) | Somewhat challenging |
| **Water** | Blue | 3.0 (extremely slow) | Avoid if possible |
| **Quantum Node** | Purple (glowing) | 1.0 (easy) | Strategic objective! |

**Important**: Lower movement cost = easier to move through!

---

## Resources & Economy

### What Are Resources?
Resources are the currency you use to perform actions. Think of them as your "action points."

### Starting Resources
- Every player starts with **100 resources**

### Earning Resources (Income)
At the end of each complete round (after all 3 players take their turn):
- **Base income**: +10 resources
- **Territory bonus**: +2 resources per hex you control

**Example**: If you control 8 hexes, you get 10 + (8 × 2) = **26 resources** per round!

### Important: Hex Resources vs Your Resources

When you hover over a hex, you'll see "Resources: 18" (or some number). **This does NOT get added to your resources when you claim the hex!**

That number is just information about the hex itself - it doesn't affect gameplay in the current version.

**What you actually get from expanding:**
- ✅ +1 territory (increases your income by +2 per round)
- ❌ The hex's resource number is NOT added to your pool

---

## Your Turn: 4 Possible Actions

Each turn, you can perform **ONE action**, then your turn ends.

### 1. EXPAND [E key or button] - Cost: 30 Resources

**What it does**: Claim a new neutral (unowned) hex next to your territory.

**How to use**:
1. Click the "Expand" button or press **E**
2. The game will highlight all neutral hexes adjacent to your territory (they'll glow yellow)
3. Click on any highlighted hex to claim it
4. Press **Esc** to cancel if you change your mind

**Why use it**:
- Increases your territory count (closer to territorial victory)
- Increases your income (more resources per round)
- Might capture a Quantum Node!

---

### 2. BUILD [B key or button] - Cost: 40 Resources

**What it does**: Train a Warrior unit on one of your hexes.

**How to use**:
- Click the "Build" button or press **B**
- A Warrior appears on one of your controlled hexes

**Why use it**:
- Units can defend your territory
- Units help you control strategic areas
- Shows your military strength

**Unit Details**:
- **Warrior**: 100 health, 2 movement points

---

### 3. ECONOMY [C key or button] - Cost: 25 Resources

**What it does**: Trade action that gives you quick resources.

**How it works**:
- You spend **25 resources**
- You immediately receive **40 resources**
- Net gain: **+15 resources**

**Why use it**:
- When you're low on resources and need a quick boost
- When you're close to 600 resources (economic victory)
- When you want to save up for multiple expensive actions

**⚠️ COMMON SITUATION**: If Expand and Build are grayed out but Economy is available, you have 25-29 resources. Use Economy to get back above 30!

---

### 4. END TURN [Space key or button] - Cost: 0 Resources

**What it does**: Pass your turn to the next player.

**When to use it**:
- You can't afford any other actions
- You want to save resources for next round
- You're in a good position and want to wait

---

## Units & Combat

### Unit Types

The game has 4 unit types (though you'll mainly use Warriors):

| Unit Type | Health | Movement | Special Ability |
|-----------|--------|----------|-----------------|
| **Scout** | 50 | 3 | Moves 20% faster on all terrain |
| **Warrior** | 100 | 2 | Standard combat unit |
| **Engineer** | 75 | varies | 30% faster in Mountains |
| **Quantum Specialist** | 60 | varies | Special quantum abilities |

**Note**: You start with 1 Scout. The Build action creates Warriors.

### Movement Costs

Different units move differently based on terrain:

**Example - Moving through Forest**:
- Warrior: 1.5 movement cost
- Scout: 1.2 movement cost (1.5 × 0.8)
- Engineer: 1.5 movement cost

**Moving through enemy territory**: +50% cost penalty!

---

## Game Interface Explained

### Top Bar (Header)
- Shows current **Turn number**
- When expanding, shows instructions: "Select a highlighted hex to Expand"

### Right Panel (Player Info)
Shows all 3 players' status:
- **Name & Type** (Human or AI)
- **Resources**: Blue bar (max 600)
- **Territories**: Green bar (max 18)
- **Quantum Nodes**: Purple bar (max 5)
- **Turn Log**: Recent actions

**Active player** has a glowing yellow outline!

### Bottom Bar (Actions)
- Shows your 4 action buttons
- Displays your current resources
- Buttons are **grayed out** if you can't afford them
- Shows hotkeys: [E], [B], [C], [SPACE]

### Minimap (Bottom-left)
- Small overview of the entire map
- Colored dots show who controls each hex
- Purple circles mark Quantum Nodes

### Hex Tooltip (Hover)
When you hover over a hex, you see:
- **Terrain type**
- **Owner** (which faction controls it)
- **Resources** available
- **Units** stationed there
- **Movement costs** for each unit type
- **Coordinates** (q, r position)

---

## The AI System (How Opponents Think)

The AI uses two advanced techniques:

### 1. Minimax Algorithm (Strategic Planning)
- Looks **2 turns ahead**
- Evaluates all possible moves and counter-moves
- Uses **Alpha-Beta pruning** (optimization)
- Chooses the move with the best outcome

### 2. Fuzzy Logic Evaluation (Scoring)
The AI scores game states based on:
- **Resources**: Low / Medium / High
- **Territories**: Few / Moderate / Many
- **Quantum Nodes**: None / Some / Many
- **Units**: Weak / Balanced / Strong

It combines these to determine if a position is:
- **Poor** (150 points)
- **Fair** (400 points)
- **Good** (700 points)
- **Excellent** (950 points)

**Bonus points** for being close to victory:
- +50 if you control 15+ territories
- +80 if you control 4+ Quantum Nodes
- +40 if you have 450+ resources

---

## Strategy Tips

### Early Game (Turns 1-10)
✅ **Focus on EXPAND**
- Territory gives you more income
- More income = more actions later
- Aim for 8-10 territories quickly

✅ **Grab Quantum Nodes**
- They're critical for quantum victory
- Even if you don't win via quantum, they deny your opponents

❌ **Don't spam BUILD too early**
- Units don't directly give you resources
- Better to expand first, build later

### Mid Game (Turns 11-20)
✅ **Balance EXPAND and BUILD**
- Keep expanding, but build some units for defense
- Protect your Quantum Nodes

✅ **Watch your opponents**
- If someone has 3-4 Quantum Nodes, they might win soon!
- If someone has 15+ territories, they're close to territorial victory

✅ **Use ECONOMY strategically**
- Convert when you're at 200-300 resources
- Helps you afford both EXPAND and BUILD

### Late Game (Turns 20+)
✅ **Push for victory**
- If you're at 500 resources, use ECONOMY to reach 600
- If you're at 16 territories, expand to 18
- If you're at 4 Quantum Nodes, grab the last one!

✅ **Block opponents**
- If an opponent is 1 territory away from winning, try to delay them
- Claim hexes they need

---

## Keyboard Controls

### During Your Turn
- **E**: Expand action (select a hex to claim)
- **B**: Build a Warrior unit
- **C**: Economy action (trade resources)
- **Space**: End your turn

### Other Controls
- **Esc**:
  - Cancel expand targeting (if active)
  - Open "Return to Home" menu (abandons match)
- **R**: Restart game (only after game over)
- **1 / 2 / 3**: Select game mode (on title screen)
- **Left / Right Arrow**: Navigate manual pages
- **Mouse Click**: Select hexes, click buttons

---

## Game Flow

1. **Title Screen**
   - Choose mode: 1, 2, or 3 players
   - Read manual (optional)
   - Click "Manual / How to Play" for detailed rules

2. **Game Start**
   - Random map generates with 5 Quantum Nodes
   - Each faction starts at a random location with 1 Scout unit
   - Each player has 100 resources

3. **Turn Order**
   - Blue → Red → Green → Blue → ...
   - After all 3 players take a turn = 1 complete round

4. **Each Turn**
   - Choose ONE action: Expand, Build, Economy, or End Turn
   - AI players think for ~0.3 seconds, then act
   - Turn passes to next player

5. **Income Phase**
   - After each complete round, all players get income
   - 10 base + 2 per territory controlled

6. **Victory Check**
   - After each action, game checks if anyone won
   - First to achieve any victory condition wins!

7. **Game Over**
   - Winner announced
   - Options: Restart (R) or Return Home (Esc)

---

## Common Questions

### Q: How do I attack other players?
**A**: This game doesn't have direct combat! You compete by racing to victory conditions. Units are mainly for territorial control.

### Q: What happens if I can't afford any actions?
**A**: Press Space to end your turn. You'll get income at the end of the round.

### Q: Can I cancel an action after clicking?
**A**: Only EXPAND can be canceled (press Esc). Other actions happen immediately.

### Q: Why is my button grayed out?
**A**: You don't have enough resources. The cost is shown on the button (-30, -40, -25).

### Q: I can only use Economy or End Turn - why are Expand and Build disabled?
**A**: You have between 25-29 resources! You can afford Economy (25) but not Expand (30) or Build (40).

**Quick Fix**: Use Economy! It costs 25 but gives you 40 back (+15 net). Then you'll have enough for Expand next turn.

**Example**:
- You have 28 resources
- Use Economy: 28 - 25 + 40 = **43 resources**
- Next turn you can afford Expand (30) or Build (40)!

**Alternative**: Press Space to end your turn and wait for income (10 + 2 per territory).

### Q: What if I control 3 Quantum Nodes - do I get a bonus?
**A**: No direct bonus, but you're closer to quantum victory (need all 5)!

### Q: Is there a turn limit?
**A**: No! The game continues until someone wins.

### Q: Can territories be captured by opponents?
**A**: No, once you claim a hex, it stays yours for the game.

---

## Winning Strategies by Victory Type

### Territorial Victory (18 hexes)
- **Focus**: Spam EXPAND every turn
- **Income**: High territory = high income = more expands
- **Timing**: Usually achievable by turn 15-20
- **Counter**: Other players will also expand, so be quick!

### Quantum Victory (5 nodes)
- **Focus**: Identify Quantum Node locations early (purple hexes)
- **Strategy**: Expand toward them specifically
- **Risk**: High competition - everyone wants them
- **Timing**: Can happen quickly if you're lucky with spawns

### Economic Victory (600 resources)
- **Focus**: Use ECONOMY action repeatedly
- **Math**: Each ECONOMY nets +15 resources
- **Combo**: High territory income + ECONOMY = fast win
- **Timing**: Usually turn 20-30 depending on strategy

---

## Visual Indicators

### Colors on Map
- **Blue hexes**: Expansion Empire territory
- **Red hexes**: Tech Collective territory
- **Green hexes**: Adaptive Alliance territory
- **Gray hexes**: Neutral (unclaimed)

### Glowing Effects
- **Yellow glow**: Selected hex or expand targets
- **Purple glow**: Quantum Nodes (always visible)
- **White ring**: Unit health indicator (circular arc)

### Unit Markers
- Colored circles show units
- Number badge shows if multiple units on same hex
- Health bar appears as an arc around the unit

---

## Technical Features (for the curious)

This game uses advanced algorithms:
- **A* Pathfinding**: Units find optimal routes considering terrain
- **Minimax AI**: Makes strategic decisions 2 turns ahead
- **Fuzzy Logic**: Evaluates complex game states
- **Alpha-Beta Pruning**: Optimizes AI decision speed

---

## Summary Cheat Sheet

| Action | Hotkey | Cost | Effect |
|--------|--------|------|--------|
| Expand | E | 30 | Claim adjacent neutral hex |
| Build | B | 40 | Train a Warrior unit |
| Economy | C | 25 | Get 40 resources (net +15) |
| End Turn | Space | 0 | Pass to next player |

**Win Conditions**:
- 18 territories OR 5 Quantum Nodes OR 600 resources

**Income**: 10 + (2 × territories owned)

**Starting**: 100 resources, 1 Scout unit, random map

---

## Final Tips

1. **Early expansion is key** - More territory = more income
2. **Watch the victory bars** in the right panel
3. **Quantum Nodes** are game-changers - prioritize them
4. **ECONOMY** is useful when you're resource-starved
5. **Don't over-build** - Units don't win the game directly
6. **Adapt your strategy** - If one path is blocked, switch victory conditions!

---

**Good luck, Commander! May your faction dominate the Quantum Territory!** 🎮🌍

---

*For more help, press the "Manual / How to Play" button on the title screen to see the in-game tutorial.*
